from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.storage.database import get_db
from src.storage.repository import Repository
from src.models.web_schemas import LeagueOut, LiveBoardResponse

router = APIRouter(prefix="/api/leagues", tags=["Leagues"])

@router.get("", response_model=list[LeagueOut])
def list_leagues(db: Session = Depends(get_db)):
    leagues = Repository.get_active_leagues(db)
    return leagues

@router.get("/{league_id}/live-board")
def get_live_board(league_id: int, db: Session = Depends(get_db)):
    league = Repository.get_league_by_id(db, league_id)
    if not league:
        raise HTTPException(status_code=404, detail="Liga no encontrada")

    standing_snap = Repository.get_latest_standing(db, league.id)
    fixture_snap = Repository.get_latest_fixture(db, league.id)

    return {
        "league": {
            "id": league.id,
            "name": league.name,
            "country": league.country,
            "flag": league.flag,
            "fotmob_id": league.fotmob_id,
            "caliente_url": league.caliente_url,
            "is_active": league.is_active
        },
        "standings": standing_snap.positions_json if standing_snap else [],
        "fixtures": fixture_snap.matches_json if fixture_snap else []
    }
