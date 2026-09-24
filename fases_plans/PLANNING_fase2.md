# Fase 2 — Plan de Trabajo

## Objetivo

El usuario elige la ubicación que más le convence del análisis de Fase 1.
La IA genera un **escenario financiero base** para ese negocio en esa zona.
El usuario puede dejarlo como está o ajustar variables clave.
Opcionalmente puede añadir un **análisis FODA** y/o declarar **financiamiento con deuda**.
Las métricas se recalculan en tiempo real sin llamar a la IA de nuevo.

---

## Estructura real de archivos (fase 2)

> Nota: el plan original contemplaba `ui/scenario_components.py` y `ai/scenario_prompt.py`
> como archivos separados. La implementación final los consolidó en `ui/components.py`
> y `ai/scenario_client.py` respectivamente.

```
/ (raíz del repositorio)
├── app.py                        # Punto de entrada — fase 2 integrada aquí
├── ui/
│   └── components.py             # Componentes fase 1 y fase 2 en el mismo archivo
├── ai/
│   └── scenario_client.py        # get_scenario() + _build_scenario_prompt() internamente
├── core/
│   └── scenario_parser.py        # parse_scenario(str) → dict
└── tests/
    ├── mock_client.py             # get_mock_scenario(ubicacion) — reemplaza get_scenario() en tests
    └── mock_escenario.json        # Datos de ejemplo (cafetería Zona Río, Tijuana)
```

---

## Estado de tareas

### Backend / IA

- [x] `ai/scenario_client.py` — `get_scenario(giro, capital, ciudad, ubicacion) → str` (JSON crudo)
- [x] Prompt incluye objeto `madurez` (meses_hasta_madurez, porcentaje_ventas_mes1)
- [x] Prompt incluye objeto `foda` (fortalezas, oportunidades, debilidades, amenazas)
- [x] Prompt incluye desgloses `desglose_fijos` y `desglose_variables` como listas de `{concepto, monto}`
- [x] Alerta en prompt cuando capital < 80,000 MXN
- [x] `_clean_json()` extrae JSON aunque Gemini lo envuelva en markdown

### Parser / Datos

- [x] `core/scenario_parser.py` — `parse_scenario(str) → dict`
- [x] Valida todas las claves raíz requeridas
- [x] Valida y coerciona `madurez` (meses int 1–120, pct float 1–100)
- [x] Valida y coerciona `foda` (4 categorías, listas de str)
- [x] Parsea y valida `desglose_fijos` y `desglose_variables` como `list[{concepto, monto}]`
- [x] Calcula `costos_fijos_mes` y `costos_variables_mes` sumando los desgloses (Gemini no los envía)
- [x] `meses_recuperacion_capital` puede ser `null` (utilidad ≤ 0) — se acepta como `None`
- [x] Lanza `ValueError` descriptivo en cualquier campo faltante o mal tipado

### UI — Estado de resultados (`render_escenario`)

- [x] P&L mensual con desgloses expandidos (fijos + variables)
- [x] Modo edición inline (toggle `✏️ Ajustar valores`) — modifica ingresos, fijos, variables, precio
- [x] Viabilidad: 2 KPIs — Margen de contribución y Punto de equilibrio (con precio/costo en subtítulo)
- [x] Recuperación de capital eliminada de este bloque — vive exclusivamente en la curva
- [x] Alerta solo cuando utilidad neta < 0 (estructural)
- [x] Devuelve dict de valores activos (base o ajustados) para pasarlos a `render_madurez()`

### UI — Curva de maduración (`render_madurez`)

- [x] Firma: `render_madurez(escenario: dict, deuda: dict | None = None)`
- [x] Recibe valores activos de `render_escenario()` — reacciona al modo edición
- [x] 3 botones de escenario: 🔴 Pesimista / ⚪ Moderado / 🟢 Optimista
- [x] Multiplicadores por escenario: pesimista ×1.5/×0.7 · moderado base · optimista ×0.65/×1.4 (cap 90%)
- [x] Curva exponencial: `ventas(t) = ventas_maduras × (1 − e^(−k·t))`, `k = ln(20) / meses_hasta_madurez`
- [x] Horizonte dinámico topado en 60 meses: `min(60, max(meses_madurez+6, mes_recuperacion+2))`
- [x] KPIs siempre calculados sobre 60 meses aunque el horizonte visible sea menor
- [x] 3 KPI cards: Break-even real · Capital en riesgo · Recuperación real de inversión
- [x] KPI recuperación: muestra `> 60 meses` si no se alcanza dentro del tope
- [x] Gráfica Plotly: línea costos, curva ingresos, vline break-even, vline recuperación (si visible)
- [x] Alerta narrativa con 4 ramas: capital insuficiente / sin break-even / break-even tardío / éxito

### UI — Deuda (`_calcular_pago_mensual` + integración en curva)

- [x] `_calcular_pago_mensual(monto, tasa_anual, plazo_meses) → (pago_mensual, total_pagado, total_intereses)` — helper puro sin UI
- [x] `render_deuda()` eliminada — la deuda se integra directamente en `render_madurez()`
- [x] Panel colapsable `➕ Agregar financiamiento con deuda` en `app.py` antes de la curva
- [x] Inputs: monto, tasa anual (%), plazo (meses) — pasados como `deuda` dict a `render_madurez()`
- [x] Cuando hay deuda: `pago_mensual` se suma a `costos_totales` en la curva
- [x] Pill informativa encima de la curva: monto · tasa · plazo · pago/mes · % utilidad · total intereses
- [x] Segunda línea en la gráfica (`Costos operativos`) para mostrar el costo sin deuda como referencia

### UI — FODA (`render_foda`)

- [x] Panel colapsable `➕ Agregar análisis FODA`
- [x] 4 columnas editables (text_area por categoría)
- [x] Ediciones guardadas en `st.session_state["foda_editable"]`

### Mock / Tests

- [x] `tests/mock_client.py` — `get_mock_scenario(ubicacion)` devuelve JSON crudo del mock
- [x] `tests/mock_escenario.json` — incluye `madurez`, `foda`, `desglose_fijos`, `desglose_variables`
- [x] Bloque de test delimitado por `# ── TEST` / `# ── FIN TEST` en `app.py`

---

## Flujo de datos (estado actual)

```
Usuario selecciona ubicación en app.py
    │  giro, capital, ciudad, ubicacion_elegida (session_state)
    ▼
ai.scenario_client.get_scenario()  →  JSON string crudo
    ▼
core.scenario_parser.parse_scenario()  →  dict validado (incluye madurez, foda)
    │  guardado en st.session_state["escenario"]
    ▼
ui.components.render_escenario(escenario, modo_edicion)
    │  devuelve _escenario_activo (valores base o ajustados por el usuario)
    ▼
[opcional] panel deuda → _deuda_dict
    ▼
ui.components.render_madurez(_escenario_activo, deuda=_deuda_dict)
    │  curva + KPIs + alertas (deuda integrada si aplica)
    ▼
[opcional] ui.components.render_foda(escenario["foda"])
```

---

## Session state — claves fase 2

| Clave | Tipo | Descripción |
|---|---|---|
| `ubicacion_elegida` | `str` | Nombre de la ubicación seleccionada para fase 2 |
| `escenario` | `dict` | Resultado de `parse_scenario()` — incluye `madurez` y `foda` |
| `modo_edicion_escenario` | `bool` | Toggle del panel de edición inline del P&L |
| `mostrar_foda` | `bool` | Toggle del panel FODA |
| `mostrar_deuda` | `bool` | Toggle del panel de financiamiento con deuda |
| `escenario_madurez` | `str` | Escenario activo de la curva: `"pesimista"`, `"moderado"`, `"optimista"` |

> `foda` y `deuda` **no** son claves de session_state. FODA vive dentro de `escenario["foda"]`;
> deuda se construye inline en `app.py` cada re-render y se pasa directo a `render_madurez()`.

---

## Métricas calculadas en el frontend (sin IA)

| Métrica | Fórmula / Fuente |
|---|---|
| `costos_fijos_mes` | `sum(desglose_fijos[].monto)` — calculado en `parse_scenario()` |
| `costos_variables_mes` | `sum(desglose_variables[].monto)` — calculado en `parse_scenario()` |
| Utilidad neta activa | `ingresos − costos_fijos − costos_variables` (recalculada en modo edición) |
| Margen de contribución | `(precio − costo_variable_unitario) / precio × 100` |
| Punto de equilibrio | `costos_fijos / (precio − costo_variable_unitario)` |
| Pago mensual de deuda | Amortización francesa: `monto × (r × (1+r)^n) / ((1+r)^n − 1)` |
| Curva de ingresos | `ventas_maduras × (1 − e^(−k·t))` re-escalada a `porcentaje_ventas_mes1` en t=1 |
| Break-even real | Primer mes `t` donde `ingresos(t) − costos_totales ≥ 0` |
| Capital quemado | `abs(sum(utilidad(t) for t < mes_breakeven if utilidad(t) < 0))` |
| Recuperación real | Primer mes `t` donde flujo acumulado ≥ capital inicial |

Semáforo de viabilidad (en `render_madurez`):
- 🔴 Capital quemado > capital disponible
- 🔴 Break-even no alcanzado en 60 meses
- 🟡 Break-even > 18 meses
- 🟡 Break-even alcanzado pero recuperación > 60 meses
- 🟢 Break-even ≤ 18 meses y recuperación dentro del horizonte
