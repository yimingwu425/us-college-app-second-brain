# Changelog

## v5.0.0

### Student-only product

- Narrow the product to students using their own local application workspace.
- Remove parent, consultant, intermediary, and multi-user proxy behavior from the runtime.
- Replace the zero-install prompt-only promise with a Prompt + local CLI architecture.

### Reliable memory and time

- Add a v5 vault schema with canonical student facts, sourced profile insights, material records, task records, checkpoints, session handoffs, school research, and versioned artifacts.
- Add `brain context`, `remember`, `task`, `checkpoint`, `validate`, and `doctor` commands.
- Read current system time at session start and again for time/completion events.
- Compute overdue and urgency dynamically; require completion evidence before marking a task complete.

### Advisor knowledge base

- Add combined TXT/Markdown transcript import with per-video source files.
- Add local keyword search and optional OpenAI-compatible embeddings.
- Return stable source/chunk citations and keep advisor opinion separate from student and official school facts.

### Migration and quality

- Add non-destructive `brain migrate-v4` with dry-run and migration report.
- Make `brain init`, template validation, runtime, demo, and tests follow one manifest.
- Add automatic tests for data contracts and deterministic model eval cases.

## v4.2-lite

- Slim runtime to five prompt modules.
- Keep Markdown templates, fictional demo, and manual evaluation cases.
- Superseded by v5 because memory extraction, time, retrieval, and task state require local tooling rather than prompt-only principles.
