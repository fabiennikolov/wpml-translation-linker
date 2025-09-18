#!/bin/bash

# Production startup script for Translation Service
# Usage: ./start_production.sh

echo "🚀 Starting Translation Service for Production"
echo "============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📋 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=clubs1-translation

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8001

# Default Languages
DEFAULT_SOURCE_LANGUAGE=bg
DEFAULT_TARGET_LANGUAGE=en
EOF
    echo "📝 Please edit .env file with your API keys before starting the service"
    exit 1
fi

# Check if PM2 is available
if command -v pm2 &> /dev/null; then
    echo "🔄 Using PM2 for process management..."
    
    # Stop existing process if running
    pm2 delete translation-service 2>/dev/null || true
    
    # Start with PM2
    pm2 start api.py --name translation-service --interpreter ./venv/bin/python
    pm2 save
    
    echo "✅ Translation service started with PM2"
    echo "📊 Check status: pm2 status"
    echo "📋 View logs: pm2 logs translation-service"
    
else
    echo "🔄 Starting service directly (install PM2 for production)..."
    echo "💡 Install PM2: npm install -g pm2"
    
    # Start directly
    python api.py
fi

echo ""
echo "🌐 Service should be available at:"
echo "   http://localhost:8001"
echo "   http://your-server-ip:8001"
echo ""
echo "🔧 Configure WordPress at:"
echo "   WordPress Admin → Settings → Translation Service"
