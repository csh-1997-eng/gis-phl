#!/usr/bin/env bash
set -euo pipefail

KERNEL_NAME="${KERNEL_NAME:-gis-phl}"

jupyter kernelspec uninstall -y "$KERNEL_NAME"

echo "Removed Jupyter kernel: $KERNEL_NAME"
