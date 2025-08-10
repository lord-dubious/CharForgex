#!/bin/bash
set -e

echo "🚀 Starting CharForgex RunPod Worker..."

# Activate virtual environment
cd /workspace
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️ No virtual environment found, using system Python"
fi

# Set environment variables
export PYTHONPATH="/workspace:/workspace/runpod_worker:$PYTHONPATH"
export HF_HOME="/runpod-volume/huggingface"
export COMFYUI_PATH="/workspace/ComfyUI"
export APP_PATH="/workspace"
export PLATFORM="serverless"

# Create directories if they don't exist
mkdir -p /runpod-volume/huggingface /runpod-volume/loras /runpod-volume/datasets /runpod-volume/outputs

# Check GPU availability
python -c "
import torch
print(f'🎮 CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'🎮 GPU: {torch.cuda.get_device_name(0)}')
    print(f'🎮 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB')
" || echo "⚠️ GPU check failed, continuing..."

# Start the appropriate service based on environment
STARTUP_MODE=${STARTUP_MODE:-worker}

if [ "$STARTUP_MODE" = "gui" ]; then
    echo "🌐 Starting GUI web server..."
    python -u runpod_worker/web_server.py --port 8000
elif [ "$STARTUP_MODE" = "both" ]; then
    echo "🔄 Starting both GUI and worker..."
    # Start GUI in background
    python -u runpod_worker/web_server.py --port 8000 &
    # Start worker in foreground
    python -u runpod_worker/worker.py
else
    echo "🔄 Starting RunPod worker..."
    python -u runpod_worker/worker.py
fi
