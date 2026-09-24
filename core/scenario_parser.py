import json

# ──────────────────────────────────────────────────────────────────────────────
# Claves requeridas según el esquema real de ai/scenario_client.py
# ──────────────────────────────────────────────────────────────────────────────

# Claves raíz obligatorias cuyo valor debe ser numérico (float).
# costos_fijos_mes y costos_variables_mes se calculan aquí sumando los desgloses
# — Gemini ya no los devuelve directamente.
_CLAVES_NUMERICAS = {
    "capital",
    "ingresos_estimados_mes",
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

# Desgloses: listas de objetos {concepto, monto} — obligatorios
_CLAVE_DF = "desglose_fijos"
_CLAVE_DV = "desglose_variables"

# Madurez: objeto con dos claves numéricas
_CLAVE_MADUREZ = "madurez"
_CLAVES_MADUREZ = {"meses_hasta_madurez", "porcentaje_ventas_mes1"}

# Todas las claves raíz requeridas
_CLAVES_RAIZ = _CLAVES_NUMERICAS | _CLAVES_STRING | {_CLAVE_MRC, _CLAVE_FODA, _CLAVE_DF, _CLAVE_DV, _CLAVE_MADUREZ}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────────────────────

def _validar_claves(d: dict, claves_requeridas: set, contexto: str) -> None:
    """Lanza ValueError si faltan claves requeridas en el diccionario."""
    faltantes = claves_requeridas - d.keys()
    if faltantes:
        raise ValueError(
            f"Faltan campos requeridos en {contexto}: {sorted(faltantes)}"
        )


def _parsear_desglose(raw: object, nombre: str) -> list[dict]:
    """
    Parsea y valida una lista de items {concepto, monto}.

    Args:
        raw: valor crudo del campo (debe ser una lista de dicts).
        nombre: nombre del campo para mensajes de error.

    Returns:
        Lista de dicts con claves 'concepto' (str) y 'monto' (float),
        sin items con monto 0 o concepto vacío.

    Raises:
        ValueError: si el formato es incorrecto o la lista está vacía.
    """
    if not isinstance(raw, list):
        raise ValueError(
            f"'{nombre}' debe ser una lista, se recibió: {type(raw).__name__}"
        )
    if len(raw) == 0:
        raise ValueError(f"'{nombre}' no puede ser una lista vacía")

    result = []
    for i, item in enumerate(raw):
        ctx = f"{nombre}[{i}]"
        if not isinstance(item, dict):
            raise ValueError(f"{ctx} debe ser un objeto, se recibió: {type(item).__name__}")
        if "concepto" not in item:
            raise ValueError(f"Falta 'concepto' en {ctx}")
        if "monto" not in item:
            raise ValueError(f"Falta 'monto' en {ctx}")
        concepto = str(item["concepto"]).strip()
        if not concepto:
            raise ValueError(f"'concepto' está vacío en {ctx}")
        try:
            monto = float(item["monto"])
        except (TypeError, ValueError):
            raise ValueError(
                f"'monto' en {ctx} debe ser numérico, se recibió: {item['monto']!r}"
            )
        result.append({"concepto": concepto, "monto": monto})

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Función pública
# ──────────────────────────────────────────────────────────────────────────────

def parse_scenario(json_str: str) -> dict:
    """
    Convierte el JSON crudo devuelto por get_scenario() en un dict validado
    y con tipos coercionados, listo para consumir en ui/components.py.

    Esquema de entrada (Gemini):
        giro, capital, ciudad, ubicacion, ingresos_estimados_mes,
        desglose_fijos: [{concepto, monto}, ...],
        desglose_variables: [{concepto, monto}, ...],
        utilidad_neta_mes, punto_equilibrio_unidades,
        meses_recuperacion_capital (float o null),
        precio_unitario_promedio, costo_variable_unitario,
        foda: {fortalezas, oportunidades, debilidades, amenazas}

    costos_fijos_mes y costos_variables_mes NO vienen de Gemini — se calculan
    aquí sumando los items del desglose correspondiente.

    Args:
        json_str: String JSON crudo tal como lo devuelve
                  ai.scenario_client.get_scenario().

    Returns:
        dict con todos los campos del esquema, tipos coercionados:
        - Numéricos → float  (meses_recuperacion_capital puede ser None)
        - Strings → str
        - costos_fijos_mes / costos_variables_mes → float calculado
        - desglose_fijos / desglose_variables → list[dict] con concepto+monto
        - foda → dict con listas de str

    Raises:
        ValueError: Si json_str no es JSON válido o faltan campos requeridos.
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

    # 6. Parsear desgloses libres y calcular totales
    desglose_fijos    = _parsear_desglose(data[_CLAVE_DF], _CLAVE_DF)
    desglose_variables = _parsear_desglose(data[_CLAVE_DV], _CLAVE_DV)

    costos_fijos_mes    = sum(item["monto"] for item in desglose_fijos)
    costos_variables_mes = sum(item["monto"] for item in desglose_variables)

    # 7. Parsear y validar madurez
    madurez_raw = data[_CLAVE_MADUREZ]
    if not isinstance(madurez_raw, dict):
        raise ValueError(
            f"El campo 'madurez' debe ser un objeto, se recibió: {type(madurez_raw).__name__}"
        )
    _validar_claves(madurez_raw, _CLAVES_MADUREZ, "madurez")
    try:
        meses_hasta_madurez = int(madurez_raw["meses_hasta_madurez"])
    except (TypeError, ValueError):
        raise ValueError(
            f"madurez.meses_hasta_madurez debe ser entero, "
            f"se recibió: {madurez_raw['meses_hasta_madurez']!r}"
        )
    try:
        porcentaje_mes1 = float(madurez_raw["porcentaje_ventas_mes1"])
    except (TypeError, ValueError):
        raise ValueError(
            f"madurez.porcentaje_ventas_mes1 debe ser numérico, "
            f"se recibió: {madurez_raw['porcentaje_ventas_mes1']!r}"
        )
    if not (1 <= meses_hasta_madurez <= 120):
        raise ValueError(
            f"madurez.meses_hasta_madurez debe estar entre 1 y 120, "
            f"se recibió: {meses_hasta_madurez}"
        )
    if not (1.0 <= porcentaje_mes1 <= 100.0):
        raise ValueError(
            f"madurez.porcentaje_ventas_mes1 debe estar entre 1 y 100, "
            f"se recibió: {porcentaje_mes1}"
        )

    # 8. Validar y coercionar FODA
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
        foda[categoria] = [str(item) for item in items if str(item).strip()]

    # 9. Ensamblar el dict de salida
    return {
        **strings,
        **numericos,
        "costos_fijos_mes":     costos_fijos_mes,
        "costos_variables_mes": costos_variables_mes,
        _CLAVE_MRC:             meses_recuperacion,
        _CLAVE_DF:              desglose_fijos,
        _CLAVE_DV:              desglose_variables,
        _CLAVE_MADUREZ: {
            "meses_hasta_madurez":    meses_hasta_madurez,
            "porcentaje_ventas_mes1": porcentaje_mes1,
        },
        _CLAVE_FODA:            foda,
    }
