# Repository Maintainer Guide

This repository publishes user-facing runtime prompts at `dist/CLAUDE.md` and `dist/AGENTS.md`.

> This root file is for maintainers. Students should copy files from `dist/`, not this file.

## For users

Copy `dist/CLAUDE.md` as `CLAUDE.md`, or `dist/AGENTS.md` as `AGENTS.md`, into an empty workspace and say `启动`. See `docs/setup.md`.

Example vault: `examples/demo-vault/`.

## For maintainers

v4.2-lite rule: **keep the runtime thin**. Prefer deleting redundant instructions over adding procedures.

1. Edit `src/runtime/` (five modules).
2. Keep `templates/vault/` as the only vault template source.
3. Keep `src/manifest.md` ordered.
4. Run `./scripts/build-dist.sh`.
5. Spot-check `evals/cases.md` — pass means principle-correct behavior, not matching old checklists.

Do not edit `dist/` directly unless repairing a release and backporting into `src/runtime/` immediately.
