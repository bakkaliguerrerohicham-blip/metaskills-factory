from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
import time

from skills import REGISTRY, load_fabricated_skills
from skills.fabricator import fabricar_skill
from skills.dynamic import DynamicSkill

app = FastAPI(
    title="MetaSkills Factory",
    description="Fábrica de habilidades de IA: 150 skills por sector + MetaFabricador que genera nuevas desde cualquier problema. Por Impacto Digital.",
    version="2.0.0",
)

API_KEY = os.environ.get("METASKILLS_API_KEY", "dev-key-2026")


def verify_key(x_metaskills_key: str = Header(...)):
    if x_metaskills_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    return x_metaskills_key


# ─── Modelos ──────────────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    input: str
    context: Optional[str] = None


class RunResponse(BaseModel):
    skill_id: str
    output: str
    latency_ms: int


class FabricarRequest(BaseModel):
    problema: str
    sector: str
    contexto: Optional[str] = None


class FabricarResponse(BaseModel):
    skill_id: str
    name: str
    description: str
    category: str
    sector: str
    price_eur: int
    price_setup_eur: int
    system_prompt: str
    pitch_comercial: str
    ejemplo_input: str
    mensaje: str


# ─── Endpoints base ───────────────────────────────────────────────────────────

@app.get("/")
def root():
    sectores = {}
    for s in REGISTRY.values():
        sec = getattr(s, "sector", "general")
        sectores[sec] = sectores.get(sec, 0) + 1
    return {
        "product": "MetaSkills Factory",
        "version": "2.0.0",
        "by": "Impacto Digital",
        "skills_totales": len(REGISTRY),
        "por_sector": sectores,
        "docs": "/docs",
        "catalogo": "/skills",
        "fabricar": "POST /fabricar — Genera una skill nueva desde tu problema",
    }


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0", "skills": len(REGISTRY)}


@app.get("/skills")
def list_skills(sector: Optional[str] = None, category: Optional[str] = None):
    skills = list(REGISTRY.values())
    if sector:
        skills = [s for s in skills if getattr(s, "sector", "") == sector]
    if category:
        skills = [s for s in skills if getattr(s, "category", "") == category]
    return {
        "total": len(skills),
        "filtros": {"sector": sector, "category": category},
        "skills": [s.to_dict() for s in skills],
    }


@app.get("/skills/{skill_id}")
def get_skill(skill_id: str):
    skill = REGISTRY.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' no encontrada")
    d = skill.to_dict()
    d["system_prompt"] = skill.system_prompt  # Incluir el prompt en detalle
    d["ejemplo_input"] = getattr(skill, "ejemplo_input", "")
    d["ejemplo_output"] = getattr(skill, "ejemplo_output", "")
    return d


@app.post("/skills/{skill_id}/run", response_model=RunResponse)
def run_skill(skill_id: str, body: RunRequest, _key: str = Depends(verify_key)):
    skill = REGISTRY.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' no encontrada")
    if not body.input.strip():
        raise HTTPException(status_code=422, detail="El campo 'input' no puede estar vacío")

    t0 = time.time()
    try:
        output = skill.run(input_text=body.input, context=body.context)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Error ejecutando skill: {str(e)}")
    latency = int((time.time() - t0) * 1000)
    return RunResponse(skill_id=skill_id, output=output, latency_ms=latency)


# ─── MetaFabricador ───────────────────────────────────────────────────────────

@app.post("/fabricar", response_model=FabricarResponse)
def fabricar(body: FabricarRequest, _key: str = Depends(verify_key)):
    """
    El endpoint estrella. Le dices tu problema → Claude genera la skill → queda registrada.

    Ejemplo:
    {
      "problema": "Cuando llego tarde a una reunión con un propietario no sé de qué hablamos la última vez",
      "sector": "inmobiliaria",
      "contexto": "Somos una agencia con 3 agentes comerciales"
    }
    """
    if not body.problema.strip():
        raise HTTPException(status_code=422, detail="El campo 'problema' no puede estar vacío")
    if not body.sector.strip():
        raise HTTPException(status_code=422, detail="El campo 'sector' no puede estar vacío")

    try:
        skill_def = fabricar_skill(
            problema=body.problema,
            sector=body.sector,
            contexto=body.contexto,
        )
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Error del fabricador: {str(e)}")

    # Registrar en el REGISTRY para uso inmediato
    new_skill = DynamicSkill(skill_def)
    REGISTRY[new_skill.id] = new_skill

    return FabricarResponse(
        skill_id=new_skill.id,
        name=skill_def.get("name", ""),
        description=skill_def.get("description", ""),
        category=skill_def.get("category", ""),
        sector=skill_def.get("sector", body.sector),
        price_eur=skill_def.get("price_eur", 79),
        price_setup_eur=skill_def.get("price_setup_eur", 497),
        system_prompt=skill_def.get("system_prompt", ""),
        pitch_comercial=skill_def.get("pitch_comercial", ""),
        ejemplo_input=skill_def.get("ejemplo_input", ""),
        mensaje=f"✅ Skill '{new_skill.id}' generada y disponible en /skills/{new_skill.id}/run",
    )


@app.get("/sectores")
def list_sectores():
    """Lista todos los sectores disponibles con su número de skills."""
    sectores: dict[str, dict] = {}
    for s in REGISTRY.values():
        sec = getattr(s, "sector", "general")
        if sec not in sectores:
            sectores[sec] = {"total": 0, "categorias": set()}
        sectores[sec]["total"] += 1
        sectores[sec]["categorias"].add(getattr(s, "category", "general"))

    return {
        "sectores": {
            k: {"total": v["total"], "categorias": list(v["categorias"])}
            for k, v in sectores.items()
        }
    }


@app.get("/fabricadas")
def list_fabricated(_key: str = Depends(verify_key)):
    """Lista todas las skills generadas por el MetaFabricador."""
    from skills.fabricator import _load_generated
    fabricadas = _load_generated()
    return {
        "total": len(fabricadas),
        "skills": [
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "sector": s.get("sector"),
                "price_eur": s.get("price_eur"),
                "problema_que_resuelve": s.get("problema_que_resuelve"),
                "fabricado_en": s.get("fabricado_en"),
            }
            for s in fabricadas
        ],
    }
