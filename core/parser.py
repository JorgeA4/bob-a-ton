import json
from typing import List

from core.models import Criterio, Ubicacion, RespuestaIA

# Claves requeridas en cada nivel del JSON
_CLAVES_RAIZ = {"ciudad", "giro", "capital", "ubicaciones"}
_CLAVES_UBICACION = {"id", "nombre", "descripcion_breve", "criterios", "puntaje_total", "recomendacion_ia"}
_CLAVES_CRITERIO = {"puntaje", "nota"}

# Criterios donde el puntaje representa bondad pero el nivel debe reflejar
# la magnitud real del coste: puntaje alto (accesible) → nivel "bajo" (renta baja).
CRITERIOS_INVERTIDOS = {"costo_renta", "compatibilidad_capital"}


def _nivel_from_puntaje(puntaje: float, clave: str) -> str:
    """
    Deriva el nivel cualitativo a partir del puntaje numérico (1–10).

    Criterios normales: puntaje alto → nivel alto (ej. flujo_peatonal 9 → "muy alto").
    Criterios invertidos (costo_renta, compatibilidad_capital): el puntaje mide bondad
    pero el nivel describe la magnitud real del costo, invertida:
        puntaje 9 (renta accesible)  → nivel "bajo"    (renta baja)
        puntaje 2 (renta cara)       → nivel "muy alto" (renta muy alta)
    El color en la UI se asigna por bondad (puntaje), no por nivel literal.
    """
    if clave in CRITERIOS_INVERTIDOS:
        # Invertir: puntaje alto → magnitud baja
        if puntaje >= 8:
            return "bajo"
        elif puntaje >= 6:
            return "medio"
        elif puntaje >= 4:
            return "alto"
        else:
            return "muy alto"
    else:
        if puntaje >= 8:
            return "muy alto"
        elif puntaje >= 6:
            return "alto"
        elif puntaje >= 4:
            return "medio"
        else:
            return "bajo"

# Los 9 criterios que deben estar presentes en cada ubicación
_CRITERIOS_ESPERADOS = {
    "costo_renta",
    "flujo_peatonal",
    "accesibilidad_transporte",
    "nivel_competencia",
    "afinidad_con_giro",
    "seguridad_zona",
    "potencial_crecimiento",
    "visibilidad_local",
    "compatibilidad_capital",
}


def _validar_claves(d: dict, claves_requeridas: set, contexto: str) -> None:
    """Lanza ValueError si faltan claves requeridas en el diccionario."""
    faltantes = claves_requeridas - d.keys()
    if faltantes:
        raise ValueError(
            f"Faltan campos requeridos en {contexto}: {sorted(faltantes)}"
        )


def parse_response(json_str: str) -> List[dict]:
    """
    Convierte el JSON crudo devuelto por get_locations() en una lista de dicts
    de ubicaciones validados y con tipos coercionados.

    Args:
        json_str: String JSON crudo tal como lo devuelve ai.gemini_client.get_locations().

    Returns:
        Lista de dicts de ubicaciones, lista para consumir por ui/components.py.

    Raises:
        ValueError: Si json_str no es JSON válido o faltan campos requeridos.
    """
    # 1. Parsear el JSON
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

    ubicaciones_raw = data["ubicaciones"]
    if not isinstance(ubicaciones_raw, list):
        raise ValueError(
            f"El campo 'ubicaciones' debe ser una lista, se recibió: {type(ubicaciones_raw).__name__}"
        )

    resultado: List[dict] = []

    for idx, u in enumerate(ubicaciones_raw):
        contexto_u = f"ubicaciones[{idx}]"

        if not isinstance(u, dict):
            raise ValueError(f"{contexto_u} debe ser un objeto, se recibió: {type(u).__name__}")

        # 3. Validar claves de ubicación
        _validar_claves(u, _CLAVES_UBICACION, contexto_u)

        criterios_raw = u["criterios"]
        if not isinstance(criterios_raw, dict):
            raise ValueError(
                f"{contexto_u}.criterios debe ser un objeto, se recibió: {type(criterios_raw).__name__}"
            )

        # 4. Validar que estén los 9 criterios esperados
        _validar_claves(criterios_raw, _CRITERIOS_ESPERADOS, f"{contexto_u}.criterios")

        # 5. Validar y coercionar cada criterio; ignorar claves desconocidas
        criterios_validados: dict = {}
        for clave in _CRITERIOS_ESPERADOS:
            c = criterios_raw[clave]
            if not isinstance(c, dict):
                raise ValueError(
                    f"{contexto_u}.criterios.{clave} debe ser un objeto, se recibió: {type(c).__name__}"
                )
            _validar_claves(c, _CLAVES_CRITERIO, f"{contexto_u}.criterios.{clave}")
            puntaje = float(c["puntaje"])
            criterios_validados[clave] = {
                "nivel": _nivel_from_puntaje(puntaje, clave),
                "puntaje": puntaje,
                "nota": str(c["nota"]),
            }

        # 6. Construir el dict de ubicación con tipos coercionados; campos extra se ignoran
        ubicacion_dict = {
            "id": int(u["id"]),
            "nombre": str(u["nombre"]),
            "descripcion_breve": str(u["descripcion_breve"]),
            "criterios": criterios_validados,
            "puntaje_total": float(u["puntaje_total"]),
            "recomendacion_ia": str(u["recomendacion_ia"]),
        }
        resultado.append(ubicacion_dict)

    return resultado
