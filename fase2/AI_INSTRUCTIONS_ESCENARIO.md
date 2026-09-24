# Fase 2 — Contrato JSON del Escenario Financiero

Este archivo es la **única fuente de verdad** para el formato de respuesta de `get_scenario()`.
Todos los módulos (`ai/scenario_client.py`, `core/scenario_parser.py`, `ui/components.py`) deben
ser consistentes con él.

---

## Firma de la función que genera el JSON

```python
get_scenario(giro: str, capital: float, ciudad: str, ubicacion: str) -> str
```

---

## Estructura JSON exacta que Gemini debe devolver

```json
{
  "giro": "string",
  "capital": 100000.0,
  "ciudad": "string",
  "ubicacion": "string",
  "ingresos_estimados_mes": 45000.0,
  "desglose_fijos": [
    {"concepto": "Nombre específico del costo fijo 1", "monto": 8000.0},
    {"concepto": "Nombre específico del costo fijo 2", "monto": 6000.0},
    {"concepto": "Nombre específico del costo fijo 3", "monto": 4000.0}
  ],
  "desglose_variables": [
    {"concepto": "Nombre específico del costo variable 1", "monto": 5000.0},
    {"concepto": "Nombre específico del costo variable 2", "monto": 2500.0},
    {"concepto": "Nombre específico del costo variable 3", "monto": 1500.0}
  ],
  "utilidad_neta_mes": 18000.0,
  "punto_equilibrio_unidades": 120.0,
  "meses_recuperacion_capital": 6.0,
  "precio_unitario_promedio": 150.0,
  "costo_variable_unitario": 60.0,
  "foda": {
    "fortalezas": ["texto 1", "texto 2", "texto 3"],
    "oportunidades": ["texto 1", "texto 2", "texto 3"],
    "debilidades": ["texto 1", "texto 2", "texto 3"],
    "amenazas": ["texto 1", "texto 2", "texto 3"]
  }
}
```

> **Nota**: `costos_fijos_mes` y `costos_variables_mes` **no aparecen en el JSON de Gemini**.
> El parser los calcula sumando los montos de `desglose_fijos` y `desglose_variables` respectivamente,
> eliminando cualquier posibilidad de inconsistencia entre el total y el desglose.

---

## Descripción de cada campo

| Campo | Tipo | Descripción |
|---|---|---|
| `giro` | string | Giro del negocio (echo del input) |
| `capital` | float | Capital inicial en MXN (echo del input) |
| `ciudad` | string | Ciudad (echo del input) |
| `ubicacion` | string | Nombre de la ubicación elegida (echo del input) |
| `ingresos_estimados_mes` | float | Ingresos brutos estimados en el primer año de operación normal (MXN/mes) |
| `desglose_fijos` | list | Lista de 3–6 objetos `{concepto, monto}` con costos fijos **específicos al giro** |
| `desglose_fijos[].concepto` | string | Nombre descriptivo del costo fijo (ej. "Renta del local", "Nómina barista + cajero") |
| `desglose_fijos[].monto` | float | Monto mensual del costo fijo en MXN |
| `desglose_variables` | list | Lista de 3–6 objetos `{concepto, monto}` con costos variables **específicos al giro** |
| `desglose_variables[].concepto` | string | Nombre descriptivo del costo variable (ej. "Granos de café", "Comisión app delivery") |
| `desglose_variables[].monto` | float | Monto mensual del costo variable en MXN |
| `utilidad_neta_mes` | float | `ingresos_estimados_mes − sum(desglose_fijos) − sum(desglose_variables)` |
| `punto_equilibrio_unidades` | float | `sum(desglose_fijos) / (precio_unitario_promedio − costo_variable_unitario)` |
| `meses_recuperacion_capital` | float\|null | `capital / utilidad_neta_mes` (null si utilidad ≤ 0) |
| `precio_unitario_promedio` | float | Precio de venta promedio por unidad/servicio (MXN) |
| `costo_variable_unitario` | float | Costo variable por unidad/servicio (MXN) |
| `foda.fortalezas` | list[string] | 3–4 fortalezas internas del negocio en esa ubicación |
| `foda.oportunidades` | list[string] | 3–4 oportunidades del entorno |
| `foda.debilidades` | list[string] | 3–4 debilidades o riesgos internos |
| `foda.amenazas` | list[string] | 3–4 amenazas externas |

---

## Reglas de consistencia

- `utilidad_neta_mes` = `ingresos_estimados_mes − sum(desglose_fijos[].monto) − sum(desglose_variables[].monto)`.
- `meses_recuperacion_capital` = `capital / utilidad_neta_mes` (si utilidad ≤ 0, devolver `null`).
- `punto_equilibrio_unidades` = `sum(desglose_fijos[].monto) / (precio_unitario_promedio − costo_variable_unitario)`.
- Los conceptos de desglose deben ser **específicos al giro** — no usar términos genéricos como "otros" o "misceláneos".
- Todos los valores monetarios en MXN, sin símbolos de moneda, como `float` puro.
- Responder **solo con JSON bare** — sin bloques ```json```, sin texto previo, sin texto posterior.
- JSON válido siempre: sin comas finales, sin comentarios.
- Los valores deben ser realistas para el giro y ciudad dados.
- Si capital < 80 000 MXN, reflejar esa restricción en costos más conservadores.

---

## Ejemplo de respuesta válida (Cafetería, CDMX, Condesa)

```json
{
  "giro": "Cafetería",
  "capital": 120000.0,
  "ciudad": "CDMX",
  "ubicacion": "Condesa",
  "ingresos_estimados_mes": 52000.0,
  "desglose_fijos": [
    {"concepto": "Renta del local", "monto": 10000.0},
    {"concepto": "Nómina (barista + cajero)", "monto": 7000.0},
    {"concepto": "Servicios (agua, luz, internet)", "monto": 2500.0},
    {"concepto": "Contabilidad y licencia sanitaria", "monto": 1500.0}
  ],
  "desglose_variables": [
    {"concepto": "Granos de café e insumos de barra", "monto": 7000.0},
    {"concepto": "Empaque y desechables", "monto": 1500.0},
    {"concepto": "Comisión plataforma delivery", "monto": 1000.0},
    {"concepto": "Reposición de alimentos y snacks", "monto": 1500.0}
  ],
  "utilidad_neta_mes": 20000.0,
  "punto_equilibrio_unidades": 369.0,
  "meses_recuperacion_capital": 6.0,
  "precio_unitario_promedio": 90.0,
  "costo_variable_unitario": 38.0,
  "foda": {
    "fortalezas": [
      "Alta densidad de público joven con poder adquisitivo",
      "Zona con cultura de café consolidada",
      "Buena conectividad peatonal y ciclista"
    ],
    "oportunidades": [
      "Crecimiento del consumo de specialty coffee",
      "Posibilidad de alianzas con coworkings cercanos",
      "Turismo gastronómico activo en la zona"
    ],
    "debilidades": [
      "Renta elevada que presiona el margen",
      "Alta rotación de locales en la zona",
      "Capital inicial ajustado para un local premium"
    ],
    "amenazas": [
      "Competencia de cadenas internacionales ya instaladas",
      "Sensibilidad al precio en época de inflación",
      "Dependencia de temporada turística"
    ]
  }
}
```
