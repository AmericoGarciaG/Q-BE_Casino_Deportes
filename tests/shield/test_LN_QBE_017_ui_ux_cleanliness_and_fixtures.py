"""
Kybern Industrial Governance — The Shield
Prueba Concreta: [LN-QBE-017 / ARCH-1.6.1 / DES-QBE-015 / DES-QBE-016]
Auditoría de Usabilidad, Cero Fugas Técnicas y Cartelera
"""
from typing import Dict, Any
from fastapi.testclient import TestClient

from tests.shield.abstract_test_LN_QBE_017_ui_ux_cleanliness_and_fixtures import (
    AbstractTestUIUXCleanlinessAndFixtures,
)
from src.web.app import app
from src.storage.seeder import seed_initial_leagues


class TestLN_QBE_017_UIUXCleanliness_Concrete(AbstractTestUIUXCleanlinessAndFixtures):
    def setup_method(self):
        seed_initial_leagues()

    @property
    def client(self) -> TestClient:
        return TestClient(app)

    def get_rendered_web_html(self) -> str:
        resp = self.client.get("/")
        assert resp.status_code == 200, f"Error al renderizar HTML raíz '/': {resp.text}"
        return resp.text

    def get_live_board_payload(self) -> Dict[str, Any]:
        resp = self.client.get("/api/leagues/262/live-board")
        assert resp.status_code == 200, f"Error al consultar live-board: {resp.text}"
        return resp.json()
