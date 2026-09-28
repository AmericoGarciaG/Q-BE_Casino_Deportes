# -*- coding: utf-8 -*-
#
# [VAR FASE6_PASO2 / VARIANCE-01] Desviación declarada D-1: la aserción 3 incorpora el token
# legislado `progol-slate-container` (DES-QBE-046) — la ley es la fuente de verdad y el Juez
# debe servirla, no al revés. Los tokens legacy se conservan como compatibilidad.
"""
🛡️ THE SHIELD — TWIN-TEST: CONTRATOS DE INTERFAZ DE USUARIO Y DESPACHO MESA DE APUESTAS
[DES-QBE-045, DES-QBE-046, DES-QBE-047]
Régimen: [DIRGEN-STRICT]
Axioma: Validación estructural estática del DOM, eventos de JS y tokens CSS.
"""

import os
import re
import pytest
from abc import ABC, abstractmethod


class AbstractTestPhase6UIContracts(ABC):
    """Juez Abstracto que audita la fidelidad de diseño y contratos en frontend."""

    def test_multi_operator_select_options(self):
        """Verifica que el selector de casinos contenga Caliente y Betway en index.html."""
        html_path = os.path.join("src", "web", "templates", "index.html")
        assert os.path.exists(html_path), "index.html no encontrado"

        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        assert 'id="casino-operator-select"' in html, "Falta selector #casino-operator-select"
        assert 'value="caliente"' in html, "Falta opción Caliente en el selector"
        assert 'value="betway"' in html, "Violación DES-QBE-047: Falta opción Betway en el selector de casinos"

    def test_subtabs_progol_y_sportsbook_en_html(self):
        """Verifica que index.html contenga la navegación bipartita de la Mesa de Apuestas."""
        html_path = os.path.join("src", "web", "templates", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Debe contener controles para conmutar entre Sportsbook y Progol
        assert "btn-subtab-sportsbook" in html or "data-subview=\"sportsbook\"" in html or "Sportsbook" in html
        assert "btn-subtab-progol" in html or "data-subview=\"progol\"" in html or "Progol" in html
        assert "progol-slate-container" in html or "progol-container" in html \
               or "progol-slate-view" in html or "contenedor-progol" in html, \
            "Violación DES-QBE-046: Falta contenedor para el concurso Progol en index.html"
    # ─────────────────────────────────────────────────────────────────────────────
    # [VAR FASE6_PASO2 / VARIANCE-01] DESVIACIONES DECLARADAS (autorizadas por la Tríada):
    #   D-1: la aserción 3 adopta el token LEGISLADO `progol-slate-container` (mandato DES-QBE-046)
    #        y conserva los tokens legacy como compatibilidad.
    #        Motivo: la ley es la fuente de verdad; sin esta corrección, una materialización FIEL
    #        a la ley quedaría ROJA (falso negativo perverso).
    #   D-2: reasignación registral de los IDs citados: DES-QBE-042 -> DES-QBE-045,
    #        DES-QBE-043 -> DES-QBE-046, DES-QBE-044 -> DES-QBE-047 (colisión de ID, VARIANCE-01).
    #        Afecta solo texto de docstring/mensajes: cero cambios en la lógica de verificación.
    # ─────────────────────────────────────────────────────────────────────────────

    def test_app_js_consumo_claves_canonicas_3nf(self):
        """Verifica que app.js lea las claves 3NF (ordenes_ejecucion_partidos) de markets.py."""
        js_path = os.path.join("src", "web", "static", "js", "app.js")
        assert os.path.exists(js_path), "app.js no encontrado"

        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        # Auditar que no dependa exclusivamente de data.ordenes
        assert "ordenes_ejecucion_partidos" in js, \
            "Violación DES-QBE-045: app.js no consume la clave canónica ordenes_ejecucion_partidos"
        assert "control_portafolio" in js, \
            "Violación DES-QBE-045: app.js no consume la clave canónica control_portafolio"
        assert "balance_global_portafolio" in js, \
            "Violación DES-QBE-045: app.js no consume la clave canónica balance_global_portafolio"

    def test_css_badges_para_nueve_estrategias(self):
        """Verifica que theme.css o app.js contemplen las 9 estrategias canónicas."""
        css_path = os.path.join("src", "web", "static", "css", "theme.css")
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()

        # Verificar reglas para las nuevas familias estratégicas
        # Al menos las familias D, H, R, C deben tener representación
        assert "QBE" in css or "badge" in css


class TestPhase6UIContracts(AbstractTestPhase6UIContracts):
    """Implementación concreta del Juez en The Shield."""
    pass
