#!/usr/bin/env python3
"""
CharForgex RunPod Serverless Worker
Seamless serverless worker following RunPod patterns
"""

import runpod
import os
import sys
import logging
import time
from typing import Dict, Any, Optional
import traceback
import json

# Add workspace to Python path
sys.path.insert(0, '/workspace')
sys.path.insert(0, '/workspace/runpod_worker')

# Import with fallback for different environments
try:
    from handler import CharForgeHandler
    from utils import setup_logging, ensure_directories, cleanup_temp_files
except ImportError:
    # Try relative imports
    try:
        from runpod_worker.handler import CharForgeHandler
        from runpod_worker.utils import setup_logging, ensure_directories, cleanup_temp_files
    except ImportError:
        # Try absolute imports from current directory
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        from handler import CharForgeHandler
        from utils import setup_logging, ensure_directories, cleanup_temp_files

# Configure logging for RunPod
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global handler instance for reuse across requests
charforge_handler = None

def initialize_handler():
    """Initialize the CharForge handler with error handling"""
    global charforge_handler
    try:
        if charforge_handler is None:
            logger.info("🚀 Initializing CharForge handler...")
            charforge_handler = CharForgeHandler()
            logger.info("✅ Handler initialized successfully")
        return charforge_handler
    except Exception as e:
        logger.error(f"❌ Failed to initialize handler: {e}")
        logger.error(traceback.format_exc())
        raise

def handler(job):
    """
    RunPod serverless handler function - CORRECTED to match RunPod documentation

    Args:
        job: RunPod job dictionary containing input parameters

    Returns:
        Result data (not wrapped in additional dict)
    """
    start_time = time.time()

    try:
        # Validate job input
        if not isinstance(job, dict):
            raise ValueError("Job must be a dictionary")

        # Ensure required directories exist
        ensure_directories()

        # Extract input from job - RunPod passes job with 'input' key
        job_input = job.get("input", {})

        # Validate job_input
        if not isinstance(job_input, dict):
            raise ValueError("Job input must be a dictionary")

        # Default operation for backward compatibility
        operation = job_input.get("operation", "inference")

        logger.info(f"🔄 Processing {operation} request")

        # Initialize handler if needed
        current_handler = initialize_handler()

        # Route to appropriate operation
        if operation == "inference" or operation == "generate":
            # Support both 'inference' and 'generate' for compatibility
            result = current_handler.handle_inference(job_input)
        elif operation == "training" or operation == "train":
            # Support both 'training' and 'train' for compatibility
            result = current_handler.handle_training(job_input)
        elif operation == "list_characters" or operation == "list":
            result = current_handler.list_characters()
        elif operation == "health_check" or operation == "health":
            result = current_handler.get_system_status()
        elif operation == "system_status" or operation == "status":
            result = current_handler.get_system_status()
        elif operation == "clear_cache" or operation == "clear":
            cleanup_temp_files()
            from utils import clear_gpu_memory
            clear_gpu_memory()
            result = {"status": "completed", "message": "Cache cleared successfully"}
        else:
            # If no operation specified, try to infer from input
            if "prompt" in job_input and "character_name" in job_input:
                result = current_handler.handle_inference(job_input)
            elif "character_name" in job_input and "input_image" in job_input:
                result = current_handler.handle_training(job_input)
            else:
                raise ValueError(f"Unknown operation: {operation}. Available: inference, training, list_characters, health_check, system_status, clear_cache")

        # Cleanup temporary files after successful operation
        cleanup_temp_files()

        # Add execution time to result
        execution_time = time.time() - start_time
        if isinstance(result, dict):
            result["execution_time"] = round(execution_time, 2)

        logger.info(f"✅ Request completed successfully: {operation} ({execution_time:.2f}s)")

        # Return result directly - RunPod wraps it automatically
        return result

    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Error processing request: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(traceback.format_exc())

        # Cleanup on error
        cleanup_temp_files()

        # Return error - RunPod will handle the wrapping
        return {
            "error": error_msg,
            "execution_time": round(execution_time, 2)
        }

def main():
    """Main entry point for RunPod serverless worker"""
    logger.info("🚀 Starting CharForgex RunPod Serverless Worker")

    # Log environment info
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")

    # Check GPU availability
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"🎮 GPU detected: {gpu_name} ({gpu_memory:.1f}GB)")
        else:
            logger.warning("⚠️ No GPU detected")
    except ImportError:
        logger.warning("⚠️ PyTorch not available")

    # Verify environment
    logger.info("🔍 Checking environment...")

    # Check for persistent storage
    if os.path.exists('/runpod-volume'):
        logger.info("💾 Persistent storage detected")
    else:
        logger.warning("⚠️ No persistent storage - creating local directories")

    # Initialize directories
    ensure_directories()

    # Start RunPod serverless worker - CORRECTED to match documentation
    logger.info("🌟 Starting RunPod serverless worker...")

    runpod.serverless.start(handler)

if __name__ == "__main__":
    main()
