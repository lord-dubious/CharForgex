#!/usr/bin/env python3
"""
CharForgex RunPod Worker Startup Script
Handles initialization, GUI serving, and worker startup
"""

import os
import sys
import time
import threading
import subprocess
import logging
from pathlib import Path

# Add workspace to Python path
sys.path.insert(0, '/workspace')

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def serve_gui():
    """Serve the GUI on port 8000"""
    try:
        import http.server
        import socketserver
        import os
        
        # Change to GUI directory
        gui_dir = '/workspace/runpod_worker/gui'
        os.chdir(gui_dir)
        
        # Create simple HTTP server
        PORT = 8000
        Handler = http.server.SimpleHTTPRequestHandler
        
        with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
            print(f"🌐 GUI server running at http://0.0.0.0:{PORT}")
            httpd.serve_forever()
            
    except Exception as e:
        print(f"❌ Failed to start GUI server: {e}")

def check_environment():
    """Check and setup environment"""
    print("🔍 Checking environment...")
    
    # Check GPU availability
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"✅ GPU detected: {gpu_name} ({gpu_memory:.1f}GB)")
        else:
            print("⚠️ No GPU detected - some features may not work")
    except ImportError:
        print("⚠️ PyTorch not available")
    
    # Check persistent storage
    volume_path = '/runpod-volume'
    if os.path.exists(volume_path):
        try:
            import shutil
            total, used, free = shutil.disk_usage(volume_path)
            print(f"💾 Storage: {free/(1024**3):.1f}GB free / {total/(1024**3):.1f}GB total")
        except Exception as e:
            print(f"⚠️ Storage check failed: {e}")
    else:
        print("⚠️ Persistent volume not mounted - creating local directories")
        os.makedirs('/runpod-volume/huggingface', exist_ok=True)
        os.makedirs('/runpod-volume/loras', exist_ok=True)
        os.makedirs('/runpod-volume/datasets', exist_ok=True)
        os.makedirs('/runpod-volume/outputs', exist_ok=True)
    
    # Set environment variables
    env_vars = {
        'HF_HOME': '/runpod-volume/huggingface',
        'COMFYUI_PATH': '/workspace/ComfyUI',
        'APP_PATH': '/workspace',
        'PLATFORM': 'serverless',
        'PYTHONPATH': '/workspace'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Environment setup complete")

def start_worker():
    """Start the main RunPod worker"""
    print("🚀 Starting CharForgex RunPod worker...")
    
    # Change to workspace directory
    os.chdir('/workspace')
    
    # Activate virtual environment
    activate_script = '/workspace/.venv/bin/activate'
    if os.path.exists(activate_script):
        # Source the virtual environment
        import subprocess
        result = subprocess.run([
            'bash', '-c', 
            f'source {activate_script} && python runpod_worker/worker.py'
        ], cwd='/workspace')
    else:
        # Run directly if no venv
        import worker
        # This will start the RunPod serverless worker

def main():
    """Main startup function"""
    setup_logging()
    print("🎬 Starting CharForgex RunPod Worker...")
    
    # Check environment
    check_environment()
    
    # Determine startup mode
    startup_mode = os.environ.get('STARTUP_MODE', 'worker')
    
    if startup_mode == 'gui':
        # Start GUI server only
        print("🌐 Starting in GUI mode...")
        serve_gui()
    elif startup_mode == 'both':
        # Start both GUI and worker
        print("🔄 Starting in combined mode...")
        
        # Start GUI in background thread
        gui_thread = threading.Thread(target=serve_gui, daemon=True)
        gui_thread.start()
        
        # Give GUI time to start
        time.sleep(2)
        
        # Start worker in main thread
        start_worker()
    else:
        # Default: Start worker only
        print("⚡ Starting in worker mode...")
        start_worker()

if __name__ == "__main__":
    main()
