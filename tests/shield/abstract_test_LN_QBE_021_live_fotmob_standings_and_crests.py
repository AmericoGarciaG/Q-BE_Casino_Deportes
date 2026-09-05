"""
Kybern Industrial Governance — The Shield
Juez Inmutable: [LN-QBE-003 / ARCH-1.5.1] Validación Dinámica de Tabla FotMob y Escudos Reales
ID de Prueba: SHIELD-TEST-LN-QBE-021-LIVE-CRESTS-AND-PACHUCA
"""
import abc
from typing import Dict, Any, List


class AbstractTestLiveFotMobStandingsAndCrests(abc.ABC):
    """
    Juez Abstracto que audita:
    1. Que Pachuca esté en la posición #11 con 8 puntos (partido adelantado reflejado).
    2. Que los 18 clubes tengan URLs de escudos reales obtenidas directamente del ID de FotMob.
    3. Que ningún club tenga el escudo vacío o roto.
    """

    @abc.abstractmethod
    def get_live_standings_from_fotmob(self, league_id: int = 262) -> List[Dict[str, Any]]:
        pass

    def test_pachuca_standings_matches_live_fotmob(self):
        """[SHIELD-INVARIANTE] Pachuca debe tener 8 puntos y estar en la posición #11."""
        standings = self.get_live_standings_from_fotmob(262)
        assert len(standings) == 18
        
        pachuca = next((t for t in standings if "PACHUCA" in t["equipo"].upper()), None)
        assert pachuca is not None, "Club Pachuca no encontrado en la tabla."
        assert pachuca["puntos"] == 8, f"Pachuca debe tener 8 puntos, se encontró: {pachuca['puntos']}."
        assert pachuca["pos"] == 11, f"Pachuca debe estar en la posición #11, se encontró: #{pachuca['pos']}."
        assert pachuca["pj"] == 7, f"Pachuca debe tener 7 partidos jugados, se encontró: {pachuca['pj']}."

    def test_all_18_teams_have_valid_dynamic_crests(self):
        """[SHIELD-INVARIANTE] Todos los 18 clubes deben tener URLs de escudos reales de FotMob CDN."""
        standings = self.get_live_standings_from_fotmob(262)
        for t in standings:
            assert "escudo_url" in t and t["escudo_url"], f"Falta escudo_url para {t['equipo']}."
            assert t["escudo_url"].startswith("https://images.fotmob.com/image_resources/logo/teamlogo/"), (
                f"URL de escudo inválida para {t['equipo']}: {t['escudo_url']}"
            )
