# Fase 3 — Plan de Trabajo

## Objetivo

Una vez que el usuario ha revisado y (opcionalmente) ajustado el escenario financiero de Fase 2,
puede solicitar un **análisis de vulnerabilidades** del negocio.

El análisis es **híbrido**:
1. **Capa numérica (determinista)** — el sistema evalúa el escenario con reglas matemáticas
   y produce una lista de alertas objetivas con severidad.
2. **Capa IA (Gemini)** — recibe el contexto completo (escenario activo, deuda, criterios de Fase 1,
   FODA, alertas numéricas ya detectadas) y enriquece el análisis con:
   - Riesgos cuantificables que los números confirman pero requieren interpretación.
   - Riesgos contextuales derivados del FODA, la zona, el giro y la combinación del contexto.

Al solicitar el análisis, **la sección de Fase 2 queda cerrada** (colapsada) y no puede
modificarse. Los valores congelados son los que el usuario dejó al pulsar el botón.

---

## Archivos nuevos y modificados

```
/ (raíz del repositorio)
├── app.py                              # Dev A — botón Fase 3, colapso Fase 2, orquestación
├── ui/
│   └── components.py                  # Dev A — añadir render_vulnerabilidades()
├── ai/
│   └── vulnerability_client.py        # Dev B — get_vulnerability_analysis() + prompt
├── core/
│   ├── vulnerability_analyzer.py      # Dev C — análisis numérico determinista
│   └── vulnerability_parser.py        # Dev C — parse_vulnerability(str) → dict
├── tests/
│   ├── mock_client.py                 # Dev A — añadir get_mock_vulnerability()
│   └── mock_vulnerabilidad.json       # Dev B — datos de ejemplo para desarrollo
└── fases_plans/
    └── PLANNING_fase3.md              # Este archivo
```

Archivos de Fases 1 y 2 que **no se tocan**:
`ai/gemini_client.py`, `ai/prompt_builder.py`, `ai/scenario_client.py`,
`core/models.py`, `core/parser.py`, `core/scenario_parser.py`.

---

## División de responsabilidades

### 👤 Dev A — UI / Streamlit
**Archivos propios:** `app.py`, `ui/components.py`, `tests/mock_client.py`

**Tareas:**
- [ ] En `app.py`, añadir botón `🔬 Analizar vulnerabilidades` al final de la sección de Fase 2
- [ ] Al pulsar el botón: congelar `_escenario_activo` y `_deuda_dict` en `session_state` como `escenario_congelado` y `deuda_congelada`; marcar `session_state["fase3_activa"] = True`
- [ ] Cuando `fase3_activa` es `True`, envolver la sección completa de Fase 2 en un `st.expander("📋 Escenario financiero", expanded=False)` colapsado
- [ ] Orquestar la llamada: pasar las alertas numéricas (Dev C) + contexto completo a `get_vulnerability_analysis()` (Dev B), parsear con `parse_vulnerability()` (Dev C), guardar en `session_state["analisis_vulnerabilidades"]`
- [ ] Recuperar criterios de la ubicación elegida desde `session_state["ubicaciones"]` buscando el dict cuyo `nombre == session_state["ubicacion_elegida"]` — **opción A, sin clave nueva en session_state**
- [ ] Añadir `render_vulnerabilidades(alertas_numericas, analisis_ia)` en `ui/components.py`
- [ ] En `tests/mock_client.py` añadir `get_mock_vulnerability()` que devuelve el JSON crudo de `tests/mock_vulnerabilidad.json`
- [ ] Bloque de test delimitado por `# ── TEST` / `# ── FIN TEST` para la llamada a `get_vulnerability_analysis()`

**Contratos que debe respetar:**
- Llamar a `core.vulnerability_analyzer.analizar_vulnerabilidades(escenario_activo, deuda, criterios_ubicacion) -> list[dict]`
- Llamar a `ai.vulnerability_client.get_vulnerability_analysis(escenario_activo, deuda, criterios_ubicacion, alertas_numericas) -> str`
- Parsear el resultado con `core.vulnerability_parser.parse_vulnerability(raw) -> dict`
- Los valores congelados en `escenario_congelado` son los que el usuario dejó al pulsar el botón — nunca los valores base de la IA si el usuario los editó
- `fase3_activa` se limpia junto con el resto del estado de Fase 2 cuando el usuario hace un nuevo análisis de Fase 1 o confirma una nueva ubicación

---

### 👤 Dev B — IA / Gemini
**Archivos propios:** `ai/vulnerability_client.py`, `tests/mock_vulnerabilidad.json`

**Tareas:**
- [ ] Crear `ai/vulnerability_client.py` con `get_vulnerability_analysis(escenario_activo, deuda, criterios_ubicacion, alertas_numericas) -> str`
- [ ] Reutilizar `_ensure_configured()` — copiar el patrón de `scenario_client.py` (load_dotenv + genai.configure idempotente)
- [ ] Escribir `_build_vulnerability_prompt(...)` que construya el prompt con el contexto completo (ver sección "Contexto del prompt" abajo)
- [ ] El prompt debe indicar explícitamente que las alertas numéricas ya están detectadas — Gemini no debe repetirlas, debe profundizar y añadir lo que los números no capturan
- [ ] Incluir `_clean_json()` (igual que en `scenario_client.py`) para extraer JSON aunque Gemini lo envuelva en markdown
- [ ] Crear `tests/mock_vulnerabilidad.json` con un ejemplo válido del JSON de respuesta que respete el schema acordado (ver sección "Schema JSON Fase 3")

**Contratos que debe respetar:**
- `get_vulnerability_analysis()` devuelve el JSON **como string** — el parseo lo hace Dev C
- El modelo a usar: `gemini-3.6-flash`
- El prompt instruye a Gemini a responder **solo** con JSON válido, sin bloques markdown
- `riesgos_cuantificables` son los que los números confirman pero requieren interpretación (ej. sensibilidad al precio, impacto de variación de costos); `riesgos_contextuales` son los derivados del FODA, zona y giro
- El campo `veredicto` debe ser exactamente uno de: `"viable"` | `"viable_con_reservas"` | `"riesgo_alto"` | `"no_viable"`

---

### 👤 Dev C — Datos / Lógica numérica
**Archivos propios:** `core/vulnerability_analyzer.py`, `core/vulnerability_parser.py`

**Tareas:**

#### `core/vulnerability_analyzer.py`
- [ ] Escribir `analizar_vulnerabilidades(escenario_activo: dict, deuda: dict | None, criterios_ubicacion: dict) -> list[dict]`
- [ ] Implementar las 12 reglas numéricas (ver tabla "Reglas del analizador numérico" abajo)
- [ ] Cada alerta devuelta tiene la estructura `{severidad, categoria, titulo, detalle, datos}` (ver sección "Estructura de alerta")
- [ ] Las alertas se ordenan por severidad: `critica` primero, luego `alta`, luego `media`
- [ ] Si no se detecta ningún problema, devolver lista vacía — es un resultado válido
- [ ] La función es **pura** (sin efectos secundarios, sin imports de Streamlit)
- [ ] Para calcular `capital_quemado` en la curva, reutilizar la misma lógica que `render_madurez()`: curva exponencial con los factores del escenario **moderado** (`meses_factor=1.0`, `pct_factor=1.0`) — no importar `ui/components.py`; duplicar las 3 funciones matemáticas necesarias (`_curva_params`, `_flujo_mensual`, iteración de flujo acumulado) dentro del módulo

#### `core/vulnerability_parser.py`
- [ ] Escribir `parse_vulnerability(json_str: str) -> dict`
- [ ] Validar claves raíz: `resumen_ejecutivo` (str), `riesgos_cuantificables` (list), `riesgos_contextuales` (list), `veredicto` (str)
- [ ] Validar que `veredicto` sea exactamente uno de los 4 valores permitidos; lanzar `ValueError` si no
- [ ] Validar cada item de `riesgos_cuantificables`: claves `titulo`, `descripcion`, `severidad`, `mitigacion` — todas strings
- [ ] Validar cada item de `riesgos_contextuales`: claves `titulo`, `descripcion`, `severidad`, `fuente`, `mitigacion` — todas strings; `fuente` debe ser `"foda"` | `"zona"` | `"giro"` | `"deuda"`
- [ ] Lanzar `ValueError` descriptivo en cualquier campo faltante o mal tipado — nunca devolver silenciosamente `None`

**Contratos que debe respetar:**
- `analizar_vulnerabilidades()` y `parse_vulnerability()` son funciones puras sin dependencias de Streamlit
- `analizar_vulnerabilidades()` nunca lanza excepciones por datos faltantes — usa `.get()` con defaults seguros
- `parse_vulnerability()` sí lanza `ValueError` en datos inválidos — es el guardián del contrato con la IA

---

## Contexto del prompt (Dev B)

El prompt enviado a Gemini incluye las siguientes secciones, en este orden:

1. **Rol y tarea**: consultor de riesgos para pequeños negocios en México
2. **Ficha del negocio**: giro, capital declarado, ciudad, ubicación
3. **Escenario financiero activo** (valores que el usuario dejó al cerrar Fase 2):
   - Ingresos estimados, costos fijos, costos variables, utilidad neta (todos MXN/mes)
   - Inversión de apertura (one-time)
   - Margen de contribución (%), punto de equilibrio (unidades)
   - Curva de madurez: meses hasta madurez, % ventas mes 1
   - Mes de break-even (escenario moderado), capital quemado, mes de recuperación
4. **Deuda** (si existe): monto, tasa anual, plazo, pago mensual
5. **Criterios de la ubicación** (Fase 1): los 9 puntajes con sus niveles y notas
6. **FODA completo**: las 4 categorías con sus items (incluyendo ediciones del usuario si las hay)
7. **Alertas numéricas detectadas**: lista con título y detalle de cada alerta; instrucción explícita: *"Estos problemas ya están identificados. No los repitas. Profundiza en su implicación o añade riesgos que los números solos no capturan."*
8. **Instrucciones de respuesta**: solo JSON válido, sin markdown

---

## Reglas del analizador numérico (Dev C)

Las reglas se evalúan siempre sobre el escenario **moderado** (sin multiplicadores),
salvo donde se indica explícitamente el escenario pesimista.

| # | Condición | Severidad | Categoría | Título |
|---|---|---|---|---|
| 1 | `inversion_inicial > capital` | crítica | capital | Apertura financieramente inviable sin financiamiento |
| 2 | `capital_quemado > inversion_inicial` (moderado) | crítica | liquidez | La rampa consume más de lo que costó abrir |
| 3 | `capital_quemado > capital` (moderado) | crítica | liquidez | Capital insuficiente para sostener la rampa |
| 4 | `utilidad_neta_mes <= 0` | crítica | rentabilidad | El negocio no genera utilidad en régimen estable |
| 5 | Break-even no alcanzado en 60 meses (moderado) | crítica | rentabilidad | El negocio no alcanza rentabilidad en el horizonte proyectado |
| 6 | Break-even > 24 meses (moderado) | alta | rentabilidad | Período de pérdidas excesivamente largo |
| 7 | Margen de contribución < 20% | alta | rentabilidad | Margen de contribución peligrosamente estrecho |
| 8 | `costos_fijos_mes / ingresos_estimados_mes > 0.70` | alta | rentabilidad | Estructura de costos fijos dominante |
| 9 | `pago_mensual_deuda / utilidad_neta_mes > 0.40` (solo si hay deuda y utilidad > 0) | alta | deuda | Carga de deuda absorbe más del 40% de la utilidad |
| 10 | `capital_quemado > capital` en escenario **pesimista** (aunque no crítico en moderado) | media | liquidez | Escenario pesimista agota el capital disponible |
| 11 | Recuperación de inversión > 48 meses (moderado) | media | capital | Retorno de inversión muy tardío |
| 12 | `punto_equilibrio_unidades > ingresos_estimados_mes / precio_unitario_promedio * 0.80` | alta | rentabilidad | Punto de equilibrio cercano a la capacidad máxima estimada |

> Las reglas no son excluyentes — un mismo escenario puede disparar varias.
> Si `utilidad_neta_mes <= 0`, las reglas 9 y 12 no se evalúan (división por cero).

---

## Estructura de alerta (Dev C → Dev A → Dev B)

Cada alerta que devuelve `analizar_vulnerabilidades()` tiene esta forma:

```python
{
    "severidad": "critica" | "alta" | "media",
    "categoria": "capital" | "liquidez" | "rentabilidad" | "deuda",
    "titulo": str,       # nombre corto de la alerta
    "detalle": str,      # explicación con los valores concretos interpolados
    "datos": dict        # valores numéricos crudos usados en la evaluación
                         # (útil para que el prompt de Dev B sea preciso)
}
```

Ejemplo:
```python
{
    "severidad": "critica",
    "categoria": "liquidez",
    "titulo": "Capital insuficiente para sostener la rampa",
    "detalle": "En el escenario moderado, el negocio acumula $47,000 en pérdidas antes de ser rentable, pero el capital disponible es $30,000.",
    "datos": {"capital_quemado": 47000.0, "capital": 30000.0}
}
```

---

## Schema JSON Fase 3 (contrato Dev B → Dev C)

```json
{
  "resumen_ejecutivo": "str — 2 a 4 oraciones sobre el perfil de riesgo general del negocio",
  "riesgos_cuantificables": [
    {
      "titulo": "str",
      "descripcion": "str — cuantifica el impacto con números concretos del contexto",
      "severidad": "critica | alta | media",
      "mitigacion": "str — acción concreta y específica"
    }
  ],
  "riesgos_contextuales": [
    {
      "titulo": "str",
      "descripcion": "str — basado en FODA, zona, giro o combinación del contexto",
      "severidad": "alta | media | baja",
      "fuente": "foda | zona | giro | deuda",
      "mitigacion": "str — acción concreta y específica"
    }
  ],
  "veredicto": "viable | viable_con_reservas | riesgo_alto | no_viable"
}
```

> `riesgos_cuantificables` puede ser lista vacía `[]` si la IA no identifica riesgos adicionales
> a los ya capturados por el analizador numérico.
> `riesgos_contextuales` siempre debe tener al menos 1 item — hay contexto suficiente para opinar.

---

## Flujo de datos

```
Usuario pulsa "🔬 Analizar vulnerabilidades" en app.py
    │
    │  Congelar en session_state:
    │    escenario_congelado  ← _escenario_activo (valores editados por el usuario)
    │    deuda_congelada      ← _deuda_dict (None si no hay deuda)
    │    fase3_activa = True
    │
    │  Buscar criterios de ubicación:
    │    criterios_ubicacion ← session_state["ubicaciones"] donde nombre == ubicacion_elegida
    ▼
core.vulnerability_analyzer.analizar_vulnerabilidades(
    escenario_congelado, deuda_congelada, criterios_ubicacion
)
    │  → alertas_numericas: list[dict]  (puede ser vacía)
    ▼
ai.vulnerability_client.get_vulnerability_analysis(
    escenario_congelado, deuda_congelada, criterios_ubicacion, alertas_numericas
)
    │  → JSON crudo (str)
    ▼
core.vulnerability_parser.parse_vulnerability(raw)
    │  → dict validado
    │  guardado en session_state["analisis_vulnerabilidades"]
    ▼
ui.components.render_vulnerabilidades(alertas_numericas, analisis_ia)
    │  sección Fase 3 visible
    ▼
Fase 2 queda en st.expander("📋 Escenario financiero", expanded=False)
```

---

## Session state — claves nuevas en Fase 3

| Clave | Tipo | Descripción |
|---|---|---|
| `fase3_activa` | `bool` | `True` cuando el usuario ha solicitado el análisis; hace colapsar Fase 2 |
| `escenario_congelado` | `dict` | Copia de `_escenario_activo` en el momento de pulsar el botón; no cambia aunque el usuario reabra Fase 2 |
| `deuda_congelada` | `dict \| None` | Copia de `_deuda_dict` en el momento de pulsar el botón |
| `analisis_vulnerabilidades` | `dict` | Resultado de `parse_vulnerability()` — incluye `resumen_ejecutivo`, `riesgos_cuantificables`, `riesgos_contextuales`, `veredicto` |

> `fase3_activa`, `escenario_congelado`, `deuda_congelada` y `analisis_vulnerabilidades`
> se limpian junto con el resto del estado de Fase 2 cuando el usuario hace un nuevo análisis
> de Fase 1 o confirma una nueva ubicación en Fase 2.

---

## Layout de `render_vulnerabilidades(alertas_numericas, analisis_ia)` (Dev A)

```
┌─────────────────────────────────────────────────────────────────┐
│  🔬 Análisis de vulnerabilidades                                │
│  [resumen_ejecutivo — texto narrativo de 2-4 líneas]            │
│  Veredicto: [badge con color según veredicto]                   │
│    viable → 🟢   viable_con_reservas → 🟡                       │
│    riesgo_alto → 🟠   no_viable → 🔴                            │
└─────────────────────────────────────────────────────────────────┘

━━ Alertas detectadas automáticamente ━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Solo si alertas_numericas no está vacía]
Cards ordenadas por severidad (crítica → alta → media).
Cada card muestra: badge de severidad · título · detalle

━━ Riesgos cuantificables ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Solo si riesgos_cuantificables no está vacía]
Cards con: badge de severidad · título · descripción · mitigación

━━ Riesgos contextuales ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cards con: badge de fuente (FODA | Zona | Giro | Deuda)
           badge de severidad · título · descripción · mitigación
```

Si `alertas_numericas` está vacía y `riesgos_cuantificables` también, mostrar
un mensaje positivo: *"No se detectaron problemas numéricos estructurales."*

---

## Puntos de integración (evitar conflictos)

| Punto | Quién produce | Quién consume | Formato acordado |
|---|---|---|---|
| Alertas numéricas | Dev C (`analizar_vulnerabilidades`) | Dev A (`app.py`) y Dev B (como contexto del prompt) | `list[dict]` con `{severidad, categoria, titulo, detalle, datos}` |
| JSON de vulnerabilidades | Dev B (`get_vulnerability_analysis`) | Dev C (`parse_vulnerability`) | `str` JSON crudo |
| Resultado parseado | Dev C (`parse_vulnerability`) | Dev A (`render_vulnerabilidades`) | `dict` con `{resumen_ejecutivo, riesgos_cuantificables, riesgos_contextuales, veredicto}` |

**Regla:** Dev A puede empezar `render_vulnerabilidades()` en paralelo usando `tests/mock_vulnerabilidad.json` (Dev B) y una implementación stub de `analizar_vulnerabilidades()` que devuelva una lista fija de alertas de prueba.

---

## Orden de desarrollo sugerido

1. **Dev C empieza primero** — escribe `vulnerability_analyzer.py` con las 12 reglas; es independiente de la IA y permite a Dev A tener alertas reales para probar el render
2. **Dev B en paralelo** — crea `mock_vulnerabilidad.json` primero para desbloquear a Dev A, luego implementa `vulnerability_client.py`
3. **Dev A en paralelo con Dev B** — implementa `render_vulnerabilidades()` usando el mock, y añade el botón + lógica de congelado en `app.py`
4. **Dev C cierra** — implementa `vulnerability_parser.py` una vez que Dev B tiene el schema del JSON definitivo en el mock
5. **Integración final** — Dev A conecta la llamada real sustituyendo el mock, igual que en Fases 1 y 2
