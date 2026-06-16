"""
Tests unitarios del MetaFabricador.
Verifica la generación de skills desde problemas, persistencia JSON
y manejo de errores — sin llamadas reales a OpenAI.
"""
import json
import os
from unittest.mock import MagicMock, patch

import pytest


def patch_fabricador(raw_content: str):
    """
    Parchea _fabricar_con_claude y _fabricar_con_openai para devolver raw_content.
    Usar como context manager: `with patch_fabricador(json_str):`
    """
    from unittest.mock import patch as _patch
    from contextlib import ExitStack

    stack = ExitStack()
    stack.enter_context(_patch("skills.fabricator._fabricar_con_claude", return_value=raw_content))
    stack.enter_context(_patch("skills.fabricator._fabricar_con_openai", return_value=raw_content))
    return stack


SKILL_JSON_VALIDO = json.dumps({
    "id": "inmo-detector-precio-alto",
    "name": "Detector de Precio Alto",
    "description": "Analiza si un inmueble está sobrevalorado respecto al mercado",
    "category": "analisis",
    "sector": "inmobiliaria",
    "price_eur": 79,
    "price_setup_eur": 497,
    "system_prompt": "Eres un tasador inmobiliario experto. Analiza el precio del inmueble y determina si está alineado con el mercado. Responde con PRECIO_ALTO, PRECIO_JUSTO o PRECIO_BAJO seguido de justificación.",
    "temperature": 0.3,
    "model": "gpt-4o",
    "ejemplo_input": "Piso 80m² en Chamberí Madrid, precio 450.000€",
    "ejemplo_output": "PRECIO_JUSTO — Chamberí cotiza a ~5.500€/m². Este piso está a 5.625€/m², dentro del rango.",
    "problema_que_resuelve": "Sin esta skill el agente no sabe si el precio está inflado antes de visitar",
    "pitch_comercial": "Sabe en 10 segundos si el precio vale antes de perder el tiempo"
})


class TestExtractJson:

    def test_json_limpio(self):
        from skills.fabricator import _extract_json
        result = _extract_json('{"id": "test", "name": "Test"}')
        assert result == {"id": "test", "name": "Test"}

    def test_json_con_backticks(self):
        from skills.fabricator import _extract_json
        texto = "```json\n{\"id\": \"test\"}\n```"
        result = _extract_json(texto)
        assert result["id"] == "test"

    def test_json_con_backticks_sin_json(self):
        from skills.fabricator import _extract_json
        texto = "```\n{\"id\": \"test\"}\n```"
        result = _extract_json(texto)
        assert result["id"] == "test"

    def test_json_con_texto_previo(self):
        from skills.fabricator import _extract_json
        texto = "Aquí tienes la skill:\n\n{\"id\": \"mi-skill\", \"name\": \"Test\"}"
        result = _extract_json(texto)
        assert result["id"] == "mi-skill"

    def test_sin_json_lanza_error(self):
        from skills.fabricator import _extract_json
        with pytest.raises(ValueError, match="No se encontró JSON"):
            _extract_json("Texto sin ningún JSON aquí")

    def test_json_invalido_lanza_error(self):
        from skills.fabricator import _extract_json
        with pytest.raises(json.JSONDecodeError):
            _extract_json("{id: sin-comillas}")


class TestFabricarSkill:

    def test_fabricar_retorna_skill_def_valido(self, tmp_generated_file):
        from skills import fabricator
        original_file = fabricator.GENERATED_FILE

        try:
            fabricator.GENERATED_FILE = tmp_generated_file

            with patch_fabricador(SKILL_JSON_VALIDO):
                result = fabricator.fabricar_skill(
                    problema="No sé si el precio del piso está bien",
                    sector="inmobiliaria",
                )
        finally:
            fabricator.GENERATED_FILE = original_file

        assert result["id"] == "inmo-detector-precio-alto"
        assert result["name"] == "Detector de Precio Alto"
        assert result["sector"] == "inmobiliaria"
        assert "fabricado_en" in result
        assert "fabricado_por" in result

    def test_fabricar_persiste_en_json(self, tmp_generated_file):
        from skills import fabricator
        original_file = fabricator.GENERATED_FILE

        try:
            fabricator.GENERATED_FILE = tmp_generated_file

            with patch_fabricador(SKILL_JSON_VALIDO):
                fabricator.fabricar_skill("Mi problema", "inmobiliaria")

            assert os.path.exists(tmp_generated_file)
            with open(tmp_generated_file) as f:
                guardadas = json.load(f)

            assert len(guardadas) == 1
            assert guardadas[0]["id"] == "inmo-detector-precio-alto"
        finally:
            fabricator.GENERATED_FILE = original_file

    def test_fabricar_id_duplicado_agrega_timestamp(self, tmp_generated_file):
        from skills import fabricator
        original_file = fabricator.GENERATED_FILE

        try:
            fabricator.GENERATED_FILE = tmp_generated_file

            with patch_fabricador(SKILL_JSON_VALIDO):
                first = fabricator.fabricar_skill("Problema 1", "inmobiliaria")

            with patch_fabricador(SKILL_JSON_VALIDO):
                second = fabricator.fabricar_skill("Mismo problema", "inmobiliaria")

            assert first["id"] != second["id"], "IDs duplicados no deben quedarse iguales"
            assert second["id"].startswith("inmo-detector-precio-alto-")
        finally:
            fabricator.GENERATED_FILE = original_file

    def test_fabricar_sin_openai_key_lanza_error(self, tmp_generated_file):
        from skills import fabricator
        original_key = os.environ.pop("OPENAI_API_KEY", None)
        original_file = fabricator.GENERATED_FILE

        try:
            fabricator.GENERATED_FILE = tmp_generated_file
            with pytest.raises(EnvironmentError, match="OPENAI_API_KEY"):
                fabricator.fabricar_skill("Mi problema", "dental")
        finally:
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key
            fabricator.GENERATED_FILE = original_file

    def test_fabricar_json_invalido_lanza_value_error(self, tmp_generated_file):
        from skills import fabricator
        original_file = fabricator.GENERATED_FILE

        try:
            fabricator.GENERATED_FILE = tmp_generated_file

            with patch_fabricador("Texto sin JSON válido aquí"):
                with pytest.raises(ValueError):
                    fabricator.fabricar_skill("Problema", "veterinaria")
        finally:
            fabricator.GENERATED_FILE = original_file

    def test_fabricar_acepta_contexto_opcional(self, tmp_generated_file):
        from skills import fabricator
        original_file = fabricator.GENERATED_FILE
        captured = {}

        def mock_claude(prompt):
            captured["prompt"] = prompt
            return SKILL_JSON_VALIDO

        try:
            fabricator.GENERATED_FILE = tmp_generated_file

            with patch("skills.fabricator._fabricar_con_claude", side_effect=mock_claude), \
                 patch("skills.fabricator._fabricar_con_openai", return_value=SKILL_JSON_VALIDO):
                fabricator.fabricar_skill(
                    problema="Gestionar facturas",
                    sector="gestoria",
                    contexto="Tenemos 200 clientes autónomos"
                )

            assert "200 clientes autónomos" in captured.get("prompt", "")
        finally:
            fabricator.GENERATED_FILE = original_file

    def test_fabricar_fields_por_defecto(self, tmp_generated_file):
        """Los campos version, model y fabricado_por se añaden aunque no estén en el JSON."""
        from skills import fabricator
        original_file = fabricator.GENERATED_FILE

        json_sin_version = json.dumps({
            "id": "test-sin-version",
            "name": "Test",
            "description": "Desc",
            "category": "productividad",
            "sector": "dental",
            "price_eur": 49,
            "price_setup_eur": 297,
            "system_prompt": "Eres un asistente.",
            "ejemplo_input": "",
            "ejemplo_output": "",
            "problema_que_resuelve": "",
            "pitch_comercial": "",
        })

        try:
            fabricator.GENERATED_FILE = tmp_generated_file

            with patch_fabricador(json_sin_version):
                result = fabricator.fabricar_skill("Problema dental", "dental")

            assert result["version"] == "1.0.0"
            assert result["model"] == "gpt-4o"
            assert "MetaFabricador v2" in result["fabricado_por"]
        finally:
            fabricator.GENERATED_FILE = original_file


class TestGetFabricatedSkills:

    def test_sin_archivo_devuelve_lista_vacia(self, tmp_path):
        from skills import fabricator
        original = fabricator.GENERATED_FILE
        fabricator.GENERATED_FILE = str(tmp_path / "no_existe.json")
        try:
            result = fabricator.get_fabricated_skills()
            assert result == []
        finally:
            fabricator.GENERATED_FILE = original

    def test_con_skills_guardadas_devuelve_dynamic_skills(self, tmp_generated_file):
        from skills import fabricator
        from skills.dynamic import DynamicSkill

        skills_data = [json.loads(SKILL_JSON_VALIDO)]
        with open(tmp_generated_file, "w") as f:
            json.dump(skills_data, f)

        original = fabricator.GENERATED_FILE
        fabricator.GENERATED_FILE = tmp_generated_file
        try:
            result = fabricator.get_fabricated_skills()
            assert len(result) == 1
            assert isinstance(result[0], DynamicSkill)
            assert result[0].id == "inmo-detector-precio-alto"
        finally:
            fabricator.GENERATED_FILE = original
