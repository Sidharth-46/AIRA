#!/bin/bash
# AIRA Setup Script for Linux/macOS

echo "============================================"
echo "    AIRA - Think. Reason. Build."
echo "    Initial Setup Script"
echo "============================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[!] Docker could not be found. Please install Docker and docker-compose first."
    exit 1
fi

echo "[*] Checking for .env file..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "[*] Creating .env from .env.example..."
        cp .env.example .env
        echo "[*] Please update .env with your specific configuration if necessary."
    else
        echo "[!] .env.example not found. Please create a .env file."
        exit 1
    fi
else
    echo "[*] .env file already exists."
fi

echo "[*] Creating local data directories..."
mkdir -p data/uploads data/embeddings data/workspace logs

echo "[*] Setup complete."
echo ""
echo "To start AIRA, run:"
echo "    docker-compose up -d --build"
echo ""
echo "Once started, AIRA will be available at: http://localhost:3000"
echo "============================================"
