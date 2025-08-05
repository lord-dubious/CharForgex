#!/bin/bash

# CharForge GUI Development Startup Script

echo "🚀 Starting CharForge GUI Development Environment"

# Check if we're in the right directory
if [ ! -f "start-dev.sh" ]; then
    echo "❌ Please run this script from the charforge-gui directory"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is required but not installed"
    exit 1
fi

echo "✅ Dependencies check passed"

# Setup backend
echo "🔧 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
SECRET_KEY=your-secret-key-change-this-in-production
DATABASE_URL=sqlite:///./database.db
HF_TOKEN=
HF_HOME=
CIVITAI_API_KEY=
GOOGLE_API_KEY=
FAL_KEY=
EOF
    echo "⚠️  Please edit backend/.env file with your API keys"
fi

cd ..

# Setup frontend
echo "🎨 Setting up frontend..."
cd frontend

# Install Node.js dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

cd ..

echo "✅ Setup complete!"

# Start services
echo "🚀 Starting services..."

# Get the local IP address for remote access
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")

# Start backend in background
echo "Starting FastAPI backend..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "Starting Vue frontend..."
cd frontend
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!
cd ..

echo ""
echo "🎉 CharForge GUI is now running!"
echo ""
echo "📱 Frontend (Local):  http://localhost:5173"
echo "📱 Frontend (Remote): http://${LOCAL_IP}:5173"
echo ""
echo "🔧 Backend API (Local):  http://localhost:8000"
echo "🔧 Backend API (Remote): http://${LOCAL_IP}:8000"
echo "📚 API Docs: http://${LOCAL_IP}:8000/docs"
echo ""
echo "🌐 For remote access, use your server's IP address: ${LOCAL_IP}"
echo "🔒 Make sure ports 5173 and 8000 are open in your firewall"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM

# Wait for processes
wait
