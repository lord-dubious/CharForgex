# CharForgex RunPod Worker - Quick Start Guide

## 🚀 Deploy in 5 Minutes

### Step 1: Prepare Deployment
```bash
cd runpod_worker
chmod +x setup_runpod.sh
./setup_runpod.sh
```

### Step 2: Deploy to RunPod
```bash
# Replace with your container registry
python deploy_to_runpod.py --registry docker.io/yourusername
```

### Step 3: Create RunPod Resources
1. **Template**: Use generated `template_config.json`
2. **Endpoint**: Use generated `endpoint_config.json`  
3. **Environment**: Set your API keys

### Step 4: Test & Use
```bash
# Test the deployment
python test_worker.py https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync YOUR_API_KEY

# Use the GUI
cd gui && python -m http.server 8080
```

## 🎯 What You Get

### ✅ **Removed Authentication System**
- No login/signup required
- Single-user mode optimized for personal use
- Simplified deployment and configuration

### ✅ **Enhanced Stability & Recovery**
- Automatic GPU memory management
- Robust error handling with retries
- Graceful degradation on resource constraints
- Automatic cleanup of temporary files

### ✅ **Persistent Storage**
- LoRAs survive worker restarts
- Model caching reduces cold start times
- Datasets preserved across sessions
- Organized file structure

### ✅ **Improved GUI**
- Clean, responsive interface
- Real-time progress tracking
- Better error messages
- Automatic connection testing

### ✅ **API Enhancements**
- Input validation and parameter clamping
- Comprehensive error responses
- System status monitoring
- Multiple operation types

## 🔧 Key Improvements Made

### 1. **Authentication Removal**
- Disabled user authentication system
- Removed login/registration flows
- Single-user mode for simplified deployment
- No database requirements for user management

### 2. **Error Handling & Recovery**
- GPU memory cleanup on failures
- Automatic retry logic for transient errors
- Parameter validation and clamping
- Graceful fallback options

### 3. **Performance Optimizations**
- Model caching in persistent storage
- Optimized Docker image layers
- Reduced cold start times
- Memory-efficient operations

### 4. **Deployment Simplification**
- Automated build and deployment scripts
- Pre-configured RunPod templates
- Environment variable management
- Comprehensive documentation

### 5. **Monitoring & Debugging**
- Detailed system status reporting
- GPU and storage monitoring
- Structured logging
- Health check endpoints

## 📊 Performance Expectations

| Operation | Time | GPU Memory | Notes |
|-----------|------|------------|-------|
| Cold Start | 2-3 min | - | First request only |
| Model Loading | 60s | 20GB | Cached after first use |
| Training | 30-40 min | 45GB | RTX A6000 recommended |
| Inference (1 image) | 30-60s | 25GB | RTX A5000 minimum |
| Inference (4 images) | 2-3 min | 35GB | Batch processing |

## 💰 Cost Optimization

### Recommended Settings
- **GPU**: RTX A5000 for inference, RTX A6000 for training
- **Idle Timeout**: 5 minutes
- **Max Workers**: 3
- **Network Volume**: 200GB+
- **Use Spot Instances**: For non-critical training

### Cost Estimates (Approximate)
- **Training**: $2-4 per character (30-40 min on RTX A6000)
- **Inference**: $0.10-0.20 per image (RTX A5000)
- **Storage**: $0.10/GB/month for network volume

## 🛡️ Security & Data

### Data Persistence
- **LoRAs**: `/runpod-volume/loras/` - Permanent storage
- **Models**: `/runpod-volume/huggingface/` - Cached models
- **Datasets**: `/runpod-volume/datasets/` - Training data
- **Outputs**: `/runpod-volume/outputs/` - Generated images

### Security Features
- No authentication system (single-user)
- API keys stored as environment variables
- Input validation and sanitization
- Automatic cleanup of sensitive temporary files
- No data logging of user content

## 🔗 Integration Examples

### Python Client
```python
from runpod_worker.client_example import CharForgexClient

client = CharForgexClient("endpoint_id", "api_key")
client.train_character("anime_girl", "reference.jpg")
images = client.generate_images("anime_girl", "portrait, detailed")
```

### cURL API
```bash
# Health check
curl -X POST $ENDPOINT_URL \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"input": {"operation": "health_check"}}'

# Generate image
curl -X POST $ENDPOINT_URL \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"input": {"operation": "inference", "character_name": "my_char", "prompt": "portrait"}}'
```

### Web GUI
- Simple drag-and-drop interface
- Real-time progress tracking
- Character management
- Image gallery and downloads

## 🆘 Support & Troubleshooting

### Common Issues
1. **Cold Start Timeout**: Increase timeout, use FlashBoot
2. **Memory Errors**: Reduce batch size, use larger GPU
3. **Training Failures**: Check API keys, verify image format
4. **Connection Issues**: Verify endpoint URL and API key

### Debug Tools
- `system_status` operation for diagnostics
- `clear_cache` operation for memory cleanup
- Comprehensive logging in RunPod console
- Test script for validation

### Getting Help
- 📖 Full documentation in `RUNPOD_DEPLOYMENT.md`
- 🧪 Test with `test_worker.py`
- 💻 Example code in `client_example.py`
- 🌐 GUI for visual interface

---

**Ready to deploy? Follow the [Complete Deployment Guide](RUNPOD_DEPLOYMENT.md)!**
