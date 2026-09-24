"""
core/scenario_parser.py
Fase 2 — Parsea y valida el JSON crudo devuelto por ai.scenario_client.get_scenario().

Contrato de salida: dict plano con tipos coercionados, listo para ui/components.py.
Fuente de verdad del esquema: fase2/AI_INSTRUCTIONS_ESCENARIO.md
"""

import json

# ──────────────────────────────────────────────────────────────────────────────
# Claves requeridas según fase2/AI_INSTRUCTIONS_ESCENARIO.md
# ──────────────────────────────────────────────────────────────────────────────

_CLAVES_RAIZ_NUMERICAS = {
    "ingresos_estimados_mes",
    "costos_fijos_mes",
    "costos_variables_mes",
    "utilidad_neta_mes",
    "punto_equilibrio_unidades",
    "precio_unitario_promedio",
    "costo_variable_unitario",
}

# meses_recuperacion_capital puede ser null (utilidad <= 0), se trata aparte
_CLAVES_RAIZ_STRING = {"giro", "ciudad", "ubicacion"}
_CLAVES_RAIZ_OBLIGATORIAS = (
    _CLAVES_RAIZ_NUMERICAS
    | _CLAVES_RAIZ_STRING
    | {"capital", "meses_recuperacion_capital", "foda"}
)

_CLAVES_FODA = {"fortalezas", "oportunidades", "debilidades", "amenazas"}


def _validar_claves(d: dict, requeridas: set, contexto: str) -> None:
    """Lanza ValueError si alguna clave requerida no está presente."""
    faltantes = requeridas - d.keys()
    if faltantes:
        raise ValueError(
            f"Faltan campos requeridos en {contexto}: {sorted(faltantes)}"
        )


def _strip_markdown_fences(text: str) -> str:
    """
    Elimina bloques ```json ... ``` o ``` ... ``` que Gemini a veces añade
    pese a las instrucciones del prompt.
    """
    text = text.strip()
    if text.startswith("```"):
        # Elimina la primera línea (```json o ```)
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        # Elimina el cierre ```
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3].rstrip()
    return text


def parse_scenario(json_str: str) -> dict:
    """
    Convierte el JSON crudo de get_scenario() en un dict validado y tipado.

    Args:
        json_str: String JSON crudo tal como lo devuelve get_scenario().

    Returns:
        Dict con todos los campos del contrato, tipos coercionados:
        - Numéricos → float (meses_recuperacion_capital puede ser None)
        - Strings → str
        - foda → dict con listas de str

    Raises:
        ValueError: Si el JSON es inválido o faltan campos requeridos.
    """
    # 1. Defensiva: eliminar markdown fences si Gemini los incluyó
    clean = _strip_markdown_fences(json_str)

    # 2. Parsear JSON
    try:
        data = json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"La respuesta de la IA (escenario) no es JSON válido: {e}"
        ) from e

    if not isinstance(data, dict):
        raise ValueError(
            f"Se esperaba un objeto JSON en la raíz del escenario, "
            f"se recibió: {type(data).__name__}"
        )

    # 3. Validar claves raíz
    _validar_claves(data, _CLAVES_RAIZ_OBLIGATORIAS, "la raíz del escenario")

    # 4. Validar y coercionar campos numéricos obligatorios (no pueden ser None)
    numericos: dict = {}
    for clave in _CLAVES_RAIZ_NUMERICAS:
        valor = data[clave]
        try:
            numericos[clave] = float(valor)
        except (TypeError, ValueError):
            raise ValueError(
                f"El campo '{clave}' debe ser numérico, se recibió: {valor!r}"
            )

    # 5. Coercionar capital
    try:
        capital = float(data["capital"])
    except (TypeError, ValueError):
        raise ValueError(
            f"El campo 'capital' debe ser numérico, se recibió: {data['capital']!r}"
        )

    # 6. meses_recuperacion_capital puede ser null si utilidad <= 0
    mrc_raw = data["meses_recuperacion_capital"]
    if mrc_raw is None:
        meses_recuperacion: float | None = None
    else:
        try:
            meses_recuperacion = float(mrc_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"El campo 'meses_recuperacion_capital' debe ser numérico o null, "
                f"se recibió: {mrc_raw!r}"
            )

    # 7. Coercionar campos string
    strings: dict = {}
    for clave in _CLAVES_RAIZ_STRING:
        strings[clave] = str(data[clave])

    # 8. Validar y coercionar FODA
    foda_raw = data["foda"]
    if not isinstance(foda_raw, dict):
        raise ValueError(
            f"El campo 'foda' debe ser un objeto, se recibió: {type(foda_raw).__name__}"
        )
    _validar_claves(foda_raw, _CLAVES_FODA, "foda")

    foda: dict = {}
    for categoria in _CLAVES_FODA:
        items = foda_raw[categoria]
        if not isinstance(items, list):
            raise ValueError(
                f"foda.{categoria} debe ser una lista, se recibió: {type(items).__name__}"
            )
        # Coercionar cada elemento a string y descartar elementos vacíos
        foda[categoria] = [str(item) for item in items if str(item).strip()]

    # 9. Ensamblar el dict de salida con tipos garantizados
    return {
        "giro": strings["giro"],
        "capital": capital,
        "ciudad": strings["ciudad"],
        "ubicacion": strings["ubicacion"],
        "ingresos_estimados_mes": numericos["ingresos_estimados_mes"],
        "costos_fijos_mes": numericos["costos_fijos_mes"],
        "costos_variables_mes": numericos["costos_variables_mes"],
        "utilidad_neta_mes": numericos["utilidad_neta_mes"],
        "punto_equilibrio_unidades": numericos["punto_equilibrio_unidades"],
        "meses_recuperacion_capital": meses_recuperacion,
        "precio_unitario_promedio": numericos["precio_unitario_promedio"],
        "costo_variable_unitario": numericos["costo_variable_unitario"],
        "foda": foda,
    }
