# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — CABLEADO REACTIVO DE LOS PARÁMETROS GOBERNANTES Γ / CERTEZA / δ
Juez Inmutable: [ARCH-1.4.53] / [LN-QBE-114] / [LN-QBE-115] / [DES-QBE-068]

Invariantes legisladas:
1. El cuerpo de `POST /api/markets/backtesting/simulate` que emite `app.js` transporta las TRES
   llaves gobernantes con los nombres EXACTOS del DTO `SimulatePortfolioRequest`
   (`gamma_slider`, `target_certeza_pct`, `modo_cobertura`). El contrato declara
   `extra="ignore"`: un alias inventado (`gamma`, `target_certeza`) se descartaría en silencio y
   el motor volvería a sus defaults sin error visible (el defecto que este sprint erradica).
2. Los valores se capturan de los selectores DOM REALES de la ventanilla
   (`input[name="opcion_gamma"]`, `#slider-risk-certainty`, `state.modo_cobertura`).
3. `target_certeza_pct` viaja en PORCENTAJE: la división `/100` de la ventanilla viva
   (`GeneratePortfolioRequest.target_certeza`, fracción) NO puede reaparecer en el laboratorio.
4. El juez queda atado al contrato Pydantic: si el DTO renombra un campo, este Juez rompe antes
   de que la UI vuelva a mentir en silencio.
"""

import os
import re

import pytest

INDEX_HTML_PATH = os.path.join("src", "web", "templates", "index.html")
APP_JS_PATH = os.path.join("src", "web", "static", "js", "app.js")

# Inicio/fin del bloque del laboratorio dentro de app.js (router vivo ⇄ laboratorio).
_INICIO_FUNCION = "async function iniciarSimulacionRentabilidad("
_FIN_FUNCION = "function pintarPanelFinanciero("

LLAVES_GOBERNANTES = ("gamma_slider", "target_certeza_pct", "modo_cobertura")
ALIAS_PROHIBIDOS = ("gamma:", "target_certeza:")


def _leer(ruta):
    assert os.path.exists(ruta), f"Artefacto ausente: {ruta}"
    with open(ruta, "r", encoding="utf-8") as archivo:
        return archivo.read()


def _bloque_laboratorio():
    """Extrae el cuerpo de `iniciarSimulacionRentabilidad` (cero heurística sobre el resto)."""
    js = _leer(APP_JS_PATH)
    inicio = js.find(_INICIO_FUNCION)
    assert inicio >= 0, f"Falta la función {_INICIO_FUNCION} en app.js"
    fin = js.find(_FIN_FUNCION, inicio)
    assert fin > inicio, "No se pudo delimitar el bloque del laboratorio en app.js"
    return js[inicio:fin]


def test_payload_transporta_las_tres_llaves_legisladas():
    """[INVARIANZA 1 - TRANSPORTE]: el JSON de simulación declara Γ, Certeza y δ con sus nombres."""
    bloque = _bloque_laboratorio()

    for llave in LLAVES_GOBERNANTES:
        patron = re.compile(rf"^\s*{llave}\s*:\s*\w+", re.MULTILINE)
        assert patron.search(bloque), (
            f"El payload de /backtesting/simulate no envía '{llave}': el motor caería en su "
            "default y la curva certificada divergiría de la pantalla"
        )

    # Los alias que el DTO descartaría por `extra="ignore"` quedan proscritos.
    for alias in ALIAS_PROHIBIDOS:
        assert re.search(rf"^\s*{re.escape(alias)}\s*", bloque, re.MULTILINE) is None, (
            f"Alias prohibido '{alias}' en el payload: `extra=\"ignore\"` lo descartaría en "
            "silencio y el defecto de cableado reaparecería sin error HTTP"
        )


def test_valores_se_capturan_de_los_selectores_dom_legislados():
    """[INVARIANZA 2 - CAPTURA]: las tres cifras nacen del DOM real, no de constantes quemadas."""
    bloque = _bloque_laboratorio()
    html = _leer(INDEX_HTML_PATH)

    # Γ: tri-estado de radios (67% | 70% | 75%) con fallback al default legislado de la UI.
    assert 'input[name="opcion_gamma"]:checked' in bloque, "Γ no se lee del selector tri-estado"
    assert "DEFAULTS_CARTERA.gamma" in bloque, "Γ no declara fallback al default legislado"
    assert 'name="opcion_gamma"' in html, "index.html no expone el grupo de radios de Γ"
    for valor in ('value="0.67"', 'value="0.70"', 'value="0.75"'):
        assert valor in html, f"Falta la píldora de Γ {valor} en index.html"

    # Certeza: slider de la ventanilla (PORCENTAJE), con respaldo declarado.
    assert 'getElementById("slider-risk-certainty")' in bloque, (
        "Certeza no se lee de #slider-risk-certainty"
    )
    assert "CERTEZA_PCT_DEFAULT" in bloque, "Certeza no declara fallback porcentual"
    assert 'id="slider-risk-certainty"' in html, "index.html no expone el slider de Certeza"

    # Cobertura: estado soberano del tríptico δ (DEF | BAL | AGR).
    assert "state.modo_cobertura" in bloque, "Cobertura no se lee del estado soberano del tríptico"
    assert 'id="toggle-modo-cobertura"' in html, "index.html no expone el tríptico de Cobertura"
    for modo in ('data-modo="DEF"', 'data-modo="BAL"', 'data-modo="AGR"'):
        assert modo in html, f"Falta la píldora {modo} en index.html"


def test_certeza_viaja_en_porcentaje_sin_la_division_de_la_ventanilla_viva():
    """[INVARIANZA 3 - UNIDADES]: `target_certeza_pct` es porcentaje; prohibido reutilizar `/100`."""
    bloque = _bloque_laboratorio()

    assert re.search(r"/\s*100(?:\.0)?\b", bloque) is None, (
        "El bloque del laboratorio divide entre 100: `target_certeza_pct` es PORCENTAJE "
        "(0.0-100.0) y 0.8 lo degradaría a la banda CRECIMIENTO sin aviso"
    )
    assert re.search(r"target_certeza_pct\s*:\s*certezaSeleccionada", bloque), (
        "La certeza no viaja verbatim del slider al campo porcentual"
    )


def test_juez_atado_al_contrato_pydantic_del_dto():
    """[INVARIANZA 4 - CONTRATO]: las llaves del cable existen en el DTO y el DTO ignora extras."""
    from src.models.web_schemas import SimulatePortfolioRequest

    campos = set(SimulatePortfolioRequest.model_fields)

    for llave in LLAVES_GOBERNANTES:
        assert llave in campos, (
            f"'{llave}' no existe en SimulatePortfolioRequest: el cable estaría inventando "
            "un campo y el motor usaría el default"
        )

    assert SimulatePortfolioRequest.model_config.get("extra") == "ignore", (
        "El DTO dejó de declarar extra='ignore': el juez de transporte debe re-evaluarse"
    )

    # Dominios legislados que la UI no puede violar al despachar desde los selectores.
    dto = SimulatePortfolioRequest()
    assert dto.gamma_slider == pytest.approx(0.67)
    assert dto.target_certeza_pct == pytest.approx(0.0)
    assert dto.modo_cobertura == "DEF"

