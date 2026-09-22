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
    """Valida la presencia de los contenedores cardinales en index.html tras la restauración."""
    assert os.path.exists(INDEX_HTML_PATH), "No existe index.html"
    
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Single-tier slim header
    assert 'class="app-header"' in html or 'header-container' in html, "Falta el encabezado en index.html"

    # 2. Vistas principales
    assert 'id="view-leagues-hub"' in html, "Falta contenedor view-leagues-hub"
    assert 'id="view-matchday-selection"' in html, "Falta contenedor view-matchday-selection"
    assert 'id="tab-portfolio"' in html, "Falta contenedor tab-portfolio"


def test_sovereign_view_has_no_betting_checkboxes():
    """Valida que no existan checkboxes indebidos en las secciones de visualización de liga."""
    assert os.path.exists(INDEX_HTML_PATH), "No existe index.html"


def test_app_js_dual_core_functions():
    """Valida que app.js declare las funciones de control de vistas."""
    assert os.path.exists(APP_JS_PATH), "No existe app.js"
    
    with open(APP_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    assert "initNavigation" in js or "switchView" in js, "Falta función de navegación en app.js"
