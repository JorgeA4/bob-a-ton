"""
ai/gemini_client.py — Fase 1: análisis de ubicaciones via Groq.

Nombre histórico mantenido para no romper imports en app.py.
El proveedor de IA cambió de Google Gemini a Groq (llama-3.3-70b-versatile).

Contrato: get_locations() devuelve el JSON CRUDO como string.
El parseo es responsabilidad exclusiva de core.parser.parse_response().
"""

import json

from ai._client import get_client, MODEL, clean_json
from ai.prompt_builder import build_prompt


def _call_api(client, prompt: str) -> str:
    """Realiza una llamada a la API y devuelve el JSON limpio como string."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return clean_json(response.choices[0].message.content)


def get_locations(giro: str, capital: float, ciudad: str, zona_preferida: str = "") -> str:
    """
    Llama a la API de Groq y devuelve el JSON crudo como string.
    Reintenta una vez si la primera respuesta no es JSON válido.
    No parsea la respuesta — eso es responsabilidad de core.parser.

    Args:
        giro: Tipo o rubro del negocio (ej. "Cafetería")
        capital: Capital inicial en MXN (ej. 120000)
        ciudad: Ciudad donde se abrirá el negocio (ej. "Guadalajara")
        zona_preferida: Zona o colonia específica que el usuario quiere evaluar (opcional).

    Returns:
        String con el JSON crudo devuelto por Groq.

    Raises:
        EnvironmentError: Si no se encuentra GROQ_API_KEY en el entorno.
        RuntimeError: Si la llamada a la API falla por red, cuota u otro error.
        ValueError: Si ambos intentos producen una respuesta que no es JSON válido.
    """
    client = get_client()
    prompt = build_prompt(giro, capital, ciudad, zona_preferida)

    # Intento 1
    try:
        raw = _call_api(client, prompt)
    except Exception as e:
        raise RuntimeError(
            f"Error al llamar a la API de Groq (ubicaciones): {e}. "
            "Verifica tu conexión a internet o el estado de tu cuota."
        ) from e

    try:
        json.loads(raw)
        return raw  # JSON válido — devolver directamente
    except json.JSONDecodeError:
        pass  # Continuar con reintento

    # Intento 2 — misma llamada, el modelo puede variar la respuesta
    try:
        raw = _call_api(client, prompt)
    except Exception as e:
        raise RuntimeError(
            f"Error al llamar a la API de Groq (ubicaciones, reintento): {e}. "
            "Verifica tu conexión a internet o el estado de tu cuota."
        ) from e

    try:
        json.loads(raw)
        return raw  # JSON válido en el segundo intento
    except json.JSONDecodeError as e:
        raise ValueError(f"La respuesta de la IA no es JSON válido: {e}") from e
