#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"

echo "==================================================="
echo "Starting Electronic Warfare Simulation Backend..."
echo "==================================================="

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    echo "Installing backend dependencies..."
    ./.venv/bin/pip install -r backend/requirements.txt
fi

echo "Launching FastAPI gateway on http://0.0.0.0:8000..."
./.venv/bin/uvicorn backend.gateway.main:app --host 0.0.0.0 --port 8000 --reload
