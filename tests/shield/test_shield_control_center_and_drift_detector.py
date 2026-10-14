# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [ARCH-1.4.12-B] & [ARCH-1.4.12-C] Detector de Deriva y Cadenas del Centro de Control
Base de Gobierno: docs/ARCH.md [ARCH-1.4.12-B] / [ARCH-1.4.12-C]
Autoridad: Américo García Guerrero (Director Humano)
Régimen: [DIRGEN-STRICT] — Inmutable, Cero Mocks.
"""

import pytest
from fastapi.testclient import TestClient
from src.web.app import app


def test_invarianza_endpoint_admin_drift_status_200_ok():
    """
    [INVARIANZA 1 - CONTRATO REST DETECTOR DE DERIVA]:
    Verifica que GET /api/admin/status/drift responda HTTP 200 con las 4 dimensiones.
    """
    client = TestClient(app)
    response = client.get("/api/admin/status/drift")

    # DEBE FALLAR EN ROJO antes de implementar la ruta
    assert response.status_code == 200, f"🚨 ERROR: Endpoint /status/drift retornó {response.status_code}"
    data = response.json()
    assert "status_mercado" in data
    assert "status_deportivo" in data
    assert "status_progol" in data
    assert "status_integridad" in data
    assert "accion_recomendada" in data


def test_invarianza_whitelist_incluye_nuevas_tareas_y_cadenas():
    """
    [INVARIANZA 2 - SEGURIDAD Y WHITELIST STRICT]:
    Verifica que TAREAS_PERMITIDAS en admin_tasks.py incorpore los nuevos scripts y cadenas.
    """
    from src.web.routes.admin_tasks import TAREAS_PERMITIDAS

    # Nuevos sensores individuales
    assert "ingestar_historico_betexplorer" in TAREAS_PERMITIDAS
    assert "auditar_coherencia_cartelera" in TAREAS_PERMITIDAS

    # Nuevas cadenas temporales
    assert "cadena_pre_jornada" in TAREAS_PERMITIDAS
    assert "cadena_post_jornada" in TAREAS_PERMITIDAS
    assert "cadena_progol" in TAREAS_PERMITIDAS


def test_invarianza_mesa_apuestas_default_cobertura_balanceado():
    """
    [INVARIANZA 3 - DEFAULT UI BALANCEADO]:
    Verifica que en index.html el botón Balanceado (+15%) porte la clase active por defecto.
    """
    from pathlib import Path
    html_content = Path("src/web/templates/index.html").read_text(encoding="utf-8")

    assert 'data-modo="BAL"' in html_content
    # El botón BAL debe tener la clase active
    assert 'class="btn-cobertura active" data-modo="BAL"' in html_content or (
        'data-modo="BAL"' in html_content and 'active' in html_content.split('data-modo="BAL"')[0].split('<button')[-1]
    )
