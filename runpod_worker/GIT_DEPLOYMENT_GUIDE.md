# CharForgex Git Repository Deployment Guide

## 🎯 **Verified Git-Based Deployment**

This guide ensures your CharForgex system deploys flawlessly from your Git repository to RunPod with comprehensive error checking and validation.

## ✅ **Pre-Deployment Validation**

### Step 1: Validate Your Setup
```bash
cd runpod_worker
python validate_setup.py
```

**This checks:**
- ✅ Docker installation and daemon
- ✅ System packages (git, curl, wget, python3, pip3)
- ✅ Graphics libraries (libgl1-mesa-glx, libglib2.0-0, ffmpeg)
- ✅ All required CharForgex files
- ✅ RunPod worker files and syntax
- ✅ Python environment and dependencies
- ✅ Configuration files

### Step 2: Repository Requirements Checklist

**Required Files in Your Repository:**
```
✅ train_character.py          # Main training script
✅ test_character.py           # Inference script  
✅ base_requirements.txt       # Python dependencies
✅ install.py                  # Installation script
✅ runpod_worker/Dockerfile    # Container definition
✅ runpod_worker/worker.py     # RunPod worker entry point
✅ runpod_worker/handler.py    # Request handler
✅ runpod_worker/utils.py      # Utility functions
✅ runpod_worker/gui/          # Web interface files
```

**Repository Structure Validation:**
```bash
# Test repository accessibility
git ls-remote --heads https://github.com/yourusername/CharForgex.git

# Validate required files exist
python runpod_worker/deploy_from_git.py --validate-only
```

## 🚀 **Deployment Options**

### Option 1: Comprehensive Git Deployment (Recommended)
```bash
cd runpod_worker
python deploy_from_git.py
```

**What it does:**
1. **Validates Git repository** - Checks accessibility and branch existence
2. **Validates required files** - Ensures all necessary files are present
3. **Builds Docker image** - Uses Git clone in Dockerfile with fallback
4. **Tests Docker image** - Comprehensive testing of all components
5. **Pushes to registry** - Automated push to Docker Hub/registry
6. **Creates RunPod resources** - Template, volume, and endpoint
7. **Validates deployment** - End-to-end testing

### Option 2: One-Click with Git Support
```bash
cd runpod_worker
./one_click_deploy.sh
```

**Enhanced with Git support:**
- Uses current repository URL automatically
- Validates all files before deployment
- Comprehensive error handling

### Option 3: Manual Git-Based Build
```bash
# Build with Git arguments
docker build \
  --build-arg REPO_URL=https://github.com/yourusername/CharForgex.git \
  --build-arg BRANCH=main \
  -t yourusername/charforgex-runpod:latest \
  -f runpod_worker/Dockerfile \
  .
```

## 🔧 **Dockerfile Git Integration**

The Dockerfile now includes comprehensive Git support:

```dockerfile
# Clone repository with fallback
ARG REPO_URL=https://github.com/lord-dubious/CharForgex.git
ARG BRANCH=main
RUN git clone --depth 1 --branch ${BRANCH} ${REPO_URL} /workspace || \
    (echo "Failed to clone repository. Falling back to COPY." && exit 0)

# Copy local files if git clone failed
COPY . /workspace/

# Validate repository structure
RUN test -f /workspace/train_character.py || (echo "ERROR: train_character.py not found!" && exit 1)
```

**Key Features:**
- ✅ **Git clone with fallback** to local COPY
- ✅ **File validation** ensures required files exist
- ✅ **Error handling** with descriptive messages
- ✅ **System package installation** with comprehensive dependencies
- ✅ **Python syntax validation** for critical files
- ✅ **Import testing** validates all dependencies work

## 🛡️ **Error Prevention & Handling**

### System Package Issues
```bash
# The Dockerfile installs comprehensive system packages:
RUN apt-get update && apt-get install -y \
    git git-lfs wget curl unzip build-essential \
    python3-dev python3-pip python3-venv \
    libgl1-mesa-glx libgl1-mesa-dev libglib2.0-0 libglib2.0-dev \
    libgtk-3-0 libgtk-3-dev libgstreamer1.0-0 \
    libopencv-dev libsm6 libxext6 libxrender-dev \
    ffmpeg libavcodec-dev libavformat-dev libswscale-dev \
    && rm -rf /var/lib/apt/lists/*
```

### Missing Dependencies
```bash
# Comprehensive Python dependency installation:
RUN pip install runpod>=1.6.0 requests>=2.31.0 pillow>=10.0.0 \
               numpy>=1.24.0 opencv-python-headless>=4.8.0 \
               torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
               diffusers>=0.30.0 transformers>=4.40.0 accelerate>=0.30.0
```

### Import Validation
```bash
# The Dockerfile validates all critical imports:
RUN python -c "
import torch, runpod, diffusers, transformers, accelerate
print('✅ All critical imports successful')
"
```

### File Structure Validation
```bash
# Validates repository structure:
RUN test -f /workspace/train_character.py && \
    test -f /workspace/runpod_worker/worker.py && \
    test -f /workspace/runpod_worker/handler.py && \
    echo '✅ File structure validated'
```

## 🧪 **Testing Your Deployment**

### Pre-Deployment Testing
```bash
# Validate everything before deployment
python runpod_worker/validate_setup.py

# Test Docker build locally
docker build -t test-charforgex -f runpod_worker/Dockerfile .

# Test Docker image
docker run --rm test-charforgex python -c "
import sys
sys.path.append('/workspace')
sys.path.append('/workspace/runpod_worker')
import runpod_worker.worker as w
print('✅ Worker import successful')
"
```

### Post-Deployment Testing
```bash
# Test the deployed endpoint
python runpod_worker/test_worker.py \
  https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  YOUR_API_KEY

# Test with GUI
cd runpod_worker/gui
python -m http.server 8080
# Open http://localhost:8080
```

## 🔑 **Required Environment Variables**

Set these in your RunPod endpoint:
```bash
HF_TOKEN=your_huggingface_token
CIVITAI_API_KEY=your_civitai_key
GOOGLE_API_KEY=your_google_genai_key
FAL_KEY=your_fal_ai_key
```

## 📋 **Deployment Checklist**

### Before Deployment
- [ ] Repository is public or you have access credentials
- [ ] All required files are in the repository
- [ ] Python syntax is valid for all .py files
- [ ] Docker is installed and running
- [ ] You have Docker registry credentials
- [ ] You have RunPod API key

### During Deployment
- [ ] Repository validation passes
- [ ] File structure validation passes
- [ ] Docker build completes successfully
- [ ] Docker image tests pass
- [ ] Image pushes to registry successfully
- [ ] RunPod resources are created
- [ ] Endpoint becomes active

### After Deployment
- [ ] Health check passes
- [ ] Environment variables are set
- [ ] Test training works
- [ ] Test inference works
- [ ] GUI is accessible

## 🚨 **Common Issues & Solutions**

### Repository Access Issues
```bash
# Make repository public or use access token
git clone https://username:token@github.com/username/repo.git
```

### Missing System Packages
```bash
# The Dockerfile includes comprehensive packages
# If issues persist, add to Dockerfile:
RUN apt-get update && apt-get install -y your-missing-package
```

### Python Import Errors
```bash
# Validate imports locally first:
python -c "import torch, runpod, diffusers"

# Check requirements.txt includes all dependencies
```

### Docker Build Failures
```bash
# Build with verbose output:
docker build --progress=plain -t test -f runpod_worker/Dockerfile .

# Check Docker daemon is running:
docker info
```

## 🎉 **Success Indicators**

When deployment is successful, you'll see:
```
✅ Repository validation passed
✅ File structure validated  
✅ Docker image built successfully
✅ All import tests passed
✅ Image pushed to registry
✅ RunPod template created
✅ RunPod endpoint created
✅ Health check passed
🎉 Git-based deployment completed successfully!
```

Your CharForgex system is now running from your Git repository with full validation and error handling!

## 📖 **Additional Resources**

- **Validation Script**: `validate_setup.py`
- **Git Deployment**: `deploy_from_git.py`
- **Testing**: `test_worker.py`
- **Client Example**: `client_example.py`
- **Troubleshooting**: `README.md`
