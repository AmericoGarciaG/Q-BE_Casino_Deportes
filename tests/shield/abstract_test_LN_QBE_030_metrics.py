import abc
from src.models.analytics import SyntheticMetricsResult

class AbstractTestMetrics(abc.ABC):
    @abc.abstractmethod
    def run_metrics(self, poss_l, sot_l, sota_l, gf_l, poss_v, sot_v, sota_v, gf_v) -> SyntheticMetricsResult:
        pass

    def test_fcf_and_eatt_clamping_boundaries(self):
        """[ALGO-PROTECTED] Los factores FCF y E_att deben respetar estrictamente los límites de clamp."""
        res = self.run_metrics(poss_l=90.0, sot_l=15.0, sota_l=0.0, gf_l=5.0, poss_v=10.0, sot_v=0.0, sota_v=15.0, gf_v=0.0)
        assert res.fcf_local <= 1.35
        assert res.e_att_local <= 1.40
        assert res.fcf_vis >= 0.65
        assert res.e_att_vis >= 0.60
