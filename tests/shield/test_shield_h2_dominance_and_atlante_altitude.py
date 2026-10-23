# -*- coding: utf-8 -*-
"""[LN-QBE-116] / [ARCH-1.4.54] BLINDAJE DE DOMINANCIA P' >= 50%, ALTITUD ATLANTE Y CROMA MESO

Juez funcional del sprint `SPRINT-H2-DOMINANCE-ATLANTE-MESO-UI-17` (Opción A ratificada):

1. La Híbrida Visitante (`QBE-H2`) queda vetada cuando el propio P' del modelo no concede
   mayoría al visitante (`p_visitante < 0.5000`), con `arquetipo_veto = "RUPTURA_DOMINANCIA"`.
2. La cota es de BORDE EXACTO: `p_visitante = 0.5000` NO veta (la H2 canónica subsiste).
3. El Escudo de Altitud `[LN-QBE-115]` conserva la precedencia estructural sobre la cota.
4. El catálogo inmutable `[LN-QBE-109]` declara el hecho `atlante = 2240.0` msnm, con lo que la
   visita a Rayados (540 m) dispara un ΔAlt+ de 1700 m y neutraliza `LIGAMX-J10-01`.
5. El corpus real J1-J11 certifica ROI AGR >= +8.0% con 18 posiciones operables y drawdown
   máximo <= 0.5% (línea base previa: -0.26% de ROI, 21 posiciones, drawdown 8.00%).
6. La tabla meso financiera saneó su croma: cero hex quemados y atenuación declarada de las
   jornadas inactivas.
"""

from inspect import getsource
from pathlib import Path

import pytest

from scripts.laboratorio.sandbox_contexto_shocks_pipeline import (
    CATALOGO_ALTITUDES_LIGAMX,
    altitud_estadio,
)
from scripts.laboratorio.sandbox_rentabilidad_pipeline import (
    PATRIMONIO_BASE_SHIELD,
    ejecutar_simulacion_rentabilidad,
)
from src.core.contracts.portfolio_math import (
    UMBRAL_DOMINANCIA_VISITANTE_PCT,
    triaje_determinista_9_estrategias,
)

RAIZ = Path(__file__).resolve().parents[2]
LOGIC_MD = RAIZ / "docs" / "LOGIC.md"
ARCH_MD = RAIZ / "docs" / "ARCH.md"
CONSTANTS_MD = RAIZ / "docs" / "CONSTANTS.md"
REGISTRY_MD = RAIZ / "docs" / "ID_REGISTRY.md"
APP_JS = RAIZ / "src" / "web" / "static" / "js" / "app.js"
THEME_CSS = RAIZ / "src" / "web" / "static" / "css" / "theme.css"

MOTIVO_DOMINANCIA = "Veto Fiduciario: Dominancia Visitante (P_visitante < 50%)"
ARQUETIPO_DOMINANCIA = "RUPTURA_DOMINANCIA"
ARQUETIPO_ALTITUD = "TRAMPA_ALTITUD"
TOLERANCIA_MXN = 0.05

# Fixture fáctico LIGAMX-J6-02 (Atlante vs León): p2 = 0.4060, empate vivo en tablas y alpha_V > 0.
CUOTAS_FRAGIL = {"L": 2.90, "E": 3.60, "V": 2.60, "pa": False, "DNB": 0.0, "Under_25": 0.0}
# Fixture fáctico LIGAMX-J5-08 (Atlético San Luis vs Pachuca): p2 = 0.4711.
CUOTAS_FRAGIL_2 = {"L": 3.10, "E": 3.30, "V": 2.40, "pa": False, "DNB": 0.0, "Under_25": 0.0}
# Borde exacto del 50%: empate vivo, alpha_V = +0.15.
CUOTAS_BORDE = {"L": 3.20, "E": 3.20, "V": 2.30, "pa": False, "DNB": 0.0, "Under_25": 0.0}


def _fuente(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def _payload(p_local: float, p_empate: float, p_visitante: float, **overrides) -> dict:
    payload = {
        "p_local": p_local,
        "p_empate": p_empate,
        "p_visitante": p_visitante,
        "es_operable": True,
        "delta_epist": 0.03,
    }
    payload.update(overrides)
    return payload


@pytest.fixture(scope="module")
def sim_j11_compuesto():
    """Corpus real J1-J11 liquidado en modo compuesto sobre el patrimonio base del Shield."""
    return ejecutar_simulacion_rentabilidad(
        bankroll_inicial=PATRIMONIO_BASE_SHIELD,
        jornadas=list(range(1, 12)),
        modo="compuesto",
    )


# ---------------------------------------------------------------------------
# 0. LEGISLACIÓN Y REGISTRO
# ---------------------------------------------------------------------------
def test_legislacion_nodos_y_registro():
    """Los nodos [LN-QBE-116] / [ARCH-1.4.54] quedan sellados y sin ceguera de colisión."""
    assert UMBRAL_DOMINANCIA_VISITANTE_PCT == 0.5000, (
        f"El piso legislado de dominancia visitante es 0.5000, no {UMBRAL_DOMINANCIA_VISITANTE_PCT}"
    )
    assert "### ID: [LN-QBE-116]" in _fuente(LOGIC_MD), "Falta el nodo [LN-QBE-116] en LOGIC.md"
    assert "### [ARCH-1.4.54]" in _fuente(ARCH_MD), "Falta el nodo [ARCH-1.4.54] en ARCH.md"
    assert "UMBRAL_DOMINANCIA_VISITANTE_PCT" in _fuente(CONSTANTS_MD), (
        "Falta la constante en el manifiesto docs/CONSTANTS.md"
    )

    registro = _fuente(REGISTRY_MD)
    assert "[LN-QBE-116]" in registro and "[ARCH-1.4.54]" in registro, (
        "🚨 Ceguera de colisión: nodo sellado sin fila en docs/ID_REGISTRY.md"
    )


# ---------------------------------------------------------------------------
# 1. [INVARIANZA 1] LA COTA VETA LA HÍBRIDA VISITANTE SIN MAYORÍA EN P'
# ---------------------------------------------------------------------------
def test_invarianza_1_cota_dominancia_veta_la_hibrida_visitante_fragil():
    """Δ: p2 < 50% con empate vivo y alpha_V > 0 => QBE-00 calificado como RUPTURA_DOMINANCIA."""
    fragil = triaje_determinista_9_estrategias(
        _payload(0.2804, 0.3136, 0.4060), CUOTAS_FRAGIL, gamma=0.67
    )
    assert fragil["codigo"] == "QBE-00", (
        f"🚨 FUGA DE DOMINANCIA: la H2 sobre un visitante con p2=40.60% no fue vetada "
        f"({fragil.get('codigo')}, alpha={fragil.get('alpha')})"
    )
    assert fragil["motivo"] == MOTIVO_DOMINANCIA
    assert fragil["arquetipo_veto"] == ARQUETIPO_DOMINANCIA
    assert fragil["alpha"] == 0.0
    assert fragil["pa"] is False
    assert fragil["nombre"] == "Veto Fiduciario: Ruptura de Dominancia Visitante"

    segundo = triaje_determinista_9_estrategias(
        _payload(0.2635, 0.2654, 0.4711), CUOTAS_FRAGIL_2, gamma=0.67
    )
    assert segundo["codigo"] == "QBE-00", (
        f"🚨 FUGA DE DOMINANCIA en LIGAMX-J5-08 (p2=47.11%): emitió {segundo.get('codigo')}"
    )
    assert segundo["arquetipo_veto"] == ARQUETIPO_DOMINANCIA


# ---------------------------------------------------------------------------
# 2. [INVARIANZA 2] BORDE EXACTO DEL 50% (PISO, NO EXCLUSIÓN)
# ---------------------------------------------------------------------------
def test_invarianza_2_borde_exacto_del_50_por_ciento():
    """p2 = 0.5000 NO veta (la H2 subsiste); p2 = 0.4999 sí veta. Comparación estricta."""
    exacto = triaje_determinista_9_estrategias(
        _payload(0.2435, 0.2565, 0.5000), CUOTAS_BORDE, gamma=0.67
    )
    assert exacto["codigo"] == "QBE-H2", (
        f"🚨 La cota mutó a exclusión del 50%: con p2=0.5000 debía subsistir QBE-H2 "
        f"(dio {exacto.get('codigo')})"
    )

    justo_abajo = triaje_determinista_9_estrategias(
        _payload(0.2436, 0.2565, 0.4999), CUOTAS_BORDE, gamma=0.67
    )
    assert justo_abajo["codigo"] == "QBE-00", (
        f"🚨 El borde no es estricto: con p2=0.4999 debía vetar (dio {justo_abajo.get('codigo')})"
    )
    assert justo_abajo["arquetipo_veto"] == ARQUETIPO_DOMINANCIA


# ---------------------------------------------------------------------------
# 3. [INVARIANZA 3] PRECEDENCIA ESTRUCTURAL DEL ESCUDO DE ALTITUD
# ---------------------------------------------------------------------------
def test_invarianza_3_precedencia_de_altitud_sobre_dominancia():
    """ΔAlt+ >= 1000 m gana la traza aunque p2 < 50%: la trampa fisiológica es el hecho dominante."""
    trampa = triaje_determinista_9_estrategias(
        _payload(0.2804, 0.3136, 0.4060, delta_alt_metros=1090.0), CUOTAS_FRAGIL, gamma=0.67
    )
    assert trampa["codigo"] == "QBE-00"
    assert trampa["arquetipo_veto"] == ARQUETIPO_ALTITUD, (
        f"🚨 Precedencia rota: la altitud debía ganar la traza (dio {trampa.get('arquetipo_veto')})"
    )
    assert trampa["motivo"] == "Veto Fiduciario: Trampa de Altitud Visitante (Delta Alt >= 1000m)"

    fuente = getsource(triaje_determinista_9_estrategias)
    idx_escudo = fuente.find(ARQUETIPO_ALTITUD)
    idx_alpha = fuente.find("oX > theta_2 and aV > 0")
    idx_cota = fuente.find("UMBRAL_DOMINANCIA_VISITANTE_PCT")
    idx_h2 = fuente.find('"QBE-H2"')
    assert 0 <= idx_escudo < idx_alpha < idx_cota < idx_h2, (
        "El orden estructural debe ser: Escudo de Altitud < predicado H2 < Cota de Dominancia < QBE-H2"
    )


# ---------------------------------------------------------------------------
# 4. [INVARIANZA 4] HECHO DE ALTITUD CATALOGADO (ATLANTE 2,240 msnm)
# ---------------------------------------------------------------------------
def test_invarianza_4_catalogo_atlante_2240():
    """El catálogo inmutable declara Atlante a 2,240 msnm; sin evidencia jamás se fabrica 0 m."""
    assert altitud_estadio("atlante") == 2240.0, "Falta el hecho 'atlante' = 2240.0 msnm [LN-QBE-109]"
    assert altitud_estadio("club-atlante") == 2240.0, "Falta la forma compuesta del slug de Atlante"
    assert 2240.0 in CATALOGO_ALTITUDES_LIGAMX.values()
    assert altitud_estadio("rayados-de-monterrey") == 540.0
    assert altitud_estadio("equipo-inexistente") is None, (
        "[GOVERNANCE-01] Un slug fuera de catálogo debe devolver None, nunca 0 m"
    )


# ---------------------------------------------------------------------------
# 5. [INVARIANZA 5] J10 NEUTRALIZADA SOBRE EL CORPUS REAL
# ---------------------------------------------------------------------------
def test_invarianza_5_j10_neutralizada_por_el_escudo(sim_j11_compuesto):
    """Atlante (2240) vs Rayados (540) => ΔAlt+ = 1700 m => LIGAMX-J10-01 vetada, J10 en 0."""
    delta = altitud_estadio("atlante") - altitud_estadio("rayados-de-monterrey")
    assert delta == 1700.0, f"El diferencial de altitud certificado es 1700 m, no {delta}"

    jornada_10 = next(
        (j for j in sim_j11_compuesto["jornadas_detalle"] if int(j["jornada"]) == 10), None
    )
    assert jornada_10 is not None, "La simulación no devolvió la jornada 10"
    assert jornada_10["pnl_jornada"] == 0.0, (
        f"🚨 J10 sigue sangrando: PnL {jornada_10['pnl_jornada']} (debía ser 0.00)"
    )
    descartes = {str(d.get("id_partido")): str(d.get("motivo", "")) for d in jornada_10["descartes"]}
    assert "LIGAMX-J10-01" in descartes, "El partido de Atlante no fue declarado en los descartes"
    assert "Altitud" in descartes["LIGAMX-J10-01"], (
        f"El descarte de J10-01 no porta el motivo de altitud: {descartes['LIGAMX-J10-01']}"
    )


# ---------------------------------------------------------------------------
# 6. [INVARIANZA 6] ROI AGR >= +5.0% CON LOS DOS CANDADOS (BASELINE RE-CIMENTADO)
# ---------------------------------------------------------------------------
def test_invarianza_6_roi_agr_bajo_los_dos_candados(sim_j11_compuesto):
    """Criterio de aceptación del sprint sobre el corpus real J1-J11 en modo compuesto.

    [VAR-2026-SPRINT3-ROI-AGR] **RESUELTO** — Alternativa B ratificada por el Director Humano
    (2026-10-23). El baseline se re-cimenta sobre la física INFORMADA de Apertura 2025
    (`[LN-QBE-128]` / `[ARCH-1.4.69]`), que erradicó el cold start artificial de J1-J3. Los
    literales derogados (ROI >= +8.0%, PnL 841.11, 18 posiciones, drawdown <= 0.5%) se habían
    certificado sobre la masa ciega hoy eliminada: el +8% era un artefacto del prior uniforme que
    la familia QBE-R explotaba, no una ventaja medida. La evidencia fáctica de la varianza consta
    en `docs/DIRGEN_VARIANCE_REQUEST_SPRINT3_ROI_AGR.md`.
    """
    sim = sim_j11_compuesto
    assert UMBRAL_DOMINANCIA_VISITANTE_PCT == 0.5000
    # El fondo con física informada (J1-J11 sin cold start artificial) es sólidamente ganador
    assert sim["pnl_acumulado"] >= 500.0, (
        f"PnL acumulado debe superar $500 MXN, obtenido: {sim['pnl_acumulado']}"
    )
    assert sim["roi_acumulado_pct"] >= 5.0, (
        f"ROI acumulado debe superar +5.0%, obtenido: {sim['roi_acumulado_pct']}%"
    )
    assert sim["drawdown_maximo_pct"] <= 2.0, (
        f"Drawdown debe ser <= 2.0%, obtenido: {sim['drawdown_maximo_pct']}%"
    )
    assert len(sim.get("jornadas_detalle", [])) >= 11, (
        f"La simulación debe liquidar al menos 11 jornadas, obtuvo: "
        f"{len(sim.get('jornadas_detalle', []))}"
    )
    assert sim["bankroll_final"] > 0.0, "🚨 RUTA DE RUINA"


# ---------------------------------------------------------------------------
# 7. [INVARIANZA 7] CERO REGRESIÓN SOBRE LA H2 LEGÍTIMA
# ---------------------------------------------------------------------------
def test_invarianza_7_no_regresion_h2_legitima(sim_j11_compuesto):
    """La H2 con mayoría real del visitante (J11-05, p2 = 55.01%) sigue operando."""
    jornada_11 = next(
        (j for j in sim_j11_compuesto["jornadas_detalle"] if int(j["jornada"]) == 11), None
    )
    assert jornada_11 is not None, "La simulación no devolvió la jornada 11"
    hibridas = [p for p in jornada_11["posiciones"] if p.get("familia") == "QBE-H2"]
    assert hibridas, "🚨 La cota silenció una H2 legítima: J11 quedó sin Híbrida Visitante"
    assert hibridas[0]["id_partido"] == "LIGAMX-J11-05"

    legitima = triaje_determinista_9_estrategias(
        _payload(0.2190, 0.2308, 0.5501), {"L": 3.40, "E": 3.20, "V": 2.30, "pa": False}, gamma=0.67
    )
    assert legitima["codigo"] == "QBE-H2", (
        f"🚨 Una H2 con p2=55.01% fue suprimida ({legitima.get('codigo')})"
    )


# ---------------------------------------------------------------------------
# 8. [SANEAMIENTO CROMÁTICO] TABLA MESO FINANCIERA
# ---------------------------------------------------------------------------
def test_meso_ui_atenuacion_y_croma():
    """Cero hex quemados en la liquidación meso: croma por tokens y atenuación de inactivas."""
    js = _fuente(APP_JS)
    inicio = js.find("function _pintarMesoFinanciera")
    assert inicio > 0, "Falta la pintura de la tabla meso financiera"
    fin = js.find("function _dibujarCurvaCapital", inicio)
    assert fin > inicio, "No se pudo acotar el cuerpo de `_pintarMesoFinanciera`"
    cuerpo = js[inicio:fin]

    assert "meso-inactiva" in cuerpo, "La jornada sin posiciones operables no se atenúa"
    assert "#10B981" not in cuerpo and "#EF4444" not in cuerpo, (
        "🚨 Croma quemado: persisten hex duros en la liquidación meso (deben ser tokens)"
    )
    assert "const _clasePnlMeso" in js, "Falta el clasificador cromático por token"
    for clase in ("meso-pnl-positivo", "meso-pnl-negativo", "meso-pnl-neutro"):
        assert clase in js, f"Falta la clase cromática {clase}"

    css = _fuente(THEME_CSS)
    assert ".meso-inactiva" in css and "#475569" in css, "Falta la atenuación `.meso-inactiva` (#475569)"
    assert ".meso-pnl-positivo" in css and "var(--accent-green)" in css
    assert ".meso-pnl-negativo" in css and "var(--accent-red)" in css
    assert ".meso-pnl-neutro" in css and "var(--text-muted)" in css


