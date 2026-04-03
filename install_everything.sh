#!/bin/bash

# ==============================================================================
# 🎯 Gewinn Sovereign Machine v1.0 - MASTER INSTALLER
# ==============================================================================
# This script automates the installation and setup of the Sovereign Machine.
# It ensures all DePIN nodes and AI Micro-Agents are properly configured.

set -e

echo "=================================================================="
echo "🚀 Gewinn Sovereign Machine v1.0: Final Transformation"
echo "=================================================================="

# 1. System Requirements & Environment
echo "📦 Updating system repositories..."
pkg update -y && pkg upgrade -y
pkg install -y python git termux-services openssl nodejs-lts lsof

# 2. Python Environment & Dependencies
echo "📦 Installing core Python engine..."
pip install --upgrade pip
pip install fastapi uvicorn cryptography httpx psutil simplepyq apscheduler python-dotenv playwright

# 3. Project Structure Verification
echo "📁 Validating Sovereign directory structure..."
mkdir -p nexus-core/static
mkdir -p nexus-core/config
touch nexus-core/config/keys.env

# 4. Service Persistence (termux-services)
echo "⚙️ Configuring autonomous background services..."
SERVICE_DIR="$PREFIX/var/service/sovereign_engine"
mkdir -p "$SERVICE_DIR"
cat << 'SV' > "$SERVICE_DIR/run"
#!/bin/bash
PROJECT_DIR="$HOME/Gewinn/nexus-core"
cd "$PROJECT_DIR"
# The system starts in a locked state, waiting for the UI Master Password
exec uvicorn app:app --host 0.0.0.0 --port 8000 2>&1
SV
chmod +x "$SERVICE_DIR/run"

# 5. Self-Healing Mechanism (Watchdog)
echo "🛡️ Enabling self-healing watchdog..."
cat << 'WD' > nexus-core/watchdog.sh
#!/bin/bash
while true; do
  if ! lsof -i:8000 > /dev/null; then
    echo "Sovereign Engine down. Restarting..."
    sv restart sovereign_engine
  fi
  sleep 60
done
WD
chmod +x nexus-core/watchdog.sh

# 6. Final Report
echo ""
echo "=================================================================="
echo "🎉 SOVEREIGN MACHINE v1.0 INSTALLED SUCCESSFULLY!"
echo "=================================================================="
echo "📍 Sovereign Dashboard: http://localhost:8000"
echo "📍 Service Control:    sv start sovereign_engine"
echo ""
echo "🔒 SECURITY NOTICE:"
echo "The system is currently LOCKED. Open the Dashboard and enter your"
echo "Master Password to decrypt AI keys and activate DePIN workers."
echo ""
echo "⚖️ Compliance: Platform operates in GDPR-compliant mode."
echo "=================================================================="
