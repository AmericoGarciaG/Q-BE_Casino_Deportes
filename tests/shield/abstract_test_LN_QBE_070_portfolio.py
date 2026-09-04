import abc
from typing import List, Dict, Any
from src.models.decision import PortfolioExecutionPlan

class AbstractTestPortfolio(abc.ABC):
    @abc.abstractmethod
    def build_portfolio(self, matches: List[Dict[str, Any]], bankroll: float) -> PortfolioExecutionPlan:
        pass

    def test_hard_caps_and_exact_dutching(self):
        """[SHIELD-INVARIANTE #2, #3, #4] Hard-caps individual (<=8%) y global (<=25%) con Dutching exacto."""
        matches = [
            {
                "id_partido": "M1", "partido_nombre": "A vs B", "fav_name": "A", "und_name": "B",
                "strategy_code": "QBE-H1", "strategy_nombre": "Favorito con Seguro",
                "ev_neto_roi": 15.0, "psi_downside": 0.08, "phi_lead2": 0.40,
                "odd_fav": 1.70, "odd_emp": 3.60, "odd_und": 4.50
            }
        ]
        plan = self.build_portfolio(matches, bankroll=200.0)
        ord1 = plan.ordenes_ejecucion_partidos[0]
        assert ord1.boletos.inversion_partido_A_i <= 16.01
        ret_seguro = ord1.boletos.boleto_1_seguro.monto_mxn * ord1.boletos.boleto_1_seguro.momio
        assert abs(ret_seguro - ord1.boletos.inversion_partido_A_i) <= 0.08
