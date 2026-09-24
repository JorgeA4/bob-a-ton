# Plan Dev C — Fase 2: scenario_parser

## Resumen

Implementar `core/scenario_parser.py` con la función `parse_scenario(json_str: str) -> dict`.
Esta función es el único entregable de Dev C en fase 2: convierte el JSON crudo devuelto por
`ai.scenario_client.get_scenario()` en un dict limpio, validado y con tipos coercionados,
listo para que Dev A lo consuma en `ui/scenario_components.py`.

**Archivo propio:** `core/scenario_parser.py` (archivo nuevo — no modificar nada de fase 1)

**Contrato de entrada:** `str` JSON crudo de `ai.scenario_client.get_scenario()`
**Contrato de salida:** `dict` con claves validadas y valores numéricos como `float`

**Patrón a seguir:** `core/parser.py` de fase 1 — misma estructura, mismas convenciones.

---

## Estructura del JSON de entrada

```
{
  "ubicacion": str,
  "giro": str,
  "inversion_inicial": {
    "renta_deposito": número,
    "adecuaciones": número,
    "equipo": número,
    "inventario_inicial": número,
    "otros": número
  },
  "costos_fijos_mensuales": {
    "renta": número,
    "nomina": número,
    "servicios": número,
    "otros": número
  },
  "proyeccion_ingresos": {
    "clientes_dia_estimado": número,
    "ticket_promedio": número,
    "dias_operacion_mes": número
  },
  "supuestos": str
}
```

---

## Sub-tarea 1 — Implementar `parse_scenario()` en `core/scenario_parser.py`

**Intent**
Crear el único archivo de Dev C en fase 2. La función valida la estructura del JSON de Gemini
en tres niveles (raíz → sección → subclave), coerciona todos los numéricos a `float`,
ignora campos desconocidos, y lanza `ValueError` descriptivo ante cualquier problema.

**Expected Outcomes**
- `core/scenario_parser.py` existe y es importable.
- `parse_scenario(json_str)` devuelve un `dict` con exactamente estas claves en la raíz:
  `ubicacion`, `giro`, `inversion_inicial`, `costos_fijos_mensuales`, `proyeccion_ingresos`, `supuestos`.
- Cada subsección contiene solo sus claves conocidas, con valores `float` coercionados.
- `ubicacion`, `giro` y `supuestos` se devuelven como `str`.
- JSON inválido → `ValueError` con el error de `json.JSONDecodeError`.
- Clave raíz faltante → `ValueError` con lista de claves faltantes.
- Subclave faltante dentro de una sección → `ValueError` indicando la sección y la clave.
- Claves desconocidas en cualquier nivel → ignoradas silenciosamente.

**Todo List**
- [ ] Crear `core/scenario_parser.py`
- [ ] Definir constantes de claves requeridas por sección (igual que en `parser.py`)
- [ ] Implementar helper `_validar_claves(d, claves_requeridas, contexto)` — puede reutilizarse copiando el patrón de `parser.py`
- [ ] Implementar `parse_scenario(json_str: str) -> dict`:
  - `json.loads()` dentro de `try/except json.JSONDecodeError`
  - Verificar que la raíz sea un `dict`
  - Validar las 6 claves raíz
  - Para cada una de las 3 secciones numéricas: verificar que sea `dict`, validar subclaves, coercionar cada valor a `float`
  - Devolver dict construido explícitamente con solo las claves conocidas

**Relevant Context**
- Esquema JSON de referencia: `fases_plans/PLANNING_fase2.md` — sección "Esquema JSON que debe devolver Gemini"
- Patrón de validación y coerción a seguir: `core/parser.py` (función `_validar_claves` y estructura general)
- Dev A accede al resultado con: `escenario["inversion_inicial"]["renta_deposito"]`, etc.
- No importar nada de `core/models.py` — no se necesita dataclass para este parser

**Status:** `[x] done`

---

## Contratos que Dev C NO debe cruzar

- `core/scenario_parser.py` no llama a Gemini ni a ningún cliente de red.
- No modificar `core/models.py`, `core/parser.py` ni ningún archivo de fase 1.
- La función devuelve `dict`, no un dataclass (consistente con `parse_response` de fase 1).
