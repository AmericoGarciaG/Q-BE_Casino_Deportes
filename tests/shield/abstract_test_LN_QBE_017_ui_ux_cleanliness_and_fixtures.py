"""
Kybern Industrial Governance — Twin-Test Protocol
Juez Inmutable: [ARCH-1.6.1 / DES-QBE-015 / DES-QBE-016] Auditoría de Usabilidad, Cero Fugas Técnicas y Cartelera
ID de Prueba: SHIELD-TEST-LN-QBE-017-UX-CLEANLINESS
"""
import abc
import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup


class AbstractTestUIUXCleanlinessAndFixtures(abc.ABC):
    """
    Juez Abstracto que audita la experiencia visual del usuario:
    1. Cero fugas de jerga de programador (SQLite, Tokens LLM, P.I.R.).
    2. Ausencia del glitch de doble signo (+ -) en la columna DIF xG.
    3. Próximo rival en pestaña Forma debe indicar rivales reales (no 'vs Rival' genérico).
    4. Cartelera agrupada por bloques de fecha con un solo checkbox por partido.
    """

    @abc.abstractmethod
    def get_rendered_web_html(self) -> str:
        """Debe retornar el HTML de la aplicación web renderizado por el servidor."""
        pass

    @abc.abstractmethod
    def get_live_board_payload(self) -> Dict[str, Any]:
        """Debe retornar el payload JSON emitido por /api/leagues/262/live-board."""
        pass

    # ══════════════════════════════════════════════════════════════════
    # ASERCIONES INMUTABLES DE ESPECIFICACIÓN VISUAL
    # ══════════════════════════════════════════════════════════════════

    def test_no_system_developer_jargon_leaks(self):
        """[SHIELD-UX] Prohíbe terminología de desarrollo expuesta al usuario final."""
        html = self.get_rendered_web_html()
        soup = BeautifulSoup(html, "html.parser")
        texto_visible = soup.get_text()

        # Palabras prohibidas en la interfaz de usuario
        prohibidas = ["SQLite", "Tokens LLM", "P.I.R. Sensor", "100% Determinista"]
        for p in prohibidas:
            assert p not in texto_visible, f"Fuga de jerga técnica detectada en la UI: '{p}'."

    def test_no_double_signs_in_xg_dif(self):
        """[SHIELD-UX] Prohíbe el formateo roto '+ -' en la columna de diferencia de xG."""
        html = self.get_rendered_web_html()
        assert "+ -" not in html and "+-" not in html, "Glitch de formato detectado: '+ -' en DIF xG."

    def test_standings_has_actual_rival_names_no_generic_placeholder(self):
        """[SHIELD-UX] Prohíbe que el próximo rival sea un placeholder 'vs Rival' repetido en todos los clubes."""
        board = self.get_live_board_payload()
        standings = board.get("standings", [])
        assert len(standings) >= 18
        
        rivales = [t.get("proximo_rival", "") for t in standings if t.get("proximo_rival")]
        # No puede ser que todos digan 'vs Rival'
        assert not all(r == "vs Rival" for r in rivales), "Regresión: Todos los clubes muestran 'vs Rival' genérico."

    def test_fixtures_have_single_checkbox_per_card(self):
        """[SHIELD-UX] Cada tarjeta de partido en la cartelera debe tener exactamente UN checkbox selector."""
        html = self.get_rendered_web_html()
        soup = BeautifulSoup(html, "html.parser")
        
        cards = soup.select(".fixture-card")
        if cards:
            for c in cards:
                checkboxes = c.find_all("input", attrs={"type": "checkbox"})
                assert len(checkboxes) == 1, f"Tarjeta de partido con selectores duplicados o ausentes: {len(checkboxes)}."
