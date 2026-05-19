#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT_DIR/src/manifest.md"
OUT="$ROOT_DIR/dist/CLAUDE.md"

if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing manifest: $MANIFEST" >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/dist"

{
  echo "# 美本申请第二大脑 | CLAUDE.md v3.0"
  echo
  echo "> Generated from src/manifest.md. Edit src/ modules, then run scripts/build-dist.sh."
  echo
  while IFS= read -r line; do
    [[ "$line" =~ ^-\  ]] || continue
    path="${line#- }"
    file="$ROOT_DIR/$path"
    if [[ ! -f "$file" ]]; then
      echo "Manifest entry not found: $path" >&2
      exit 1
    fi
    echo
    echo "<!-- BEGIN $path -->"
    cat "$file"
    echo
    echo "<!-- END $path -->"
  done < "$MANIFEST"
} > "$OUT"

echo "Wrote $OUT"
