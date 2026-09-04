import os
from typing import List
from tests.shield.abstract_test_LN_QBE_002_gemini_rotator import AbstractTestGeminiRotator
from src.ingestion.providers.gemini_search_sensor import GeminiKeyRotator

class TestLN_QBE_002_GeminiRotator_Concrete(AbstractTestGeminiRotator):
    def setup_method(self):
        self.rotator = GeminiKeyRotator()

    def set_mock_env_keys(self, keys: List[str]) -> None:
        for i in range(1, 20):
            os.environ.pop(f"Gemini_API_4_QBE_{i:03d}", None)
        for idx, k in enumerate(keys, 1):
            os.environ[f"Gemini_API_4_QBE_{idx:03d}"] = k
        self.rotator.reset()

    def get_discovered_keys(self) -> List[str]:
        return self.rotator.get_discovered_keys()

    def trigger_rate_limit_rotation(self, cooldown_seconds: int = 60) -> bool:
        return self.rotator.rotate_on_rate_limit(cooldown_seconds)
