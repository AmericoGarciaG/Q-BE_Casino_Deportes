# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [FASE 6 SPRINT 6.3] Verificación de Despacho con Slider y Optimizador Progol
Doctrina: Kybern Framework v12.0 [GOV-TEST-01 a 07]
Régimen: [HÍBRIDO DUAL-TRACK]
"""

import pytest
from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)


def test_sportsbook_portfolio_with_risk_slider():
    """
    [LN-QBE-073] Valida que el generador de cartera reciba target_certeza
    y satisfaga el umbral estocástico de no-pérdida.
    """
    payload = {
        "league_id": 262,
        "selected_match_ids": ["LIGAMX-J9-01", "LIGAMX-J9-08", "LIGAMX-J9-02"],
        "bankroll": 200.0,
        "target_certeza": 0.75
    }
    response = client.post("/api/markets/sportsbook/portfolio/generate", json=payload)
    assert response.status_code == 200, f"Error en endpoint: {response.text}"
    
    data = response.json()
    assert "balance_global_portafolio" in data
    assert "control_portafolio" in data
    
    # Verificar presencia de las Tres Píldoras
    trinidad = data["control_portafolio"]["desglose_bankroll"].get("trinidad_resiliencia")
    assert trinidad is not None
    assert trinidad["tablas_o_ganancia"]["probabilidad_pct"] >= 70.0
    
    # Hard-Cap Global <= 25%
    capital_comprometido = data["balance_global_portafolio"]["capital_total_comprometido_mxn"]
    assert capital_comprometido <= 200.0 * 0.2501


def test_progol_budget_combinatorial_optimizer():
    """
    [LN-QBE-074] Valida que el optimizador Progol asigne dobles y triples
    respetando exactamente el presupuesto comercial ($360 MXN = 1 triple + 3 dobles = 24 quinielas).
    """
    payload = {
        "slate_id": "PROGOL_2245",
        "presupuesto_mxn": 360.0
    }
    response = client.post("/api/markets/progol/optimize", json=payload)
    assert response.status_code == 200, f"Error en optimizador Progol: {response.text}"
    
    data = response.json()
    assert data["costo_total_mxn"] <= 360.0
    assert data["costo_total_mxn"] == 360.0  # 15 * (2^3) * (3^1) = 15 * 8 * 3 = 360.0
    assert len(data["matriz_quiniela"]) == 14

    # Verificar que los partidos con alerta de sesgo tengan doble o triple asignado
    for item in data["matriz_quiniela"]:
        if item.get("alerta_sesgo"):
            casillas_activas = sum([item["juega_L"], item["juega_E"], item["juega_V"]])
            assert casillas_activas >= 2, f"Partido con sesgo #{item['order']} debió recibir doble o triple"
