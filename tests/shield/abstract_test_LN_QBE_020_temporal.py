import abc
import pytest
from typing import List
from src.models.raw_input import H2HMatchRaw
from src.models.analytics import H2HDecayResult

class AbstractTestTemporal(abc.ABC):
    @abc.abstractmethod
    def run_decay(self, matches: List[H2HMatchRaw], local: str, vis: str, fav: str) -> H2HDecayResult:
        pass

    def test_h2h_simplex_conservation(self, sample_match_input):
        """[SHIELD-INVARIANTE #1] Suma de probabilidades H2H == 1.0000."""
        res = self.run_decay(sample_match_input.h2h_matches, "FC Juárez", "Club Pachuca", "Club Pachuca")
        assert abs((res.p_fav + res.p_emp + res.p_und) - 1.0) <= 0.0001

    def test_requires_exactly_5_matches(self):
        """[SHIELD-SAD-PATH] Menos de 5 partidos debe fallar."""
        with pytest.raises(ValueError, match="requiere exactamente 5 partidos"):
            self.run_decay([], "A", "B", "A")
