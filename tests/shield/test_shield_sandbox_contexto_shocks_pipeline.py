# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — SANDBOX CONTEXTO & SHOCKS (DIM 7) SUITE
Juez Inmutable: [LN-QBE-109] / [ARCH-1.4.48]
Base de Gobierno: Kybern Framework v13.5 [GOV-TEST-01] (Pure Read-Only / In-Memory Test)
"""

import math
import pytest
from scripts.laboratorio.sandbox_contexto_shocks_pipeline import (
    ejecutar_sandbox_contexto_partido,
    calcular_vector_contextual_c
)

def test_invarianza_sandbox_contexto_resuelve_variables_dim7():
    """[INVARIANZA 1 - E2E]: El sandbox debe procesar un partido y extraer V25, V26, V27, V28."""
    # Probar con San Luis vs Santos en J11
    res = ejecutar_sandbox_contexto_partido(match_id="LIGAMX-J11-07")
    
    assert res is not None
    assert res["status"] == "EXITO"
    assert "dimension_7_contexto" in res
    
    dim7 = res["dimension_7_contexto"]
    assert "V25" in dim7 and "V26" in dim7 and "V27" in dim7 and "V28" in dim7
    
    # V27 (Descanso) y V28 (Altitud) deben estar evaluadas con unidades
    assert dim7["V27"]["estado"] == "EVALUADO"
    assert dim7["V28"]["estado"] == "EVALUADO"
    assert "d" in str(dim7["V27"]["local"])
    assert "m" in str(dim7["V28"]["local"])

def test_invarianza_altitud_fisiologica_unidireccional():
    """[INVARIANZA 2 - ALTITUD]: Jugar a mayor altitud otorga bono; jugar más bajo no penaliza al local."""
    # Caso A: Toluca (2660m) recibe a Mazatlán (10m) -> Diff = +2650m -> Bono = 0.03 * 2.65 = +0.0795
    ctx_toluca = calcular_vector_contextual_c(
        altitud_local=2660.0, altitud_visita=10.0,
        dias_descanso_local=7.0, dias_descanso_visita=7.0,
        home_slug="deportivo-toluca",
        q_mod_h=1.0, q_mod_a=1.0
    )
    assert abs(ctx_toluca["delta_altitud_metros"] - 2650.0) < 1e-4
    assert abs(ctx_toluca["bono_altitud"] - 0.0795) < 1e-4
    
    # Caso B: Mazatlán (10m) recibe a Toluca (2660m) -> Diff negativo -> Bono Altitud = 0.0000
    ctx_mazatlan = calcular_vector_contextual_c(
        altitud_local=10.0, altitud_visita=2660.0,
        dias_descanso_local=7.0, dias_descanso_visita=7.0,
        home_slug="mazatlan-fc",
        q_mod_h=1.0, q_mod_a=1.0
    )
    assert ctx_mazatlan["delta_altitud_metros"] == 0.0
    assert ctx_mazatlan["bono_altitud"] == 0.0000

def test_invarianza_descanso_clamping_acotado():
    """[INVARIANZA 3 - DESCANSO]: El bono de recuperación debe estar acotado estrictamente en [-0.06, +0.06]."""
    # Caso Extremo: Local descansó 14 días, Visita jugó hace 2 días (Diff = +12d -> Clamp en +3d -> Bono = +0.06)
    ctx_extremo = calcular_vector_contextual_c(
        altitud_local=1500.0, altitud_visita=1500.0,
        dias_descanso_local=14.0, dias_descanso_visita=2.0,
        home_slug="club-puebla",
        q_mod_h=1.0, q_mod_a=1.0
    )
    assert ctx_extremo["delta_descanso_clamped"] == 3.0
    assert abs(ctx_extremo["bono_descanso"] - 0.0600) < 1e-4

def test_invarianza_vector_c_conservacion_con_vault():
    """[INVARIANZA 4 - VAULT PARITY]: C_H y C_A deben coincidir exactamente con la formulación log-lineal."""
    ctx = calcular_vector_contextual_c(
        altitud_local=2660.0, altitud_visita=1560.0,  # Toluca (2660m) vs Chivas (1560m) -> Diff = +1100m
        dias_descanso_local=5.0, dias_descanso_visita=7.0,  # Local descansó 2 días menos (-2d)
        home_slug="deportivo-toluca",  # Plaza Toluca = +0.06
        q_mod_h=0.95, q_mod_a=1.00     # Shock leve en local (-5%)
    )
    
    # 1. Bono altitud = 0.03 * 1.10 = +0.0330
    # 2. Bono descanso = 0.02 * (-2.0) = -0.0400
    # 3. Plaza Toluca = +0.0600
    # 4. gamma_contextual = 0.15 + 0.06 + 0.0330 - 0.0400 = 0.2030
    # 5. C_H = (0.2030 - 0.15) + ln(0.95) = 0.0530 + (-0.05129) = +0.0017
    # 6. C_A = ln(1.00) = 0.0000
    assert abs(ctx["gamma_contextual"] - 0.2030) < 1e-4
    assert abs(ctx["C_H"] - (0.0530 + math.log(0.95))) < 1e-4
    assert abs(ctx["C_A"] - 0.0000) < 1e-4
