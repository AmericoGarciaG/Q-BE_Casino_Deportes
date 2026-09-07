"""
Kybern Industrial — [ARCH-1.5.2] Router Administrativo de Curación HITL
Controlador de endpoints /api/admin/catalogs/*

Endpoints:
  POST /api/admin/catalogs/discover   — Inicia prospección agéntica
  GET  /api/admin/catalogs/staging    — Retorna candidatos en staging
  POST /api/admin/catalogs/commit     — Sella el catálogo confirmado en SQLite

[AISLAMIENTO DE PRODUCCIÓN]: Ningún candidato en staging es visible en
/api/leagues/{id}/live-board hasta el commit administrativo. [LN-QBE-015]
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from pydantic import BaseModel

from src.storage.database import get_db
from src.storage.curation_service import (
    ejecutar_prospeccion_liga,
    obtener_staging_liga,
    sellar_catalogo_en_db,
)

router = APIRouter(prefix="/api/admin/catalogs", tags=["Admin Curation HITL"])


class CommitCatalogRequest(BaseModel):
    """Contrato de entrada para el sellado de catálogo [ARCH-1.5.2]."""
    league_id: int
    approved_teams: List[Dict[str, Any]]


@router.post("/discover")
def discover_catalogs(league_id: int = Query(default=262)) -> Dict[str, Any]:
    """
    [ARCH-1.5.2 — Endpoint 1]
    Inicia la prospección agéntica y prepara el staging temporal de clubes candidatos.
    El agente curador (Catálogo Canónico v1.0) detecta nombre oficial, slug, estadio,
    ciudad, aliases y URL de escudo en alta resolución.
    """
    try:
        return ejecutar_prospeccion_liga(league_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/staging")
def get_staging_catalogs(league_id: int = Query(default=262)) -> List[Dict[str, Any]]:
    """
    [ARCH-1.5.2 — Endpoint 2]
    Retorna los clubes en prospección temporal para revisión e inspección visual HITL.
    Si el staging no existe, auto-ejecuta la prospección primero.
    """
    try:
        return obtener_staging_liga(league_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/commit")
def commit_catalogs(
    payload: CommitCatalogRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    [ARCH-1.5.2 — Endpoint 3]
    Sella los clubes confirmados por el Director Humano:
    - Descarga física de escudos a src/web/static/img/crests/{slug}.png
    - Verificación SHA256 de integridad de activos
    - Inserción/actualización inmutable en tabla `teams` de SQLite
    """
    try:
        return sellar_catalogo_en_db(payload.league_id, payload.approved_teams, db)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
