import abc
from typing import Dict, Any, List, Tuple

class AbstractTestTriage(abc.ABC):
    @abc.abstractmethod
    def evaluate_odds_triage(self, l: float, e: float, v: float, pa: bool = True) -> Tuple[bool, str]:
        pass

    @abc.abstractmethod
    def process_triage_matches(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        pass

    def test_viable_h1_route_approved(self):
        """[SHIELD] Cuotas con asimetría H1 deben ser aprobadas."""
        viable, motivo = self.evaluate_odds_triage(1.65, 4.33, 4.50, pa=True)
        assert viable is True
        assert "H1" in motivo or "D1" in motivo

    def test_coin_flip_odds_rejected(self):
        """[SHIELD] Volado plano 2.60 / 3.10 / 2.60 sin margen debe ser descartado."""
        viable, motivo = self.evaluate_odds_triage(2.60, 3.10, 2.60, pa=False)
        assert viable is False
        assert "volado" in motivo.lower() or "sin margen" in motivo.lower()

    def test_triage_preserves_tournament_identity(self):
        """[SHIELD] El triaje debe preservar la liga_torneo sin sobreescribir 'Liga MX' a ciegas."""
        raw = [{"id_partido": "M1", "local": "Toluca", "visitante": "León", "momios": {"L": 1.6, "E": 3.4, "V": 3.6}, "liga_torneo": "Leagues Cup 2026"}]
        res = self.process_triage_matches(raw)
        assert len(res["aprobados"]) == 1
        assert res["aprobados"][0]["liga_torneo"] == "Leagues Cup 2026"
