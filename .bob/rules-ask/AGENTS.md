# AGENTS.md — Ask mode

This file provides guidance to agents when working with code in this repository.

## Documentation context

- The canonical data contract (JSON schema, 9 evaluation criteria, scoring rules) lives in `fase1/AI_INSTRUCTIONS.md` — this is the single source of truth for AI output format.
- `fase1/PLANNING.md` documents the three-dev split (Dev A = UI, Dev B = AI, Dev C = models/parser) and the integration flow.
- No code has been written yet; all source files described in `PLANNING.md` still need to be created.
- `requirements.txt` is in `fase1/`, not the project root, and is encoded as wide-character (every character spaced) — use pip normally regardless.
