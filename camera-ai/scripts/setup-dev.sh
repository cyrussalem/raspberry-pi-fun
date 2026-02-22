#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Camera AI: Development Setup ==="

cd "$PROJECT_DIR"
python -m venv .venv

# Activate venv (Windows Git Bash vs Linux)
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

pip install --upgrade pip
pip install -e ".[dev]"

echo "Installing frontend dependencies..."
cd "$PROJECT_DIR/frontend"
npm install

echo ""
echo "Setup complete."
echo ""
echo "To run backend:  source .venv/Scripts/activate && python -m uvicorn backend.main:app --reload"
echo "To run frontend: cd frontend && npx ng serve"
