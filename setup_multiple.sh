#!/data/data/com.termux/files/usr/bin/bash
# setup_multiple.sh - Automated setup for Multiple Network on Termux
pkg update && pkg upgrade -y
pkg install proot-distro -y
proot-distro install ubuntu

# Load environment to get the wallet address
source config/keys.env

if [ -z "$MULTIPLE_WALLET_ADDRESS" ]; then
    echo "ERROR: MULTIPLE_WALLET_ADDRESS not set in config/keys.env"
    exit 1
fi

# Logic for Ubuntu setup and execution
proot-distro login ubuntu <<EOF
wget https://github.com/Multiple-Network/depin-client/releases/download/v1.2.0/multiple_arm64
chmod +x ./multiple_arm64
nohup ./multiple_arm64 -wallet=$MULTIPLE_WALLET_ADDRESS -auto > multiple.log 2>&1 &
EOF

echo "Multiple Network node initiated on Ubuntu via proot-distro."
