import abc
from typing import Dict, Any

class AbstractTestEvaluator(abc.ABC):
    @abc.abstractmethod
    def evaluate_all(self, **kwargs) -> Dict[str, Dict[str, Any]]:
        pass

    def test_d1_no_70_percent_fixed_threshold(self):
        """[ALGO-PROTECTED] Favorito con 65% de probabilidad y cuota de 1.60 debe activar D1."""
        evals = self.evaluate_all(
            p_fav=0.65, p_emp=0.25, p_und=0.10,
            o_fav=1.60, o_emp=3.50, o_und=5.00,
            theta_fav_h1=0.40, theta_emp_h2=0.30, theta_emp_pa_h2_plus=0.25, theta_und_r1=0.80,
            momio_sintetico_x2=2.0, phi_lead2=0.50, psi_ruina=0.08, d_mkt=0.96, pago_anticipado=True
        )
        assert evals["QBE_D1"]["viable"] is True
        d1_plus = evals.get("QBE_D1_plus") or evals.get("QBE_D1+")
        assert d1_plus["viable"] is True

    def test_triple_candado_rejects_solid_favorite(self):
        """[BIZ-LOGIC] Si el favorito tiene P_Fav > 48%, la Familia R debe ser vetada."""
        evals = self.evaluate_all(
            p_fav=0.55, p_emp=0.25, p_und=0.20,
            o_fav=1.60, o_emp=3.50, o_und=5.00,
            theta_fav_h1=0.40, theta_emp_h2=0.30, theta_emp_pa_h2_plus=0.25, theta_und_r1=0.80,
            momio_sintetico_x2=2.0, phi_lead2=0.50, psi_ruina=0.18, d_mkt=1.10, pago_anticipado=True
        )
        assert evals["QBE_R1"]["viable"] is False
        assert evals["QBE_R2"]["viable"] is False
