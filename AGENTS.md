# Repository Maintainer Guide

This repository publishes user-facing runtime prompts at `dist/CLAUDE.md` and `dist/AGENTS.md`.

## For users

Copy `dist/CLAUDE.md` or `dist/AGENTS.md` and `templates/vault/` into your AI workspace. Follow `docs/setup.md`.

## For maintainers

Edit the Markdown modules under `src/runtime/`, keep `src/manifest.md` in the intended order, then run:

```bash
./scripts/build-dist.sh
```

Do not edit generated files in `dist/` directly unless you are repairing a release artifact and immediately backporting the same change into `src/runtime/`.
