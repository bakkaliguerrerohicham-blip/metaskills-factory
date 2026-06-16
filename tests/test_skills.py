"""
Tests unitarios de DynamicSkill, BaseSkill y el REGISTRY.
OpenAI se mockea — no hay llamadas reales a la API.
"""
import os
from unittest.mock import MagicMock, patch

import pytest

SKILL_DEF_MINIMO = {
    "id": "test-skill-basica",
    "name": "Skill Básica de Test",
    "description": "Solo para testing",
    "category": "productividad",
    "sector": "inmobiliaria",
    "price_eur": 49,
    "system_prompt": "Eres un asistente de prueba. Responde siempre 'TEST OK'.",
}

SKILL_DEF_COMPLETO = {
    **SKILL_DEF_MINIMO,
    "price_setup_eur": 297,
    "version": "2.0.0",
    "model": "gpt-4o",
    "temperature": 0.5,
    "ejemplo_input": "Hola",
    "ejemplo_output": "TEST OK",
    "problema_que_resuelve": "Nada, es un test",
}


class TestDynamicSkill:

    def _make_skill(self, overrides=None):
        from skills.dynamic import DynamicSkill
        d = {**SKILL_DEF_MINIMO, **(overrides or {})}
        return DynamicSkill(d)

    def test_carga_campos_obligatorios(self):
        skill = self._make_skill()
        assert skill.id == "test-skill-basica"
        assert skill.name == "Skill Básica de Test"
        assert skill.description == "Solo para testing"
        assert skill.category == "productividad"
        assert skill.sector == "inmobiliaria"
        assert skill.price_eur == 49

    def test_system_prompt_property(self):
        skill = self._make_skill()
        assert "asistente de prueba" in skill.system_prompt

    def test_valores_por_defecto(self):
        """Sin campos opcionales, usa los defaults."""
        skill = self._make_skill()
        assert skill.version == "1.0.0"
        assert skill._model == "gpt-4o"
        assert skill._temperature == 0.3
        assert skill.price_setup_eur == 497
        assert skill.ejemplo_input == ""
        assert skill.ejemplo_output == ""
        assert skill.problema_que_resuelve == ""

    def test_carga_campos_opcionales(self):
        from skills.dynamic import DynamicSkill
        skill = DynamicSkill(SKILL_DEF_COMPLETO)
        assert skill.version == "2.0.0"
        assert skill._model == "gpt-4o"
        assert skill._temperature == 0.5
        assert skill.price_setup_eur == 297
        assert skill.ejemplo_input == "Hola"
        assert skill.ejemplo_output == "TEST OK"

    def test_to_dict_tiene_campos_clave(self):
        skill = self._make_skill()
        d = skill.to_dict()
        for campo in ["id", "name", "description", "category", "sector", "price_eur_month"]:
            assert campo in d, f"Falta '{campo}' en to_dict()"

    def test_to_dict_price_eur_month_correcto(self):
        skill = self._make_skill({"price_eur": 79})
        assert skill.to_dict()["price_eur_month"] == 79

    def test_run_llama_openai(self):
        from skills.dynamic import DynamicSkill
        skill = DynamicSkill(SKILL_DEF_MINIMO)

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Respuesta fake"

        with patch("skills.dynamic.OpenAI") as mock_openai_cls:
            mock_instance = MagicMock()
            mock_openai_cls.return_value = mock_instance
            mock_instance.chat.completions.create.return_value = mock_response

            result = skill.run("Entrada de prueba")

        assert result == "Respuesta fake"
        mock_instance.chat.completions.create.assert_called_once()

    def test_run_incluye_system_prompt(self):
        from skills.dynamic import DynamicSkill
        skill = DynamicSkill(SKILL_DEF_MINIMO)

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "ok"

        with patch("skills.dynamic.OpenAI") as mock_openai_cls:
            mock_instance = MagicMock()
            mock_openai_cls.return_value = mock_instance
            mock_instance.chat.completions.create.return_value = mock_response

            skill.run("test input")

        call_args = mock_instance.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
        # El primer mensaje debe ser el system prompt
        system_msgs = [m for m in messages if m.get("role") == "system"]
        assert system_msgs, "No hay mensaje de sistema en la llamada a OpenAI"
        assert "asistente de prueba" in system_msgs[0]["content"]

    def test_run_con_contexto_adicional(self):
        from skills.dynamic import DynamicSkill
        skill = DynamicSkill(SKILL_DEF_MINIMO)

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "ok con contexto"

        with patch("skills.dynamic.OpenAI") as mock_openai_cls:
            mock_instance = MagicMock()
            mock_openai_cls.return_value = mock_instance
            mock_instance.chat.completions.create.return_value = mock_response

            result = skill.run("input", context="contexto extra importante")

        assert result == "ok con contexto"
        call_args = mock_instance.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages", [])
        contenidos = " ".join(m.get("content", "") for m in messages)
        assert "contexto extra importante" in contenidos

    def test_run_usa_modelo_configurado(self):
        from skills.dynamic import DynamicSkill
        skill = DynamicSkill({**SKILL_DEF_MINIMO, "model": "gpt-4o-mini"})

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "ok"

        with patch("skills.dynamic.OpenAI") as mock_openai_cls:
            mock_instance = MagicMock()
            mock_openai_cls.return_value = mock_instance
            mock_instance.chat.completions.create.return_value = mock_response

            skill.run("test")

        call_args = mock_instance.chat.completions.create.call_args
        assert call_args.kwargs.get("model") == "gpt-4o-mini"


class TestRegistry:

    def test_registry_no_vacio(self):
        from skills import REGISTRY
        assert len(REGISTRY) > 0, "El REGISTRY está vacío"

    def test_registry_tiene_todas_las_skills_catalogo(self):
        from skills import REGISTRY
        from skills.catalog.inmobiliaria import SKILLS as INMO
        from skills.catalog.veterinaria import SKILLS as VET
        from skills.catalog.dental import SKILLS as DENTAL
        from skills.catalog.abogados import SKILLS as LEGAL
        from skills.catalog.gestoria import SKILLS as GEST

        total_catalogo = len(INMO) + len(VET) + len(DENTAL) + len(LEGAL) + len(GEST)
        assert len(REGISTRY) >= total_catalogo, (
            f"REGISTRY tiene {len(REGISTRY)} pero el catálogo tiene {total_catalogo} skills"
        )

    def test_registry_skills_legacy_incluidas(self):
        from skills import REGISTRY
        legacy_ids = [
            "atencion-cliente", "extractor-facturas",
            "clasificador-leads", "resumen-reuniones", "extractor-contratos"
        ]
        for lid in legacy_ids:
            assert lid in REGISTRY, f"Skill legacy '{lid}' no está en el REGISTRY"

    def test_registry_tiene_skill_inmobiliaria_conocida(self):
        from skills import REGISTRY
        assert "inmo-resumen-reunion" in REGISTRY

    def test_registry_tiene_skill_vet_triaje(self):
        from skills import REGISTRY
        assert "vet-triaje-urgencias" in REGISTRY

    def test_registry_ids_coinciden_con_objetos(self):
        """La clave del dict debe coincidir con el .id del objeto."""
        from skills import REGISTRY
        for key, skill in REGISTRY.items():
            assert key == skill.id, f"Clave '{key}' no coincide con skill.id='{skill.id}'"

    def test_load_fabricated_skills_no_falla_sin_archivo(self):
        """Si no hay skills_generadas.json, load_fabricated_skills no debe lanzar error."""
        from skills import load_fabricated_skills
        load_fabricated_skills()  # No debe lanzar

    def test_todos_los_objetos_tienen_metodo_run(self):
        from skills import REGISTRY
        sin_run = [sid for sid, s in REGISTRY.items() if not callable(getattr(s, "run", None))]
        assert not sin_run, f"Skills sin método run: {sin_run[:5]}"

    def test_todos_los_objetos_tienen_to_dict(self):
        from skills import REGISTRY
        sin_to_dict = [sid for sid, s in REGISTRY.items() if not callable(getattr(s, "to_dict", None))]
        assert not sin_to_dict, f"Skills sin to_dict: {sin_to_dict[:5]}"
