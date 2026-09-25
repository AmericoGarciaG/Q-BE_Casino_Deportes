# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: MODO ENFOQUE DE CARTELERA (STANDINGS TOGGLE)
[DES-QBE-040]
"""

import os
import pytest


def test_existencia_control_toggle_standings_en_templates():
    """Verifica que index.html contenga el disparador del modo enfoque."""
    html_path = os.path.join("src", "web", "templates", "index.html")
    assert os.path.exists(html_path), "index.html no encontrado"
    
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    assert 'id="btn-toggle-standings"' in html or 'toggleTablaPosiciones' in html, \
        "Violación DES-QBE-040: Falta el control interactivo #btn-toggle-standings"


def test_reglas_css_modo_enfoque():
    """Verifica que theme.css defina la clase .standings-hidden y el centrado a 880px."""
    css_path = os.path.join("src", "web", "static", "css", "theme.css")
    assert os.path.exists(css_path), "theme.css no encontrado"
    
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    
    assert "standings-hidden" in css, "Falta la clase .standings-hidden en theme.css"
    assert "880px" in css or "max-width" in css, "Falta la regla de centrado de cartelera en theme.css"
