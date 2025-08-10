#!/usr/bin/env python3
"""
CharForgex RunPod Setup Validation Script
Validates that all components are properly configured for RunPod deployment
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"🔍 {text}")
    print('='*60)

def print_check(item, status, details=""):
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {item}")
    if details:
        print(f"   {details}")

def check_file_exists(filepath, description):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    size = os.path.getsize(filepath) if exists else 0
    details = f"Size: {size} bytes" if exists else "File not found"
    print_check(description, exists, details)
    return exists

def check_docker_setup():
    """Check Docker installation and functionality"""
    print_header("Docker Setup")

    # Check Docker installation
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        docker_available = result.returncode == 0
        version = result.stdout.strip() if docker_available else "Not installed"
        print_check("Docker Installation", docker_available, version)
    except FileNotFoundError:
        print_check("Docker Installation", False, "Docker not found in PATH")
        return False

    # Check Docker daemon
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        daemon_running = result.returncode == 0
        print_check("Docker Daemon", daemon_running, "Running" if daemon_running else "Not running")
    except:
        print_check("Docker Daemon", False, "Cannot connect to Docker daemon")
        return False

    # Check Docker buildx (for multi-platform builds)
    try:
        result = subprocess.run(['docker', 'buildx', 'version'], capture_output=True, text=True)
        buildx_available = result.returncode == 0
        print_check("Docker Buildx", buildx_available, "Available" if buildx_available else "Not available")
    except:
        print_check("Docker Buildx", False, "Not available")

    return docker_available and daemon_running

def check_system_packages():
    """Check system packages required for CharForgex"""
    print_header("System Packages")

    required_packages = [
        ("git", "Git version control"),
        ("curl", "HTTP client"),
        ("wget", "File downloader"),
        ("python3", "Python interpreter"),
        ("pip3", "Python package manager")
    ]

    all_available = True
    for package, description in required_packages:
        try:
            result = subprocess.run([package, '--version'], capture_output=True, text=True)
            available = result.returncode == 0
            version = result.stdout.split('\n')[0] if available else "Not found"
            print_check(description, available, version)
            all_available = all_available and available
        except FileNotFoundError:
            print_check(description, False, "Not found in PATH")
            all_available = False

    # Check for graphics libraries (important for image processing)
    graphics_libs = [
        "libgl1-mesa-glx",
        "libglib2.0-0",
        "ffmpeg"
    ]

    for lib in graphics_libs:
        try:
            # Try to find the library
            result = subprocess.run(['dpkg', '-l', lib], capture_output=True, text=True)
            installed = result.returncode == 0 and 'ii' in result.stdout
            print_check(f"Library: {lib}", installed, "Installed" if installed else "Not installed")
        except:
            print_check(f"Library: {lib}", False, "Cannot check (not Debian/Ubuntu)")

    return all_available

def check_runpod_files():
    """Check RunPod worker files"""
    print_header("RunPod Worker Files")

    required_files = [
        ("runpod_worker/Dockerfile", "Docker container definition"),
        ("runpod_worker/worker.py", "Main worker entry point"),
        ("runpod_worker/handler.py", "Request handler"),
        ("runpod_worker/utils.py", "Utility functions"),
        ("runpod_worker/requirements.txt", "Python dependencies"),
        ("runpod_worker/config.json", "RunPod configuration"),
        ("runpod_worker/setup_runpod.sh", "Setup script"),
        ("runpod_worker/deploy_from_git.py", "Git deployment script"),
        ("runpod_worker/deploy_seamless.py", "Seamless deployment"),
        ("runpod_worker/one_click_deploy.sh", "One-click deployment"),
        ("runpod_worker/client_example.py", "Python client example"),
        ("runpod_worker/test_worker.py", "Testing script"),
        ("runpod_worker/gui/index.html", "Web GUI"),
        ("runpod_worker/gui/app.js", "GUI JavaScript"),
    ]

    all_exist = True
    for filepath, description in required_files:
        exists = check_file_exists(filepath, description)
        all_exist = all_exist and exists

    # Additional validation for critical files
    if os.path.exists("runpod_worker/Dockerfile"):
        print_check("Dockerfile Git support", check_dockerfile_git_support(), "Checks for Git clone functionality")

    if os.path.exists("runpod_worker/worker.py"):
        print_check("Worker.py syntax", check_python_syntax("runpod_worker/worker.py"), "Python syntax validation")

    return all_exist

def check_dockerfile_git_support():
    """Check if Dockerfile supports Git deployment"""
    try:
        with open("runpod_worker/Dockerfile", 'r') as f:
            content = f.read()

        required_elements = [
            "ARG REPO_URL",
            "ARG BRANCH",
            "git clone",
            "COPY . /workspace/",  # Fallback
            "test -f /workspace/train_character.py"  # Validation
        ]

        for element in required_elements:
            if element not in content:
                return False

        return True
    except Exception:
        return False

def check_python_syntax(filepath):
    """Check Python file syntax"""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        return True
    except SyntaxError:
        return False
    except Exception:
        return False

def check_base_system():
    """Check base CharForgex system"""
    print_header("Base CharForgex System")
    
    required_files = [
        ("train_character.py", "Training script"),
        ("test_character.py", "Inference script"),
        ("base_requirements.txt", "Base dependencies"),
        ("install.py", "Installation script"),
        ("setup.sh", "Setup script"),
    ]
    
    all_exist = True
    for filepath, description in required_files:
        exists = check_file_exists(filepath, description)
        all_exist = all_exist and exists
    
    return all_exist

def check_python_environment():
    """Check Python environment"""
    print_header("Python Environment")
    
    # Check Python version
    python_version = sys.version
    python_ok = sys.version_info >= (3, 10)
    print_check("Python Version", python_ok, f"Python {python_version.split()[0]} (requires 3.10+)")
    
    # Check virtual environment
    venv_exists = os.path.exists(".venv")
    print_check("Virtual Environment", venv_exists, ".venv directory found" if venv_exists else "Run setup.sh first")
    
    # Check if we can import key modules
    try:
        import torch
        torch_available = True
        torch_version = torch.__version__
        cuda_available = torch.cuda.is_available()
        print_check("PyTorch", torch_available, f"Version {torch_version}, CUDA: {cuda_available}")
    except ImportError:
        print_check("PyTorch", False, "Not installed or not accessible")
        torch_available = False
    
    return python_ok and venv_exists and torch_available

def check_configuration():
    """Check configuration files"""
    print_header("Configuration")
    
    # Check .env file
    env_exists = os.path.exists(".env")
    print_check(".env file", env_exists, "Contains API keys" if env_exists else "Create from .env.example")
    
    # Check config.json
    config_exists = os.path.exists("runpod_worker/config.json")
    if config_exists:
        try:
            with open("runpod_worker/config.json", 'r') as f:
                config = json.load(f)
            print_check("RunPod Config", True, "Valid JSON configuration")
        except json.JSONDecodeError:
            print_check("RunPod Config", False, "Invalid JSON format")
            config_exists = False
    else:
        print_check("RunPod Config", False, "Configuration file missing")
    
    return config_exists

def generate_deployment_checklist():
    """Generate a deployment checklist"""
    checklist = """
# 📋 CharForgex RunPod Deployment Checklist

## Pre-Deployment
- [ ] All validation checks passed
- [ ] Docker image builds successfully
- [ ] Container registry account ready
- [ ] RunPod account with credits
- [ ] API keys obtained:
  - [ ] Hugging Face token (with Flux.1-dev access)
  - [ ] CivitAI API key
  - [ ] Google GenAI API key
  - [ ] FAL.ai API key

## Deployment Steps
- [ ] Push Docker image to registry
- [ ] Create RunPod template
- [ ] Create network volume (200GB+)
- [ ] Create serverless endpoint
- [ ] Configure environment variables
- [ ] Test health check
- [ ] Test character listing
- [ ] Train test character
- [ ] Generate test images

## Post-Deployment
- [ ] Monitor initial cold start performance
- [ ] Verify persistent storage works
- [ ] Test GUI interface
- [ ] Set up monitoring/alerts
- [ ] Document endpoint details for team

## Optimization
- [ ] Adjust idle timeout based on usage
- [ ] Monitor costs and optimize GPU selection
- [ ] Set up batch processing workflows
- [ ] Configure backup strategies for LoRAs

Use this checklist to ensure a smooth deployment process!
"""
    
    with open("runpod_worker/DEPLOYMENT_CHECKLIST.md", 'w') as f:
        f.write(checklist)
    
    print_check("Deployment Checklist", True, "Created DEPLOYMENT_CHECKLIST.md")

def main():
    """Main validation function"""
    print("🔍 CharForgex RunPod Setup Validation")
    print("This script checks if your system is ready for RunPod deployment")
    
    # Run all checks
    checks = [
        ("Docker Setup", check_docker_setup),
        ("System Packages", check_system_packages),
        ("Base System", check_base_system),
        ("Python Environment", check_python_environment),
        ("RunPod Files", check_runpod_files),
        ("Configuration", check_configuration),
    ]
    
    results = {}
    for check_name, check_func in checks:
        results[check_name] = check_func()
    
    # Generate checklist
    generate_deployment_checklist()
    
    # Summary
    print_header("Validation Summary")
    
    all_passed = True
    for check_name, passed in results.items():
        print_check(check_name, passed)
        all_passed = all_passed and passed
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 All checks passed! Your system is ready for RunPod deployment.")
        print("\n📋 Next steps:")
        print("1. Run: python deploy_to_runpod.py --registry your-registry.com/username")
        print("2. Follow the generated deployment instructions")
        print("3. Test with: python test_worker.py")
        print("4. Use the GUI or Python client for operations")
    else:
        print("❌ Some checks failed. Please fix the issues above before deploying.")
        print("\n🔧 Common fixes:")
        print("- Run setup.sh to install dependencies")
        print("- Install Docker and start the daemon")
        print("- Create .env file with your API keys")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
