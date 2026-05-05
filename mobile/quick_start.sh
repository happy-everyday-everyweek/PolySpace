#!/data/data/com.termux/files/usr/bin/bash
set -e

POLYSPACE_DIR="$HOME/polyspace"

echo "=== PolySpace Mobile Quick Start ==="

if ! command -v python &> /dev/null; then
    echo "Installing Python..."
    pkg install -y python python-pip 2>/dev/null
fi

cd "$POLYSPACE_DIR/backend"

export POLYSPACE_DATA_DIR="$POLYSPACE_DIR/data"
export POLYSPACE_HOST="0.0.0.0"
export POLYSPACE_PORT="8000"
mkdir -p "$POLYSPACE_DIR/data"

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
