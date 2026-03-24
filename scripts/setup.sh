#!/bin/bash

echo "🔗 ChainTrace Setup Script"
echo "=========================="
echo ""

# Check if Docker is installed
if command -v docker &> /dev/null; then
    echo "✅ Docker found"
    DOCKER_AVAILABLE=true
else
    echo "⚠️  Docker not found - will use manual setup"
    DOCKER_AVAILABLE=false
fi

# Create environment files
echo ""
echo "📝 Setting up environment files..."

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env"
else
    echo "⚠️  backend/.env already exists, skipping"
fi

if [ ! -f frontend/.env ]; then
    cp frontend/.env.example frontend/.env
    echo "✅ Created frontend/.env"
else
    echo "⚠️  frontend/.env already exists, skipping"
fi

echo ""
echo "🔑 API Key Setup"
echo "================"
echo "You'll need a BlockCypher API token for the backend."
echo "Get one free at: https://blockcypher.com"
echo ""
read -p "Do you have a BlockCypher token? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your BlockCypher token: " TOKEN
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/your_blockcypher_token_here/$TOKEN/" backend/.env
    else
        sed -i "s/your_blockcypher_token_here/$TOKEN/" backend/.env
    fi
    echo "✅ Token added to backend/.env"
else
    echo "⚠️  You can add it later by editing backend/.env"
fi

echo ""
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "🐳 Docker Setup"
    echo "==============="
    read -p "Start with Docker Compose? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting services..."
        docker-compose up -d
        echo ""
        echo "✅ Services started!"
        echo ""
        echo "🌐 Access points:"
        echo "   Frontend: http://localhost:5173"
        echo "   Backend API: http://localhost:8000"
        echo "   API Docs: http://localhost:8000/docs"
        echo ""
        echo "View logs with: docker-compose logs -f"
        echo "Stop services with: docker-compose down"
    fi
else
    echo "📦 Manual Setup"
    echo "==============="
    echo ""
    echo "Backend setup:"
    echo "  cd backend"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "  uvicorn app.main:app --reload"
    echo ""
    echo "Frontend setup (in a new terminal):"
    echo "  cd frontend"
    echo "  npm install"
    echo "  npm run dev"
    echo ""
    echo "See SETUP.md for detailed instructions."
fi

echo ""
echo "✨ Setup complete! Check SETUP.md for more information."
