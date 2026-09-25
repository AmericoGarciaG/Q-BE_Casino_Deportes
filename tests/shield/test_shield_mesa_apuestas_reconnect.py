# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [FASE 6 SPRINT 6.9] Verificación de Reconexión de Mesa de Apuestas
Doctrina: Kybern Framework v12.0 [ARCH-1.4.6 / LN-QBE-065]
Régimen: [HÍBRIDO DUAL-TRACK]
"""

import pytest
from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)


def test_despacho_automatico_jornada_completa_sin_seleccion_manual():
    """
    [ARCH-1.4.6] Valida que al no enviar selected_match_ids, el endpoint
    tome automáticamente los partidos de la Jornada 10 y procese la cartera.
    """
    payload = {
        "league_id": 262,
        "selected_match_ids": [],  # Lista vacía: despacho automático
        "bankroll": 200.0,
        "target_certeza": 0.80,
        "operador": "caliente"
    }
    response = client.post("/api/markets/sportsbook/portfolio/generate", json=payload)
    assert response.status_code == 200, f"Error en endpoint: {response.text}"

    data = response.json()
    assert "balance_global_portafolio" in data
    assert "control_portafolio" in data
    assert "ordenes_ejecucion_partidos" in data

    # Validar que se generaron órdenes reales
    ordenes = data["ordenes_ejecucion_partidos"]
    assert len(ordenes) >= 1, "Debió generarse al menos una orden aprobada con +EV"

    # Validar que las órdenes lleven la herencia de Pago Anticipado
    for o in ordenes:
        assert o["boletos"]["inversion_partido_A_i"] >= 2.0, "Violación de piso mínimo $2.00 MXN"


def test_descarte_temprano_activos_no_rentables():
    """
    [LN-QBE-065] Valida que los partidos sin ventaja (+EV <= 0)
    sean vetados como QBE-00 y reciban $0.00 MXN de inversión.
    """
    payload = {
        "league_id": 262,
        "bankroll": 200.0,
        "target_certeza": 0.80,
        "operador": "caliente"
    }
    response = client.post("/api/markets/sportsbook/portfolio/generate", json=payload)
    assert response.status_code == 200

    data = response.json()
    descartes = data.get("descartes", [])
    
    # Debe existir al menos un partido vetado (ej. volados simétricos como Cruz Azul vs Toluca)
    assert len(descartes) >= 1, "El filtro de descarte temprano debió vetar partidos no rentables"
    for d in descartes:
        assert d.get("codigo_estrategia") == "QBE-00" or "VETO" in d.get("motivo", "").upper()


def test_fuga_probabilidades_leagues_corregida():
    """
    Valida que el endpoint principal de ligas entregue p_local numérico (NO null).
    """
    response = client.get("/api/leagues/262/live-board?jornada=10")
    assert response.status_code == 200
    data = response.json()
    p1 = data["fixtures"][0]
    assert p1.get("p_local") is not None, "Fuga persistente: p_local sigue saliendo null en leagues.py"
    assert 0.0 <= p1.get("p_local") <= 1.0
