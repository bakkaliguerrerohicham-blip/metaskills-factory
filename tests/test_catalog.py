"""
Tests de integridad del catálogo de skills.
Verifica que los 143 skills tienen todos los campos requeridos,
IDs únicos, precios razonables y system_prompts no vacíos.
"""
import pytest
from skills.catalog.inmobiliaria import SKILLS as INMO
from skills.catalog.veterinaria import SKILLS as VET
from skills.catalog.dental import SKILLS as DENTAL
from skills.catalog.abogados import SKILLS as LEGAL
from skills.catalog.gestoria import SKILLS as GEST

TODOS_LOS_SKILLS = INMO + VET + DENTAL + LEGAL + GEST

CAMPOS_OBLIGATORIOS = ["id", "name", "description", "category", "sector", "system_prompt", "price_eur"]

SECTORES_ESPERADOS = {
    "inmobiliaria": INMO,
    "veterinaria": VET,
    "dental": DENTAL,
    "abogados": LEGAL,
    "gestoria": GEST,
}


class TestCatalogIntegridad:

    def test_total_skills_minimo(self):
        """El catálogo debe tener al menos 130 skills."""
        assert len(TODOS_LOS_SKILLS) >= 130, (
            f"Solo hay {len(TODOS_LOS_SKILLS)} skills. Se esperan al menos 130."
        )

    def test_ids_unicos(self):
        """Ningún ID puede repetirse en todo el catálogo."""
        ids = [s["id"] for s in TODOS_LOS_SKILLS]
        duplicados = [x for x in ids if ids.count(x) > 1]
        assert not duplicados, f"IDs duplicados encontrados: {set(duplicados)}"

    @pytest.mark.parametrize("campo", CAMPOS_OBLIGATORIOS)
    def test_todos_tienen_campo(self, campo):
        """Todas las skills deben tener el campo obligatorio (0 es válido para price_eur)."""
        sin_campo = [s["id"] for s in TODOS_LOS_SKILLS if s.get(campo) is None or s.get(campo) == ""]
        assert not sin_campo, (
            f"Skills sin '{campo}': {sin_campo[:5]}{'...' if len(sin_campo) > 5 else ''}"
        )

    def test_system_prompts_suficientemente_largos(self):
        """Un system_prompt de menos de 50 chars es inútil."""
        cortos = [s["id"] for s in TODOS_LOS_SKILLS if len(s.get("system_prompt", "")) < 50]
        assert not cortos, f"System prompts demasiado cortos en: {cortos}"

    def test_precios_en_rango_razonable(self):
        """price_eur entre 0 (gratuito social) y 500€."""
        fuera = [s["id"] for s in TODOS_LOS_SKILLS if not (0 <= s.get("price_eur", -1) <= 500)]
        assert not fuera, f"Precios fuera de rango en: {fuera}"

    def test_sector_coincide_con_lista(self):
        """El campo 'sector' de cada skill debe coincidir con su lista de origen."""
        for sector_nombre, lista in SECTORES_ESPERADOS.items():
            incorrectos = [s["id"] for s in lista if s.get("sector") != sector_nombre]
            assert not incorrectos, (
                f"Skills en {sector_nombre} con sector incorrecto: {incorrectos}"
            )

    def test_ids_en_kebab_case(self):
        """Los IDs deben ser kebab-case (solo minúsculas, números y guiones)."""
        import re
        invalidos = [
            s["id"] for s in TODOS_LOS_SKILLS
            if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", s["id"])
        ]
        assert not invalidos, f"IDs no kebab-case: {invalidos}"

    def test_names_no_vacios(self):
        """El nombre no puede estar vacío ni ser solo espacios."""
        vacios = [s["id"] for s in TODOS_LOS_SKILLS if not s.get("name", "").strip()]
        assert not vacios, f"Skills sin nombre: {vacios}"

    def test_category_es_string_valido(self):
        """La categoría debe ser una string no vacía."""
        sin_cat = [s["id"] for s in TODOS_LOS_SKILLS if not isinstance(s.get("category"), str) or not s["category"]]
        assert not sin_cat, f"Skills sin categoría válida: {sin_cat}"


class TestSectoresCuenta:

    def test_inmobiliaria_tiene_suficientes_skills(self):
        assert len(INMO) >= 25, f"Inmobiliaria tiene solo {len(INMO)} skills"

    def test_veterinaria_tiene_suficientes_skills(self):
        assert len(VET) >= 20, f"Veterinaria tiene solo {len(VET)} skills"

    def test_dental_tiene_suficientes_skills(self):
        assert len(DENTAL) >= 20, f"Dental tiene solo {len(DENTAL)} skills"

    def test_abogados_tiene_suficientes_skills(self):
        assert len(LEGAL) >= 20, f"Abogados tiene solo {len(LEGAL)} skills"

    def test_gestoria_tiene_suficientes_skills(self):
        assert len(GEST) >= 20, f"Gestoría tiene solo {len(GEST)} skills"

    def test_cada_sector_tiene_al_menos_5_categorias(self):
        """Cada sector debe cubrir variedad de categorías."""
        for nombre, lista in SECTORES_ESPERADOS.items():
            cats = {s.get("category") for s in lista}
            assert len(cats) >= 5, (
                f"Sector {nombre} solo tiene {len(cats)} categorías distintas: {cats}"
            )


class TestSkillsEspecificas:
    """Verifica que skills concretas de alto valor existen en el catálogo."""

    def test_inmo_resumen_reunion_existe(self):
        ids = {s["id"] for s in INMO}
        assert "inmo-resumen-reunion" in ids

    def test_vet_triaje_urgencias_existe(self):
        ids = {s["id"] for s in VET}
        assert "vet-triaje-urgencias" in ids

    def test_legal_violencia_genero_precio_cero(self):
        """El bot de violencia de género debe ser gratuito (servicio social)."""
        skill = next((s for s in LEGAL if s["id"] == "legal-bot-violencia-genero"), None)
        assert skill is not None, "legal-bot-violencia-genero no existe en el catálogo"
        assert skill["price_eur"] == 0, (
            f"legal-bot-violencia-genero debe ser gratis pero price_eur={skill['price_eur']}"
        )

    def test_dental_resumen_reunion_existe(self):
        ids = {s["id"] for s in DENTAL}
        assert "dental-resumen-reunion-llegada-tarde" in ids

    def test_gest_clasificador_facturas_existe(self):
        ids = {s["id"] for s in GEST}
        assert "gest-clasificador-facturas" in ids
