# CharForgex RunPod Worker - Git Repository Deployment
FROM runpod/pytorch:0.7.0-cu1241-torch251-ubuntu2004

# Set working directory
WORKDIR /workspace

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PLATFORM=serverless
ENV COMFYUI_PATH=/workspace/ComfyUI
ENV HF_HOME=/runpod-volume/huggingface
ENV APP_PATH=/workspace
ENV TORCH_CUDA_ARCH_LIST="6.0 6.1 7.0 7.5 8.0 8.6+PTX"
ENV FORCE_CUDA="1"
ENV PYTHONPATH="/workspace:/workspace/runpod_worker"

# Install comprehensive system dependencies
RUN apt-get update && apt-get install -y \
    # Core system tools
    git \
    git-lfs \
    wget \
    curl \
    unzip \
    build-essential \
    # Python build dependencies
    python3-dev \
    python3-pip \
    python3-venv \
    # Graphics and media libraries
    libgl1-mesa-glx \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libglib2.0-dev \
    libgtk-3-0 \
    libgtk-3-dev \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    # Image processing libraries
    libopencv-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1 \
    libice6 \
    libxt6 \
    # Audio/Video processing
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    # Additional utilities
    tmux \
    nano \
    htop \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv for faster package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Clone the repository (for Git-based deployment)
ARG REPO_URL=https://github.com/lord-dubious/CharForgex.git
ARG BRANCH=main
RUN git clone --depth 1 --branch ${BRANCH} ${REPO_URL} /workspace || \
    (echo "Failed to clone repository. Falling back to COPY." && exit 0)

# Copy local files if git clone failed (for local builds)
COPY . /workspace/

# Ensure we have the repository structure
RUN ls -la /workspace/ && \
    test -f /workspace/train_character.py || (echo "ERROR: train_character.py not found!" && exit 1) && \
    test -f /workspace/base_requirements.txt || (echo "ERROR: base_requirements.txt not found!" && exit 1) && \
    test -f /workspace/install.py || (echo "ERROR: install.py not found!" && exit 1)

# Remove authentication from GUI backend (single-user mode) - handle missing directories gracefully
RUN cd /workspace && \
    if [ -d "charforge-gui/backend" ]; then \
        find charforge-gui/backend -name "*.py" -exec sed -i 's/ENABLE_AUTH=true/ENABLE_AUTH=false/g' {} \; 2>/dev/null || true; \
        find charforge-gui/backend -name "*.py" -exec sed -i 's/ALLOW_REGISTRATION=true/ALLOW_REGISTRATION=false/g' {} \; 2>/dev/null || true; \
    fi

# Create Python virtual environment
RUN cd /workspace && \
    python3 -m venv .venv && \
    . .venv/bin/activate && \
    pip install --upgrade pip setuptools wheel

# Install RunPod SDK and core dependencies first
RUN cd /workspace && \
    . .venv/bin/activate && \
    pip install runpod>=1.6.0 requests>=2.31.0 pillow>=10.0.0 numpy>=1.24.0 \
                opencv-python-headless>=4.8.0 psutil>=5.9.0 fastapi>=0.100.0 \
                pydantic>=2.0.0 python-multipart>=0.0.6 uvicorn>=0.20.0

# Install PyTorch with CUDA support (use available version)
RUN cd /workspace && \
    . .venv/bin/activate && \
    pip install torch==2.4.1+cu121 torchvision==0.19.1+cu121 torchaudio==2.4.1+cu121 \
                --index-url https://download.pytorch.org/whl/cu121

# Install base requirements
RUN cd /workspace && \
    . .venv/bin/activate && \
    pip install -r base_requirements.txt

# Install project dependencies with error handling
RUN cd /workspace && \
    . .venv/bin/activate && \
    python install.py --platform serverless || \
    (echo "install.py failed, continuing with manual setup..." && \
     pip install diffusers>=0.30.0 transformers>=4.40.0 accelerate>=0.30.0 \
                 scikit-image>=0.21.0 python-dotenv>=1.0.0 tqdm>=4.65.0)

# Create necessary directories with proper permissions
RUN mkdir -p /runpod-volume/models /runpod-volume/loras /runpod-volume/datasets /runpod-volume/outputs \
             /runpod-volume/huggingface /workspace/scratch /tmp/charforge && \
    chmod -R 755 /runpod-volume /workspace/scratch /tmp/charforge

# Verify RunPod worker files exist (they should be in the repo)
RUN test -f /workspace/runpod_worker/worker.py || (echo "ERROR: worker.py not found!" && exit 1) && \
    test -f /workspace/runpod_worker/handler.py || (echo "ERROR: handler.py not found!" && exit 1) && \
    test -f /workspace/runpod_worker/utils.py || (echo "ERROR: utils.py not found!" && exit 1)

# Make scripts executable with error handling
RUN find /workspace -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true && \
    find /workspace/runpod_worker -name "*.py" -type f -exec chmod +x {} \; 2>/dev/null || true

# Create robust startup script that matches RunPod patterns
COPY runpod_worker/start.sh /workspace/start.sh
RUN chmod +x /workspace/start.sh

# Verify Python imports work
RUN cd /workspace && \
    . .venv/bin/activate && \
    python -c "import sys; print('✅ Python version:', sys.version.split()[0])" && \
    python -c "import torch; print('✅ PyTorch:', torch.__version__); print('✅ CUDA available:', torch.cuda.is_available())" && \
    python -c "import runpod; print('✅ RunPod SDK:', runpod.__version__)" && \
    python -c "import diffusers, transformers, accelerate; print('✅ ML libraries imported successfully')" && \
    echo "✅ All critical imports successful"

# Health check with better error handling
HEALTHCHECK --interval=60s --timeout=30s --start-period=10m --retries=3 \
    CMD cd /workspace && . .venv/bin/activate && \
        python -c "import requests; import sys; response = requests.get('http://localhost:8000', timeout=10); sys.exit(0 if response.status_code == 200 else 1)" || \
        python -c "import runpod_worker.utils; exit(0)" || exit 1

# Create non-root user for security
RUN useradd -m -u 1000 runpod && \
    mkdir -p /runpod-volume && \
    chown -R runpod:runpod /workspace && \
    chmod -R 755 /workspace

# Note: Don't change ownership of /runpod-volume as it may be mounted
# Switch to non-root user
USER runpod

# Expose ports
EXPOSE 8000

# Set the default command
CMD ["/workspace/start.sh"]
