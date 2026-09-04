import abc
from typing import List, Dict, Any

class AbstractTestFotMob(abc.ABC):
    @abc.abstractmethod
    def get_standings(self, league_id: int) -> List[Dict[str, Any]]:
        pass

    def test_fotmob_standings_has_18_teams_and_xg(self):
        """[LN-QBE-003] La tabla de FotMob debe retornar los 18 clubes con puntos y xG."""
        standings = self.get_standings(262)
        assert len(standings) >= 18
        assert all(("equipo" in t or "name" in t) and ("puntos" in t or "pts" in t) for t in standings)
