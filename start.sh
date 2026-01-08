#!/bin/bash

echo "========================================"
echo "  LogiTech Route Planning System"
echo "  Starting Application..."
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo "[INFO] Docker is running..."
echo ""

# Clean previous builds (optional - uncomment if needed)
# echo "[INFO] Cleaning previous containers..."
# docker-compose down -v

echo "[INFO] Building and starting containers..."
echo "This may take 5-10 minutes on first run..."
echo ""

docker-compose up --build

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to start services!"
    echo "Check the error messages above."
    exit 1
fi
