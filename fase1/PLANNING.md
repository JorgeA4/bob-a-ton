# Fase 1 — Plan de Trabajo en Equipo

## Objetivo
Construir una aplicación Streamlit donde el usuario ingresa **giro**, **capital inicial** y **ciudad**,
y la IA (Gemini) devuelve una comparativa visual de ubicaciones recomendadas dentro de esa ciudad.

---

## Estructura de carpetas

El código fuente vive en la **raíz del repositorio**. `fase1/` contiene únicamente archivos de planificación.

```
/ (raíz del repositorio)
├── app.py                  # Punto de entrada Streamlit (Dev A)
├── ui/
│   └── components.py       # Componentes visuales reutilizables (Dev A)
├── ai/
│   └── gemini_client.py    # Lógica de llamada a Gemini (Dev B)
│   └── prompt_builder.py   # Construcción del prompt estructurado (Dev B)
├── core/
│   └── models.py           # Dataclasses / modelos de datos del JSON (Dev C)
│   └── parser.py           # Parseo y validación del JSON de respuesta (Dev C)
├── requirements.txt        # Dependencias del proyecto
├── .env.example            # Variables de entorno necesarias
└── fase1/
    ├── PLANNING.md         # Este archivo
    ├── AI_INSTRUCTIONS.md  # Instrucciones para el agente de IA
    └── dev-c-plan.md       # Plan detallado de Dev C (completado — ver resumen abajo)
```

---

## División de responsabilidades

### 👤 Dev A — UI / Streamlit
**Archivos propios:** `app.py`, `ui/components.py`

**Tareas:**
- [x] Armar el formulario de entrada: campos `giro`, `capital` y `ciudad`
- [x] Agregar validaciones de formulario (campos no vacíos, capital numérico positivo)
- [x] Mostrar estado de carga mientras la IA procesa (`st.spinner`)
- [x] Consumir la función `get_locations()` del módulo `ai/` y pasar el resultado a los componentes
- [x] Renderizar la tabla comparativa usando `ui/components.py`
- [x] Renderizar el gráfico de radar/barras por ubicación
- [x] Mostrar la recomendación final de la IA en un bloque destacado
- [x] Eliminar el mock de `parse_response` en `app.py` — `core/parser.py` ya existe y puede importarse directamente

**Contratos que debe respetar:**
- Llamar a `ai.gemini_client.get_locations(giro, capital, ciudad) -> str`
- Parsear el resultado con `core.parser.parse_response(raw) -> List[dict]`
- Pasar `ubicaciones` (lista de dicts) directamente a los componentes

---

### 👤 Dev B — IA / Gemini
**Archivos propios:** `ai/gemini_client.py`, `ai/prompt_builder.py`

**Tareas:**
- [x] Configurar el cliente de Gemini con la API key desde `.env`
- [x] Escribir `build_prompt(giro, capital, ciudad) -> str` en `prompt_builder.py`
- [x] Asegurarse de que el prompt instruya a Gemini a responder **solo** con JSON válido
- [x] Escribir `get_locations(giro, capital, ciudad) -> str` en `gemini_client.py`
  - Llama a `build_prompt()`
  - Envía el prompt a Gemini
  - Devuelve el string JSON crudo (sin parsear)
- [x] Manejar errores de red y de cuota de la API con excepciones claras

**Contratos que debe respetar:**
- `get_locations()` devuelve el JSON **como string**, el parseo lo hace Dev C
- El modelo a usar: `gemini-3.6-flash`

---

### 👤 Dev C — Datos / Modelos ✅ completado
**Archivos propios:** `core/models.py`, `core/parser.py`

**Tareas:**
- [x] Definir `@dataclass Criterio`: `nivel: str`, `puntaje: float`, `nota: str`
- [x] Definir `@dataclass Ubicacion`: `id`, `nombre`, `descripcion_breve`, `criterios: dict`, `puntaje_total: float`, `recomendacion_ia`
- [x] Definir `@dataclass RespuestaIA`: `ciudad`, `giro`, `capital: float`, `ubicaciones: list`
- [x] Escribir `parse_response(json_str: str) -> RespuestaIA` en `parser.py`
  - Valida claves raíz y por ubicación/criterio; lanza `ValueError` si faltan
  - Coerciona `puntaje`, `puntaje_total` y `capital` a `float`
  - Ignora claves desconocidas en cualquier nivel
- [x] Escribir `requirements.txt` con dependencias fijadas
- [x] Escribir `.env.example`

**Contratos que debe respetar:**
- `parse_response()` devuelve `List[dict]` validados y con tipos coercionados — ni `RespuestaIA` ni `List[Ubicacion]` directamente (decisión de implementación final)
- Los nombres de campos coinciden exactamente con el JSON definido en `AI_INSTRUCTIONS.md`

---

## Flujo de datos entre los tres devs

```
[Dev A] Formulario
    │  giro, capital, ciudad
    ▼
[Dev B] gemini_client.get_locations()
    │  prompt → Gemini API → JSON string
    ▼
[Dev C] parser.parse_response()
    │  JSON string → RespuestaIA
    ▼
[Dev A] ui/components.py
    │  respuesta.ubicaciones → tabla + gráfico + recomendación
    ▼
[Dev A] Pantalla final
```

---

## Puntos de integración (evitar conflictos)

| Punto | Quién produce | Quién consume | Formato acordado |
|---|---|---|---|
| Resultado de IA | Dev B (`get_locations`) | Dev C (`parse_response`) | `str` JSON crudo |
| Datos parseados | Dev C (`parse_response`) | Dev A (`app.py`) | `RespuestaIA` — acceder a `.ubicaciones` para la lista |
| Componentes visuales | Dev A (`components.py`) | Dev A (`app.py`) | Funciones que reciben `list[Ubicacion]` |

**Regla:** Nadie toca los archivos del otro sin avisar. Si se necesita cambiar una firma de función, se acuerda primero.

---

## Orden de desarrollo sugerido

1. **Dev C empieza primero** — define `models.py` para que todos tengan el contrato de datos claro
2. **Dev B y Dev A arrancan en paralelo** una vez que `Ubicacion` está definido
3. **Integración final** — Dev A conecta todo en `app.py` usando mocks si Dev B o Dev C no han terminado

---

## Dependencias del proyecto (`requirements.txt`)

```
streamlit
google-generativeai
python-dotenv
```

---

## Variables de entorno (`.env.example`)

```
GEMINI_API_KEY=tu_api_key_aqui
```
