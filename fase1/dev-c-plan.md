# Plan Dev C — Modelos y Parser

## Resumen

Implementar la capa de datos de la aplicación: los dataclasses que representan la respuesta de Gemini
(`Criterio`, `Ubicacion`, `RespuestaIA`) y la función `parse_response()` que convierte el JSON crudo
de Dev B en un objeto `RespuestaIA`. También generar `requirements.txt` y `.env.example`.

**Archivos propios:** `core/models.py`, `core/parser.py`, `requirements.txt`, `.env.example`

**Contrato de entrada:** `str` JSON crudo devuelto por `ai.gemini_client.get_locations()`
**Contrato de salida:** `RespuestaIA` (con lista de `Ubicacion`) consumido por `app.py` / Dev A

---

## Sub-tarea 1 — Definir los modelos de datos en `core/models.py`

**Intent**
Crear los tres dataclasses que representan la estructura completa del JSON de Gemini.
Estos son el contrato de datos compartido con Dev A; deben estar listos primero.

**Expected Outcomes**
- `core/models.py` existe con tres dataclasses: `Criterio`, `Ubicacion`, `RespuestaIA`.
- Todos los campos coinciden exactamente con las claves JSON de `AI_INSTRUCTIONS.md`.
- `puntaje` y `puntaje_total` aceptan `int` o `float` (coerción en el parser, no en el modelo).
- El archivo no importa nada externo a la biblioteca estándar de Python.

**Todo List**
- [ ] Crear el directorio `core/` con `__init__.py` vacío
- [ ] Crear `core/models.py` con:
  - `@dataclass Criterio`: campos `nivel: str`, `puntaje: float`, `nota: str`
  - `@dataclass Ubicacion`: campos `id: int`, `nombre: str`, `descripcion_breve: str`,
    `criterios: dict`, `puntaje_total: float`, `recomendacion_ia: str`
  - `@dataclass RespuestaIA`: campos `ciudad: str`, `giro: str`, `capital: float`,
    `ubicaciones: list`

**Relevant Context**
- Esquema JSON de referencia: `fase1/AI_INSTRUCTIONS.md` — sección "Estructura exacta del JSON"
- Los 9 criterios son claves del dict `criterios`; no se listan como atributos individuales

**Status:** `[x] done`

---

## Sub-tarea 2 — Implementar `parse_response()` en `core/parser.py`

**Intent**
Convertir el string JSON crudo que devuelve Dev B en un objeto `RespuestaIA` validado.
Es el único punto de parseo en toda la aplicación.

**Expected Outcomes**
- `core/parser.py` existe con la función `parse_response(json_str: str) -> RespuestaIA`.
- Válida que existan las claves raíz: `ciudad`, `giro`, `capital`, `ubicaciones`.
- Válida que cada ubicación tenga: `id`, `nombre`, `descripcion_breve`, `criterios`,
  `puntaje_total`, `recomendacion_ia`.
- Válida que cada criterio tenga: `nivel`, `puntaje`, `nota`.
- Aplica coerción numérica silenciosa: `float(puntaje)`, `float(capital)`, etc.
- Ignora silenciosamente claves desconocidas en cualquier nivel.
- Lanza `ValueError` con mensaje descriptivo si falta cualquier clave requerida.
- Lanza `ValueError` con mensaje descriptivo si el string no es JSON válido.

**Todo List**
- [ ] Crear `core/parser.py` con `parse_response(json_str: str) -> RespuestaIA`
  - Llamar a `json.loads(json_str)` dentro de un try/except para capturar `json.JSONDecodeError`
  - Validar claves raíz; lanzar `ValueError` si faltan
  - Iterar `ubicaciones`, validar claves por ubicación
  - Iterar `criterios` de cada ubicación, validar claves por criterio
  - Construir `Criterio` → insertar en dict → construir `Ubicacion` → construir `RespuestaIA`
  - Coercionar `puntaje`, `puntaje_total`, `capital` a `float`

**Relevant Context**
- Modelos definidos en sub-tarea 1: `core/models.py`
- Regla del AGENTS.md: `core/parser.py` es el **único** lugar donde se parsea; no puede llamar a Gemini

**Status:** `[x] done`

---

## Sub-tarea 3 — Generar `requirements.txt` y crear `.env.example`

**Intent**
Fijar las versiones exactas del entorno activo para reproducibilidad y documentar las variables
de entorno necesarias para que los otros devs puedan arrancar el proyecto.

**Expected Outcomes**
- `fase1/requirements.txt` contiene las dependencias con versiones fijadas (salida de `pip freeze`
  filtrada a los paquetes relevantes: `streamlit`, `google-generativeai`, `python-dotenv`
  y sus dependencias directas).
- `fase1/.env.example` contiene la variable `GEMINI_API_KEY=tu_api_key_aqui`.

**Todo List**
- [ ] Ejecutar `pip freeze` en el entorno activo
- [ ] Escribir `fase1/requirements.txt` con el output de `pip freeze`
- [ ] Crear `fase1/.env.example` con `GEMINI_API_KEY=tu_api_key_aqui`

**Relevant Context**
- El entorno Python ya tiene instalados `streamlit`, `google-generativeai`, `python-dotenv`
- El archivo va en `fase1/`, no en la raíz del proyecto (per AGENTS.md)

**Status:** `[x] done`

---

## Diagrama de dependencias entre sub-tareas

Sub-tarea 1 (models) debe completarse antes que Sub-tarea 2 (parser).
Sub-tarea 3 (requirements) es independiente y puede hacerse en cualquier orden.

```
[Sub-tarea 1: models.py] ──► [Sub-tarea 2: parser.py]

[Sub-tarea 3: requirements.txt]  (independiente)
```

---

## Contratos que este Dev C NO debe cruzar

- `core/parser.py` no llama a Gemini ni a ningún cliente de red.
- `core/models.py` no importa paquetes externos.
- `parse_response()` devuelve `RespuestaIA`, no `List[Ubicacion]` directamente (a diferencia de lo
  que indica PLANNING.md — actualización acordada durante la planificación).
