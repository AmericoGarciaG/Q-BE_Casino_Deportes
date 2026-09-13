from typing import List, Dict, Any
from fastapi.testclient import TestClient
from tests.shield.abstract_test_LN_QBE_020_temporal import AbstractTestTemporal
from src.core.temporal import TemporalDecayEngine
from src.models.raw_input import H2HMatchRaw
from src.models.analytics import H2HDecayResult
from src.web.app import app

class TestLN_QBE_020_Concrete(AbstractTestTemporal):
    def setup_method(self):
        self.client = TestClient(app)

    def run_decay(self, matches: List[H2HMatchRaw], local: str, vis: str, fav: str) -> H2HDecayResult:
        return TemporalDecayEngine.compute_decay(matches, local, vis, fav)

    def get_rendered_web_html(self) -> str:
        resp = self.client.get("/")
        assert resp.status_code == 200
        return resp.text

    def get_live_board_payload(self) -> Dict[str, Any]:
        resp = self.client.get("/api/leagues/262/live-board")
        assert resp.status_code == 200
        return resp.json()
