#!/bin/bash
# ==========================================
# Gmail Creator - Termux Setup Script
# Run this on your Android device with Termux
# ==========================================

set -e

echo "╔═══════════════════════════════════════╗"
echo "║  📧 Gmail Creator - Termux Setup 📧  ║"
echo "╚═══════════════════════════════════════╝"

# Step 1: Update Termux
echo ""
echo "📦 [1/6] Updating Termux packages..."
pkg update -y && pkg upgrade -y

# Step 2: Install Python 3.11 (playwright does NOT support Python 3.13)
echo ""
echo "📦 [2/6] Installing Python 3.11 (required for playwright)..."
pkg install -y python3.11 python3.11-pip git wget curl

# Create symlinks so 'python3' points to 3.11
PYTHON_VER=$(python3.11 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Installed Python $PYTHON_VER"

# Step 3: Install build deps for playwright
echo ""
echo "📦 [3/6] Installing build dependencies..."
pkg install -y libffi openssl clang binutils make cmake

# Step 4: Install Chromium
echo ""
echo "🌐 [4/6] Installing Chromium browser..."
pkg install -y x11-repo 2>/dev/null || true
pkg install -y chromium 2>/dev/null || {
    echo "⚠️  chromium not available, using playwright's bundled chromium"
}

# Step 5: Install Python packages with Python 3.11
echo ""
echo "📦 [5/6] Installing Python packages..."
python3.11 -m pip install --upgrade pip setuptools wheel cffi

# Install playwright from PyPI (Python 3.11 has proper support)
echo "🔧 Installing playwright (with Python 3.11)..."
python3.11 -m pip install playwright 2>/dev/null || {
    echo "⚠️  PyPI failed, building from source..."
    python3.11 -m pip install git+https://github.com/microsoft/playwright-python.git 2>/dev/null || {
        echo "❌ Playwright install failed."
    }
}

python3.11 -m pip install faker rich requests

# Install playwright browsers
echo "🌐 Installing playwright chromium..."
python3.11 -m playwright install chromium 2>/dev/null || {
    echo "⚠️  Using system chromium"
    CHROMIUM_PATH=$(which chromium 2>/dev/null || echo "")
    if [ -n "$CHROMIUM_PATH" ]; then
        echo "export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=$CHROMIUM_PATH" >> ~/.bashrc
    fi
}

# Step 6: Create wrapper script
echo ""
echo "📁 [6/6] Creating launcher script..."
cat > ~/gmail-creator << 'LAUNCHER'
#!/bin/bash
cd "$(dirname "$0")"
python3.11 main.py "$@"
LAUNCHER
chmod +x ~/gmail-creator
echo "export PATH=\$HOME:\$PATH" >> ~/.bashrc

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║       ✅ Setup Complete!              ║"
echo "╠═══════════════════════════════════════╣"
echo "║                                       ║"
echo "║  Run:                                 ║"
echo "║    python3.11 main.py                 ║"
echo "║    # or                               ║"
echo "║    ~/gmail-creator                    ║"
echo "║                                       ║"
echo "║  Quick test:                          ║"
echo "║    python3.11 main.py --test          ║"
echo "║                                       ║"
echo "╚═══════════════════════════════════════╝"
