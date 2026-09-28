# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: RESOLUCIÓN CRONOLÓGICA DE MERCADO, PURGA ATÓMICA Y TOOLTIPS
[ARCH-1.6.15-B, ARCH-1.6.13-B, ARCH-1.6.10-B, ARCH-1.4.13] & [DES-QBE-050]
Régimen: [DIRGEN-STRICT]
Axioma: Cero confusión entre calendario administrativo y ventanilla de casino.
"""

import os
import pytest
from abc import ABC, abstractmethod


class AbstractTestMarketResolutionAndPurge(ABC):
    """Juez Abstracto que audita la cronología de mercado y la higiene de base de datos."""

    def test_resolucion_cronologica_mercado_ignora_reprogramados_lejanos(self):
        """Verifica que el resolver no quede atrapado en J7 por juegos de noviembre."""
        from scripts.daemons.centinela_mercado import resolver_jornada_activa_dinamica

        # Simular base de datos real:
        # J10: Todos FINALIZADO (25-27 sep)
        # J7: 7 FINALIZADO y 2 juegos lejanos de octubre/noviembre
        # J11: 9 juegos PROGRAMADO para el próximo fin de semana (octubre)
        mock_fixtures = {
            7: [
                {"estado": "FINALIZADO"},
                {"estado": "PROGRAMADO", "sub_badge": "Fecha Lejana", "fecha_dt": "2026-10-28T21:00:00"},
                {"estado": "PROGRAMADO", "sub_badge": "Fecha Lejana", "fecha_dt": "2026-11-14T17:00:00"},
            ],
            10: [{"estado": "FINALIZADO"} for _ in range(9)],
            11: [{"estado": "PROGRAMADO", "sub_badge": None, "fecha_dt": "2026-10-09T19:00:00"} for _ in range(9)],
            12: [{"estado": "PROGRAMADO", "sub_badge": None, "fecha_dt": "2026-10-16T19:00:00"} for _ in range(9)]
        }
        jornada = resolver_jornada_activa_dinamica(mock_fixtures)
        assert jornada == 11, f"Fallo cronológico: debía resolver J11 por ser la próxima cartelera regular, resolvió J{jornada}"

    def test_purga_atomica_incluye_tablas_3nf(self):
        """Verifica mediante inspección de código que purgar_base_datos limpie Match y Slate."""
        purga_path = os.path.join("scripts", "utilidades", "purgar_base_datos.py")
        assert os.path.exists(purga_path), "purgar_base_datos.py no encontrado"

        with open(purga_path, "r", encoding="utf-8") as f:
            code = f.read()

        assert "Match" in code, "Violación ARCH-1.6.10-B: purgar_base_datos no limpia la tabla Match"
        assert "SovereignDistribution" in code, "Violación ARCH-1.6.10-B: no limpia SovereignDistribution"
        assert "Slate" in code, "Violación ARCH-1.6.10-B: no limpia Slates"

    def test_tooltips_didacticos_en_index_html(self):
        """Verifica que los botones del Centro de Control contengan el atributo title explicativo."""
        html_path = os.path.join("src", "web", "templates", "index.html")
        assert os.path.exists(html_path), "index.html no encontrado"

        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Acotar la inspección estrictamente al contenedor de la vista
        assert 'id="view-control-center"' in html
        seccion_cc = html.split('id="view-control-center"')[1].split('</section>')[0]

        # Verificar que el botón de purga y los daemons tengan su tooltip fiduciario
        assert 'title=' in seccion_cc, "Violación DES-QBE-050: Los botones en view-control-center no tienen tooltips"
        assert 'purgar_base_datos' in seccion_cc

    def test_erradicacion_duplicados_reprogramados_en_deportivo(self):
        """Verifica que centinela_deportivo no tenga la inyección fija if r == 8."""
        dep_path = os.path.join("scripts", "daemons", "centinela_deportivo.py")
        with open(dep_path, "r", encoding="utf-8") as f:
            code = f.read()

        assert "if r == 8" not in code, \
            "Violación ARCH-1.6.13-B: centinela_deportivo aún inyecta reprogramados con 'if r == 8'"


class TestMarketResolutionAndPurge(AbstractTestMarketResolutionAndPurge):
    """Implementación concreta en The Shield."""
    pass
