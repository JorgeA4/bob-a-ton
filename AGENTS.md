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
    └── PLANNING_fase2.md
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
| `escenario` | `dict` | Parsed scenario from `parse_scenario()` — includes `madurez` and `foda` sub-dicts |
| `modo_edicion_escenario` | `bool` | Toggle for inline edit mode in the P&L (replaces the old separate adjust panel) |
| `mostrar_foda` | `bool` | Toggle for the FODA panel |
| `mostrar_deuda` | `bool` | Toggle for the debt-financing panel; auto-set to `True` when `inversion_inicial > capital` |
| `escenario_madurez` | `str` | Active maturity scenario: `"pesimista"`, `"moderado"`, or `"optimista"` (default `"moderado"`) |
| `_moneda_form` | `str` | Currency selected in the form radio (`"MXN"` or `"USD"`); managed by Streamlit widget state |
| `_deuda_sugerida` | `float` | Transient key — pre-fills debt amount input with `inversion_inicial − capital` when debt is auto-activated; consumed (popped) on first render |

Notes:
- `foda` and `deuda` are **not** standalone session_state keys. FODA data lives inside `escenario["foda"]`; debt inputs are built inline in `app.py` and passed as a `deuda` dict directly to `render_madurez()`.
- All Phase 2 toggle keys (`modo_edicion_escenario`, `mostrar_foda`, `mostrar_deuda`) are cleared whenever a new Phase 1 analysis is submitted or a new location is confirmed.
- `escenario_madurez` persists between re-renders — it is NOT cleared on new analysis (the user's scenario selection is intentional). Clear it manually if needed.
- When a new scenario is generated, if `inversion_inicial > capital` the debt panel opens automatically with the shortfall pre-filled in `_deuda_sugerida`. `_deuda_sugerida` is a one-shot key — it is popped on the first render so subsequent user edits to the amount are not overwritten.

## Phase 2 financial metrics (computed in frontend, no AI call)

- Gemini returns `ingresos_estimados_mes`, `inversion_inicial`, `desglose_fijos` (list), `desglose_variables` (list), `utilidad_neta_mes`, `punto_equilibrio_unidades`, `meses_recuperacion_capital`, `precio_unitario_promedio`, `costo_variable_unitario`, `madurez` (object). `costos_fijos_mes` and `costos_variables_mes` are **computed by `parse_scenario()`** by summing the respective breakdown lists — Gemini never sends them.
- The adjust panel is inline in `render_escenario()` (toggle via `modo_edicion_escenario` session state key); viability KPIs recalculate in real time with the edited values. `render_escenario()` returns a dict of active values (base or user-adjusted) that is passed to `render_madurez()`. The returned dict includes `"inversion_inicial"` so edits propagate to the maturity curve.
- `render_escenario()` edit mode exposes `inversion_inicial` as an editable `number_input` (key `"escenario_inversion"`). Changing it updates the recovery threshold in `render_madurez()` and may trigger or dismiss the auto-debt warning.
- `render_escenario()` viability block shows two KPIs only: **Margen de contribución** and **Punto de equilibrio**. Recovery is intentionally omitted here — it lives exclusively in the maturity curve.
- French amortisation formula lives in `_calcular_pago_mensual(monto, tasa_anual, plazo_meses) → (pago_mensual, total_pagado, total_intereses)` — a pure helper with no Streamlit calls. `render_deuda()` no longer exists.
- Debt financing: the user opens an optional `➕ Agregar financiamiento con deuda` panel in `app.py`; its three inputs (monto, tasa_anual, plazo_meses) are collected and passed as `deuda: dict` to `render_madurez()`. When present, `pago_mensual` is added to `costos_totales` in the curve. A pill above the chart summarises the credit terms. The panel **auto-opens** when `inversion_inicial > capital`, with the shortfall pre-filled as the suggested credit amount.
- Maturity curve (`render_madurez(escenario, deuda=None)`): exponential saturation `ventas(t) = ventas_maduras × (1 − e^(−k·t))`, re-scaled so `ventas(1) == porcentaje_ventas_mes1 %` and `ventas(meses_hasta_madurez) ≈ 95 %`. `k = ln(20) / meses_hasta_madurez`. Three scenarios apply multipliers to `meses_hasta_madurez` and `porcentaje_ventas_mes1` — the math is purely in the frontend; the AI only supplies the two base parameters.
- Maturity curve recovery threshold: `flujo_acumulado >= inversion_inicial` (falls back to `capital` if `inversion_inicial` is absent or zero). This measures real return of the one-time opening investment, not just the declared capital.
- Maturity curve horizon: KPIs (break-even, capital quemado, recuperación) are always computed over the full 60-month ceiling. The chart's x-axis extends to `min(60, max(meses_madurez + 6, mes_recuperacion + 2))` so the recovery point is always visible when it falls within 60 months. If recovery exceeds 60 months the KPI shows `> 60 meses`.

## Phase 2 scenario JSON schema (returned by `get_scenario()`, validated by `parse_scenario()`)

```json
{
  "giro": "str",
  "capital": "float",
  "ciudad": "str",
  "ubicacion": "str",
  "ingresos_estimados_mes": "float",
  "inversion_inicial": "float",
  "desglose_fijos": [{"concepto": "str", "monto": "float"}, "..."],
  "desglose_variables": [{"concepto": "str", "monto": "float"}, "..."],
  "utilidad_neta_mes": "float",
  "punto_equilibrio_unidades": "float",
  "meses_recuperacion_capital": "float | null",
  "precio_unitario_promedio": "float",
  "costo_variable_unitario": "float",
  "madurez": {
    "meses_hasta_madurez": "int (6–48)",
    "porcentaje_ventas_mes1": "float (5–80)"
  },
  "foda": {
    "fortalezas": ["str", "..."],
    "oportunidades": ["str", "..."],
    "debilidades": ["str", "..."],
    "amenazas": ["str", "..."]
  }
}
```

`costos_fijos_mes` y `costos_variables_mes` **no los devuelve Gemini** — `parse_scenario()` los calcula sumando los montos del desglose correspondiente y los añade al dict resultado. Los consumidores (`render_escenario`, `render_madurez`) los reciben normalmente.

## Code style

- `@dataclass` models in `core/models.py`; parsers always return plain `dict`/`List[dict]`, never dataclasses.
- Parsers raise `ValueError` with descriptive messages on missing keys; never silently return `None`.
- `st.session_state` is the only state bridge between Phases 1 and 2.

## Test / mock mode

- `tests/mock_client.py` provides `get_mock_locations()` and `get_mock_scenario(ubicacion)` as drop-in replacements for the real AI calls.
- Mock data lives in `tests/mock_ubicaciones.json` (Phase 1 shape) and `tests/mock_escenario.json` (Phase 2 shape).
- The test button and its imports are delimited by `# ── TEST` / `# ── FIN TEST` comments in `app.py` — remove those blocks and swap back `get_scenario(...)` to disable mock mode.
- `tests/` files must never be imported outside of the clearly marked test blocks in `app.py`.
- `tests/mock_escenario.json` must always match the shape validated by `core/scenario_parser.py`. When the Phase 2 JSON schema changes, update both the parser and the mock together.
