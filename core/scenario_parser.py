import json

# ──────────────────────────────────────────────────────────────────────────────
# Claves requeridas según el esquema real de ai/scenario_client.py
# ──────────────────────────────────────────────────────────────────────────────

# Claves raíz obligatorias cuyo valor debe ser numérico (float)
_CLAVES_NUMERICAS = {
    "capital",
    "ingresos_estimados_mes",
    "costos_fijos_mes",
    "costos_variables_mes",
    "utilidad_neta_mes",
    "punto_equilibrio_unidades",
    "precio_unitario_promedio",
    "costo_variable_unitario",
}

# Claves raíz obligatorias de tipo string
_CLAVES_STRING = {"giro", "ciudad", "ubicacion"}

# meses_recuperacion_capital es obligatoria pero puede ser null (utilidad <= 0)
_CLAVE_MRC = "meses_recuperacion_capital"

# Clave del FODA y sus cuatro subcategorías
_CLAVE_FODA = "foda"
_CLAVES_FODA = {"fortalezas", "oportunidades", "debilidades", "amenazas"}

# Todas las claves raíz requeridas
_CLAVES_RAIZ = _CLAVES_NUMERICAS | _CLAVES_STRING | {_CLAVE_MRC, _CLAVE_FODA}


# ──────────────────────────────────────────────────────────────────────────────
# Helper interno
# ──────────────────────────────────────────────────────────────────────────────

def _validar_claves(d: dict, claves_requeridas: set, contexto: str) -> None:
    """Lanza ValueError si faltan claves requeridas en el diccionario."""
    faltantes = claves_requeridas - d.keys()
    if faltantes:
        raise ValueError(
            f"Faltan campos requeridos en {contexto}: {sorted(faltantes)}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Función pública
# ──────────────────────────────────────────────────────────────────────────────

def parse_scenario(json_str: str) -> dict:
    """
    Convierte el JSON crudo devuelto por get_scenario() en un dict validado
    y con tipos coercionados, listo para consumir en ui/components.py.

    El esquema esperado (plano) es el que devuelve ai/scenario_client.py:
        giro, ciudad, ubicacion, capital,
        ingresos_estimados_mes, costos_fijos_mes, costos_variables_mes,
        utilidad_neta_mes, punto_equilibrio_unidades,
        meses_recuperacion_capital (float o null),
        precio_unitario_promedio, costo_variable_unitario,
        foda: {fortalezas, oportunidades, debilidades, amenazas}

    Args:
        json_str: String JSON crudo tal como lo devuelve
                  ai.scenario_client.get_scenario().

    Returns:
        dict con todos los campos del esquema, tipos coercionados:
        - Numéricos → float  (meses_recuperacion_capital puede ser None)
        - Strings → str
        - foda → dict con listas de str (elementos vacíos descartados)

    Raises:
        ValueError: Si json_str no es JSON válido o faltan campos requeridos
                    en cualquier nivel.
    """
    # 1. Parsear el string JSON
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"La respuesta de la IA no es JSON válido: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(
            f"Se esperaba un objeto JSON en la raíz, se recibió: {type(data).__name__}"
        )

    # 2. Validar que estén todas las claves raíz requeridas
    _validar_claves(data, _CLAVES_RAIZ, "la raíz del JSON")

    # 3. Coercionar claves numéricas obligatorias
    numericos: dict = {}
    for clave in _CLAVES_NUMERICAS:
        try:
            numericos[clave] = float(data[clave])
        except (TypeError, ValueError):
            raise ValueError(
                f"El campo '{clave}' debe ser numérico, se recibió: {data[clave]!r}"
            )

    # 4. meses_recuperacion_capital: puede ser null/None (utilidad <= 0)
    mrc_raw = data[_CLAVE_MRC]
    if mrc_raw is None:
        meses_recuperacion = None
    else:
        try:
            meses_recuperacion = float(mrc_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"El campo '{_CLAVE_MRC}' debe ser numérico o null, "
                f"se recibió: {mrc_raw!r}"
            )

    # 5. Coercionar claves string
    strings = {clave: str(data[clave]) for clave in _CLAVES_STRING}

    # 6. Validar y coercionar FODA
    foda_raw = data[_CLAVE_FODA]
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
                f"foda.{categoria} debe ser una lista, "
                f"se recibió: {type(items).__name__}"
            )
        # Coercionar cada elemento a str; descartar elementos vacíos
        foda[categoria] = [str(item) for item in items if str(item).strip()]

    # 7. Ensamblar el dict de salida con solo las claves conocidas
    return {
        **strings,
        **numericos,
        _CLAVE_MRC: meses_recuperacion,
        _CLAVE_FODA: foda,
    }
