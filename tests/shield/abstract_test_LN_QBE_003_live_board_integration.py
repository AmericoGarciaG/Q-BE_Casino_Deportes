"""
Kybern Industrial Governance — Twin-Test Protocol
Juez Inmutable: [LN-QBE-003 / ARCH-1.6.0] Integración Live Board, Persistencia SQLite y 3 Pestañas
ID de Prueba: SHIELD-TEST-LN-QBE-003-LIVE-BOARD
"""
import abc
from typing import Dict, Any, List


class AbstractTestLiveBoardIntegration(abc.ABC):
    """
    Juez Abstracto que audita:
    1. Endpoint /api/leagues consulta SQLite y retorna la Liga MX (ID 262) precargada por el seeder.
    2. Endpoint /api/leagues/262/live-board retorna exactamente 18 clubes completos en standings.
    3. Cada club contiene los datos para las 3 pestañas: General (G,E,P,GF,GC), Forma (5 W/D/L) y xG Opta.
    4. La cartelera contiene partidos con momios 1X2 válidos y soporte para checkboxes de selección.
    5. Los snapshots quedan físicamente persistidos en SQLite (data/qbe_database.db).
    """

    @abc.abstractmethod
    def fetch_active_leagues_api(self) -> List[Dict[str, Any]]:
        """Debe invocar GET /api/leagues y retornar la lista."""
        pass

    @abc.abstractmethod
    def fetch_live_board_api(self, league_id: int) -> Dict[str, Any]:
        """Debe invocar GET /api/leagues/{id}/live-board y retornar el payload."""
        pass

    @abc.abstractmethod
    def check_db_snapshots_exist(self, league_id: int) -> bool:
        """Debe verificar en SQLite que existan registros en standings_snapshots y fixtures_snapshots."""
        pass

    # ══════════════════════════════════════════════════════════════════
    # ASERCIONES INMUTABLES DEL CONTRATO
    # ══════════════════════════════════════════════════════════════════

    def test_leagues_endpoint_returns_db_seeded_liga_mx(self):
        """[SHIELD-INVARIANTE] La API de ligas debe leer de SQLite y contener la Liga MX activa."""
        leagues = self.fetch_active_leagues_api()
        assert len(leagues) >= 1, "Debe existir al menos 1 liga registrada en la base de datos."
        liga_mx = next((l for l in leagues if l.get("fotmob_id") == 262 or "LIGA MX" in l.get("name", "").upper()), None)
        assert liga_mx is not None, "La Liga MX (FotMob ID: 262) debe estar registrada y activa en SQLite."

    def test_live_board_standings_has_18_complete_teams_with_3_tabs_data(self):
        """[SHIELD-INVARIANTE] El Live Board debe retornar los 18 clubes completos con datos para las 3 pestañas."""
        board = self.fetch_live_board_api(262)
        standings = board.get("standings", [])
        
        # 1. Prohibido truncar la tabla a 4 o 6 clubes
        assert len(standings) == 18, f"La tabla en vivo debe contener exactamente 18 clubes (recibidos: {len(standings)})."

        # 2. Validar presencia de campos para las 3 pestañas
        for team in standings:
            # Pestaña General
            assert "pos" in team and "equipo" in team and "puntos" in team
            assert "pj" in team and "pg" in team and "pe" in team and "pp" in team
            assert "gf" in team and "gc" in team and "dif" in team
            
            # Pestaña Forma
            assert "forma" in team and isinstance(team["forma"], list)
            assert len(team["forma"]) >= 1, f"El equipo {team.get('equipo')} debe tener historial de forma reciente."
            
            # Pestaña xG Opta
            assert "xg" in team and team["xg"] is not None, f"Falta métrica xG Opta en {team.get('equipo')}."

    def test_live_board_fixtures_has_valid_odds_and_pa(self):
        """[SHIELD-INVARIANTE] La cartelera del Live Board debe contener partidos con cuotas y estado de selección."""
        board = self.fetch_live_board_api(262)
        fixtures = board.get("fixtures", [])
        assert len(fixtures) >= 1, "La cartelera de la jornada activa debe contener al menos 1 partido."

        for f in fixtures:
            assert "id_partido" in f and "local" in f and "visitante" in f
            if f.get("es_operable", True) and f.get("momios") is not None:
                momios = f.get("momios") or {}
                assert momios.get("L", 0.0) > 1.0, f"Momio local inválido en {f.get('id_partido')}."
                assert momios.get("E", 0.0) > 1.0, f"Momio empate inválido en {f.get('id_partido')}."
                assert momios.get("V", 0.0) > 1.0, f"Momio visita inválido en {f.get('id_partido')}."
                assert "pago_anticipado" in momios

    def test_live_board_persists_snapshots_in_sqlite(self):
        """[SHIELD-INVARIANTE] Al consultar el Live Board, los datos deben persistirse en la base de datos local."""
        persisted = self.check_db_snapshots_exist(262)
        assert persisted is True, "Los snapshots de tabla y cartelera deben quedar guardados en SQLite."
