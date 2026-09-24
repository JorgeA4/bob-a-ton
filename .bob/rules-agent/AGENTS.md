# AGENTS.md — Agent (coding) mode

This file provides guidance to agents when working with code in this repository.

## Critical coding rules

- `get_locations()`, `get_scenario()`, and `get_vulnerability_analysis()` must return the **raw JSON string** — never parse inside `ai/`.
- `parse_response()` returns `List[dict]` (plain dicts, not `List[Ubicacion]`); `parse_scenario()` returns `dict`; `parse_vulnerability()` returns `dict` — never dataclasses.
- All parsers must raise `ValueError` with a descriptive message on missing keys; never silently return `None`.
- All AI clients call `ai._client.get_client()` — do NOT import `google.generativeai` or instantiate `groq.Groq` directly in any `ai/` module other than `_client.py`.
- `load_dotenv()` and `GROQ_API_KEY` resolution happen only inside `ai/_client.get_client()` (idempotent singleton). The env var is `GROQ_API_KEY`, not `GEMINI_API_KEY`.
- Active model is `ai._client.MODEL` (`"llama-3.3-70b-versatile"`) — never hardcode a model string in any other file.
- All imports use package paths from repo root (`ai.gemini_client`, `core.parser`, etc.); run everything from root.
- `gemini_client.py` retains its name for import compatibility — the underlying provider is Groq.
- Phase 1 files must not be modified in Phase 2/3 work: `gemini_client.py`, `prompt_builder.py`, `models.py`, `parser.py`.
- Phase 2 files must not be modified in Phase 3 work: `scenario_client.py`, `scenario_parser.py`.
- `core/vulnerability_analyzer.py` is a **pure module** — zero Streamlit imports, safe `.get()` calls, never raises. Do not import `ui/components.py` from `core/`.
- The exponential curve math is duplicated in `vulnerability_analyzer.py` as `_curva_k`, `_flujo_mensual`, `_calcular_pago_mensual` — do not refactor into a shared module.
- Planning docs are in `fases_plans/` (not `fase1/` or `fase2/` — those directories no longer exist).
- No test framework — validate with `streamlit run app.py` from repo root.
