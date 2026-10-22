# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — SANDBOX TRAYECTORIA & MOMENTO (DIM 8) SUITE
Juez Inmutable: [LN-QBE-110] / [ARCH-1.4.49]
Base de Gobierno: Kybern Framework v13.5 [GOV-TEST-01] (Pure Read-Only / In-Memory Test)
"""

import pytest
from scripts.laboratorio.sandbox_trayectoria_momento_pipeline import (
    ejecutar_sandbox_trayectoria_partido,
    calcular_pendiente_lineal_5p,
    evaluar_diagnostico_xpts,
)


def test_invarianza_sandbox_trayectoria_resuelve_variables_dim8():
    """[INVARIANZA 1 - E2E]: El sandbox debe procesar un partido y extraer V31, AUX_M_XG, AUX_M_XGA y V32."""
    res = ejecutar_sandbox_trayectoria_partido(match_id="LIGAMX-J11-07")

    assert res is not None
    assert res["status"] == "EXITO"
    assert "dimension_8_trayectoria" in res

    dim8 = res["dimension_8_trayectoria"]
    assert "V31" in dim8 and "AUX_M_XG" in dim8 and "AUX_M_XGA" in dim8 and "V32" in dim8

    # Comprobar estados
    assert dim8["V31"]["estado"] == "EVALUADO"
    assert dim8["AUX_M_XG"]["estado"] == "EVALUADO"
    assert dim8["AUX_M_XGA"]["estado"] == "EVALUADO"
    assert dim8["V32"]["estado"] == "EVALUADO"


def test_invarianza_forma_5p_acotada_entre_0_y_15():
    """[INVARIANZA 2 - FORMA 5P]: Los puntos de los últimos 5 partidos deben pertenecer a [0, 15]."""
    res = ejecutar_sandbox_trayectoria_partido(match_id="LIGAMX-J11-07")
    v29 = res["dimension_8_trayectoria"]["V31"]

    pts_local = v29["puntos_local"]
    pts_visita = v29["puntos_visita"]

    assert 0 <= pts_local <= 15, f"Puntos 5P local fuera de cota: {pts_local}"
    assert 0 <= pts_visita <= 15, f"Puntos 5P visita fuera de cota: {pts_visita}"
    assert v29["delta_puntos"] == pts_local - pts_visita


def test_invarianza_calculo_pendiente_lineal_exacta():
    """[INVARIANZA 3 - REGRESIÓN]: La pendiente de 5 puntos debe calcularse con exactitud matemática."""
    # Serie creciente: [1.0, 1.2, 1.4, 1.6, 1.8] -> t = 1..5, delta_t = 1, delta_y = 0.2 -> m = +0.2000
    serie_creciente = [1.0, 1.2, 1.4, 1.6, 1.8]
    m_crec = calcular_pendiente_lineal_5p(serie_creciente)
    assert abs(m_crec - 0.2000) < 1e-4

    # Serie decreciente: [2.0, 1.75, 1.50, 1.25, 1.0] -> m = -0.2500
    serie_decreciente = [2.0, 1.75, 1.50, 1.25, 1.0]
    m_dec = calcular_pendiente_lineal_5p(serie_decreciente)
    assert abs(m_dec - (-0.2500)) < 1e-4

    # Serie plana: [1.5, 1.5, 1.5, 1.5, 1.5] -> m = 0.0000
    assert abs(calcular_pendiente_lineal_5p([1.5] * 5) - 0.0) < 1e-4


def test_invarianza_diagnostico_xpts_varianza():
    """[INVARIANZA 4 - xPTS]: Saldo PTS - xPTS diagnostica sobre/sub-rendimiento."""
    # Caso Sobrerrendimiento (Suerte / Inflado): 22 PTS con solo 14.2 xPTS -> Delta = +7.8
    diag_suerte = evaluar_diagnostico_xpts(puntos_reales=22, xpts=14.2)
    assert abs(diag_suerte["delta_xpts"] - 7.8) < 1e-4
    assert diag_suerte["diagnostico"] == "SOBRERRENDIMIENTO"
    assert "Regresión" in diag_suerte["alerta"]

    # Caso Subrrendimiento (Ineficiencia / Mala Suerte): 10 PTS con 15.5 xPTS -> Delta = -5.5
    diag_mala_suerte = evaluar_diagnostico_xpts(puntos_reales=10, xpts=15.5)
    assert abs(diag_mala_suerte["delta_xpts"] - (-5.5)) < 1e-4
    assert diag_mala_suerte["diagnostico"] == "SUBRRENDIMIENTO"
    assert "Rebote" in diag_mala_suerte["alerta"]
