#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Building Angular frontend..."
cd "$PROJECT_DIR/frontend"
npm ci
npx ng build --configuration=production

echo "Copying build output to backend static directory..."
rm -rf "$PROJECT_DIR/backend/static"
cp -r "$PROJECT_DIR/frontend/dist/frontend/browser" "$PROJECT_DIR/backend/static"

echo "Build complete. Run the server with:"
echo "  cd $PROJECT_DIR && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
