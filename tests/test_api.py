"""
Tests de integración de la API FastAPI de MetaSkills Factory.
Cubre todos los endpoints: health, catálogo, run, fabricar, sectores.
OpenAI mockeado — sin llamadas reales.
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

VALID_KEY = "test-key-2026"
HEADERS = {"x-metaskills-key": VALID_KEY}
BAD_HEADERS = {"x-metaskills-key": "clave-incorrecta"}

FABRICAR_RESPONSE_JSON = json.dumps({
    "id": "vet-consejo-postoperatorio-gen",
    "name": "Consejo Post-Operatorio",
    "description": "Genera instrucciones de cuidado post-operatorio para el dueño",
    "category": "clinica",
    "sector": "veterinaria",
    "price_eur": 79,
    "price_setup_eur": 497,
    "system_prompt": "Eres un veterinario experto. Genera instrucciones claras de cuidado post-operatorio adaptadas al procedimiento indicado.",
    "temperature": 0.3,
    "model": "gpt-4o",
    "ejemplo_input": "Esterilización de gata de 2 años",
    "ejemplo_output": "1. Reposo 24h. 2. No mojar la herida 10 días. 3. Collar isabelino.",
    "problema_que_resuelve": "Sin esta skill el veterinario olvida dar instrucciones completas por las prisas",
    "pitch_comercial": "Instrucciones perfectas en 5 segundos, dueños felices, menos reclamaciones",
})


def _make_mock_response(content="Respuesta mockeada de la skill"):
    resp = MagicMock()
    resp.choices[0].message.content = content
    return resp


@pytest.fixture(autouse=True)
def patch_openai():
    """Parchea OpenAI en todos los módulos para toda la sesión de tests de API."""
    with patch("skills.dynamic.OpenAI") as mock_dyn, \
         patch("skills.base.OpenAI") as mock_base:
        for m in [mock_dyn, mock_base]:
            instance = MagicMock()
            instance.chat.completions.create.return_value = _make_mock_response()
            m.return_value = instance
        yield


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app)


# ─── GET / ────────────────────────────────────────────────────────────────────

class TestRoot:

    def test_root_ok(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_root_tiene_product(self, client):
        data = client.get("/").json()
        assert data["product"] == "MetaSkills Factory"

    def test_root_tiene_version(self, client):
        data = client.get("/").json()
        assert "version" in data

    def test_root_tiene_skills_totales(self, client):
        data = client.get("/").json()
        assert data["skills_totales"] >= 130

    def test_root_tiene_por_sector(self, client):
        data = client.get("/").json()
        assert "por_sector" in data
        assert len(data["por_sector"]) >= 5


# ─── GET /health ──────────────────────────────────────────────────────────────

class TestHealth:

    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_incluye_conteo_skills(self, client):
        data = client.get("/health").json()
        assert data["skills"] >= 130


# ─── GET /skills ──────────────────────────────────────────────────────────────

class TestListSkills:

    def test_lista_skills_sin_filtro(self, client):
        r = client.get("/skills")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 130
        assert isinstance(data["skills"], list)

    def test_filtrar_por_sector_inmobiliaria(self, client):
        r = client.get("/skills?sector=inmobiliaria")
        data = r.json()
        assert data["total"] >= 25
        for s in data["skills"]:
            assert s["sector"] == "inmobiliaria"

    def test_filtrar_por_sector_veterinaria(self, client):
        r = client.get("/skills?sector=veterinaria")
        data = r.json()
        assert data["total"] >= 20
        for s in data["skills"]:
            assert s["sector"] == "veterinaria"

    def test_filtrar_por_sector_dental(self, client):
        r = client.get("/skills?sector=dental")
        data = r.json()
        assert data["total"] >= 20

    def test_filtrar_por_sector_abogados(self, client):
        r = client.get("/skills?sector=abogados")
        data = r.json()
        assert data["total"] >= 20

    def test_filtrar_por_sector_gestoria(self, client):
        r = client.get("/skills?sector=gestoria")
        data = r.json()
        assert data["total"] >= 20

    def test_sector_inexistente_devuelve_cero(self, client):
        r = client.get("/skills?sector=pizzeria")
        data = r.json()
        assert data["total"] == 0
        assert data["skills"] == []

    def test_filtrar_por_categoria(self, client):
        r = client.get("/skills?category=productividad")
        data = r.json()
        for s in data["skills"]:
            assert s["category"] == "productividad"

    def test_cada_skill_tiene_campos_basicos(self, client):
        skills = client.get("/skills").json()["skills"]
        for s in skills[:20]:  # Verificamos los primeros 20 para no tardar
            for campo in ["id", "name", "description", "category"]:
                assert campo in s, f"Skill {s.get('id')} sin campo '{campo}'"


# ─── GET /skills/{id} ─────────────────────────────────────────────────────────

class TestGetSkill:

    def test_get_skill_existente(self, client):
        r = client.get("/skills/inmo-resumen-reunion")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "inmo-resumen-reunion"

    def test_get_skill_incluye_system_prompt(self, client):
        r = client.get("/skills/inmo-resumen-reunion")
        data = r.json()
        assert "system_prompt" in data
        assert len(data["system_prompt"]) > 50

    def test_get_skill_incluye_ejemplo_input(self, client):
        r = client.get("/skills/inmo-resumen-reunion")
        data = r.json()
        assert "ejemplo_input" in data

    def test_get_skill_vet_triaje(self, client):
        r = client.get("/skills/vet-triaje-urgencias")
        assert r.status_code == 200

    def test_get_skill_no_existente_404(self, client):
        r = client.get("/skills/skill-que-no-existe-jamas")
        assert r.status_code == 404
        assert "no encontrada" in r.json()["detail"].lower()

    def test_get_skill_legal_violencia_genero(self, client):
        r = client.get("/skills/legal-bot-violencia-genero")
        assert r.status_code == 200
        data = r.json()
        assert data["price_eur_month"] == 0


# ─── POST /skills/{id}/run ────────────────────────────────────────────────────

class TestRunSkill:

    def test_run_skill_con_key_valida(self, client):
        r = client.post(
            "/skills/inmo-resumen-reunion/run",
            json={"input": "El cliente quiere un piso de 3 habitaciones en Madrid"},
            headers=HEADERS,
        )
        assert r.status_code == 200
        data = r.json()
        assert "output" in data
        assert "latency_ms" in data
        assert data["skill_id"] == "inmo-resumen-reunion"

    def test_run_skill_output_no_vacio(self, client):
        r = client.post(
            "/skills/vet-triaje-urgencias/run",
            json={"input": "Perro convulsionando, 3 años, pastor alemán"},
            headers=HEADERS,
        )
        assert r.status_code == 200
        assert r.json()["output"] != ""

    def test_run_skill_latency_es_numero_positivo(self, client):
        r = client.post(
            "/skills/dental-resumen-reunion-llegada-tarde/run",
            json={"input": "Reunión sobre el paciente García"},
            headers=HEADERS,
        )
        assert r.status_code == 200
        assert r.json()["latency_ms"] >= 0

    def test_run_skill_sin_key_401(self, client):
        r = client.post(
            "/skills/inmo-resumen-reunion/run",
            json={"input": "test"},
        )
        assert r.status_code == 422  # header requerido falta

    def test_run_skill_key_incorrecta_401(self, client):
        r = client.post(
            "/skills/inmo-resumen-reunion/run",
            json={"input": "test"},
            headers=BAD_HEADERS,
        )
        assert r.status_code == 401
        assert "inválida" in r.json()["detail"].lower()

    def test_run_skill_input_vacio_422(self, client):
        r = client.post(
            "/skills/inmo-resumen-reunion/run",
            json={"input": "   "},
            headers=HEADERS,
        )
        assert r.status_code == 422

    def test_run_skill_inexistente_404(self, client):
        r = client.post(
            "/skills/skill-fantasma-xyz/run",
            json={"input": "test"},
            headers=HEADERS,
        )
        assert r.status_code == 404

    def test_run_skill_con_contexto(self, client):
        r = client.post(
            "/skills/inmo-generador-anuncio/run",
            json={
                "input": "Piso 90m², 3 hab, Chamberí Madrid, 350.000€",
                "context": "Cliente VIP, usar tono premium"
            },
            headers=HEADERS,
        )
        assert r.status_code == 200

    def test_run_skill_gest_clasificador_facturas(self, client):
        r = client.post(
            "/skills/gest-clasificador-facturas/run",
            json={"input": "Factura de Endesa 85€ del 01/03/2026"},
            headers=HEADERS,
        )
        assert r.status_code == 200

    def test_run_skill_legal_detector_prescripcion(self, client):
        r = client.post(
            "/skills/legal-detector-prescripcion/run",
            json={"input": "Accidente de tráfico ocurrido el 15/03/2023, ¿ha prescrito?"},
            headers=HEADERS,
        )
        assert r.status_code == 200


# ─── POST /fabricar ───────────────────────────────────────────────────────────

class TestFabricar:

    def _fabricar(self, client, problema, sector, contexto=None):
        body = {"problema": problema, "sector": sector}
        if contexto:
            body["contexto"] = contexto
        with patch("skills.fabricator.OpenAI") as mock_cls, \
             patch("skills.fabricator._save_generated"), \
             patch("skills.fabricator._load_generated", return_value=[]):
            instance = MagicMock()
            instance.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content=FABRICAR_RESPONSE_JSON))]
            )
            mock_cls.return_value = instance
            return client.post("/fabricar", json=body, headers=HEADERS)

    def test_fabricar_devuelve_200(self, client):
        r = self._fabricar(client, "Los dueños olvidan las instrucciones post-op", "veterinaria")
        assert r.status_code == 200

    def test_fabricar_respuesta_tiene_skill_id(self, client):
        r = self._fabricar(client, "Problema de consejo post-op", "veterinaria")
        data = r.json()
        assert "skill_id" in data
        assert data["skill_id"] != ""

    def test_fabricar_respuesta_tiene_mensaje_exito(self, client):
        r = self._fabricar(client, "Problema de consejo post-op", "veterinaria")
        assert "✅" in r.json()["mensaje"]

    def test_fabricar_skill_queda_en_registry(self, client):
        from skills import REGISTRY
        r = self._fabricar(client, "Necesito consejo post-op", "veterinaria")
        skill_id = r.json()["skill_id"]
        assert skill_id in REGISTRY, f"La skill fabricada '{skill_id}' no está en el REGISTRY"

    def test_fabricar_skill_es_ejecutable_despues(self, client):
        r = self._fabricar(client, "Consejo post-op para veterinaria", "veterinaria")
        skill_id = r.json()["skill_id"]

        r2 = client.post(
            f"/skills/{skill_id}/run",
            json={"input": "Esterilización de gato"},
            headers=HEADERS,
        )
        assert r2.status_code == 200

    def test_fabricar_key_incorrecta_401(self, client):
        r = client.post(
            "/fabricar",
            json={"problema": "test", "sector": "dental"},
            headers=BAD_HEADERS,
        )
        assert r.status_code == 401

    def test_fabricar_problema_vacio_422(self, client):
        r = client.post(
            "/fabricar",
            json={"problema": "   ", "sector": "dental"},
            headers=HEADERS,
        )
        assert r.status_code == 422

    def test_fabricar_sector_vacio_422(self, client):
        r = client.post(
            "/fabricar",
            json={"problema": "Tengo un problema", "sector": ""},
            headers=HEADERS,
        )
        assert r.status_code == 422

    def test_fabricar_sin_key_422(self, client):
        r = client.post(
            "/fabricar",
            json={"problema": "Problema", "sector": "dental"},
        )
        assert r.status_code == 422

    def test_fabricar_acepta_contexto(self, client):
        r = self._fabricar(
            client,
            "Los pacientes cancelan sin avisar",
            "dental",
            "Clínica con 3 dentistas y 200 pacientes/mes"
        )
        assert r.status_code == 200

    def test_fabricar_respuesta_tiene_price_eur(self, client):
        r = self._fabricar(client, "Problema vet", "veterinaria")
        data = r.json()
        assert "price_eur" in data
        assert data["price_eur"] >= 0


# ─── GET /sectores ────────────────────────────────────────────────────────────

class TestSectores:

    def test_sectores_ok(self, client):
        r = client.get("/sectores")
        assert r.status_code == 200

    def test_sectores_tiene_cinco_sectores(self, client):
        data = client.get("/sectores").json()
        assert len(data["sectores"]) >= 5

    def test_sectores_tiene_inmobiliaria(self, client):
        data = client.get("/sectores").json()
        assert "inmobiliaria" in data["sectores"]

    def test_sectores_tiene_veterinaria(self, client):
        data = client.get("/sectores").json()
        assert "veterinaria" in data["sectores"]

    def test_sectores_cada_uno_tiene_total(self, client):
        data = client.get("/sectores").json()
        for sec, info in data["sectores"].items():
            assert "total" in info, f"Sector {sec} sin campo 'total'"
            assert info["total"] >= 1

    def test_sectores_cada_uno_tiene_categorias(self, client):
        data = client.get("/sectores").json()
        for sec, info in data["sectores"].items():
            assert "categorias" in info, f"Sector {sec} sin 'categorias'"
            assert isinstance(info["categorias"], list)


# ─── GET /fabricadas ──────────────────────────────────────────────────────────

class TestFabricadas:

    def test_fabricadas_con_key_valida(self, client):
        with patch("skills.fabricator._load_generated", return_value=[]):
            r = client.get("/fabricadas", headers=HEADERS)
        assert r.status_code == 200

    def test_fabricadas_key_incorrecta_401(self, client):
        r = client.get("/fabricadas", headers=BAD_HEADERS)
        assert r.status_code == 401

    def test_fabricadas_sin_key_422(self, client):
        r = client.get("/fabricadas")
        assert r.status_code == 422

    def test_fabricadas_tiene_total(self, client):
        with patch("skills.fabricator._load_generated", return_value=[]):
            data = client.get("/fabricadas", headers=HEADERS).json()
        assert "total" in data
        assert "skills" in data
