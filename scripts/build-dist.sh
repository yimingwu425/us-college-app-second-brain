#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT_DIR/src/manifest.md"

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

if [[ ${#paths[@]} -eq 0 ]]; then
  echo "Manifest has no module entries: $MANIFEST" >&2
  exit 1
fi

for path in "${paths[@]}"; do
  file="$ROOT_DIR/$path"
  if [[ ! -f "$file" ]]; then
    echo "Manifest entry not found: $path" >&2
    exit 1
  fi
done

# Guardrail: bootstrap and vault template both must exist as dual seeds.
if [[ ! -d "$ROOT_DIR/templates/vault" ]]; then
  echo "Missing templates/vault (single template source)" >&2
  exit 1
fi

build_out() {
  local name="$1"
  local out="$ROOT_DIR/dist/$name"
  local tmp_out="$out.tmp.$$"

  {
    echo "# 美本申请第二大脑 | $name v4.2-lite"
    echo
    echo "> Generated from src/manifest.md. Edit src/runtime/ modules, then run scripts/build-dist.sh."
    echo
    for path in "${paths[@]}"; do
      file="$ROOT_DIR/$path"
      echo
      echo "<!-- BEGIN $path -->"
      cat "$file"
      echo
      echo "<!-- END $path -->"
    done
  } > "$tmp_out"

  mv "$tmp_out" "$out"
  echo "Wrote $out ($(wc -l < "$out" | tr -d ' ') lines)"
}

build_out "CLAUDE.md"
build_out "AGENTS.md"
