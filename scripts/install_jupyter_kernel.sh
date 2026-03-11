#!/usr/bin/env bash
set -euo pipefail

KERNEL_NAME="${KERNEL_NAME:-gis-phl}"
KERNEL_DISPLAY="${KERNEL_DISPLAY:-Python (gis-phl)}"

uv run python -m ipykernel install --user --name "$KERNEL_NAME" --display-name "$KERNEL_DISPLAY"

echo "Installed Jupyter kernel: $KERNEL_NAME ($KERNEL_DISPLAY)"
