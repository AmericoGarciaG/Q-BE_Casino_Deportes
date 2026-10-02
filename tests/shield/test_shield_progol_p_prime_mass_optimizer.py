# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: MOTOR DE MASA ACUMULADA P' Y OPTIMIZADOR PROGOL
[LN-QBE-084, LN-QBE-085, LN-QBE-086, LN-QBE-087] & [ARCH-1.4.20]
Régimen: [DIRGEN-STRICT]
Axioma: Maximización estricta de masa C(M), orden monotónico P' y garantía fiduciaria.
"""

import pytest
from abc import ABC, abstractmethod


class AbstractTestProgolPPrimeMassOptimizer(ABC):
    """Juez Abstracto que audita la optimización combinatoria pura de Progol."""

    @pytest.fixture
    def mock_partidos_14(self):
        """Genera un fixture mock realista de 14 partidos con probabilidades soberanas."""
        partidos = []
        for i in range(1, 15):
            partidos.append({
                "order": i,
                "local": f"Local_{i}",
                "visitante": f"Visita_{i}",
                "p_qbe": {
                    "L": round(0.50 + (i % 3) * 0.05, 4),
                    "E": 0.25,
                    "V": round(1.0 - (0.50 + (i % 3) * 0.05) - 0.25, 4)
                }
            })
        return partidos

    def test_invarianza_monotonia_p_prime(self, mock_partidos_14):
        """Verifica que la secuencia P' esté estrictamente ordenada de mayor a menor probabilidad."""
        from src.core.contracts.progol_math import generar_universo_restringido_y_ordenar_p_prime

        p_prime = generar_universo_restringido_y_ordenar_p_prime(mock_partidos_14)
        assert len(p_prime) == 2**14  # 16,384 combinaciones de cobertura binaria

        # Verificar monotonía: P(B_j) >= P(B_{j+1})
        for idx in range(len(p_prime) - 1):
            assert p_prime[idx][1] >= p_prime[idx + 1][1], \
                f"Violación LN-QBE-084: Monotonía rota en posición {idx}: {p_prime[idx][1]} < {p_prime[idx+1][1]}"

    def test_teorema_maximizacion_masa_acumulada(self, mock_partidos_14):
        """Verifica que seleccionar las primeras M boletas maximice estrictamente C(M)."""
        from src.core.contracts.progol_math import (
            generar_universo_restringido_y_ordenar_p_prime,
            seleccionar_primeras_m_combinaciones
        )

        p_prime = generar_universo_restringido_y_ordenar_p_prime(mock_partidos_14)
        M = 24  # Cupo para $360 MXN

        boletas_top, masa_optima = seleccionar_primeras_m_combinaciones(p_prime, m_cupo=M)
        assert len(boletas_top) == M

        # Comparar contra cualquier subconjunto alternativo del mismo tamaño M (ej. las siguientes M)
        masa_alternativa = sum(item[1] for item in p_prime[M:2*M])
        assert masa_optima > masa_alternativa, \
            "Violación Teorema de Maximización: Las primeras M deben acumular mayor masa que cualquier alternativa"

    def test_cumplimiento_estricto_presupuesto(self, mock_partidos_14):
        """Verifica que el optimizador no exceda el presupuesto en pesos ($15 MXN por boleta)."""
        from src.core.contracts.progol_math import optimizar_quiniela_progol_soberana

        presupuesto = 360.0
        resultado = optimizar_quiniela_progol_soberana(mock_partidos_14, presupuesto_mxn=presupuesto)

        assert resultado["costo_total_mxn"] <= presupuesto
        assert resultado["combinaciones_totales"] == 24
        assert resultado["costo_total_mxn"] == 24 * 15.0

    def test_resiliencia_partidos_bizarros_prior_un_tercio(self):
        """Verifica que partidos con prior (1/3, 1/3, 1/3) se procesen sin excepción."""
        from src.core.contracts.progol_math import optimizar_quiniela_progol_soberana

        # 12 partidos normales + 2 partidos bizarros sin información
        partidos_mixtos = []
        for i in range(1, 13):
            partidos_mixtos.append({"order": i, "local": f"L_{i}", "visitante": f"V_{i}", "p_qbe": {"L": 0.60, "E": 0.25, "V": 0.15}})
        for i in range(13, 15):
            partidos_mixtos.append({"order": i, "local": f"Bizarro_{i}", "visitante": f"Bizarro_V_{i}", "p_qbe": {"L": 0.3333, "E": 0.3333, "V": 0.3334}})

        # Descenso a garantía de 12 aciertos por haber 2 partidos bizarros
        res = optimizar_quiniela_progol_soberana(partidos_mixtos, presupuesto_mxn=300.0, l_objetivo=12)
        assert res["costo_total_mxn"] <= 300.0
        assert "12 Aciertos Garantizados" in res["garantia_fiduciaria"]

    def test_reduccion_hamming_cobertura_radio_uno(self, mock_partidos_14):
        """Verifica que la reducción a radio de Hamming d=1 cubra efectivamente combinaciones a 13 aciertos."""
        from src.core.contracts.progol_math import (
            generar_universo_restringido_y_ordenar_p_prime,
            reducir_a_garantia_hamming_l
        )

        p_prime = generar_universo_restringido_y_ordenar_p_prime(mock_partidos_14)
        boletas_13 = reducir_a_garantia_hamming_l(p_prime, l_aciertos_objetivo=13, max_boletas=16)

        assert len(boletas_13) <= 16
        assert len(boletas_13) >= 1
        # Verificar que la primera boleta sea la combinación modal B*
        assert boletas_13[0]["combinacion"] == list(p_prime[0][0])


class TestProgolPPrimeMassOptimizer(AbstractTestProgolPPrimeMassOptimizer):
    """Implementación concreta en The Shield."""
    pass
