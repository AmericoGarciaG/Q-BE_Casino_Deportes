from tests.shield.abstract_test_LN_QBE_030_metrics import AbstractTestMetrics
from src.core.metrics import SyntheticMetricsEngine
from src.models.analytics import SyntheticMetricsResult

class TestLN_QBE_030_Concrete(AbstractTestMetrics):
    def run_metrics(self, poss_l, sot_l, sota_l, gf_l, poss_v, sot_v, sota_v, gf_v) -> SyntheticMetricsResult:
        return SyntheticMetricsEngine.compute_all(poss_l, sot_l, sota_l, gf_l, poss_v, sot_v, sota_v, gf_v)
