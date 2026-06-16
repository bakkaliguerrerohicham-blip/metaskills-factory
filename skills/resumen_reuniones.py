from .base import BaseSkill


class ResumenReunionesSkill(BaseSkill):
    id = "resumen-reuniones"
    name = "Resumen de Reuniones"
    description = "Convierte transcripciones de reuniones en resúmenes ejecutivos con decisiones y tareas asignadas."
    price_eur = 149
    category = "productividad"

    @property
    def system_prompt(self) -> str:
        return """Eres un asistente ejecutivo especializado en sintetizar reuniones.
Dado el texto o transcripción de una reunión, responde en JSON:

{
  "resumen_ejecutivo": "2-3 frases del propósito y resultado",
  "decisiones": ["decisión 1", "decisión 2"],
  "tareas": [
    {"responsable": "", "tarea": "", "fecha_limite": ""}
  ],
  "proxima_reunion": "",
  "participantes": []
}

Si algo no está claro, infiere razonablemente. Responde SOLO con el JSON."""
