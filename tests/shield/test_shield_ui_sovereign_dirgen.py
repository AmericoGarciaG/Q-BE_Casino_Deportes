# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [DES-QBE-035 / VAULT-UI-001] Verificación DirGen de la Vista Soberana
Doctrina: Kybern Framework v12.0 [DIRGEN-SEALED] [GOV-TEST-01 a 07]
Régimen: [DIRGEN-STRICT]
"""

import os
import re
import pytest

INDEX_HTML_PATH = os.path.join("src", "web", "templates", "index.html")
APP_JS_PATH = os.path.join("src", "web", "static", "js", "app.js")


def test_purga_controles_comerciales_en_vista_partidos():
    """
    [DES-QBE-035] Valida que en la vista de Equipos y Partidos se hayan extirpado
    por completo los controles comerciales de apuestas.
    """
    assert os.path.exists(INDEX_HTML_PATH), "No existe index.html"
    
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Prohibido el botón "Generar Portafolio" dentro de la vista de partidos
    assert "btn-generate-portfolio" not in html and "Generar Portafolio" not in html, (
        "Violación DirGen: El botón 'Generar Portafolio' no debe existir en la vista soberana de partidos."
    )

    # 2. Prohibidos los botones de selección masiva en la vista de partidos
    assert "Seleccionar Todos" not in html, "Violación DirGen: 'Seleccionar Todos' debe ser extirpado."
    assert "Deseleccionar Todos" not in html, "Violación DirGen: 'Deseleccionar Todos' debe ser extirpado."
    assert "partidos seleccionados" not in html, "Violación DirGen: Contador de selección debe ser extirpado."

    # 3. La tabla de posiciones con sus 3 modalidades debe estar intacta
    assert 'id="table-standings"' in html or 'table-responsive' in html, "Falta la tabla de clasificación."
    assert "General" in html and "Forma" in html and "xG Opta" in html, "Faltan las pestañas de la tabla de posiciones."


def test_app_js_erradica_mercado_abierto_en_pildoras():
    """
    [DES-QBE-035] Valida que en app.js no se inyecte la etiqueta 'Mercado Abierto'
    en el selector de jornadas deportivas.
    """
    assert os.path.exists(APP_JS_PATH), "No existe app.js"
    
    with open(APP_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    assert "Mercado Abierto" not in js, (
        "Violación DirGen: 'Mercado Abierto' debe eliminarse de las píldoras de jornada (aplica solo en casinos)."
    )
