# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [DES-QBE-036 / VAULT-UI-002] Verificación del Carrusel Dual J1-J17
Doctrina: Kybern Framework v12.0 [DIRGEN-SEALED]
Régimen: [DIRGEN-STRICT]
"""

import os
import pytest

INDEX_HTML_PATH = os.path.join("src", "web", "templates", "index.html")
APP_JS_PATH = os.path.join("src", "web", "static", "js", "app.js")


def test_carrusel_dual_temporada_completa_presente():
    """Valida la existencia física de los controles del carrusel y el track de temporada."""
    assert os.path.exists(INDEX_HTML_PATH), "No existe index.html"

    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Controles del Carrusel
    assert 'id="btn-carousel-prev"' in html, "Falta boton del carrusel"
    assert 'id="btn-carousel-next"' in html, "Falta boton del carrusel"
    assert 'id="season-matchdays-track"' in html, "Falta track deslizante de jornadas"

    # 2. Contenedores sincronizados
    assert 'id="table-standings"' in html, "Falta tabla de posiciones izquierda"
    assert 'id="fixtures-container"' in html, "Falta contenedor de partidos derecho"

    # 3. Prohibicion de botones invasivos dentro de la tarjeta
    assert "btn-rad-subtle" not in html, "Violacion estetica: No debe haber botones anadidos dentro de las tarjetas"
    assert "Radiografia Estocastica" not in html, "Violacion estetica: Prohibida nomenclatura arrogante"


def test_app_js_soporta_carrusel_j1_a_j17_sincronizado():
    """Valida que app.js gestione la navegacion y sincronizacion de ambas tablas."""
    assert os.path.exists(APP_JS_PATH), "No existe app.js"

    with open(APP_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    assert "navegarCarruselTemporal" in js, "Falta funcion navegarCarruselTemporal en app.js"
    assert "renderizarCarruselTemporadaCompleta" in js, "Falta renderizarCarruselTemporadaCompleta en app.js"
