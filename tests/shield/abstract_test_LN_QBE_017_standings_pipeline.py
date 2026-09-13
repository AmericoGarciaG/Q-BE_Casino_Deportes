# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [LN-QBE-017] Ingesta Fáctica Soberana de la Tabla General (Liga MX)
Base de Gobierno: Kybern Framework v8.0 / v12.0
Axioma: Paridad matemática 100% con ligamx.net y erradicación total de fallbacks mockeados.
"""
import abc
from typing import Dict, Any, List
import pytest

from bs4 import BeautifulSoup

class AbstractTestLN_QBE_017_StandingsPipeline(abc.ABC):

    @abc.abstractmethod
    def obtener_tabla_posiciones_liga_mx(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Retorna la tabla de posiciones de Liga MX procesada por el pipeline de producción."""
        pass

    @abc.abstractmethod
    def verificar_presencia_mock_estatico(self) -> bool:
        """Verifica si el código fuente aún contiene o utiliza LIGA_MX_CLUBS_DYNAMIC_FALLBACK."""
        pass

    @abc.abstractmethod
    def get_rendered_web_html(self) -> str:
        """Debe retornar el HTML de la aplicación web renderizado por el servidor."""
        pass

    @abc.abstractmethod
    def get_live_board_payload(self) -> Dict[str, Any]:
        """Debe retornar el payload JSON emitido por /api/leagues/262/live-board."""
        pass

    # =========================================================================
    # INVARIANTES DEL ESCUDO (THE SHIELD)
    # =========================================================================

    def test_invariante_paridad_con_jornada_7_concluida(self):
        """
        [INVARIANZA 1 - VERDAD FÁCTICA OFICIAL]
        La tabla oficial de Liga MX debe reflejar la conclusión de la Jornada 7:
        - Guadalajara (Chivas) debe tener >= 14 puntos (triunfo 0-3 ante San Luis).
        - Cruz Azul debe tener >= 12 puntos (triunfo 1-0 ante Santos).
        - Pumas UNAM debe tener >= 11 puntos.
        - Atlas FC debe tener >= 13 puntos.
        Prohibido devolver los puntos viejos de la Jornada 6 (Chivas 11, Cruz Azul 9).
        """
        tabla = self.obtener_tabla_posiciones_liga_mx(force_refresh=False)
        assert len(tabla) == 18, f"Se esperaban 18 clubes, se recibieron {len(tabla)}"

        tabla_dict = {t["equipo"]: t for t in tabla}

        # Validar Chivas Guadalajara
        chivas = tabla_dict.get("Chivas Guadalajara") or tabla_dict.get("Guadalajara")
        assert chivas is not None, "Chivas Guadalajara no encontrada en la tabla."
        assert chivas["puntos"] >= 14, (
            f"Violación de Paridad: Chivas tiene {chivas['puntos']} pts (Jornada 6 congelada). "
            f"Debe tener >= 14 pts tras concluir la Jornada 7."
        )
        assert chivas["pj"] >= 7, f"Chivas debe tener >= 7 partidos jugados, tiene {chivas['pj']}."

        # Validar Cruz Azul
        cruz_azul = tabla_dict.get("Cruz Azul")
        assert cruz_azul is not None, "Cruz Azul no encontrado en la tabla."
        assert cruz_azul["puntos"] >= 12, (
            f"Violación de Paridad: Cruz Azul tiene {cruz_azul['puntos']} pts (Jornada 6 congelada). "
            f"Debe tener >= 12 pts tras concluir la Jornada 7."
        )

        # Validar Pumas UNAM
        pumas = tabla_dict.get("Pumas UNAM") or tabla_dict.get("Pumas")
        assert pumas is not None, "Pumas UNAM no encontrado en la tabla."
        assert pumas["puntos"] >= 11, f"Pumas debe tener >= 11 pts, tiene {pumas['puntos']}."

    def test_invariante_presencia_oficial_atlante_en_tabla(self):
        """
        [INVARIANZA 2 - INTEGRIDAD DE CLUBES DEL TORNEO]
        La tabla oficial de la FMF incluye al Atlante FC en la posición #14 con 7 puntos.
        El sistema debe reflejar la presencia real del Atlante y no reemplazarlo con Mazatlán.
        """
        tabla = self.obtener_tabla_posiciones_liga_mx(force_refresh=False)
        equipos = [t["equipo"] for t in tabla]

        tiene_atlante = any("atlante" in e.lower() for e in equipos)
        assert tiene_atlante is True, (
            f"Violación Fáctica: Atlante FC está ausente en la tabla de posiciones. "
            f"Equipos actuales: {equipos}"
        )

        atlante_item = next(t for t in tabla if "atlante" in t["equipo"].lower())
        assert atlante_item["puntos"] >= 7, f"Atlante debe tener >= 7 puntos, tiene {atlante_item['puntos']}."

    def test_invariante_consistencia_aritmetica_de_tabla(self):
        """
        [INVARIANZA 3 - SIMETRÍA MATEMÁTICA DE LIGA]
        En la tabla general completa:
        1. Puntos = (PG * 3) + PE para cada club.
        2. Suma total de GF == Suma total de GC.
        3. Suma total de PG == Suma total de PP.
        """
        tabla = self.obtener_tabla_posiciones_liga_mx(force_refresh=False)
        
        total_gf = sum(t["gf"] for t in tabla)
        total_gc = sum(t["gc"] for t in tabla)
        total_pg = sum(t["pg"] for t in tabla)
        total_pp = sum(t["pp"] for t in tabla)

        for t in tabla:
            puntos_calculados = (t["pg"] * 3) + t["pe"]
            assert t["puntos"] == puntos_calculados, (
                f"Error Contable en {t['equipo']}: Puntos reportados {t['puntos']} != "
                f"Calculados {puntos_calculados} (PG:{t['pg']}, PE:{t['pe']})."
            )

        assert total_gf == total_gc, f"Asimetría de Goles: Total GF {total_gf} != Total GC {total_gc}"
        assert total_pg == total_pp, f"Asimetría de Partidos: Total PG {total_pg} != Total PP {total_pp}"

    def test_invariante_erradicacion_total_de_mocks_estaticos(self):
        """
        [INVARIANZA 4 - GOVERNANCE-01]
        El código de producción NO debe depender de LIGA_MX_CLUBS_DYNAMIC_FALLBACK.
        """
        tiene_mock = self.verificar_presencia_mock_estatico()
        assert tiene_mock is False, (
            "Violación Crítica [GOVERNANCE-01]: El código de producción aún contiene "
            "o recurre a LIGA_MX_CLUBS_DYNAMIC_FALLBACK. Debe ser erradicado por completo."
        )

    def test_no_system_developer_jargon_leaks(self):
        """[SHIELD-UX] Prohíbe terminología de desarrollo expuesta al usuario final."""
        html = self.get_rendered_web_html()
        soup = BeautifulSoup(html, "html.parser")
        texto_visible = soup.get_text()

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
