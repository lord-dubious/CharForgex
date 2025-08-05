"""Input validation utilities for CharForge GUI."""

import re
from typing import Any, Dict, List, Optional
from pathlib import Path


class ValidationError(Exception):
    """Custom validation error."""
    pass


def validate_username(username: str) -> bool:
    """Validate username format."""
    if not username or not isinstance(username, str):
        return False
    
    # Username should be 3-50 characters, alphanumeric plus underscore/hyphen
    if not (3 <= len(username) <= 50):
        return False
    
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, username))


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False
    
    # Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> bool:
    """Validate password strength."""
    if not password or not isinstance(password, str):
        return False
    
    # At least 8 characters
    if len(password) < 8:
        return False
    
    # Check for at least one letter and one number
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_number = bool(re.search(r'\d', password))
    
    return has_letter and has_number


def validate_character_name(name: str) -> bool:
    """Validate character name."""
    if not name or not isinstance(name, str):
        return False
    
    # 1-100 characters, alphanumeric plus underscore/hyphen
    if not (1 <= len(name) <= 100):
        return False
    
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, name))


def validate_file_path(file_path: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """Validate file path for security."""
    if not file_path or not isinstance(file_path, str):
        return False
    
    try:
        path = Path(file_path)
        
        # Check for path traversal attempts
        if '..' in str(path) or str(path).startswith('/'):
            return False
        
        # Check file extension if specified
        if allowed_extensions:
            if path.suffix.lower() not in allowed_extensions:
                return False
        
        return True
    except (ValueError, OSError):
        return False


def validate_training_params(params: Dict[str, Any]) -> bool:
    """Validate training parameters."""
    try:
        # Validate numeric parameters
        steps = int(params.get('steps', 0))
        if not (100 <= steps <= 10000):
            return False
        
        batch_size = int(params.get('batch_size', 0))
        if not (1 <= batch_size <= 32):
            return False
        
        learning_rate = float(params.get('learning_rate', 0))
        if not (0.0001 <= learning_rate <= 1.0):
            return False
        
        train_dim = int(params.get('train_dim', 0))
        if not (256 <= train_dim <= 2048):
            return False
        
        rank_dim = int(params.get('rank_dim', 0))
        if not (1 <= rank_dim <= 128):
            return False
        
        pulidflux_images = int(params.get('pulidflux_images', 0))
        if not (0 <= pulidflux_images <= 100):
            return False
        
        return True
    except (ValueError, TypeError):
        return False


def validate_inference_params(params: Dict[str, Any]) -> bool:
    """Validate inference parameters."""
    try:
        # Validate numeric parameters
        lora_weight = float(params.get('lora_weight', 0))
        if not (0.1 <= lora_weight <= 2.0):
            return False
        
        test_dim = int(params.get('test_dim', 0))
        if not (256 <= test_dim <= 2048):
            return False
        
        batch_size = int(params.get('batch_size', 0))
        if not (1 <= batch_size <= 16):
            return False
        
        num_inference_steps = int(params.get('num_inference_steps', 0))
        if not (10 <= num_inference_steps <= 200):
            return False
        
        # Validate prompt
        prompt = params.get('prompt', '')
        if not prompt or len(prompt) > 2000:
            return False
        
        return True
    except (ValueError, TypeError):
        return False


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input."""
    if not isinstance(value, str):
        value = str(value)
    
    # Remove null bytes and control characters
    value = ''.join(char for char in value if ord(char) >= 32)
    
    # Limit length
    return value[:max_length].strip()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    if not isinstance(filename, str):
        filename = str(filename)
    
    # Remove path separators and dangerous characters
    dangerous_chars = ['/', '\\', '..', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '')
    
    # Limit length and ensure it's not empty
    filename = filename.strip()[:255]
    if not filename:
        filename = 'unnamed_file'
    
    return filename


def validate_api_key(key: str, key_type: str) -> bool:
    """Validate API key format."""
    if not key or not isinstance(key, str):
        return False
    
    # Basic validation based on key type
    if key_type == 'HF_TOKEN':
        return key.startswith('hf_') and len(key) > 10
    elif key_type == 'GOOGLE_API_KEY':
        return key.startswith('AIza') and len(key) > 20
    elif key_type == 'FAL_KEY':
        return len(key) > 10  # Basic length check
    elif key_type == 'CIVITAI_API_KEY':
        return len(key) > 10  # Basic length check
    
    return True  # Allow other key types


def validate_json_structure(data: Any, max_depth: int = 10, max_keys: int = 100) -> bool:
    """Validate JSON structure to prevent DoS attacks."""
    def check_depth(obj, current_depth=0):
        if current_depth > max_depth:
            return False
        
        if isinstance(obj, dict):
            if len(obj) > max_keys:
                return False
            return all(check_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if len(obj) > max_keys:
                return False
            return all(check_depth(item, current_depth + 1) for item in obj)
        
        return True
    
    return check_depth(data)
