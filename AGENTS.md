# Repository Maintainer Guide

This repository publishes the student runtime at `dist/AGENTS.md` and `dist/CLAUDE.md`.

Students use the v5 local `brain` CLI plus one runtime file. This root file is for maintainers, not a student vault.

## Maintainer workflow

1. Edit Python code under `src/college_brain/`.
2. Edit student rules under `src/runtime/`.
3. Keep `src/college_brain/data/vault_manifest.yaml` as the machine-readable vault contract.
4. Run `pytest`.
5. Run `./scripts/build-dist.sh`; it validates `templates/vault/` before generating dist.
6. Review `evals/cases.md` for model behavior changes.

Do not edit `dist/` directly. Do not commit private transcripts, embedding keys, generated SQLite indexes, or real student vaults.
