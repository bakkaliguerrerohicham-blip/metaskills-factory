from abc import ABC, abstractmethod
from typing import Optional
from openai import OpenAI
import os


class BaseSkill(ABC):
    id: str
    name: str
    description: str
    price_eur: int
    version: str = "1.0.0"
    category: str = "general"

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        ...

    def run(self, input_text: str, context: Optional[str] = None) -> str:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.append({"role": "user", "content": f"Contexto adicional:\n{context}"})
            messages.append({"role": "assistant", "content": "Entendido, lo tendré en cuenta."})
        messages.append({"role": "user", "content": input_text})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1024,
            temperature=0.3,
        )
        return response.choices[0].message.content

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price_eur_month": self.price_eur,
            "version": self.version,
            "category": self.category,
        }
