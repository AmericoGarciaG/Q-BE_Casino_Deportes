# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — SANDBOX H2H PIPELINE & RELATIONAL ATTRIBUTION SUITE
Juez Inmutable: [LN-QBE-106] / [ARCH-1.4.45]
Base de Gobierno: Kybern Framework v13.5 [GOV-TEST-01] (Pure Read-Only / In-Memory Test)
"""

import pytest
from scripts.laboratorio.sandbox_h2h_pipeline import ejecutar_sandbox_partido

def test_invarianza_sandbox_ejecuta_y_resuelve_variables_h2h():
    """[INVARIANZA 1 - E2E]: El sandbox debe procesar un partido real de J11 y extraer V26, V27 y V28."""
    # Probar con Atlético San Luis vs Santos Laguna en J11 (LIGAMX-J11-07)
    res = ejecutar_sandbox_partido(match_id="LIGAMX-J11-07")
    
    assert res is not None, "El sandbox retornó None para un partido válido"
    assert res["status"] == "EXITO"
    
    # 1. Verificar variables de la dimensión H2H
    vars_h2h = res["variables_h2h"]
    assert "V26" in vars_h2h and "V27" in vars_h2h and "V28" in vars_h2h
    
    # V27 debe tener modelado relacional con beneficiario
    v27 = vars_h2h["V27"]
    assert "delta_goles" in v27
    assert "beneficiario" in v27
    assert v27["beneficiario"] in ["LOCAL", "VISITANTE", "EQUILIBRADO"]
    assert "saldo_descriptivo" in v27

def test_invarianza_sandbox_fuson_estocastica_conserva_simplex():
    """[INVARIANZA 2 - SIMPLEX]: La distribución resultante de la fusión debe sumar 1.0."""
    res = ejecutar_sandbox_partido(match_id="LIGAMX-J11-07")
    p_hib = res["distribucion_hibrida"]
    
    suma = p_hib["p_local"] + p_hib["p_empate"] + p_visita if "p_visita" in p_hib else p_hib["p_local"] + p_hib["p_empate"] + p_hib["p_visitante"]
    assert abs(suma - 1.0) < 1e-6, f"Violación de Símplex Δ² en la fusión del sandbox: {suma}"

def test_invarianza_sandbox_antisimetria_v40():
    """[INVARIANZA 3 - ANTISIMETRÍA]: Si el visitante domina en goles, el beneficiario es VISITANTE."""
    from scripts.laboratorio.sandbox_h2h_pipeline import calcular_metricas_relacionales_h2h
    
    # Simular historial donde la visita supera al local: Local anota 2, Visita anota 8
    duelos_mock = [
        {"goles_local": 1, "goles_visita": 3, "dias_antiguedad": 50, "es_local_sede": True},
        {"goles_local": 1, "goles_visita": 5, "dias_antiguedad": 120, "es_local_sede": False}
    ]
    
    rel = calcular_metricas_relacionales_h2h(duelos_mock, local_nombre="Puebla", visita_nombre="Toluca")
    assert rel["V27"]["delta_goles_local"] == -6
    assert rel["V27"]["beneficiario"] == "VISITANTE"
    assert "Toluca (+6)" in rel["V27"]["saldo_descriptivo"]
