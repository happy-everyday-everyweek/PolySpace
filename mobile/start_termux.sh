#!/data/data/com.termux/files/usr/bin/bash
set -e

POLYSPACE_DIR="$HOME/polyspace"
BACKEND_DIR="$POLYSPACE_DIR/backend"

echo "=== PolySpace Mobile Setup ==="

pkg update -y 2>/dev/null || true
pkg install -y python python-pip openssl libffi sqlite 2>/dev/null || true

if [ ! -d "$POLYSPACE_DIR" ]; then
    echo "Copying PolySpace to $POLYSPACE_DIR..."
    mkdir -p "$POLYSPACE_DIR"
    cp -r /sdcard/PolySpace/backend "$POLYSPACE_DIR/"
    cp -r /sdcard/PolySpace/frontend/dist "$POLYSPACE_DIR/frontend_dist" 2>/dev/null || true
fi

cd "$BACKEND_DIR"

if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt --cache-dir "$HOME/.pip_cache" 2>/dev/null || true
fi

export POLYSPACE_DATA_DIR="$POLYSPACE_DIR/data"
export POLYSPACE_HOST="0.0.0.0"
export POLYSPACE_PORT="8000"
mkdir -p "$POLYSPACE_DIR/data"

echo "=== Starting PolySpace Backend ==="
echo "Access at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --data-dir "$POLYSPACE_DIR/data"
