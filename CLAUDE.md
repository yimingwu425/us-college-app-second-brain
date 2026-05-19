# Repository Maintainer Guide

This repository publishes the user-facing runtime prompt at `dist/CLAUDE.md`.

## For users

Copy `dist/CLAUDE.md` and `templates/vault/` into your AI workspace. Follow `docs/setup.md`.

## For maintainers

Edit the Markdown modules under `src/`, keep `src/manifest.md` in the intended order, then run:

```bash
./scripts/build-dist.sh
```

Do not edit `dist/CLAUDE.md` directly unless you are repairing a release artifact and immediately backporting the same change into `src/`.
