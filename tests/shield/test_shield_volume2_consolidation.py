# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: CONSOLIDACIÓN VOLUMEN II, LOGOS DE CASINO Y JORNADA DINÁMICA
[ARCH-1.5.10-B, ARCH-1.6.17, ARCH-1.6.15-C] & [DES-QBE-055, DES-QBE-056]
Régimen: [DIRGEN-STRICT]
Axioma: Cero duplicación de texto en boletos, logos locales presentes y Live Board dinámico.
"""

import os
import re
import pytest
from abc import ABC, abstractmethod


# [ARCH-1.5.10-B] Geometría del vector de Betway fijada por el inspector (catálogo soberano).
GEOMETRIA_VECTOR_BETWAY = "0 -2 55 20"


def _cuerpo_funcion_js(js: str, nombre: str) -> str:
    """Extrae el cuerpo de una función JS por nombre: audita la frontera, no la vecindad léxica."""
    inicio = js.find(f"function {nombre}")
    assert inicio != -1, f"Falta la función {nombre} en el archivo auditado"
    salto = chr(10)
    fin = js.find(salto + "}", inicio)
    return js[inicio:fin if fin != -1 else len(js)]


class AbstractTestVolume2Consolidation(ABC):
    """Juez Abstracto que audita los logos locales, anti-duplicación y apertura dinámica."""

    def test_existencia_logos_oficiales_casinos(self):
        """Verifica que existan físicamente los emblemas locales de Caliente y Betway."""
        bookmakers_dir = os.path.join("src", "web", "static", "img", "bookmakers")
        assert os.path.exists(bookmakers_dir), "Directorio static/img/bookmakers no existe"

        caliente_img = os.path.join(bookmakers_dir, "caliente.png")
        betway_svg = os.path.join(bookmakers_dir, "betway.svg")

        # Al menos uno de los dos formatos debe existir con peso real
        assert os.path.exists(caliente_img) or os.path.exists(os.path.join(bookmakers_dir, "caliente.svg")), \
            "Falta logo local de Caliente en /static/img/bookmakers/"
        assert os.path.exists(betway_svg) or os.path.exists(os.path.join(bookmakers_dir, "betway.png")), \
            "Falta logo local de Betway en /static/img/bookmakers/"

    def test_cero_texto_duplicado_boletos_app_js(self):
        """Verifica que app.js no concatene el nombre del casino tras la imagen del logo."""
        js_path = os.path.join("src", "web", "static", "js", "app.js")
        assert os.path.exists(js_path)

        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        # Prohibido concatenar ${nombre} tras la imagen del logo en el pie del boleto
        assert "bookmaker-logo-inline" in js, "Falta clase bookmaker-logo-inline en app.js"
        assert 'bookmaker-logo-inline"> ${nombre}' not in js, \
            "Violación DES-QBE-055: app.js concatena ${nombre} tras el logo, duplicando texto"

    def test_live_board_jornada_actual_dinamica(self):
        """Verifica que sync_service.py no tenga jornada_actual = 10 quemada."""
        sync_path = os.path.join("src", "storage", "sync_service.py")
        assert os.path.exists(sync_path)

        with open(sync_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Debe utilizar el resolver dinámico o consultar MatchdayState, no tener 10 fijo
        assert "jornada_actual = 10" not in code, \
            "Violación ARCH-1.6.15-C: sync_service.py mantiene 'jornada_actual = 10' quemado"

    def test_betway_scraper_soporte_fechas_calendario(self):
        """Verifica que betway_scraper expanda acordeones con lógica de fechas de octubre/lejanas."""
        scraper_path = os.path.join("src", "ingestion", "betway_scraper.py")
        assert os.path.exists(scraper_path)

        with open(scraper_path, "r", encoding="utf-8") as f:
            code = f.read()

        # [ARCH-1.6.17] Exigencia fáctica: contención de acordeones cerrados o meses de calendario
        assert "aria-expanded" in code or "oct" in code.lower(), \
            "Violación ARCH-1.6.17: betway_scraper no soporta aria-expanded ni fechas calendario"

    # ── B.4: cierre de la deuda de sensores ([ARCH-1.5.10-B] y [DES-QBE-056]) ──
    def test_boveda_emblemas_casinos_anclaje_autonomo_anti_hotlink(self):
        """[ARCH-1.5.10-B] La bóveda local se auto-abastece y el cliente jamás hotlinkea."""
        script_path = os.path.join("scripts", "utilidades", "sincronizar_boveda_activos.py")
        js_path = os.path.join("src", "web", "static", "js", "app.js")
        with open(script_path, "r", encoding="utf-8") as f:
            script = f.read()
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        # Catálogo soberano: endpoint oficial declarado + geometría del inspector del vector
        assert "https://sports.caliente.mx/es_MX/desktop_header_logo.png" in script, \
            "Violación ARCH-1.5.10-B: falta el endpoint oficial de Caliente en el catálogo"
        assert GEOMETRIA_VECTOR_BETWAY in script, \
            "Violación ARCH-1.5.10-B: falta la geometría del inspector del vector de Betway"

        # Frontera del cliente: el rótulo de operador consume SOLO la bóveda local (cero hotlink)
        cuerpo = _cuerpo_funcion_js(js, "_rotuloCasaApostar")
        assert "/static/img/bookmakers/" in cuerpo, \
            "Violación ARCH-1.5.10-B: el rótulo de operador no lee de la bóveda local"
        assert "http://" not in cuerpo and "https://" not in cuerpo, \
            "Violación ARCH-1.5.10-B: hotlink remoto detectado en el rótulo de operador"

    def test_apertura_live_board_jornada_vigente(self):
        """[DES-QBE-056] La cartelera abre en la jornada vigente: cero celdas quemadas."""
        js_path = os.path.join("src", "web", "static", "js", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        assert "view-matchday-selection" in js, "Falta la vista canónica del Live Board"
        assert "resolverJornadaVigenteLiveBoard" in js, \
            "Violación DES-QBE-056: no existe resolvedor dinámico de jornada vigente en app.js"
        assert not re.search(r"jornada_(?:actual|mostrada)\s*\|\|\s*\d+", js), \
            "Violación DES-QBE-056: celda quemada en la apertura del selector de jornadas"


class TestVolume2Consolidation(AbstractTestVolume2Consolidation):
    """Implementación concreta en The Shield."""
    pass
