#!/bin/bash
set -euo pipefail
chmod +x install.sh
./install.sh
echo "[INFO] Starting Docker Compose services..."
docker-compose up --build --remove-orphans
