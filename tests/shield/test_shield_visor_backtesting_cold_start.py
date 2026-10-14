# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [LN-QBE-100] Axioma de Cold Start y Prior de Mercado
Régimen: [DIRGEN-STRICT]
"""

from fastapi.testclient import TestClient
from src.web.app import app

def test_invarianza_cold_start_prior_de_mercado():
    """
    [INVARIANZA 4 - SUSTITUCIÓN DE PRIOR DE MERCADO EN S(I)=0]:
    Si un partido tiene suficiencia_S_I == 0, la API de calibración debe
    sobrescribir P' con el consenso del mercado (qL, qE, qV)
    para garantizar que Brier QBE == Brier Mercado y Alpha == 0.0%.
    """
    client = TestClient(app)
    resp = client.get("/api/markets/backtesting/calibration-report?league_id=1")
    assert resp.status_code == 200
    data = resp.json()

    evaluados = 0
    fallos = 0
    for j in data["jornadas"]:
        for p in j["partidos"]:
            if p.get("suficiencia_S_I") == 0:
                evaluados += 1
                brier_qbe = float(p.get("brier_qbe", 0.0))
                brier_mkt = float(p.get("brier_mercado", 0.0))
                if abs(brier_qbe - brier_mkt) > 0.001:
                    fallos += 1

    assert evaluados >= 27, "El test requiere al menos 27 partidos ciegos (J1-J3) en la BD"
    assert fallos == 0, f"🚨 FALLO COLD START: {fallos} partidos con S(I)=0 no igualan el Brier del Mercado."
