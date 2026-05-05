#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOTFS_DIR="$SCRIPT_DIR/rootfs"
PYTHON_VERSION="3.12"
PYTHON_DIR="$ROOTFS_DIR/usr"

echo "=== Building PolySpace Linux RootFS for Android ==="

rm -rf "$ROOTFS_DIR"
mkdir -p "$ROOTFS_DIR"/{usr,dev,proc,sys,tmp,home/polyspace,data,etc}

if command -v apt-get &>/dev/null; then
    sudo apt-get update
    sudo apt-get install -y debootstrap qemu-user-static
fi

if command -v debootstrap &>/dev/null; then
    echo "Using debootstrap to create minimal Debian rootfs..."
    sudo debootstrap --arch=arm64 --variant=minbase bookworm "$ROOTFS_DIR" http://deb.debian.org/debian
else
    echo "debootstrap not found, creating minimal rootfs manually..."
    mkdir -p "$PYTHON_DIR"/{bin,lib/python3.12,local/lib/python3.12/dist-packages}
    mkdir -p "$ROOTFS_DIR"/{etc,home/polyspace/backend,home/polyspace/data,tmp}
fi

echo "Installing Python and dependencies into rootfs..."
if [ -d "$ROOTFS_DIR/usr/bin" ]; then
    if command -v pip &>/dev/null; then
        echo "Copying Python installation..."
        PYTHON_PREFIX=$(python3 -c "import sys; print(sys.prefix)")
        cp -r "$PYTHON_PREFIX/bin/python3"* "$PYTHON_DIR/bin/" 2>/dev/null || true
        cp -r "$PYTHON_PREFIX/lib/python3.12" "$PYTHON_DIR/lib/" 2>/dev/null || true
    fi
fi

echo "Copying backend code..."
BACKEND_SRC="$SCRIPT_DIR/../../backend"
if [ -d "$BACKEND_SRC" ]; then
    cp -r "$BACKEND_SRC/app" "$ROOTFS_DIR/home/polyspace/backend/"
    cp -r "$BACKEND_SRC/requirements.txt" "$ROOTFS_DIR/home/polyspace/backend/" 2>/dev/null || true
fi

echo "Creating startup script..."
cat > "$ROOTFS_DIR/home/polyspace/start.sh" << 'STARTUP'
#!/bin/sh
export POLYSPACE_DATA_DIR=/home/polyspace/data
export POLYSPACE_HOST=0.0.0.0
export POLYSPACE_PORT=8000
cd /home/polyspace/backend
exec /usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
STARTUP
chmod +x "$ROOTFS_DIR/home/polyspace/start.sh"

echo "Creating tarball..."
cd "$SCRIPT_DIR"
tar czf "$SCRIPT_DIR/polyspace-rootfs.tar.gz" -C "$ROOTFS_DIR" .

echo "=== RootFS build complete ==="
echo "Output: $SCRIPT_DIR/polyspace-rootfs.tar.gz"
echo "Size: $(du -sh "$SCRIPT_DIR/polyspace-rootfs.tar.gz" | cut -f1)"
echo ""
echo "To use in Android:"
echo "1. Place polyspace-rootfs.tar.gz in android/app/src/main/assets/"
echo "2. LinuxManager will extract it on first launch"
