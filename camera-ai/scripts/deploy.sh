#!/bin/bash
set -euo pipefail

# Usage: ./scripts/deploy.sh <pi-host> [user]
# Example: ./scripts/deploy.sh 192.168.68.50
# Example: ./scripts/deploy.sh 192.168.68.50 pi

if [ $# -lt 1 ]; then
    echo "Usage: $0 <pi-host> [user]"
    echo "  pi-host: IP address or hostname of the Raspberry Pi"
    echo "  user:    SSH user (default: pi)"
    exit 1
fi

PI_HOST="$1"
PI_USER="${2:-pi}"
REMOTE_DIR="/home/$PI_USER/camera-ai"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

ARCHIVE="/tmp/camera-ai-deploy.tar.gz"

echo "Packaging camera-ai source code..."
tar -czf "$ARCHIVE" \
    -C "$PROJECT_DIR" \
    --exclude='node_modules' \
    --exclude='frontend/dist' \
    --exclude='frontend/.angular' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.egg-info' \
    --exclude='backend/static' \
    --exclude='.env' \
    --exclude='dist' \
    .

echo "Deploying to $PI_USER@$PI_HOST:$REMOTE_DIR ..."
ssh "$PI_USER@$PI_HOST" "mkdir -p $REMOTE_DIR"
scp "$ARCHIVE" "$PI_USER@$PI_HOST:/tmp/camera-ai-deploy.tar.gz"
ssh "$PI_USER@$PI_HOST" "rm -rf $REMOTE_DIR/* && tar -xzf /tmp/camera-ai-deploy.tar.gz -C $REMOTE_DIR && rm /tmp/camera-ai-deploy.tar.gz"

rm "$ARCHIVE"

echo ""
echo "Deploy complete. SSH into the Pi to set up:"
echo "  ssh $PI_USER@$PI_HOST"
echo "  cd $REMOTE_DIR"
echo "  ./scripts/setup-pi.sh"
