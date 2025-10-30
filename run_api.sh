#!/bin/bash

# Aether AI Engine API Startup Script

echo "=========================================="
echo "🚀 Starting Aether AI Engine API"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found. Please run: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Check if API dependencies are installed
echo "🔍 Checking dependencies..."
pip show fastapi > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📥 Installing API dependencies..."
    pip install -r requirements-api.txt
fi

# Set environment variables (if needed)
# export SERPER_API_KEY="your-key-here"

# Run the API server
echo "🌐 Starting API server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/health"
echo "=========================================="
echo ""

cd src/aether_2/api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

