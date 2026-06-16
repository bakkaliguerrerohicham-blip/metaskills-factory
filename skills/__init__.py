"""
MetaSkills Registry — 150 skills de catálogo + skills generadas dinámicamente por el Fabricador.
"""
from .dynamic import DynamicSkill
from .catalog.inmobiliaria import SKILLS as INMO_SKILLS
from .catalog.veterinaria import SKILLS as VET_SKILLS
from .catalog.dental import SKILLS as DENTAL_SKILLS
from .catalog.abogados import SKILLS as LEGAL_SKILLS
from .catalog.gestoria import SKILLS as GEST_SKILLS

# Skills heredadas (se mantienen para compatibilidad)
from .atencion_cliente import AtencionClienteSkill
from .extractor_facturas import ExtractorFacturasSkill
from .clasificador_leads import ClasificadorLeadsSkill
from .resumen_reuniones import ResumenReunionesSkill
from .extractor_contratos import ExtractorContratosSkill

# Construir registro base con las 150 skills del catálogo
_catalog_skills = [
    DynamicSkill(s)
    for s in (INMO_SKILLS + VET_SKILLS + DENTAL_SKILLS + LEGAL_SKILLS + GEST_SKILLS)
]

# Skills heredadas
_legacy_skills = [
    AtencionClienteSkill(),
    ExtractorFacturasSkill(),
    ClasificadorLeadsSkill(),
    ResumenReunionesSkill(),
    ExtractorContratosSkill(),
]

# Registro principal
REGISTRY: dict = {s.id: s for s in (_catalog_skills + _legacy_skills)}


def load_fabricated_skills():
    """
    Carga las skills generadas dinámicamente por el MetaFabricador y las añade al REGISTRY.
    Llamar al arranque del servidor para incluir todas las skills persistidas.
    """
    try:
        from .fabricator import get_fabricated_skills
        for skill in get_fabricated_skills():
            if skill.id not in REGISTRY:
                REGISTRY[skill.id] = skill
    except Exception:
        pass  # Si no hay skills generadas todavía, continuar


# Cargar skills fabricadas al importar el módulo
load_fabricated_skills()
