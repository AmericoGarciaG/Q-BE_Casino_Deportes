# -*- coding: utf-8 -*-
"""
Kybern Industrial — Portfolio REST Router [ARCH-PILLAR]
Endpoint POST /api/portfolio/generate conectado al motor determinista QBEPipelineEngine.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from src.storage.database import get_db
from src.storage.models import League, StandingSnapshot, FixtureSnapshot, PortfolioRecord
from src.models.web_schemas import GeneratePortfolioRequest
from src.pipeline.adapter import construir_master_table_snapshot, construir_master_table_desde_db, hidratar_partidos_cuantitativos, obtener_fixtures_multiversal
from src.pipeline.engine import QBEPipelineEngine


router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.post("/generate")
def generate_portfolio(req: GeneratePortfolioRequest, db: Session = Depends(get_db)):
    """
    [FASE 3 SOBERANA]
    Recibe la selección de partidos de la cartelera, los hidrata con las cuotas reales de Caliente
    y la tabla oficial de ligamx.net, ejecuta el pipeline cuantitativo y retorna el plan consolidado.
    """
    # 1. Validar Liga
    league = db.query(League).filter(
        (League.id == req.league_id) | (League.fotmob_id == req.league_id)
    ).first()
    if not league:
        raise HTTPException(status_code=404, detail=f"Liga con ID {req.league_id} no encontrada.")

    # 2. [ARCH-1.6.8] Recuperación Multiversal de Fixtures (Multi-Jornada)
    fixtures_pool = obtener_fixtures_multiversal(db, league.id)

    standing_snap = db.query(StandingSnapshot).filter(
        StandingSnapshot.league_id == league.id
    ).order_by(StandingSnapshot.captured_at.desc()).first()

    if not fixtures_pool:
        raise HTTPException(status_code=400, detail="No hay cartelera activa registrada en la base de datos.")

    if not standing_snap or not standing_snap.positions_json:
        raise HTTPException(status_code=400, detail="No hay tabla de posiciones registrada en la base de datos.")

    # 3. Filtrar partidos seleccionados por el usuario desde el pool multiversal
    if req.selected_match_ids:
        seleccionados = []
        for match_id in req.selected_match_ids:
            fx = fixtures_pool.get(match_id)
            if not fx:
                continue
            momios = fx.get("momios")
            if not momios or not momios.get("L"):
                continue
            if fx.get("estado") == "FINALIZADO":
                continue
            seleccionados.append(fx)
    else:
        # Si no envió IDs específicos, tomar todos los operables del pool multiversal
        seleccionados = [
            fx for fx in fixtures_pool.values()
            if fx.get("disponible_para_seleccion") is not False
            and fx.get("estado") != "FINALIZADO"
            and fx.get("momios")
            and fx.get("momios", {}).get("L")
        ]

    if not seleccionados:
        raise HTTPException(status_code=400, detail="Ninguno de los partidos seleccionados es operable para inversión.")

    last_fix_snap = db.query(FixtureSnapshot).filter(
        FixtureSnapshot.league_id == league.id
    ).order_by(FixtureSnapshot.updated_at.desc()).first()
    jornada_activa = (last_fix_snap.matchday if last_fix_snap else 8) or 8


    # 4. Construir contratos matemáticos vía Adaptador
    master_table = construir_master_table_desde_db(db, league.id, jornada_activa)
    raw_matches = hidratar_partidos_cuantitativos(seleccionados, master_table, jornada=jornada_activa)

    # 5. Ejecutar Motor Cuantitativo E2E (Poisson 6x6, Kelly, Dutching V=0, The Shield Gate)
    try:
        plan, consolidated_payload = QBEPipelineEngine.run_full(
            matches=raw_matches,
            master_table=master_table,
            bankroll=req.bankroll,
            mode=req.mode
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error en motor cuantitativo: {str(exc)}")

    # 6. Persistir en SQLite (Ledger Histórico para PM-FACE)
    record = PortfolioRecord(
        league_id=league.id,
        matchday=jornada_activa,
        bankroll=req.bankroll,
        portfolio_json=consolidated_payload
    )
    db.add(record)
    db.commit()

    consolidated_payload["portfolio_id"] = record.id
    return consolidated_payload


import logging
from typing import Dict, Any
from pydantic import BaseModel

logger = logging.getLogger("PortfolioRouter")

class MatchThesisRequest(BaseModel):
    partido_id: str
    partido_data: Dict[str, Any]


@router.post("/match-thesis")
def generate_match_thesis_endpoint(req: MatchThesisRequest):
    """
    [ARCH-1.3.4 / ARCH-1.6.10] Invocación real de Gemini 3.6 Flash bajo demanda.
    """
    logger.info(f"🧠 [ON-DEMAND] Redactando Tesis con Gemini para partido {req.partido_id}...")
    print(f"🧠 [ON-DEMAND] Redactando Tesis con Gemini para partido {req.partido_id}...")
    from src.services.gemini_gateway import GeminiCognitiveGateway
    gateway = GeminiCognitiveGateway()
    tesis_html = gateway.generate_thesis(req.partido_data)
    return {"partido_id": req.partido_id, "tesis_html": tesis_html}
