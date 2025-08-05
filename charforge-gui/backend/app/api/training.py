from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime
from pathlib import Path

from app.core.database import get_db, Character, TrainingSession, User
from app.core.auth import get_current_active_user
from app.services.charforge_integration import CharForgeIntegration, CharacterConfig
from app.services.settings_service import get_user_env_vars

router = APIRouter()

# Pydantic models
class TrainingRequest(BaseModel):
    character_id: int
    steps: Optional[int] = 800
    batch_size: Optional[int] = 1
    learning_rate: Optional[float] = 8e-4
    train_dim: Optional[int] = 512
    rank_dim: Optional[int] = 8
    pulidflux_images: Optional[int] = 0

class TrainingResponse(BaseModel):
    id: int
    character_id: int
    status: str
    progress: float
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class CharacterResponse(BaseModel):
    id: int
    name: str
    status: str
    work_dir: str
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class CharacterCreateRequest(BaseModel):
    name: str
    input_image_path: str

# Global integration instance
charforge = CharForgeIntegration()

@router.post("/characters", response_model=CharacterResponse)
async def create_character(
    request: CharacterCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new character."""

    # Validate input
    if not request.name or len(request.name.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Character name is required"
        )

    # Sanitize character name
    sanitized_name = ''.join(c for c in request.name if c.isalnum() or c in '_-').strip()
    if not sanitized_name or len(sanitized_name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid character name. Use only letters, numbers, underscores, and hyphens (max 100 chars)"
        )

    # Validate image path
    if not request.input_image_path or not Path(request.input_image_path).exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid input image path is required"
        )

    # Check if character name already exists for this user
    existing = db.query(Character).filter(
        Character.name == sanitized_name,
        Character.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Character with this name already exists"
        )

    # Create character record
    character = Character(
        name=sanitized_name,
        user_id=current_user.id,
        input_image_path=request.input_image_path,
        work_dir=str(charforge.scratch_dir / sanitized_name),
        status="created"
    )

    db.add(character)
    db.commit()
    db.refresh(character)

    return character

@router.get("/characters", response_model=List[CharacterResponse])
async def list_characters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all characters for the current user."""
    characters = db.query(Character).filter(Character.user_id == current_user.id).all()
    return characters

@router.get("/characters/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific character."""
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == current_user.id
    ).first()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    return character

@router.post("/characters/{character_id}/train", response_model=TrainingResponse)
async def start_training(
    character_id: int,
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start training for a character."""
    
    # Get character
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == current_user.id
    ).first()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    # Check if there's already a running training session
    existing_session = db.query(TrainingSession).filter(
        TrainingSession.character_id == character_id,
        TrainingSession.status.in_(["pending", "running"])
    ).first()
    
    if existing_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Training session already in progress"
        )
    
    # Create training session
    training_session = TrainingSession(
        character_id=character_id,
        user_id=current_user.id,
        steps=request.steps,
        batch_size=request.batch_size,
        learning_rate=request.learning_rate,
        train_dim=request.train_dim,
        rank_dim=request.rank_dim,
        pulidflux_images=request.pulidflux_images,
        status="pending"
    )
    
    db.add(training_session)
    db.commit()
    db.refresh(training_session)
    
    # Start training in background
    background_tasks.add_task(
        run_training_background,
        training_session.id,
        character,
        request,
        current_user.id
    )
    
    return training_session

async def run_training_background(
    session_id: int,
    character: Character,
    request: TrainingRequest,
    user_id: int
):
    """Background task to run training."""
    db = next(get_db())
    
    try:
        # Update session status
        session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
        session.status = "running"
        session.started_at = datetime.utcnow()
        db.commit()
        
        # Update character status
        character.status = "training"
        db.commit()
        
        # Get user environment variables
        env_vars = await get_user_env_vars(user_id, db)
        
        # Create CharForge config
        config = CharacterConfig(
            name=character.name,
            input_image=character.input_image_path,
            work_dir=character.work_dir,
            steps=request.steps,
            batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            train_dim=request.train_dim,
            rank_dim=request.rank_dim,
            pulidflux_images=request.pulidflux_images
        )
        
        # Progress callback
        def update_progress(progress: float, message: str):
            session.progress = progress
            db.commit()
        
        # Run training
        result = await charforge.run_training(config, env_vars, update_progress)
        
        # Update session with results
        session.status = "completed" if result["success"] else "failed"
        session.completed_at = datetime.utcnow()
        session.progress = 100.0 if result["success"] else session.progress
        
        # Update character status
        character.status = "completed" if result["success"] else "failed"
        if result["success"]:
            character.completed_at = datetime.utcnow()
        
        db.commit()
        
    except Exception as e:
        # Handle errors
        session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
        session.status = "failed"
        session.completed_at = datetime.utcnow()
        
        character.status = "failed"
        
        db.commit()
    
    finally:
        db.close()

@router.get("/characters/{character_id}/training", response_model=List[TrainingResponse])
async def get_training_sessions(
    character_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get training sessions for a character."""
    
    # Verify character ownership
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == current_user.id
    ).first()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    sessions = db.query(TrainingSession).filter(
        TrainingSession.character_id == character_id
    ).order_by(TrainingSession.created_at.desc()).all()
    
    return sessions

@router.get("/training/{session_id}", response_model=TrainingResponse)
async def get_training_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific training session."""

    # Validate session_id
    if session_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID"
        )

    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
        TrainingSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training session not found"
        )

    return session
