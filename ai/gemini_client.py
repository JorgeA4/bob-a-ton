import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
from ai.prompt_builder import build_prompt


def get_locations(giro: str, capital: float, ciudad: str, zona_preferida: str = "") -> str:
    """
    Llama a la API de Gemini y devuelve el JSON crudo como string.
    No parsea la respuesta — eso es responsabilidad de core.parser.

    Args:
        giro: Tipo o rubro del negocio (ej. "Cafetería")
        capital: Capital inicial en MXN (ej. 120000)
        ciudad: Ciudad donde se abrirá el negocio (ej. "Guadalajara")
        zona_preferida: Zona o colonia específica que el usuario quiere evaluar (opcional).

    Returns:
        String con el JSON crudo devuelto por Gemini.

    Raises:
        EnvironmentError: Si no se encuentra la GEMINI_API_KEY en el entorno.
        RuntimeError: Si la llamada a la API falla por red, cuota u otro error.
    """
    # Busca el .env en la raíz del proyecto (un nivel arriba de ai/)
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "No se encontró GEMINI_API_KEY. "
            "Asegúrate de tener un archivo .env con GEMINI_API_KEY=tu_clave."
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-3.6-flash",
        generation_config={"response_mime_type": "application/json"},
    )

    prompt = build_prompt(giro, capital, ciudad, zona_preferida)

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        raise RuntimeError(
            f"Error al llamar a la API de Gemini: {e}. "
            "Verifica tu conexión a internet o el estado de tu cuota."
        ) from e

    return _clean_json(response.text)


def _clean_json(text: str) -> str:
    """
    Extrae el JSON de la respuesta aunque Gemini lo envuelva en markdown.
    Estrategia: localizar el primer '{' y el último '}' del texto y devolver
    solo ese fragmento — funciona tanto para JSON limpio como para respuestas
    envueltas en bloques ```json ... ```.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text.strip()
