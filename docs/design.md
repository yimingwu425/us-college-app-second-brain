# Architecture

v3 uses a source-and-distribution model.

- `src/` contains maintainable prompt modules.
- `src/manifest.md` defines publication order.
- `scripts/build-dist.sh` generates `dist/CLAUDE.md`.
- `dist/CLAUDE.md` is the only complete runtime prompt users copy.
- `templates/vault/` is the starter vault.
- `examples/demo-vault/` is reserved for fictional demo vault examples and currently documents the intended shape.

## Module Rules

Core rules belong in `src/core/`.
Task procedures belong in `src/flows/`.
US-college-specific logic belongs in `src/domain/us-college/`.

When a rule seems to fit multiple places, put the imperative operating rule in the flow and put domain explanation or constants in the domain module.
