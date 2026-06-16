from .base import BaseSkill


class ClasificadorLeadsSkill(BaseSkill):
    id = "clasificador-leads"
    name = "Clasificador de Leads"
    description = "Puntúa y clasifica leads del CRM según intención de compra, urgencia y potencial económico."
    price_eur = 249
    category = "ventas"

    @property
    def system_prompt(self) -> str:
        return """Eres un experto en cualificación de leads B2B.
Dado el texto de un lead (formulario, email, nota de CRM), responde SIEMPRE en JSON:

{
  "score": 0,
  "clasificacion": "frio|tibio|caliente",
  "urgencia": "baja|media|alta",
  "potencial_economico": "bajo|medio|alto",
  "motivo": "explicación en 1-2 frases",
  "siguiente_accion": "acción concreta recomendada"
}

Score de 0 a 100. Caliente = >70. Tibio = 40-70. Frío = <40.
Responde SOLO con el JSON."""
