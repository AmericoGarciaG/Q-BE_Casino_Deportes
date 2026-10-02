# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: SENSOR LIGA PREMIER FMF Y ALIASES GLOBALES PROGOL
[ARCH-1.4.23, ARCH-1.6.20, ARCH-1.5.11] & [LN-QBE-091]
Régimen: [DIRGEN-STRICT]
Axioma: Cero llamadas de red en pruebas unitarias. Determinismo absoluto de jerga.
"""

import os
import pytest
from abc import ABC, abstractmethod


class AbstractTestLigaPremierAndGlobalAliases(ABC):
    """Juez Abstracto que audita el parser de Liga Premier y la traducción de jerga global."""

    def test_traduccion_jerga_global_progol(self):
        """Verifica que el catálogo resuelva los nombres crudos de Progol #2353."""
        from src.ingestion.progol_resolver import traducir_jerga_global_progol

        assert traducir_jerga_global_progol("VERACRUZ") == "Racing de Veracruz"
        assert traducir_jerga_global_progol("OAXACA") == "Chapulineros de Oaxaca"
        assert traducir_jerga_global_progol("DURANGO") == "Alacranes de Durango"
        assert traducir_jerga_global_progol("R SOCIED. B") == "Real Sociedad B"
        assert traducir_jerga_global_progol("AGUILAS F") == "Club América Femenil"
        assert traducir_jerga_global_progol("MILAN F") == "AC Milan Femenil"
        assert traducir_jerga_global_progol("E.U.A.") == "USA"

    def test_parseo_tabla_ligapremier_html(self):
        """Verifica que el parser de ligapremier_scraper procese el HTML de estadísticas."""
        from src.ingestion.ligapremier_scraper import LigaPremierScraper

        # Mock representativo de la tabla de ligapremier.mx/estadisticas
        mock_html = """
        <table class="tabla-general">
            <tr><td>1</td><td>Club Deportivo Irapuato</td><td>5</td><td>5</td><td>0</td><td>0</td><td>13</td><td>4</td><td>16</td></tr>
            <tr><td>2</td><td>Racing de Veracruz</td><td>5</td><td>3</td><td>2</td><td>0</td><td>16</td><td>6</td><td>14</td></tr>
            <tr><td>14</td><td>Chapulineros de Oaxaca</td><td>5</td><td>0</td><td>2</td><td>3</td><td>4</td><td>11</td><td>2</td></tr>
        </table>
        """

        standings = LigaPremierScraper.parsear_tabla_estadisticas_html(mock_html)
        assert len(standings) == 3
        assert standings[0]["nombre"] == "Club Deportivo Irapuato"
        assert standings[0]["pts"] == 16
        assert standings[1]["nombre"] == "Racing de Veracruz"
        assert standings[1]["gf"] == 16
        assert standings[2]["nombre"] == "Chapulineros de Oaxaca"
        assert standings[2]["gc"] == 11

    def test_endpoint_fotmob_suggest_url_valida(self):
        """Verifica que progol_resolver apunte al endpoint activo /api/searchapi/suggest."""
        from src.ingestion.progol_resolver import URL_FOTMOB_SUGGEST_BASE

        assert "searchapi/suggest" in URL_FOTMOB_SUGGEST_BASE, \
            "Violación ARCH-1.6.20: progol_resolver sigue apuntando al endpoint deprecado /api/search/searchapi"


class TestLigaPremierAndGlobalAliases(AbstractTestLigaPremierAndGlobalAliases):
    """Implementación concreta en The Shield."""
    pass
