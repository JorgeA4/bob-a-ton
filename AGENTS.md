# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Stack

- Python + Streamlit frontend (`app.py` in repo root)
- Gemini API via `google-generativeai` — model: `gemini-3.6-flash`
- `python-dotenv` for secrets; `.env` must contain `GEMINI_API_KEY`
- `requests` for live USD→MXN exchange rate (`api.frankfurter.app`); cached 1 hour via `@st.cache_data`
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
│   ├── gemini_client.py            # get_locations(giro, capital, ciudad, zona_preferida) → raw JSON str
│   ├── prompt_builder.py           # Phase 1 prompt
│   └── scenario_client.py          # get_scenario(giro, capital, ciudad, ubicacion) → raw JSON str
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
    ├── PLANNING_fase2.md
    └── dev-c-fase2-plan.md
```

## Hard contracts — do not break

- `ai.gemini_client.get_locations()` returns **raw JSON string** — never parses.
- `ai.scenario_client.get_scenario()` returns **raw JSON string** — never parses.
- `core.parser.parse_response(raw) -> List[dict]` — not `List[Ubicacion]`, plain dicts.
- `core.scenario_parser.parse_scenario(raw) -> dict` — plain dict, not a dataclass.
- `load_dotenv()` called only in `gemini_client.py` — `.env` path is `parents[1]` (repo root).
- `scenario_client.py` calls `_ensure_configured()` (idempotent load_dotenv + genai.configure) — do not assume gemini_client was imported first.
- `parser.py` computes `nivel` from `puntaje` via `_nivel_from_puntaje()`; the AI never returns `nivel` in criteria objects.
- `CRITERIOS_INVERTIDOS = {"costo_renta", "compatibilidad_capital"}` — for these two, high puntaje means low cost (good), so the level label and UI colour are inverted.
- `parse_response()` detects an unrecognised-giro signal: if the root JSON contains an `"error"` key it raises `ValueError` with the `"mensaje"` value — never returns a partial list.
- Currency conversion: when the user inputs capital in USD, `app.py` fetches a live rate from `api.frankfurter.app` and converts to MXN **before** storing. `st.session_state["capital"]` is **always in MXN**, regardless of the currency selected in the form.

## session_state keys

| Key | Type | Description |
|---|---|---|
| `ubicaciones` | `list[dict]` | Phase 1 results |
| `giro` | `str` | Business type submitted in the form |
| `capital` | `float` | Initial capital **always in MXN** (converted from USD if needed) |
| `ciudad` | `str` | City submitted in the form |
| `zona_preferida` | `str` | Optional preferred zone submitted in the form |
| `ubicacion_elegida` | `str` | Name of the location selected for Phase 2 |
| `escenario` | `dict` | Parsed scenario from `parse_scenario()` — includes `foda` sub-dict |
| `modo_edicion_escenario` | `bool` | Toggle for inline edit mode in the P&L (replaces the old separate adjust panel) |
| `mostrar_foda` | `bool` | Toggle for the FODA panel |
| `mostrar_deuda` | `bool` | Toggle for the debt-financing panel |
| `_moneda_form` | `str` | Currency selected in the form radio (`"MXN"` or `"USD"`); managed by Streamlit widget state |

Notes:
- `foda` and `deuda` are **not** standalone session_state keys. FODA data lives inside `escenario["foda"]`; debt inputs are built inline in `app.py` and passed directly to `render_deuda()`.
- All Phase 2 toggle keys (`mostrar_ajustes`, `mostrar_foda`, `mostrar_deuda`) are cleared whenever a new Phase 1 analysis is submitted or a new location is confirmed.

## Phase 2 financial metrics (computed in frontend, no AI call)

- Gemini returns pre-computed `ingresos_estimados_mes`, `costos_fijos_mes`, `costos_variables_mes`, `utilidad_neta_mes`, `punto_equilibrio_unidades`, `meses_recuperacion_capital`, `precio_unitario_promedio`, `costo_variable_unitario` — all floats, MXN/month.
- The adjust panel is inline in `render_escenario()` (toggle via `modo_edicion_escenario` session state key); viability KPIs recalculate in real time with the edited values.
- Pago deuda mensual = French amortisation formula (applied in `render_deuda()`).
- Viability semaphore: 🔴 utilidad ≤ 0 · 🟡 recuperación > 24 meses · 🟢 recuperación ≤ 24 meses

## Phase 2 scenario JSON schema (flat — returned by `get_scenario()`, validated by `parse_scenario()`)

```json
{
  "giro": "str",
  "capital": "float",
  "ciudad": "str",
  "ubicacion": "str",
  "ingresos_estimados_mes": "float",
  "costos_fijos_mes": "float",
  "costos_variables_mes": "float",
  "utilidad_neta_mes": "float",
  "punto_equilibrio_unidades": "float",
  "meses_recuperacion_capital": "float | null",
  "precio_unitario_promedio": "float",
  "costo_variable_unitario": "float",
  "foda": {
    "fortalezas": ["str", "..."],
    "oportunidades": ["str", "..."],
    "debilidades": ["str", "..."],
    "amenazas": ["str", "..."]
  }
}
```

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
