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

    def test_pachuca_standings_matches_live_fotmob(self):
        """[SHIELD-INVARIANTE] Pachuca debe tener 8 puntos y 7 partidos jugados tras J7."""
        standings = self.get_live_standings_from_fotmob(262)
        assert len(standings) == 18

        pachuca = next((t for t in standings if "PACHUCA" in t["equipo"].upper()), None)
        assert pachuca is not None, "Club Pachuca no encontrado en la tabla."
        assert pachuca["puntos"] == 8, f"Pachuca debe tener 8 puntos, se encontró: {pachuca['puntos']}."
        assert pachuca["pj"] == 7, f"Pachuca debe tener 7 partidos jugados, se encontró: {pachuca['pj']}."
