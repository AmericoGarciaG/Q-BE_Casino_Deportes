# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: REFINAMIENTO DE BOLETOS, FORMATO DUAL Y ESCENARIOS DINÁMICOS
[LN-QBE-083, ARCH-1.4.19] & [DES-QBE-061, DES-QBE-062]
Régimen: [DIRGEN-STRICT]
Axioma: Momio con probabilidad implícita, Doble Cobro explícito y monotonía post-Dutching.
"""

import os
import re
import pytest
from abc import ABC, abstractmethod


class AbstractTestTicketUXAndCashoutRefinement(ABC):
    """Juez Abstracto que audita el formato dual, escenarios dinámicos y monotonía."""

    def test_formato_dual_momio_casino_en_app_js(self):
        """Verifica que app.js renderice el momio con formato dual: XX.X% (@X.XX)."""
        js_path = os.path.join("src", "web", "static", "js", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        assert "Momio Casino:" in js
        assert "toFixed(1)}% (@" in js or "prob_implicita" in js, \
            "Violación DES-QBE-061: app.js no formatea la cuota como Prob% (@Decimal)"

    def test_escenario_pago_anticipado_con_empate_en_app_js(self):
        """Verifica que app.js despliegue el escenario explícito 'Pago Anticipado con Empate:'."""
        js_path = os.path.join("src", "web", "static", "js", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        assert "Pago Anticipado con Empate:" in js, \
            "Violación DES-QBE-062: Falta renglón literal 'Pago Anticipado con Empate:' en app.js"

    def test_escenario_salida_emergencia_en_app_js(self):
        """Verifica que app.js despliegue la instrucción de CashOut de emergencia."""
        js_path = os.path.join("src", "web", "static", "js", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        assert "Salida de Emergencia:" in js or "CashOut" in js, \
            "Violación DES-QBE-062: Falta renglón de 'Salida de Emergencia' en app.js"

    def test_monotonia_estricta_capital_post_dutching(self):
        """Verifica que build_plan preserve la monotonía no creciente B_1 >= B_2 >= ... >= B_K."""
        from src.core.portfolio import PortfolioEngine

        candidatos_base = [
            {"id_partido": "P1", "strategy_code": "QBE-H1", "odd_fav": 2.06, "odd_emp": 3.60, "odd_und": 3.45, "prob_fav": 60.3, "prob_emp": 23.1, "prob_und": 16.6, "fav_name": "A", "und_name": "B"},
            {"id_partido": "P2", "strategy_code": "QBE-H1", "odd_fav": 2.00, "odd_emp": 3.75, "odd_und": 3.65, "prob_fav": 58.8, "prob_emp": 22.1, "prob_und": 19.1, "fav_name": "C", "und_name": "D"},
            {"id_partido": "P3", "strategy_code": "QBE-H2", "odd_fav": 2.40, "odd_emp": 3.55, "odd_und": 2.80, "prob_fav": 55.2, "prob_emp": 23.0, "prob_und": 21.8, "fav_name": "E", "und_name": "F"},
            {"id_partido": "P4", "strategy_code": "QBE-H2", "odd_fav": 2.50, "odd_emp": 3.60, "odd_und": 2.90, "prob_fav": 51.4, "prob_emp": 22.0, "prob_und": 26.6, "fav_name": "G", "und_name": "H"},
            {"id_partido": "P5", "strategy_code": "QBE-H1", "odd_fav": 2.10, "odd_emp": 3.60, "odd_und": 3.55, "prob_fav": 47.6, "prob_emp": 24.0, "prob_und": 28.4, "fav_name": "I", "und_name": "J"},
            {"id_partido": "P6", "strategy_code": "QBE-D2", "odd_fav": 2.35, "odd_emp": 3.45, "odd_und": 2.95, "prob_fav": 68.3, "prob_emp": 18.1, "prob_und": 13.6, "fav_name": "K", "und_name": "L"},
            {"id_partido": "P7", "strategy_code": "QBE-D1", "odd_fav": 1.70, "odd_emp": 3.95, "odd_und": 4.70, "prob_fav": 67.5, "prob_emp": 18.0, "prob_und": 14.5, "fav_name": "M", "und_name": "N"},
            {"id_partido": "P8", "strategy_code": "QBE-H1", "odd_fav": 3.25, "odd_emp": 3.60, "odd_und": 2.15, "prob_fav": 40.0, "prob_emp": 21.0, "prob_und": 39.0, "fav_name": "O", "und_name": "P"}
        ]

        # [Contrato Extendido] El motor exige la terna fiduciaria sellada (psi_downside y compañía):
        # sin estos campos el Juez abortaba en KeyError antes de auditar la matemática pura.
        candidatos = []
        for c in candidatos_base:
            candidatos.append({
                **c,
                "partido_nombre": f"{c['fav_name']} vs {c['und_name']}",
                "strategy_nombre": "Estrategia",
                "ev_neto_roi": 0.15,
                "psi_downside": 0.05,
                "psi_epist": 0.97,
                "delta_epist": 0.02,
                "alpha": 0.15,
            })

        plan = PortfolioEngine.build_plan(candidatos, bankroll=200.0, mode="BANKROLL", total_jornada=9)
        inversiones = [o.boletos.inversion_partido_A_i for o in plan.ordenes_ejecucion_partidos]

        # Verificar monotonía estricta no creciente: B_1 >= B_2 >= ... >= B_K
        for i in range(len(inversiones) - 1):
            assert inversiones[i] >= inversiones[i+1] - 0.05, \
                f"Violación ARCH-1.4.19: Inversión en pos {i} (${inversiones[i]}) < pos {i+1} (${inversiones[i+1]})"


class TestTicketUXAndCashoutRefinement(AbstractTestTicketUXAndCashoutRefinement):
    """Implementación concreta en The Shield."""
    pass
