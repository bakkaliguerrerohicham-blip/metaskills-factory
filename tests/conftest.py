"""
Fixtures compartidas para toda la suite de tests MetaSkills Factory.
"""
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Asegurar que metaskills/ está en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Variables de entorno mínimas para que los módulos importen sin errores
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key-for-unit-tests")
os.environ.setdefault("METASKILLS_API_KEY", "test-key-2026")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-fake")

VALID_API_KEY = "test-key-2026"
HEADERS_OK = {"x-metaskills-key": VALID_API_KEY}
HEADERS_BAD = {"x-metaskills-key": "clave-incorrecta"}


def make_openai_response(content: str):
    """Crea un mock de respuesta OpenAI con el contenido dado."""
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.fixture()
def openai_mock():
    """Parchea OpenAI.chat.completions.create para evitar llamadas reales."""
    with patch("openai.OpenAI") as mock_class:
        instance = MagicMock()
        mock_class.return_value = instance
        instance.chat.completions.create.return_value = make_openai_response(
            "Respuesta mock de la skill"
        )
        yield instance


@pytest.fixture()
def client(openai_mock):
    """Cliente de test FastAPI con OpenAI mockeado."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.fixture()
def fabricator_json():
    """JSON válido que devolvería el MetaFabricador."""
    return {
        "id": "test-skill-generada",
        "name": "Skill de Test",
        "description": "Skill generada en test para verificar el fabricador",
        "category": "productividad",
        "sector": "inmobiliaria",
        "price_eur": 79,
        "price_setup_eur": 497,
        "system_prompt": "Eres un asistente de test. Responde con 'TEST OK'.",
        "temperature": 0.3,
        "model": "gpt-4o",
        "ejemplo_input": "Prueba de test",
        "ejemplo_output": "TEST OK",
        "problema_que_resuelve": "Sin esta skill los tests no funcionan",
        "pitch_comercial": "La skill que hace pasar todos tus tests",
        "version": "1.0.0",
    }


@pytest.fixture()
def tmp_generated_file(tmp_path):
    """Archivo temporal para skills_generadas.json en tests del fabricador."""
    return str(tmp_path / "skills_generadas.json")
