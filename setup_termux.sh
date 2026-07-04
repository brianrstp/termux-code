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
echo "📦 [1/7] Updating Termux packages..."
pkg update -y && pkg upgrade -y

# Step 2: Install required packages
echo ""
echo "📦 [2/7] Installing system dependencies..."
pkg install -y python python-pip git wget curl

# Step 3: Install Node.js (needed for Playwright)
echo ""
echo "📦 [3/7] Installing Node.js (required by Playwright)..."
pkg install -y nodejs

# Step 4: Install Python dependencies
echo ""
echo "📦 [4/7] Installing Python packages..."
pip install --upgrade pip setuptools wheel

# Install playwright - ARM/Termux needs special handling
echo "🔧 Installing playwright (may take a while on ARM)..."
pip install playwright 2>/dev/null || {
    echo "⚠️  Standard install failed, trying without binary..."
    pip install --no-binary playwright playwright
}

# Install other dependencies
pip install faker rich requests

# Step 5: Setup Chromium (system + playwright)
echo ""
echo "🌐 [5/7] Setting up Chromium..."
pkg install -y chromium 2>/dev/null || true

python -m playwright install chromium 2>/dev/null || {
    echo "⚠️  Playwright chromium failed on ARM, using system chromium"
    CHROMIUM_PATH=$(which chromium-browser 2>/dev/null || which chromium 2>/dev/null || echo "")
    if [ -n "$CHROMIUM_PATH" ]; then
        echo "✅ System chromium: $CHROMIUM_PATH"
        export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH="$CHROMIUM_PATH"
        echo "export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=$CHROMIUM_PATH" >> ~/.bashrc
    else
        echo "❌ No chromium found. Run: pkg install chromium"
    fi
}
python -m playwright install-deps 2>/dev/null || true

# Step 6: Create data directory
echo ""
echo "📁 [6/7] Creating data directory..."
mkdir -p ~/.gmail_creator
mkdir -p ~/.gmail_creator/profiles

# Step 7: Verify installation
echo ""
echo "✅ [7/7] Verifying installation..."
python -c "from playwright.async_api import async_playwright; print('✅ Playwright OK')"
python -c "from faker import Faker; print('✅ Faker OK')"
python -c "from rich.console import Console; print('✅ Rich OK')"

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║       ✅ Setup Complete!              ║"
echo "╠═══════════════════════════════════════╣"
echo "║                                       ║"
echo "║  Run the creator:                     ║"
echo "║    python main.py                     ║"
echo "║                                       ║"
echo "║  Quick test:                          ║"
echo "║    python main.py --test              ║"
echo "║                                       ║"
echo "║  CLI options:                         ║"
echo "║    python main.py -n 5  (5 accounts) ║"
echo "║    python main.py --list             ║"
echo "║                                       ║"
echo "║  SMS providers (env vars):            ║"
echo "║    export SMS_ACTIVATE_API_KEY=...    ║"
echo "║    export FIVE_SIM_API_KEY=...        ║"
echo "║    export PROXY=socks5://...          ║"
echo "║                                       ║"
echo "╚═══════════════════════════════════════╝"
