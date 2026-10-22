# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — CONSUMO MACRO-TORNEAL DE EXHIBICIÓN (FASE B)
Juez Inmutable: [LN-QBE-121] · Plano: `docs/DIRGEN_VAULT.md` [VAULT-CORE-005]
Base de Gobierno: Kybern Framework v13.5

Régimen declarado (Dual-Track honesto):
* `[DIRGEN-STRICT]` — `src/core/sovereign_pipeline.py` (anidamiento `macro_stats`) y
  `src/core/sovereign/factor_attribution.py` (aduana de exhibición). SÓLO se certifica que λ,
  Dixon-Coles, André y la fusión `[LN-QBE-104]` permanecen BIT-IDÉNTICOS: ninguna fórmula sellada
  se re-calcula en este juez.
* `[DBBD-FUNGIBLE]` — resolución de identidad del artefacto torneal en el orquestador de ingesta
  (`homologar_temporada_optah2h.py`, C5) y su transcripción al catálogo de 32 variables.

Aislamiento hermético: cero red, cero base de datos, cero navegador. El artefacto torneal se
materializa en `tmp_path` con la aduana REAL del homologador (`32V-2026` + `Liga MX`).
"""

import json
from pathlib import Path

import pytest

from src.core.sovereign.factor_attribution import (
    CELDAS_INSUMIDAS,
    _CLAVES_COTEJO_MACRO,
    _CLAVES_MACRO_STATS,
    empaquetar_insumos_factivados,
    estructurar_catalogo_44_variables,
)
from src.core.sovereign_pipeline import (
    _bloque_macro_stats,
    _empaquetar_insumos_factivados,
    generar_distribucion_soberana,
)
from scripts.ingesta.homologar_temporada_optah2h import (
    _bloque_macro,
    _cargar_cache_macro,
)

RAIZ = Path(__file__).resolve().parents[2]
ARTEFACTO_REAL = RAIZ / "data" / "cache_macro_stats_liga_mx_2026.json"

# Club torneal COMPLETO (todas las claves de las 19 recetas) y club con HUECO declarado.
_CLUB_COMPLETO = {
    "possession_pct": 53.6,
    "xg_per_match": 1.62,
    "sot_per_match": 4.9,
    "xga_per_match": 1.24,
    "sota_per_match": 3.8,
    "touches_opp_box_per_match": 22.4,
    "accurate_passes_per_match": 287.4,
    "accurate_long_balls_per_match": 19.5,
    "fouls_per_match": 14.0,
    "big_chances_created_per_match": 2.2308,
    "big_chances_missed_per_match": 1.5385,
    "xgot_squad": 8.7,
    "xa_squad": 12.4,
    "defensive_actions_per_match": 58.6,
    "interceptions_per_match": 9.4,
    "goals_prevented_squad": 1.1,
    "save_percentage": 69.8,
    "sweeper_actions": 0.8,
    "clean_sheets": 2.0,
    "set_piece_goals_per_match": 0.31,
    "set_piece_goals_conceded_per_match": 0.15,
    "corners_per_match": 5.3846,
    "penalties_won_total": 3.0,
    "penalties_conceded_total": 4.0,
    "yellow_cards_per_match": 1.69,
    "red_cards_per_match": 0.08,
}
_CLUB_CON_HUECO = {k: v for k, v in _CLUB_COMPLETO.items() if k != "clean_sheets"}


def _artefacto(equipos, version="32V-2026", liga="Liga MX"):
    """Artefacto torneal mínimo con la forma REAL de `[ARCH-1.4.59]`."""
    return {
        "catalogo_version": version,
        "liga": {"nombre": liga, "data_provider": "opta"},
        "equipos": equipos,
        "huecos": [],
        "fuente": "artefacto de prueba hermético",
    }


def _registro(match_id="M_MACRO_01"):
    """Registro fáctico suficiente para el generador sellado (cero red, cero BD)."""
    return {
        "match_id": match_id,
        "competition_id": "MEX_LIGAMX",
        "home_team_slug": "atlante",
        "away_team_slug": "atlas-fc",
        "home_team_stats": {
            "pj": 8, "gf": 14, "gc": 6,
            "xg": 12.8, "xga": 8.0, "sot": 40, "sota": 32, "possession": 53.5,
        },
        "away_team_stats": {
            "pj": 8, "gf": 9, "gc": 12,
            "xg": 8.8, "xga": 12.0, "sot": 24, "sota": 32, "possession": 46.5,
        },
        "home_split_stats": {"pj": 4, "gf": 8, "gc": 3},
        "away_split_stats": {"pj": 4, "gf": 4, "gc": 7},
        "h2h_matches": [],
    }


def _celdas(catalogo):
    return {v["id"]: v for d in catalogo["dimensiones"] for v in d["variables"]}


# ── INVARIANTE 1 — la macro ENCIENDE celdas apagadas; jamás pisa las insumidas ────────────────
def test_macro_enciende_celdas_apagadas_sin_tocar_las_insumidas():
    """[INVARIANZA 1] `[LN-QBE-121]`: 19 celdas de exhibición se encienden y V01/V06/V07/V12/V13 no."""
    base = estructurar_catalogo_44_variables({"insumos_factivados": empaquetar_insumos_factivados()})
    assert base["total_evaluadas"] == 0, "Sin corte ni macro, el catálogo debe estar apagado."

    bloque = _bloque_macro(_artefacto({"atlante": _CLUB_COMPLETO, "atlas-fc": _CLUB_COMPLETO}),
                           "atlante", "atlas-fc")
    assert bloque["procedencia"] == "MACRO_TORNEAL"
    assert bloque["catalogo_version"] == "32V-2026"

    catalogo = estructurar_catalogo_44_variables(
        {"insumos_factivados": empaquetar_insumos_factivados(macro_stats=bloque)}
    )
    celdas = _celdas(catalogo)
    encendidas = {i for i, v in celdas.items() if v["estado"] == "EVALUADO"}

    assert encendidas == set(_CLAVES_MACRO_STATS), "La macro debe encender EXACTAMENTE sus recetas."
    assert catalogo["total_evaluadas"] == len(_CLAVES_MACRO_STATS) == 19
    # Jurisdicción de EXHIBICIÓN: ninguna celda que alimente λ se toca por esta vía.
    assert encendidas.isdisjoint(CELDAS_INSUMIDAS)
    for insumida in CELDAS_INSUMIDAS:
        assert celdas[insumida]["estado"] == "SIN EVIDENCIA"
        assert celdas[insumida]["local"] is None
    # V16 no tiene leaderboard en la fuente: permanece oscura (cero imputación).
    assert celdas["V16"]["estado"] == "SIN EVIDENCIA"
    # Transcripción literal (sin recálculo): se compara contra los números del artefacto.
    assert celdas["V18"]["local"] == "69.8%"
    assert celdas["V20"]["local"] == "2"
    assert celdas["V24"]["local"] == "3 a favor · 4 en contra"
    assert celdas["V25"]["local"] == "1.69 amarillas/PJ · 0.08 rojas/PJ"


# ── INVARIANTE 2 — λ, Dixon-Coles, André y la fusión son bit-idénticos ───────────────────────
def test_lambda_y_traza_son_bit_identicas_con_y_sin_macro():
    """[INVARIANZA 2] `[LN-QBE-121]`: el bloque torneal NO entra en la matemática sellada."""
    bloque = _bloque_macro(_artefacto({"atlante": _CLUB_COMPLETO, "atlas-fc": _CLUB_COMPLETO}),
                           "atlante", "atlas-fc")
    registro = _registro()

    sin_macro = generar_distribucion_soberana("M_MACRO_01", dict(registro))
    con_macro = generar_distribucion_soberana(
        "M_MACRO_01", dict(registro), cache_macro_stats=bloque
    )

    assert (con_macro.lambda_home, con_macro.lambda_away) == (sin_macro.lambda_home, sin_macro.lambda_away)
    assert (con_macro.p_local, con_macro.p_empate, con_macro.p_visitante) == (
        sin_macro.p_local, sin_macro.p_empate, sin_macro.p_visitante
    )
    assert (con_macro.phi_lead2_home, con_macro.phi_lead2_away) == (
        sin_macro.phi_lead2_home, sin_macro.phi_lead2_away
    )

    traza_con = con_macro.audit_trace.model_dump()
    traza_sin = sin_macro.audit_trace.model_dump()
    # El bloque se transcribe TAL CUAL llega (incluido el cotejo de las celdas insumidas).
    assert traza_con["insumos_factivados"]["macro_stats"] == bloque
    assert set(traza_con["insumos_factivados"]["macro_stats"]["cotejo"]) == set(_CLAVES_COTEJO_MACRO)
    assert traza_sin["insumos_factivados"].get("macro_stats") is None

    # El resto de la traza (intensidades, matriz, factores, simplex) es idéntico byte a byte.
    recortada = json.loads(json.dumps(traza_con, sort_keys=True))
    recortada["insumos_factivados"].pop("macro_stats")
    assert json.dumps(recortada, sort_keys=True) == json.dumps(
        json.loads(json.dumps(traza_sin, sort_keys=True)), sort_keys=True
    )


# ── INVARIANTE 3 — sin artefacto, el paquete y el catálogo son BYTE-IDÉNTICOS ─────────────────
def test_sin_artefacto_el_paquete_es_byte_identico():
    """[INVARIANZA 3] `[LN-QBE-121]`: `cache_macro_stats=None` no altera un solo byte."""
    registro = _registro()
    referencia = _empaquetar_insumos_factivados(registro, 0.0, 0.0, 1.0, 1.0, True)
    explicito = _empaquetar_insumos_factivados(
        registro, 0.0, 0.0, 1.0, 1.0, True, cache_macro_stats=None
    )
    assert json.dumps(referencia, sort_keys=True) == json.dumps(explicito, sort_keys=True)
    assert "macro_stats" not in referencia

    # El catálogo de 32 variables tampoco cambia (ruta heredada intacta).
    catalogo_ref = estructurar_catalogo_44_variables({"insumos_factivados": referencia})
    catalogo_exp = estructurar_catalogo_44_variables({"insumos_factivados": explicito})
    assert json.dumps(catalogo_ref, sort_keys=True) == json.dumps(catalogo_exp, sort_keys=True)

    # Y un artefacto inservible se degrada a `{}` sin fabricar bloque alguno.
    assert _bloque_macro_stats(None) == {}
    assert _bloque_macro_stats({}) == {}
    assert _bloque_macro_stats({"local": None, "visita": None}) == {}


# ── INVARIANTE 4 — ausencia de club o de clave ⇒ celda SIN EVIDENCIA (cero imputación) ────────
def test_club_ausente_o_clave_ausente_deja_la_celda_sin_evidencia(tmp_path):
    """[INVARIANZA 4] `[LN-QBE-121]`: la ausencia apaga la celda; jamás se proyecta ni se promedia."""
    # Club ausente de la fuente ⇒ ninguna celda encendida.
    artefacto = _artefacto({"atlante": _CLUB_COMPLETO})
    assert _bloque_macro(artefacto, "club-fantasma", "otro-fantasma") == {}
    catalogo = estructurar_catalogo_44_variables(
        {"insumos_factivados": empaquetar_insumos_factivados(macro_stats={})}
    )
    assert catalogo["total_evaluadas"] == 0

    # Hueco declarado (`clean_sheets`): V20 sólo publica el lado que la fuente SÍ trae.
    bloque = _bloque_macro(
        _artefacto({"atlante": _CLUB_CON_HUECO, "atlas-fc": _CLUB_COMPLETO}),
        "atlante",
        "atlas-fc",
    )
    celdas = _celdas(
        estructurar_catalogo_44_variables(
            {"insumos_factivados": empaquetar_insumos_factivados(macro_stats=bloque)}
        )
    )
    assert celdas["V20"]["local"] is None, "Un hueco del artefacto no se rellena jamás."
    assert celdas["V20"]["visita"] == "2"
    assert celdas["V20"]["estado"] == "EVALUADO"

    # Sin NINGÚN lado publicado, la celda permanece `SIN EVIDENCIA`.
    solo_huecos = _bloque_macro(
        _artefacto({"atlante": _CLUB_CON_HUECO, "atlas-fc": _CLUB_CON_HUECO}),
        "atlante",
        "atlas-fc",
    )
    celdas_hueco = _celdas(
        estructurar_catalogo_44_variables(
            {"insumos_factivados": empaquetar_insumos_factivados(macro_stats=solo_huecos)}
        )
    )
    assert celdas_hueco["V20"]["estado"] == "SIN EVIDENCIA"
    assert celdas_hueco["V20"]["local"] is None and celdas_hueco["V20"]["visita"] is None
    assert celdas_hueco["V02"]["estado"] == "EVALUADO"

    # Aduana del orquestador: catálogo o liga ajenos desactivan la exhibición por completo.
    ruta_ok = tmp_path / "macro_ok.json"
    ruta_ok.write_text(json.dumps(_artefacto({"atlante": _CLUB_COMPLETO})), encoding="utf-8")
    assert _cargar_cache_macro(str(ruta_ok))["catalogo_version"] == "32V-2026"

    ruta_version = tmp_path / "macro_44v.json"
    ruta_version.write_text(
        json.dumps(_artefacto({"atlante": _CLUB_COMPLETO}, version="44V-2024")), encoding="utf-8"
    )
    assert _cargar_cache_macro(str(ruta_version)) == {}

    ruta_liga = tmp_path / "macro_otra_liga.json"
    ruta_liga.write_text(
        json.dumps(_artefacto({"atlante": _CLUB_COMPLETO}, liga="Premier League")), encoding="utf-8"
    )
    assert _cargar_cache_macro(str(ruta_liga)) == {}
    assert _cargar_cache_macro(str(tmp_path / "inexistente.json")) == {}


# ── INVARIANTE 5 — el artefacto REAL de la liga publica las 19 celdas y su cotejo ────────────
@pytest.mark.skipif(not ARTEFACTO_REAL.is_file(), reason="Artefacto torneal no presente en el lote")
def test_artefacto_torneal_real_alimenta_el_catalogo_sin_tocar_lambda():
    """[INVARIANZA 5] `[LN-QBE-121]`: consumo del artefacto real `cache_macro_stats_liga_mx_2026`."""
    artefacto = _cargar_cache_macro(str(ARTEFACTO_REAL))
    assert artefacto.get("catalogo_version") == "32V-2026"
    assert (artefacto.get("liga") or {}).get("nombre") == "Liga MX"
    equipos = artefacto.get("equipos") or {}
    assert len(equipos) == 18, "La fuente cubre los 18 clubes del torneo."

    local, visita = "atlante", "atlas-fc"
    bloque = _bloque_macro(artefacto, local, visita)
    assert bloque and bloque["procedencia"] == "MACRO_TORNEAL"
    assert set(bloque["cotejo"]) <= set(_CLAVES_COTEJO_MACRO)

    catalogo = estructurar_catalogo_44_variables(
        {"insumos_factivados": empaquetar_insumos_factivados(macro_stats=bloque)}
    )
    celdas = _celdas(catalogo)
    assert catalogo["total_evaluadas"] >= 19
    assert celdas["V18"]["local"].endswith("%")
    assert celdas["V01"]["estado"] == "SIN EVIDENCIA", "La macro no enciende celdas del motor."

    registro = _registro()
    sin_macro = generar_distribucion_soberana("M_MACRO_REAL", dict(registro))
    con_macro = generar_distribucion_soberana(
        "M_MACRO_REAL", dict(registro), cache_macro_stats=bloque
    )
    assert (con_macro.lambda_home, con_macro.lambda_away) == (
        sin_macro.lambda_home, sin_macro.lambda_away
    )
