from tests.shield.abstract_test_LN_QBE_010_sanitizer import AbstractTestSanitizer
from src.core.sanitizer import SanitizerEngine
from src.models.raw_input import RawMatchInput, MasterTableSnapshot

class TestLN_QBE_010_Concrete(AbstractTestSanitizer):
    def run_sanitizer(self, match_input: RawMatchInput, master_table: MasterTableSnapshot) -> bool:
        return SanitizerEngine.audit_and_sanitize(match_input, master_table)
