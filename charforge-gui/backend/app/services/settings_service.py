from sqlalchemy.orm import Session
from typing import Dict, Optional
import base64
from cryptography.fernet import Fernet
import os

from app.core.database import AppSettings

# Simple encryption for sensitive settings
def get_encryption_key():
    """Get or create encryption key for sensitive settings."""
    # Use environment variable for production
    env_key = os.getenv("ENCRYPTION_KEY")
    if env_key:
        return base64.urlsafe_b64decode(env_key.encode())

    # Fallback to file-based key for development
    key_file = "encryption.key"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        # Set secure permissions on the key file
        with open(key_file, "wb") as f:
            f.write(key)
        os.chmod(key_file, 0o600)  # Read/write for owner only
        print("WARNING: Generated new encryption key. Set ENCRYPTION_KEY environment variable for production.")
        return key

ENCRYPTION_KEY = get_encryption_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_value(value: str) -> str:
    """Encrypt a sensitive value."""
    return cipher_suite.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value: str) -> str:
    """Decrypt a sensitive value."""
    return cipher_suite.decrypt(encrypted_value.encode()).decode()

async def save_user_setting(
    user_id: int,
    key: str,
    value: str,
    is_sensitive: bool,
    db: Session
) -> AppSettings:
    """Save a user setting."""
    
    # Check if setting already exists
    existing = db.query(AppSettings).filter(
        AppSettings.user_id == user_id,
        AppSettings.key == key
    ).first()
    
    # Encrypt sensitive values
    stored_value = encrypt_value(value) if is_sensitive else value
    
    if existing:
        existing.value = stored_value
        existing.is_encrypted = is_sensitive
        db.commit()
        db.refresh(existing)
        return existing
    else:
        setting = AppSettings(
            user_id=user_id,
            key=key,
            value=stored_value,
            is_encrypted=is_sensitive
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
        return setting

async def get_user_setting(
    user_id: int,
    key: str,
    db: Session
) -> Optional[str]:
    """Get a user setting value."""
    
    setting = db.query(AppSettings).filter(
        AppSettings.user_id == user_id,
        AppSettings.key == key
    ).first()
    
    if not setting:
        return None
    
    if setting.is_encrypted:
        return decrypt_value(setting.value)
    else:
        return setting.value

async def get_user_settings(user_id: int, db: Session) -> Dict[str, str]:
    """Get all user settings."""
    
    settings = db.query(AppSettings).filter(AppSettings.user_id == user_id).all()
    
    result = {}
    for setting in settings:
        if setting.is_encrypted:
            result[setting.key] = decrypt_value(setting.value)
        else:
            result[setting.key] = setting.value
    
    return result

async def get_user_env_vars(user_id: int, db: Session) -> Dict[str, str]:
    """Get environment variables for CharForge from user settings."""
    
    settings = await get_user_settings(user_id, db)
    
    env_vars = {
        'HF_TOKEN': settings.get('HF_TOKEN', ''),
        'HF_HOME': settings.get('HF_HOME', ''),
        'CIVITAI_API_KEY': settings.get('CIVITAI_API_KEY', ''),
        'GOOGLE_API_KEY': settings.get('GOOGLE_API_KEY', ''),
        'FAL_KEY': settings.get('FAL_KEY', ''),
    }
    
    return env_vars

async def delete_user_setting(user_id: int, key: str, db: Session) -> bool:
    """Delete a user setting."""
    
    setting = db.query(AppSettings).filter(
        AppSettings.user_id == user_id,
        AppSettings.key == key
    ).first()
    
    if setting:
        db.delete(setting)
        db.commit()
        return True
    
    return False
