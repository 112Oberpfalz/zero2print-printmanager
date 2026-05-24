#!/bin/bash

# Zero2Print PrintManager - Update Script for Raspberry Pi

set -e

PROJECT_DIR="$(pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo ""
echo "=========================================="
echo " Zero2Print PrintManager - Pi Update"
echo "=========================================="
echo ""

echo "1. Pulling latest code..."
git pull

echo ""
echo "2. Updating pip..."
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip

echo ""
echo "3. Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "4. Running database migrations..."
python -c "from app.migrations import run_migrations; run_migrations()"

echo ""
echo "5. Restarting service..."
sudo systemctl restart zero2print

echo ""
echo "=========================================="
echo " ✓ Update completed successfully"
echo "=========================================="
echo ""
echo "Check status: sudo systemctl status zero2print"
echo ""
