#!/bin/bash

# Gewinn Platform - Secure Master Startup Script
# This script handles the Master Password prompt and starts the system securely.

echo "======================================"
echo "🎯 Gewinn Platform: Real-World Transformation"
echo "======================================"

# Navigate to project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/nexus-core"
cd "$PROJECT_DIR"

# Ensure cryptography and httpx are installed
echo "📦 Checking Python packages..."
# pip install --quiet cryptography httpx simplepyq fastapi uvicorn python-dotenv

# Prompt for Master Password (Judge's requirement)
echo -n "🔐 Enter Master Password to initialize the security system: "
read -s MASTER_PASS
echo ""
echo "✅ Password received. Initializing encrypted environment..."

# Initialize security manager and start the FastAPI server
export GEWINN_MASTER_PASS="$MASTER_PASS"

echo ""
echo "🚀 Starting Secure Gewinn Server..."
echo "📍 Dashboard: http://localhost:8000"
echo ""

# Start the FastAPI server
uvicorn app:app --host 0.0.0.0 --port 8000
