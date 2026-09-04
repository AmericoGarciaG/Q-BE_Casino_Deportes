from tests.shield.abstract_test_LN_QBE_050_breakeven import AbstractTestBreakeven
from src.core.breakeven import BreakevenEngine
from src.models.analytics import BreakevenThresholdsResult

class TestLN_QBE_050_Concrete(AbstractTestBreakeven):
    def compute_thresholds(self, odd_fav, odd_emp, odd_und, psi_ruina, phi_lead2, p_hib_fav) -> BreakevenThresholdsResult:
        return BreakevenEngine.compute_thresholds(odd_fav, odd_emp, odd_und, psi_ruina, phi_lead2, p_hib_fav)
