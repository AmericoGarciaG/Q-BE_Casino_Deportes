# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [FASE 6 SPRINT 6.2] Verificación de la Estructura DOM Dual-Core
Doctrina: Kybern Framework v12.0 [DES-QBE-030 a 033] [GOV-TEST-01 a 07]
Régimen: [DBBD-FUNGIBLE]
"""

import os
import re
import pytest

INDEX_HTML_PATH = os.path.join("src", "web", "templates", "index.html")
APP_JS_PATH = os.path.join("src", "web", "static", "js", "app.js")


def test_dual_core_dom_identifiers_present():
    """Valida la presencia de los contenedores cardinales en index.html."""
    assert os.path.exists(INDEX_HTML_PATH), "No existe index.html"
    
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Cockpit Top Navbar
    assert 'id="main-navbar"' in html, "Falta #main-navbar en index.html"
    assert 'id="nav-btn-sovereign"' in html, "Falta #nav-btn-sovereign"
    assert 'id="nav-btn-markets"' in html, "Falta #nav-btn-markets"

    # 2. Pantalla Core 1 (Soberana)
    assert 'id="view-sovereign-hub"' in html, "Falta contenedor #view-sovereign-hub"
    assert 'id="sovereign-matches-carousel"' in html, "Falta #sovereign-matches-carousel"

    # 3. Pantalla Core 2 (Mercados)
    assert 'id="view-markets-hub"' in html, "Falta contenedor #view-markets-hub"
    assert 'id="market-vehicle-tabs"' in html, "Falta #market-vehicle-tabs"
    assert 'id="tab-btn-casino"' in html, "Falta #tab-btn-casino"
    assert 'id="tab-btn-progol"' in html, "Falta #tab-btn-progol"


def test_sovereign_view_has_no_betting_checkboxes():
    """
    [DES-QBE-031] Pureza de la Pantalla Soberana:
    Valida que la sección soberana no contenga casillas de selección de apuestas.
    """
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Extraer bloque de view-sovereign-hub
    match = re.search(r'<div[^>]*id="view-sovereign-hub"[^>]*>(.*?)</div>\s*<!--\s*FIN VIEW-SOVEREIGN-HUB', html, re.DOTALL | re.IGNORECASE)
    if match:
        sovereign_block = match.group(1)
        assert 'type="checkbox"' not in sovereign_block, "Violación Ontológica: No debe haber checkboxes en la vista soberana."


def test_app_js_dual_core_functions():
    """Valida que app.js declare las funciones de control de vistas."""
    assert os.path.exists(APP_JS_PATH), "No existe app.js"
    
    with open(APP_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    assert "cambiarVistaPrincipal" in js, "Falta función cambiarVistaPrincipal en app.js"
    assert "cargarTableroSoberano" in js or "renderizarTableroSoberano" in js
    assert "renderizarMercadoCasino" in js or "cargarMercadoCasino" in js
    assert "renderizarMercadoProgol" in js or "cargarMercadoProgol" in js
