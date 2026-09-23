# AGENTS.md — Ask mode

This file provides guidance to agents when working with code in this repository.

## Documentation context

- Planning docs for both phases are in `fases_plans/PLANNING_fase1.md` and `fases_plans/PLANNING_fase2.md` — the old `fase1/` and `fase2/` directories no longer exist.
- The canonical JSON schema for Phase 1 (9 evaluation criteria, scoring rules) lives in `ai/prompt_builder.py` — the former `fase1/AI_INSTRUCTIONS.md` has been deleted.
- The canonical JSON schema for Phase 2 (scenario structure) lives in `fases_plans/PLANNING_fase2.md` under "Dev B" tasks.
- Three-dev split: Dev A = UI/Streamlit (`app.py`, `ui/`), Dev B = AI/Gemini (`ai/`), Dev C = data/models (`core/`).
- Phase 1 is complete. Phase 2 files to be created: `ai/scenario_client.py`, `ai/scenario_prompt.py`, `core/scenario_parser.py`, `ui/scenario_components.py`.
- `parse_response()` returns `List[dict]` (not `List[Ubicacion]` as originally planned); `parse_scenario()` returns `dict`.
- All source code lives in the repo root — never inside `fases_plans/`.
