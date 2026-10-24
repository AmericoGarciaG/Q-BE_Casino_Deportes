# -*- coding: utf-8 -*-
"""Rutas de Ligas y Live Board — [ARCH-1.5.0 · Enmienda Nudo 2].

Toda lectura/escritura se canaliza por `PersistenceGateway`; el motor paralelo
`src/storage/database.py` queda fuera de este módulo. Los Jueces de The Shield
invocan estas funciones directamente con una sesión inyectada (`db=`), por lo que
se conserva ese puerto opcional sin acoplarse al motor erradicado.
"""
import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.storage.gateway import PersistenceGateway
from src.storage.models import League
from src.storage.sync_service import sync_league_live_board
from src.storage.crest_resolver import resolver_escudo_canonico
from src.models.web_schemas import LeagueOut, LiveBoardOut, MatchFixtureOut

router = APIRouter(prefix="/api/leagues", tags=["Leagues & Live Board"])

logger = logging.getLogger(__name__)

# Puerto opcional para invocación directa (The Shield). En HTTP se inyecta None y el
# acceso se resuelve por el Gateway: cero import del motor paralelo.
_PUERTO_SESION_OPCIONAL = Depends(lambda: None)


@router.get("", response_model=List[LeagueOut])
@router.get("/", response_model=List[LeagueOut], include_in_schema=False)
def get_leagues():
    """Retorna todas las ligas activas registradas en SQLite (lectura gobernada)."""
    with PersistenceGateway().read_session() as db:
        return db.query(League).filter(League.is_active == True).all()


# [ARCH-1.6.3] Orden de prioridad topológica inmutable
_ORDEN_TOPOLOGICO = {"EN_CURSO": 1, "PROGRAMADO": 2, "REPROGRAMADO": 3, "FINALIZADO": 4}


@router.get("/{league_id}/live-board", response_model=LiveBoardOut)
def get_live_board(
    league_id: int,
    jornada: Optional[int] = Query(default=None),
    force_refresh: bool = Query(default=False),
    db: Any = _PUERTO_SESION_OPCIONAL,
):
    target_jornada = jornada if isinstance(jornada, int) else None
    force_refresh_bool = force_refresh if isinstance(force_refresh, bool) else False
    sesion_inyectada = db if (db is not None and hasattr(db, "query")) else None
    try:
        if sesion_inyectada is not None:
            board_data = sync_league_live_board(
                league_id=league_id,
                db=sesion_inyectada,
                target_jornada=target_jornada,
                force_refresh=force_refresh_bool,
            )
        else:
            with PersistenceGateway().write_transaction() as session:
                board_data = sync_league_live_board(
                    league_id=league_id,
                    db=session,
                    target_jornada=target_jornada,
                    force_refresh=force_refresh_bool,
                )
        return board_data
    except Exception as e:
        logger.error(f"Error en get_live_board: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{league_id}/refresh-tabla")
def refresh_tabla_only(league_id: int, db: Any = _PUERTO_SESION_OPCIONAL):
    """
    [DESACOPLAMIENTO TOTAL] Actualiza exclusivamente la tabla de posiciones en SQLite
    sin tocar la cartelera ni invocar a Caliente.mx.
    """
    try:
        from src.storage.sync_service import sync_standings_only

        sesion_inyectada = db if (db is not None and hasattr(db, "query")) else None
        if sesion_inyectada is not None:
            standings = sync_standings_only(league_id, sesion_inyectada)
        else:
            with PersistenceGateway().write_transaction() as session:
                standings = sync_standings_only(league_id, session)
        return {"status": "SUCCESS", "standings": standings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refrescando tabla: {str(e)}")


@router.post("/{league_id}/refresh-momios")
def refresh_momios_only(league_id: int, db: Any = _PUERTO_SESION_OPCIONAL):
    """
    [DESACOPLAMIENTO TOTAL] Actualiza exclusivamente los momios de Caliente y cartelera
    sin tocar la tabla de posiciones ni consultar FotMob.
    """
    try:
        from src.storage.sync_service import sync_fixtures_only

        sesion_inyectada = db if (db is not None and hasattr(db, "query")) else None
        if sesion_inyectada is not None:
            fixtures = sync_fixtures_only(league_id, sesion_inyectada)
        else:
            with PersistenceGateway().write_transaction() as session:
                fixtures = sync_fixtures_only(league_id, session)
        return {"status": "SUCCESS", "fixtures": fixtures}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refrescando momios: {str(e)}")
