"""
Kybern Industrial Governance — The Shield
Prueba Concreta: [LN-QBE-003 / ARCH-1.5.1] Validación Dinámica de Tabla FotMob y Escudos Reales
ID de Prueba: SHIELD-TEST-LN-QBE-021-LIVE-CRESTS-AND-PACHUCA
"""

from typing import List, Dict, Any
from tests.shield.abstract_test_LN_QBE_021_live_fotmob_standings_and_crests import (
    AbstractTestLiveFotMobStandingsAndCrests
)
from src.ingestion.providers.fotmob_provider import FotMobProvider


class TestLN_QBE_021_LiveFotMobStandingsAndCrests_Concrete(AbstractTestLiveFotMobStandingsAndCrests):
    def get_live_standings_from_fotmob(self, league_id: int = 262) -> List[Dict[str, Any]]:
        return FotMobProvider.obtener_tabla_posiciones(league_id)
