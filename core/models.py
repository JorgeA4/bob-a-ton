from dataclasses import dataclass, field


@dataclass
class Criterio:
    """Evaluación de un criterio individual para una ubicación."""
    nivel: str          # "bajo" | "medio" | "alto" | "muy alto"
    puntaje: float      # 1–10
    nota: str           # Descripción concreta del criterio en esa zona


@dataclass
class Ubicacion:
    """Representa una zona o colonia candidata evaluada por la IA."""
    id: int
    nombre: str
    descripcion_breve: str
    criterios: dict     # {str: Criterio} — las 9 claves definidas en AI_INSTRUCTIONS.md
    puntaje_total: float
    recomendacion_ia: str


@dataclass
class RespuestaIA:
    """Respuesta completa de la IA: metadatos de la consulta + lista de ubicaciones evaluadas."""
    ciudad: str
    giro: str
    capital: float
    ubicaciones: list   # List[Ubicacion]
