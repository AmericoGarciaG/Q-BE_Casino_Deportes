from typing import Dict, Any, List, Tuple
from tests.shield.abstract_test_LN_QBE_005_triage import AbstractTestTriage
from src.core.triage import evaluar_viabilidad_cuotas, procesar_triaje_partidos

class TestLN_QBE_005_Triage_Concrete(AbstractTestTriage):
    def evaluate_odds_triage(self, l: float, e: float, v: float, pa: bool = True) -> Tuple[bool, str]:
        return evaluar_viabilidad_cuotas(l, e, v, pa)

    def process_triage_matches(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        return procesar_triaje_partidos(matches)
