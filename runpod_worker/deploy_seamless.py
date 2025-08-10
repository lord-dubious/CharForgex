#!/usr/bin/env python3
"""
CharForgex Seamless RunPod Deployment
One-click deployment to RunPod with automatic setup
"""

import os
import sys
import json
import requests
import subprocess
import time
from typing import Dict, Any, Optional

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    CharForgex RunPod                         ║
║                  Seamless Deployment                         ║
╚══════════════════════════════════════════════════════════════╝
""")

def print_step(step: str):
    print(f"\n🔄 {step}")

def print_success(message: str):
    print(f"✅ {message}")

def print_error(message: str):
    print(f"❌ {message}")

def print_info(message: str):
    print(f"ℹ️ {message}")

def check_runpod_api_key():
    """Check if RunPod API key is available"""
    api_key = os.getenv('RUNPOD_API_KEY')
    if not api_key:
        print_error("RUNPOD_API_KEY environment variable not set")
        print_info("Get your API key from: https://console.runpod.io/user/settings")
        print_info("Then run: export RUNPOD_API_KEY=your_api_key_here")
        return None
    return api_key

def create_network_volume(api_key: str, name: str = "charforgex-storage", size: int = 200) -> Optional[str]:
    """Create a network volume for persistent storage"""
    print_step(f"Creating network volume: {name} ({size}GB)")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Check if volume already exists
    response = requests.get('https://api.runpod.ai/graphql', headers=headers, json={
        'query': '''
        query {
            myself {
                networkVolumes {
                    id
                    name
                    size
                }
            }
        }
        '''
    })
    
    if response.status_code == 200:
        volumes = response.json().get('data', {}).get('myself', {}).get('networkVolumes', [])
        for volume in volumes:
            if volume['name'] == name:
                print_success(f"Using existing network volume: {volume['id']}")
                return volume['id']
    
    # Create new volume
    response = requests.post('https://api.runpod.ai/graphql', headers=headers, json={
        'query': '''
        mutation($input: NetworkVolumeInput!) {
            createNetworkVolume(input: $input) {
                id
                name
            }
        }
        ''',
        'variables': {
            'input': {
                'name': name,
                'size': size,
                'dataCenterId': 'US-OR-1'  # Default to Oregon
            }
        }
    })
    
    if response.status_code == 200:
        result = response.json()
        if 'errors' in result:
            print_error(f"Failed to create network volume: {result['errors']}")
            return None
        
        volume_id = result['data']['createNetworkVolume']['id']
        print_success(f"Created network volume: {volume_id}")
        return volume_id
    else:
        print_error(f"Failed to create network volume: {response.text}")
        return None

def create_template(api_key: str, image_name: str, volume_id: Optional[str] = None) -> Optional[str]:
    """Create a RunPod template"""
    print_step("Creating RunPod template")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    template_config = {
        'name': 'CharForgex Worker',
        'imageName': image_name,
        'containerDiskInGb': 50,
        'volumeInGb': 200 if not volume_id else 0,
        'volumeMountPath': '/runpod-volume',
        'ports': '8000/http',
        'env': [
            {'key': 'PLATFORM', 'value': 'serverless'},
            {'key': 'HF_HOME', 'value': '/runpod-volume/huggingface'},
            {'key': 'COMFYUI_PATH', 'value': '/workspace/ComfyUI'},
            {'key': 'APP_PATH', 'value': '/workspace'},
            {'key': 'PYTHONPATH', 'value': '/workspace'}
        ]
    }
    
    if volume_id:
        template_config['networkVolumeId'] = volume_id
    
    response = requests.post('https://api.runpod.ai/graphql', headers=headers, json={
        'query': '''
        mutation($input: SaveTemplateInput!) {
            saveTemplate(input: $input) {
                id
                name
            }
        }
        ''',
        'variables': {'input': template_config}
    })
    
    if response.status_code == 200:
        result = response.json()
        if 'errors' in result:
            print_error(f"Failed to create template: {result['errors']}")
            return None
        
        template_id = result['data']['saveTemplate']['id']
        print_success(f"Created template: {template_id}")
        return template_id
    else:
        print_error(f"Failed to create template: {response.text}")
        return None

def create_endpoint(api_key: str, template_id: str, name: str = "CharForgex") -> Optional[str]:
    """Create a serverless endpoint"""
    print_step(f"Creating serverless endpoint: {name}")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    endpoint_config = {
        'name': name,
        'templateId': template_id,
        'gpuIds': 'NVIDIA RTX A5000,NVIDIA RTX A6000,NVIDIA GeForce RTX 4090',
        'idleTimeout': 5,
        'maxWorkers': 3,
        'flashBoot': True,
        'locations': 'US,EU'
    }
    
    response = requests.post('https://api.runpod.ai/graphql', headers=headers, json={
        'query': '''
        mutation($input: EndpointInput!) {
            createEndpoint(input: $input) {
                id
                name
            }
        }
        ''',
        'variables': {'input': endpoint_config}
    })
    
    if response.status_code == 200:
        result = response.json()
        if 'errors' in result:
            print_error(f"Failed to create endpoint: {result['errors']}")
            return None
        
        endpoint_id = result['data']['createEndpoint']['id']
        print_success(f"Created endpoint: {endpoint_id}")
        return endpoint_id
    else:
        print_error(f"Failed to create endpoint: {response.text}")
        return None

def test_endpoint(api_key: str, endpoint_id: str) -> bool:
    """Test the endpoint with a health check"""
    print_step("Testing endpoint")
    
    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Wait for endpoint to be ready
    print_info("Waiting for endpoint to initialize...")
    time.sleep(30)
    
    try:
        response = requests.post(url, headers=headers, json={
            'input': {'operation': 'health_check'}
        }, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'healthy':
                print_success("Endpoint is healthy and ready!")
                return True
            else:
                print_error(f"Endpoint health check failed: {result}")
                return False
        else:
            print_error(f"Endpoint test failed: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Endpoint test timed out - this may be normal for cold starts")
        return False
    except Exception as e:
        print_error(f"Endpoint test failed: {e}")
        return False

def generate_usage_guide(endpoint_id: str, api_key: str):
    """Generate usage instructions"""
    guide = f"""
╔══════════════════════════════════════════════════════════════╗
║                    🎉 Deployment Complete!                   ║
╚══════════════════════════════════════════════════════════════╝

Your CharForgex RunPod worker is ready to use!

📋 Endpoint Details:
   • Endpoint ID: {endpoint_id}
   • URL: https://api.runpod.ai/v2/{endpoint_id}/runsync
   • GUI: https://api.runpod.ai/v2/{endpoint_id}:8000

🔧 Quick Test:
curl -X POST https://api.runpod.ai/v2/{endpoint_id}/runsync \\
  -H "Authorization: Bearer {api_key[:8]}..." \\
  -H "Content-Type: application/json" \\
  -d '{{"input": {{"operation": "health_check"}}}}'

🎨 Train a Character:
curl -X POST https://api.runpod.ai/v2/{endpoint_id}/run \\
  -H "Authorization: Bearer {api_key[:8]}..." \\
  -H "Content-Type: application/json" \\
  -d '{{
    "input": {{
      "operation": "training",
      "character_name": "my_character",
      "input_image": "base64_encoded_image_data",
      "steps": 800
    }}
  }}'

🖼️ Generate Images:
curl -X POST https://api.runpod.ai/v2/{endpoint_id}/runsync \\
  -H "Authorization: Bearer {api_key[:8]}..." \\
  -H "Content-Type: application/json" \\
  -d '{{
    "input": {{
      "operation": "inference", 
      "character_name": "my_character",
      "prompt": "portrait of my_character, detailed face"
    }}
  }}'

🌐 Web GUI:
   Open: cd runpod_worker/gui && python -m http.server 8080
   Then: http://localhost:8080

📖 Documentation:
   • Full guide: runpod_worker/RUNPOD_DEPLOYMENT.md
   • Python client: runpod_worker/client_example.py
   • Test script: runpod_worker/test_worker.py

⚠️ Important:
   Set these environment variables in your RunPod endpoint:
   • HF_TOKEN=your_huggingface_token
   • CIVITAI_API_KEY=your_civitai_key
   • GOOGLE_API_KEY=your_google_genai_key
   • FAL_KEY=your_fal_ai_key

🎉 Happy character training and image generation!
"""
    
    print(guide)
    
    # Save to file
    with open('runpod_worker/DEPLOYMENT_SUCCESS.md', 'w') as f:
        f.write(guide)

def main():
    """Main deployment function"""
    print_banner()
    
    # Check API key
    api_key = check_runpod_api_key()
    if not api_key:
        sys.exit(1)
    
    # Get image name
    image_name = input("Enter your Docker image URL (e.g., docker.io/username/charforgex-runpod:latest): ").strip()
    if not image_name:
        print_error("Image name is required")
        sys.exit(1)
    
    try:
        # Create network volume
        volume_id = create_network_volume(api_key)
        
        # Create template
        template_id = create_template(api_key, image_name, volume_id)
        if not template_id:
            sys.exit(1)
        
        # Create endpoint
        endpoint_id = create_endpoint(api_key, template_id)
        if not endpoint_id:
            sys.exit(1)
        
        # Test endpoint
        test_endpoint(api_key, endpoint_id)
        
        # Generate usage guide
        generate_usage_guide(endpoint_id, api_key)
        
    except KeyboardInterrupt:
        print_error("Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
