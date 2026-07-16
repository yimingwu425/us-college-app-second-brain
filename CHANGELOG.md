# Changelog

## v4.2-lite

### Posture: max feasible help, zero moralizing

- Default: if the user proposes it and it is doable, help execute—no lectures on morals, purity, or “should you”.
- Feasibility-only brakes: fabricated facts that will not survive scrutiny, forged credentials, safety crises.
- Explicitly wild: packaging craft, round strategy, paid programs as evidence plays, intermediary tactics reused when useful—judged by effectiveness and risk, not virtue.

### Posture: sharp, not preachy


- Keep the end goal: a specific person + materials that stand up.
- Narrow hard limits to fraud/safety/proxy trust.
- Explicitly welcome legal presentation craft ("小聪明"): framing, emphasis, round strategy, honest quantification.
- Treat hollow packaging mainly as an effectiveness risk (unconvincing / interview-fragile), not a moral lecture.

### Runtime slim-down

- Collapse runtime to five short modules: identity, work, files, bootstrap, judgment.
- Remove dense tables for micro-commands, task-pattern catalogs, consolidation choreography, and heavy artifact templates from the model prompt.
- Keep hard limits: no fabrication, no packaging-as-identity, safety first, student-first when adults proxy.
- Keep structural memory: two-layer profile, paths, bootstrap tree, light product guidance.
- `dist/*` shrinks from ~880 lines (v4.1) to ~200 lines.

### Unchanged in repo (on purpose)

- `templates/vault/` single template source
- `examples/demo-vault/` fictional student
- `evals/cases.md` manual regression suite

## v4.1-modern

### Structure

- Make `templates/vault/` the only template source; remove duplicated top-level `templates/*` copies.
- Split responsibilities: `本体画像/` = facts, `用户画像.md` = AI understanding layer.
- Bootstrap also creates `文书/`, `活动列表/`, `推荐信/`.

### Runtime (superseded by v4.2-lite density)

- Anti-packaging checks, compression protocol, session continuity, micro-commands, China context, artifacts module — substance retained where useful, wording compressed in v4.2.

### Examples and quality

- Fictional demo vault and eval suite added.

## v4.0-modern

- Rebuild around principle-dense runtime modules instead of stage machinery.
- Single-file zero-install bootstrap.
- Dynamic `用户画像.md` as main memory surface.
