"""
Kybern Industrial Governance — The Shield
Prueba Concreta: [ARCH-1.5.1 / ARCH-1.6.2 / LN-QBE-003]
Catálogo de Equipos, Escudos y Ciclo de Vida de Cuotas
"""
from typing import Dict, Any, List
from sqlalchemy import text
from fastapi.testclient import TestClient

from tests.shield.abstract_test_LN_QBE_019_teams_catalog_and_odds_status import (
    AbstractTestTeamsCatalogAndOddsStatus,
)
from src.web.app import app
from src.storage.database import SessionLocal
from src.storage.models import League
from src.storage.seeder import seed_initial_leagues


class TestLN_QBE_019_TeamsCatalogAndOddsStatus_Concrete(
    AbstractTestTeamsCatalogAndOddsStatus
):
    def setup_method(self):
        seed_initial_leagues()

    @property
    def client(self) -> TestClient:
        return TestClient(app)

    def get_teams_from_db(self, league_id: int = 262) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            league = db.query(League).filter((League.fotmob_id == league_id) | (League.id == league_id)).first()
            lid = league.id if league else league_id
            result = db.execute(
                text(
                    "SELECT id, league_id, fotmob_team_id, name, short_name, canonical_slug, crest_url FROM teams WHERE league_id = :lid"
                ),
                {"lid": lid},
            )
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception:
            return []
        finally:
            db.close()

    def get_live_board_payload(self, league_id: int = 262) -> Dict[str, Any]:
        resp = self.client.get(f"/api/leagues/{league_id}/live-board")
        assert resp.status_code == 200, f"Error al consultar live-board: {resp.text}"
        return resp.json()
