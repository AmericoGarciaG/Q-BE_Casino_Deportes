from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.storage.database import get_db
from src.storage.repository import Repository
from src.core.portfolio import PortfolioEngine
from src.models.web_schemas import GeneratePortfolioRequest

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])

@router.post("/generate")
def generate_portfolio(req: GeneratePortfolioRequest, db: Session = Depends(get_db)):
    league = Repository.get_league_by_id(db, req.league_id)
    if not league:
        raise HTTPException(status_code=404, detail="Liga no encontrada")

    fixture_snap = Repository.get_latest_fixture(db, league.id)
    matches = fixture_snap.matches_json if fixture_snap else []

    portfolio_result = PortfolioEngine.allocate_portfolio(matches, req.bankroll)
    portfolio_result["league_name"] = league.name
    portfolio_result["matchday"] = req.matchday

    saved_record = Repository.save_portfolio(
        db=db,
        league_id=league.id,
        matchday=req.matchday,
        bankroll=req.bankroll,
        portfolio_data=portfolio_result
    )

    portfolio_result["portfolio_id"] = saved_record.id
    return portfolio_result
