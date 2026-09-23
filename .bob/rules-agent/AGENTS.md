# AGENTS.md — Agent (coding) mode

This file provides guidance to agents when working with code in this repository.

## Critical coding rules

- `get_locations()` and `get_scenario()` must return the **raw JSON string** — never parse inside `ai/`.
- `parse_response()` returns `List[dict]` (plain dicts, not `List[Ubicacion]`); `parse_scenario()` returns `dict` — never dataclasses.
- Both parsers must raise `ValueError` with a descriptive message on missing keys; never silently return `None`.
- `load_dotenv()` is called only in `ai/gemini_client.py`; the `.env` path is `parents[1]` (repo root, not `parents[2]`).
- `scenario_client.py` must reuse the `genai.configure` already done in `gemini_client.py` — do not call it again.
- All imports use package paths from repo root (`ai.gemini_client`, `core.parser`, etc.); run everything from root.
- Gemini model is `gemini-3.6-flash` — watch for regressions back to old names like `gemini-1.5-flash`.
- Phase 1 files must not be modified in Phase 2 work: `gemini_client.py`, `prompt_builder.py`, `components.py`, `models.py`, `parser.py`.
- Planning docs are in `fases_plans/` (not `fase1/` or `fase2/` — those directories no longer exist).
- No test framework — validate with `streamlit run app.py` from repo root.
