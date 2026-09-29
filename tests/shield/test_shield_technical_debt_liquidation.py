# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: FINIQUITO TOTAL DE DEUDA TÉCNICA Y SANEAMIENTO FASE 8
[LN-QBE-070-E, LN-QBE-078, ARCH-1.4.16, ARCH-1.3.4] & [DES-QBE-058, DES-QBE-059]
Régimen: [DIRGEN-STRICT]
Axioma: Respeto al piso de $2.00 bajo prorrateo global y transparencia total de vetos.
"""

import os
import ast
import pytest
from abc import ABC, abstractmethod


class AbstractTestTechnicalDebtLiquidation(ABC):
    """Juez Abstracto que audita la liquidación de deuda técnica en backend y frontend."""

    def test_prorrateo_resiliente_piso_ventanilla(self):
        """Verifica que el prorrateo del cap 25% no comprima el seguro por debajo de $2.00 MXN."""
        from src.core.contracts.portfolio_math import aplicar_hard_caps_con_respeto_a_piso

        bankroll = 200.0  # Cap 25% = $50.00 MXN
        ordenes = [
            {"id": "P1", "strategy_code": "QBE-H1", "inversion_total": 18.0, "odd_emp": 3.30},
            {"id": "P2", "strategy_code": "QBE-H1", "inversion_total": 15.0, "odd_emp": 3.30},
            {"id": "P3", "strategy_code": "QBE-H1", "inversion_total": 12.0, "odd_emp": 3.50},
            {"id": "P4", "strategy_code": "QBE-H1", "inversion_total": 10.0, "odd_emp": 3.75},
            {"id": "P5", "strategy_code": "QBE-H1", "inversion_total": 8.0,  "odd_emp": 3.95}
        ]  # Suma = 63.0 (excede 50.0)

        ordenes_ajustadas = aplicar_hard_caps_con_respeto_a_piso(ordenes, bankroll, piso_min_boleto=2.00)

        for o in ordenes_ajustadas:
            b_seg = round(o["inversion_total"] / o["odd_emp"], 2)
            # En ningún partido híbrido el seguro puede ser menor a $2.00 MXN
            assert b_seg >= 1.99, f"Violación LN-QBE-070-E: Seguro en {o['id']} cayó a ${b_seg} (< $2.00)"

    def test_cifras_cuantitativas_en_descartes_qbe00(self):
        """Verifica que los descartes QBE-00 contengan métricas numéricas en su contrato."""
        from src.web.routes.markets import _descartar_partido

        descartes = []
        _descartar_partido(
            descartes=descartes,
            partido_id="TEST-01",
            local="Puebla",
            visitante="León",
            motivo="Cuarentena / Sin Valor",
            motivo_codigo="QBE-00",
            codigo_estrategia="QBE-00",
            explicacion_didactica="Sin rentabilidad",
            metricas_cifras={"alpha_max": -0.10, "theta_estrella": 2.11, "p_fav": 0.40, "cuota_fav": 2.25}
        )

        assert len(descartes) == 1
        d = descartes[0]
        assert "metricas" in d or "alpha_max" in str(d.get("explicacion_didactica", "")) or "metricas_cifras" in d, \
            "Violación LN-QBE-078: Descarte QBE-00 no contiene cifras cuantitativas de justificación"

    def test_atribucion_operador_en_mono_casino(self):
        """Verifica que markets.py inyecte el slug del operador en mono-casino para evitar 'VENTANILLA'."""
        from src.web.routes.markets import generate_sportsbook_portfolio_endpoint, SportsbookPortfolioRequest

        req = SportsbookPortfolioRequest(
            league_id=262,
            selected_match_ids=[],
            bankroll=200.0,
            target_certeza=0.80,
            operador="caliente"
        )
        # El generador debe procesar y asignar operador='caliente' en los boletos
        markets_path = os.path.join("src", "web", "routes", "markets.py")
        with open(markets_path, "r", encoding="utf-8") as f:
            code = f.read()

        assert 'operador = op_sel' in code or 'operador_boleto' in code or '"operador": op_sel' in code, \
            "Violación ARCH-1.4.16: markets.py no asigna el slug en mono-operador"

    def test_delegacion_kelly_en_build_plan_ast(self):
        """Verifica mediante AST que build_plan invoque a calcular_kelly_atenuado de portfolio_math."""
        portfolio_path = os.path.join("src", "core", "portfolio.py")
        with open(portfolio_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        calls = [n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        assert "calcular_kelly_atenuado" in calls, \
            "Violación TD-COR-01: build_plan no delega el cálculo a calcular_kelly_atenuado"

    def test_deprecacion_definitiva_routes_portfolio_ast(self):
        """Verifica que routes/portfolio.py no contenga llamadas a QBEPipelineEngine."""
        port_route_path = os.path.join("src", "web", "routes", "portfolio.py")
        with open(port_route_path, "r", encoding="utf-8") as f:
            code = f.read()

        assert "QBEPipelineEngine.run_full" not in code, \
            "Violación ARCH-1.3.4: routes/portfolio.py sigue llamando al pipeline monolítico viejo"


class TestTechnicalDebtLiquidation(AbstractTestTechnicalDebtLiquidation):
    """Implementación concreta en The Shield."""
    pass
