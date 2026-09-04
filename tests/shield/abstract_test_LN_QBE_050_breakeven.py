import abc
from src.models.analytics import BreakevenThresholdsResult

class AbstractTestBreakeven(abc.ABC):
    @abc.abstractmethod
    def compute_thresholds(self, odd_fav, odd_emp, odd_und, psi_ruina, phi_lead2, p_hib_fav) -> BreakevenThresholdsResult:
        pass

    def test_breakeven_clamping_and_negative_denominators(self):
        """[ALGO-PROTECTED] Umbrales theta* acotados strictly en [0.0, 1.0] ante cuotas sin margen."""
        res = self.compute_thresholds(odd_fav=1.10, odd_emp=2.00, odd_und=9.00, psi_ruina=0.10, phi_lead2=0.50, p_hib_fav=0.85)
        assert 0.0 <= res.theta_fav_h1 <= 1.0
        assert 0.0 <= res.theta_emp_h2 <= 1.0
        assert 0.0 <= res.theta_emp_pa_h2_plus <= 1.0
        assert 0.0 <= res.theta_und_r1 <= 1.0
