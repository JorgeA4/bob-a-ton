# Fase 2 — Plan de Trabajo en Equipo

## Objetivo

El usuario elige la ubicación que más le convence del análisis de Fase 1.
La IA genera un **escenario financiero base** para ese negocio en esa zona.
El usuario puede dejarlo como está o ajustar variables clave.
Opcionalmente puede añadir un **análisis FODA** y/o declarar **financiamiento con deuda**.
Las métricas se recalculan en tiempo real sin llamar a la IA de nuevo.

---

## Estructura de carpetas

El código fuente vive en la **raíz del repositorio**. `fase2/` contiene únicamente archivos de planificación.

```
/ (raíz del repositorio)
├── app.py                        # Punto de entrada Streamlit — extendido con fase 2 (Dev A)
├── ui/
│   ├── components.py             # Componentes de fase 1 — no tocar
│   └── scenario_components.py   # Componentes visuales de fase 2 (Dev A)
├── ai/
│   ├── gemini_client.py          # Cliente fase 1 — no tocar
│   ├── prompt_builder.py         # Prompt fase 1 — no tocar
│   ├── scenario_client.py        # Llamada a Gemini para escenario (Dev B)
│   └── scenario_prompt.py        # Construcción del prompt de escenario (Dev B)
├── core/
│   ├── models.py                 # Modelos fase 1 — no tocar
│   ├── parser.py                 # Parser fase 1 — no tocar
│   └── scenario_parser.py        # Parseo y validación del escenario (Dev C)
└── fase2/
    └── PLANNING.md               # Este archivo
```

---

## División de responsabilidades

### 👤 Dev A — UI / Streamlit
**Archivos propios:** `app.py`, `ui/scenario_components.py`

**Tareas:**
- [ ] Añadir selector de ubicación al final de los resultados de fase 1 en `app.py`
- [ ] Guardar la ubicación elegida y el resultado de fase 1 en `st.session_state`
- [ ] Llamar a `get_scenario()` y `parse_scenario()` al confirmar la selección
- [ ] Renderizar el escenario base con `render_escenario()` (sin edición por defecto)
- [ ] Implementar botón "✏️ Ajustar escenario" que expande los controles de edición
- [ ] Recalcular y mostrar métricas en tiempo real al cambiar variables con `render_metricas()`
- [ ] Implementar botón "➕ Agregar análisis FODA" con `render_foda()`
- [ ] Implementar botón "➕ Agregar financiamiento con deuda" con `render_deuda()`
- [ ] Recalcular métricas incluyendo pago mensual de deuda cuando aplique

**Contratos que debe respetar:**
- Llamar a `ai.scenario_client.get_scenario(giro, capital, ciudad, ubicacion) -> str`
- Parsear con `core.scenario_parser.parse_scenario(raw) -> dict`
- Leer ubicación elegida de `st.session_state["ubicacion_elegida"]`
- Escribir en `st.session_state`: `escenario`, `foda`, `deuda`
- No modificar ningún archivo de fase 1

---

### 👤 Dev B — IA / Gemini
**Archivos propios:** `ai/scenario_client.py`, `ai/scenario_prompt.py`

**Tareas:**
- [ ] Escribir `build_scenario_prompt(giro, capital, ciudad, ubicacion) -> str` en `scenario_prompt.py`
  - El prompt debe instruir a Gemini a responder **solo** con JSON válido
  - Debe incluir la estructura exacta del JSON esperado (ver esquema más abajo)
- [ ] Escribir `get_scenario(giro, capital, ciudad, ubicacion) -> str` en `scenario_client.py`
  - Reutiliza la configuración de Gemini (`genai.configure`) ya hecha en `gemini_client.py`
  - Llama a `build_scenario_prompt()`
  - Devuelve el string JSON crudo (sin parsear)
  - Maneja errores de red y cuota con excepciones claras

**Contratos que debe respetar:**
- `get_scenario()` devuelve el JSON **como string** — el parseo lo hace Dev C
- El modelo a usar: `gemini-3.6-flash`
- No modificar `gemini_client.py` ni `prompt_builder.py`

**Esquema JSON que debe devolver Gemini:**

```json
{
  "ubicacion": "nombre de la zona elegida",
  "giro": "giro del negocio",
  "inversion_inicial": {
    "renta_deposito": 0,
    "adecuaciones": 0,
    "equipo": 0,
    "inventario_inicial": 0,
    "otros": 0
  },
  "costos_fijos_mensuales": {
    "renta": 0,
    "nomina": 0,
    "servicios": 0,
    "otros": 0
  },
  "proyeccion_ingresos": {
    "clientes_dia_estimado": 0,
    "ticket_promedio": 0,
    "dias_operacion_mes": 0
  },
  "supuestos": "2-3 líneas explicando en qué se basan las cifras"
}
```

---

### 👤 Dev C — Datos / Modelos
**Archivos propios:** `core/scenario_parser.py`

**Tareas:**
- [ ] Escribir `parse_scenario(json_str: str) -> dict` en `scenario_parser.py`
  - Llama a `json.loads()` dentro de try/except para capturar `json.JSONDecodeError`
  - Valida claves requeridas: `ubicacion`, `giro`, `inversion_inicial`, `costos_fijos_mensuales`, `proyeccion_ingresos`, `supuestos`
  - Valida subclaves de cada sección (ver esquema de Dev B)
  - Coerciona todos los valores numéricos a `float`
  - Lanza `ValueError` con mensaje descriptivo si falta cualquier clave requerida
  - Ignora claves desconocidas en cualquier nivel
  - Devuelve el dict validado y coercionado (no un dataclass — consistente con `parse_response`)

**Contratos que debe respetar:**
- `parse_scenario()` recibe el string crudo de Dev B y devuelve `dict` para Dev A
- No modificar `models.py`, `parser.py` ni ningún archivo de fase 1

---

## Flujo de datos entre los tres devs

```
[Dev A] Usuario selecciona ubicación de los resultados de fase 1
    │  giro, capital, ciudad, ubicacion_elegida
    ▼
[Dev B] scenario_client.get_scenario()
    │  prompt → Gemini API → JSON string
    ▼
[Dev C] scenario_parser.parse_scenario()
    │  JSON string → dict validado
    ▼
[Dev A] ui/scenario_components.py
    │  dict → escenario base + simulador + métricas
    ▼
[Dev A] Opcionales: FODA y/o deuda → recalculo de métricas
```

---

## Puntos de integración (evitar conflictos)

| Punto | Quién produce | Quién consume | Formato acordado |
|---|---|---|---|
| Resultado de IA | Dev B (`get_scenario`) | Dev C (`parse_scenario`) | `str` JSON crudo |
| Escenario parseado | Dev C (`parse_scenario`) | Dev A (`app.py`) | `dict` con claves validadas |
| Componentes visuales | Dev A (`scenario_components.py`) | Dev A (`app.py`) | Funciones que reciben `dict` |
| Estado entre fases | Dev A | Dev A | `st.session_state` con claves acordadas |

**Regla:** Nadie toca los archivos del otro sin avisar. Si se necesita cambiar una firma de función, se acuerda primero.

---

## Session state — claves acordadas

| Clave | Tipo | Quién escribe | Descripción |
|---|---|---|---|
| `ubicaciones` | `list[dict]` | Dev A (fase 1) | Resultados completos de fase 1 |
| `ubicacion_elegida` | `dict` | Dev A (fase 2) | Ubicación seleccionada por el usuario |
| `escenario` | `dict` | Dev A (fase 2) | Escenario base devuelto por `parse_scenario()` |
| `foda` | `dict` | Dev A (fase 2) | `{fortalezas, oportunidades, debilidades, amenazas}` — opcional |
| `deuda` | `dict` | Dev A (fase 2) | `{monto, tasa_anual, plazo_meses}` — opcional |

---

## Métricas calculadas en el frontend (sin IA)

| Métrica | Fórmula |
|---|---|
| Ingreso mensual | `clientes_dia × ticket_promedio × dias_operacion_mes` |
| Costos totales mensuales | `suma(costos_fijos) + pago_deuda_mensual` |
| Utilidad mensual | `ingreso_mensual − costos_totales_mensuales` |
| Punto de equilibrio (clientes/día) | `costos_totales_mensuales / (ticket_promedio × dias_operacion_mes)` |
| Meses para recuperar inversión | `suma(inversion_inicial) / utilidad_mensual` |
| Pago mensual de deuda | `monto × (tasa_mensual) / (1 − (1 + tasa_mensual)^−plazo)` (amortización francesa) |

Semáforo de viabilidad: 🔴 utilidad ≤ 0 · 🟡 utilidad > 0 pero recuperación > 24 meses · 🟢 recuperación ≤ 24 meses

---

## Orden de desarrollo sugerido

1. **Dev C empieza primero** — `parse_scenario()` define el contrato de datos para Dev A
2. **Dev B y Dev A arrancan en paralelo** una vez que `parse_scenario()` está listo
3. **Integración final** — Dev A conecta todo en `app.py` usando un dict mock si Dev B o Dev C no han terminado
