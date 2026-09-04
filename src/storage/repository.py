from typing import List, Optional
from sqlalchemy.orm import Session
from src.storage.models import League, StandingSnapshot, FixtureSnapshot, PortfolioRecord

class Repository:
    @staticmethod
    def get_active_leagues(db: Session) -> List[League]:
        return db.query(League).filter(League.is_active == True).all()

    @staticmethod
    def get_league_by_id(db: Session, league_id: int) -> Optional[League]:
        return db.query(League).filter(League.id == league_id).first()

    @staticmethod
    def get_league_by_fotmob_id(db: Session, fotmob_id: int) -> Optional[League]:
        return db.query(League).filter(League.fotmob_id == fotmob_id).first()

    @staticmethod
    def get_latest_standing(db: Session, league_id: int) -> Optional[StandingSnapshot]:
        return (
            db.query(StandingSnapshot)
            .filter(StandingSnapshot.league_id == league_id)
            .order_by(StandingSnapshot.captured_at.desc())
            .first()
        )

    @staticmethod
    def get_latest_fixture(db: Session, league_id: int) -> Optional[FixtureSnapshot]:
        return (
            db.query(FixtureSnapshot)
            .filter(FixtureSnapshot.league_id == league_id)
            .order_by(FixtureSnapshot.updated_at.desc())
            .first()
        )

    @staticmethod
    def save_portfolio(db: Session, league_id: int, matchday: int, bankroll: float, portfolio_data: dict) -> PortfolioRecord:
        record = PortfolioRecord(
            league_id=league_id,
            matchday=matchday,
            bankroll=bankroll,
            portfolio_json=portfolio_data
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
