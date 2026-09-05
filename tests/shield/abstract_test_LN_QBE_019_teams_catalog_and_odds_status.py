"""
Kybern Industrial Governance — Twin-Test Protocol
Juez Inmutable: [ARCH-1.5.1 / ARCH-1.6.2 / LN-QBE-003] Catálogo de Equipos, Escudos y Ciclo de Vida de Cuotas
ID de Prueba: SHIELD-TEST-LN-QBE-019-TEAMS-AND-ODDS
"""
import abc
from typing import Dict, Any, List


class AbstractTestTeamsCatalogAndOddsStatus(abc.ABC):
    """
    Juez Abstracto que audita:
    1. Existencia y poblado de la tabla `teams` en SQLite con 18 clubes y URLs de escudos reales de FotMob.
    2. Correspondencia fáctica de la tabla de posiciones: el líder de Liga MX Apertura 2026 debe ser América con 16 pts.
    3. Manejo resiliente de partidos sin cuotas publicadas: marcado limpio como no disponibles y checkbox deshabilitado.
    4. Separación de partidos con fecha lejana (>14 días) en bloque de reprogramados.
    """

    @abc.abstractmethod
    def get_teams_from_db(self, league_id: int = 262) -> List[Dict[str, Any]]:
        """Debe consultar la tabla teams en SQLite."""
        pass

    @abc.abstractmethod
    def get_live_board_payload(self, league_id: int = 262) -> Dict[str, Any]:
        """Debe invocar /api/leagues/{id}/live-board."""
        pass

    # ══════════════════════════════════════════════════════════════════
    # ASERCIONES INMUTABLES
    # ══════════════════════════════════════════════════════════════════

    def test_teams_catalog_populated_with_18_clubs_and_crests(self):
        """[SHIELD-INVARIANTE] La tabla teams en SQLite debe contener 18 clubes con URLs de escudos válidas."""
        teams = self.get_teams_from_db(262)
        assert len(teams) == 18, f"Se esperaban 18 clubes en la tabla teams de SQLite, encontrados: {len(teams)}."
        
        for t in teams:
            assert "name" in t and "canonical_slug" in t
            assert "crest_url" in t and t["crest_url"] is not None
            assert t["crest_url"].startswith("http"), f"Escudo inválido para {t.get('name')}: {t.get('crest_url')}"

    def test_standings_reflects_apertura_2026_real_leader(self):
        """[SHIELD-INVARIANTE] La tabla de posiciones de Liga MX debe tener al Club América como líder con 16 puntos."""
        board = self.get_live_board_payload(262)
        standings = board.get("standings", [])
        assert len(standings) == 18, "La tabla debe tener 18 clubes."
        
        lider = standings[0]
        assert lider["pos"] == 1
        assert "AMÉRICA" in lider["equipo"].upper(), f"El líder debe ser América, se encontró: {lider['equipo']}."
        assert lider["puntos"] == 16, f"El líder debe tener 16 puntos, se encontró: {lider['puntos']}."

    def test_fixtures_handles_pending_odds_cleanly(self):
        """[SHIELD-INVARIANTE] Los partidos sin momios publicados deben marcarse como pendientes sin crashear."""
        board = self.get_live_board_payload(262)
        fixtures = board.get("fixtures", [])
        assert len(fixtures) >= 1
        
        # Verificar que existan partidos operables y partidos con cuota pendiente
        pendientes = [f for f in fixtures if not (f.get("momios") or {}).get("pago_anticipado") or (f.get("momios") or {}).get("L") is None]
        assert len(pendientes) >= 1, "Se esperaban partidos con cuotas pendientes."
        
        # Si hay partidos lejanos (como América vs Tijuana el 28 de oct), deben tener cuota pendiente o bandera no operable
        lejanos = [f for f in fixtures if "OCT" in f.get("horario", "").upper() or "NOV" in f.get("horario", "").upper() or "REPROGRAMADOS" in f.get("fecha_bloque", "").upper()]
        if lejanos:
            for lej in lejanos:
                assert lej.get("es_operable", True) is False or lej.get("es_pospuesto") is True, (
                    f"El partido lejano {lej.get('local')} vs {lej.get('visitante')} debe estar marcado como no operable/pospuesto."
                )
