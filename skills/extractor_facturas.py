from .base import BaseSkill


class ExtractorFacturasSkill(BaseSkill):
    id = "extractor-facturas"
    name = "Extractor de Facturas"
    description = "Extrae datos estructurados de texto de facturas: emisor, receptor, importe, IVA, fecha, número."
    price_eur = 199
    category = "contabilidad"

    @property
    def system_prompt(self) -> str:
        return """Eres un motor de extracción de datos contables.
Dado el texto de una factura, extrae SIEMPRE en JSON válido con esta estructura exacta:

{
  "numero_factura": "",
  "fecha_emision": "",
  "emisor": {"nombre": "", "cif": "", "direccion": ""},
  "receptor": {"nombre": "", "cif": "", "direccion": ""},
  "lineas": [{"descripcion": "", "cantidad": 0, "precio_unitario": 0, "importe": 0}],
  "base_imponible": 0,
  "iva_porcentaje": 0,
  "iva_importe": 0,
  "total": 0,
  "moneda": "EUR"
}

Si un campo no está disponible, usa null. Responde SOLO con el JSON, sin texto adicional."""
