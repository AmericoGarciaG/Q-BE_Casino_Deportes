from typing import Dict, Any
from tests.shield.abstract_test_LN_QBE_060_evaluator import AbstractTestEvaluator
from src.core.evaluator import StrategyEvaluatorEngine

class TestLN_QBE_060_Concrete(AbstractTestEvaluator):
    def evaluate_all(self, **kwargs) -> Dict[str, Dict[str, Any]]:
        return StrategyEvaluatorEngine.evaluate_all(**kwargs)
