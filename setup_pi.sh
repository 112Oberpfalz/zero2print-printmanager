#!/bin/bash

set -e

echo ""
echo "=============================================="
echo " Zero2Print PrintManager - Raspberry Pi Setup"
echo "=============================================="
echo ""

PROJECT_DIR="$(pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo "Projektordner:"
echo "$PROJECT_DIR"
echo ""

echo "Systempakete aktualisieren..."
sudo apt update
sudo apt upgrade -y

echo ""
echo "Installiere benötigte Pakete..."
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    curl \
    nano

echo ""
echo "Erstelle Python Virtual Environment..."
python3 -m venv "$VENV_DIR"

echo ""
echo "Aktiviere Virtual Environment..."
source "$VENV_DIR/bin/activate"

echo ""
echo "Aktualisiere pip..."
python -m pip install --upgrade pip

echo ""
echo "Installiere Python-Abhängigkeiten..."
pip install -r requirements.txt

echo ""
echo "Erstelle Datenordner..."
mkdir -p data
mkdir -p data/uploads
mkdir -p data/pdf
mkdir -p data/qr
mkdir -p data/backups

echo ""
echo "Setze Rechte..."
chmod +x setup_pi.sh

echo ""
echo "=============================================="
echo " Setup abgeschlossen"
echo "=============================================="
echo ""
echo "Teststart:"
echo ""
echo "source .venv/bin/activate"
echo "uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "Danach im Browser öffnen:"
echo "http://RASPBERRY-PI-IP:8000"
echo ""
echo "Für Autostart:"
echo "sudo cp zero2print.service.example /etc/systemd/system/zero2print.service"
echo "sudo nano /etc/systemd/system/zero2print.service"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl enable zero2print"
echo "sudo systemctl start zero2print"
echo "sudo systemctl status zero2print"
echo ""