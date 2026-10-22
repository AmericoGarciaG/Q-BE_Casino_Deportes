# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DE LOS CARDS POLIMÓRFICOS Y EL RETIRO VISUAL DE EPIST (FASE 3)
Gobierno: `docs/DESIGN.md` [DES-QBE-070] / [DES-QBE-071] / `docs/ARCH.md` [ARCH-1.4.57]

Régimen declarado: [DBBD-FUNGIBLE] — capa de presentación (`src/web/static/**`, `src/web/templates/**`).
Ninguna aserción toca `src/core/**`, `src/storage/**` ni el DTO `AtribucionFactorialOut`: el Hallazgo
Maestro de la Fase 3 certificó que las magnitudes de los Cards ya viajan al cliente dentro de
`atribucion_factorial.variables_44` (incluidas las celdas en cadena `V39`/`V40`/`V41`), por lo que la
ÚNICA fuente legislada es ese bloque servido.

[GOV-TEST-01] Aislamiento hermético: sólo lectura de archivos del repositorio. Cero red, cero navegador.

Tres defectos legislados que este Juez clausura:
1. `● EPIST` persistía en la capa visible (micro-HUD y panel de semáforos del modal) como quinto
   veredicto interno, mezclando un juicio epistémico con la tetralogía fáctica de datos.
2. Las 44 variables se exhibían sólo como tabla plana de 7 columnas: ilegible como insight deportivo
   (posesión, balanza de goles, récord H2H) aun cuando la magnitud REAL ya estaba servida.
3. Riesgo de recálculo en cliente: cualquier derivación local (`Math.log`, λ, Δlog) violaría
   `[GOVERNANCE-01]`. El Juez certifica transcripción pura de celdas servidas.

ANCLA DE MUTACIÓN: `[DES-QBE-071]` retira EPIST **de la vista**, jamás del gobierno: el filtro
anti-cuarentena `#chk-excluir-vetados` ([DES-QBE-067]) sigue leyendo `semaforos["epist"]` por acceso
indexado y `SEMAFORO_EPIST_VETO` debe sobrevivir intacto.
"""

from pathlib import Path

RUTA_APP_JS = Path("src/web/static/js/app.js")
RUTA_CSS = Path("src/web/static/css/theme.css")
RUTA_HTML = Path("src/web/templates/index.html")

CLASES_CARD = (
    "card-semantico-dimension",
    "barra-posesion-dual",
    "balanza-goles-badge",
    "card-fase6-muted",
)

# Tetralogía fáctica legislada por [DES-QBE-071] (EPIST queda fuera de la vitrina).
TETRALOGIA = ("opta", "sede", "h2h", "ctx")


def _fuente(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


# ── TEST 1 — [DES-QBE-071] Retiro visual de EPIST y tetralogía fáctica ────────────────────────────
def test_retiro_visual_de_epist_y_tetralogia_factica():
    """El HUD visible publica `● OPTA ● SEDE ● H2H ● CTX`; EPIST desaparece de la vista.

    El retiro es de PRESENTACIÓN: el semáforo sigue en el payload y el veto anti-cuarentena
    ([DES-QBE-067]) lo lee por acceso indexado. Por eso el Juez exige, en el mismo acto, la
    supervivencia de `SEMAFORO_EPIST_VETO` y del literal `"epist"` dentro del cuerpo del filtro.
    """
    app_js = _fuente(RUTA_APP_JS)
    css = _fuente(RUTA_CSS)

    # 1) Cero pilón epistémico en la capa visible (ni en el micro-HUD ni en el panel del modal).
    assert "● EPIST" not in app_js, (
        "El pilón `● EPIST` sobrevive en la capa visible: [DES-QBE-071] lo prohíbe."
    )
    assert "card-semaforo-epist" not in app_js and "card-semaforo-epist" not in css, (
        "Clase `card-semaforo-epist` prohibida por [DES-QBE-071]."
    )
    assert "vars44-semaforo" in app_js, "El panel de semáforos del modal debe conservarse."

    # 2) La tira del micro-HUD declara EXACTAMENTE la tetralogía fáctica.
    inicio_tira = app_js.index("const tiraSemaforos")
    tira = app_js[inicio_tira:app_js.index("].map(clave", inicio_tira)]
    for clave in TETRALOGIA:
        assert f'"{clave}"' in tira, f"Semáforo fáctico ausente en la tira: {clave}"
    assert '"epist"' not in tira, "EPIST sigue formando parte de la tira visible del micro-HUD."

    # 3) El catálogo de rótulos del modal tampoco rotula EPIST.
    inicio_etiquetas = app_js.index("const ETIQUETAS_SEMAFORO_44 = {")
    etiquetas = app_js[inicio_etiquetas:app_js.index("};", inicio_etiquetas)]
    for clave in TETRALOGIA:
        assert f"{clave}:" in etiquetas, f"Rótulo ausente en el modal: {clave}"
    assert "epist" not in etiquetas, (
        "EPIST sigue rotulado en `.vars44-semaforos`: [DES-QBE-071] lo retira de la vitrina."
    )

    # 4) Certificación de NO mutación del gobierno: el veto sigue leyendo la clave real.
    assert 'const SEMAFORO_EPIST_VETO = "ROJO";' in app_js, (
        "El sello del veto epistémico fue demolido: [DES-QBE-067] lo necesita intacto."
    )
    inicio_veto = app_js.index("function _partidoVetadoBacktesting(")
    cuerpo_veto = app_js[inicio_veto:app_js.index("}", app_js.index("SEMAFORO_EPIST_VETO", inicio_veto))]
    assert '"epist"' in cuerpo_veto and "SEMAFORO_EPIST_VETO" in cuerpo_veto, (
        "El filtro anti-cuarentena debe seguir leyendo `semaforos[\"epist\"]`: retiro visual ≠ retiro de gobierno."
    )


# ── TEST 2 — [DES-QBE-070] Colorimetría y geometría legisladas de los Cards ───────────────────────
def test_theme_css_legisla_los_cards_polimorficos():
    """Las cuatro clases del Card Semántico existen en `theme.css` con la paleta Dark Fintech."""
    css = _fuente(RUTA_CSS)
    html = _fuente(RUTA_HTML)

    for clase in CLASES_CARD:
        assert f".{clase}" in css, f"Clase de Card ausente en `theme.css`: .{clase}"

    # Paleta sellada (`[DES-QBE-066]` conserva la suya): verde evaluado, azul derivado/contexto,
    # ámbar, rojo y gris de ausencia.
    for color in ("#10B981", "#38BDF8", "#F59E0B", "#EF4444", "#94A3B8"):
        assert color in css, f"Colorimetría Dark Fintech ausente: {color}"

    inicio_muted = css.index(".card-fase6-muted")
    bloque_muted = css[inicio_muted:css.index("}", inicio_muted)]
    assert "#475569" in bloque_muted or "#94A3B8" in bloque_muted, (
        "El Card atenuado de Fase 6 debe declarar su gris de ausencia (coherencia con [DES-QBE-066])."
    )

    inicio_posesion = css.index(".barra-posesion-dual")
    bloque_posesion = css[inicio_posesion:css.index("}", inicio_posesion)]
    assert "flex" in bloque_posesion or "grid" in bloque_posesion, (
        "La barra dual de posesión requiere geometría de dos carriles."
    )

    # El contenedor del modal sigue siendo el único punto de hidratación servido.
    assert 'id="vars44-cuerpo"' in html, "El modal forense perdió su cuerpo hidratable."


# ── TEST 3 — [DES-QBE-070] Transcripción pura de `variables_44` (cero recálculo) ──────────────────
def test_cards_consumen_variables_44_sin_recalculo_en_cliente():
    """El Card se compone de celdas SERVIDAS: prohibido derivar λ, Δlog o récords en el cliente."""
    app_js = _fuente(RUTA_APP_JS)

    assert "function _cardDimension44(" in app_js, "Falta el despachador polimórfico del Card."
    assert "_cardDimension44(dimension)" in app_js, "El acordeón no invoca el Card por dimensión."

    inicio = app_js.index("   [DES-QBE-070] CARDS SEMÁNTICOS")
    fin = app_js.index("function abrirModal44Variables(", inicio)
    bloque = app_js[inicio:fin]

    for clase in CLASES_CARD:
        assert clase in bloque, f"El renderizador de Cards no materializa la clase: {clase}"

    # Anatomías legisladas: posesión dual, altitud/descanso y récord H2H verbatim.
    for literal in ("Posesión", "Altitud", "Descanso", "H2H", "xG"):
        assert literal in bloque, f"Anatomía legislada ausente en los Cards: {literal}"

    # Blindaje fiduciario: cero matemática de modelo y cero hidratación por marcado crudo.
    for prohibido in ("Math.log", "Math.exp", "Math.pow", "lambda_", "innerHTML"):
        assert prohibido not in bloque, (
            f"El Card derivó magnitud en cliente (`{prohibido}`): [GOVERNANCE-01] exige transcripción pura."
        )

    # Las celdas en cadena (`V39` — `'3V - 1E - 0D'`) sobreviven gracias a `_valor44`.
    assert "_valor44(" in bloque, "El Card debe transcribir las celdas servidas vía `_valor44`."
    assert "(Fase 6)" in bloque, "El Card atenuado debe rotular su Fase 6 sin fabricar ceros."

    # Enmienda, no deroga: la tabla numérica de 7 columnas de [DES-QBE-064] sobrevive.
    assert "dimensiones.map(_tablaDimension44)" in app_js, (
        "La tabla forense fue demolida: [DES-QBE-070] la conserva como soporte de auditoría."
    )
    assert "vars44-tabla" in app_js, "El soporte tabular debe seguir presente."
