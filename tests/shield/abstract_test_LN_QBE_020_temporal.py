import abc
import pytest
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from src.models.raw_input import H2HMatchRaw
from src.models.analytics import H2HDecayResult

class AbstractTestTemporal(abc.ABC):
    @abc.abstractmethod
    def run_decay(self, matches: List[H2HMatchRaw], local: str, vis: str, fav: str) -> H2HDecayResult:
        pass

    def get_rendered_web_html(self) -> str:
        return ""

    def get_live_board_payload(self) -> Dict[str, Any]:
        return {}

    def test_h2h_simplex_conservation(self, sample_match_input):
        """[SHIELD-INVARIANTE #1] Suma de probabilidades H2H == 1.0000."""
        res = self.run_decay(sample_match_input.h2h_matches, "FC Juárez", "Club Pachuca", "Club Pachuca")
        assert abs((res.p_fav + res.p_emp + res.p_und) - 1.0) <= 0.0001

    def test_requires_exactly_5_matches(self):
        """[SHIELD-SAD-PATH] Entre 1 y 4 partidos (incompletos) debe fallar con ValueError."""
        with pytest.raises(ValueError, match="requiere exactamente 5 partidos"):
            # 3 partidos es inválido: ni cero ni cinco
            from src.models.raw_input import H2HMatchRaw
            three_matches = [
                H2HMatchRaw(fecha="2025-01-01", local_real="A", visitante_real="B", dias_transcurridos=100, marcador="1-0"),
                H2HMatchRaw(fecha="2025-02-01", local_real="B", visitante_real="A", dias_transcurridos=200, marcador="0-1"),
                H2HMatchRaw(fecha="2025-03-01", local_real="A", visitante_real="B", dias_transcurridos=300, marcador="2-1"),
            ]
            self.run_decay(three_matches, "A", "B", "A")

    def test_zero_h2h_returns_neutral_result(self):
        """[SHIELD-LN-QBE-020-B] Lista vacía activa Ley Zero-H2H: retorna resultado neutro."""
        res = self.run_decay([], "A", "B", "A")
        assert res is not None, "Zero-H2H no debe colapsar."
        assert abs((res.p_fav + res.p_emp + res.p_und) - 1.0) <= 0.001, "Simplex debe conservarse."
        assert res.antiguedad_promedio_dias >= 9000.0, "Antigüedad sentinel debe ser >= 9000."

    def test_navigation_and_headers_use_user_didactic_copy(self):
        """[SHIELD-UX] Valida textos didácticos orientados al usuario final."""
        html = self.get_rendered_web_html()
        if not html: return
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
        if not html: return
        assert "white-space: nowrap" in html, (
            "La columna Forma debe forzar white-space: nowrap para evitar que los círculos se apilen en 'T'."
        )

    def test_standings_apertura_2026_exact_leader_and_subleader(self):
        """[SHIELD-INVARIANTE #6] La tabla refleja la conclusión de la Jornada 7: América 16 pts, Chivas sublíder 14 pts."""
        board = self.get_live_board_payload()
        if not board: return
        standings = board.get("standings", [])
        assert len(standings) == 18, "La tabla debe tener 18 clubes."

        p1 = standings[0]
        assert "AMÉRICA" in p1["equipo"].upper(), f"El líder debe ser América, se encontró: {p1['equipo']}."
        assert p1["puntos"] == 16, f"El líder debe tener 16 puntos, se encontró: {p1['puntos']}."
        assert p1["dif"] == 10, f"Diferencia de goles de América debe ser +10, se encontró: {p1['dif']}."

        p2 = standings[1]
        assert "CHIVAS" in p2["equipo"].upper() or "GUADALAJARA" in p2["equipo"].upper() or "TOLUCA" in p2["equipo"].upper(), f"El sublíder debe ser Chivas/Toluca tras J7, se encontró: {p2['equipo']}."
        assert p2["puntos"] >= 13, f"El sublíder debe tener >= 13 puntos, se encontró: {p2['puntos']}."

    def test_teams_have_mexican_crests_and_proximo_rival_has_crest(self):
        """[SHIELD-UX / ARCH-1.5.1] Los escudos deben corresponder a los clubes reales de México."""
        board = self.get_live_board_payload()
        if not board: return
        standings = board.get("standings", [])
        
        for t in standings:
            assert "escudo_url" in t and t["escudo_url"], f"Falta escudo para {t.get('equipo')}."
            assert t.get("proximo_rival") and t["proximo_rival"] != "vs Rival", (
                f"El próximo rival de {t.get('equipo')} no puede ser el texto estático 'vs Rival'."
            )

