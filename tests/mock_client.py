"""
tests/mock_client.py — Respuestas de ejemplo para testing sin llamadas a la IA.

Uso: importar get_mock_locations() y get_mock_scenario() en app.py
y conectarlos al botón de "Modo test". Fácil de quitar: solo eliminar
el bloque del botón en app.py y estos imports.
"""

import json
from pathlib import Path

_DIR = Path(__file__).parent
_FILE_UBICACIONES = _DIR / "mock_ubicaciones.json"
_FILE_ESCENARIO   = _DIR / "mock_escenario.json"


def get_mock_locations() -> str:
    """Devuelve el JSON de ubicaciones de ejemplo como string crudo."""
    return _FILE_UBICACIONES.read_text(encoding="utf-8")


def get_mock_scenario(ubicacion: str | None = None) -> str:
    """
    Devuelve el JSON de escenario de ejemplo como string crudo.
    Si se pasa una ubicacion, sobreescribe el campo 'ubicacion' en el JSON
    para que coincida con la selección del usuario.
    """
    data = json.loads(_FILE_ESCENARIO.read_text(encoding="utf-8"))
    if ubicacion:
        data["ubicacion"] = ubicacion
    return json.dumps(data, ensure_ascii=False)

_FILE_VULNERABILIDAD = _DIR / "mock_vulnerabilidad.json"


def get_mock_vulnerability() -> str:
    """Devuelve el JSON de vulnerabilidades de ejemplo como string crudo."""
    return _FILE_VULNERABILIDAD.read_text(encoding="utf-8")
