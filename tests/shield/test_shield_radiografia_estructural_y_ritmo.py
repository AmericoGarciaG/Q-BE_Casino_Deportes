# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DE LA RADIOGRAFÍA ESTRUCTURAL Y EL RITMO COMPETITIVO
Directiva Quirúrgica del Director (2026-10-08): erradicación de la estrella del
'Casino Seleccionado', poblado de las métricas 3 (Solidez Defensiva) y 4 (Ritmo
Competitivo) del comparador dual, y reemplazo definitivo de la tabla inferior por
'📋 Radiografía Estructural y Forma Reciente'.

Contrato vigilado:
- [DES-QBE-063-ext-min] Las métricas 3 y 4 leen el hecho soberano del partido
  (`gf_gc`/`pts_pj` de `tabla_10p`) y, cuando el partido no porta el hecho (ruta
  `_adaptarFixtureARadiografia`, payload del Live Board), rematan en la fila homóloga
  de `currentLiveBoard.standings` (`gc/pj`, `puntos/pj`): aritmética sobre hechos reales.
- [GOVERNANCE-01] Cero cifras fabricadas: sin hecho homólogo se rotula "--". PROHIBIDO el
  relleno quemado (`|| 10`, `: 1.30`, `: 1.20`, `: 1.00`, `: 2.00`) y prohibido adivinar la
  fila por posición o por el primer elemento de la tabla.
- [DES-QBE-063-ext-min] Cero estrellas (⭐) en la columna CASINO SELECCIONADO: el operador
  se rotula en el color de su boleto (verde ataque / azul cobertura).
Régimen: [DBBD-FUNGIBLE] (capa de presentación; Poisson/André/Kelly/persistencia intactos).
Gobierno: [GOV-TEST-01] Aislamiento hermético en memoria (cero red / cero navegador).
"""

from pathlib import Path
import re

INDEX_HTML = Path("src/web/templates/index.html")
APP_JS = Path("src/web/static/js/app.js")

CABECERAS_ESTRUCTURALES = (
    "EQUIPO", "PUESTO", "PTS", "RÉCORD (G-E-P)", "DIF GOLES",
    "FORMA RECIENTE (5P)", "xPTS OPTA", "DIF xG", "Q_MOD",
)


def _cuerpo_funcion(nombre: str) -> str:
    assert APP_JS.exists(), "Falta src/web/static/js/app.js"
    js = APP_JS.read_text(encoding="utf-8")
    match = re.search(r"function\s+%s\s*\([^)]*\)\s*\{(.*?)\n\}" % nombre, js, re.DOTALL)
    assert match is not None, "Debe existir la función %s en app.js" % nombre
    return match.group(1)


def test_tabla_inferior_es_radiografia_estructural_y_forma_reciente():
    """La tabla inferior del modal debe ser la Radiografía Estructural, no el 10P previo."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "📋 Radiografía Estructural y Forma Reciente" in html, (
        "🚨 VIOLACIÓN: Falta el rótulo '📋 Radiografía Estructural y Forma Reciente'.")
    assert "Desempeño y Control de Cancha" not in html, (
        "🚨 VIOLACIÓN: La tabla inferior previa (10P) no fue reemplazada.")
    assert 'id="rad-cuerpo-equipos"' in html, "Debe conservarse el tbody gobernado del modal."
    faltantes = [c for c in CABECERAS_ESTRUCTURALES if ">%s<" % c not in html]
    assert not faltantes, (
        "🚨 VIOLACIÓN: Faltan cabeceras de la Radiografía Estructural: %s" % faltantes)
    for residual in ("PTS/PJ", "SOT", "SOTA", "POSESIÓN", "GF / GC"):
        assert ">%s<" % residual not in html, (
            "🚨 VIOLACIÓN: Cabecera residual de la tabla 10P: '%s'." % residual)


def test_hidratacion_de_la_tabla_lee_la_fila_homologa_del_live_board():
    """[DES-QBE-063-ext-min] La hidratación no depende de `tabla_10p` y cruza standings."""
    cuerpo = _cuerpo_funcion("_hidratarTablasRadiografia")
    assert "_filaStandings(" in cuerpo, (
        "🚨 VIOLACIÓN: La tabla estructural debe leer la fila homóloga del Live Board.")
    assert "_dividirContendientes(p)" in cuerpo, (
        "🚨 VIOLACIÓN: Los contendientes deben resolverse con el divisor soberano.")
    assert "_normalizarClub(" in cuerpo, (
        "🚨 VIOLACIÓN: La homología de nombres debe usar el normalizador soberano.")
    assert "tbodyEq && p.tabla_10p" not in cuerpo, (
        "🚨 VIOLACIÓN: La tabla estructural no puede exigir `tabla_10p` para hidratarse.")
    for clave_10p in ("row.sot", "row.sota", "row.posesion", "row.pts_pj"):
        assert clave_10p not in cuerpo, (
            "🚨 VIOLACIÓN: Columna 10P residual '%s' en la tabla estructural." % clave_10p)


def test_cero_estrellas_en_la_columna_casino_seleccionado():
    """[DES-QBE-063-ext-min] El operador se rotula con el color de su boleto y sin ⭐."""
    js = APP_JS.read_text(encoding="utf-8")
    assert "⭐ ${nombreCap}" not in js, (
        "🚨 VIOLACIÓN: Persiste la estrella en la columna CASINO SELECCIONADO.")
    i = js.find("const casinoTxt")
    assert i > 0, "Debe existir la celda `casinoTxt` en la hidratación de la tabla."
    bloque = js[i:i + 400]
    assert "⭐" not in bloque, (
        "🚨 VIOLACIÓN: La celda CASINO SELECCIONADO sigue portando la estrella.")
    assert "color: ${colorRes}" in bloque, (
        "🚨 VIOLACIÓN: El operador debe pintarse con la colorimetría de su boleto.")


def test_fila_standings_elastica_sin_adivinar_por_posicion():
    """La homología elástica ('Tigres' ⇄ 'Tigres UANL') jamás resuelve por posición."""
    normalizador = _cuerpo_funcion("_normalizarClub")
    assert "club|deportivo|fc" in normalizador, (
        "🚨 VIOLACIÓN: El normalizador debe erradicar los prefijos societarios declarados.")
    assert 'normalize("NFD")' in normalizador, (
        "🚨 VIOLACIÓN: El normalizador debe ser insensible a acentos.")

    cuerpo = _cuerpo_funcion("_filaStandings")
    assert "=== objetivo" in cuerpo, (
        "🚨 VIOLACIÓN [GOVERNANCE-01]: Falta la igualdad estricta normalizada como 1ª pasada.")
    assert "includes(objetivo)" in cuerpo and "objetivo.includes(" in cuerpo, (
        "🚨 VIOLACIÓN: La 2ª pasada debe ser contención bidireccional declarada.")
    for ciego in ("tabla[0]", "standings[0]", "|| tabla[0]", "|| standings[0]"):
        assert ciego not in cuerpo, (
            "🚨 VIOLACIÓN [GOVERNANCE-01]: '%s' adivina la fila por posición." % ciego)


def test_metricas_3_y_4_rematan_en_hechos_sin_cifras_de_relleno():
    """[GOVERNANCE-01] GC/PJ y PTS/PJ bajan de tabla_10p a la fila homóloga, nunca a relleno."""
    comparador = _cuerpo_funcion("_hidratarRadarYMarcadores")
    for fuente in ('_hechoNumerico(stLoc, "gc")', '_hechoNumerico(stLoc, "puntos")',
                   "_filaStandings(localNom)", "_filaStandings(visitaNom)", "_porPartido("):
        assert fuente in comparador, (
            "🚨 VIOLACIÓN: El comparador no remata en la fuente soberana '%s'." % fuente)
    for relleno in ("|| 10", ": 1.30", ": 1.20", ": 1.00", ": 2.00", "1.15", "2.54"):
        assert relleno not in comparador, (
            "🚨 VIOLACIÓN [GOVERNANCE-01]: Cifra de relleno '%s' en el comparador." % relleno)
    assert "stLoc.pts_pj" not in comparador and "stLoc.gf_gc" not in comparador, (
        "🚨 VIOLACIÓN: Se está leyendo una clave 10P sobre la fila del Live Board.")


def test_aritmetica_soberana_y_degradacion_honesta_en_la_tabla_nueva():
    """[GOVERNANCE-01] Cociente estricto y '--' cuando el hecho no existe."""
    cociente = _cuerpo_funcion("_porPartido")
    assert "d <= 0" in cociente, (
        "El cociente debe rechazar denominadores no positivos (cero división fabricada).")
    assert "null" in cociente, "El cociente debe degradar a null, nunca a 0."

    cuerpo = _cuerpo_funcion("_hidratarTablasRadiografia")
    assert '"--"' in cuerpo, (
        "🚨 VIOLACIÓN [GOVERNANCE-01]: La tabla estructural debe rotular '--' sin hecho.")
    for disfraz in ("?? 0", "|| 0)"):
        assert disfraz not in cuerpo, (
            "🚨 VIOLACIÓN [GOVERNANCE-01]: '%s' disfraza la ausencia de hecho como cero." % disfraz)

    hecho = _cuerpo_funcion("_hechoNumerico")
    assert "Number.isFinite" in hecho, (
        "🚨 VIOLACIÓN [GOVERNANCE-01]: El hecho numérico exige finitud explícita.")
