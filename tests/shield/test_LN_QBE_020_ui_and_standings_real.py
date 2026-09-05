"""
Kybern Industrial Governance — The Shield
Prueba Concreta: [DES-QBE-016 / ARCH-1.5.1 / LN-QBE-003] Verificación Real de UI y Tabla Apertura 2026
"""

from typing import Dict, Any
from fastapi.testclient import TestClient
from tests.shield.abstract_test_LN_QBE_020_ui_and_standings_real import AbstractTestUIAndStandingsReal
from src.web.app import app


class TestLN_QBE_020_UIAndStandingsReal_Concrete(AbstractTestUIAndStandingsReal):
    def setup_method(self):
        self.client = TestClient(app)

    def get_rendered_web_html(self) -> str:
        resp = self.client.get("/")
        assert resp.status_code == 200
        return resp.text

    def get_live_board_payload(self) -> Dict[str, Any]:
        resp = self.client.get("/api/leagues/262/live-board")
        assert resp.status_code == 200
        return resp.json()
