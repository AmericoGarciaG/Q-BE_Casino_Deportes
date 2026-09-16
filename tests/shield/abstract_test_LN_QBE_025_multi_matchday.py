# -*- coding: utf-8 -*-
"""
JUEZ ABSTRACTO INMUTABLE: [LN-QBE-025] Multi-Jornada y Selección Híbrida
Doctrina: Kybern Framework v8.0 / v12.0 [GOV-TEST-01 a 07]
Desacoplamiento total de red, base de datos en memoria y Sad Paths.
"""

import abc
import pytest
from typing import List, Dict, Any
from pydantic import ValidationError


class AbstractTestMultiMatchdayPipeline(abc.ABC):
    """
    Oráculo Forense Inmutable para la verificación de Conmutación Multi-Jornada
    y Selección Híbrida de Cartera.
    """

    @abc.abstractmethod
    def obtener_live_board_jornada(self, league_id: int, jornada: int) -> Dict[str, Any]:
        """Debe invocar el servicio o endpoint para la jornada especificada."""
        pass

    @abc.abstractmethod
    def despachar_portafolio_hibrido(self, match_ids: List[str], bankroll: float) -> Dict[str, Any]:
        """Debe procesar la cartera combinando partidos de jornadas distintas."""
        pass

    def test_contrato_live_board_extensible(self):
        """Valida que el payload contenga las propiedades multi-jornada requeridas."""
        res = self.obtener_live_board_jornada(league_id=262, jornada=9)
        assert "jornada_actual" in res, "Falta 'jornada_actual' en LiveBoardOut"
        assert "jornada_mostrada" in res, "Falta 'jornada_mostrada' en LiveBoardOut"
        assert "jornadas_disponibles" in res, "Falta 'jornadas_disponibles' en LiveBoardOut"
        assert res["jornada_mostrada"] == 9
        assert isinstance(res["jornadas_disponibles"], list)
        assert len(res["jornadas_disponibles"]) >= 2

    def test_aislamiento_particion_sqlite(self):
        """Valida que consultar la Jornada 9 no sobreescriba ni borre la Jornada 8."""
        board_j8 = self.obtener_live_board_jornada(league_id=262, jornada=8)
        board_j9 = self.obtener_live_board_jornada(league_id=262, jornada=9)

        assert board_j8["jornada_mostrada"] == 8
        assert board_j9["jornada_mostrada"] == 9
        assert board_j8["fixtures"] != board_j9["fixtures"], "Colisión de fixtures entre jornadas"

    def test_seleccion_hibrida_cumple_hard_caps(self):
        """
        Sad Path & Invarianzas: Valida que la selección combinada de J8 y J9
        respete rigurosamente el Hard-Cap global del 25.0% (Invarianza #4) y Simplex.
        """
        bankroll = 1000.0
        # IDs representativos de ambas jornadas
        partidos_hibridos = ["partido_262_j8_test_01", "partido_262_j9_test_02"]
        
        plan = self.despachar_portafolio_hibrido(partidos_hibridos, bankroll=bankroll)
        assert plan is not None

        control = plan["control_portafolio"]
        balance = plan["balance_global_portafolio"]

        # Invarianza #4: Hard-Cap Global <= 25.01%
        max_inversion_permitida = bankroll * 0.2501
        assert balance["capital_total_comprometido_mxn"] <= max_inversion_permitida, (
            f"Violación Invarianza #4 en Portafolio Híbrido: "
            f"Comprometido {balance['capital_total_comprometido_mxn']} > {max_inversion_permitida}"
        )

        # Invarianza #2: Dutching exacto en cada orden con cobertura
        for orden in plan["ordenes_ejecucion_partidos"]:
            if orden["boletos"]["boleto_1_seguro"]["monto_mxn"] > 0:
                retorno_seguro = (
                    orden["boletos"]["boleto_1_seguro"]["monto_mxn"] * 
                    orden["boletos"]["boleto_1_seguro"]["momio"]
                )
                inv_total = orden["boletos"]["inversion_partido_A_i"]
                assert abs(retorno_seguro - inv_total) <= 0.08, "Violación Invarianza #2 en híbrido"
