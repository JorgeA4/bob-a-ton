# AGENTS.md — Agent (coding) mode

This file provides guidance to agents when working with code in this repository.

## Critical coding rules

- `get_locations()`, `get_scenario()`, and `get_vulnerability_analysis()` must return the **raw JSON string** — never parse inside `ai/`.
- `parse_response()` returns `List[dict]` (plain dicts, not `List[Ubicacion]`); `parse_scenario()` returns `dict`; `parse_vulnerability()` returns `dict` — never dataclasses.
- All parsers must raise `ValueError` with a descriptive message on missing keys; never silently return `None`.
- `load_dotenv()` is called only in `ai/gemini_client.py`; the `.env` path is `parents[1]` (repo root, not `parents[2]`).
- `scenario_client.py` and `vulnerability_client.py` each call their own `_ensure_configured()` (idempotent load_dotenv + genai.configure) — do not assume any other AI module was imported first.
- All imports use package paths from repo root (`ai.gemini_client`, `core.parser`, etc.); run everything from root.
- Gemini model is `gemini-3.6-flash` — watch for regressions back to old names like `gemini-1.5-flash`.
- Phase 1 files must not be modified in Phase 2/3 work: `gemini_client.py`, `prompt_builder.py`, `models.py`, `parser.py`.
- Phase 2 files must not be modified in Phase 3 work: `scenario_client.py`, `scenario_parser.py`.
- `core/vulnerability_analyzer.py` is a **pure module** — zero Streamlit imports, safe `.get()` calls, never raises. Do not import `ui/components.py` from `core/`.
- The exponential curve math is duplicated in `vulnerability_analyzer.py` as `_curva_k`, `_flujo_mensual`, `_calcular_pago_mensual` — do not refactor into a shared module.
- `ai/vulnerability_client.py` does not exist yet (Dev B pending) — `app.py` imports it unconditionally, so the app requires that file to start.
- Planning docs are in `fases_plans/` (not `fase1/` or `fase2/` — those directories no longer exist).
- No test framework — validate with `streamlit run app.py` from repo root.
