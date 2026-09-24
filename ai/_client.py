"""
ai/_client.py — Cliente Groq singleton compartido por todos los módulos ai/.

Centraliza la inicialización del cliente y la key para que gemini_client.py,
scenario_client.py y vulnerability_client.py no dupliquen configuración.

Uso:
    from ai._client import get_client, MODEL

    client = get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Modelo activo — cambiar aquí para actualizar los tres clientes a la vez.
MODEL = "openai/gpt-oss-120b"

_client: Groq | None = None


def get_client() -> Groq:
    """
    Devuelve el cliente Groq configurado con la API key.
    Idempotente: carga .env y crea el cliente solo una vez (singleton).

    Raises:
        EnvironmentError: Si no se encuentra GROQ_API_KEY en el entorno.
    """
    global _client
    if _client is not None:
        return _client

    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "No se encontró GROQ_API_KEY. "
            "Asegúrate de tener un archivo .env con GROQ_API_KEY=tu_clave."
        )

    _client = Groq(api_key=api_key)
    return _client


def clean_json(text: str) -> str:
    """
    Extrae el JSON de la respuesta aunque el modelo lo envuelva en markdown.
    Localiza el primer '{' y el último '}' y devuelve solo ese fragmento.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text.strip()
