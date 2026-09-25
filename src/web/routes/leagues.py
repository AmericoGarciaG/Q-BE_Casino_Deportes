from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from src.storage.database import get_db
from src.storage.models import League
from src.storage.sync_service import sync_league_live_board
from src.storage.crest_resolver import resolver_escudo_canonico
from src.models.web_schemas import LeagueOut, LiveBoardOut, MatchFixtureOut

router = APIRouter(prefix="/api/leagues", tags=["Leagues & Live Board"])


@router.get("", response_model=List[LeagueOut])
@router.get("/", response_model=List[LeagueOut], include_in_schema=False)
def get_leagues(db: Session = Depends(get_db)):
    """Retorna todas las ligas activas registradas en SQLite."""
    leagues = db.query(League).filter(League.is_active == True).all()
    return leagues


# [ARCH-1.6.3] Orden de prioridad topológica inmutable
_ORDEN_TOPOLOGICO = {"EN_CURSO": 1, "PROGRAMADO": 2, "REPROGRAMADO": 3, "FINALIZADO": 4}


import logging

logger = logging.getLogger(__name__)


@router.get("/{league_id}/live-board", response_model=LiveBoardOut)
def get_live_board(
    league_id: int,
    jornada: Optional[int] = Query(default=None),
    force_refresh: bool = Query(default=False),
    db: Session = Depends(get_db)
):
    target_jornada = jornada if isinstance(jornada, int) else None
    force_refresh_bool = force_refresh if isinstance(force_refresh, bool) else False
    try:
        board_data = sync_league_live_board(
            league_id=league_id,
            db=db,
            target_jornada=target_jornada,
            force_refresh=force_refresh_bool
        )
        return board_data
    except Exception as e:
        logger.error(f"Error en get_live_board: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{league_id}/refresh-tabla")
def refresh_tabla_only(league_id: int, db: Session = Depends(get_db)):
    """
    [DESACOPLAMIENTO TOTAL] Actualiza exclusivamente la tabla de posiciones en SQLite
    sin tocar la cartelera ni invocar a Caliente.mx.
    """
    try:
        from src.storage.sync_service import sync_standings_only
        standings = sync_standings_only(league_id, db)
        return {"status": "SUCCESS", "standings": standings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refrescando tabla: {str(e)}")


@router.post("/{league_id}/refresh-momios")
def refresh_momios_only(league_id: int, db: Session = Depends(get_db)):
    """
    [DESACOPLAMIENTO TOTAL] Actualiza exclusivamente los momios de Caliente y cartelera
    sin tocar la tabla de posiciones ni consultar FotMob.
    """
    try:
        from src.storage.sync_service import sync_fixtures_only
        fixtures = sync_fixtures_only(league_id, db)
        return {"status": "SUCCESS", "fixtures": fixtures}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refrescando momios: {str(e)}")

