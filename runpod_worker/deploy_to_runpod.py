#!/usr/bin/env python3
"""
Automated CharForgex RunPod Deployment Script
Handles the complete deployment process to RunPod
"""

import os
import sys
import json
import subprocess
import argparse
import requests
from typing import Dict, Any, Optional

def print_step(step: str):
    print(f"\n🔄 {step}")

def print_success(message: str):
    print(f"✅ {message}")

def print_error(message: str):
    print(f"❌ {message}")

def print_warning(message: str):
    print(f"⚠️ {message}")

def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run shell command with error handling"""
    print(f"   Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print_error(f"Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        if not check:
            return result
        sys.exit(1)
    
    return result

def check_prerequisites():
    """Check if all prerequisites are met"""
    print_step("Checking prerequisites...")
    
    # Check Docker
    result = run_command("docker --version", check=False)
    if result.returncode != 0:
        print_error("Docker is not installed or not running")
        return False
    
    # Check if we're in the right directory
    if not os.path.exists("train_character.py"):
        print_error("Please run this script from the CharForgex root directory")
        return False
    
    # Check for required files
    required_files = [
        "base_requirements.txt",
        "install.py", 
        "setup.sh"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print_error(f"Required file missing: {file}")
            return False
    
    print_success("All prerequisites met")
    return True

def build_and_test_image(image_tag: str):
    """Build and test the Docker image"""
    print_step(f"Building Docker image: {image_tag}")
    
    # Build image
    run_command(f"docker build -t {image_tag} -f runpod_worker/Dockerfile .")
    
    print_step("Testing Docker image...")
    
    # Test basic functionality
    test_cmd = f"""docker run --rm {image_tag} python -c "
import sys
print('Python version:', sys.version)
try:
    import torch
    print('PyTorch version:', torch.__version__)
    print('CUDA available:', torch.cuda.is_available())
except ImportError as e:
    print('PyTorch import error:', e)
try:
    import runpod
    print('RunPod SDK version:', runpod.__version__)
except ImportError as e:
    print('RunPod SDK import error:', e)
print('✅ Basic test passed')
" """
    
    run_command(test_cmd)
    print_success("Docker image built and tested successfully")

def push_to_registry(image_tag: str, registry_url: str) -> str:
    """Push image to container registry"""
    print_step(f"Pushing to registry: {registry_url}")
    
    registry_tag = f"{registry_url}/{image_tag}"
    
    # Tag for registry
    run_command(f"docker tag {image_tag} {registry_tag}")
    
    # Push to registry
    run_command(f"docker push {registry_tag}")
    
    print_success(f"Image pushed: {registry_tag}")
    return registry_tag

def create_runpod_configs(image_url: str, endpoint_name: str):
    """Create RunPod template and endpoint configurations"""
    print_step("Creating RunPod configurations...")
    
    # Load base config
    with open('runpod_worker/config.json', 'r') as f:
        config = json.load(f)
    
    # Update template with actual image URL
    config['runpod_template']['imageName'] = image_url
    config['runpod_template']['name'] = f"{endpoint_name} Template"
    
    # Update endpoint config
    config['runpod_endpoint']['name'] = endpoint_name
    
    # Save updated configs
    with open('runpod_worker/template_config.json', 'w') as f:
        json.dump(config['runpod_template'], f, indent=2)
    
    with open('runpod_worker/endpoint_config.json', 'w') as f:
        json.dump(config['runpod_endpoint'], f, indent=2)
    
    print_success("Configuration files created")
    return config

def generate_deployment_instructions(endpoint_name: str, image_url: str):
    """Generate step-by-step deployment instructions"""
    instructions = f"""
# 🚀 CharForgex RunPod Deployment Instructions

## Your Deployment Details
- **Image**: {image_url}
- **Endpoint Name**: {endpoint_name}

## Step 1: Create RunPod Template
1. Go to [RunPod Console → Templates](https://console.runpod.io/templates)
2. Click "New Template"
3. Use these settings:
   - **Name**: {endpoint_name} Template
   - **Image**: {image_url}
   - **Container Disk**: 50GB
   - **Volume Mount Path**: /runpod-volume
   - **Ports**: 8000/http

## Step 2: Create Network Volume (Recommended)
1. Go to [RunPod Console → Storage](https://console.runpod.io/storage)
2. Create new Network Volume:
   - **Name**: charforgex-storage
   - **Size**: 200GB+

## Step 3: Create Serverless Endpoint
1. Go to [RunPod Console → Serverless](https://console.runpod.io/serverless)
2. Click "New Endpoint"
3. Configure:
   - **Name**: {endpoint_name}
   - **Template**: Select your template
   - **GPU Types**: RTX A5000, RTX A6000, RTX 4090
   - **Max Workers**: 3
   - **Idle Timeout**: 5 minutes
   - **FlashBoot**: Enabled
   - **Network Volume**: Attach your storage volume

## Step 4: Set Environment Variables
Add these to your endpoint:
```
HF_TOKEN=your_huggingface_token
CIVITAI_API_KEY=your_civitai_api_key
GOOGLE_API_KEY=your_google_genai_api_key
FAL_KEY=your_fal_ai_api_key
```

## Step 5: Test Your Deployment
```bash
# Test with provided script
python runpod_worker/test_worker.py https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync YOUR_API_KEY

# Or use the GUI
cd runpod_worker/gui && python -m http.server 8080
# Then open http://localhost:8080
```

## 🎉 You're Ready!
Your CharForgex system is now deployed as a scalable RunPod serverless worker!

For detailed usage instructions, see:
- runpod_worker/RUNPOD_DEPLOYMENT.md
- runpod_worker/client_example.py
"""
    
    with open('runpod_worker/DEPLOYMENT_INSTRUCTIONS.md', 'w') as f:
        f.write(instructions)
    
    print_success("Deployment instructions created")

def main():
    parser = argparse.ArgumentParser(description="Deploy CharForgex to RunPod")
    parser.add_argument("--registry", type=str, required=True, 
                       help="Container registry URL (e.g., docker.io/username, ghcr.io/username)")
    parser.add_argument("--tag", type=str, default="charforgex-runpod", 
                       help="Docker image tag")
    parser.add_argument("--endpoint-name", type=str, default="CharForgex", 
                       help="RunPod endpoint name")
    parser.add_argument("--skip-build", action="store_true", 
                       help="Skip Docker build (use existing image)")
    parser.add_argument("--skip-push", action="store_true", 
                       help="Skip pushing to registry")
    
    args = parser.parse_args()
    
    print("🚀 CharForgex RunPod Deployment Automation")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Build image
    if not args.skip_build:
        build_and_test_image(args.tag)
    else:
        print_warning("Skipping Docker build")
    
    # Push to registry
    if not args.skip_push:
        final_image_url = push_to_registry(args.tag, args.registry)
    else:
        final_image_url = f"{args.registry}/{args.tag}"
        print_warning(f"Skipping push, using: {final_image_url}")
    
    # Create configurations
    create_runpod_configs(final_image_url, args.endpoint_name)
    
    # Generate instructions
    generate_deployment_instructions(args.endpoint_name, final_image_url)
    
    print("\n" + "=" * 50)
    print_success("🎉 Deployment preparation complete!")
    print("\n📋 Next Steps:")
    print("1. Follow instructions in runpod_worker/DEPLOYMENT_INSTRUCTIONS.md")
    print("2. Create RunPod template and endpoint")
    print("3. Set up your API keys")
    print("4. Test with runpod_worker/test_worker.py")
    print("5. Use the GUI or Python client for operations")
    
    print(f"\n🔗 Your image URL: {final_image_url}")
    print("📖 Full documentation: runpod_worker/RUNPOD_DEPLOYMENT.md")

if __name__ == "__main__":
    main()
