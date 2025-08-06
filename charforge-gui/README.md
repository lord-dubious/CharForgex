# CharForge GUI

A beautiful Vue.js frontend with FastAPI backend for controlling the CharForge AI-powered character LoRA creation pipeline.

## Features

### 🎨 **Beautiful UI with ShadCN/Vue**
- Modern, responsive design with TailwindCSS
- Dark/light mode support
- Accessible components following design system principles

### 🔐 **Authentication & Security (Optional)**
- **Optional Authentication**: Enable/disable user authentication via environment variable
- **Default Mode**: No authentication required - perfect for local/personal use
- **Secure Mode**: JWT-based authentication when enabled
- **Flexible Configuration**: Toggle registration and set default users
- **Secure API**: Rate limiting and security headers included

### 🎯 **Core Functionality**
- **Character Management**: Create, view, and manage AI characters
- **Training Workflow**: Full integration with CharForge training pipeline
- **Real-time Progress**: WebSocket updates for training progress
- **Inference Interface**: Generate images with trained LoRAs
- **Media Management**: Upload, organize, and process images
- **Settings Management**: Configure environment variables via UI

### 🔧 **Technical Stack**
- **Frontend**: Vue 3 + Vite + TypeScript + ShadCN/Vue + TailwindCSS
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **State Management**: Pinia
- **API Client**: Axios with interceptors
- **Real-time**: WebSocket support
- **File Handling**: Drag-and-drop uploads with image processing

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn
- Docker & Docker Compose (for containerized deployment)

### 🚀 Development Setup (Local)

```bash
# Clone and start the development environment
./start-dev.sh
```

This script will:
1. ✅ Check all dependencies
2. 🔧 Set up Python virtual environment
3. 📦 Install all dependencies
4. 🔑 Create environment configuration
5. 🚀 Start both frontend and backend servers

### 🐳 Docker Deployment (Recommended for Remote Access)

```bash
# Development with Docker
./deploy.sh development

# Production with Docker (with SSL)
./deploy.sh production yourdomain.com your@email.com
```

### 🌐 Remote Access Setup

For remote access, the application is configured to work seamlessly:

1. **Automatic Network Binding**: Both frontend and backend bind to `0.0.0.0`
2. **CORS Configuration**: Allows cross-origin requests
3. **Proxy Setup**: Internal proxying handles API requests
4. **Firewall Ports**: Ensure ports 5173 and 8000 are open

### Manual Setup

#### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file with your API keys
cp .env.example .env
# Edit .env with your actual API keys

# Start the backend
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Authentication Configuration (Optional)

**By default, authentication is DISABLED** for ease of use. The application works without any login/signup process.

### Default Mode (No Authentication)
- ✅ No login/signup required
- ✅ All features work immediately
- ✅ Uses a default user account automatically
- ✅ Perfect for local/personal use

### Secure Mode (Authentication Enabled)
To enable authentication, set these environment variables:

```bash
# Enable authentication and registration
ENABLE_AUTH=true
ALLOW_REGISTRATION=true

# Or just enable auth without registration
ENABLE_AUTH=true
ALLOW_REGISTRATION=false
```

When enabled:
- 🔐 Users must register/login
- 👥 Multi-user support
- 🛡️ Secure JWT-based authentication
- 🔒 User isolation and data protection

## Environment Configuration

Create a `.env` file in the `backend` directory:

```env
# Security
SECRET_KEY=your-secret-key-change-this-in-production

# Database
DATABASE_URL=sqlite:///./database.db

# CharForge API Keys
HF_TOKEN=your_huggingface_token
HF_HOME=/path/to/huggingface/cache
CIVITAI_API_KEY=your_civitai_key
GOOGLE_API_KEY=your_google_genai_key
FAL_KEY=your_fal_ai_key
```

## Usage

### 🌐 Accessing the Application

**Local Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

**Remote Access:**
- Frontend: http://YOUR_SERVER_IP:5173
- Backend API: http://YOUR_SERVER_IP:8000
- API Docs: http://YOUR_SERVER_IP:8000/docs

### 1. **First Time Setup**
1. Register a new account at the frontend URL
2. Login and go to Settings to configure your API keys
3. Test your environment configuration

### 2. **Create a Character**
1. Go to Characters → Create Character
2. Upload a reference image
3. Configure training parameters
4. Start the training process

### 3. **Monitor Training**
1. View real-time progress in the Training section
2. Check logs and training metrics
3. Get notified when training completes

### 4. **Generate Images**
1. Go to Inference section
2. Select your trained character
3. Enter a prompt
4. Configure generation settings
5. Generate and download images

### 🔧 Remote Access Configuration

#### For Cloud/VPS Deployment:

1. **Firewall Configuration:**
   ```bash
   # Ubuntu/Debian
   sudo ufw allow 5173
   sudo ufw allow 8000

   # CentOS/RHEL
   sudo firewall-cmd --permanent --add-port=5173/tcp
   sudo firewall-cmd --permanent --add-port=8000/tcp
   sudo firewall-cmd --reload
   ```

2. **Cloud Provider Security Groups:**
   - AWS: Add inbound rules for ports 5173 and 8000
   - Google Cloud: Create firewall rules for these ports
   - Azure: Configure Network Security Group rules

3. **Domain Setup (Optional):**
   ```bash
   # Use production deployment with your domain
   ./deploy.sh production yourdomain.com your@email.com
   ```

#### For Local Network Access:

1. **Find your local IP:**
   ```bash
   # Linux/Mac
   hostname -I | awk '{print $1}'

   # Windows
   ipconfig | findstr IPv4
   ```

2. **Access from other devices:**
   - Use http://YOUR_LOCAL_IP:5173 from any device on the same network

## API Documentation

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## Architecture

```
charforge-gui/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core functionality
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI app
│   └── requirements.txt
├── frontend/               # Vue 3 frontend
│   ├── src/
│   │   ├── components/     # Vue components
│   │   ├── views/          # Page views
│   │   ├── stores/         # Pinia stores
│   │   └── services/       # API services
│   └── package.json
└── start-dev.sh           # Development startup script
```

## Integration with CharForge

The GUI integrates seamlessly with the main CharForge pipeline:

- **Training**: Calls `train_character.py` with configured parameters
- **Inference**: Uses `test_character.py` for image generation
- **File Management**: Works with CharForge directory structure
- **Environment**: Manages all required API keys and settings

## Development

### Adding New Features

1. **Backend**: Add new API endpoints in `backend/app/api/`
2. **Frontend**: Create new views in `frontend/src/views/`
3. **Components**: Add reusable components in `frontend/src/components/`
4. **State**: Manage state with Pinia stores in `frontend/src/stores/`

### Code Style

- **Backend**: Follow FastAPI and Python best practices
- **Frontend**: Use Vue 3 Composition API with TypeScript
- **Styling**: TailwindCSS with ShadCN/Vue components
- **Linting**: ESLint and Prettier for code formatting

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in configuration files
2. **API key errors**: Verify keys in Settings page
3. **Database issues**: Delete `database.db` to reset
4. **Node modules**: Delete `node_modules` and reinstall

### Getting Help

1. Check the console for error messages
2. Verify API key configuration
3. Ensure CharForge dependencies are installed
4. Check file permissions for uploads

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the CharForge ecosystem. See the main CharForge repository for license information.
