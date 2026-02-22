#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Camera AI: Raspberry Pi Setup ==="

# System dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-picamera2 python3-opencv python3-numpy

# Python virtual environment
# --system-site-packages is critical: picamera2 and its native dependencies
# are installed via apt and must be accessible from the venv.
echo "Creating Python virtual environment..."
cd "$PROJECT_DIR"
python3.11 -m venv .venv --system-site-packages
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements-pi.txt

echo ""
echo "Setup complete. To run:"
echo "  cd $PROJECT_DIR"
echo "  source .venv/bin/activate"
echo "  ./scripts/build.sh   # (if frontend not yet built)"
echo "  python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
