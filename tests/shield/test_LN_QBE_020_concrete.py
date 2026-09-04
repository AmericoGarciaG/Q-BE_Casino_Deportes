from typing import List
from tests.shield.abstract_test_LN_QBE_020_temporal import AbstractTestTemporal
from src.core.temporal import TemporalDecayEngine
from src.models.raw_input import H2HMatchRaw
from src.models.analytics import H2HDecayResult

class TestLN_QBE_020_Concrete(AbstractTestTemporal):
    def run_decay(self, matches: List[H2HMatchRaw], local: str, vis: str, fav: str) -> H2HDecayResult:
        return TemporalDecayEngine.compute_decay(matches, local, vis, fav)
