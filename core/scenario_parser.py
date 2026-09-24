import json

# ──────────────────────────────────────────────────────────────────────────────
# Claves requeridas por nivel del JSON
# ──────────────────────────────────────────────────────────────────────────────

_CLAVES_RAIZ = {
    "ubicacion",
    "giro",
    "inversion_inicial",
    "costos_fijos_mensuales",
    "proyeccion_ingresos",
    "supuestos",
}

_CLAVES_INVERSION = {
    "renta_deposito",
    "adecuaciones",
    "equipo",
    "inventario_inicial",
    "otros",
}

_CLAVES_COSTOS_FIJOS = {
    "renta",
    "nomina",
    "servicios",
    "otros",
}

_CLAVES_PROYECCION = {
    "clientes_dia_estimado",
    "ticket_promedio",
    "dias_operacion_mes",
}


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


def _coercionar_seccion(raw: dict, claves: set, contexto: str) -> dict:
    """
    Valida que `raw` sea un dict con las claves requeridas y devuelve
    un nuevo dict con solo esas claves, coercionando cada valor a float.
    Claves desconocidas se ignoran silenciosamente.
    """
    if not isinstance(raw, dict):
        raise ValueError(
            f"'{contexto}' debe ser un objeto JSON, se recibió: {type(raw).__name__}"
        )
    _validar_claves(raw, claves, contexto)
    return {clave: float(raw[clave]) for clave in claves}


# ──────────────────────────────────────────────────────────────────────────────
# Función pública
# ──────────────────────────────────────────────────────────────────────────────

def parse_scenario(json_str: str) -> dict:
    """
    Convierte el JSON crudo devuelto por get_scenario() en un dict validado
    y con tipos coercionados, listo para consumir en ui/scenario_components.py.

    Args:
        json_str: String JSON crudo tal como lo devuelve
                  ai.scenario_client.get_scenario().

    Returns:
        dict con claves:
            ubicacion (str), giro (str), supuestos (str),
            inversion_inicial (dict[str, float]),
            costos_fijos_mensuales (dict[str, float]),
            proyeccion_ingresos (dict[str, float])

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

    # 2. Validar claves raíz
    _validar_claves(data, _CLAVES_RAIZ, "la raíz del JSON")

    # 3. Validar y coercionar cada sección numérica; ignorar campos extra
    inversion = _coercionar_seccion(
        data["inversion_inicial"], _CLAVES_INVERSION, "inversion_inicial"
    )
    costos = _coercionar_seccion(
        data["costos_fijos_mensuales"], _CLAVES_COSTOS_FIJOS, "costos_fijos_mensuales"
    )
    proyeccion = _coercionar_seccion(
        data["proyeccion_ingresos"], _CLAVES_PROYECCION, "proyeccion_ingresos"
    )

    # 4. Construir y devolver el dict con solo las claves conocidas
    return {
        "ubicacion": str(data["ubicacion"]),
        "giro": str(data["giro"]),
        "inversion_inicial": inversion,
        "costos_fijos_mensuales": costos,
        "proyeccion_ingresos": proyeccion,
        "supuestos": str(data["supuestos"]),
    }
