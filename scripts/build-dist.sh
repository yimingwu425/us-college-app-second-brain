#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT_DIR/src/manifest.md"
OUT="$ROOT_DIR/dist/CLAUDE.md"
TMP_OUT="$OUT.tmp.$$"

if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing manifest: $MANIFEST" >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/dist"

paths=()
while IFS= read -r line; do
  [[ "$line" =~ ^-\  ]] || continue
  paths+=("${line#- }")
done < "$MANIFEST"

for path in "${paths[@]}"; do
  file="$ROOT_DIR/$path"
  if [[ ! -f "$file" ]]; then
    echo "Manifest entry not found: $path" >&2
    exit 1
  fi
done

trap 'rm -f "$TMP_OUT"' EXIT

{
  echo "# 美本申请第二大脑 | CLAUDE.md v3.0"
  echo
  echo "> Generated from src/manifest.md. Edit src/ modules, then run scripts/build-dist.sh."
  echo
  for path in "${paths[@]}"; do
    file="$ROOT_DIR/$path"
    echo
    echo "<!-- BEGIN $path -->"
    cat "$file"
    echo
    echo "<!-- END $path -->"
  done
} > "$TMP_OUT"

mv "$TMP_OUT" "$OUT"
trap - EXIT

echo "Wrote $OUT"
