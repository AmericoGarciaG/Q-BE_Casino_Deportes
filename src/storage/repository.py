from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from src.storage.database import SessionLocal
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


# ── [LN-QBE-093] / [ARCH-1.4.24] PUERTO DE PERSISTENCIA INYECTABLE ──
# [LN-QBE-017] Los sensores de ingesta pura reciben este callable por Inversión de
# Dependencias: la capacidad offline ante contingencia de red NO se deroga, pero deja
# de ejercerse mediante import estático dentro de `src/ingestion/providers/`.
def cargar_snapshot_certificado_posiciones(fotmob_id: int) -> Optional[List[Dict[str, Any]]]:
    """
    Retorna el último snapshot certificado de posiciones de la bóveda 3NF.

    Invariante de fidelidad: retorna `None` cuando no existe liga registrada o el snapshot
    no alcanza 18 clubes (CERO MOCKS: jamás se fabrican posiciones federativas).
    """
    with SessionLocal() as db:
        league = Repository.get_league_by_fotmob_id(db, fotmob_id)
        if not league:
            return None
        snapshot = Repository.get_latest_standing(db, league.id)
        if snapshot and snapshot.positions_json and len(snapshot.positions_json) >= 18:
            return snapshot.positions_json
    return None

