#!/bin/bash

# CharForge GUI Deployment Script

set -e

echo "🚀 CharForge GUI Deployment Script"
echo "=================================="

# Configuration
ENVIRONMENT=${1:-development}
DOMAIN=${2:-localhost}
SSL_EMAIL=${3:-}

echo "📋 Deployment Configuration:"
echo "   Environment: $ENVIRONMENT"
echo "   Domain: $DOMAIN"
echo "   SSL Email: $SSL_EMAIL"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command_exists docker; then
    echo "❌ Docker is required but not installed"
    echo "   Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is required but not installed"
    echo "   Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Dependencies check passed"

# Create environment file
echo "🔧 Setting up environment..."

if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Security
SECRET_KEY=$(openssl rand -hex 32)

# CharForge API Keys
HF_TOKEN=
HF_HOME=
CIVITAI_API_KEY=
GOOGLE_API_KEY=
FAL_KEY=

# Deployment
DOMAIN=$DOMAIN
SSL_EMAIL=$SSL_EMAIL
CHARFORGE_ROOT=$(pwd)/..

# Database
DATABASE_URL=sqlite:///./database.db
EOF
    echo "⚠️  Please edit .env file with your API keys before continuing"
    echo "   You can do this now or later through the web interface"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/uploads backend/media backend/results
mkdir -p ssl

# Development deployment
if [ "$ENVIRONMENT" = "development" ]; then
    echo "🔧 Starting development environment..."
    
    # Stop any existing containers
    docker-compose down 2>/dev/null || true
    
    # Build and start services
    docker-compose up --build -d backend frontend
    
    echo ""
    echo "🎉 Development environment is running!"
    echo ""
    echo "📱 Frontend: http://$DOMAIN:5173"
    echo "🔧 Backend API: http://$DOMAIN:8000"
    echo "📚 API Docs: http://$DOMAIN:8000/docs"
    echo ""
    echo "🔧 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"

# Production deployment
elif [ "$ENVIRONMENT" = "production" ]; then
    echo "🏭 Starting production environment..."
    
    # Check for SSL email
    if [ -z "$SSL_EMAIL" ]; then
        echo "⚠️  SSL email is required for production deployment"
        echo "   Usage: ./deploy.sh production yourdomain.com your@email.com"
        exit 1
    fi
    
    # Create nginx configuration for production
    cat > nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:5173;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name $DOMAIN;
        return 301 https://\$server_name\$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name $DOMAIN;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header Strict-Transport-Security "max-age=63072000" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # API
        location /api/ {
            proxy_pass http://backend/api/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Media
        location /media/ {
            proxy_pass http://backend/media/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Results
        location /results/ {
            proxy_pass http://backend/results/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF

    # Generate SSL certificates (you might want to use Let's Encrypt in production)
    if [ ! -f "ssl/cert.pem" ]; then
        echo "🔒 Generating SSL certificates..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/key.pem \
            -out ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
        echo "⚠️  Using self-signed certificates. For production, use Let's Encrypt or proper SSL certificates."
    fi
    
    # Stop any existing containers
    docker-compose --profile production down 2>/dev/null || true
    
    # Build and start services
    docker-compose --profile production up --build -d
    
    echo ""
    echo "🎉 Production environment is running!"
    echo ""
    echo "🌐 Website: https://$DOMAIN"
    echo "🔧 API: https://$DOMAIN/api"
    echo "📚 API Docs: https://$DOMAIN/api/docs"
    echo ""
    echo "🔧 To view logs: docker-compose --profile production logs -f"
    echo "🛑 To stop: docker-compose --profile production down"

else
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "   Valid options: development, production"
    exit 1
fi

echo ""
echo "📝 Next Steps:"
echo "1. Configure your API keys in the Settings page"
echo "2. Upload reference images in the Media section"
echo "3. Create your first character"
echo "4. Start training!"
echo ""
echo "📖 For more information, see README.md"
