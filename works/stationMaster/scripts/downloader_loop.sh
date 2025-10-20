#!/usr/bin/env bash
set -euo pipefail

# downloader_loop.sh
# Runs the incremental downloader in a resilient loop. Intended to be run as a systemd service.

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJ_DIR="$BASE_DIR/projection"
DOWNLOAD_SCRIPT="$PROJ_DIR/download_faces.py"

echo "Downloader loop starting (base=$BASE_DIR)"
mkdir -p "$BASE_DIR/faces"

while true; do
  python3 "$DOWNLOAD_SCRIPT" || true
  sleep 10
done
