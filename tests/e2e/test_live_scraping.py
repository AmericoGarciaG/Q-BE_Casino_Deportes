"""
Kybern Industrial Governance — E2E Suite
Pruebas de Ingesta e Integración en Vivo (Scraping contra FotMob / Red Externa).
"""
import pytest
from src.ingestion.providers.fotmob_provider import FotMobProvider

@pytest.mark.e2e
class TestLiveScraping:

    def test_fotmob_standings_has_18_teams_and_xg(self):
        """[E2E] Ingesta real desde FotMob de la tabla de posiciones con 18 equipos y xG."""
        standings = FotMobProvider.obtener_tabla_posiciones(262)
        assert len(standings) == 18, f"Se esperaban 18 equipos en la tabla, se obtuvo {len(standings)}"
        assert "xg" in standings[0], "Falta métrica xG en la tabla de FotMob"

    def test_pachuca_standings_matches_live_fotmob(self):
        """[E2E] Verificación en vivo de Pachuca en la tabla de posiciones."""
        standings = FotMobProvider.obtener_tabla_posiciones(262)
        pachuca = next((t for t in standings if "PACHUCA" in t["equipo"].upper()), None)
        assert pachuca is not None, "Club Pachuca no encontrado en la tabla."
        assert pachuca["puntos"] == 8, f"Pachuca debe tener 8 puntos, se encontró: {pachuca['puntos']}."
        assert pachuca["pj"] == 7, f"Pachuca debe tener 7 partidos jugados, se encontró: {pachuca['pj']}."

    def test_all_18_teams_have_valid_dynamic_crests(self):
        """[E2E] Verificación de rutas de escudos dinámicos en vivo."""
        standings = FotMobProvider.obtener_tabla_posiciones(262)
        for t in standings:
            assert "escudo_url" in t and t["escudo_url"], f"Falta escudo_url para {t['equipo']}."
            assert (
                t["escudo_url"].startswith("/static/img/crests/")
                or t["escudo_url"].startswith("data:image/svg+xml")
            ), f"URL de escudo inválida para {t['equipo']}: {t['escudo_url']}"
            assert "fotmob.com" not in t["escudo_url"].lower(), f"Se encontró hotlink externo para {t['equipo']}: {t['escudo_url']}"
