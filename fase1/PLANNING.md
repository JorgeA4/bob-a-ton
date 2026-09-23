# Fase 1 — Plan de Trabajo en Equipo

## Objetivo
Construir una aplicación Streamlit donde el usuario ingresa **giro**, **capital inicial** y **ciudad**,
y la IA (Gemini) devuelve una comparativa visual de ubicaciones recomendadas dentro de esa ciudad.

---

## Estructura de carpetas

```
fase1/
├── app.py                  # Punto de entrada Streamlit (Dev A)
├── ui/
│   └── components.py       # Componentes visuales reutilizables (Dev A)
├── ai/
│   └── gemini_client.py    # Lógica de llamada a Gemini (Dev B)
│   └── prompt_builder.py   # Construcción del prompt estructurado (Dev B)
├── core/
│   └── models.py           # Dataclasses / modelos de datos del JSON (Dev C)
│   └── parser.py           # Parseo y validación del JSON de respuesta (Dev C)
├── PLANNING.md             # Este archivo
├── AI_INSTRUCTIONS.md      # Instrucciones para el agente de IA
├── requirements.txt        # Dependencias del proyecto
└── .env.example            # Variables de entorno necesarias
```

---

## División de responsabilidades

### 👤 Dev A — UI / Streamlit
**Archivos propios:** `app.py`, `ui/components.py`

**Tareas:**
- [ ] Armar el formulario de entrada: campos `giro`, `capital` y `ciudad`
- [ ] Agregar validaciones de formulario (campos no vacíos, capital numérico positivo)
- [ ] Mostrar estado de carga mientras la IA procesa (`st.spinner`)
- [ ] Consumir la función `get_locations()` del módulo `ai/` y pasar el resultado a los componentes
- [ ] Renderizar la tabla comparativa usando `ui/components.py`
- [ ] Renderizar el gráfico de radar/barras por ubicación
- [ ] Mostrar la recomendación final de la IA en un bloque destacado

**Contratos que debe respetar:**
- Llamar a `ai.gemini_client.get_locations(giro, capital, ciudad) -> List[Ubicacion]`
- Recibir una lista de objetos `Ubicacion` definidos en `core/models.py`

---

### 👤 Dev B — IA / Gemini
**Archivos propios:** `ai/gemini_client.py`, `ai/prompt_builder.py`

**Tareas:**
- [ ] Configurar el cliente de Gemini con la API key desde `.env`
- [ ] Escribir `build_prompt(giro, capital, ciudad) -> str` en `prompt_builder.py`
- [ ] Asegurarse de que el prompt instruya a Gemini a responder **solo** con JSON válido
- [ ] Escribir `get_locations(giro, capital, ciudad) -> str` en `gemini_client.py`
  - Llama a `build_prompt()`
  - Envía el prompt a Gemini
  - Devuelve el string JSON crudo (sin parsear)
- [ ] Manejar errores de red y de cuota de la API con excepciones claras

**Contratos que debe respetar:**
- `get_locations()` devuelve el JSON **como string**, el parseo lo hace Dev C
- El modelo a usar: `gemini-1.5-flash` (gratuito y rápido)

---

### 👤 Dev C — Datos / Modelos
**Archivos propios:** `core/models.py`, `core/parser.py`

**Tareas:**
- [ ] Definir la dataclass `Criterio` con campos: `nivel`, `puntaje`, `nota`
- [ ] Definir la dataclass `Ubicacion` con todos los campos del JSON acordado
- [ ] Escribir `parse_response(json_str: str) -> List[Ubicacion]` en `parser.py`
  - Valida que el JSON tenga la estructura esperada
  - Convierte el dict a objetos `Ubicacion`
  - Lanza excepciones descriptivas si faltan campos clave
- [ ] Escribir `requirements.txt` con todas las dependencias
- [ ] Escribir `.env.example` con las variables necesarias

**Contratos que debe respetar:**
- `parse_response()` recibe el string crudo de Dev B y devuelve `List[Ubicacion]` para Dev A
- Los nombres de campos de `Ubicacion` deben coincidir exactamente con el JSON definido en `AI_INSTRUCTIONS.md`

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
    │  JSON string → List[Ubicacion]
    ▼
[Dev A] ui/components.py
    │  List[Ubicacion] → tabla + gráfico + recomendación
    ▼
[Dev A] Pantalla final
```

---

## Puntos de integración (evitar conflictos)

| Punto | Quién produce | Quién consume | Formato acordado |
|---|---|---|---|
| Resultado de IA | Dev B (`get_locations`) | Dev C (`parse_response`) | `str` JSON crudo |
| Datos parseados | Dev C (`parse_response`) | Dev A (`app.py`) | `List[Ubicacion]` |
| Componentes visuales | Dev A (`components.py`) | Dev A (`app.py`) | Funciones que reciben `List[Ubicacion]` |

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
