from .base import BaseSkill
from openai import OpenAI
import os
from typing import Optional


class DynamicSkill(BaseSkill):
    """Skill creada desde un diccionario de definición — base del catálogo y el fabricador."""

    def __init__(self, skill_def: dict):
        self.id = skill_def["id"]
        self.name = skill_def["name"]
        self.description = skill_def["description"]
        self.category = skill_def["category"]
        self.price_eur = skill_def.get("price_eur", 97)
        self.version = skill_def.get("version", "1.0.0")
        self.sector = skill_def.get("sector", "general")
        self._system_prompt = skill_def["system_prompt"]
        self._model = skill_def.get("model", "gpt-4o")
        self._temperature = skill_def.get("temperature", 0.3)
        self.price_setup_eur = skill_def.get("price_setup_eur", 497)
        self.ejemplo_input = skill_def.get("ejemplo_input", "")
        self.ejemplo_output = skill_def.get("ejemplo_output", "")
        self.problema_que_resuelve = skill_def.get("problema_que_resuelve", "")

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    def run(self, input_text: str, context: Optional[str] = None) -> str:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        messages = [{"role": "system", "content": self._system_prompt}]
        if context:
            messages.append({"role": "user", "content": f"Contexto adicional:\n{context}"})
            messages.append({"role": "assistant", "content": "Entendido."})
        messages.append({"role": "user", "content": input_text})
        response = client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=1500,
            temperature=self._temperature,
        )
        return response.choices[0].message.content

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "sector": self.sector,
            "price_eur_month": self.price_eur,
            "price_setup_eur": self.price_setup_eur,
            "version": self.version,
            "problema_que_resuelve": self.problema_que_resuelve,
            "ejemplo_input": self.ejemplo_input,
        }
