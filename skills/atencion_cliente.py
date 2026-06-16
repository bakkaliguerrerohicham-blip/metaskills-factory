from .base import BaseSkill


class AtencionClienteSkill(BaseSkill):
    id = "atencion-cliente"
    name = "Atención al Cliente 24/7"
    description = "Responde consultas de clientes en el tono y voz de tu marca, con contexto del negocio."
    price_eur = 299
    category = "comunicacion"

    @property
    def system_prompt(self) -> str:
        return """Eres un agente de atención al cliente profesional y empático.
Tu objetivo es resolver la consulta del cliente de forma clara, breve y útil.

REGLAS:
- Responde siempre en el mismo idioma que el cliente.
- Sé conciso: máximo 150 palabras por respuesta.
- Si no tienes información suficiente, ofrece escalar a un agente humano.
- Nunca inventes datos, precios ni políticas.
- Tono: profesional pero cercano. Nunca robótico."""
