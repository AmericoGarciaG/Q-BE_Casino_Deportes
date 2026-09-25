# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: CONTRATO REST Y SELECTORES DOM PARA CONSENSO DE MERCADO
[DES-QBE-039] & [ARCH-1.4.8]
"""

import pytest
from src.models.web_schemas import MatchFixtureOut


def test_contrato_fixture_consenso_mercado():
    """Verifica que el contrato web acepte el payload de consenso de mercado."""
    data = {
        "id_partido": "LIGAMX-J10-01",
        "local": "Atlante",
        "visitante": "Rayados de Monterrey",
        "horario": "25/09 19:00 hr",
        "momios": {"L": 3.45, "E": 3.80, "V": 1.98, "pago_anticipado": True},
        "consenso_mercado": {
            "p_L_mercado": 0.278,
            "p_E_mercado": 0.249,
            "p_V_mercado": 0.472,
            "delta_L": -0.072,
            "delta_E": -0.013,
            "delta_V": 0.085
        }
    }
    # Validar serialización Pydantic
    obj = MatchFixtureOut(**data)
    dumped = obj.model_dump()
    assert "consenso_mercado" in dumped
    assert dumped["consenso_mercado"]["p_L_mercado"] == 0.278
    assert dumped["consenso_mercado"]["delta_L"] == -0.072
