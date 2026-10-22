# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — SANDBOX MICRO-DINÁMICAS ESPEJO (`𝒯_Spc`, V21-V25) SUITE
Juez Inmutable: [LN-QBE-112] / [ARCH-1.4.51] / [ARCH-1.4.62]
Base de Gobierno: Kybern Framework v13.5 [GOV-TEST-01] (Pure Read-Only / In-Memory Test)
"""

import pytest
from scripts.laboratorio.sandbox_micro_dinamicas_pipeline import (
    ejecutar_sandbox_micro_dinamicas_partido,
    calcular_ratio_cronometria,
    evaluar_alerta_fragilidad_cierre
)

def test_invarianza_sandbox_micro_dinamicas_resuelve_5_celdas_canonicas():
    """[INVARIANZA 1 - E2E]: El sandbox emite UNA dimensión canónica con sus 5 celdas (V21-V25)."""
    res = ejecutar_sandbox_micro_dinamicas_partido(match_id="LIGAMX-J11-07")
    
    assert res is not None
    assert res["status"] in ("EXITO", "PARCIAL", "SIN_EVIDENCIA")
    
    # 1. Comprobar presencia de la única dimensión del catálogo de 32 ([ARCH-1.4.62]).
    assert "dimension_5_balon_parado_y_disciplina" in res
    
    # 2. Comprobar presencia de las 5 celdas canónicas de `𝒯_Spc`.
    d5 = res["dimension_5_balon_parado_y_disciplina"]
    assert all(k in d5 for k in ["V21", "V22", "V23", "V24", "V25"])
    assert len(d5) == 5
    assert res["celdas_totales"] == 5

def test_invarianza_ratios_cronometria_no_negativos():
    """[INVARIANZA 2 - CRONOMETRÍA]: Ratios 1T/2T deben ser no negativos con guardas de división por cero."""
    # Caso 1: Producción balanceada: 0.8 xG en 1T, 0.8 xG en 2T -> Ratio = 1.0
    assert abs(calcular_ratio_cronometria(xg_1t=0.8, xg_2t=0.8) - 1.0) < 1e-4

    # Caso 2: Explosión en 1T: 1.2 xG en 1T, 0.4 xG en 2T -> Ratio = 3.0
    assert abs(calcular_ratio_cronometria(xg_1t=1.2, xg_2t=0.4) - 3.0) < 1e-4

    # Caso 3: Sin producción en 2T: 0.8 xG en 1T, 0.0 xG en 2T -> Guarda acotada (ej. 5.0 máx)
    ratio_inf = calcular_ratio_cronometria(xg_1t=0.8, xg_2t=0.0)
    assert ratio_inf >= 1.0 and ratio_inf <= 10.0

    # Caso 4: Sin producción en ambos: 0.0 / 0.0 -> Ratio = 1.0 (neutro)
    assert abs(calcular_ratio_cronometria(xg_1t=0.0, xg_2t=0.0) - 1.0) < 1e-4

def test_invarianza_alerta_fragilidad_cierre_pago_anticipado():
    """[INVARIANZA 3 - CIERRE TARDÍO]: xGA en minutos 80-90+ >= 0.35 dispara alerta de riesgo en +PA."""
    # Caso Fragilidad Alta: xGA tardío = 0.42 -> Alerta de riesgo de empate en el cierre
    alerta_alta = evaluar_alerta_fragilidad_cierre(xga_80_90=0.42)
    assert alerta_alta["riesgo_quiebre_pa"] is True
    assert "FRAGILIDAD" in alerta_alta["diagnostico"]

    # Caso Cierre Sólido: xGA tardío = 0.12 -> Cerrojo defensivo
    alerta_solida = evaluar_alerta_fragilidad_cierre(xga_80_90=0.12)
    assert alerta_solida["riesgo_quiebre_pa"] is False
    assert "SÓLIDO" in alerta_solida["diagnostico"]

def test_invarianza_degradacion_fiduciaria_sin_feed_granular():
    """[INVARIANZA 4 - ZERO MOCKS]: Variables sin feed específico degradan a SIN EVIDENCIA con None."""
    res = ejecutar_sandbox_micro_dinamicas_partido(match_id="LIGAMX-J11-07")
    v25 = res["dimension_5_balon_parado_y_disciplina"]["V25"]  # Tarjetas (sin feed granular)
    
    assert v25["estado"] == "SIN EVIDENCIA"
    assert v25["local"] is None and v25["visita"] is None
    assert "FASE 6" in str(v25["nota"])
