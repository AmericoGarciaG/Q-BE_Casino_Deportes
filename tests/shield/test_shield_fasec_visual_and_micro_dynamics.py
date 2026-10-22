# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DE LA FASE C: VITRINA 32V Y MICRO-DINÁMICAS ESPEJO
Gobierno: `docs/DESIGN.md` [DES-QBE-070-B] / `docs/ARCH.md` [ARCH-1.4.62] / `[LN-QBE-112]`

Régimen declarado: `[HÍBRIDO DUAL-TRACK]`
* `[DBBD-FUNGIBLE]`: capa de presentación (`src/web/**`) y COMPOSICIÓN del sandbox de
  laboratorio (`scripts/laboratorio/sandbox_micro_dinamicas_pipeline.py`).
* `[DIRGEN-STRICT]`: intacto. Este Juez NO toca `src/core/**`, `src/storage/**` ni el DTO
  `AtribucionFactorialOut`; las tres funciones puras de `[LN-QBE-112]`
  (`calcular_ratio_cronometria`, `evaluar_alerta_fragilidad_cierre`,
  `calcular_indice_rotacion_xi`) se ejercitan en su propio Juez y aquí se dan por selladas.

[GOV-TEST-01] Aislamiento hermético: lectura de archivos del repositorio + ejecución del sandbox
real en modo sólo lectura (sin red, sin escritura en la 3NF, sin dobles de prueba).

Tres defectos legislados que este Juez clausura:

1. **Deriva nominal de vitrina.** La SPA seguía rotulando «44 Variables» / «44 variables» /
   «(44V)» y un subtítulo con «12 dimensiones», aunque el catálogo vigente es de 32 celdas en 6
   familias canónicas ([LN-QBE-120] / [ARCH-1.4.60] / [ARCH-1.4.61]).
2. **Ramas de familia fantasma.** El despachador del Hero Card conservaba `𝒯_Shk` y `𝒯_H2H`,
   familias que la purga nominal eliminó: su lectura quedó consolidada dentro de `𝒯_Ctx`.
3. **Sandbox desalineado.** `sandbox_micro_dinamicas_pipeline.py` seguía emitiendo cinco
   dimensiones del régimen derogado (5/6/9/10/12) y su semáforo `disciplina_roja` leía `V24`,
   celda que el catálogo de 32 reasigna a **Penales Favor/Contra**.

ANCLA DE MUTACIÓN: el contrato de red y DOM **no** se renombra —`#modal-44-variables`, las clases
`vars44-*`, `.btn-ver-44-vars`, `abrirModal44Variables()` y `atribucion_factorial.variables_44`
sobreviven ([ARCH-1.4.57]). Lo que se purga es el RÓTULO visible y la deriva interna de helpers.
"""

import re
from pathlib import Path

from scripts.laboratorio import sandbox_micro_dinamicas_pipeline as sandbox

RUTA_APP_JS = Path("src/web/static/js/app.js")
RUTA_HTML = Path("src/web/templates/index.html")
RUTA_SANDBOX = Path("scripts/laboratorio/sandbox_micro_dinamicas_pipeline.py")

# Rótulos derogados por [DES-QBE-070-B]: el régimen de 44 celdas / 12 dimensiones no se exhibe.
# `44V` se audita aparte con frontera de palabra: la ancla `abrirModal44Variables` (contrato de
# DOM/JS sellado por [ARCH-1.4.57]) no es un rótulo y debe sobrevivir.
ROTULOS_DEROGADOS = (
    "44 Variables",
    "44 variables",
    "44 VARIABLES",
    "12 dimensiones",
)

# Anclas de contrato congelado ([ARCH-1.4.57] / [DES-QBE-070-B]): NO se renombran.
ANCLAS_CONTRATO = (
    'id="modal-44-variables"',
    "vars44-cuerpo",
    "btn-ver-44-vars",
    "abrirModal44Variables",
    "variables_44",
)

CLAVE_DIMENSION = "dimension_5_balon_parado_y_disciplina"
IDS_ESPECIALES = ("V21", "V22", "V23", "V24", "V25")

# Dimensiones derogadas por [ARCH-1.4.61] / [ARCH-1.4.62]: prohibidas en el reporte y en la fuente.
CLAVES_DEROGADAS = (
    "dimension_5_balon_parado",
    "dimension_6_disciplina",
    "dimension_9_cronometria",
    "dimension_10_banca",
    "dimension_12_cierre",
)


def _fuente(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


# ── TEST 1 — [DES-QBE-070-B] La vitrina publica 32V y no exhibe el régimen derogado ───────────────
def test_vitrina_publica_32v_sin_rotulos_derogados():
    """Cero literales «44V» en la capa visible; el rótulo vigente es 32V / 6 dimensiones.

    La purga es de PRESENTACIÓN: las anclas de contrato (`#modal-44-variables`, `vars44-*`,
    `.btn-ver-44-vars`, `abrirModal44Variables()`, `variables_44`) sobreviven porque son DOM y
    contrato de red sellado. El Juez exige, en el mismo acto, su supervivencia.
    """
    app_js = _fuente(RUTA_APP_JS)
    html = _fuente(RUTA_HTML)

    for rotulo in ROTULOS_DEROGADOS:
        assert rotulo not in app_js, (
            f"Rótulo derogado `{rotulo}` sobrevive en `app.js`: [DES-QBE-070-B] lo prohíbe."
        )
        assert rotulo not in html, (
            f"Rótulo derogado `{rotulo}` sobrevive en `index.html`: [DES-QBE-070-B] lo prohíbe."
        )

    # `44V` con frontera de palabra: castiga el rótulo «(44V)» sin matar la ancla de contrato.
    for etiqueta, corpus in (("app.js", app_js), ("index.html", html)):
        assert re.search(r"44V\b", corpus) is None, (
            f"Rótulo derogado `44V` sobrevive en `{etiqueta}`: [DES-QBE-070-B] lo prohíbe."
        )

    # El botón del micro-HUD publica la cardinalidad VIGENTE.
    assert "🔬 Catálogo Fáctico (32V)" in app_js, (
        "El acceso forense del micro-HUD debe rotular `🔬 Catálogo Fáctico (32V)`."
    )

    # El modal declara 32 variables / 6 dimensiones canónicas (ni 44 ni 12).
    assert "32 variables" in html, "El título del modal debe declarar `32 variables`."
    assert "6 dimensiones canónicas" in html, (
        "El subtítulo del modal debe declarar `6 dimensiones canónicas`."
    )

    # La sonda de completitud del Centro de Control también se rotula en 32V.
    assert "Auditoría de Completitud Fáctica (32V)" in html, (
        "El botón del panel 🛡️ debe rotular la sonda en 32V."
    )
    assert "catálogo de 32 variables" in html, (
        "El tooltip de la sonda debe declarar el catálogo de 32 variables."
    )

    # Ancla de mutación: el contrato de red/DOM NO se renombra.
    for ancla in ANCLAS_CONTRATO:
        corpus = html if ancla.startswith("id=") or ancla == "vars44-cuerpo" else app_js
        assert ancla in corpus, (
            f"Ancla de contrato demolida por la purga de vitrina: {ancla} ([ARCH-1.4.57])."
        )


# ── TEST 2 — [ARCH-1.4.62] Sandbox espejo: una dimensión, cinco celdas, FASE 6 forzada ───────────
def test_sandbox_espeja_una_dimension_te_spc_en_fase_6():
    """El reporte emite SÓLO `dimension_5_balon_parado_y_disciplina` con V21-V25 sin magnitud.

    La atenuación es de RÉGIMEN, no de conteo: ninguna de las cinco celdas puede publicar `0.00`
    ni magnitud alguna mientras el corpus congelado no tenga feed de pelota parada, córners,
    penales o tarjetas ([GOVERNANCE-01]: cero maquillaje).
    """
    fuente = _fuente(RUTA_SANDBOX)

    # 1) Contrato declarado del módulo.
    assert dict(sandbox._DIMENSIONES) == {CLAVE_DIMENSION: IDS_ESPECIALES}, (
        f"`_DIMENSIONES` debe declarar exactamente {CLAVE_DIMENSION} con {IDS_ESPECIALES}."
    )
    assert sandbox.TOTAL_VARIABLES == 5, "`TOTAL_VARIABLES` debe ser 5 (𝒯_Spc del catálogo de 32)."

    # 2) Cero rastro de las dimensiones derogadas en la fuente (ni en comentarios).
    #    Se compara la clave ENTRE COMILLAS porque `dimension_5_balon_parado` es prefijo de la
    #    clave canónica `dimension_5_balon_parado_y_disciplina` (falso positivo de subcadena).
    for clave in CLAVES_DEROGADAS:
        assert '"' + clave + '"' not in fuente, (
            f"Clave derogada `{clave}` sobrevive en el sandbox: [ARCH-1.4.62] la purga."
        )
    for identificador in ("V18", "V19", "V20", "V33", "V37", "V43", "V44"):
        assert '"' + identificador + '"' not in fuente, (
            f"Identificador derogado `{identificador}` sobrevive en la taxonomía del sandbox."
        )

    # 3) Ejecución REAL en corte N−1 (sólo lectura, cero red).
    reporte = sandbox.ejecutar_sandbox_micro_dinamicas_partido(match_id="LIGAMX-J11-07")
    assert isinstance(reporte, dict) and reporte.get("status") in (
        "EXITO", "PARCIAL", "SIN_EVIDENCIA", "NO_ENCONTRADO"
    ), "El sandbox debe publicar un reporte honesto con status declarado."

    # 4) La dimensión es la ÚNICA del contrato canónico.
    assert CLAVE_DIMENSION in reporte, f"Falta la dimensión canónica `{CLAVE_DIMENSION}`."
    for clave in CLAVES_DEROGADAS:
        assert clave not in reporte, (
            f"El reporte sigue emitiendo la dimensión derogada `{clave}`."
        )

    # 5) Cinco celdas, todas SIN EVIDENCIA con `None` bipartito y nota de Fase 6.
    celdas = reporte[CLAVE_DIMENSION]
    assert tuple(sorted(celdas)) == IDS_ESPECIALES, (
        f"`{CLAVE_DIMENSION}` debe publicar exactamente {IDS_ESPECIALES}; publicó {sorted(celdas)}."
    )
    for identificador in IDS_ESPECIALES:
        celda = celdas[identificador]
        assert celda["estado"] == "SIN EVIDENCIA", (
            f"{identificador} debe declararse SIN EVIDENCIA (FASE 6), no {celda['estado']}."
        )
        assert celda["local"] is None and celda["visita"] is None, (
            f"{identificador} publicó magnitud sin feed: imputación prohibida ([GOVERNANCE-01])."
        )
        assert "FASE 6" in str(celda["nota"]), (
            f"{identificador} debe declarar `FASE 6` en su nota de evidencia."
        )

    # 6) Contadores y salvaguardas fiduciarias coherentes con el contrato de 5 celdas.
    assert reporte.get("celdas_evaluadas") == 0, "Cero celdas evaluadas: 𝒯_Spc está en Fase 6."
    assert reporte.get("celdas_totales") == 5, "El denominador debe ser 5, no 15/44."
    assert reporte.get("status") == "SIN_EVIDENCIA", (
        "Con 0/5 celdas el status honesto es SIN_EVIDENCIA."
    )
    assert reporte.get("escritura_bd") is False and reporte.get("llamadas_red") is False, (
        "El sandbox es de sólo lectura y sin red ([GOV-TEST-01] / [LN-QBE-112])."
    )

    # 7) La salpicadura a +PA ([LN-QBE-083]) sobrevive como lectura NO COMPUTABLE, jamás inventada.
    alerta = reporte.get("alerta_cierre") or {}
    assert alerta.get("riesgo_global") is None, (
        "Sin xGA tardío no se emite juicio sobre el Pago Anticipado."
    )
    assert "SIN EVIDENCIA" in str(alerta.get("cobertura_pa")), (
        "La cobertura +PA debe declararse NO COMPUTABLE — SIN EVIDENCIA."
    )

    # 8) Los bloques derivados de celdas inexistentes fueron retirados del reporte.
    for bloque in ("ratios_cronometria", "indice_riesgo_roja"):
        assert bloque not in reporte, (
            f"El bloque `{bloque}` leía celdas derogadas (V33/V34, V24): [ARCH-1.4.62] lo retira."
        )


# ── TEST 3 — [DES-QBE-070-B] Seis familias canónicas: 𝒯_Spc atenuada y 𝒯_Ctx consolidado ─────────
def test_hero_card_cubre_seis_familias_canonicas():
    """El despachador realinea ids canónicos: `𝒯_Shk`/`𝒯_H2H` mueren, `𝒯_Ctx` los absorbe."""
    app_js = _fuente(RUTA_APP_JS)

    assert "function _cardDimension32(" in app_js, "Falta el despachador polimórfico del Card."
    assert "_cardDimension32(dimension)" in app_js, "El acordeón no invoca el Card por dimensión."
    assert "dimensiones.map(_tablaDimension32)" in app_js, (
        "La tabla forense de [DES-QBE-064] debe sobrevivir como soporte de auditoría."
    )

    inicio = app_js.index("[DES-QBE-070-B] CARDS SEMÁNTICOS")
    fin = app_js.index("function abrirModal44Variables(", inicio)
    bloque = app_js[inicio:fin]

    # 1) Cero helpers del régimen derogado en el renderizador.
    heredados = re.findall(r"_[A-Za-z]+44\(", bloque)
    assert not heredados, f"Helpers del régimen 44V sobreviven en el Card: {sorted(set(heredados))}"

    # 2) Las familias extintas no se despachan (su lectura vive en `𝒯_Ctx`).
    assert 'familia === "Shk"' not in bloque, "La familia 𝒯_Shk no existe en el catálogo de 32."
    assert 'familia === "H2H"' not in bloque, "La familia 𝒯_H2H no existe en el catálogo de 32."

    # 3) Anatomías por familia con ids canónicos.
    for literal in (
        "_cardPosesion32(dimension)",
        '_rejillaCard32(dimension, ["V02", "V03", "V04", "V05"])',
        '_balanzaGoles32(dimension, "V06", "xG")',
        '_rejillaCard32(dimension, ["V07", "V08", "V09", "V10", "V11"])',
        '_balanzaGoles32(dimension, "V12", "xGA")',
        '_balanzaGoles32(dimension, "V18", "Atajadas")',
        '_rejillaCard32(dimension, ["V21", "V22", "V23", "V24", "V25"])',
        '_celda32(dimension, "V26")',
        '_celda32(dimension, "V27")',
        '_celda32(dimension, "V28")',
        '_celda32(dimension, "V29")',
        '_celda32(dimension, "V30")',
        '_celda32(dimension, "V32")',
        '_rejillaCard32(dimension, ["V31"])',
    ):
        assert literal in bloque, f"Anatomía canónica ausente en el Hero Card: {literal}"

    # 4) 𝒯_Spc se atenúa SIEMPRE (régimen de evidencia, no conteo servido).
    assert 'familia === "Spc"' in bloque, "Falta la rama explícita de 𝒯_Spc."
    inicio_spc = bloque.index('familia === "Spc"')
    rama_spc = bloque[inicio_spc:bloque.index("} else if", inicio_spc)]
    assert "card-fase6-muted" in rama_spc, (
        "La atenuación de 𝒯_Spc debe declararse en su propia rama, no depender del conteo servido."
    )

    # 5) Blindaje fiduciario: cero matemática de modelo en el renderizador.
    for prohibido in ("Math.log", "Math.exp", "Math.pow", "innerHTML"):
        assert prohibido not in bloque, (
            f"El Card derivó magnitud en cliente (`{prohibido}`): [GOVERNANCE-01] exige transcripción pura."
        )

