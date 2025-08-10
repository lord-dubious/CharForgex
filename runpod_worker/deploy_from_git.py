#!/usr/bin/env python3
"""
CharForgex Git Repository Deployment to RunPod
Comprehensive deployment with error checking and validation
"""

import os
import sys
import json
import requests
import subprocess
import time
import tempfile
from typing import Dict, Any, Optional, List

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║              CharForgex RunPod Git Deployment               ║
║                   Comprehensive Setup                       ║
╚══════════════════════════════════════════════════════════════╝
""")

def print_step(step: str):
    print(f"\n🔄 {step}")

def print_success(message: str):
    print(f"✅ {message}")

def print_error(message: str):
    print(f"❌ {message}")

def print_warning(message: str):
    print(f"⚠️ {message}")

def print_info(message: str):
    print(f"ℹ️ {message}")

def run_command(cmd: str, check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run command with comprehensive error handling"""
    print_info(f"Running: {cmd}")

    try:
        # Split command for security (avoid shell=True)
        import shlex
        cmd_args = shlex.split(cmd)

        result = subprocess.run(
            cmd_args,
            shell=False,
            capture_output=capture_output,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if check and result.returncode != 0:
            print_error(f"Command failed with exit code {result.returncode}")
            if result.stderr:
                print_error(f"Error output: {result.stderr}")
            if result.stdout:
                print_info(f"Output: {result.stdout}")
            raise subprocess.CalledProcessError(result.returncode, cmd)
        
        return result
        
    except subprocess.TimeoutExpired:
        print_error(f"Command timed out: {cmd}")
        raise
    except Exception as e:
        print_error(f"Command execution failed: {e}")
        raise

def validate_git_repository(repo_url: str, branch: str = "main") -> bool:
    """Validate that the Git repository exists and has required files"""
    print_step("Validating Git repository")
    
    # Test repository accessibility
    try:
        result = run_command(f"git ls-remote --heads {repo_url}")
        if result.returncode != 0:
            print_error(f"Cannot access repository: {repo_url}")
            return False
        
        print_success("Repository is accessible")
        
        # Check if branch exists
        if branch not in result.stdout:
            print_warning(f"Branch '{branch}' not found, available branches:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    branch_name = line.split('/')[-1]
                    print_info(f"  - {branch_name}")
            return False
        
        print_success(f"Branch '{branch}' exists")
        return True
        
    except Exception as e:
        print_error(f"Repository validation failed: {e}")
        return False

def validate_required_files(repo_url: str, branch: str = "main") -> bool:
    """Clone repository temporarily and validate required files"""
    print_step("Validating required files in repository")
    
    required_files = [
        "train_character.py",
        "test_character.py", 
        "base_requirements.txt",
        "install.py",
        "runpod_worker/worker.py",
        "runpod_worker/handler.py",
        "runpod_worker/utils.py",
        "runpod_worker/Dockerfile"
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Clone repository
            clone_cmd = f"git clone --depth 1 --branch {branch} {repo_url} {temp_dir}/repo"
            run_command(clone_cmd)
            
            repo_path = f"{temp_dir}/repo"
            missing_files = []
            
            # Check each required file
            for file_path in required_files:
                full_path = os.path.join(repo_path, file_path)
                if not os.path.exists(full_path):
                    missing_files.append(file_path)
                else:
                    # Check file size (should not be empty)
                    if os.path.getsize(full_path) == 0:
                        print_warning(f"File is empty: {file_path}")
            
            if missing_files:
                print_error("Missing required files:")
                for file_path in missing_files:
                    print_error(f"  - {file_path}")
                return False
            
            print_success("All required files found")
            
            # Validate Python syntax of key files
            python_files = [f for f in required_files if f.endswith('.py')]
            for py_file in python_files:
                full_path = os.path.join(repo_path, py_file)
                try:
                    with open(full_path, 'r') as f:
                        compile(f.read(), py_file, 'exec')
                    print_success(f"Python syntax valid: {py_file}")
                except SyntaxError as e:
                    print_error(f"Python syntax error in {py_file}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            print_error(f"File validation failed: {e}")
            return False

def build_docker_image(repo_url: str, branch: str, image_tag: str) -> bool:
    """Build Docker image from Git repository"""
    print_step(f"Building Docker image: {image_tag}")
    
    try:
        # Build with build args for Git deployment
        build_cmd = f"""
        docker build \
            --build-arg REPO_URL={repo_url} \
            --build-arg BRANCH={branch} \
            -t {image_tag} \
            -f runpod_worker/Dockerfile \
            .
        """
        
        result = run_command(build_cmd, capture_output=False)
        
        if result.returncode == 0:
            print_success(f"Docker image built successfully: {image_tag}")
            return True
        else:
            print_error("Docker build failed")
            return False
            
    except Exception as e:
        print_error(f"Docker build error: {e}")
        return False

def test_docker_image(image_tag: str) -> bool:
    """Test the built Docker image"""
    print_step("Testing Docker image")
    
    test_commands = [
        # Basic Python test
        "python -c 'import sys; print(f\"Python: {sys.version.split()[0]}\")'",
        
        # PyTorch test
        "python -c 'import torch; print(f\"PyTorch: {torch.__version__}\"); print(f\"CUDA: {torch.cuda.is_available()}\")'",
        
        # RunPod SDK test
        "python -c 'import runpod; print(f\"RunPod SDK: {runpod.__version__}\")'",
        
        # CharForgex imports test
        "python -c 'import sys; sys.path.append(\"/workspace\"); sys.path.append(\"/workspace/runpod_worker\"); import runpod_worker.worker as w; print(\"Worker import: OK\")'",
        
        # File structure test
        "ls -la /workspace/ && test -f /workspace/train_character.py && echo 'File structure: OK'"
    ]
    
    for i, cmd in enumerate(test_commands, 1):
        try:
            print_info(f"Test {i}/{len(test_commands)}: {cmd[:50]}...")
            
            docker_cmd = f"docker run --rm {image_tag} bash -c '{cmd}'"
            result = run_command(docker_cmd)
            
            if result.returncode == 0:
                print_success(f"Test {i} passed")
                if result.stdout.strip():
                    print_info(f"Output: {result.stdout.strip()}")
            else:
                print_error(f"Test {i} failed")
                if result.stderr:
                    print_error(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            print_error(f"Test {i} error: {e}")
            return False
    
    print_success("All Docker image tests passed")
    return True

def push_to_registry(image_tag: str, registry_username: str, registry_password: str) -> bool:
    """Push image to container registry"""
    print_step(f"Pushing image to registry: {image_tag}")
    
    try:
        # Login to registry
        login_cmd = f"echo '{registry_password}' | docker login -u {registry_username} --password-stdin"
        run_command(login_cmd)
        print_success("Registry login successful")
        
        # Push image
        push_cmd = f"docker push {image_tag}"
        result = run_command(push_cmd, capture_output=False)
        
        if result.returncode == 0:
            print_success(f"Image pushed successfully: {image_tag}")
            return True
        else:
            print_error("Image push failed")
            return False
            
    except Exception as e:
        print_error(f"Registry push error: {e}")
        return False

def create_runpod_resources(api_key: str, image_tag: str) -> Optional[Dict[str, str]]:
    """Create RunPod template and endpoint"""
    print_step("Creating RunPod resources")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Create network volume
        print_info("Creating network volume...")
        volume_response = requests.post('https://api.runpod.ai/graphql', headers=headers, json={
            'query': '''
            mutation($input: NetworkVolumeInput!) {
                createNetworkVolume(input: $input) { id name }
            }
            ''',
            'variables': {
                'input': {
                    'name': 'charforgex-storage',
                    'size': 200,
                    'dataCenterId': 'US-OR-1'
                }
            }
        })
        
        volume_id = None
        if volume_response.status_code == 200:
            result = volume_response.json()
            if 'errors' not in result:
                volume_id = result['data']['createNetworkVolume']['id']
                print_success(f"Network volume created: {volume_id}")
        
        # Create template
        print_info("Creating template...")
        template_config = {
            'name': 'CharForgex Git Worker',
            'imageName': image_tag,
            'containerDiskInGb': 50,
            'volumeMountPath': '/runpod-volume',
            'ports': '8000/http',
            'env': [
                {'key': 'PLATFORM', 'value': 'serverless'},
                {'key': 'HF_HOME', 'value': '/runpod-volume/huggingface'},
                {'key': 'COMFYUI_PATH', 'value': '/workspace/ComfyUI'},
                {'key': 'APP_PATH', 'value': '/workspace'},
                {'key': 'PYTHONPATH', 'value': '/workspace:/workspace/runpod_worker'}
            ]
        }
        
        if volume_id:
            template_config['networkVolumeId'] = volume_id
        else:
            template_config['volumeInGb'] = 200
        
        template_response = requests.post('https://api.runpod.ai/graphql', headers=headers, json={
            'query': '''
            mutation($input: SaveTemplateInput!) {
                saveTemplate(input: $input) { id name }
            }
            ''',
            'variables': {'input': template_config}
        })
        
        template_id = None
        if template_response.status_code == 200:
            result = template_response.json()
            if 'errors' not in result:
                template_id = result['data']['saveTemplate']['id']
                print_success(f"Template created: {template_id}")
        
        if not template_id:
            print_error("Failed to create template")
            return None
        
        # Create endpoint
        print_info("Creating endpoint...")
        endpoint_config = {
            'name': 'CharForgex Git',
            'templateId': template_id,
            'gpuIds': 'NVIDIA RTX A5000,NVIDIA RTX A6000,NVIDIA GeForce RTX 4090',
            'idleTimeout': 5,
            'maxWorkers': 3,
            'flashBoot': True
        }
        
        endpoint_response = requests.post('https://api.runpod.ai/graphql', headers=headers, json={
            'query': '''
            mutation($input: EndpointInput!) {
                createEndpoint(input: $input) { id name }
            }
            ''',
            'variables': {'input': endpoint_config}
        })
        
        endpoint_id = None
        if endpoint_response.status_code == 200:
            result = endpoint_response.json()
            if 'errors' not in result:
                endpoint_id = result['data']['createEndpoint']['id']
                print_success(f"Endpoint created: {endpoint_id}")
        
        if not endpoint_id:
            print_error("Failed to create endpoint")
            return None
        
        return {
            'volume_id': volume_id,
            'template_id': template_id,
            'endpoint_id': endpoint_id
        }
        
    except Exception as e:
        print_error(f"RunPod resource creation failed: {e}")
        return None

def main():
    """Main deployment function"""
    print_banner()
    
    # Get configuration
    repo_url = input("Enter your Git repository URL: ").strip()
    if not repo_url:
        print_error("Repository URL is required")
        sys.exit(1)
    
    branch = input("Enter branch name (default: main): ").strip() or "main"
    
    registry_username = input("Enter Docker registry username: ").strip()
    if not registry_username:
        print_error("Registry username is required")
        sys.exit(1)
    
    registry_password = input("Enter Docker registry password/token: ").strip()
    if not registry_password:
        print_error("Registry password is required")
        sys.exit(1)
    
    runpod_api_key = input("Enter RunPod API key: ").strip()
    if not runpod_api_key:
        print_error("RunPod API key is required")
        sys.exit(1)
    
    image_name = input("Enter image name (default: charforgex-runpod): ").strip() or "charforgex-runpod"
    image_tag = f"{registry_username}/{image_name}:latest"
    
    try:
        # Step 1: Validate repository
        if not validate_git_repository(repo_url, branch):
            sys.exit(1)
        
        # Step 2: Validate required files
        if not validate_required_files(repo_url, branch):
            sys.exit(1)
        
        # Step 3: Build Docker image
        if not build_docker_image(repo_url, branch, image_tag):
            sys.exit(1)
        
        # Step 4: Test Docker image
        if not test_docker_image(image_tag):
            sys.exit(1)
        
        # Step 5: Push to registry
        if not push_to_registry(image_tag, registry_username, registry_password):
            sys.exit(1)
        
        # Step 6: Create RunPod resources
        resources = create_runpod_resources(runpod_api_key, image_tag)
        if not resources:
            sys.exit(1)
        
        # Success!
        print_success("🎉 Git-based deployment completed successfully!")
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    Deployment Complete!                     ║
╚══════════════════════════════════════════════════════════════╝

📋 Deployment Details:
   • Repository: {repo_url}
   • Branch: {branch}
   • Image: {image_tag}
   • Endpoint ID: {resources['endpoint_id']}
   • Template ID: {resources['template_id']}
   • Volume ID: {resources.get('volume_id', 'N/A')}

🔗 URLs:
   • API: https://api.runpod.ai/v2/{resources['endpoint_id']}/runsync
   • GUI: Access via port 8000

⚠️ Next Steps:
1. Set environment variables in RunPod endpoint:
   • HF_TOKEN=your_huggingface_token
   • CIVITAI_API_KEY=your_civitai_key
   • GOOGLE_API_KEY=your_google_genai_key
   • FAL_KEY=your_fal_ai_key

2. Test your deployment:
   python runpod_worker/test_worker.py https://api.runpod.ai/v2/{resources['endpoint_id']}/runsync {runpod_api_key[:8]}...

3. Use the GUI:
   cd runpod_worker/gui && python -m http.server 8080

🎉 Your CharForgex system is now running from your Git repository!
        """)
        
        # Save deployment info
        deployment_info = {
            'repo_url': repo_url,
            'branch': branch,
            'image_tag': image_tag,
            'deployment_time': time.time(),
            **resources
        }
        
        with open('deployment_info.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print_success("Deployment info saved to deployment_info.json")
        
    except KeyboardInterrupt:
        print_error("Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
