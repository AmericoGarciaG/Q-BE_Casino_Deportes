# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DEL SELLO OPTA, LA MEMORIA H2H CONGELADA Y EL ACORDEÓN BICOLOR
Gobierno: `docs/LOGIC.md` [LN-QBE-103] / `docs/ARCH.md` [ARCH-1.4.44] / `docs/DESIGN.md` [DES-QBE-066]

Régimen declarado (Dual-Track honesto):
- [DIRGEN-STRICT] en la extracción H2H (futuro-ceguera, deduplicación, perspectiva), en la
  certificación tri-estado de la procedencia Opta y en la telemetría dimensional.
- [DBBD-FUNGIBLE] en la presentación (acordeón bicolor del modal de 44 variables).

[GOV-TEST-01] Aislamiento hermético: cero red, cero navegador. El corpus sintético vive en
`tmp_path` y la bóveda 3NF se materializa en un motor `sqlite://` en memoria.

Cinco defectos legislados que este Juez clausura:
1. `OPTA` en rojo sobre evidencia real: sin el sello `xg_es_real_opta` el semáforo degradaba a 🔴
   aun con `xg_local_rate`/`xg_visita_rate` publicadas. El tri-estado distingue VERDE (Opta real
   bilateral), AMARILLO (métrica publicada, procedencia no certificada) y ROJO (sin métrica).
2. `H2H` neutral por ausencia estructural de fuente: la tabla `matches` es monotorneo, de modo que
   el proveedor `[ARCH-1.4.44]` restituye la memoria longitudinal desde el corpus congelado.
3. Puente de identidad roto (`slugs` comparados contra nombres de exhibición ⇒ cero duelos).
4. `V10` apagada cuando el generador publica `gc_*_rate` sin `xga_*_rate` (Axioma 4 incompleto).
5. Acordeón sin distinción visual entre dimensión evaluada y dimensión en fase 6.
"""

import json
import re
from datetime import datetime
from pathlib import Path

import pytest

RUTA_PROVEEDOR = Path("src/core/sovereign/h2h_provider.py")
RUTA_ATRIBUCION = Path("src/core/sovereign/factor_attribution.py")
RUTA_APP_JS = Path("src/web/static/js/app.js")
RUTA_CSS = Path("src/web/static/css/theme.css")
RUTA_CORPUS_REAL = Path("data/cache_h2h_liga_mx_2026.json")

# ── Fixture de verdad sellada: paquete vivo completo (las 8 variables del Axioma 4) ─────────────
INSUMOS_VIVOS = {
    "xg_local_rate": 1.42,
    "xg_visita_rate": 1.18,
    "xga_local_rate": 1.05,
    "xga_visita_rate": 1.31,
    "gc_local_rate": 1.10,
    "gc_visita_rate": 1.20,
    "sot_local": 5.0,
    "sot_visita": 4.0,
    "sota_local": 3.0,
    "sota_visita": 4.0,
    "poss_local": 53.5,
    "poss_visita": 46.5,
    "pj_sede_local": 5,
    "pj_sede_visita": 4,
    "h2h_conteo": 5,
    "q_mod_h": 1.0,
    "q_mod_a": 1.0,
    "delta_alt_metros": -150.0,
    "delta_descanso_dias": 3.0,
    "xg_es_real_opta": True,
}

DIMENSIONES_CON_DATOS = {"𝒯_Vol", "𝒯_Rem", "𝒯_Def", "𝒯_Ctx"}


def _dimensiones(bloque):
    raiz = bloque.get("variables_44") if isinstance(bloque.get("variables_44"), dict) else bloque
    return {d["dimension"]: d for d in raiz["dimensiones"]}


# ────────────────────────────────────────────────────────────────────────────────────────────────
# INVARIANZA 1 — CERTIFICACIÓN TRI-ESTADO DE LA PROCEDENCIA OPTA
# ────────────────────────────────────────────────────────────────────────────────────────────────
def test_semaforo_opta_tri_estado():
    """[INVARIANZA 1 — TRES ESTADOS HONESTOS, CERO ROJO SOBRE EVIDENCIA]:
    🟢 sólo con certificación bilateral de Opta real; 🟡 con métrica publicada pero procedencia no
    certificada; 🔴 únicamente cuando no hay métrica que juzgar.
    """
    from src.core.sovereign.factor_attribution import construir_atribucion_factorial

    verde = construir_atribucion_factorial({"insumos_factivados": dict(INSUMOS_VIVOS)})
    assert verde["semaforos"]["opta"] == "VERDE", (
        "El sello `xg_es_real_opta=True` debe encender el semáforo OPTA en verde."
    )

    amarillo = construir_atribucion_factorial({
        "insumos_factivados": {**INSUMOS_VIVOS, "xg_es_real_opta": False}
    })
    assert amarillo["semaforos"]["opta"] == "AMARILLO", (
        "Con xG publicado pero sin certificación Opta bilateral el veredicto honesto es AMARILLO."
    )

    sin_sello = {
        clave: valor for clave, valor in INSUMOS_VIVOS.items() if clave != "xg_es_real_opta"
    }
    heredado = construir_atribucion_factorial({"insumos_factivados": sin_sello})
    assert heredado["semaforos"]["opta"] == "AMARILLO", (
        "La ausencia del sello no autoriza rojo: la métrica xG está publicada y debe juzgarse."
    )

    sin_metrica = construir_atribucion_factorial({
        "insumos_factivados": {
            "h2h_conteo": 5,
            "pj_sede_local": 4,
            "pj_sede_visita": 4,
            "xg_es_real_opta": False,
        }
    })
    assert sin_metrica["semaforos"]["opta"] == "ROJO", (
        "Sin ninguna tasa xG el semáforo OPTA debe declarar ROJO."
    )

    # La ignorancia canónica S(I)=0 jamás puede maquillarse de verde.
    ignorancia = construir_atribucion_factorial({
        "insumos_factivados": {**INSUMOS_VIVOS, "xg_es_real_opta": None},
        "S_I": 0,
    })
    assert ignorancia["semaforos"]["opta"] == "ROJO"


def test_predicado_de_procedencia_opta_real():
    """[INVARIANZA 1-bis — TAXONOMÍA CERRADA]: sólo las fuentes fácticas FotMob/Opta certifican
    Opta real; el respaldo calibrado `calibrado_gf` NUNCA se certifica como métrica real.
    """
    from scripts.ingesta.homologar_temporada_optah2h import (
        PROCEDENCIA_CACHE,
        PROCEDENCIA_CALIBRADA,
        PROCEDENCIA_SENSOR,
        PROCEDENCIA_TELEMETRIA,
        es_procedencia_opta_real,
    )

    for real in (PROCEDENCIA_CACHE, PROCEDENCIA_TELEMETRIA, PROCEDENCIA_SENSOR):
        assert es_procedencia_opta_real(real) is True, f"Fuente fáctica no certificada: {real}"
    for espuria in (PROCEDENCIA_CALIBRADA, "sin_fuente", "", None):
        assert es_procedencia_opta_real(espuria) is False, (
            f"Procedencia no certificable aceptada como Opta real: {espuria}"
        )



# ────────────────────────────────────────────────────────────────────────────────────────────────
# INVARIANZA 2 — TELEMETRÍA DIMENSIONAL Y UMBRALES DEL SEMÁFORO H2H
# ────────────────────────────────────────────────────────────────────────────────────────────────
def test_telemetria_dimensional_del_catalogo():
    """[INVARIANZA 2 — CONTADORES SERVIDOS POR DIMENSIÓN]:
    El acordeón bicolor sólo puede pintarse con la verdad del servidor: 6 dimensiones, 32
    variables y contadores `total_variables` / `variables_evaluadas` / `tiene_datos` coherentes.
    """
    from src.core.sovereign.factor_attribution import estructurar_catalogo_44_variables

    bloque = estructurar_catalogo_44_variables({"insumos_factivados": dict(INSUMOS_VIVOS)})
    dimensiones = bloque["dimensiones"]
    assert len(dimensiones) == 6, "La partición canónica [LN-QBE-120] exige 6 dimensiones."
    assert sum(d["total_variables"] for d in dimensiones) == 32
    assert sum(d["conteo"] for d in dimensiones) == 32 == bloque["total_variables"]

    for dimension in dimensiones:
        for clave in ("total_variables", "variables_evaluadas", "tiene_datos"):
            assert clave in dimension, f"Telemetría dimensional incompleta: falta '{clave}'."
        assert dimension["total_variables"] == dimension["conteo"]
        assert 0 <= dimension["variables_evaluadas"] <= dimension["total_variables"]
        assert dimension["tiene_datos"] is (dimension["variables_evaluadas"] > 0)

    # Las 8 variables vivas del Axioma 4 caen en 5 dimensiones: el resto queda en fase 6.
    con_datos = {d["dimension"] for d in dimensiones if d["tiene_datos"]}
    assert con_datos == DIMENSIONES_CON_DATOS, f"Dimensiones iluminadas inesperadas: {con_datos}"
    assert sum(d["variables_evaluadas"] for d in dimensiones) == 8

    # Sin paquete de insumos NADA se ilumina (ruta heredada intacta, cero invención).
    vacio = estructurar_catalogo_44_variables({})
    for dimension in vacio["dimensiones"]:
        assert dimension["variables_evaluadas"] == 0
        assert dimension["tiene_datos"] is False
        assert all(v["estado"] == "SIN EVIDENCIA" for v in dimension["variables"])


def test_semaforo_h2h_sobre_la_ventana_publicada():
    """[INVARIANZA 2-bis — LA VENTANA MANDADA POR EL PROVEEDOR ENCIENDE EL SEMÁFORO]:
    🟢 ≥ 5 duelos · 🟡 1–4 · ⚪ 0 (Ley Zero-H2H), leídos del `h2h_conteo` publicado.
    """
    from src.core.sovereign.factor_attribution import construir_atribucion_factorial

    def _h2h(conteo):
        return construir_atribucion_factorial({
            "insumos_factivados": {**INSUMOS_VIVOS, "h2h_conteo": conteo}
        })["semaforos"]["h2h"]

    assert _h2h(5) == "VERDE"
    assert _h2h(4) == "AMARILLO"
    assert _h2h(1) == "AMARILLO"
    assert _h2h(0) == "NEUTRO"


# ────────────────────────────────────────────────────────────────────────────────────────────────
# INVARIANZA 3 — AXIOMA 4 COMPLETO (V12 CON RESPALDO GC/PJ · V10→V12 [LN-QBE-120])
# ────────────────────────────────────────────────────────────────────────────────────────────────
def test_axioma4_v12_respaldo_gc():
    """[INVARIANZA 3 — AXIOMA 4 SIN AGUJEROS]:
    `V12` enciende con `xga_*_rate`; si el generador sólo publicó `gc_*_rate`, la celda transcribe
    el respaldo GC/PJ declarándolo en la nota forense (cero fabricación de xGA).
    """
    from src.core.sovereign.factor_attribution import estructurar_catalogo_44_variables

    solo_gc = {
        clave: valor for clave, valor in INSUMOS_VIVOS.items()
        if not clave.startswith("xga_")
    }
    bloque = estructurar_catalogo_44_variables({"insumos_factivados": solo_gc})
    v12 = _dimensiones(bloque)["𝒯_Def"]["variables"][0]
    assert v12["id"] == "V12"
    assert v12["local"] == "1.10" and v12["visita"] == "1.20", (
        f"V12 debe transcribir el respaldo GC/PJ: {v12['local']} / {v12['visita']}"
    )
    assert v12["estado"] == "EVALUADO"
    assert "GC" in v12["nota"].upper(), "El respaldo debe declararse en la nota (cero maquillaje)."

    # Con xGA publicado el respaldo NO se usa: manda la métrica defensiva canónica.
    bloque_xga = estructurar_catalogo_44_variables({"insumos_factivados": dict(INSUMOS_VIVOS)})
    v12_xga = _dimensiones(bloque_xga)["𝒯_Def"]["variables"][0]
    assert v12_xga["local"] == "1.05" and v12_xga["visita"] == "1.31"



# ────────────────────────────────────────────────────────────────────────────────────────────────
# INVARIANZA 4 — PROVEEDOR H2H SOBRE EL CORPUS CONGELADO
# ────────────────────────────────────────────────────────────────────────────────────────────────
CORPUS_SINTETICO = {
    "esquema": "h2h_corpus_v1",
    "liga": "LIGAMX",
    "fuente": "juez_sintetico",
    "partidos": [
        # 7 duelos consumados + 1 futuro (debe quedar fuera por futuro-ceguera).
        {"fecha": "2023-03-04", "local_slug": "club-america", "visitante_slug": "chivas-guadalajara",
         "goles_local": 4, "goles_visita": 0},
        {"fecha": "2023-09-16", "local_slug": "chivas-guadalajara", "visitante_slug": "club-america",
         "goles_local": 0, "goles_visita": 0},
        {"fecha": "2024-02-10", "local_slug": "club-america", "visitante_slug": "chivas-guadalajara",
         "goles_local": 1, "goles_visita": 3},
        {"fecha": "2024-08-24", "local_slug": "chivas-guadalajara", "visitante_slug": "club-america",
         "goles_local": 2, "goles_visita": 2},
        {"fecha": "2025-01-18", "local_slug": "club-america", "visitante_slug": "chivas-guadalajara",
         "goles_local": 0, "goles_visita": 1},
        {"fecha": "2025-08-15", "local_slug": "chivas-guadalajara", "visitante_slug": "club-america",
         "goles_local": 1, "goles_visita": 1},
        {"fecha": "2026-05-01", "local_slug": "club-america", "visitante_slug": "chivas-guadalajara",
         "goles_local": 0, "goles_visita": 3},
        {"fecha": "2027-01-01", "local_slug": "club-america", "visitante_slug": "chivas-guadalajara",
         "goles_local": 9, "goles_visita": 9},
    ],
}


@pytest.fixture()
def corpus_sintetico(tmp_path):
    ruta = tmp_path / "corpus_h2h_juez.json"
    ruta.write_text(json.dumps(CORPUS_SINTETICO, ensure_ascii=False), encoding="utf-8")
    return ruta


def test_proveedor_h2h_corpus_congelado(corpus_sintetico):
    """[INVARIANZA 4 — EXTRACCIÓN DETERMINISTA, FUTURO-CIEGA Y EN PERSPECTIVA]:
    ≤ 5 duelos, ordenados del más reciente al más antiguo, sin fabricar enfrentamientos y con los
    goles leídos en la perspectiva del club local evaluado.
    """
    from src.core.sovereign.h2h_provider import (
        FUENTE_CORPUS,
        LIMITE_DUELOS_H2H,
        obtener_h2h_unificado,
    )

    duelos = obtener_h2h_unificado(
        None, "chivas-guadalajara", "club-america", datetime(2026, 6, 1), ruta_corpus=corpus_sintetico
    )
    assert len(duelos) == LIMITE_DUELOS_H2H == 5, f"Selección canónica de 5 duelos: {len(duelos)}"

    antiguedades = [d["dias_antiguedad"] for d in duelos]
    assert antiguedades == sorted(antiguedades), "El orden debe ser del más reciente al más antiguo."
    assert all(isinstance(valor, int) and valor >= 0 for valor in antiguedades)
    assert 9 * 9 not in [(d["goles_local"], d["goles_visita"]) for d in duelos], (
        "Un duelo posterior al kickoff se filtró: fuga temporal."
    )
    assert antiguedades[0] == 31, f"El duelo más reciente está a 31 días: {antiguedades[0]}"

    # Perspectiva: el 2026-05-01 lo ganó el América 0-3 siendo LOCAL ⇒ para Chivas es 3-0.
    reciente = duelos[0]
    assert (reciente["goles_local"], reciente["goles_visita"]) == (3, 0), (
        f"La perspectiva del local evaluado no se respetó: {reciente}"
    )
    assert reciente["fecha"] == "2026-05-01"
    assert reciente["fuente"] == FUENTE_CORPUS

    # La perspectiva contraria invierte el marcador: América local en ese mismo duelo ⇒ 0-3.
    espejo = obtener_h2h_unificado(
        None, "club-america", "chivas-guadalajara", datetime(2026, 6, 1), ruta_corpus=corpus_sintetico
    )
    assert (espejo[0]["goles_local"], espejo[0]["goles_visita"]) == (0, 3)

    # Cero fabricación: una pareja sin historia devuelve lista vacía (Ley Zero-H2H).
    assert obtener_h2h_unificado(
        None, "atlas-fc", "necaxa", datetime(2026, 6, 1), ruta_corpus=corpus_sintetico
    ) == []

    # Corpus ausente: degradación limpia (lista vacía), jamás excepción.
    assert obtener_h2h_unificado(
        None, "chivas-guadalajara", "club-america", datetime(2026, 6, 1),
        ruta_corpus=corpus_sintetico.parent / "inexistente.json",
    ) == []


def test_proveedor_h2h_es_de_solo_lectura():
    """[INVARIANZA 4-bis — PUREZA DE ACCESO]: el proveedor no abre red en tiempo de ejecución ni
    reimplementa la ponderación sellada `[LN-QBE-020-C]`.
    """
    assert RUTA_PROVEEDOR.exists(), "El proveedor H2H [ARCH-1.4.44] no está materializado."
    fuente = RUTA_PROVEEDOR.read_text(encoding="utf-8")
    for prohibido in ("requests", "httpx", "urllib", "playwright", "aiohttp", "socket"):
        assert prohibido not in fuente, (
            f"[DIRGEN-STRICT] El proveedor no puede portar acceso de red: '{prohibido}'."
        )
    assert "calcular_matriz_h2h_empirica" in fuente, (
        "La ponderación debe delegarse al kernel sellado [LN-QBE-020-C]."
    )

    import src.core.sovereign.h2h_provider as proveedor

    assert callable(getattr(proveedor, "obtener_h2h_unificado", None))
    assert proveedor.ESQUEMA_CORPUS_H2H == "h2h_corpus_v1"


def test_proveedor_h2h_puente_boveda_3nf(tmp_path):
    """[INVARIANZA 4-ter — PUENTE slug ↔ NOMBRE DE EXHIBICIÓN]:
    La bóveda publica nombres de exhibición y el contrato exige slugs canónicos; el proveedor debe
    canonicalizar ambos flujos. Sin el puente, la comparación es vacía por construcción.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from src.core.sovereign.h2h_provider import FUENTE_BOVEDA, obtener_h2h_unificado
    from src.storage.models import Base, FixtureSnapshot, League, Team

    motor = create_engine("sqlite://")
    Base.metadata.create_all(bind=motor)
    sesion = sessionmaker(bind=motor)()
    try:
        sesion.add(League(id=1, name="Liga MX", country="México", flag="mx", fotmob_id=262))
        sesion.flush()  # la liga precede al club y al fixture (sin relaciones ORM declaradas)
        sesion.add(Team(league_id=1, fotmob_team_id=9101, name="Club América", short_name="América",
                        canonical_slug="club-america", crest_url="/static/img/crests/club-america.png"))
        sesion.add(Team(league_id=1, fotmob_team_id=9102, name="Chivas Guadalajara", short_name="Chivas",
                        canonical_slug="chivas-guadalajara", crest_url="/static/img/crests/chivas.png"))
        sesion.flush()
        sesion.add(FixtureSnapshot(league_id=1, matchday=3, matches_json=[{
            "id_partido": "LIGAMX-J3-01",
            "local": "Club América",
            "visitante": "Chivas Guadalajara",
            "home_team_slug": "club-america",
            "away_team_slug": "chivas-guadalajara",
            "estado": "FINALIZADO",
            "marcador_actual": "2 - 0",
            "fecha_dt": "2026-02-10T19:00:00",
        }]))
        sesion.commit()

        duelos = obtener_h2h_unificado(
            sesion, "chivas-guadalajara", "club-america", datetime(2026, 4, 1),
            ruta_corpus=tmp_path / "sin_corpus.json",
        )
    finally:
        sesion.close()
        motor.dispose()

    assert len(duelos) == 1, f"El puente de identidad no resolvió el duelo de la bóveda: {duelos}"
    assert duelos[0]["fuente"] == FUENTE_BOVEDA
    assert (duelos[0]["goles_local"], duelos[0]["goles_visita"]) == (0, 2)
    assert duelos[0]["dias_antiguedad"] == 49, (
        f"Antigüedad fáctica 2026-02-10 → 2026-04-01: {duelos[0]['dias_antiguedad']}"
    )
    assert duelos[0]["fecha"] == "2026-02-10"



# ────────────────────────────────────────────────────────────────────────────────────────────────
# INVARIANZA 5 — CONTRATO DE PRESENTACIÓN (DES-QBE-066)
# ────────────────────────────────────────────────────────────────────────────────────────────────
def test_ui_acordeon_bicolor():
    """[INVARIANZA 5 — BICOLOR SIN MAQUILLAJE EN EL CLIENTE]:
    La dimensión con evidencia y la dimensión en fase 6 se distinguen por clase y badge; el rótulo
    sale del servidor y se pinta con `createElement` + `textContent` (cero `innerHTML` con red).
    """
    app_js = RUTA_APP_JS.read_text(encoding="utf-8")
    css = RUTA_CSS.read_text(encoding="utf-8")

    for marcador in ("dim-con-datos", "dim-fase6", "badge-dim-evaluada", "badge-dim-fase6"):
        assert marcador in app_js, f"El acordeón bicolor no declara '{marcador}' en app.js."
        assert f".{marcador}" in css, f"Falta la regla CSS '.{marcador}'."

    assert "variables_evaluadas" in app_js, "El cliente debe transcribir el contador servido."
    assert "tiene_datos" in app_js

    # Geometría y colorimetría legisladas.
    assert "#10B981" in css and "#475569" in css

    # El badge se construye sin `innerHTML` (datos de red jamás interpolados en crudo).
    constructor = re.search(
        r"function _badgeDimension44[\s\S]{0,1200}?\n}", app_js
    )
    assert constructor is not None, "Falta el constructor `_badgeDimension44` del badge bicolor."
    cuerpo = constructor.group(0)
    assert "innerHTML" not in cuerpo, "El badge bicolor no puede hidratarse por `innerHTML`."
    assert "createElement" in cuerpo and "textContent" in cuerpo

    # El acordeón conserva la geometría previa de [DES-QBE-064].
    assert "vars44-dimension" in app_js
    assert "vars44-tabla" in app_js


def test_corpus_congelado_materializado():
    """[INVARIANZA 6 — ARTEFACTO SELLADO DISPONIBLE]: el corpus congelado existe, declara su
    esquema y cubre la memoria longitudinal de la Liga MX sin habilitar red en ejecución.
    """
    if not RUTA_CORPUS_REAL.exists():
        pytest.skip("Corpus congelado ausente en esta estación (artefacto data/).")

    corpus = json.loads(RUTA_CORPUS_REAL.read_text(encoding="utf-8"))
    assert corpus["esquema"] == "h2h_corpus_v1"
    assert corpus["ventana_tau_deep_dias"] == 540.0
    assert len(corpus["partidos"]) > 0, "El corpus congelado no puede estar vacío."

    slugs_validos = {
        "atlas-fc", "atletico-san-luis", "chivas-guadalajara", "club-america", "club-leon",
        "club-pachuca", "club-puebla", "club-tijuana", "cruz-azul", "deportivo-toluca",
        "fc-juarez", "necaxa", "pumas-unam", "queretaro-fc", "rayados-de-monterrey",
        "santos-laguna", "tigres-uanl", "atlante",
    }
    for partido in corpus["partidos"]:
        assert partido["local_slug"] in slugs_validos, f"Slug no canónico: {partido['local_slug']}"
        assert partido["visitante_slug"] in slugs_validos
        assert isinstance(partido["goles_local"], int) and isinstance(partido["goles_visita"], int)

    from src.core.sovereign.h2h_provider import obtener_h2h_unificado

    clasico = obtener_h2h_unificado(
        None, "club-america", "chivas-guadalajara", datetime(2026, 9, 1), ruta_corpus=RUTA_CORPUS_REAL
    )
    assert len(clasico) > 0, "El corpus no cubre el Clásico Nacional: la memoria sigue vacía."
    assert obtener_h2h_unificado(
        None, "club-america", "atlante", datetime(2026, 9, 1), ruta_corpus=RUTA_CORPUS_REAL
    ) == [], "Un club sin historia en el corpus no puede heredar duelos fabricados."
