from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json
import shutil
from pathlib import Path
from datetime import datetime

from app.core.database import get_db, Dataset, DatasetImage, User
from app.core.auth import get_current_active_user, get_current_user_optional
from app.core.config import settings

router = APIRouter()

# Pydantic models
class DatasetCreateRequest(BaseModel):
    name: str
    trigger_word: str
    caption_template: str = "a photo of {trigger} person"
    auto_caption: bool = True
    resize_images: bool = True
    crop_images: bool = True
    flip_images: bool = False
    quality_filter: str = "basic"
    selected_images: List[str]

class DatasetResponse(BaseModel):
    id: int
    name: str
    trigger_word: str
    caption_template: str
    auto_caption: bool
    resize_images: bool
    crop_images: bool
    flip_images: bool
    quality_filter: str
    image_count: int
    status: str
    created_at: datetime
    updated_at: datetime

class DatasetImageResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    caption: Optional[str]
    processed: bool
    created_at: datetime

class DatasetListResponse(BaseModel):
    datasets: List[DatasetResponse]
    total: int

class CaptionUpdateRequest(BaseModel):
    caption: str

class TriggerWordUpdateRequest(BaseModel):
    trigger_word: str

@router.post("/datasets", response_model=DatasetResponse)
async def create_dataset(
    request: DatasetCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Create a new dataset from selected images."""
    
    # Validate input
    if not request.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset name is required"
        )
    
    if not request.trigger_word.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trigger word is required"
        )
    
    if not request.selected_images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image must be selected"
        )
    
    # Check if dataset name already exists for this user
    existing = db.query(Dataset).filter(
        Dataset.name == request.name.strip(),
        Dataset.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset with this name already exists"
        )
    
    # Create dataset record
    dataset = Dataset(
        user_id=current_user.id,
        name=request.name.strip(),
        trigger_word=request.trigger_word.strip(),
        caption_template=request.caption_template,
        auto_caption=request.auto_caption,
        resize_images=request.resize_images,
        crop_images=request.crop_images,
        flip_images=request.flip_images,
        quality_filter=request.quality_filter,
        image_count=len(request.selected_images),
        status="processing"
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    # Add images to dataset
    user_media_dir = settings.MEDIA_DIR / str(current_user.id)
    for filename in request.selected_images:
        # Verify file exists
        file_path = user_media_dir / filename
        if file_path.exists():
            dataset_image = DatasetImage(
                dataset_id=dataset.id,
                filename=filename,
                original_filename=filename,  # TODO: Get original filename from media table
                caption=None,
                processed=False
            )
            db.add(dataset_image)
    
    db.commit()
    
    # Process dataset in background
    background_tasks.add_task(process_dataset, dataset.id, current_user.id)
    
    return dataset

@router.get("/datasets", response_model=DatasetListResponse)
async def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Get all datasets for the current user."""
    
    datasets = db.query(Dataset).filter(
        Dataset.user_id == current_user.id
    ).order_by(Dataset.created_at.desc()).all()
    
    return DatasetListResponse(
        datasets=datasets,
        total=len(datasets)
    )

@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Get a specific dataset."""
    
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    return dataset

@router.get("/datasets/{dataset_id}/images", response_model=List[DatasetImageResponse])
async def get_dataset_images(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Get all images in a dataset."""
    
    # Verify dataset ownership
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    images = db.query(DatasetImage).filter(
        DatasetImage.dataset_id == dataset_id
    ).order_by(DatasetImage.created_at).all()
    
    return images

@router.put("/datasets/{dataset_id}/trigger-word")
async def update_trigger_word(
    dataset_id: int,
    request: TriggerWordUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Update the trigger word for a dataset."""
    
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    if not request.trigger_word.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trigger word cannot be empty"
        )
    
    dataset.trigger_word = request.trigger_word.strip()
    dataset.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Trigger word updated successfully"}

@router.put("/datasets/{dataset_id}/images/{image_id}/caption")
async def update_image_caption(
    dataset_id: int,
    image_id: int,
    request: CaptionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Update the caption for a specific image in a dataset."""
    
    # Verify dataset ownership
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Get the image
    image = db.query(DatasetImage).filter(
        DatasetImage.id == image_id,
        DatasetImage.dataset_id == dataset_id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found in dataset"
        )
    
    image.caption = request.caption
    db.commit()
    
    return {"message": "Caption updated successfully"}

@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Delete a dataset and all its images."""
    
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Delete dataset images
    db.query(DatasetImage).filter(
        DatasetImage.dataset_id == dataset_id
    ).delete()
    
    # Delete dataset
    db.delete(dataset)
    db.commit()
    
    return {"message": "Dataset deleted successfully"}

async def process_dataset(dataset_id: int, user_id: int):
    """Background task to process dataset images."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    dataset = None

    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            return

        # Update status to processing
        dataset.status = "processing"
        db.commit()

        # Get dataset images
        images = db.query(DatasetImage).filter(
            DatasetImage.dataset_id == dataset_id
        ).all()

        # Process each image
        processed_count = 0
        for image in images:
            try:
                # Generate caption if auto_caption is enabled
                if dataset.auto_caption:
                    caption = generate_caption(image.filename, dataset.trigger_word, dataset.caption_template)
                    image.caption = caption
                else:
                    # Use template with trigger word
                    caption = dataset.caption_template.replace("{trigger}", dataset.trigger_word)
                    image.caption = caption

                image.processed = True
                processed_count += 1

                # Commit every 10 images to avoid long transactions
                if processed_count % 10 == 0:
                    db.commit()

            except Exception as e:
                print(f"Error processing image {image.filename}: {e}")
                continue

        # Final commit for remaining images
        db.commit()

        # Update dataset status
        dataset.status = "ready"
        db.commit()

    except Exception as e:
        # Update status to failed
        try:
            if dataset:
                dataset.status = "failed"
                db.commit()
        except Exception:
            pass  # Ignore commit errors during error handling
        print(f"Error processing dataset {dataset_id}: {e}")

    finally:
        db.close()

def generate_caption(filename: str, trigger_word: str, template: str) -> str:
    """Generate a caption for an image."""
    # For now, just use the template with trigger word
    # TODO: Implement AI-based caption generation
    return template.replace("{trigger}", trigger_word)
