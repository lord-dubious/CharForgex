# CharForgex GUI & Web Server Deployment Guide

## 🎯 **Complete GUI Integration**

The CharForgex system now includes a comprehensive web interface that works with both local testing and RunPod deployment.

---

## 🌐 **Web Server Features**

### **Integrated Web Server** (`web_server.py`)
- ✅ **FastAPI-based** - Modern async web framework
- ✅ **GUI serving** - Serves the Vue.js interface
- ✅ **Local API endpoints** - For testing without RunPod
- ✅ **RunPod proxy** - Forwards requests to RunPod endpoints
- ✅ **Health monitoring** - Real-time status checking
- ✅ **CORS enabled** - Cross-origin requests supported

### **Smart GUI** (`gui/`)
- ✅ **Dual mode operation** - Local API or RunPod endpoints
- ✅ **Auto-detection** - Switches between modes seamlessly
- ✅ **Real-time status** - Live worker status monitoring
- ✅ **Configuration persistence** - Saves settings locally
- ✅ **Error handling** - Comprehensive error reporting

---

## 🚀 **Deployment Options**

### **Option 1: RunPod with GUI Access**
```bash
# Deploy to RunPod with GUI enabled
cd runpod_worker
python deploy_from_git.py

# Set environment variable in RunPod endpoint:
STARTUP_MODE=both
```

**Access:**
- **Worker API**: `https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync`
- **GUI**: `https://YOUR_ENDPOINT_ID-8000.proxy.runpod.net`

### **Option 2: Local Development with GUI**
```bash
# Start local web server with GUI
cd runpod_worker
python web_server.py --port 8000

# Or start GUI only (no API)
python web_server.py --port 8000 --gui-only
```

**Access:**
- **GUI**: `http://localhost:8000`
- **Local API**: `http://localhost:8000/api/*`

### **Option 3: Separate GUI Client**
```bash
# Serve GUI separately for RunPod connection
cd runpod_worker/gui
python -m http.server 8080
```

**Access:**
- **GUI**: `http://localhost:8080`
- **Connects to**: RunPod endpoint

---

## 🔧 **Configuration Modes**

### **Local API Mode** (Testing)
- ✅ **No RunPod needed** - Test locally
- ✅ **Direct API calls** - Faster response
- ✅ **Full functionality** - All features available
- ⚠️ **Requires GPU** - For training/inference

**Setup:**
1. Start web server: `python web_server.py`
2. Open GUI: `http://localhost:8000`
3. Enable "Use Local API" checkbox
4. Click "Test Connection"

### **RunPod Mode** (Production)
- ✅ **Cloud GPU access** - No local GPU needed
- ✅ **Scalable** - Auto-scaling workers
- ✅ **Persistent storage** - Models saved to volume
- ✅ **Production ready** - Robust deployment

**Setup:**
1. Deploy to RunPod
2. Open GUI (local or RunPod)
3. Enter endpoint URL and API key
4. Click "Test Connection"

---

## 📋 **GUI Features**

### **Configuration Panel**
- **API Mode Toggle** - Switch between local/RunPod
- **Endpoint Configuration** - RunPod URL and API key
- **Connection Testing** - Real-time status check
- **Settings Persistence** - Automatic save/restore

### **Training Interface**
- **Character Creation** - Upload images and configure
- **Training Parameters** - Steps, learning rate, rank dimension
- **Progress Monitoring** - Real-time training status
- **Result Management** - Download trained LoRAs

### **Inference Interface**
- **Character Selection** - Choose from trained characters
- **Prompt Engineering** - Advanced prompt controls
- **Generation Settings** - Size, steps, batch size
- **Image Gallery** - View and download results

### **Character Management**
- **Character Library** - Browse available characters
- **LoRA Management** - Upload/download LoRA files
- **Metadata Display** - Training info and statistics

---

## 🔌 **API Endpoints**

### **Local API Endpoints**
```
GET  /                    # Serve GUI
GET  /health             # Health check
POST /api/inference      # Generate images
POST /api/training       # Train characters
GET  /api/characters     # List characters
POST /api/runpod         # Proxy to RunPod
```

### **RunPod API Format**
```json
{
  "input": {
    "operation": "inference|training|list_characters|health_check",
    "character_name": "character_name",
    "prompt": "your prompt here",
    "image_data": "base64_encoded_image",
    // ... other parameters
  }
}
```

---

## 🛠 **Development Setup**

### **Local Development**
```bash
# Install dependencies
pip install fastapi uvicorn

# Start development server
cd runpod_worker
python web_server.py --port 8000

# Access GUI
open http://localhost:8000
```

### **Docker Development**
```bash
# Build with GUI support
docker build -t charforgex-gui -f runpod_worker/Dockerfile .

# Run with GUI enabled
docker run -p 8000:8000 -e STARTUP_MODE=gui charforgex-gui

# Run with both worker and GUI
docker run -p 8000:8000 -e STARTUP_MODE=both charforgex-gui
```

---

## 🔍 **Troubleshooting**

### **GUI Not Loading**
```bash
# Check if web server is running
curl http://localhost:8000/health

# Check GUI files exist
ls runpod_worker/gui/

# Check for JavaScript errors in browser console
```

### **API Connection Issues**
```bash
# Test local API
curl http://localhost:8000/health

# Test RunPod API
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"operation": "health_check"}}'
```

### **CORS Issues**
- ✅ **CORS enabled** in FastAPI server
- ✅ **All origins allowed** for development
- ⚠️ **Configure properly** for production

---

## 📊 **Monitoring & Logging**

### **Web Server Logs**
```bash
# View web server logs
python web_server.py --port 8000

# Check specific endpoints
tail -f /var/log/charforgex-web.log
```

### **GUI Status Indicators**
- 🟢 **Green**: Worker online and ready
- 🟡 **Yellow**: Worker starting or degraded
- 🔴 **Red**: Worker offline or error
- 🔵 **Blue**: Local API mode active

---

## 🎯 **Production Deployment**

### **RunPod Template Configuration**
```json
{
  "name": "CharForgex with GUI",
  "imageName": "yourusername/charforgex-runpod:latest",
  "containerDiskInGb": 50,
  "volumeInGb": 200,
  "ports": "8000/http",
  "env": [
    {"key": "STARTUP_MODE", "value": "both"},
    {"key": "HF_TOKEN", "value": "your_token"},
    {"key": "CIVITAI_API_KEY", "value": "your_key"}
  ]
}
```

### **Environment Variables**
```bash
# Required for full functionality
HF_TOKEN=your_huggingface_token
CIVITAI_API_KEY=your_civitai_key
GOOGLE_API_KEY=your_google_genai_key
FAL_KEY=your_fal_ai_key

# Optional for GUI/worker mode
STARTUP_MODE=worker|gui|both  # Default: worker
```

---

## 🎉 **Quick Start**

### **1. Local Testing**
```bash
cd runpod_worker
python web_server.py
# Open http://localhost:8000
# Enable "Use Local API"
# Test connection
```

### **2. RunPod Deployment**
```bash
python deploy_from_git.py
# Set STARTUP_MODE=both in RunPod
# Access GUI via RunPod proxy URL
# Configure endpoint and API key
```

### **3. Production Use**
```bash
# Deploy with GUI enabled
# Configure monitoring
# Set up persistent storage
# Enable auto-scaling
```

**🚀 Your CharForgex system now has a complete web interface for both local development and production deployment!**
