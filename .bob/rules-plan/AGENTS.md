# AGENTS.md — Plan mode

This file provides guidance to agents when working with code in this repository.

## Architectural constraints

- **Strict layer separation:** `ai/` never parses JSON; `core/` never calls Gemini. This is a hard boundary — both phases follow it.
- **Parsers return plain dicts, not dataclasses.** `parse_response() -> List[dict]`, `parse_scenario() -> dict`. The `Ubicacion`/`RespuestaIA` dataclasses in `core/models.py` exist but parsers do not use them as return types.
- **Gemini model is fixed at `gemini-3.6-flash`** — do not plan around other model names.
- **Phase 1 files are frozen.** Any Phase 2 feature must use new files (`scenario_*.py`) and must not modify the Phase 1 layer.
- **No persistence.** All data is ephemeral per Streamlit session; `st.session_state` is the only state mechanism.
- **`scenario_client.py` shares Gemini configuration** with `gemini_client.py` — plan for reuse of `genai.configure`, not duplication.
- **Phase 2 financial metrics are computed entirely in the frontend** (no extra AI call) — see formulas in `fases_plans/PLANNING_fase2.md`.
- Planning docs live in `fases_plans/` — `fase1/` and `fase2/` directories no longer exist.
