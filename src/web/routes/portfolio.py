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
from src.pipeline.adapter import construir_master_table_snapshot, hidratar_partidos_cuantitativos
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

    # 2. Leer snapshots más recientes de SQLite
    fixture_snap = db.query(FixtureSnapshot).filter(
        FixtureSnapshot.league_id == league.id
    ).order_by(FixtureSnapshot.updated_at.desc()).first()

    standing_snap = db.query(StandingSnapshot).filter(
        StandingSnapshot.league_id == league.id
    ).order_by(StandingSnapshot.captured_at.desc()).first()

    if not fixture_snap or not fixture_snap.matches_json:
        raise HTTPException(status_code=400, detail="No hay cartelera activa registrada en la base de datos.")

    if not standing_snap or not standing_snap.positions_json:
        raise HTTPException(status_code=400, detail="No hay tabla de posiciones registrada en la base de datos.")

    # 3. Filtrar partidos seleccionados por el usuario
    todos_fixtures = fixture_snap.matches_json
    if req.selected_match_ids:
        seleccionados = [f for f in todos_fixtures if f.get("id_partido") in req.selected_match_ids]
    else:
        # Si no envió IDs específicos, tomar todos los operables de la ventana activa
        seleccionados = [f for f in todos_fixtures if f.get("disponible_para_seleccion") is not False]

    if not seleccionados:
        raise HTTPException(status_code=400, detail="Ninguno de los partidos seleccionados es operable para inversión.")

    jornada_activa = fixture_snap.matchday or 8

    # 4. Construir contratos matemáticos vía Adaptador
    master_table = construir_master_table_snapshot(standing_snap.positions_json, jornada=jornada_activa)
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
