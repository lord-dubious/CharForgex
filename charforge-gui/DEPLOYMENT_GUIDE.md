# CharForge GUI Deployment Guide

## 🚀 Complete Deployment Options

### Option 1: Development Mode (Recommended for Testing)

```bash
cd charforge-gui
./start-dev.sh
```

**Access URLs:**
- Frontend: http://localhost:5173 or http://YOUR_IP:5173
- Backend: http://localhost:8000 or http://YOUR_IP:8000
- API Docs: http://YOUR_IP:8000/docs

### Option 2: Docker Development

```bash
cd charforge-gui
./deploy.sh development
```

**Benefits:**
- Containerized environment
- Easy to reproduce
- Better isolation
- Automatic dependency management

### Option 3: Production Deployment

```bash
cd charforge-gui
./deploy.sh production yourdomain.com your@email.com
```

**Features:**
- SSL/HTTPS support
- Nginx reverse proxy
- Production optimizations
- Security headers

## 🌐 Remote Access Configuration

### Cloud Deployment (AWS, Google Cloud, Azure, etc.)

1. **Launch a server instance:**
   - Minimum: 2 CPU, 4GB RAM, 20GB storage
   - Recommended: 4 CPU, 8GB RAM, 50GB storage
   - OS: Ubuntu 20.04+ or similar

2. **Install dependencies:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   
   # Logout and login again for Docker group changes
   ```

3. **Clone and deploy:**
   ```bash
   git clone <your-repo-url>
   cd charforge-gui
   ./deploy.sh development  # or production
   ```

4. **Configure firewall:**
   ```bash
   sudo ufw allow 22      # SSH
   sudo ufw allow 80      # HTTP
   sudo ufw allow 443     # HTTPS
   sudo ufw allow 5173    # Frontend (development)
   sudo ufw allow 8000    # Backend (development)
   sudo ufw enable
   ```

### Local Network Deployment

1. **Find your local IP:**
   ```bash
   ip addr show | grep "inet " | grep -v 127.0.0.1
   ```

2. **Deploy normally:**
   ```bash
   ./start-dev.sh
   ```

3. **Access from other devices:**
   - Use http://YOUR_LOCAL_IP:5173

### VPS/Dedicated Server

1. **Secure the server:**
   ```bash
   # Change SSH port (optional)
   sudo nano /etc/ssh/sshd_config
   # Port 2222
   sudo systemctl restart ssh
   
   # Setup fail2ban
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   ```

2. **Deploy with domain:**
   ```bash
   ./deploy.sh production yourdomain.com admin@yourdomain.com
   ```

## 🔧 Configuration

### Environment Variables

Create `.env` file in the backend directory:

```env
# Security
SECRET_KEY=your-super-secret-key-here

# CharForge Integration
HF_TOKEN=hf_your_huggingface_token
HF_HOME=/path/to/huggingface/cache
CIVITAI_API_KEY=your_civitai_key
GOOGLE_API_KEY=your_google_genai_key
FAL_KEY=your_fal_ai_key

# Database
DATABASE_URL=sqlite:///./database.db

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### API Keys Setup

1. **HuggingFace Token:**
   - Go to https://huggingface.co/settings/tokens
   - Create a new token with read permissions
   - Add to HF_TOKEN in settings

2. **Google GenAI API Key:**
   - Go to https://makersuite.google.com/app/apikey
   - Create a new API key
   - Add to GOOGLE_API_KEY in settings

3. **FAL.AI Key:**
   - Go to https://fal.ai/dashboard
   - Get your API key
   - Add to FAL_KEY in settings

4. **CivitAI Key (Optional):**
   - Go to https://civitai.com/user/account
   - Generate API key
   - Add to CIVITAI_API_KEY in settings

## 🔒 Security Considerations

### Development Mode
- Use only in trusted networks
- Not suitable for public internet exposure
- Default credentials should be changed

### Production Mode
- SSL/TLS encryption enabled
- Security headers configured
- Regular security updates recommended
- Use strong passwords and API keys

### Firewall Rules
```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 📊 Monitoring and Maintenance

### View Logs
```bash
# Development mode
tail -f backend/logs/app.log

# Docker mode
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Health Checks
- Backend health: http://YOUR_IP:8000/health
- Frontend: Check if UI loads properly
- API docs: http://YOUR_IP:8000/docs

### Backup
```bash
# Backup database
cp backend/database.db backup/database_$(date +%Y%m%d).db

# Backup media files
tar -czf backup/media_$(date +%Y%m%d).tar.gz backend/media/

# Backup results
tar -czf backup/results_$(date +%Y%m%d).tar.gz backend/results/
```

### Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   sudo lsof -i :5173
   sudo lsof -i :8000
   # Kill processes if needed
   ```

2. **Permission denied:**
   ```bash
   sudo chown -R $USER:$USER charforge-gui/
   chmod +x start-dev.sh deploy.sh
   ```

3. **Docker issues:**
   ```bash
   # Restart Docker
   sudo systemctl restart docker
   
   # Clean up
   docker system prune -a
   ```

4. **API connection issues:**
   - Check firewall settings
   - Verify CORS configuration
   - Check network connectivity

### Getting Help

1. Check logs for error messages
2. Verify all API keys are configured
3. Ensure CharForge dependencies are installed
4. Check file permissions for uploads
5. Verify network connectivity

## 📈 Performance Optimization

### For High Traffic
- Use production deployment with Nginx
- Enable gzip compression
- Use CDN for static assets
- Monitor resource usage

### For Large Files
- Increase upload limits in nginx.conf
- Configure appropriate timeout values
- Monitor disk space usage

### For Multiple Users
- Consider using PostgreSQL instead of SQLite
- Implement user quotas
- Monitor concurrent training sessions
