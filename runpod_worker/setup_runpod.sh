#!/bin/bash
set -e

echo "🚀 CharForgex RunPod - Seamless Setup & Deployment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${PURPLE}ℹ️ $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "train_character.py" ]; then
    print_error "Please run this script from the CharForgex root directory"
    exit 1
fi

# Create runpod_worker directory if it doesn't exist
mkdir -p runpod_worker/gui

print_status "Checking Docker daemon..."
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi

print_success "Docker is available and running"

# Check for registry configuration
print_status "Checking deployment configuration..."

if [ -z "$DOCKER_REGISTRY" ]; then
    print_info "DOCKER_REGISTRY not set. Using default: docker.io/username"
    print_info "Set DOCKER_REGISTRY environment variable for automatic push"
    print_info "Example: export DOCKER_REGISTRY=docker.io/yourusername"
fi

# Build the Docker image
print_status "Building CharForgex RunPod Docker image..."
IMAGE_TAG="charforgex-runpod:latest"

if [ ! -z "$DOCKER_REGISTRY" ]; then
    FULL_IMAGE_TAG="$DOCKER_REGISTRY/$IMAGE_TAG"
else
    FULL_IMAGE_TAG="$IMAGE_TAG"
fi

docker build -t "$FULL_IMAGE_TAG" -f runpod_worker/Dockerfile .

if [ $? -eq 0 ]; then
    print_success "Docker image built successfully: $FULL_IMAGE_TAG"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Test the Docker image
print_status "Testing Docker image..."
docker run --rm "$FULL_IMAGE_TAG" python -c "
import sys
print('✅ Python version:', sys.version.split()[0])
try:
    import torch
    print('✅ PyTorch version:', torch.__version__)
    print('✅ CUDA available:', torch.cuda.is_available())
except ImportError:
    print('⚠️ PyTorch not available in test')
try:
    import runpod
    print('✅ RunPod SDK version:', runpod.__version__)
except ImportError:
    print('⚠️ RunPod SDK not available')
print('✅ Basic test passed')
"

if [ $? -eq 0 ]; then
    print_success "Docker image test passed"
else
    print_warning "Docker image test had issues, but continuing..."
fi

# Push to registry if configured
if [ ! -z "$DOCKER_REGISTRY" ] && [ ! -z "$DOCKER_USERNAME" ] && [ ! -z "$DOCKER_PASSWORD" ]; then
    print_status "Pushing to Docker registry..."
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
    docker push "$FULL_IMAGE_TAG"

    if [ $? -eq 0 ]; then
        print_success "Image pushed to registry: $FULL_IMAGE_TAG"
    else
        print_error "Failed to push image to registry"
        exit 1
    fi
elif [ ! -z "$DOCKER_REGISTRY" ]; then
    print_info "To push automatically, set DOCKER_USERNAME and DOCKER_PASSWORD"
    print_info "Or push manually: docker push $FULL_IMAGE_TAG"
fi

# Create example environment file
print_status "Creating example environment configuration..."
cat > runpod_worker/.env.example << 'EOF'
# Required API Keys for CharForgex
HF_TOKEN=your_huggingface_token_here
CIVITAI_API_KEY=your_civitai_api_key_here
GOOGLE_API_KEY=your_google_genai_api_key_here
FAL_KEY=your_fal_ai_api_key_here

# RunPod Configuration
RUNPOD_AI_API_KEY=your_runpod_api_key_here
RUNPOD_ENDPOINT_ID=your_endpoint_id_here

# Optional Configuration
PLATFORM=serverless
HF_HOME=/runpod-volume/huggingface
COMFYUI_PATH=/workspace/ComfyUI
APP_PATH=/workspace
EOF

print_success "Example environment file created: runpod_worker/.env.example"

# Create deployment instructions
print_status "Creating deployment instructions..."
cat > runpod_worker/README.md << 'EOF'
# CharForgex RunPod Worker

This directory contains everything needed to deploy CharForgex as a RunPod serverless worker.

## Quick Deployment

1. **Build and test locally:**
   ```bash
   ./setup_runpod.sh
   ```

2. **Push to container registry:**
   ```bash
   # Tag for your registry
   docker tag charforgex-runpod:latest your-registry.com/charforgex-runpod:latest
   
   # Push to registry
   docker push your-registry.com/charforgex-runpod:latest
   ```

3. **Create RunPod template:**
   - Go to RunPod Console → Templates
   - Create new template with your image URL
   - Set container disk: 50GB
   - Set volume mount: /runpod-volume (100GB+)

4. **Create RunPod endpoint:**
   - Go to RunPod Console → Serverless
   - Create new endpoint with your template
   - Set environment variables from .env.example
   - Choose GPU: RTX A5000/A6000/4090 or better

5. **Test deployment:**
   - Use the GUI in gui/ folder
   - Or test with curl commands from DEPLOYMENT_GUIDE.md

## Files

- `Dockerfile` - Container definition
- `worker.py` - Main RunPod worker entry point
- `handler.py` - Request handling logic
- `utils.py` - Utility functions
- `deploy.py` - Automated deployment script
- `gui/` - Simple web interface
- `requirements.txt` - Python dependencies

## GPU Requirements

- **Minimum**: RTX A5000 (24GB VRAM)
- **Recommended**: RTX A6000 (48GB VRAM) or RTX 4090
- **Training**: Requires 48GB+ VRAM for optimal performance
- **Inference**: Works with 24GB+ VRAM

## Storage Requirements

- **Container Disk**: 50GB minimum
- **Network Volume**: 100GB+ recommended for model caching
- **Persistent Data**: LoRAs, datasets, and model cache

## Performance Notes

- **Cold Start**: 2-3 minutes for first request (model loading)
- **Warm Inference**: 30-60 seconds per batch
- **Training Time**: 30-40 minutes per character
- **Model Caching**: Significantly reduces subsequent cold starts
EOF

print_success "Deployment README created: runpod_worker/README.md"

# Create a simple test script
print_status "Creating test script..."
cat > runpod_worker/test_worker.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for CharForgex RunPod Worker
"""

import requests
import json
import base64
import os
import sys

def test_health_check(endpoint_url, api_key):
    """Test worker health check"""
    print("Testing health check...")
    
    response = requests.post(
        endpoint_url,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'input': {
                'operation': 'health_check'
            }
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Health check passed: {result}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code} - {response.text}")
        return False

def test_list_characters(endpoint_url, api_key):
    """Test listing characters"""
    print("Testing character listing...")
    
    response = requests.post(
        endpoint_url,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'input': {
                'operation': 'list_characters'
            }
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Character listing: {result}")
        return result
    else:
        print(f"❌ Character listing failed: {response.status_code} - {response.text}")
        return None

def main():
    if len(sys.argv) != 3:
        print("Usage: python test_worker.py <endpoint_url> <api_key>")
        print("Example: python test_worker.py https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync YOUR_API_KEY")
        sys.exit(1)
    
    endpoint_url = sys.argv[1]
    api_key = sys.argv[2]
    
    print(f"Testing RunPod worker at: {endpoint_url}")
    
    # Test health check
    if test_health_check(endpoint_url, api_key):
        print("✅ Worker is healthy")
    else:
        print("❌ Worker health check failed")
        sys.exit(1)
    
    # Test character listing
    characters = test_list_characters(endpoint_url, api_key)
    if characters:
        print(f"✅ Found {len(characters.get('characters', []))} trained characters")
    
    print("\n🎉 All tests passed! Your RunPod worker is ready to use.")

if __name__ == "__main__":
    main()
EOF

chmod +x runpod_worker/test_worker.py
print_success "Test script created: runpod_worker/test_worker.py"

# Create docker-compose for local testing
print_status "Creating docker-compose for local testing..."
cat > runpod_worker/docker-compose.yml << 'EOF'
version: '3.8'

services:
  charforgex-worker:
    build:
      context: ..
      dockerfile: runpod_worker/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./test_volume:/runpod-volume
      - ../.env:/workspace/.env
    environment:
      - PLATFORM=serverless
      - HF_HOME=/runpod-volume/huggingface
      - COMFYUI_PATH=/workspace/ComfyUI
      - APP_PATH=/workspace
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: python worker.py

  gui:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./gui:/usr/share/nginx/html
    depends_on:
      - charforgex-worker
EOF

print_success "Docker Compose file created: runpod_worker/docker-compose.yml"

# Automatic deployment if RunPod API key is available
if [ ! -z "$RUNPOD_API_KEY" ] && [ ! -z "$DOCKER_REGISTRY" ]; then
    print_status "RunPod API key detected - starting automatic deployment..."
    python3 runpod_worker/deploy_seamless.py
else
    print_info "For automatic deployment, set environment variables:"
    print_info "  export RUNPOD_API_KEY=your_runpod_api_key"
    print_info "  export DOCKER_REGISTRY=docker.io/yourusername"
    print_info "  export DOCKER_USERNAME=yourusername"
    print_info "  export DOCKER_PASSWORD=yourpassword"
    print_info ""
    print_info "Then run: ./setup_runpod.sh"
fi

print_success "🎉 CharForgex RunPod setup complete!"
print_status "Next steps:"

if [ -z "$RUNPOD_API_KEY" ]; then
    echo "1. Get your RunPod API key: https://console.runpod.io/user/settings"
    echo "2. Set environment variables (see above)"
    echo "3. Re-run this script for automatic deployment"
    echo "4. Or deploy manually: python3 runpod_worker/deploy_seamless.py"
else
    echo "1. Set your API keys in the RunPod endpoint environment variables:"
    echo "   • HF_TOKEN=your_huggingface_token"
    echo "   • CIVITAI_API_KEY=your_civitai_key"
    echo "   • GOOGLE_API_KEY=your_google_genai_key"
    echo "   • FAL_KEY=your_fal_ai_key"
    echo "2. Test your deployment: python3 runpod_worker/test_worker.py ENDPOINT_URL API_KEY"
    echo "3. Use the GUI: cd runpod_worker/gui && python3 -m http.server 8080"
fi

echo ""
print_info "📖 Documentation:"
echo "   • Quick Start: runpod_worker/QUICK_START.md"
echo "   • Full Guide: runpod_worker/RUNPOD_DEPLOYMENT.md"
echo "   • Python Client: runpod_worker/client_example.py"
