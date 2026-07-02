# Architecture

v4.0-modern uses a small runtime prompt source and a generated distribution file.

- `src/runtime/` contains maintainable prompt modules.
- `src/manifest.md` defines publication order.
- `scripts/build-dist.sh` generates `dist/CLAUDE.md` and `dist/AGENTS.md`.
- `dist/CLAUDE.md` and `dist/AGENTS.md` are equivalent runtime prompts with tool-specific filenames.
- `templates/vault/` is a reference starter vault; the runtime prompt can bootstrap an empty folder by itself.
- `examples/demo-vault/` is reserved for fictional demo vault examples and currently documents the intended shape.

## Runtime Philosophy

The modern version assumes strong model-level intent understanding. The prompt defines principles, judgment standards, data boundaries, and output quality bars. It avoids micromanaging every turn.

Key changes:

- `用户画像.md` is the main long-term memory surface.
- The prompt supports zero-install bootstrap from a single `CLAUDE.md` or `AGENTS.md` file.
- Runtime modules live in `src/runtime/`, not a flow-heavy folder tree.
- Conversation stages are replaced by fluid work modes: understand, explore, judge, execute, and consolidate.
- Advice can be provisional when context is incomplete, as long as uncertainty is explicit.

## Module Rules

Runtime files should stay few, dense, and principle-driven.

Add a new runtime module only when it changes the assistant's operating model. Prefer revising existing modules over rebuilding a detailed procedure tree.
