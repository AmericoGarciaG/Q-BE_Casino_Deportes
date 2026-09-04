from typing import Tuple, List, Dict, Any
from tests.shield.abstract_test_LN_QBE_090_auditor import AbstractTestAuditor
from src.core.auditor import ShieldAuditorEngine

class TestLN_QBE_090_Concrete(AbstractTestAuditor):
    def audit_plan(self, plan_dict: Dict[str, Any], bankroll: float) -> Tuple[bool, List[str]]:
        return ShieldAuditorEngine.audit(plan_dict, bankroll)
