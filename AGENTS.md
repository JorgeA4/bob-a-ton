# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Stack

- Python + Streamlit frontend (`fase1/app.py`)
- Gemini API via `google-generativeai` — model: `gemini-1.5-flash`
- `python-dotenv` for secrets; `.env` must contain `GEMINI_API_KEY`
- No test framework yet (hackathon project)

## Run

```bash
cd fase1
streamlit run app.py
```

## Project layout (`fase1/`)

```
app.py                 # Streamlit entry point (Dev A)
ui/components.py       # Visual components — consume List[Ubicacion]
ai/gemini_client.py    # get_locations(giro, capital, ciudad) -> str (raw JSON)
ai/prompt_builder.py   # build_prompt(giro, capital, ciudad) -> str
core/models.py         # Criterio and Ubicacion dataclasses
core/parser.py         # parse_response(json_str: str) -> List[Ubicacion]
```

## Hard contracts — do not break

- `ai.gemini_client.get_locations()` returns a **raw JSON string** — it does NOT parse.
- `core.parser.parse_response()` is the only parser; it converts the raw string to `List[Ubicacion]`.
- Field names on `Ubicacion` must exactly match the JSON schema in `fase1/AI_INSTRUCTIONS.md`.
- `puntaje_total` must be the **arithmetic sum** of the 9 individual `criterios` scores.

## AI prompt rules (see `fase1/AI_INSTRUCTIONS.md`)

- Gemini must respond with **bare JSON only** — no markdown fences, no surrounding text.
- Always 4 real named neighborhoods (`nombre` = actual barrio/colonia, never generic labels).
- Scores (1–10) must differ across locations for the same criterion.
- Capital threshold logic: penalise `costo_renta` / `compatibilidad_capital` if capital < 80 000 MXN.

## Code style

- Use `@dataclass` for models (`Criterio`, `Ubicacion`) in `core/models.py`.
- Raise descriptive exceptions in `parser.py` when required JSON keys are missing.
- Handle Gemini network/quota errors in `gemini_client.py` with explicit exception messages.
- Use `st.spinner` for loading state in `app.py`.

## Dependency management

```bash
cd fase1
pip install -r requirements.txt
# or regenerate after adding packages:
pip freeze > requirements.txt
```

> Note: `requirements.txt` is in `fase1/`, not the project root.
