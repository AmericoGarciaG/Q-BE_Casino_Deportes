# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [FASE 6 SPRINT 6.1] Verificación de Contratos Desacoplados (Soberano vs Mercado)
Doctrina: Kybern Framework v12.0 [GOV-TEST-01 a 07]
Régimen: [HÍBRIDO DUAL-TRACK]
"""

import pytest
from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)


def test_sovereign_endpoint_purity_no_odds():
    """
    [DES-QBE-031 / ARCH-1.4.5] Prueba de Pureza Ontológica:
    El endpoint soberano debe devolver partidos con probabilidades reales
    pero CERO campos de cuotas, momios o apuestas comerciales.
    """
    response = client.get("/api/sovereign/leagues/262/matches")
    assert response.status_code == 200, f"Fallo de ruta: {response.status_code}"
    
    data = response.json()
    assert "matches" in data
    assert len(data["matches"]) > 0

    primer_partido = data["matches"][0]
    
    # 1. Verificación de presencia de magnitudes soberanas
    assert "p_local" in primer_partido
    assert "p_empate" in primer_partido
    assert "p_visitante" in primer_partido
    assert "lambda_home" in primer_partido
    assert "phi_lead2_home" in primer_partido

    # 2. Verificación de pureza: CERO cuotas del casino
    claves_prohibidas = ["momio", "momios", "cuota", "cuotas", "odds", "bookmaker"]
    for k in primer_partido.keys():
        for prohibida in claves_prohibidas:
            assert prohibida not in k.lower(), f"Violación de Pureza Ontológica: Clave '{k}' en endpoint soberano"


def test_market_sportsbook_contract_incorporates_gaps():
    """
    [DES-QBE-032 / ARCH-1.4.5] El endpoint de mercado de casino debe contrastar
    cuotas contra la distribución soberana y reportar los GAPs (+EV).
    """
    response = client.get("/api/markets/sportsbook/matches?bookmaker=caliente&league_id=262")
    assert response.status_code == 200

    data = response.json()
    assert "matches" in data
    assert len(data["matches"]) > 0

    m = data["matches"][0]
    assert "momio_l" in m
    assert "momio_e" in m
    assert "momio_v" in m
    assert "gap_local" in m
    assert "pago_anticipado" in m
    assert "es_viable_ev" in m


def test_progol_bias_detection_logic():
    """
    [LN-QBE-037] Valida el cálculo de sesgo popular en quinielas de concurso.
    """
    from src.core.contracts.progol_math import calcular_sesgo_quiniela
    
    v_publico = {"L": 0.65, "E": 0.20, "V": 0.15}
    p_soberana = {"L": 0.38, "E": 0.34, "V": 0.28}

    analisis = calcular_sesgo_quiniela(v_publico, p_soberana)
    assert analisis["sesgo_local"] == pytest.approx(0.27, 0.01)
    assert analisis["alerta_sesgo"] is True
    assert "X2" in analisis["recomendacion_cobertura"]
