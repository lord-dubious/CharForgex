from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    # API Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Authentication (Optional - disabled by default)
    @staticmethod
    def _parse_bool_env(var_name: str, default: str = "false") -> bool:
        """Parse boolean environment variable with multiple valid representations."""
        val = os.getenv(var_name, default)
        return str(val).strip().lower() in {"1", "true", "yes", "on"}

    ENABLE_AUTH: bool = _parse_bool_env("ENABLE_AUTH", "false")
    ALLOW_REGISTRATION: bool = _parse_bool_env("ALLOW_REGISTRATION", "false")
    DEFAULT_USER_ID: int = int(os.getenv("DEFAULT_USER_ID", "1"))  # Used when auth is disabled

    def __post_init__(self):
        """Validate critical settings after initialization."""
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            import secrets
            self.SECRET_KEY = secrets.token_urlsafe(32)
            print("WARNING: Using auto-generated SECRET_KEY. Set SECRET_KEY environment variable for production.")

        # Validate other critical settings
        if self.ACCESS_TOKEN_EXPIRE_MINUTES < 5:
            print("WARNING: ACCESS_TOKEN_EXPIRE_MINUTES is very low. Consider increasing for better UX.")

        # Ensure media directory exists and is secure
        self.MEDIA_DIR.mkdir(parents=True, exist_ok=True)

        # Set secure permissions on media directory (Unix only)
        try:
            import stat
            self.MEDIA_DIR.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)  # 750
        except (OSError, AttributeError):
            pass  # Windows or permission error
    
    # Database
    DATABASE_URL: str = "sqlite:///./database.db"
    
    # CORS - Enhanced for remote access
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://0.0.0.0:5173",
        "http://0.0.0.0:3000"
    ]

    # Server Configuration
    HOST: str = "0.0.0.0"  # Allow external connections
    PORT: int = 8000
    FRONTEND_HOST: str = "0.0.0.0"
    FRONTEND_PORT: int = 5173
    
    # File Storage
    BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MEDIA_DIR: Path = BASE_DIR / "media"
    RESULTS_DIR: Path = BASE_DIR / "results"
    
    # CharForge Integration
    CHARFORGE_ROOT: Path = BASE_DIR.parent  # Points to the main CharForge directory
    CHARFORGE_SCRATCH_DIR: Path = CHARFORGE_ROOT / "scratch"
    
    # Environment Variables for CharForge
    HF_TOKEN: str = ""
    HF_HOME: str = ""
    CIVITAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    FAL_KEY: str = ""
    
    # Training Defaults
    DEFAULT_STEPS: int = 800
    DEFAULT_BATCH_SIZE: int = 1
    DEFAULT_LEARNING_RATE: float = 8e-4
    DEFAULT_TRAIN_DIM: int = 512
    DEFAULT_RANK_DIM: int = 8
    
    # Inference Defaults
    DEFAULT_LORA_WEIGHT: float = 0.73
    DEFAULT_TEST_DIM: int = 1024
    DEFAULT_INFERENCE_STEPS: int = 30
    DEFAULT_BATCH_SIZE_INFERENCE: int = 4
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
