#!/bin/bash

set -e  # Exit on any error

echo "Updating packages..."
pkg update && pkg upgrade -y

echo "Installing Python, git, and cmake..."
pkg install python git cmake -y

echo "Creating project directory nexus-core/"
mkdir -p nexus-core

cd nexus-core

echo "Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python packages..."
pip install --upgrade pip
pip install fastapi uvicorn[standard] playwright sqlite3 apscheduler requests python-dotenv

echo "Installing Playwright browsers..."
playwright install chromium

echo "Setup complete!"
python --version

echo "Starting FastAPI server..."
python app.py