# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Stack

- Python + Streamlit frontend (`app.py` in repo root)
- Gemini API via `google-generativeai` — model: `gemini-3.6-flash`
- `python-dotenv` for secrets; `.env` must contain `GEMINI_API_KEY`
- No test framework (hackathon project) — validate with `streamlit run app.py`

## Run

```bash
streamlit run app.py
```

## Project layout

```
/ (repo root — all code lives here)
├── app.py                          # Streamlit entry point
├── ui/
│   └── components.py               # All visual components — Phase 1 and Phase 2
├── ai/
│   ├── gemini_client.py            # get_locations() → raw JSON str
│   ├── prompt_builder.py           # Phase 1 prompt
│   └── scenario_client.py          # get_scenario() → raw JSON str
├── core/
│   ├── models.py                   # Criterio, Ubicacion, RespuestaIA dataclasses
│   ├── parser.py                   # parse_response(str) → List[dict]
│   └── scenario_parser.py          # parse_scenario(str) → dict
├── tests/                          # Mock data and test helpers — do not use in production
│   ├── mock_client.py              # get_mock_locations() / get_mock_scenario() — drop-in replacements for AI calls
│   ├── mock_ubicaciones.json       # 5 example zones for Tijuana (Phase 1 response shape)
│   └── mock_escenario.json         # Example financial scenario for Zona Río (Phase 2 response shape)
├── fase2/
│   └── AI_INSTRUCTIONS_ESCENARIO.md  # Prompt/instructions reference for Phase 2 scenario
├── requirements.txt
├── .env.example
└── fases_plans/                    # Planning docs only — NO code here
    ├── PLANNING_fase1.md
    └── PLANNING_fase2.md
```

## Hard contracts — do not break

- `ai.gemini_client.get_locations()` returns **raw JSON string** — never parses.
- `ai.scenario_client.get_scenario()` returns **raw JSON string** — never parses.
- `core.parser.parse_response(raw) -> List[dict]` — not `List[Ubicacion]`, plain dicts.
- `core.scenario_parser.parse_scenario(raw) -> dict` — plain dict, not a dataclass.
- `load_dotenv()` called only in `gemini_client.py` — `.env` path is `parents[1]` (repo root).
- `scenario_client.py` must reuse `genai.configure` already done in `gemini_client.py`; do not re-configure.
- `parser.py` computes `nivel` from `puntaje` via `_nivel_from_puntaje()`; the AI never returns `nivel` in criteria objects.
- `CRITERIOS_INVERTIDOS = {"costo_renta", "compatibilidad_capital"}` — for these two, high puntaje means low cost (good), so the level label and UI colour are inverted.

## Phase 2 session_state keys

| Key | Type | Description |
|---|---|---|
| `ubicaciones` | `list[dict]` | Phase 1 results |
| `ubicacion_elegida` | `dict` | User-selected location |
| `escenario` | `dict` | Parsed scenario from `parse_scenario()` |
| `foda` | `dict` | Optional SWOT — `{fortalezas, oportunidades, debilidades, amenazas}` |
| `deuda` | `dict` | Optional debt — `{monto, tasa_anual, plazo_meses}` |

## Phase 2 financial metrics (computed in frontend, no AI call)

- Ingreso mensual = `clientes_dia × ticket_promedio × dias_operacion_mes`
- Punto de equilibrio = `costos_totales / (ticket_promedio × dias_operacion_mes)`
- Pago deuda mensual = French amortisation formula
- Viability semaphore: 🔴 utilidad ≤ 0 · 🟡 recuperación > 24 meses · 🟢 recuperación ≤ 24 meses

## Code style

- `@dataclass` models in `core/models.py`; parsers always return plain `dict`/`List[dict]`, never dataclasses.
- Parsers raise `ValueError` with descriptive messages on missing keys; never silently return `None`.
- `st.session_state` is the only state bridge between Phases 1 and 2.

## Test / mock mode

- `tests/mock_client.py` provides `get_mock_locations()` and `get_mock_scenario(ubicacion)` as drop-in replacements for the real AI calls.
- Mock data lives in `tests/mock_ubicaciones.json` (Phase 1 shape) and `tests/mock_escenario.json` (Phase 2 shape).
- The test button and its imports are delimited by `# ── TEST` / `# ── FIN TEST` comments in `app.py` — remove those blocks and swap back `get_scenario(...)` to disable mock mode.
- `tests/` files must never be imported outside of the clearly marked test blocks in `app.py`.
- Do not modify the JSON schemas in `tests/` — they must always match the shapes validated by `core/parser.py` and `core/scenario_parser.py`.
