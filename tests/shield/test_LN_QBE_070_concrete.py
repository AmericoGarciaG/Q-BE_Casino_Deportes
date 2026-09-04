from typing import List, Dict, Any
from tests.shield.abstract_test_LN_QBE_070_portfolio import AbstractTestPortfolio
from src.core.portfolio import PortfolioEngine
from src.models.decision import PortfolioExecutionPlan

class TestLN_QBE_070_Concrete(AbstractTestPortfolio):
    def build_portfolio(self, matches: List[Dict[str, Any]], bankroll: float) -> PortfolioExecutionPlan:
        return PortfolioEngine.build_plan(matches, bankroll=bankroll)
