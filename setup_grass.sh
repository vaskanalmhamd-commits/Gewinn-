#!/data/data/com.termux/files/usr/bin/bash
# setup_grass.sh - Automated setup for GRASS on Termux
pkg update -y
pkg install python python-pip git -y
pip install playwright websockets websockets-proxy loguru fake-useragent python-dotenv
playwright install-deps
playwright install chromium
