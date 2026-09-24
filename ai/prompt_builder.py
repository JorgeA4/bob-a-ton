def build_prompt(giro: str, capital: float, ciudad: str, zona_preferida: str = "") -> str:
    """
    Construye el prompt estructurado que se enviará a Gemini.
    Devuelve un string listo para ser usado como mensaje.

    Args:
        giro: Tipo o rubro del negocio.
        capital: Capital inicial en MXN.
        ciudad: Ciudad donde se abrirá el negocio.
        zona_preferida: Zona o colonia específica que el usuario quiere evaluar (opcional).
                        Si se proporciona, se incluye como primera ubicación obligatoria.
    """
    if zona_preferida.strip():
        instruccion_zona = (
            f"- Zona de interés del usuario: {zona_preferida}\n\n"
            f"IMPORTANTE: La primera ubicación del array (id: 1) DEBE ser \"{zona_preferida}\". "
            f"Evalúala con los mismos 9 criterios con la misma rigurosidad que las demás. "
            f"Las otras 4 ubicaciones las eliges tú según tu criterio experto."
        )
    else:
        instruccion_zona = ""

    return f"""Eres un consultor experto en apertura de negocios y análisis de mercado local.
Tu tarea es analizar la viabilidad de ubicaciones dentro de una ciudad para un negocio específico,
y devolver una comparativa estructurada en formato JSON.

Datos del negocio:
- Giro: {giro}
- Capital inicial: {capital} MXN
- Ciudad: {ciudad}
{instruccion_zona}
═══════════════════════════════════════════════════════════
REGLA CRÍTICA DE FORMATO — SIN EXCEPCIONES:
Tu respuesta debe ser EXCLUSIVAMENTE un objeto JSON válido.
- El PRIMER carácter de tu respuesta debe ser el carácter {{
- El ÚLTIMO carácter de tu respuesta debe ser el carácter }}
- CERO texto antes del {{, CERO texto después del }}
- CERO bloques markdown, CERO explicaciones, CERO comentarios dentro del JSON
- CERO comas finales después del último elemento de un objeto o array
- Todos los strings deben usar comillas dobles (" "), nunca comillas simples
- No uses caracteres de control ni saltos de línea dentro de strings
═══════════════════════════════════════════════════════════

CLASIFICACIÓN DEL GIRO — sigue este orden de decisión:

1. GIRO INAPROPIADO / NO ANALIZABLE: Si el giro corresponde a actividades ilegales,
   inmorales o que no son negocios formales legítimos (ejemplos: prostíbulo, burdel,
   casa de citas, narcotráfico, sicariato, casino ilegal, lavado de dinero, etc.),
   devuelve INMEDIATAMENTE y ÚNICAMENTE este JSON:
   {{"error": "giro_no_reconocido", "mensaje": "Este giro no puede analizarse porque corresponde a una actividad ilegal o no es un negocio formal legítimo."}}

2. GIRO DE ALIMENTOS / ESPECIALIDAD CULINARIA: Si el giro menciona un tipo de comida
   o especialidad gastronómica (ejemplos: "comida china", "tacos de canasta", "pizza",
   "sushi", "mariscos", "hamburguesas", "comida italiana", "marisquería"), trátalo como
   un negocio de RESTAURANTE o FONDA y analízalo normalmente con las 5 ubicaciones.

3. GIRO AMBIGUO PERO INTERPRETABLE: Si el giro no es completamente claro pero puede
   asociarse a un tipo de negocio razonable, interpreta la intención más probable y
   analízalo normalmente.

4. GIRO ININTERPRETABLE: Solo si el texto es completamente ilegible, sin sentido
   absoluto, o un conjunto de caracteres aleatorios que no corresponden a ningún
   negocio posible, devuelve ÚNICAMENTE:
   {{"error": "giro_no_reconocido", "mensaje": "El texto ingresado no corresponde a ningún tipo de negocio reconocible."}}

Instrucciones para el análisis normal (casos 2, 3 y 4 cuando aplica análisis):
1. Identifica 5 zonas o colonias REALES y representativas dentro de {ciudad} para este tipo de negocio.
2. Evalúa cada zona con los 9 criterios definidos (puntaje 1–10, donde 10 es la mejor condición).
3. Calcula el puntaje_total como la suma exacta de los 9 puntajes individuales.
4. Incluye una recomendacion_ia breve y accionable por ubicación.

Los 9 criterios (claves JSON exactas):
- costo_renta: costo mensual estimado vs el capital disponible (10 = muy accesible)
- flujo_peatonal: volumen de personas que transitan naturalmente (10 = muy alto)
- accesibilidad_transporte: facilidad para llegar en transporte (10 = excelente conectividad)
- nivel_competencia: densidad de negocios similares en 500m (10 = sin competencia)
- afinidad_con_giro: qué tan bien encaja el perfil demográfico con el negocio (10 = fit perfecto)
- seguridad_zona: nivel de seguridad percibida y real (10 = muy segura)
- potencial_crecimiento: si la zona está en expansión o declive (10 = alto potencial)
- visibilidad_local: exposición del local hacia la calle o zonas de alto tráfico (10 = máxima visibilidad)
- compatibilidad_capital: capital requerido para abrir en esa zona vs el capital disponible (10 = zona muy barata de arrancar, el capital sobra; 1 = zona requiere mucho más capital del disponible)

Estructura exacta del JSON a devolver (análisis normal):
{{
  "ciudad": "{ciudad}",
  "giro": "{giro}",
  "capital": {capital},
  "ubicaciones": [
    {{
      "id": 1,
      "nombre": "nombre real de la colonia o zona",
      "descripcion_breve": "1 o 2 oraciones describiendo la zona en contexto del negocio",
      "criterios": {{
        "costo_renta": {{"puntaje": 7, "nota": "estimación concreta"}},
        "flujo_peatonal": {{"puntaje": 8, "nota": "descripción del flujo"}},
        "accesibilidad_transporte": {{"puntaje": 6, "nota": "medios disponibles"}},
        "nivel_competencia": {{"puntaje": 5, "nota": "competencia directa"}},
        "afinidad_con_giro": {{"puntaje": 9, "nota": "perfil de la zona"}},
        "seguridad_zona": {{"puntaje": 7, "nota": "contexto de seguridad"}},
        "potencial_crecimiento": {{"puntaje": 8, "nota": "tendencia urbana"}},
        "visibilidad_local": {{"puntaje": 6, "nota": "exposición comercial"}},
        "compatibilidad_capital": {{"puntaje": 7, "nota": "estimación de arranque"}}
      }},
      "puntaje_total": 63,
      "recomendacion_ia": "2 o 3 oraciones con recomendación accionable considerando el capital"
    }}
  ]
}}

Reglas de calidad:
- Usa nombres REALES de colonias de {ciudad}, nunca genéricos como "zona norte".
- Los puntajes deben diferenciarse entre ubicaciones para el mismo criterio.
- Si el capital es menor a 80000 MXN, penaliza fuertemente costo_renta y compatibilidad_capital en zonas caras.
- Ajusta los puntajes según la lógica del giro (ej. taller mecánico necesita acceso vehicular, no flujo peatonal).
- puntaje_total debe ser la suma aritmética exacta de los 9 puntajes.
- JSON válido siempre: sin comas finales, sin comentarios, sin texto fuera del JSON.
- RECUERDA: primera respuesta = carácter {{, última respuesta = carácter }}. Nada más.
"""
