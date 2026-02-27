#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

AUTO_YES="${1:-}"

TARGETS=(
  "ingestion/tmp/source_samples"
  "ingestion/tmp/minimal_samples"
)

echo "This cleanup keeps ontology outputs and removes ingestion probe artifacts:"
for target in "${TARGETS[@]}"; do
  if [[ -e "$target" ]]; then
    size=$(du -sh "$target" 2>/dev/null | awk '{print $1}')
    echo "- $target (size: ${size:-unknown})"
  else
    echo "- $target (not found)"
  fi
done

echo "Will keep: ingestion/tmp/entities"

if [[ "$AUTO_YES" != "--yes" ]]; then
  read -r -p "Proceed with cleanup? [y/N] " confirm
  case "$confirm" in
    y|Y|yes|YES) ;;
    *)
      echo "Cleanup cancelled."
      exit 0
      ;;
  esac
fi

for target in "${TARGETS[@]}"; do
  if [[ -e "$target" ]]; then
    rm -rf "$target"
    echo "Removed: $target"
  fi
done

echo "Done. Remaining tmp folders:"
find ingestion/tmp -maxdepth 1 -type d 2>/dev/null | sort || true
