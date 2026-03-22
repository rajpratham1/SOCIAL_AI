#!/bin/bash
echo "============================================"
echo "  SocialAI Backend — Unix/Mac Startup"
echo "============================================"

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install from https://python.org"
    exit 1
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install deps
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Set API key if provided as argument
if [ -n "$1" ]; then
    export ANTHROPIC_API_KEY="$1"
    echo "Anthropic API key set."
fi

# Run
echo ""
echo "Starting server..."
python app.py
