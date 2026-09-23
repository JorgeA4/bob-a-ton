# AGENTS.md — Agent (coding) mode

This file provides guidance to agents when working with code in this repository.

## Critical coding rules

- `get_locations()` in `ai/gemini_client.py` must return the **raw JSON string** — never parse it there.
- Field names in `Ubicacion` and `Criterio` dataclasses must match the JSON schema in `fase1/AI_INSTRUCTIONS.md` exactly (snake_case keys like `costo_renta`, `flujo_peatonal`, etc.).
- `parse_response()` must raise a descriptive exception (not silently return `None`) when expected keys are absent.
- The Streamlit app imports via `ai.gemini_client` and `core.parser` — all code runs from the repo root.
- Use `python-dotenv` (`load_dotenv()`) only in `gemini_client.py`; do not read `.env` elsewhere.
- No tests exist yet; validate manually with `streamlit run app.py` from the repo root.
- `fase1/` contains planning docs only — never create code files inside it.
