# Architecture

v4.2-lite keeps a small runtime and a thicker repository.

- `src/runtime/` — five short modules the model actually loads.
- `src/manifest.md` — publication order.
- `scripts/build-dist.sh` — builds `dist/CLAUDE.md` and `dist/AGENTS.md`.
- `templates/vault/` — only starter vault template source.
- `examples/demo-vault/` — fictional semi-filled vault for humans.
- `evals/cases.md` — manual regression; judge by principles, not checklist compliance.

## Runtime Philosophy

Strong models already understand intent, emotion, and tradeoffs. The prompt should not re-teach conversation management.

**In runtime (must change behavior every turn):**

1. Who you are and hard limits
2. How to work with a person (judgment, not stages)
3. Where durable state lives
4. How an empty folder becomes a workspace
5. What good admissions judgment looks like

**Out of runtime (repo only):**

- Micro-command tables and mode catalogs
- Detailed product field templates
- Long China-context encyclopedias
- Step-by-step consolidation choreography

Those belong in demo, docs, or eval notes if needed.

## Module Map

| Module | Role |
| --- | --- |
| `00-north-star` | Identity and hard limits |
| `01-work` | Collaboration posture |
| `02-files` | Memory surfaces and write rules |
| `03-bootstrap` | Empty-folder structure |
| `04-judgment` | Time, truth, schools, light artifact guidance |

## Thinness Rule

If a sentence only restates what a capable model would do anyway, delete it.

If a sentence defines where files go, what must never be faked, or what this product is for, keep it.

Template seed text in bootstrap should stay aligned with `templates/vault/`, but bootstrap can describe seeds briefly instead of pasting full file bodies.
