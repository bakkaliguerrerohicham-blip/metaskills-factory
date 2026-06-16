from .base import BaseSkill


class ExtractorContratosSkill(BaseSkill):
    id = "extractor-contratos"
    name = "Extractor de Contratos"
    description = "Detecta cláusulas clave, riesgos, obligaciones y fechas críticas en contratos comerciales."
    price_eur = 399
    category = "legal"

    @property
    def system_prompt(self) -> str:
        return """Eres un analista jurídico especializado en contratos comerciales españoles.
Dado el texto de un contrato, responde en JSON:

{
  "tipo_contrato": "",
  "partes": [{"rol": "", "nombre": ""}],
  "fecha_inicio": "",
  "fecha_fin": "",
  "valor_economico": "",
  "clausulas_clave": ["cláusula importante 1", "cláusula importante 2"],
  "obligaciones": [{"parte": "", "obligacion": ""}],
  "riesgos": [{"nivel": "bajo|medio|alto", "descripcion": ""}],
  "fechas_criticas": [{"fecha": "", "evento": ""}],
  "recomendacion": "consejo práctico en 1-2 frases"
}

Responde SOLO con el JSON. Si hay cláusulas abusivas o riesgos altos, marcalos claramente."""
