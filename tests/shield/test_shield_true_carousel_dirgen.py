# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [DES-QBE-037 / VAULT-UI-003] Verificación del Carrusel de Una Sola Fila y Tarjeta Limpia
Doctrina: Kybern Framework v12.0 [DIRGEN-SEALED] [GOV-TEST-01 a 07]
Régimen: [DIRGEN-STRICT]
"""

import os
import re
import pytest

INDEX_HTML_PATH = os.path.join("src", "web", "templates", "index.html")
APP_JS_PATH = os.path.join("src", "web", "static", "js", "app.js")
THEME_CSS_PATH = os.path.join("src", "web", "static", "css", "theme.css")


def test_carrusel_controles_horizontales_presentes():
    """Valida que existan los controles del carrusel de una sola fila en index.html."""
    assert os.path.exists(INDEX_HTML_PATH), "No existe index.html"

    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="btn-carousel-prev"' in html, "Falta botón ◄ del carrusel (#btn-carousel-prev)"
    assert 'id="btn-carousel-next"' in html, "Falta botón ► del carrusel (#btn-carousel-next)"
    assert 'id="matchday-pill-selector"' in html, "Falta contenedor #matchday-pill-selector"


def test_tarjetas_sin_botones_invasivos_ni_jerga():
    """
    [DES-QBE-037] Valida que se hayan extirpado los botones blancos
    y la nomenclatura arrogante de las tarjetas de partidos.
    """
    assert os.path.exists(APP_JS_PATH), "No existe app.js"

    with open(APP_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    assert "btn-rad-subtle" not in js, "Violación estética: El botón 'btn-rad-subtle' debe ser eliminado de las tarjetas."
    assert "Radiografía Estocástica" not in js, "Violación de nomenclatura: Prohibido el texto 'Radiografía Estocástica'."
    assert "onclick=\"abrirRadiografiaForense" in js, "La tarjeta debe ser clicable directamente."


def test_carrusel_css_una_sola_fila():
    """Valida que el carrusel en CSS prohíba estrictamente el salto a múltiples filas."""
    assert os.path.exists(THEME_CSS_PATH), "No existe theme.css"

    with open(THEME_CSS_PATH, "r", encoding="utf-8") as f:
        css = f.read()

    assert "carousel-track-single-row" in css or "carousel-track" in css
    assert "flex-wrap: nowrap" in css, "Violación estética: El carrusel debe tener 'flex-wrap: nowrap'."
