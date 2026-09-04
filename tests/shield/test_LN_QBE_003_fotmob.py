from typing import List, Dict, Any
from tests.shield.abstract_test_LN_QBE_003_fotmob import AbstractTestFotMob
from src.ingestion.providers.fotmob_provider import FotMobProvider

class TestLN_QBE_003_FotMob_Concrete(AbstractTestFotMob):
    def get_standings(self, league_id: int) -> List[Dict[str, Any]]:
        return FotMobProvider.obtener_tabla_posiciones(league_id)
