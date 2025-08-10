# CharForgex RunPod Worker

Transform your CharForgex system into a powerful cloud-based RunPod serverless worker for scalable AI character LoRA training and inference.

## 🚀 Quick Start

### 1. Build and Deploy

```bash
# Make setup script executable and run
chmod +x setup_runpod.sh
./setup_runpod.sh

# Push to your container registry
docker tag charforgex-runpod:latest your-registry/charforgex-runpod:latest
docker push your-registry/charforgex-runpod:latest
```

### 2. Create RunPod Resources

1. **Template**: Use `config.json` settings
2. **Network Volume**: 200GB+ for persistent storage
3. **Endpoint**: Configure with your image and API keys

### 3. Test Deployment

```bash
# Test the worker
python test_worker.py https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync YOUR_API_KEY

# Or use the GUI
cd gui && python -m http.server 8080
```

## 📁 File Structure

```
runpod_worker/
├── Dockerfile              # Container definition
├── worker.py              # Main RunPod worker entry point
├── handler.py             # Request handling with error recovery
├── utils.py               # Utility functions
├── start_worker.py        # Startup script with environment setup
├── deploy.py              # Automated deployment script
├── client_example.py      # Python client example
├── test_worker.py         # Testing script
├── requirements.txt       # Python dependencies
├── config.json           # RunPod configuration templates
├── setup_runpod.sh       # Setup and build script
├── docker-compose.yml    # Local testing with Docker
├── gui/                  # Simplified web interface
│   ├── index.html        # Main GUI page
│   └── app.js           # Vue.js application
└── README.md            # This file
```

## 🎯 Key Features

### ✅ **Improvements Made**
- **Removed Authentication**: Single-user mode for simplified deployment
- **Enhanced Error Handling**: Robust recovery mechanisms
- **Persistent Storage**: LoRAs and datasets survive worker restarts
- **Optimized Performance**: Model caching and memory management
- **Simplified GUI**: Clean interface optimized for cloud use
- **Comprehensive Logging**: Detailed logs for debugging
- **Auto-cleanup**: Temporary files automatically removed

### 🔧 **Technical Enhancements**
- **GPU Memory Management**: Automatic cleanup and recovery
- **Parameter Validation**: Input clamping and validation
- **Retry Logic**: Automatic retries for transient failures
- **Progress Tracking**: Real-time training progress updates
- **Health Monitoring**: System status and resource monitoring
- **Graceful Degradation**: Fallback options for resource constraints

## 🎮 Usage Examples

### Training a Character

```python
from client_example import CharForgexClient

client = CharForgexClient("your_endpoint_id", "your_api_key")

# Train a character
result = client.train_character(
    character_name="anime_girl",
    image_path="reference.jpg",
    steps=800,
    learning_rate=8e-4,
    rank_dim=8
)
```

### Generating Images

```python
# Generate images
images = client.generate_images(
    character_name="anime_girl",
    prompt="portrait of anime_girl, detailed face, high quality",
    batch_size=4,
    save_to_dir="./outputs"
)
```

### Using the Web GUI

1. Open the GUI at your RunPod endpoint URL + `:8000`
2. Configure your endpoint URL and API key
3. Upload reference images and train characters
4. Generate images with trained LoRAs

## 🔧 Configuration

### Environment Variables

Required in RunPod endpoint:
```bash
HF_TOKEN=your_huggingface_token
CIVITAI_API_KEY=your_civitai_api_key
GOOGLE_API_KEY=your_google_genai_api_key
FAL_KEY=your_fal_ai_api_key
```

Optional:
```bash
STARTUP_MODE=worker          # worker, gui, or both
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
MAX_TRAINING_TIME=3600      # Maximum training time in seconds
MAX_BATCH_SIZE=4            # Maximum batch size for inference
```

### GPU Requirements

| Operation | Minimum VRAM | Recommended | Notes |
|-----------|--------------|-------------|-------|
| Inference | 24GB | 48GB | RTX A5000+ |
| Training | 48GB | 80GB | RTX A6000+ |
| Batch Inference | 48GB | 80GB | For batch_size > 1 |

### Storage Requirements

- **Container Disk**: 50GB minimum
- **Network Volume**: 200GB+ recommended
- **Model Cache**: ~50GB for all models
- **Per Character**: ~500MB (dataset + LoRA)

## 📊 Performance Metrics

### Expected Performance
- **Cold Start**: 2-3 minutes (model loading)
- **Warm Inference**: 30-60 seconds per image
- **Training Time**: 30-40 minutes per character
- **Model Loading**: ~60 seconds after cold start

### Cost Optimization
- **Idle Timeout**: 5 minutes recommended
- **Spot Instances**: Use for training (non-critical)
- **Network Volumes**: Prevent model re-downloading
- **Batch Requests**: More efficient for multiple images

## 🛠 API Operations

| Operation | Endpoint | Description | Timeout |
|-----------|----------|-------------|---------|
| `health_check` | `/runsync` | System status | 30s |
| `training` | `/run` | Train character LoRA | 60min |
| `inference` | `/runsync` | Generate images | 5min |
| `list_characters` | `/runsync` | List trained characters | 30s |
| `system_status` | `/runsync` | Detailed system info | 30s |
| `clear_cache` | `/runsync` | Clear temp files/memory | 60s |

## 🔍 Troubleshooting

### Common Issues

1. **Cold Start Timeout**
   ```bash
   # Increase timeout in RunPod endpoint settings
   # Use FlashBoot for faster startup
   ```

2. **Out of Memory**
   ```bash
   # Reduce batch size or image dimensions
   curl -X POST $ENDPOINT_URL -d '{"input": {"operation": "clear_cache"}}'
   ```

3. **Training Failures**
   ```bash
   # Check system status
   curl -X POST $ENDPOINT_URL -d '{"input": {"operation": "system_status"}}'
   ```

### Debug Commands

```bash
# Check worker health
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d '{"input": {"operation": "system_status"}}'

# List available characters
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d '{"input": {"operation": "list_characters"}}'
```

## 🔒 Security & Data Persistence

### Data Storage
- **LoRAs**: Persistent in `/runpod-volume/loras/`
- **Datasets**: Persistent in `/runpod-volume/datasets/`
- **Models**: Cached in `/runpod-volume/huggingface/`
- **Outputs**: Saved in `/runpod-volume/outputs/`

### Security Features
- No authentication system (single-user mode)
- API keys stored as environment variables
- Automatic cleanup of temporary files
- Input validation and sanitization
- Error logging without sensitive data exposure

## 📈 Monitoring

### Logs
- Worker logs available in RunPod console
- Structured logging with timestamps
- Error tracking with stack traces
- Performance metrics logging

### Metrics to Monitor
- GPU utilization during operations
- Memory usage patterns
- Training completion rates
- Average inference times
- Storage usage growth

## 🆘 Support

### Getting Help
1. Check RunPod console logs
2. Use system_status operation for diagnostics
3. Review troubleshooting section
4. Test with provided client examples

### Known Limitations
- Single-user mode only
- Requires GPU with 24GB+ VRAM
- Training jobs limited to 60 minutes
- Maximum 4 images per batch for inference

## 📝 License

This RunPod worker implementation is part of the CharForgex ecosystem. See the main repository for license information.
