#!/bin/bash

# Gewinn Platform - Complete Startup Script
# This script sets up and runs the entire Gewinn ecosystem

set -e

echo "======================================"
echo "🎯 Gewinn Platform Startup"
echo "======================================"

# Navigate to project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR/nexus-core"

cd "$PROJECT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📦 Installing Python packages..."
pip install --quiet -r requirements.txt

# Create config directory if it doesn't exist
if [ ! -d "config" ]; then
    echo "📁 Creating config directory..."
    mkdir -p config
fi

# Create keys.env if it doesn't exist
if [ ! -f "config/keys.env" ]; then
    echo "🔐 Creating empty keys.env (add your API keys here)"
    touch config/keys.env
fi

# Initialize database
echo "🗄️ Initializing SQLite database..."
python3 -c "import wallet; wallet.init_db()"

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "🚀 Starting Gewinn Server..."
echo "📍 Dashboard: http://localhost:8000"
echo "📍 Withdrawal: http://localhost:8000/withdraw"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the FastAPI server with uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
