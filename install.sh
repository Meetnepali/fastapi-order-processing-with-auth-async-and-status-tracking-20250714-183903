#!/bin/bash
set -euo pipefail
if [ ! -f requirements.txt ]; then
  echo "requirements.txt not found!" >&2
  exit 1
fi
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "[INFO] Python dependencies installed."
docker build -t fastapi-orders .
echo "[INFO] Docker image built successfully."
