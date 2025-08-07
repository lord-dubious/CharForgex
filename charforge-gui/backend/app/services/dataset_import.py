import os
from datetime import datetime
from sqlalchemy.orm import Session
import yaml
from app.core.config import settings
from app.core.database import Dataset, DatasetImage

def import_datasets_from_scratch(db: Session, user_id: int):
    """Import existing datasets from the scratch folder."""
    import yaml
    
    scratch_dir = settings.CHARFORGE_SCRATCH_DIR
    if not scratch_dir.exists():
        return []
    
    imported_datasets = []
    
    # Scan each folder in the scratch directory
    for folder_name in os.listdir(scratch_dir):
        folder_path = scratch_dir / folder_name
        if not folder_path.is_dir():
            continue
            
        # Check if this folder has dataset structure
        sheet_dir = folder_path / "sheet"
        config_file = folder_path / "config.yaml"
        
        if not sheet_dir.exists() or not config_file.exists():
            continue
            
        # Check if dataset already exists in database
        existing_dataset = db.query(Dataset).filter(
            Dataset.name == folder_name,
            Dataset.user_id == user_id
        ).first()
        
        if existing_dataset:
            continue
            
        # Parse config.yaml to get trigger word and other info
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                
                # Extract trigger word from datasets config
                trigger_word = ""
                if 'config' in config and 'datasets' in config['config'] and len(config['config']['datasets']) > 0:
                    # This is a bit of a guess based on the structure we saw earlier
                    trigger_word = config['config']['datasets'][0].get('trigger_word', folder_name)
        except Exception as e:
            print(f"Error parsing config for {folder_name}: {e}")
            trigger_word = folder_name
            
        # Count images in sheet directory
        image_count = 0
        for file in os.listdir(sheet_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_count += 1
                
        # Create dataset record
        dataset = Dataset(
            user_id=user_id,
            name=folder_name,
            trigger_word=trigger_word,
            caption_template="a photo of {trigger} person",
            auto_caption=True,
            resize_images=True,
            crop_images=True,
            flip_images=False,
            quality_filter="basic",
            image_count=image_count,
            status="ready",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        # Create dataset image records
        for file in os.listdir(sheet_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Check if there's a corresponding caption file
                caption = None
                caption_file = sheet_dir / f"{os.path.splitext(file)[0]}.txt"
                if caption_file.exists():
                    try:
                        with open(caption_file, 'r') as f:
                            caption = f.read().strip()
                    except:
                        pass
                
                dataset_image = DatasetImage(
                    dataset_id=dataset.id,
                    filename=file,
                    original_filename=file,
                    caption=caption,
                    processed=True,
                    created_at=datetime.utcnow()
                )
                db.add(dataset_image)
                
        db.commit()
        imported_datasets.append(dataset)
        
    return imported_datasets