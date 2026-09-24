"""
ai/scenario_client.py
Fase 2 — Genera el escenario financiero + FODA para una ubicación elegida.

Contrato: get_scenario() devuelve el JSON CRUDO como string.
El parseo es responsabilidad exclusiva de core.scenario_parser.parse_scenario().
"""

import google.generativeai as genai

# Reutiliza la inicialización del cliente ya realizada por gemini_client.
# No carga .env ni configura la API key aquí; eso lo hace gemini_client al importarse.
# Si el usuario llama a get_scenario() sin haber llamado a get_locations() antes,
# genai podría no estar configurado — por eso llamamos a _ensure_configured().
from pathlib import Path
import os
from dotenv import load_dotenv


def _ensure_configured() -> None:
    """
    Garantiza que genai esté configurado con la API key antes de usarlo.
    Idempotente: si ya está configurado, no hace nada costoso (load_dotenv es barato).
    """
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "No se encontró GEMINI_API_KEY. "
            "Asegúrate de tener un archivo .env con GEMINI_API_KEY=tu_clave."
        )
    genai.configure(api_key=api_key)


def _build_scenario_prompt(giro: str, capital: float, ciudad: str, ubicacion: str) -> str:
    """
    Construye el prompt para que Gemini devuelva el escenario financiero + FODA.
    El formato de respuesta sigue el contrato de fase2/AI_INSTRUCTIONS_ESCENARIO.md.
    """
    capital_alerta = (
        "IMPORTANTE: el capital es menor a 80 000 MXN — ajusta los estimados "
        "para ser muy conservadores y refleja esa restricción en costos y márgenes."
        if capital < 80_000
        else ""
    )

    return f"""Eres un consultor financiero experto en apertura de pequeños negocios en México.
Tu tarea es generar un escenario financiero realista y un análisis FODA para el siguiente negocio.

Datos del negocio:
- Giro: {giro}
- Capital inicial disponible: {capital} MXN
- Ciudad: {ciudad}
- Ubicación elegida: {ubicacion}
{capital_alerta}

Instrucciones:
1. Estima ingresos, costos y métricas de rentabilidad para el PRIMER AÑO de operación en esa ubicación.
2. Todos los valores monetarios en MXN/mes, como números float sin símbolos de moneda.
3. Calcula utilidad_neta_mes = ingresos_estimados_mes - costos_fijos_mes - costos_variables_mes.
4. Calcula meses_recuperacion_capital = capital / utilidad_neta_mes (null si utilidad <= 0).
5. Calcula punto_equilibrio_unidades = costos_fijos_mes / (precio_unitario_promedio - costo_variable_unitario).
6. Desglosa costos_fijos_mes en desglose_fijos: renta + nomina + servicios + otros_fijos (deben sumar costos_fijos_mes).
7. Desglosa costos_variables_mes en desglose_variables: insumos + comisiones + empaque + otros_variables (deben sumar costos_variables_mes).
8. El FODA debe ser específico para el giro Y la ubicación — no genérico.
9. Responde ÚNICA Y EXCLUSIVAMENTE con el JSON. Sin bloques markdown, sin texto antes, sin texto después.

Estructura JSON exacta (copia esta estructura, reemplaza los valores):
{{
  "giro": "{giro}",
  "capital": {capital},
  "ciudad": "{ciudad}",
  "ubicacion": "{ubicacion}",
  "ingresos_estimados_mes": 0.0,
  "costos_fijos_mes": 0.0,
  "desglose_fijos": {{
    "renta": 0.0,
    "nomina": 0.0,
    "servicios": 0.0,
    "otros_fijos": 0.0
  }},
  "costos_variables_mes": 0.0,
  "desglose_variables": {{
    "insumos": 0.0,
    "comisiones": 0.0,
    "empaque": 0.0,
    "otros_variables": 0.0
  }},
  "utilidad_neta_mes": 0.0,
  "punto_equilibrio_unidades": 0.0,
  "meses_recuperacion_capital": 0.0,
  "precio_unitario_promedio": 0.0,
  "costo_variable_unitario": 0.0,
  "foda": {{
    "fortalezas": ["fortaleza 1", "fortaleza 2", "fortaleza 3"],
    "oportunidades": ["oportunidad 1", "oportunidad 2", "oportunidad 3"],
    "debilidades": ["debilidad 1", "debilidad 2", "debilidad 3"],
    "amenazas": ["amenaza 1", "amenaza 2", "amenaza 3"]
  }}
}}

Reglas de calidad:
- Los valores deben ser realistas para {giro} en {ubicacion}, {ciudad}.
- Los valores de desglose_fijos deben sumar exactamente costos_fijos_mes.
- Los valores de desglose_variables deben sumar exactamente costos_variables_mes.
- Incluye 3 o 4 elementos en cada lista del FODA.
- JSON válido siempre: sin comas finales, sin comentarios, sin texto fuera del JSON.
"""


def get_scenario(giro: str, capital: float, ciudad: str, ubicacion: str) -> str:
    """
    Llama a la API de Gemini y devuelve el JSON crudo del escenario financiero.
    No parsea la respuesta — eso es responsabilidad de core.scenario_parser.

    Args:
        giro: Tipo o rubro del negocio (ej. "Cafetería").
        capital: Capital inicial en MXN.
        ciudad: Ciudad donde se abrirá el negocio.
        ubicacion: Nombre de la ubicación/colonia elegida por el usuario.

    Returns:
        String con el JSON crudo devuelto por Gemini.

    Raises:
        EnvironmentError: Si no se encuentra la GEMINI_API_KEY en el entorno.
        RuntimeError: Si la llamada a la API falla por red, cuota u otro error.
    """
    _ensure_configured()

    model = genai.GenerativeModel(
        "gemini-3.6-flash",
        generation_config={"response_mime_type": "application/json"},
    )
    prompt = _build_scenario_prompt(giro, capital, ciudad, ubicacion)

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        raise RuntimeError(
            f"Error al llamar a la API de Gemini (escenario): {e}. "
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
