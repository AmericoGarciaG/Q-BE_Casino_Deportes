# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: ORQUESTACIÓN 3NF Y CONVERGENCIA DE TRIAJE FASE 5
[LN-QBE-070-C, LN-QBE-070-D] & [ARCH-1.4.10]
Régimen: [DIRGEN-STRICT]
Axioma: Desacoplamiento total del motor legacy. Cero invocaciones a QBEPipelineEngine.
"""

import os
import ast
import pytest
from abc import ABC, abstractmethod


class AbstractTestPhase5Orchestration3NF(ABC):
    """Juez Abstracto que audita la orquestación 3NF y la extinción de deuda técnica."""

    def test_desacoplamiento_ast_markets_router(self):
        """Verifica mediante AST que markets.py no importe ni llame a adaptadores legacy."""
        markets_path = os.path.join("src", "web", "routes", "markets.py")
        assert os.path.exists(markets_path), "markets.py no encontrado"

        with open(markets_path, "r", encoding="utf-8") as f:
            code = f.read()

        tree = ast.parse(code)

        # 1. Prohibido importar generate_portfolio desde routes.portfolio
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "src.web.routes.portfolio" in node.module:
                    for alias in node.names:
                        assert alias.name != "generate_portfolio", \
                            "Violación ARCH-1.4.10: markets.py sigue acoplado a routes.portfolio legacy"
                if node.module and "src.pipeline.engine" in node.module:
                    for alias in node.names:
                        assert alias.name != "QBEPipelineEngine", \
                            "Violación ARCH-1.4.10: markets.py invoca al pipeline monolítico legacy"

    def test_contrato_extendido_approved_matches(self):
        """Verifica que el payload de partidos para build_plan contenga delta_epist fáctico."""
        from src.core.portfolio import PortfolioEngine

        # Mock de partido con contrato extendido [LN-QBE-070-C]
        match_candidato = {
            "id_partido": "TEST-01",
            "partido_nombre": "Toluca vs Atlas",
            "strategy_code": "QBE-H1",
            "strategy_nombre": "Híbrida Local + Empate V=0",
            "ev_neto_roi": 0.15,
            "psi_downside": 0.05,
            "delta_epist": 0.02,        # [R-1] Campo obligatorio
            "psi_epist": 0.9722,        # [R-1] Campo obligatorio
            "phi_lead2": 0.58,
            "odd_fav": 1.85,
            "odd_emp": 3.60,
            "odd_und": 4.50,
            "fav_name": "Toluca",
            "und_name": "Atlas",
            "pago_anticipado": True
        }

        # build_plan debe procesar el partido sin arrojar KeyError
        plan = PortfolioEngine.build_plan([match_candidato], bankroll=1000.0, mode="BANKROLL")
        assert plan is not None
        assert len(plan.ordenes_ejecucion_partidos) == 1
        orden = plan.ordenes_ejecucion_partidos[0]
        # El código debe ser canónico puro (sin signos '+')
        assert orden.estrategia_seleccionada.codigo in [
            "QBE-D1", "QBE-D2", "QBE-H1", "QBE-H2", "QBE-R1", "QBE-R2", "QBE-C1", "QBE-C2", "QBE-00"
        ]

    def test_convergencia_triaje_9_estrategias(self):
        """Verifica que la selección de estrategias en portfolio.py respete el catálogo canónico."""
        from src.core.portfolio import PortfolioEngine

        evals_mock = {
            "QBE_H1": {"viable": True, "nombre_oficial": "Híbrida Local V=0", "ev_neto_roi": 0.12},
            "QBE_00": {"viable": True, "nombre_oficial": "Cuarentena Fiduciaria", "ev_neto_roi": 0.0}
        }
        codigo, nombre, ev, promo = PortfolioEngine.select_best_strategy(
            evals=evals_mock,
            psi_ruina=0.04,
            pago_anticipado=True,
            p_fav=0.55
        )
        # El código devuelto debe ser estrictamente uno de los 9 canónicos
        assert codigo in [
            "QBE-D1", "QBE-D2", "QBE-H1", "QBE-H2", "QBE-R1", "QBE-R2", "QBE-C1", "QBE-C2", "QBE-00"
        ], f"Código no canónico detectado: {codigo}"


class TestPhase5Orchestration3NF(AbstractTestPhase5Orchestration3NF):
    """Implementación concreta en The Shield."""
    pass
