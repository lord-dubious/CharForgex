#!/usr/bin/env python3
"""
Utility functions for CharForgex RunPod Worker
"""

import os
import sys
import logging
import base64
import tempfile
import shutil
import glob
from typing import Optional, List
from PIL import Image
from io import BytesIO

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

# Create logger for this module
logger = logging.getLogger(__name__)

def get_persistent_path(subpath: str = "") -> str:
    """
    Get path in persistent storage (network volume)

    Args:
        subpath: Subdirectory path

    Returns:
        Full path in persistent storage
    """
    # Validate subpath to prevent directory traversal
    if subpath and ('..' in subpath or subpath.startswith('/') or subpath.startswith('\\')):
        raise ValueError("Invalid subpath: directory traversal not allowed")

    base_path = "/runpod-volume"
    if subpath:
        return os.path.join(base_path, subpath)
    return base_path

def ensure_directories():
    """Ensure all required directories exist with error handling"""
    directories = [
        get_persistent_path('models'),
        get_persistent_path('loras'),
        get_persistent_path('datasets'),
        get_persistent_path('outputs'),
        get_persistent_path('huggingface'),
        '/tmp/charforge'
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"✅ Ensured directory exists: {directory}")
        except PermissionError:
            # Fallback to /tmp if /runpod-volume is not accessible
            if '/runpod-volume' in directory:
                fallback_dir = directory.replace('/runpod-volume', '/tmp/runpod-volume')
                try:
                    os.makedirs(fallback_dir, exist_ok=True)
                    logger.warning(f"⚠️ Using fallback directory: {fallback_dir}")
                except Exception as e:
                    logger.error(f"❌ Failed to create fallback directory {fallback_dir}: {e}")
            else:
                logger.error(f"❌ Failed to create directory {directory}: Permission denied")
        except Exception as e:
            logger.error(f"❌ Failed to create directory {directory}: {e}")

def save_base64_image(base64_string: str, output_path: str) -> str:
    """
    Save base64 encoded image to file
    
    Args:
        base64_string: Base64 encoded image data
        output_path: Path to save the image
        
    Returns:
        Path to saved image
    """
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Open and save image
        image = Image.open(BytesIO(image_data))
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save image
        image.save(output_path)
        
        return output_path
        
    except Exception as e:
        raise ValueError(f"Failed to save base64 image: {e}")

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode image file to base64 string
    
    Args:
        image_path: Path to image file
        
    Returns:
        Base64 encoded image data
    """
    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            base64_string = base64.b64encode(image_data).decode('utf-8')
            return base64_string
    except Exception as e:
        raise ValueError(f"Failed to encode image to base64: {e}")

def cleanup_temp_files():
    """Clean up temporary files and directories"""
    temp_patterns = [
        '/tmp/charforge*',
        '/tmp/*_input.*',
        '/tmp/*_output.*',
        '/workspace/scratch/*/temp*'
    ]
    
    for pattern in temp_patterns:
        try:
            for path in glob.glob(pattern):
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
        except Exception as e:
            logging.warning(f"Failed to cleanup {pattern}: {e}")

def get_available_characters() -> List[str]:
    """
    Get list of available trained characters
    
    Returns:
        List of character names
    """
    characters = []
    loras_dir = get_persistent_path('loras')
    
    if os.path.exists(loras_dir):
        for item in os.listdir(loras_dir):
            character_path = os.path.join(loras_dir, item)
            if os.path.isdir(character_path):
                # Check if there are any LoRA files
                lora_files = [f for f in os.listdir(character_path) 
                             if f.endswith('.safetensors')]
                if lora_files:
                    characters.append(item)
    
    return characters

def validate_input_parameters(params: dict, required_fields: List[str]) -> None:
    """
    Validate input parameters
    
    Args:
        params: Input parameters dictionary
        required_fields: List of required field names
        
    Raises:
        ValueError: If required fields are missing
    """
    missing_fields = []
    for field in required_fields:
        if field not in params or params[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

def get_model_info() -> dict:
    """
    Get information about available models
    
    Returns:
        Dictionary with model information
    """
    info = {
        'huggingface_cache': get_persistent_path('huggingface'),
        'models_dir': get_persistent_path('models'),
        'loras_dir': get_persistent_path('loras'),
        'available_characters': get_available_characters()
    }
    
    # Check disk usage
    try:
        import shutil
        total, used, free = shutil.disk_usage(get_persistent_path())
        info['storage'] = {
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'free_gb': round(free / (1024**3), 2)
        }
    except Exception as e:
        info['storage'] = {'error': str(e)}
    
    return info

def setup_environment_variables():
    """Setup required environment variables"""
    env_vars = {
        'HF_HOME': get_persistent_path('huggingface'),
        'COMFYUI_PATH': '/workspace/ComfyUI',
        'APP_PATH': '/workspace',
        'PLATFORM': 'serverless',
        'PYTHONPATH': '/workspace',
        'TORCH_CUDA_ARCH_LIST': '6.0 6.1 7.0 7.5 8.0 8.6+PTX',
        'FORCE_CUDA': '1'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value

def check_gpu_availability() -> dict:
    """
    Check GPU availability and memory
    
    Returns:
        Dictionary with GPU information
    """
    try:
        import torch
        
        gpu_info = {
            'cuda_available': torch.cuda.is_available(),
            'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0
        }
        
        if torch.cuda.is_available():
            gpu_info['gpu_name'] = torch.cuda.get_device_name(0)
            gpu_info['memory_total'] = torch.cuda.get_device_properties(0).total_memory
            gpu_info['memory_allocated'] = torch.cuda.memory_allocated(0)
            gpu_info['memory_free'] = gpu_info['memory_total'] - gpu_info['memory_allocated']
        
        return gpu_info
        
    except Exception as e:
        return {'error': str(e)}

def clear_gpu_memory():
    """Clear GPU memory cache"""
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    except Exception as e:
        logging.warning(f"Failed to clear GPU memory: {e}")

def create_progress_callback(job_id: str = None):
    """
    Create a progress callback function for long-running operations
    
    Args:
        job_id: Optional job ID for tracking
        
    Returns:
        Progress callback function
    """
    def progress_callback(step: int, total_steps: int, message: str = ""):
        progress = (step / total_steps) * 100 if total_steps > 0 else 0
        log_message = f"Progress: {progress:.1f}% ({step}/{total_steps})"
        if message:
            log_message += f" - {message}"
        if job_id:
            log_message = f"[{job_id}] {log_message}"
        
        logging.info(log_message)
    
    return progress_callback
