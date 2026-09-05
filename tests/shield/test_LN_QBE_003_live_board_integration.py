"""
Kybern Industrial Governance — The Shield
Prueba Concreta: [LN-QBE-003 / ARCH-1.6.0] Integración Live Board y Persistencia SQLite
"""

from typing import Dict, Any, List
from fastapi.testclient import TestClient
from tests.shield.abstract_test_LN_QBE_003_live_board_integration import AbstractTestLiveBoardIntegration
from src.web.app import app
from src.storage.database import SessionLocal
from src.storage.models import StandingSnapshot, FixtureSnapshot, League
from src.storage.seeder import seed_initial_leagues


class TestLN_QBE_003_LiveBoard_Concrete(AbstractTestLiveBoardIntegration):
    def setup_method(self):
        seed_initial_leagues()

    @property
    def client(self) -> TestClient:
        return TestClient(app)

    def fetch_active_leagues_api(self) -> List[Dict[str, Any]]:
        resp = self.client.get("/api/leagues")
        assert resp.status_code == 200, f"Error en /api/leagues: {resp.text}"
        return resp.json()

    def fetch_live_board_api(self, league_id: int) -> Dict[str, Any]:
        resp = self.client.get(f"/api/leagues/{league_id}/live-board")
        assert resp.status_code == 200, f"Error en /api/leagues/{league_id}/live-board: {resp.text}"
        return resp.json()

    def check_db_snapshots_exist(self, league_id: int) -> bool:
        db = SessionLocal()
        try:
            league = db.query(League).filter(League.fotmob_id == league_id).first()
            if not league:
                return False
            has_standing = db.query(StandingSnapshot).filter(StandingSnapshot.league_id == league.id).count() > 0
            has_fixture = db.query(FixtureSnapshot).filter(FixtureSnapshot.league_id == league.id).count() > 0
            return has_standing and has_fixture
        finally:
            db.close()
