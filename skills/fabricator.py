"""
MetaFabricador — Genera skills desde la descripción de un problema.
El usuario dice "tengo este problema" → IA genera la skill → se registra → se vende.
Usa GPT-4o como motor principal (OPENAI_API_KEY). Fallback a Claude si está disponible.
"""
import json
import os
import re
import time
from typing import Optional

from openai import OpenAI

from .dynamic import DynamicSkill

GENERATED_FILE = os.path.join(os.path.dirname(__file__), "skills_generadas.json")

FABRICATOR_PROMPT = """\
Eres el arquitecto de microservicios de IA de Impacto Digital. Tu trabajo: convertir cualquier problema profesional en una skill de IA vendible como SaaS.

Un profesional del sector "{sector}" tiene este problema:

PROBLEMA: {problema}
{contexto_bloque}

Genera una skill de IA que resuelva exactamente ese problema. La skill debe:
1. Resolver el problema en menos de 30 segundos de uso
2. Poder venderse como microservicio por 49-149€/mes
3. Tener un system_prompt tan bueno que cualquier modelo lo ejecute perfectamente

Responde SOLO con este JSON (sin texto extra, sin bloques de código):

{{
  "id": "slug-kebab-case-unico-descriptivo",
  "name": "Nombre Comercial de la Skill (máx 5 palabras)",
  "description": "Qué hace en 1 frase y qué problema concreto resuelve",
  "category": "productividad|ventas|marketing|documentos|analisis|atencion-cliente|fiscal|legal|clinica|urgencias|fidelizacion|educacion",
  "sector": "{sector}",
  "price_eur": 79,
  "price_setup_eur": 497,
  "system_prompt": "Eres un experto en [sector]. Tu trabajo es [tarea específica y concreta]. El usuario te dará [input exacto]. Tú debes [output exacto con formato]. Siempre [comportamiento clave 1]. Nunca [comportamiento a evitar]. Responde [formato de salida].",
  "temperature": 0.3,
  "model": "gpt-4o",
  "ejemplo_input": "Ejemplo real de lo que le mandaría el cliente",
  "ejemplo_output": "Ejemplo de respuesta que daría la skill (breve)",
  "problema_que_resuelve": "Sin esta skill, el profesional [consecuencia negativa concreta]",
  "pitch_comercial": "Frase de venta de 1 línea para el dossier comercial"
}}

El system_prompt es lo más importante. Debe ser tan específico que no haya ambigüedad sobre qué hace la skill.
"""


def _load_generated() -> list:
    if os.path.exists(GENERATED_FILE):
        with open(GENERATED_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_generated(skills: list):
    with open(GENERATED_FILE, "w", encoding="utf-8") as f:
        json.dump(skills, f, ensure_ascii=False, indent=2)


def _extract_json(text: str) -> dict:
    text = text.strip()
    # Remove markdown code blocks if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    # Find first { ... }
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No se encontró JSON válido en la respuesta del fabricador")
    return json.loads(match.group())


def fabricar_skill(
    problema: str,
    sector: str,
    contexto: Optional[str] = None,
) -> dict:
    """
    Dado un problema en lenguaje natural, genera una skill lista para usar y vender.
    Devuelve el skill_def (dict) con el sistema listo.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY no configurada")

    contexto_bloque = f"CONTEXTO ADICIONAL: {contexto}" if contexto else ""

    prompt = FABRICATOR_PROMPT.format(
        sector=sector,
        problema=problema,
        contexto_bloque=contexto_bloque,
    )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2000,
        temperature=0.7,
        messages=[
            {"role": "system", "content": "Eres un arquitecto de microservicios de IA. Respondes SOLO con JSON válido, sin texto adicional."},
            {"role": "user", "content": prompt},
        ],
    )

    raw = response.choices[0].message.content
    skill_def = _extract_json(raw)

    # Ensure required fields
    skill_def.setdefault("version", "1.0.0")
    skill_def.setdefault("model", "gpt-4o")
    skill_def.setdefault("temperature", 0.3)
    skill_def["fabricado_en"] = int(time.time())
    skill_def["fabricado_por"] = "MetaFabricador v1"

    # Persist
    generated = _load_generated()
    # Avoid duplicates by id
    existing_ids = {s.get("id") for s in generated}
    if skill_def.get("id") in existing_ids:
        skill_def["id"] = f"{skill_def['id']}-{int(time.time())}"
    generated.append(skill_def)
    _save_generated(generated)

    return skill_def


def get_fabricated_skills() -> list[DynamicSkill]:
    """Carga todas las skills generadas dinámicamente."""
    return [DynamicSkill(s) for s in _load_generated()]
