# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: MATEMÁTICA DE MERCADO Y TELEMETRÍA MULTI-CASINO
[LN-QBE-007-B, C, D, E] & [ARCH-1.4.7]
"""

import pytest


class AbstractTestMarketTelemetry:
    """Juez Abstracto para la telemetría multi-operador."""

    def test_conversion_momios_americanos(self):
        from src.ingestion.betway_scraper import BetwayMarketScraper
        
        # Pruebas de conversión formal
        assert BetwayMarketScraper.american_to_decimal("+230") == 3.30
        assert BetwayMarketScraper.american_to_decimal("+100") == 2.00
        assert BetwayMarketScraper.american_to_decimal("-150") == 1.67
        assert BetwayMarketScraper.american_to_decimal("3.45") == 3.45  # Ya decimal

    def test_descuento_comision_simplex(self):
        from scripts.daemons.centinela_mercado import calcular_probabilidades_sin_comision
        
        # Cuotas con margen: 2.00, 3.20, 3.50 (Suma inversas: 0.5 + 0.3125 + 0.2857 = 1.0982)
        q_l, q_e, q_v = calcular_probabilidades_sin_comision(2.00, 3.20, 3.50)
        
        assert abs((q_l + q_e + q_v) - 1.0) <= 1e-4
        assert q_l < 0.50  # Debe descontar el margen
        assert q_l > 0.40

    def test_deteccion_arbitraje(self):
        from scripts.daemons.centinela_mercado import evaluar_arbitraje_partido
        
        # Caso sin arbitraje
        ops_no_arb = {
            "caliente": {"L": 2.00, "E": 3.00, "V": 3.50},
            "betway": {"L": 1.95, "E": 3.10, "V": 3.40}
        }
        res_no = evaluar_arbitraje_partido(ops_no_arb)
        assert res_no["existe"] is False

        # Caso con arbitraje real (Suma inversas < 1.0: 1/2.50 + 1/4.00 + 1/3.60 = 0.4 + 0.25 + 0.277 = 0.927)
        ops_arb = {
            "caliente": {"L": 2.50, "E": 3.20, "V": 2.80},
            "betway": {"L": 1.90, "E": 4.00, "V": 3.60}
        }
        res_arb = evaluar_arbitraje_partido(ops_arb)
        assert res_arb["existe"] is True
        assert res_arb["roi_pct"] > 5.0
        assert res_arb["mejor_L"]["operador"] == "caliente"
        assert res_arb["mejor_E"]["operador"] == "betway"


class TestMarketTelemetry(AbstractTestMarketTelemetry):
    pass
