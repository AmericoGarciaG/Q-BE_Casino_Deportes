# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DEL COMPARADOR GRÁFICO DE BARRAS DUALES (HEAD-TO-HEAD)
Contrato vigilado:
- [DES-QBE-063-ext] Sustitución del "Radar Factual de 3 Factores" (prosa generativa)
  por un comparador dual por equipo, hidratado del payload soberano.
- [DES-QBE-063-ext-min] Minimalismo Soberano (Dictamen del Director, Alternativa 2):
  leyenda apilada (Local azul arriba / Visitante verde abajo), 4 métricas de procedencia
  estrictamente soberana (λ/μ, goles_pro → GF/PJ, gf_gc → GC/PJ, pts_pj) y diferencial
  relativo plegado en la etiqueta del líder ("1.95 xG (+0.85)"). Los 4 tags diferenciales
  de la banda derecha fueron extirpados del widget.
- [ARCH-1.4.31] / [LN-QBE-098] Cero red y cero LLM: hidratación local determinista en O(1).
- [GOVERNANCE-01] Cero cifras fabricadas y cero heurísticas proxy: sin evidencia en
  `tabla_10p` se rotula "--" con barra neutra, nunca un valor de relleno.
Régimen: [DBBD-FUNGIBLE] (capa de presentación; Poisson/André/Kelly/persistencia intactos).
Gobierno: [GOV-TEST-01] Aislamiento hermético en memoria (cero red / cero navegador / cero tokens).
"""

from pathlib import Path
import re

INDEX_HTML = Path("src/web/templates/index.html")
APP_JS = Path("src/web/static/js/app.js")

IDS_COMPARADOR = (
    "rad-legend-local", "rad-legend-visita",
    "rad-bar-xg-loc", "rad-val-xg-loc", "rad-bar-xg-vis", "rad-val-xg-vis",
    "rad-bar-sot-loc", "rad-val-sot-loc", "rad-bar-sot-vis", "rad-val-sot-vis",
    "rad-bar-def-loc", "rad-val-def-loc", "rad-bar-def-vis", "rad-val-def-vis",
    "rad-bar-pos-loc", "rad-val-pos-loc", "rad-bar-pos-vis", "rad-val-pos-vis",
)

IDS_TAGS_EXTIRPADOS = (
    "rad-diff-xg-tag", "rad-diff-sot-tag", "rad-diff-def-tag", "rad-diff-pos-tag",
)

IDS_LEGADOS = (
    "rad-fac-ofensiva", "rad-bar-ofensiva",
    "rad-fac-defensa", "rad-bar-defensa",
    "rad-fac-localia", "rad-bar-localia",
)


def _cuerpo_funcion(nombre: str) -> str:
    assert APP_JS.exists(), "Falta src/web/static/js/app.js"
    js = APP_JS.read_text(encoding="utf-8")
    match = re.search(r"function\s+%s\s*\([^)]*\)\s*\{(.*?)\n\}" % nombre, js, re.DOTALL)
    assert match is not None, "Debe existir la función %s en app.js" % nombre
    return match.group(1)


def test_comparador_ids_presentes_y_legados_extirpados():
    """[DES-QBE-063-ext] Las 4 métricas duales existen y el radar legado de 3 factores desapareció."""
    assert INDEX_HTML.exists(), "Falta src/web/templates/index.html"
    html = INDEX_HTML.read_text(encoding="utf-8")

    faltantes = [i for i in IDS_COMPARADOR if 'id="%s"' % i not in html]
    assert not faltantes, "🚨 VIOLACIÓN [DES-QBE-063-ext]: Faltan ids del comparador dual: %s" % faltantes
    assert 'id="rad-top-marcadores"' in html, "El bloque Top-4 Poisson debe permanecer en el modal."

    residuales = [i for i in IDS_LEGADOS if 'id="%s"' % i in html]
    assert not residuales, (
        "🚨 VIOLACIÓN [DES-QBE-063-ext]: Persisten ids del radar de 3 factores: %s" % residuales)


def test_prosa_generativa_extirpada_del_comparador():
    """[LN-QBE-098] La prosa generativa del radar legado no debe sobrevivir en app.js."""
    js = APP_JS.read_text(encoding="utf-8")
    prohibidas = ("genera +", "goles esperados de peligro", "ΔSoTA",
                  "inclina el juego", "muestra mayor exposición")
    for frase in prohibidas:
        assert frase not in js, "🚨 VIOLACIÓN [LN-QBE-098]: Prosa generativa residual: '%s'" % frase


def test_leyenda_tolera_rotulo_con_punto_del_motor():
    """El motor rotula "A vs. B" y el Live Board "A vs B": ambos deben dividirse sin residuo."""
    cuerpo = _cuerpo_funcion("_dividirContendientes")
    assert re.search(r"split\(/\\s\+vs\\\.\?\\s\+/i\)", cuerpo), (
        "🚨 VIOLACIÓN [DES-QBE-063-ext]: El split de contendientes debe admitir 'vs.' y 'vs'.")
    assert 'split(" vs ")' not in APP_JS.read_text(encoding="utf-8"), (
        "🚨 VIOLACIÓN: El split literal ' vs ' rompe con el rótulo 'vs.' del motor.")



    comparador = _cuerpo_funcion("_hidratarRadarYMarcadores")
    assert "_dividirContendientes(p)" in comparador, (
        "El comparador debe resolver la leyenda vía _dividirContendientes(p).")


def test_gf_gc_se_parsea_con_separador_explicito():
    """[GOVERNANCE-01] GC sólo se lee del 2º término de "GF/GC" (o "GF:GC"); nunca por split ciego."""
    cuerpo = _cuerpo_funcion("_golesConcedidos")
    assert re.search(r"match\(/\(\\d\+\)\\s\*\[:/\]\\s\*\(\\d\+\)/\)", cuerpo), (
        "🚨 VIOLACIÓN: _golesConcedidos debe exigir el separador explícito ':' o '/'.")
    for ciego in ('split(":")', "split(':')"):
        assert ciego not in cuerpo, (
            "🚨 VIOLACIÓN [GOVERNANCE-01]: '%s' fabrica un valor de GC inexistente "
            "(ej. '9/9' -> '9 GC' fantasma)." % ciego)


def test_degradacion_honesta_sin_cifras_fabricadas():
    """[GOVERNANCE-01] Sin evidencia 10P: rótulo "--", barra neutra y causa declarada; cero relleno."""
    pintor = _cuerpo_funcion("_pintarBarraComparador")
    assert '"--"' in pintor, "El pintor debe rotular '--' cuando el hecho soberano no existe."
    assert '"50%"' in pintor, "El pintor debe degradar a la barra neutra del 50%."
    assert '"Sin evidencia 10P"' in pintor, (
        "La degradación debe declarar su causa honesta ('Sin evidencia 10P') junto al rótulo '--'.")

    comparador = _cuerpo_funcion("_hidratarRadarYMarcadores")
    for relleno in ("3.8", "5.2", "48.5", "51.5", "1.15", "2.54", "1.30", "1.20"):
        assert relleno not in comparador, (
            "🚨 VIOLACIÓN [GOVERNANCE-01]: Cifra de relleno '%s' inyectada en el comparador." % relleno)


def test_diferencial_plegado_y_tags_diferenciales_extirpados():
    """[DES-QBE-063-ext-min] Dictamen del Director: el diferencial relativo viaja plegado en la
    etiqueta del líder ("1.95 xG (+0.85)") y los tags de la banda derecha NO deben resucitar."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    residuales = [i for i in IDS_TAGS_EXTIRPADOS if 'id="%s"' % i in html]
    assert not residuales, (
        "🚨 VIOLACIÓN [DES-QBE-063-ext-min]: Tags diferenciales residuales en la banda derecha: %s"
        % residuales)

    ventaja = _cuerpo_funcion("_plegarVentaja")
    assert "(+" in ventaja, "El plegado de ventaja debe emitir el patrón '(+X.XX)'."
    deficit = _cuerpo_funcion("_plegarDeficit")
    assert "(-" in deficit, "El plegado de déficit (GC: menos es mejor) debe emitir '(-X.XX)'."

    comparador = _cuerpo_funcion("_hidratarRadarYMarcadores")
    for plegado in ("_plegarVentaja", "_plegarDeficit"):
        assert plegado in comparador, (
            "El comparador debe consumir %s para cada métrica (cero nombres repetidos)." % plegado)
    assert "rad-diff-" not in comparador, (
        "🚨 VIOLACIÓN [DES-QBE-063-ext-min]: El comparador sigue consultando tags extirpados.")


def test_metricas_de_procedencia_estrictamente_soberana():
    """[GOVERNANCE-01] Cada métrica lee un hecho soberano explícito: λ/μ, goles_pro (GF/PJ),
    gf_gc + pj (GC/PJ) y pts_pj. Cero heurísticas proxy y cero cifras de relleno."""
    comparador = _cuerpo_funcion("_hidratarRadarYMarcadores")
    for fuente in ("lamH", "lamA", '"pts_pj"', "_gfPorPartido", "_golesConcedidos", "_juegosJugados"):
        assert fuente in comparador, (
            "🚨 VIOLACIÓN [GOVERNANCE-01]: El comparador no lee la fuente soberana '%s'." % fuente)

    for proxy in ("locSt.xg", "visSt.xg", ".xg ", "1.15", "2.54"):
        assert proxy not in comparador, (
            "🚨 VIOLACIÓN [GOVERNANCE-01]: Operando no soberano '%s' en el comparador "
            "(el xG de standings es un proxy heurístico, no evidencia)." % proxy)

    produccion = _cuerpo_funcion("_gfPorPartido")
    assert "goles_pro" in produccion, (
        "GF/PJ debe provenir del hecho soberano 'goles_pro' emitido por el motor.")
    assert "[:/]" in produccion, (
        "🚨 VIOLACIÓN: El 1er término de 'goles_pro' exige el separador explícito ':' o '/'.")
    for ciego in ('split(":")', "split(':')", "split('/')"):
        assert ciego not in produccion, (
            "🚨 VIOLACIÓN [GOVERNANCE-01]: '%s' no lee el hecho soberano, lo interpreta." % ciego)

    standings = _cuerpo_funcion("_filaStandings")
    assert "=== objetivo" in standings, (
        "🚨 VIOLACIÓN [GOVERNANCE-01]: El cruce de standings exige igualdad estricta de nombre "
        "normalizado; prohibido adivinar por posición.")


def test_leyenda_apilada_con_orden_soberano_de_contendientes():
    """[DES-QBE-063-ext-min] Dictamen del Director: leyenda apilada vertical con el Local (azul)
    arriba y el Visitante (verde) abajo, sin rótulos de diferencial en la banda derecha."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    i_loc = html.find('id="rad-legend-local"')
    i_vis = html.find('id="rad-legend-visita"')
    assert i_loc > 0 and i_vis > i_loc, (
        "🚨 VIOLACIÓN: La leyenda debe listar al Local arriba y al Visitante abajo.")
    zona = html[max(0, i_loc - 1500):i_vis + 400]
    assert "flex-direction: column" in zona, (
        "🚨 VIOLACIÓN [DES-QBE-063-ext-min]: La leyenda debe apilarse verticalmente.")
    assert "#38bdf8" in zona and "#00e676" in zona, (
        "🚨 VIOLACIÓN [DES-QBE-063-ext-min]: La leyenda debe conservar la colorimetría Local/Visitante.")
    assert 'id="rad-diff-' not in zona, (
        "🚨 VIOLACIÓN [DES-QBE-063-ext-min]: Rótulo diferencial residual junto a la leyenda.")


def test_poisson_verbatim_y_top4_intacto():
    """[LN-QBE-040] La densidad Poisson local y el bloque Top-4 permanecen verbatim."""
    poisson = _cuerpo_funcion("_calcularPoissonP")
    assert "for (let i = 2; i <= k; i++) fact *= i;" in poisson, (
        "🚨 ALTERACIÓN: El factorial del Poisson local fue modificado.")
    assert "return (Math.pow(lambda, k) * Math.exp(-lambda)) / fact;" in poisson, (
        "🚨 ALTERACIÓN: La densidad P(X=k) = lambda^k · e^-lambda / k! fue modificada.")

    comparador = _cuerpo_funcion("_hidratarRadarYMarcadores")
    assert "scores.slice(0, 4)" in comparador, "El Top-4 de marcadores debe permanecer intacto."
    assert "_calcularPoissonP(lamH, x) * _calcularPoissonP(lamA, y)" in comparador, (
        "🚨 ALTERACIÓN: La rejilla Poisson 0..3 del Top-4 fue modificada.")


def test_comparador_se_hidrata_al_abrir_el_modal():
    """El comparador debe seguir siendo invocado desde abrirRadiografiaForense (sin fetch/LLM)."""
    apertura = _cuerpo_funcion("abrirRadiografiaForense")
    assert "_hidratarRadarYMarcadores(p)" in apertura, (
        "El modal debe hidratar el comparador dual al abrirse.")
    assert "match-thesis" not in apertura, (
        "🚨 VIOLACIÓN [LN-QBE-098]: El modal no debe tocar el endpoint de Gemini.")
