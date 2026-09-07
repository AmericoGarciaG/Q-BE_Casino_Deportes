from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.storage.database import get_db
from src.storage.models import League
from src.storage.sync_service import sync_league_live_board
from src.storage.crest_resolver import resolver_escudo_canonico
from src.models.web_schemas import LeagueOut, LiveBoardOut

router = APIRouter(prefix="/api/leagues", tags=["Leagues & Live Board"])


@router.get("", response_model=List[LeagueOut])
@router.get("/", response_model=List[LeagueOut], include_in_schema=False)
def get_leagues(db: Session = Depends(get_db)):
    """Retorna todas las ligas activas registradas en SQLite."""
    leagues = db.query(League).filter(League.is_active == True).all()
    return leagues


@router.get("/{league_id}/live-board", response_model=LiveBoardOut)
def get_live_board(league_id: int, db: Session = Depends(get_db)):
    """Extrae y sincroniza la tabla de 18 clubes de FotMob y la cartelera viva con SQLite."""
    try:
        board_data = sync_league_live_board(league_id, db)
        standings = board_data.get("standings", [])
        for row in standings:
            equipo = row.get("equipo", "")
            fotmob_id = row.get("fotmob_id")
            row["escudo_url"] = resolver_escudo_canonico(equipo, fotmob_id=fotmob_id, db=db)
        return board_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

