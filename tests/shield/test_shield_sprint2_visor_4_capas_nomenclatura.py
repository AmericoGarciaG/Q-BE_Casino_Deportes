# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ DEL VISOR DE CALIBRACIÓN EN CUATRO CAPAS Y NOMENCLATURA AUTODESCRIPTIVA
Gobierno: `docs/DESIGN.md` [DES-QBE-072] / `docs/ARCH.md` [ARCH-1.4.68] / `docs/ARCH.md` [ARCH-1.4.65]

Régimen declarado (Dual-Track honesto):
* **[DIRGEN-STRICT]** — el payload de `/api/markets/backtesting/calibration-report` es la LÍNEA BASE
  INMUTABLE: todo filtrado es proyección en cliente (cero refetch, cero mutación de la bóveda) y el
  agregado re-derivado replica la aritmética ya sellada por `[LN-QBE-100]`.
* **[DBBD-FUNGIBLE]** — `index.html`, `theme.css` y `app.js`: glosario visible, barra de cuatro capas,
  atenuación de exclusiones y banner de denominador.

Cuatro invarianzas (el Juez nace ROJO; el Sprint 2 se certifica al ponerlo VERDE):
1. **NOMENCLATURA** — la capa VISIBLE no publica ni una sigla criptográfica; publica el glosario.
2. **CUATRO CAPAS** — alcance declarado + tres toggles fiduciarios + espejo de compatibilidad sellado
   (`#chk-excluir-vetados`) + banner de denominador.
3. **PROPAGACIÓN ATÓMICA** — macro, meso y micro se repintan en la MISMA pasada y el denominador se
   declara explícitamente (`Mostrando X de N … · N = N`).
4. **LÍNEA BASE INTACTA** — el filtro no reasigna el payload original, no dispara red y la exclusión
   se atenúa con la colorimetría legislada.

[GOV-TEST-01] Aislamiento hermético: lectura estática de archivos; cero red, cero navegador, cero BD.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
APP_JS = RAIZ / "src" / "web" / "static" / "js" / "app.js"
INDEX_HTML = RAIZ / "src" / "web" / "templates" / "index.html"
THEME_CSS = RAIZ / "src" / "web" / "static" / "css" / "theme.css"

# ── Glosario vinculante de [DES-QBE-072] ──────────────────────────────────────────────────────
SIGLAS_DEROGADAS = (
    "P_max",
    "P_mid",
    "P_low",
    "H_fid",
    "S(I)",
    "v_Vol^perp",
    "Masa de Cobertura",
)

GLOSARIO_AUTODESCRIPTIVO = (
    "Acierto Primario",
    "Rescate de Cobertura",
    "Ruptura Residual",
    "Masa Probabilística Ex-Ante",
    "Tasa de Acierto de Cobertura",
    "Suficiencia de Datos",
    "Asedio Territorial Neto",
)

TOGGLES_FIDUCIARIOS = (
    "chk-filtro-epist",
    "chk-filtro-altitud",
    "chk-filtro-fragil",
)


# ── Utilidades de lectura estática (cero expresiones regulares frágiles) ──────────────────────
def _fuente_app() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _html_visible() -> str:
    """Marcado SIN comentarios HTML: la vitrina se audita sobre lo que el Director LEE.

    Los comentarios de trazabilidad legislativa (`[LN-QBE-125]`, anclas de derogación) son memoria
    documental, no cartelera: jamás cuentan como rótulo publicado.
    """
    html = INDEX_HTML.read_text(encoding="utf-8")
    while "<!--" in html and "-->" in html:
        inicio = html.index("<!--")
        fin = html.index("-->", inicio) + len("-->")
        html = html[:inicio] + html[fin:]
    return html


def _cuerpo_funcion(fuente: str, nombre: str) -> str:
    """Cuerpo balanceado de `function nombre(...) { … }`."""
    marca = f"function {nombre}("
    assert marca in fuente, f"La función `{nombre}` desapareció de la cartelera."
    apertura = fuente.index("{", fuente.index(marca))
    profundidad = 0
    for posicion in range(apertura, len(fuente)):
        if fuente[posicion] == "{":
            profundidad += 1
        elif fuente[posicion] == "}":
            profundidad -= 1
            if profundidad == 0:
                return fuente[apertura:posicion + 1]
    raise AssertionError(f"La función `{nombre}` no cierra su bloque.")


# ── INVARIANZA 1: nomenclatura autodescriptiva en la capa visible ─────────────────────────────
def test_invarianza_1_nomenclatura_autodescriptiva_sin_siglas():
    """[DES-QBE-072 §Glosario] La cartelera publica conceptos, jamás siglas criptográficas.

    Prohibido en el marcado visible: `P_max`, `P_mid`, `P_low`, `H_fid`, `S(I)`, `v_Vol^perp` y
    `Masa de Cobertura`. Obligatorio: los siete rótulos del glosario. En `app.js` el rótulo de la
    píldora del vértice consumado se sustituye por el concepto (el literal derogado sólo puede
    sobrevivir como ancla de derogación, nunca como marcado renderizado).
    """
    html = _html_visible().casefold()
    fuente = _fuente_app()

    colisiones = [sigla for sigla in SIGLAS_DEROGADAS if sigla.casefold() in html]
    assert not colisiones, (
        "🚨 SIGLAS EN LA VITRINA: la capa visible sigue rotulando "
        f"{colisiones}. [DES-QBE-072] exige el glosario autodescriptivo."
    )

    ausentes = [termino for termino in GLOSARIO_AUTODESCRIPTIVO if termino.casefold() not in html]
    assert not ausentes, f"🚨 GLOSARIO INCOMPLETO: falta publicar en la vitrina {ausentes}."

    # La píldora del vértice consumado ya no puede renderizar la sigla.
    for literal in ("🎯 ACIERTO P_MAX", "🛡️ RESCATE P_MID", "💀 RUPTURA P_LOW"):
        assert f"{literal}</span>" not in fuente, (
            f"🚨 RÓTULO DEROGADO RENDERIZADO: `{literal}` sigue construyendo marcado en app.js."
        )
    for rotulo in ("Acierto Primario", "Rescate de Cobertura", "Ruptura Residual"):
        assert rotulo in fuente, f"🚨 El glosario `{rotulo}` no llegó a los pintores de app.js."


# ── INVARIANZA 2: arquitectura de cuatro capas declarada ──────────────────────────────────────
def test_invarianza_2_arquitectura_de_cuatro_capas():
    """[ARCH-1.4.68 §P.1–P.3] Capa 0 inmutable, Capa 1 de alcance y Capa 2 fiduciaria conviven.

    El espejo `#chk-excluir-vetados` (`[DES-QBE-067]`) se conserva OCULTO y sincronizado: jamás una
    segunda verdad de estado. `_universoCalibracion` mantiene sus cláusulas selladas.
    """
    html = _html_visible()
    fuente = _fuente_app()

    # Capa 0 — línea base pura.
    assert "window._calibracionPayloadOriginal = data" in fuente

    # Capa 1 — selector de alcance (una sola verdad: `_muestraVisorActiva`).
    for ancla in ('id="visor-capas-container"', 'id="btn-alcance-calibrada"',
                  'id="btn-alcance-global"'):
        assert ancla in html, f"🚨 CAPA 1 AUSENTE: falta `{ancla}` en la vitrina."
    assert 'data-muestra="CALIBRADA"' in html and 'data-muestra="GLOBAL"' in html
    assert "conmutarAlcanceMuestra(" in html
    assert "function conmutarAlcanceMuestra(" in fuente
    assert "function _partidoDentroAlcanceVisor(" in fuente

    # Capa 2 — tres toggles fiduciarios, cada uno con su etiqueta enlazada.
    for toggle in TOGGLES_FIDUCIARIOS:
        assert f'id="{toggle}"' in html, f"🚨 CAPA 2 AUSENTE: falta `#{toggle}`."
        assert f'for="{toggle}"' in html, f"🚨 `#{toggle}` no declara etiqueta accesible (`for`)."
    assert "conmutarFiltrosVisorCalibracion(" in html
    assert "delta_alt_metros >= 1000" in fuente
    assert "< 0.50" in fuente

    # Espejo de compatibilidad: presente, oculto y sincronizado con el toggle de discrepancia.
    assert 'id="chk-excluir-vetados"' in html
    assert 'for="chk-excluir-vetados"' in html
    assert 'class="bt-filtro-vetados visor-espejo-oculto"' in html
    cuerpo_espejo = _cuerpo_funcion(fuente, "_sincronizarEspejoVetadosVisor")
    assert "chk-excluir-vetados" in cuerpo_espejo and "chk-filtro-epist" in cuerpo_espejo

    # Cláusulas selladas de `[DES-QBE-067]` intactas.
    cuerpo_universo = _cuerpo_funcion(fuente, "_universoCalibracion")
    for clausula in ("backtestingReportCache", "filter(", "_partidoVetadoBacktesting",
                     "_agregadoTriadaBacktesting", "filtroInerte"):
        assert clausula in cuerpo_universo, f"🚨 Cláusula sellada `{clausula}` perdida."
    assert "backtestingReportCache =" not in cuerpo_universo

    # Banner de denominador.
    assert 'id="visor-denominador-texto"' in html
    assert 'id="visor-filtro-activo-badge"' in html


# ── INVARIANZA 3: propagación atómica con denominador declarado ───────────────────────────────
def test_invarianza_3_propagacion_atomica_y_denominador():
    """[ARCH-1.4.68 §P.4–P.5] Una sola pasada repinta macro, meso y micro, y declara el denominador.

    La jornada sin partidos activos NO se oculta: se declara `.meso-inactiva` con guiones y conserva
    su acceso a la parrilla micro, donde cada exclusión publica su motivo.
    """
    fuente = _fuente_app()

    cuerpo_orquestador = _cuerpo_funcion(fuente, "aplicarFiltrosVisorCalibracion")
    for destino in ("actualizarMacroCards", "pintarMesoBacktesting",
                    "mostrarMicroJornadaBacktesting", "_actualizarDenominadorVisor"):
        assert destino in cuerpo_orquestador, (
            f"🚨 PROPAGACIÓN ROTA: la pasada atómica no invoca `{destino}`."
        )

    cuerpo_proyeccion = _cuerpo_funcion(fuente, "_proyectarUniversoVisorCalibracion")
    assert "_agregadoTriadaBacktesting" in cuerpo_proyeccion, (
        "El agregado proyectado debe re-derivarse de conteos enteros, no heredarse."
    )
    assert "jornadasServidas" in cuerpo_proyeccion, (
        "La proyección debe iterar las jornadas SERVIDAS (declarar, jamás ocultar)."
    )
    assert "excluidos" in cuerpo_proyeccion

    cuerpo_denominador = _cuerpo_funcion(fuente, "_actualizarDenominadorVisor")
    assert "visor-denominador-texto" in cuerpo_denominador
    assert "Mostrando" in cuerpo_denominador
    assert "excluidos por filtros activos" in cuerpo_denominador
    assert "N = " in cuerpo_denominador

    cuerpo_meso = _cuerpo_funcion(fuente, "pintarMesoBacktesting")
    assert "meso-inactiva" in cuerpo_meso, "La jornada sin activos debe declararse inactiva."
    assert "jornadasServidas" in cuerpo_meso
    assert "bt-btn-micro" in cuerpo_meso, "La jornada inactiva conserva su acceso a la micro."

    cuerpo_micro = _cuerpo_funcion(fuente, "mostrarMicroJornadaBacktesting")
    assert "partido-excluido-filtro" in cuerpo_micro
    assert "badge-excluido-motivo" in cuerpo_micro
    assert "EXCLUIDO" in cuerpo_micro
    assert "backtestingUniversoActual" in cuerpo_micro, (
        "La micro debe seguir consumiendo el universo EFECTIVO (cláusula sellada [LN-QBE-104])."
    )


# ── INVARIANZA 4: línea base intacta y atenuación legislada ───────────────────────────────────
def test_invarianza_4_linea_base_inmutable_y_atenuacion_css():
    """[GOVERNANCE-01] El filtrado es PRESENTACIÓN: la bóveda y el payload certificado no se tocan.

    Además certifica la colorimetría de la exclusión: opacidad 0.35 + desaturación 0.5, de modo que
    un partido excluido siga siendo legible (nunca invisible) en la parrilla.
    """
    fuente = _fuente_app()
    css = THEME_CSS.read_text(encoding="utf-8")

    assert fuente.count("_calibracionPayloadOriginal =") == 1, (
        "🚨 DOBLE VERDAD: el payload original se asigna más de una vez."
    )

    cuerpo_orquestador = _cuerpo_funcion(fuente, "aplicarFiltrosVisorCalibracion")
    assert "fetch(" not in cuerpo_orquestador, "🚨 El filtro refetchea: prohibido por [ARCH-1.4.68]."
    assert "backtestingReportCache =" not in cuerpo_orquestador, (
        "🚨 El filtro reescribe la caché certificada."
    )

    cuerpo_veto = _cuerpo_funcion(fuente, "_partidoVetadoBacktesting")
    assert "SEMAFORO_EPIST_VETO" in cuerpo_veto and "epist" in cuerpo_veto

    # Atenuación legislada.
    assert ".partido-excluido-filtro" in css
    bloque = css[css.index(".partido-excluido-filtro"):]
    bloque = bloque[:bloque.index("}")]
    assert "opacity" in bloque and "0.35" in bloque, "El excluido debe atenuarse al 35 %."
    assert "grayscale" in bloque and "0.5" in bloque, "El excluido debe desaturarse al 50 %."
    assert ".badge-excluido-motivo" in css
    assert ".visor-capas-container" in css
    assert ".meso-inactiva" in css and ".bt-badge-cold-start" in css, (
        "La atenuación meso y el sello de ceguera sellados deben sobrevivir."
    )
