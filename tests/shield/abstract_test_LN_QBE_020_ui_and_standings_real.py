"""
Kybern Industrial Governance — Twin-Test Protocol
Juez Inmutable: [DES-QBE-016 / ARCH-1.5.1 / LN-QBE-003] Textos Didácticos, Geometría de Forma y Tabla Apertura 2026 Real
ID de Prueba: SHIELD-TEST-LN-QBE-020-REAL-DATA-AND-UI
"""
import abc
from typing import Dict, Any, List
from bs4 import BeautifulSoup


class AbstractTestUIAndStandingsReal(abc.ABC):
    @abc.abstractmethod
    def get_rendered_web_html(self) -> str:
        """Debe retornar el HTML de la aplicación web renderizado por el servidor."""
        pass

    @abc.abstractmethod
    def get_live_board_payload(self) -> Dict[str, Any]:
        """Debe retornar el payload JSON de /api/leagues/262/live-board."""
        pass

    def test_navigation_and_headers_use_user_didactic_copy(self):
        """[SHIELD-UX] Valida textos didácticos orientados al usuario final."""
        html = self.get_rendered_web_html()
        soup = BeautifulSoup(html, "html.parser")
        texto_completo = soup.get_text()

        assert "Jornada y Tabla de Posiciones" in texto_completo, (
            "La pestaña principal debe titularse 'Jornada y Tabla de Posiciones'."
        )
        assert "Tabla Oficial (18 Clubes)" not in texto_completo, (
            "El título de la tabla no debe decir 'Tabla Oficial (18 Clubes)'; debe decir 'Liga MX'."
        )

    def test_form_circles_do_not_wrap_in_t_shape(self):
        """[SHIELD-UX / DES-QBE-036] Los 5 círculos de forma deben tener white-space: nowrap."""
        html = self.get_rendered_web_html()
        assert "white-space: nowrap" in html, (
            "La columna Forma debe forzar white-space: nowrap para evitar que los círculos se apilen en 'T'."
        )

    def test_standings_apertura_2026_exact_leader_and_subleader(self):
        """[SHIELD-INVARIANTE #6] La tabla debe anclarse al Apertura 2026: América 16 pts, Toluca 13 pts."""
        board = self.get_live_board_payload()
        standings = board.get("standings", [])
        assert len(standings) == 18, "La tabla debe tener 18 clubes."

        p1 = standings[0]
        assert "AMÉRICA" in p1["equipo"].upper(), f"El líder debe ser América, se encontró: {p1['equipo']}."
        assert p1["puntos"] == 16, f"El líder debe tener 16 puntos, se encontró: {p1['puntos']}."
        assert p1["dif"] == 10, f"Diferencia de goles de América debe ser +10, se encontró: {p1['dif']}."

        p2 = standings[1]
        assert "TOLUCA" in p2["equipo"].upper(), f"El sublíder debe ser Toluca, se encontró: {p2['equipo']}."
        assert p2["puntos"] == 13, f"Toluca debe tener 13 puntos, se encontró: {p2['puntos']}."
        assert p2["dif"] == 8, f"Diferencia de goles de Toluca debe ser +8, se encontró: {p2['dif']}."

    def test_teams_have_mexican_crests_and_proximo_rival_has_crest(self):
        """[SHIELD-UX / ARCH-1.5.1] Los escudos deben corresponder a los clubes reales de México."""
        board = self.get_live_board_payload()
        standings = board.get("standings", [])
        
        for t in standings:
            assert "escudo_url" in t and t["escudo_url"], f"Falta escudo para {t.get('equipo')}."
            assert t.get("proximo_rival") and t["proximo_rival"] != "vs Rival", (
                f"El próximo rival de {t.get('equipo')} no puede ser el texto estático 'vs Rival'."
            )
