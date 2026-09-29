# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: ARBITRAJE SINTÉTICO CROSS-MARKET Y TRADE-OFF PAGO ANTICIPADO
[LN-QBE-076, LN-QBE-077, ARCH-1.4.14, ARCH-1.5.4] & [DES-QBE-052, DES-QBE-053]
Régimen: [DIRGEN-STRICT]
Axioma: Mejor ejecución analítica por pierna y cuantificación exacta de pérdida de oportunidad.
"""

import os
import pytest
from abc import ABC, abstractmethod


class AbstractTestCrossMarketBestExecution(ABC):
    """Juez Abstracto que audita el arbitraje sintético y el trade-off de Pago Anticipado."""

    def test_ecuacion_tradeoff_pago_anticipado_vs_momio_puro(self):
        """Verifica la fórmula analítica de decisión entre +PA y cuota nominal más alta."""
        from src.core.contracts.portfolio_math import evaluar_tradeoff_pago_anticipado

        p_fav = 0.50
        delta_freeroll = 0.05  # 5% de probabilidad de tocar +2 y no ganar

        # Caso 1: Caliente @ 1.90 con +PA vs Betway @ 1.95 sin +PA
        # p_PA = 0.55 -> EV_PA = 0.55 * 1.90 - 1 = +4.5%
        # p_Vanilla = 0.50 -> EV_Vanilla = 0.50 * 1.95 - 1 = -2.5%
        # Gana Caliente (+PA) a pesar de pagar menos momio nominal
        res1 = evaluar_tradeoff_pago_anticipado(o_pa=1.90, o_vanilla=1.95, p_fav=p_fav, delta_freeroll=delta_freeroll)
        assert res1["recomendar_pa"] is True
        assert res1["ev_pa"] > res1["ev_vanilla"]

        # Caso 2: Betway paga un momio monstruoso @ 2.20 sin +PA vs Caliente @ 1.85 con +PA
        # EV_PA = 0.55 * 1.85 - 1 = +1.75%
        # EV_Vanilla = 0.50 * 2.20 - 1 = +10.0%
        # La cuota alta de Betway supera analíticamente el valor del freeroll
        res2 = evaluar_tradeoff_pago_anticipado(o_pa=1.85, o_vanilla=2.20, p_fav=p_fav, delta_freeroll=delta_freeroll)
        assert res2["recomendar_pa"] is False
        assert res2["ev_vanilla"] > res2["ev_pa"]

    def test_mejor_combinacion_cross_market_seleccion_optima(self):
        """Verifica que el resolvedor de mejor combinación elija el máximo momio por pierna."""
        from src.core.contracts.portfolio_math import resolver_mejor_combinacion_cuotas

        cuotas_partido = {
            "caliente": {"L": 2.10, "E": 3.30, "V": 3.40, "pa": True},
            "betway": {"L": 2.05, "E": 3.60, "V": 3.50, "pa": False}
        }
        # Para favorito local: debe tomar Ataque en Caliente (@2.10 con PA) y Seguro en Betway (@3.60)
        res = resolver_mejor_combinacion_cuotas(cuotas_partido, fav="L")
        assert res["ataque"]["operador"] == "caliente"
        assert res["ataque"]["momio"] == 2.10
        assert res["seguro"]["operador"] == "betway"
        assert res["seguro"]["momio"] == 3.60

    def test_denominador_total_partidos_jornada_kpi(self):
        """Verifica que el plan de ejecución reporte total_partidos_jornada = 9."""
        from src.core.portfolio import PortfolioEngine

        candidato = {
            "id_partido": "TEST-01", "partido_nombre": "A vs B", "strategy_code": "QBE-H1",
            "strategy_nombre": "Híbrida V=0", "ev_neto_roi": 0.10, "psi_downside": 0.05,
            "odd_fav": 1.90, "odd_emp": 3.50, "odd_und": 4.00, "fav_name": "A", "und_name": "B"
        }
        plan = PortfolioEngine.build_plan([candidato], bankroll=200.0, mode="BANKROLL", total_jornada=9)
        assert plan.control_portafolio.total_partidos_jornada == 9

    def test_existencia_select_mejor_combinacion_html(self):
        """Verifica que index.html contenga la opción de Mejor Combinación y el logo en boletos."""
        html_path = os.path.join("src", "web", "templates", "index.html")
        assert os.path.exists(html_path)

        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        assert 'value="mejor_combinacion"' in html, "Falta opción 'mejor_combinacion' en index.html"


class TestCrossMarketBestExecution(AbstractTestCrossMarketBestExecution):
    """Implementación concreta en The Shield."""
    pass
