import abc
from typing import Dict, Any, List

class AbstractTestGeminiRotator(abc.ABC):
    @abc.abstractmethod
    def set_mock_env_keys(self, keys: List[str]) -> None:
        pass

    @abc.abstractmethod
    def get_discovered_keys(self) -> List[str]:
        pass

    @abc.abstractmethod
    def trigger_rate_limit_rotation(self, cooldown_seconds: int = 60) -> bool:
        pass

    def test_key_discovery_indexed_format(self):
        """[SHIELD-INVARIANTE] Descubrimiento de llaves indexadas."""
        self.set_mock_env_keys(["KEY_ALPHA", "KEY_BETA"])
        keys = self.get_discovered_keys()
        assert len(keys) == 2
        assert keys == ["KEY_ALPHA", "KEY_BETA"]
