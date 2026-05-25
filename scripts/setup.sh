#!/bin/bash
# Quick setup script for RAG Research Assistant

set -e

echo "🚀 RAG Research Assistant - Quick Setup"
echo "========================================"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env and set your GOOGLE_API_KEY and passwords!"
    echo "   Run: nano .env (or use your preferred editor)"
    echo ""
    read -p "Press Enter after you've configured .env..."
fi

# Validate critical env vars
if grep -q "your-google-ai-studio-api-key" .env; then
    echo "❌ Please set GOOGLE_API_KEY in .env file"
    exit 1
fi

echo "✅ Environment configured"
echo ""

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo "🏥 Checking service health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend health check failed"
        echo "   Check logs: docker-compose logs backend"
        exit 1
    fi
    sleep 2
done

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Access points:"
echo "   Frontend:    http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs:    http://localhost:8000/docs"
echo "   Prometheus:  http://localhost:9090"
echo "   Grafana:     http://localhost:3001 (admin/admin)"
echo ""
echo "📚 Next steps:"
echo "   1. Open http://localhost:3000"
echo "   2. Register a new account"
echo "   3. Upload a research paper (PDF)"
echo "   4. Start asking questions!"
echo ""
echo "📖 For detailed documentation, see:"
echo "   - README.md (architecture & features)"
echo "   - SETUP.md (detailed setup guide)"
echo ""
echo "🛠️  Useful commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Stop all:     docker-compose down"
echo "   Restart:      docker-compose restart"
echo ""
