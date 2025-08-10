#!/usr/bin/env python3
"""
CharForgex RunPod Deployment Script
Automates the deployment of CharForgex as a RunPod serverless worker
"""

import os
import sys
import json
import subprocess
import argparse
from typing import Dict, Any, Optional

def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command with error handling"""
    print(f"🔄 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    
    return result

def build_docker_image(tag: str = "charforgex-runpod"):
    """Build the Docker image for RunPod"""
    print("🐳 Building Docker image...")
    
    # Build the image
    run_command(f"docker build -t {tag} -f runpod_worker/Dockerfile .")
    
    print(f"✅ Docker image '{tag}' built successfully")
    return tag

def push_to_registry(image_tag: str, registry_url: Optional[str] = None):
    """Push Docker image to container registry"""
    if not registry_url:
        print("⚠️ No registry URL provided, skipping push")
        return image_tag
    
    print(f"📤 Pushing image to registry: {registry_url}")
    
    # Tag for registry
    registry_tag = f"{registry_url}/{image_tag}"
    run_command(f"docker tag {image_tag} {registry_tag}")
    
    # Push to registry
    run_command(f"docker push {registry_tag}")
    
    print(f"✅ Image pushed to registry: {registry_tag}")
    return registry_tag

def create_runpod_template(image_url: str, template_name: str = "CharForgex Worker") -> Dict[str, Any]:
    """Create RunPod template configuration"""
    template_config = {
        "name": template_name,
        "imageName": image_url,
        "dockerArgs": "",
        "containerDiskInGb": 50,
        "volumeInGb": 100,
        "volumeMountPath": "/runpod-volume",
        "ports": "8000/http",
        "env": [
            {
                "key": "PLATFORM",
                "value": "serverless"
            },
            {
                "key": "HF_HOME",
                "value": "/runpod-volume/huggingface"
            },
            {
                "key": "COMFYUI_PATH",
                "value": "/workspace/ComfyUI"
            },
            {
                "key": "APP_PATH",
                "value": "/workspace"
            }
        ],
        "startJupyter": False,
        "startSsh": False
    }
    
    return template_config

def create_endpoint_config(template_id: str, endpoint_name: str = "CharForgex Endpoint") -> Dict[str, Any]:
    """Create RunPod endpoint configuration"""
    endpoint_config = {
        "name": endpoint_name,
        "template_id": template_id,
        "gpu_ids": "NVIDIA RTX A5000,NVIDIA RTX A6000,NVIDIA GeForce RTX 4090",
        "network_volume_id": None,  # Will be set if network volume is created
        "locations": "US,EU",
        "idle_timeout": 5,
        "max_workers": 3,
        "flashboot": True,
        "env": {
            "HF_TOKEN": "${HF_TOKEN}",
            "CIVITAI_API_KEY": "${CIVITAI_API_KEY}",
            "GOOGLE_API_KEY": "${GOOGLE_API_KEY}",
            "FAL_KEY": "${FAL_KEY}"
        }
    }
    
    return endpoint_config

def generate_deployment_guide(endpoint_id: str, image_url: str):
    """Generate deployment guide with instructions"""
    guide = f"""
# CharForgex RunPod Deployment Guide

## Deployment Summary
- **Docker Image**: {image_url}
- **Endpoint ID**: {endpoint_id}
- **GPU Requirements**: RTX A5000/A6000/4090 or better
- **Storage**: 50GB container + 100GB network volume

## Environment Variables Required
Set these in your RunPod endpoint configuration:

```bash
HF_TOKEN=your_huggingface_token
CIVITAI_API_KEY=your_civitai_key  
GOOGLE_API_KEY=your_google_genai_key
FAL_KEY=your_fal_ai_key
```

## API Usage Examples

### Health Check
```bash
curl -X POST https://api.runpod.ai/v2/{endpoint_id}/runsync \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"input": {{"operation": "health_check"}}}}'
```

### Train Character
```bash
curl -X POST https://api.runpod.ai/v2/{endpoint_id}/run \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "input": {{
      "operation": "training",
      "character_name": "my_character",
      "input_image": "base64_encoded_image_data",
      "steps": 800,
      "learning_rate": 8e-4,
      "rank_dim": 8
    }}
  }}'
```

### Generate Images
```bash
curl -X POST https://api.runpod.ai/v2/{endpoint_id}/runsync \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "input": {{
      "operation": "inference",
      "character_name": "my_character",
      "prompt": "portrait of my_character, detailed face, high quality",
      "lora_weight": 0.73,
      "test_dim": 1024,
      "batch_size": 1
    }}
  }}'
```

## GUI Access
Open the included GUI by serving the files in `runpod_worker/gui/`:
```bash
cd runpod_worker/gui
python -m http.server 8080
```

Then navigate to http://localhost:8080 and configure your endpoint URL and API key.

## Persistent Storage
- **LoRAs**: Stored in `/runpod-volume/loras/`
- **Models**: Cached in `/runpod-volume/huggingface/`
- **Datasets**: Stored in `/runpod-volume/datasets/`
- **Outputs**: Saved in `/runpod-volume/outputs/`

## Monitoring
- Check logs in RunPod console
- Use health_check operation to verify worker status
- Monitor GPU memory usage during training/inference

## Troubleshooting
1. **Cold Start Issues**: First request may take 2-3 minutes to load models
2. **Memory Issues**: Reduce batch_size or image dimensions
3. **Training Failures**: Check that all API keys are properly set
4. **Network Issues**: Ensure network volume is properly mounted

## Cost Optimization
- Use spot instances for training (non-critical workloads)
- Set appropriate idle_timeout to minimize costs
- Use network volumes to avoid re-downloading models
- Monitor usage in RunPod billing dashboard
"""
    
    with open('runpod_worker/DEPLOYMENT_GUIDE.md', 'w') as f:
        f.write(guide)
    
    print("📖 Deployment guide created: runpod_worker/DEPLOYMENT_GUIDE.md")

def main():
    parser = argparse.ArgumentParser(description="Deploy CharForgex to RunPod")
    parser.add_argument("--registry", type=str, help="Container registry URL (e.g., your-registry.com/username)")
    parser.add_argument("--tag", type=str, default="charforgex-runpod", help="Docker image tag")
    parser.add_argument("--endpoint-name", type=str, default="CharForgex", help="RunPod endpoint name")
    parser.add_argument("--build-only", action="store_true", help="Only build Docker image, don't deploy")
    
    args = parser.parse_args()
    
    print("🚀 Starting CharForgex RunPod deployment...")
    
    # Build Docker image
    image_tag = build_docker_image(args.tag)
    
    # Push to registry if specified
    if args.registry and not args.build_only:
        final_image_url = push_to_registry(image_tag, args.registry)
    else:
        final_image_url = image_tag
    
    if not args.build_only:
        # Generate deployment configurations
        template_config = create_runpod_template(final_image_url, f"{args.endpoint_name} Template")
        endpoint_config = create_endpoint_config("TEMPLATE_ID", args.endpoint_name)
        
        # Save configurations
        with open('runpod_worker/template_config.json', 'w') as f:
            json.dump(template_config, f, indent=2)
        
        with open('runpod_worker/endpoint_config.json', 'w') as f:
            json.dump(endpoint_config, f, indent=2)
        
        print("📋 Configuration files created:")
        print("   - runpod_worker/template_config.json")
        print("   - runpod_worker/endpoint_config.json")
        
        # Generate deployment guide
        generate_deployment_guide("YOUR_ENDPOINT_ID", final_image_url)
    
    print("\n✅ Deployment preparation complete!")
    print("\n📋 Next steps:")
    print("1. Push your Docker image to a container registry")
    print("2. Create a RunPod template using template_config.json")
    print("3. Create a RunPod endpoint using endpoint_config.json")
    print("4. Set up your environment variables")
    print("5. Test the deployment with the provided GUI")

if __name__ == "__main__":
    main()
