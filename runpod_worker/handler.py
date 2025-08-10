#!/usr/bin/env python3
"""
CharForgex Handler for RunPod Worker
Handles training and inference operations
"""

import os
import sys
import logging
import json
import base64
import time
from typing import Dict, Any, List, Optional
from io import BytesIO
from PIL import Image
import traceback

# Add workspace to Python path
sys.path.insert(0, '/workspace')

# Lazy imports for CharForgex components (imported when needed)
CharacterConfig = None
build_character = None
LoRAImageGen = None
_charforgex_imports_loaded = False

def _load_charforgex_imports():
    """Lazy load CharForgex imports to avoid import errors at module level"""
    global CharacterConfig, build_character, LoRAImageGen, _charforgex_imports_loaded

    if _charforgex_imports_loaded:
        return

    try:
        from train_character import CharacterConfig, build_character
        from test_character import LoRAImageGen
        _charforgex_imports_loaded = True
        logging.info("✅ CharForgex imports loaded successfully")
    except ImportError as e:
        logging.error(f"❌ Failed to load CharForgex imports: {e}")
        raise RuntimeError(f"CharForgex dependencies not available: {e}")

# Import utilities with fallback
try:
    from utils import save_base64_image, encode_image_to_base64, get_persistent_path, clear_gpu_memory, check_gpu_availability
except ImportError:
    # Fallback implementations for testing
    def save_base64_image(base64_data: str, output_path: str) -> str:
        """Fallback implementation"""
        image_data = base64.b64decode(base64_data)
        with open(output_path, 'wb') as f:
            f.write(image_data)
        return output_path

    def encode_image_to_base64(image_path: str) -> str:
        """Fallback implementation"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def get_persistent_path(subpath: str = '') -> str:
        """Fallback implementation"""
        base_path = '/runpod-volume' if os.path.exists('/runpod-volume') else '/tmp'
        return os.path.join(base_path, subpath) if subpath else base_path

    def check_gpu_availability() -> Dict[str, Any]:
        """Fallback implementation"""
        try:
            import torch
            return {
                'cuda_available': torch.cuda.is_available(),
                'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
                'gpu_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No GPU'
            }
        except ImportError:
            return {'cuda_available': False, 'gpu_count': 0, 'gpu_name': 'PyTorch not available'}

    def clear_gpu_memory():
        """Fallback implementation"""
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

logger = logging.getLogger(__name__)

class CharForgeHandler:
    """Main handler for CharForge operations with enhanced error handling and recovery"""

    def __init__(self):
        """Initialize the handler"""
        self.image_generator = None
        self.is_initialized = False
        self.setup_environment()
        self.verify_system_requirements()

    def verify_system_requirements(self):
        """Verify system requirements and GPU availability"""
        try:
            gpu_info = check_gpu_availability()
            if not gpu_info.get('cuda_available', False):
                raise RuntimeError("CUDA is not available - GPU required for CharForgex")

            logger.info(f"GPU detected: {gpu_info.get('gpu_name', 'Unknown')}")
            logger.info(f"GPU memory: {gpu_info.get('memory_total', 0) / (1024**3):.1f}GB")

            # Check minimum memory requirements
            min_memory_gb = 20  # Minimum 20GB for basic operations
            available_memory_gb = gpu_info.get('memory_total', 0) / (1024**3)

            if available_memory_gb < min_memory_gb:
                logger.warning(f"GPU memory ({available_memory_gb:.1f}GB) is below recommended minimum ({min_memory_gb}GB)")

            self.is_initialized = True

        except Exception as e:
            logger.error(f"System requirements check failed: {e}")
            raise
        
    def setup_environment(self):
        """Setup environment variables and paths with error handling"""
        # Set up persistent paths
        os.environ['HF_HOME'] = get_persistent_path('huggingface')
        os.environ['APP_PATH'] = '/workspace'

        # Create necessary directories with error handling
        directories = ['models', 'loras', 'datasets', 'outputs']
        for dir_name in directories:
            try:
                path = get_persistent_path(dir_name)
                os.makedirs(path, exist_ok=True)
                logger.info(f"✅ Created directory: {path}")
            except PermissionError:
                # Use fallback directory
                fallback_path = f"/tmp/runpod-volume/{dir_name}"
                try:
                    os.makedirs(fallback_path, exist_ok=True)
                    logger.warning(f"⚠️ Using fallback directory: {fallback_path}")
                except Exception as e:
                    logger.error(f"❌ Failed to create fallback directory {fallback_path}: {e}")
            except Exception as e:
                logger.error(f"❌ Failed to create directory {dir_name}: {e}")

        logger.info("✅ Environment setup completed")
    
    def handle_training(self, job_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle character training requests with enhanced error handling

        Args:
            job_input: Training parameters

        Returns:
            Training results
        """
        training_start_time = time.time()
        character_name = None

        try:
            # Load CharForgex imports when needed
            _load_charforgex_imports()

            # Verify system is ready
            if not self.is_initialized:
                raise RuntimeError("Handler not properly initialized")

            # Clear GPU memory before starting
            clear_gpu_memory()

            # Extract and validate parameters
            character_name = job_input.get('character_name', '').strip()
            input_image_b64 = job_input.get('input_image')

            if not character_name:
                raise ValueError("character_name is required and cannot be empty")
            if not input_image_b64:
                raise ValueError("input_image is required")

            # Sanitize character name for filesystem
            import re
            character_name = re.sub(r'[^\w\-_]', '_', character_name)

            logger.info(f"Starting training for character: {character_name}")

            # Save input image with error handling
            temp_dir = f"/tmp/charforge_{character_name}_{int(time.time())}"
            os.makedirs(temp_dir, exist_ok=True)
            input_image_path = save_base64_image(
                input_image_b64,
                os.path.join(temp_dir, f"{character_name}_input.png")
            )

            # Verify image was saved correctly
            if not os.path.exists(input_image_path):
                raise RuntimeError(f"Failed to save input image to {input_image_path}")

            logger.info(f"Input image saved: {input_image_path}")
            
            # Create character config with validation
            config = CharacterConfig(
                name=character_name,
                input_image=input_image_path,
                work_dir=get_persistent_path(f'datasets/{character_name}'),
                steps=max(100, min(2000, job_input.get('steps', 800))),  # Clamp steps
                batch_size=max(1, min(4, job_input.get('batch_size', 1))),  # Clamp batch size
                learning_rate=max(1e-5, min(1e-2, job_input.get('learning_rate', 8e-4))),  # Clamp LR
                train_dim=job_input.get('train_dim', 512),
                rank_dim=max(4, min(64, job_input.get('rank_dim', 8))),  # Clamp rank
                pulidflux_images=max(0, min(10, job_input.get('pulidflux_images', 0)))  # Clamp pulid images
            )

            logger.info(f"Training configuration: steps={config.steps}, lr={config.learning_rate}, rank={config.rank_dim}")

            # Ensure persistent directories exist
            os.makedirs(config.work_dir, exist_ok=True)
            persistent_lora_dir = get_persistent_path(f'loras/{character_name}')
            os.makedirs(persistent_lora_dir, exist_ok=True)

            # Check available disk space
            import shutil
            free_space_gb = shutil.disk_usage(config.work_dir)[2] / (1024**3)
            if free_space_gb < 10:  # Require at least 10GB free
                raise RuntimeError(f"Insufficient disk space: {free_space_gb:.1f}GB available, need at least 10GB")

            # Run training with progress tracking
            logger.info("Starting character training pipeline...")
            output_dir = build_character(config)

            # Verify training completed successfully
            if not os.path.exists(output_dir):
                raise RuntimeError(f"Training output directory not found: {output_dir}")

            # Find and validate trained LoRA files
            lora_files = []
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if file.endswith('.safetensors') and 'lora' in file.lower():
                        lora_path = os.path.join(root, file)
                        # Verify file is not empty
                        if os.path.getsize(lora_path) > 1024:  # At least 1KB
                            lora_files.append(lora_path)

            if not lora_files:
                raise RuntimeError("No valid LoRA files found after training")

            # Copy LoRA to persistent storage with backup
            import shutil
            lora_file = lora_files[0]  # Take the first valid LoRA file
            persistent_lora_path = os.path.join(persistent_lora_dir, os.path.basename(lora_file))

            # Create backup if file already exists
            if os.path.exists(persistent_lora_path):
                backup_path = f"{persistent_lora_path}.backup_{int(time.time())}"
                shutil.copy2(persistent_lora_path, backup_path)
                logger.info(f"Created backup: {backup_path}")

            shutil.copy2(lora_file, persistent_lora_path)
            logger.info(f"LoRA saved to persistent storage: {persistent_lora_path}")

            # Save training metadata
            metadata = {
                "character_name": character_name,
                "training_time": time.time() - training_start_time,
                "config": {
                    "steps": config.steps,
                    "learning_rate": config.learning_rate,
                    "rank_dim": config.rank_dim,
                    "train_dim": config.train_dim
                },
                "lora_file": os.path.basename(lora_file),
                "created_at": time.time()
            }

            metadata_path = os.path.join(persistent_lora_dir, "training_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            # Cleanup temporary files
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {e}")

            training_time = time.time() - training_start_time

            return {
                "status": "completed",
                "character_name": character_name,
                "output_directory": output_dir,
                "lora_files": [os.path.basename(f) for f in lora_files],
                "persistent_lora_path": persistent_lora_path,
                "training_time_seconds": round(training_time, 2),
                "metadata": metadata,
                "message": f"Training completed successfully for {character_name} in {training_time/60:.1f} minutes"
            }
            
        except Exception as e:
            logger.error(f"Training failed for {character_name}: {e}")
            logger.error(traceback.format_exc())

            # Cleanup on failure
            try:
                if 'temp_dir' in locals() and os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp directory: {cleanup_error}")

            clear_gpu_memory()  # Clear GPU memory on failure

            return {
                "status": "failed",
                "character_name": character_name,
                "error": str(e),
                "training_time_seconds": time.time() - training_start_time if 'training_start_time' in locals() else 0,
                "traceback": traceback.format_exc()
            }

    def handle_inference(self, job_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle image generation requests with enhanced error handling

        Args:
            job_input: Inference parameters

        Returns:
            Generated images
        """
        inference_start_time = time.time()
        character_name = None

        try:
            # Load CharForgex imports when needed
            _load_charforgex_imports()

            # Verify system is ready
            if not self.is_initialized:
                raise RuntimeError("Handler not properly initialized")

            # Extract and validate parameters
            character_name = job_input.get('character_name', '').strip()
            prompt = job_input.get('prompt', '').strip()

            if not character_name:
                raise ValueError("character_name is required and cannot be empty")
            if not prompt:
                raise ValueError("prompt is required and cannot be empty")

            # Sanitize character name
            import re
            character_name = re.sub(r'[^\w\-_]', '_', character_name)

            # Validate character exists
            character_lora_dir = get_persistent_path(f'loras/{character_name}')
            if not os.path.exists(character_lora_dir):
                raise ValueError(f"Character '{character_name}' not found. Available characters: {self.get_available_character_names()}")

            # Initialize image generator if needed with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if self.image_generator is None:
                        face_enhance = job_input.get('face_enhance', False)
                        logger.info(f"Initializing image generator (attempt {attempt + 1}/{max_retries})")
                        self.image_generator = LoRAImageGen(face_enhance=face_enhance)
                        self.image_generator.prepare()
                    break
                except Exception as e:
                    logger.warning(f"Failed to initialize image generator (attempt {attempt + 1}): {e}")
                    if attempt == max_retries - 1:
                        raise RuntimeError(f"Failed to initialize image generator after {max_retries} attempts: {e}")
                    clear_gpu_memory()
                    time.sleep(2)  # Wait before retry

            # Validate and clamp parameters
            params = {
                'character_name': character_name,
                'prompt': prompt,
                'work_dir': get_persistent_path(f'datasets/{character_name}'),
                'lora_weight': max(0.1, min(2.0, job_input.get('lora_weight', 0.73))),
                'test_dim': min(1536, max(512, job_input.get('test_dim', 1024))),  # Clamp dimensions
                'do_optimize_prompt': job_input.get('do_optimize_prompt', True),
                'batch_size': max(1, min(4, job_input.get('batch_size', 1))),  # Clamp batch size
                'num_inference_steps': max(10, min(100, job_input.get('num_inference_steps', 30))),  # Clamp steps
                'fix_outfit': job_input.get('fix_outfit', False),
                'face_enhance': job_input.get('face_enhance', False)
            }

            logger.info(f"Generating images for character: {character_name}")
            logger.info(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            logger.info(f"Parameters: batch_size={params['batch_size']}, steps={params['num_inference_steps']}, size={params['test_dim']}")

            # Generate images with timeout protection
            try:
                generated_files = self.image_generator.generate(**params)
            except Exception as gen_error:
                # Try to recover by clearing memory and retrying once
                logger.warning(f"Generation failed, attempting recovery: {gen_error}")
                clear_gpu_memory()
                self.image_generator = None  # Force reinitialization

                # Retry with reduced parameters
                params['batch_size'] = 1
                params['test_dim'] = min(params['test_dim'], 1024)

                face_enhance = params.pop('face_enhance', False)
                self.image_generator = LoRAImageGen(face_enhance=face_enhance)
                self.image_generator.prepare()

                generated_files = self.image_generator.generate(**params)

            # Validate generated files
            valid_files = []
            for file_path in generated_files:
                if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:  # At least 1KB
                    valid_files.append(file_path)
                else:
                    logger.warning(f"Invalid or empty generated file: {file_path}")

            if not valid_files:
                raise RuntimeError("No valid images were generated")

            # Encode images to base64 with error handling
            images_b64 = []
            for file_path in valid_files:
                try:
                    image_b64 = encode_image_to_base64(file_path)
                    images_b64.append({
                        'filename': os.path.basename(file_path),
                        'image_data': image_b64,
                        'size_bytes': os.path.getsize(file_path)
                    })
                except Exception as e:
                    logger.warning(f"Failed to encode image {file_path}: {e}")

            if not images_b64:
                raise RuntimeError("Failed to encode any generated images")

            inference_time = time.time() - inference_start_time

            return {
                "status": "completed",
                "character_name": character_name,
                "prompt": prompt,
                "images": images_b64,
                "num_images": len(images_b64),
                "inference_time_seconds": round(inference_time, 2),
                "parameters_used": params,
                "message": f"Generated {len(images_b64)} images successfully in {inference_time:.1f}s"
            }

        except Exception as e:
            logger.error(f"Inference failed for {character_name}: {e}")
            logger.error(traceback.format_exc())

            # Cleanup on failure
            clear_gpu_memory()

            inference_time = time.time() - inference_start_time

            return {
                "status": "failed",
                "character_name": character_name,
                "error": str(e),
                "inference_time_seconds": round(inference_time, 2),
                "traceback": traceback.format_exc()
            }

    def list_characters(self) -> Dict[str, Any]:
        """List available trained characters with metadata"""
        try:
            characters = []
            loras_dir = get_persistent_path('loras')

            if os.path.exists(loras_dir):
                for character_dir in os.listdir(loras_dir):
                    character_path = os.path.join(loras_dir, character_dir)
                    if os.path.isdir(character_path):
                        # Check for LoRA files
                        lora_files = [f for f in os.listdir(character_path)
                                     if f.endswith('.safetensors')]

                        if lora_files:
                            # Load metadata if available
                            metadata_path = os.path.join(character_path, "training_metadata.json")
                            metadata = {}
                            if os.path.exists(metadata_path):
                                try:
                                    with open(metadata_path, 'r') as f:
                                        metadata = json.load(f)
                                except Exception as e:
                                    logger.warning(f"Failed to load metadata for {character_dir}: {e}")

                            # Get file sizes
                            total_size = sum(os.path.getsize(os.path.join(character_path, f))
                                           for f in lora_files)

                            characters.append({
                                'name': character_dir,
                                'lora_files': lora_files,
                                'path': character_path,
                                'metadata': metadata,
                                'total_size_mb': round(total_size / (1024*1024), 2),
                                'created_at': metadata.get('created_at'),
                                'training_config': metadata.get('config', {})
                            })

            # Sort by creation time (newest first)
            characters.sort(key=lambda x: x.get('created_at', 0), reverse=True)

            return {
                "status": "completed",
                "characters": characters,
                "count": len(characters),
                "total_size_mb": sum(c['total_size_mb'] for c in characters)
            }

        except Exception as e:
            logger.error(f"Failed to list characters: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def get_available_character_names(self) -> List[str]:
        """Get list of available character names"""
        try:
            result = self.list_characters()
            if result['status'] == 'completed':
                return [char['name'] for char in result['characters']]
            return []
        except Exception:
            return []

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            gpu_info = check_gpu_availability()

            # Get storage info
            storage_info = {}
            try:
                import shutil
                total, used, free = shutil.disk_usage(get_persistent_path())
                storage_info = {
                    'total_gb': round(total / (1024**3), 2),
                    'used_gb': round(used / (1024**3), 2),
                    'free_gb': round(free / (1024**3), 2),
                    'usage_percent': round((used / total) * 100, 1)
                }
            except Exception as e:
                storage_info = {'error': str(e)}

            # Get character count
            characters_result = self.list_characters()
            character_count = characters_result.get('count', 0) if characters_result['status'] == 'completed' else 0

            return {
                "status": "healthy",
                "gpu_info": gpu_info,
                "storage_info": storage_info,
                "character_count": character_count,
                "image_generator_loaded": self.image_generator is not None,
                "system_initialized": self.is_initialized,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
