"""
ai/scenario_client.py — Fase 2: escenario financiero + FODA via Groq.

Contrato: get_scenario() devuelve el JSON CRUDO como string.
El parseo es responsabilidad exclusiva de core.scenario_parser.parse_scenario().
"""

from ai._client import get_client, MODEL, clean_json


def _build_scenario_prompt(giro: str, capital: float, ciudad: str, ubicacion: str) -> str:
    """
    Construye el prompt para que Groq devuelva el escenario financiero + FODA.
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
2. Todos los valores monetarios en MXN/mes (o MXN total para inversion_inicial), como números float sin símbolos de moneda.
3. En desglose_fijos lista entre 3 y 6 conceptos de costos fijos ESPECÍFICOS para {giro} (ej. licencia sanitaria, seguro del local, servicio de música). NO uses categorías genéricas como "otros".
4. En desglose_variables lista entre 3 y 6 conceptos de costos variables ESPECÍFICOS para {giro} (ej. granos de café, desechables, comisión de app de delivery). NO uses categorías genéricas como "otros".
5. El código calculará los totales sumando los items — NO incluyas los campos costos_fijos_mes ni costos_variables_mes en el JSON.
6. El FODA debe ser específico para el giro Y la ubicación — no genérico.
7. En el objeto "madurez" estima: cuántos meses tarda el negocio en alcanzar ventas estabilizadas (meses_hasta_madurez) y a qué porcentaje de las ventas maduras arrancaría en el mes 1 (porcentaje_ventas_mes1, entre 5 y 80).
8. En "inversion_inicial" estima el desembolso único necesario para abrir el negocio: depósito de renta, adecuaciones del local, equipamiento, inventario inicial y gastos de apertura. NO incluyas costos operativos mensuales recurrentes. Este valor puede superar el capital disponible declarado.
9. Responde ÚNICA Y EXCLUSIVAMENTE con el JSON. Sin bloques markdown, sin texto antes, sin texto después.

Estructura JSON exacta (copia esta estructura, reemplaza los valores):
{{
  "giro": "{giro}",
  "capital": {capital},
  "ciudad": "{ciudad}",
  "ubicacion": "{ubicacion}",
  "ingresos_estimados_mes": 0.0,
  "desglose_fijos": [
    {{"concepto": "Nombre del costo fijo 1", "monto": 0.0}},
    {{"concepto": "Nombre del costo fijo 2", "monto": 0.0}},
    {{"concepto": "Nombre del costo fijo 3", "monto": 0.0}}
  ],
  "desglose_variables": [
    {{"concepto": "Nombre del costo variable 1", "monto": 0.0}},
    {{"concepto": "Nombre del costo variable 2", "monto": 0.0}},
    {{"concepto": "Nombre del costo variable 3", "monto": 0.0}}
  ],
  "inversion_inicial": 0.0,
  "utilidad_neta_mes": 0.0,
  "punto_equilibrio_unidades": 0.0,
  "meses_recuperacion_capital": 0.0,
  "precio_unitario_promedio": 0.0,
  "costo_variable_unitario": 0.0,
  "madurez": {{
    "meses_hasta_madurez": 0,
    "porcentaje_ventas_mes1": 0.0
  }},
  "foda": {{
    "fortalezas": ["fortaleza 1", "fortaleza 2", "fortaleza 3"],
    "oportunidades": ["oportunidad 1", "oportunidad 2", "oportunidad 3"],
    "debilidades": ["debilidad 1", "debilidad 2", "debilidad 3"],
    "amenazas": ["amenaza 1", "amenaza 2", "amenaza 3"]
  }}
}}

Reglas de calidad:
- Los valores deben ser realistas para {giro} en {ubicacion}, {ciudad}.
- Cada concepto en desglose_fijos y desglose_variables debe ser específico al giro — evita términos genéricos.
- utilidad_neta_mes = ingresos_estimados_mes − suma(desglose_fijos[].monto) − suma(desglose_variables[].monto).
- meses_recuperacion_capital = capital / utilidad_neta_mes (null si utilidad ≤ 0).
- punto_equilibrio_unidades = suma(desglose_fijos[].monto) / (precio_unitario_promedio − costo_variable_unitario).
- madurez.meses_hasta_madurez: entero entre 6 y 48. madurez.porcentaje_ventas_mes1: float entre 5.0 y 80.0.
- inversion_inicial: float positivo, representa el total de gastos one-time para abrir (NO costos mensuales). Puede ser mayor que el capital disponible.
- Incluye 3 o 4 elementos en cada lista del FODA.
- JSON válido siempre: sin comas finales, sin comentarios, sin texto fuera del JSON.
"""


def get_scenario(giro: str, capital: float, ciudad: str, ubicacion: str) -> str:
    """
    Llama a la API de Groq y devuelve el JSON crudo del escenario financiero.
    No parsea la respuesta — eso es responsabilidad de core.scenario_parser.

    Args:
        giro: Tipo o rubro del negocio (ej. "Cafetería").
        capital: Capital inicial en MXN.
        ciudad: Ciudad donde se abrirá el negocio.
        ubicacion: Nombre de la ubicación/colonia elegida por el usuario.

    Returns:
        String con el JSON crudo devuelto por Groq.

    Raises:
        EnvironmentError: Si no se encuentra GROQ_API_KEY en el entorno.
        RuntimeError: Si la llamada a la API falla por red, cuota u otro error.
    """
    client = get_client()
    prompt = _build_scenario_prompt(giro, capital, ciudad, ubicacion)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        raise RuntimeError(
            f"Error al llamar a la API de Groq (escenario): {e}. "
            "Verifica tu conexión a internet o el estado de tu cuota."
        ) from e

    return clean_json(response.choices[0].message.content)
