from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    input_image_path = Column(String, nullable=False)
    work_dir = Column(String, nullable=False)
    status = Column(String, default="created")  # created, training, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class TrainingSession(Base):
    __tablename__ = "training_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    steps = Column(Integer, default=800)
    batch_size = Column(Integer, default=1)
    learning_rate = Column(Float, default=8e-4)
    train_dim = Column(Integer, default=512)
    rank_dim = Column(Integer, default=8)
    pulidflux_images = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    log_file = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class InferenceJob(Base):
    __tablename__ = "inference_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
    optimized_prompt = Column(Text, nullable=True)
    lora_weight = Column(Float, default=0.73)
    test_dim = Column(Integer, default=1024)
    batch_size = Column(Integer, default=4)
    num_inference_steps = Column(Integer, default=30)
    do_optimize_prompt = Column(Boolean, default=True)
    fix_outfit = Column(Boolean, default=False)
    safety_check = Column(Boolean, default=True)
    face_enhance = Column(Boolean, default=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    output_paths = Column(Text, nullable=True)  # JSON array of file paths
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class AppSettings(Base):
    __tablename__ = "app_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=True)
    is_encrypted = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Dependency to get database session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
