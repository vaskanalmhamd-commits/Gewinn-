#!/bin/bash

# ==============================================================================
# 🎯 Gewinn Reality Engine - MASTER INSTALLER
# ==============================================================================
# This script automates the installation and setup of the Gewinn platform.
# It is designed for Termux/Linux environments.

set -e

echo "=================================================================="
echo "🚀 Gewinn Reality Engine: Autonomous Platform Setup"
echo "=================================================================="

# 1. Environment & Dependencies Check
echo "📦 Checking system requirements..."
pkg update -y && pkg upgrade -y
pkg install -y python git termux-services openssl nodejs-lts

# 2. Python Environment Setup
echo "📦 Installing Python core dependencies..."
pip install --upgrade pip
pip install uvicorn fastapi cryptography httpx psutil simplepyq apscheduler python-dotenv

# 3. Playwright Setup (For browsing tasks)
echo "🌐 Setting up Playwright..."
pip install playwright
# playwright install chromium # This might fail in some Termux distros; will be handled in runtime

# 4. Directory Structure
echo "📁 Setting up directory structure..."
mkdir -p nexus-core/static
mkdir -p nexus-core/config
touch nexus-core/config/keys.env

# 5. Database Initialization (Empty)
echo "🗄️ Initializing SQLite infrastructure..."
# We will rely on the app.py to initialize the schema on first import

# 6. Service Registration (termux-services)
echo "⚙️ Registering background services..."
SERVICE_DIR="$PREFIX/var/service/nexus_server"
mkdir -p "$SERVICE_DIR"
cat << 'EOF' > "$SERVICE_DIR/run"
#!/bin/bash
PROJECT_DIR="$HOME/Gewinn/nexus-core"
cd "$PROJECT_DIR"
exec uvicorn app:app --host 0.0.0.0 --port 8000 2>&1
EOF
chmod +x "$SERVICE_DIR/run"

echo "✅ Background service 'nexus_server' registered."

# 7. Final Instructions
echo ""
echo "=================================================================="
echo "🎉 INSTALLATION COMPLETE!"
echo "=================================================================="
echo "📍 Dashboard: http://localhost:8000"
echo ""
echo "🔐 IMPORTANT: Run 'sv start nexus_server' to start the system."
echo "🔐 IMPORTANT: You will need to enter your Master Password in the"
echo "              Web UI to unlock the encrypted environment."
echo ""
echo "🚀 Happy Earnings!"
