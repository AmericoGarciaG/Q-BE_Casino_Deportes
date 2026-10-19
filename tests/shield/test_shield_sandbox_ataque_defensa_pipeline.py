# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — SANDBOX ATAQUE & DEFENSA (DIM 2 & 3) SUITE
Juez Inmutable: [LN-QBE-108] / [ARCH-1.4.47]
Base de Gobierno: Kybern Framework v13.5 [GOV-TEST-01] (Pure Read-Only / In-Memory Test)
"""

import pytest
from scripts.laboratorio.sandbox_ataque_defensa_pipeline import (
    ejecutar_sandbox_ataque_defensa_partido,
    calcular_colision_fuerzas_cruzadas
)

def test_invarianza_sandbox_ataque_defensa_resuelve_variables_nucleares():
    """[INVARIANZA 1 - E2E]: El sandbox debe procesar un partido de J11 y extraer las variables de Dim 2 y 3."""
    res = ejecutar_sandbox_ataque_defensa_partido(match_id="LIGAMX-J11-07")
    
    assert res is not None
    assert res["status"] == "EXITO"
    
    # 1. Comprobar presencia de dimensiones nucleares
    assert "dimension_2_ataque" in res
    assert "dimension_3_defensa" in res
    
    # 2. Verificar variables clave (V05 npxG y V10 xGA)
    v05 = res["dimension_2_ataque"]["V05"]
    v10 = res["dimension_3_defensa"]["V10"]
    
    assert v05["estado"] == "EVALUADO"
    assert v10["estado"] == "EVALUADO"
    assert v05["local"] > 0.0 and v05["visita"] > 0.0, "V05 debe contener tasas positivas para ambos clubes"
    assert v10["local"] > 0.0 and v10["visita"] > 0.0, "V10 debe contener tasas positivas para ambos clubes"

def test_invarianza_bipartita_simetrica_independencia():
    """[INVARIANZA 2 - BIPARTITA]: Cada club debe tener su propio valor numérico independiente."""
    res = ejecutar_sandbox_ataque_defensa_partido(match_id="LIGAMX-J11-07")
    v05 = res["dimension_2_ataque"]["V05"]
    
    # San Luis (Local) y Santos (Visita) deben tener valores distintos
    assert v05["local"] != v05["visita"], "Las métricas bipartitas no deben colapsar a valores idénticos arbitrarios"
    assert "unidad" in v05
    assert v05["unidad"] == "npxG/90"

def test_invarianza_colision_cruzada_conservacion_factores():
    """[INVARIANZA 3 - COLISIÓN]: La colisión cruzada (A_H - D_A) debe ser matemáticamente exacta."""
    # Simular factores: A_h=0.15, D_a=-0.10, A_a=-0.05, D_h=0.08
    colision = calcular_colision_fuerzas_cruzadas(
        A_h=0.15, D_a=-0.10,
        A_a=-0.05, D_h=0.08
    )
    
    # Empuje local = A_h - D_a = 0.15 - (-0.10) = 0.25
    # Empuje visita = A_a - D_h = -0.05 - 0.08 = -0.13
    assert abs(colision["empuje_ofensivo_local"] - 0.25) < 1e-4
    assert abs(colision["empuje_ofensivo_visita"] - (-0.13)) < 1e-4
    
    # Diferencial neto = 0.25 - (-0.13) = 0.38
    assert abs(colision["diferencial_neto_partido"] - 0.38) < 1e-4
    assert colision["bando_dominante"] == "LOCAL"

def test_invarianza_acotamiento_intensidades_lambda():
    """[INVARIANZA 4 - FÍSICA]: Las lambdas resultantes deben estar acotadas en [0.15, 4.50]."""
    res = ejecutar_sandbox_ataque_defensa_partido(match_id="LIGAMX-J11-07")
    lambdas = res["intensidades_proyectadas"]
    
    assert 0.15 <= lambdas["lambda_home"] <= 4.50, f"Lambda local fuera de escala física: {lambdas['lambda_home']}"
    assert 0.15 <= lambdas["lambda_away"] <= 4.50, f"Lambda visita fuera de escala física: {lambdas['lambda_away']}"
    assert lambdas["ratio_ofensivo"] > 0.0
