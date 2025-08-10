# CharForgex RunPod Worker - Complete Deployment Guide

## Overview

This guide will help you deploy CharForgex as a RunPod serverless worker, enabling you to:
- Train character LoRAs in the cloud
- Generate images with trained characters
- Access via a simple web GUI or API
- Persistent storage for models and LoRAs
- Automatic scaling and cost optimization

## Prerequisites

1. **RunPod Account** with credits
2. **Container Registry** (Docker Hub, GitHub Container Registry, etc.)
3. **API Keys**:
   - Hugging Face token (for Flux.1-dev access)
   - CivitAI API key
   - Google GenAI API key
   - FAL.ai API key
4. **Docker** installed locally

## Step 1: Prepare the Deployment

### 1.1 Build and Test Locally

```bash
# From CharForgex root directory
cd runpod_worker
chmod +x setup_runpod.sh
./setup_runpod.sh
```

This will:
- Build the Docker image
- Test basic functionality
- Create configuration files

### 1.2 Push to Container Registry

```bash
# Tag for your registry (replace with your registry)
docker tag charforgex-runpod:latest your-username/charforgex-runpod:latest

# Push to registry
docker push your-username/charforgex-runpod:latest
```

## Step 2: Create RunPod Template

1. Go to [RunPod Console → Templates](https://console.runpod.io/templates)
2. Click **"New Template"**
3. Configure:
   - **Name**: CharForgex Worker
   - **Image**: `your-username/charforgex-runpod:latest`
   - **Container Disk**: 50GB
   - **Volume Mount Path**: `/runpod-volume`
   - **Ports**: `8000/http` (for GUI access)
   - **Start Jupyter**: No
   - **Start SSH**: No

## Step 3: Create Network Volume (Recommended)

1. Go to [RunPod Console → Storage](https://console.runpod.io/storage)
2. Create new Network Volume:
   - **Name**: charforgex-storage
   - **Size**: 200GB+ (for model caching and LoRA storage)
   - **Region**: Same as your preferred GPU region

## Step 4: Create Serverless Endpoint

1. Go to [RunPod Console → Serverless](https://console.runpod.io/serverless)
2. Click **"New Endpoint"**
3. Configure:
   - **Name**: CharForgex
   - **Template**: Select your CharForgex template
   - **GPU Types**: RTX A5000, RTX A6000, RTX 4090
   - **Max Workers**: 3
   - **Idle Timeout**: 5 minutes
   - **FlashBoot**: Enabled
   - **Network Volume**: Attach your charforgex-storage volume

### 4.1 Environment Variables

Add these environment variables to your endpoint:

```bash
HF_TOKEN=your_huggingface_token
CIVITAI_API_KEY=your_civitai_api_key
GOOGLE_API_KEY=your_google_genai_api_key
FAL_KEY=your_fal_ai_api_key
```

## Step 5: Test Your Deployment

### 5.1 Health Check

```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"operation": "health_check"}}'
```

### 5.2 List Characters

```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"operation": "list_characters"}}'
```

## Step 6: Use the Web GUI

### 6.1 Serve GUI Locally

```bash
cd runpod_worker/gui
python -m http.server 8080
```

### 6.2 Configure GUI

1. Open http://localhost:8080
2. Enter your RunPod endpoint URL: `https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync`
3. Enter your RunPod API key
4. Click "Test Connection"

## API Usage Examples

### Train a Character

```bash
# Convert image to base64 first
IMAGE_B64=$(base64 -w 0 your_character_image.jpg)

curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": {
      \"operation\": \"training\",
      \"character_name\": \"my_character\",
      \"input_image\": \"$IMAGE_B64\",
      \"steps\": 800,
      \"learning_rate\": 8e-4,
      \"rank_dim\": 8
    }
  }"
```

### Generate Images

```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "operation": "inference",
      "character_name": "my_character",
      "prompt": "portrait of my_character, detailed face, high quality",
      "lora_weight": 0.73,
      "test_dim": 1024,
      "batch_size": 1,
      "num_inference_steps": 30
    }
  }'
```

## Performance & Cost Optimization

### GPU Recommendations

- **Training**: RTX A6000 (48GB) or better
- **Inference**: RTX A5000 (24GB) minimum
- **Batch Inference**: RTX 4090 or A6000 for multiple images

### Cost Optimization Tips

1. **Use Spot Instances** for training (non-critical)
2. **Set Idle Timeout** to 5 minutes to minimize costs
3. **Use Network Volumes** to avoid re-downloading models
4. **Batch Requests** when possible
5. **Monitor Usage** in RunPod billing dashboard

### Performance Expectations

- **Cold Start**: 2-3 minutes (first request)
- **Warm Inference**: 30-60 seconds per image
- **Training**: 30-40 minutes per character
- **Model Loading**: ~1 minute after cold start

## Troubleshooting

### Common Issues

1. **Cold Start Timeout**
   - Increase timeout in RunPod settings
   - Use FlashBoot for faster startup

2. **Out of Memory Errors**
   - Reduce batch_size to 1
   - Lower image dimensions
   - Use GPU with more VRAM

3. **Training Failures**
   - Check all API keys are set correctly
   - Verify input image is valid
   - Check disk space availability

4. **Model Download Issues**
   - Verify HF_TOKEN has access to Flux.1-dev
   - Check network connectivity
   - Ensure sufficient storage space

### Debug Commands

```bash
# Check system status
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"operation": "system_status"}}'

# Clear cache if needed
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"operation": "clear_cache"}}'
```

## Monitoring

### Logs
- Check RunPod console for worker logs
- Monitor GPU utilization during training/inference
- Watch for memory usage patterns

### Metrics
- Training time per character
- Inference time per image
- GPU memory usage
- Storage usage growth

## Security Notes

- API keys are stored as environment variables
- No authentication system (single-user mode)
- All data stored in persistent network volume
- Automatic cleanup of temporary files

## Support

For issues specific to:
- **RunPod Platform**: RunPod Discord/Support
- **CharForgex Logic**: Original CharForgex repository
- **Deployment Issues**: Check logs and follow troubleshooting guide
