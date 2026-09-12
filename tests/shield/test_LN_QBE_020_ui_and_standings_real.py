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

    def test_standings_apertura_2026_exact_leader_and_subleader(self):
        """[SHIELD-INVARIANTE #6] La tabla refleja la conclusión de la Jornada 7: América 16 pts, Chivas sublíder 14 pts."""
        board = self.get_live_board_payload()
        standings = board.get("standings", [])
        assert len(standings) == 18, "La tabla debe tener 18 clubes."

        p1 = standings[0]
        assert "AMÉRICA" in p1["equipo"].upper(), f"El líder debe ser América, se encontró: {p1['equipo']}."
        assert p1["puntos"] == 16, f"El líder debe tener 16 puntos, se encontró: {p1['puntos']}."
        assert p1["dif"] == 10, f"Diferencia de goles de América debe ser +10, se encontró: {p1['dif']}."

        p2 = standings[1]
        assert "CHIVAS" in p2["equipo"].upper() or "GUADALAJARA" in p2["equipo"].upper(), f"El sublíder debe ser Chivas tras J7, se encontró: {p2['equipo']}."
        assert p2["puntos"] >= 14, f"Chivas debe tener >= 14 puntos, se encontró: {p2['puntos']}."
