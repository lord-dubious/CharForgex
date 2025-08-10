#!/bin/bash
set -e

echo "🚀 CharForgex RunPod - One-Click Deployment"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "train_character.py" ]; then
    print_error "Please run this script from the CharForgex root directory"
    exit 1
fi

# Welcome message
echo "This script will:"
echo "1. Build your CharForgex Docker image"
echo "2. Push it to Docker Hub (requires login)"
echo "3. Create RunPod template and endpoint"
echo "4. Set up persistent storage"
echo "5. Test the deployment"
echo ""

# Get user inputs
read -p "Enter your Docker Hub username: " DOCKER_USERNAME
if [ -z "$DOCKER_USERNAME" ]; then
    print_error "Docker Hub username is required"
    exit 1
fi

read -s -p "Enter your Docker Hub password/token: " DOCKER_PASSWORD
echo ""
if [ -z "$DOCKER_PASSWORD" ]; then
    print_error "Docker Hub password is required"
    exit 1
fi

read -p "Enter your RunPod API key: " RUNPOD_API_KEY
if [ -z "$RUNPOD_API_KEY" ]; then
    print_error "RunPod API key is required"
    print_info "Get it from: https://console.runpod.io/user/settings"
    exit 1
fi

# Optional: Custom image name
read -p "Enter custom image name (or press Enter for 'charforgex-runpod'): " IMAGE_NAME
if [ -z "$IMAGE_NAME" ]; then
    IMAGE_NAME="charforgex-runpod"
fi

# Set environment variables
export DOCKER_REGISTRY="docker.io/$DOCKER_USERNAME"
export DOCKER_USERNAME="$DOCKER_USERNAME"
export DOCKER_PASSWORD="$DOCKER_PASSWORD"
export RUNPOD_API_KEY="$RUNPOD_API_KEY"

print_step "Starting automated deployment..."

# Step 1: Build and push Docker image
print_step "Building Docker image..."
IMAGE_TAG="$DOCKER_USERNAME/$IMAGE_NAME:latest"

docker build -t "$IMAGE_TAG" -f runpod_worker/Dockerfile .

if [ $? -ne 0 ]; then
    print_error "Docker build failed"
    exit 1
fi

print_success "Docker image built: $IMAGE_TAG"

# Step 2: Push to Docker Hub
print_step "Pushing to Docker Hub..."
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

docker push "$IMAGE_TAG"

if [ $? -ne 0 ]; then
    print_error "Docker push failed"
    exit 1
fi

print_success "Image pushed to Docker Hub: $IMAGE_TAG"

# Step 3: Deploy to RunPod
print_step "Deploying to RunPod..."

# Create a temporary Python script for deployment
cat > /tmp/deploy_charforgex.py << EOF
import os
import sys
import requests
import json
import time

def create_network_volume(api_key, name="charforgex-storage", size=200):
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    
    # Check existing volumes
    response = requests.post('https://api.runpod.ai/graphql', headers=headers, json={
        'query': 'query { myself { networkVolumes { id name size } } }'
    })
    
    if response.status_code == 200:
        volumes = response.json().get('data', {}).get('myself', {}).get('networkVolumes', [])
        for volume in volumes:
            if volume['name'] == name:
                print(f"✅ Using existing volume: {volume['id']}")
                return volume['id']
    
    # Create new volume
    response = requests.post('https://api.runpod.ai/graphql', headers=headers, json={
        'query': '''
        mutation(\$input: NetworkVolumeInput!) {
            createNetworkVolume(input: \$input) { id name }
        }
        ''',
        'variables': {'input': {'name': name, 'size': size, 'dataCenterId': 'US-OR-1'}}
    })
    
    if response.status_code == 200:
        result = response.json()
        if 'errors' not in result:
            volume_id = result['data']['createNetworkVolume']['id']
            print(f"✅ Created volume: {volume_id}")
            return volume_id
    
    print("❌ Failed to create volume")
    return None

def create_template(api_key, image_name, volume_id=None):
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    
    config = {
        'name': 'CharForgex Worker',
        'imageName': image_name,
        'containerDiskInGb': 50,
        'volumeMountPath': '/runpod-volume',
        'ports': '8000/http',
        'env': [
            {'key': 'PLATFORM', 'value': 'serverless'},
            {'key': 'HF_HOME', 'value': '/runpod-volume/huggingface'},
            {'key': 'COMFYUI_PATH', 'value': '/workspace/ComfyUI'},
            {'key': 'APP_PATH', 'value': '/workspace'}
        ]
    }
    
    if volume_id:
        config['networkVolumeId'] = volume_id
    else:
        config['volumeInGb'] = 200
    
    response = requests.post('https://api.runpod.ai/graphql', headers=headers, json={
        'query': '''
        mutation(\$input: SaveTemplateInput!) {
            saveTemplate(input: \$input) { id name }
        }
        ''',
        'variables': {'input': config}
    })
    
    if response.status_code == 200:
        result = response.json()
        if 'errors' not in result:
            template_id = result['data']['saveTemplate']['id']
            print(f"✅ Created template: {template_id}")
            return template_id
    
    print("❌ Failed to create template")
    return None

def create_endpoint(api_key, template_id, name="CharForgex"):
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    
    config = {
        'name': name,
        'templateId': template_id,
        'gpuIds': 'NVIDIA RTX A5000,NVIDIA RTX A6000,NVIDIA GeForce RTX 4090',
        'idleTimeout': 5,
        'maxWorkers': 3,
        'flashBoot': True
    }
    
    response = requests.post('https://api.runpod.ai/graphql', headers=headers, json={
        'query': '''
        mutation(\$input: EndpointInput!) {
            createEndpoint(input: \$input) { id name }
        }
        ''',
        'variables': {'input': config}
    })
    
    if response.status_code == 200:
        result = response.json()
        if 'errors' not in result:
            endpoint_id = result['data']['createEndpoint']['id']
            print(f"✅ Created endpoint: {endpoint_id}")
            return endpoint_id
    
    print("❌ Failed to create endpoint")
    return None

# Main deployment
api_key = "$RUNPOD_API_KEY"
image_name = "$IMAGE_TAG"

print("🔄 Creating network volume...")
volume_id = create_network_volume(api_key)

print("🔄 Creating template...")
template_id = create_template(api_key, image_name, volume_id)

if template_id:
    print("🔄 Creating endpoint...")
    endpoint_id = create_endpoint(api_key, template_id)
    
    if endpoint_id:
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    🎉 Deployment Complete!                   ║
╚══════════════════════════════════════════════════════════════╝

Your CharForgex RunPod worker is ready!

📋 Details:
   • Endpoint ID: {endpoint_id}
   • URL: https://api.runpod.ai/v2/{endpoint_id}/runsync
   • GUI: Access via port 8000

⚠️ Important - Set these environment variables in RunPod console:
   • HF_TOKEN=your_huggingface_token
   • CIVITAI_API_KEY=your_civitai_key  
   • GOOGLE_API_KEY=your_google_genai_key
   • FAL_KEY=your_fal_ai_key

🧪 Test your deployment:
python3 runpod_worker/test_worker.py https://api.runpod.ai/v2/{endpoint_id}/runsync YOUR_API_KEY

🌐 Use the GUI:
cd runpod_worker/gui && python3 -m http.server 8080
Then open: http://localhost:8080
        """)
        
        # Save deployment info
        with open('runpod_worker/deployment_info.json', 'w') as f:
            json.dump({
                'endpoint_id': endpoint_id,
                'template_id': template_id,
                'volume_id': volume_id,
                'image_name': image_name,
                'deployment_time': time.time()
            }, f, indent=2)
        
        print("💾 Deployment info saved to: runpod_worker/deployment_info.json")
    else:
        sys.exit(1)
else:
    sys.exit(1)
EOF

# Run the deployment script
python3 /tmp/deploy_charforgex.py

# Cleanup
rm /tmp/deploy_charforgex.py

print_success "🎉 One-click deployment complete!"
print_info "Don't forget to set your API keys in the RunPod endpoint environment variables!"
