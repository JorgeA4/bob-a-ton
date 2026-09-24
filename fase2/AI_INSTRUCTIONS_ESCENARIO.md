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
  "costos_fijos_mes": 18000.0,
  "desglose_fijos": {
    "renta": 8000.0,
    "nomina": 6000.0,
    "servicios": 2000.0,
    "otros_fijos": 2000.0
  },
  "costos_variables_mes": 9000.0,
  "desglose_variables": {
    "insumos": 5000.0,
    "comisiones": 1000.0,
    "empaque": 1500.0,
    "otros_variables": 1500.0
  },
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

---

## Descripción de cada campo

| Campo | Tipo | Descripción |
|---|---|---|
| `giro` | string | Giro del negocio (echo del input) |
| `capital` | float | Capital inicial en MXN (echo del input) |
| `ciudad` | string | Ciudad (echo del input) |
| `ubicacion` | string | Nombre de la ubicación elegida (echo del input) |
| `ingresos_estimados_mes` | float | Ingresos brutos estimados en el primer año de operación normal (MXN/mes) |
| `costos_fijos_mes` | float | Total de costos fijos del mes — debe igualar la suma del desglose (MXN/mes) |
| `desglose_fijos.renta` | float | Renta del local (MXN/mes) |
| `desglose_fijos.nomina` | float | Nómina base de empleados fijos (MXN/mes) |
| `desglose_fijos.servicios` | float | Agua, luz, internet, gas, etc. (MXN/mes) |
| `desglose_fijos.otros_fijos` | float | Seguros, mantenimiento, contabilidad y otros fijos (MXN/mes) |
| `costos_variables_mes` | float | Total de costos variables del mes — debe igualar la suma del desglose (MXN/mes) |
| `desglose_variables.insumos` | float | Materia prima e insumos directos proporcionales a ventas (MXN/mes) |
| `desglose_variables.comisiones` | float | Comisiones por venta, plataformas de entrega, etc. (MXN/mes) |
| `desglose_variables.empaque` | float | Empaques, bolsas, desechables proporcionales a ventas (MXN/mes) |
| `desglose_variables.otros_variables` | float | Otros costos que varían con el volumen de ventas (MXN/mes) |
| `utilidad_neta_mes` | float | `ingresos_estimados_mes - costos_fijos_mes - costos_variables_mes` |
| `punto_equilibrio_unidades` | float | Unidades/servicios mínimos para cubrir costos totales al mes |
| `meses_recuperacion_capital` | float | `capital / utilidad_neta_mes` (redondeado a 1 decimal) |
| `precio_unitario_promedio` | float | Precio de venta promedio por unidad/servicio (MXN) |
| `costo_variable_unitario` | float | Costo variable por unidad/servicio (MXN) |
| `foda.fortalezas` | list[string] | 3–4 fortalezas internas del negocio en esa ubicación |
| `foda.oportunidades` | list[string] | 3–4 oportunidades del entorno |
| `foda.debilidades` | list[string] | 3–4 debilidades o riesgos internos |
| `foda.amenazas` | list[string] | 3–4 amenazas externas |

---

## Reglas de consistencia

- `utilidad_neta_mes` debe ser exactamente `ingresos_estimados_mes - costos_fijos_mes - costos_variables_mes`.
- `meses_recuperacion_capital` debe ser `capital / utilidad_neta_mes` (si utilidad ≤ 0, devolver `null`).
- `punto_equilibrio_unidades` = `costos_fijos_mes / (precio_unitario_promedio - costo_variable_unitario)`.
- `desglose_fijos.renta + nomina + servicios + otros_fijos` debe igualar `costos_fijos_mes`.
- `desglose_variables.insumos + comisiones + empaque + otros_variables` debe igualar `costos_variables_mes`.
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
  "costos_fijos_mes": 21000.0,
  "desglose_fijos": {
    "renta": 10000.0,
    "nomina": 7000.0,
    "servicios": 2500.0,
    "otros_fijos": 1500.0
  },
  "costos_variables_mes": 11000.0,
  "desglose_variables": {
    "insumos": 7000.0,
    "comisiones": 1000.0,
    "empaque": 1500.0,
    "otros_variables": 1500.0
  },
  "utilidad_neta_mes": 20000.0,
  "punto_equilibrio_unidades": 233.0,
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
