# -*- coding: utf-8 -*-
"""
THE SHIELD — JUEZ INMUTABLE DEL SANEAMIENTO VOL. II
Sprint: SPRINT-SANEAMIENTO-ESTRATEGIAS-VOL2-15
Gobierno: [LN-QBE-115] / [ARCH-1.4.53]
Régimen: [DIRGEN-STRICT] — Inmutable, Cero Mocks.

Invariantes legisladas:
1. Cota Underdog Ley 3: `QBE-R1`/`QBE-R2` <= 1.5% del capital de la jornada.
2. Escudo de Altitud: ΔAlt+ >= 1000 m sobre `ASIMETRIA_VISITANTE` veta a `QBE-00`
   con precedencia estructural ANTES de exigir alpha_V > 0.
3. Cobertura dinámica δ: `DEF` (V=0) y `BAL` (δ = 0.5·δ*) producen particiones y PnL distintos.
4. Trinidad de Certeza §5.10 + trazabilidad por estrategia (`resumen_estrategias`).
"""

import pytest

from src.core.contracts.portfolio_math import (
    CAP_UNDERDOG_LEY3_PCT,
    FAMILIAS_UNDERDOG_LEY3,
    UMBRAL_VETO_ALTITUD_METROS,
    asignar_capital_monotono_cartera,
    triaje_determinista_9_estrategias,
)
from scripts.laboratorio.sandbox_rentabilidad_pipeline import (
    PATRIMONIO_BASE_SHIELD,
    ejecutar_simulacion_rentabilidad,
)

MOTIVO_VETO_ALTITUD = (
    "Veto Fiduciario: Trampa de Altitud Visitante (Delta Alt >= 1000m)"
)
ARQUETIPO_TRAMPA_ALTITUD = "TRAMPA_ALTITUD"
BANKROLL_JUEZ = 10000.0
TOLERANCIA_MXN = 0.02


def _payload_juarez_tijuana(delta_alt_metros=1090.0, **overrides):
    """Fixture fáctico LIGAMX-J11-03 (FC Juárez 1120 msnm vs Tijuana 30 msnm).

    ΔAlt+ = 1090 m; Δ_epist = 0.1024 (sobrevive la cuarentena de 0.12) y α_V = +0.2143.
    """
    payload = {
        "p_local": 0.2206479,
        "p_empate": 0.2604069,
        "p_visitante": 0.5189452,
        "es_operable": True,
        "delta_epist": 0.1024277,
        "lambda_home": 1.42,
        "lambda_away": 1.08,
    }
    if delta_alt_metros is not None:
        payload["delta_alt_metros"] = delta_alt_metros
    payload.update(overrides)
    return payload


CUOTAS_JUAREZ_TIJUANA = {
    "L": 2.98, "E": 3.40, "V": 2.34, "pa": False, "DNB": 0.0, "Under_25": 0.0,
}


def _posiciones(reporte):
    return [p for j in reporte["jornadas_detalle"] for p in j["posiciones"]]


def test_invarianza_1_cota_underdog_ley3_acota_la_familia_r():
    """[INVARIANZA 1 - HARD CAP LEY 3]: el techo del 1.5% muerde y sólo muerde a R1/R2."""
    assert CAP_UNDERDOG_LEY3_PCT == 0.0150, "La cota legislada es 1.5%"
    assert tuple(FAMILIAS_UNDERDOG_LEY3) == ("QBE-R1", "QBE-R2"), (
        "La cota Underdog cubre EXACTAMENTE la Familia R"
    )

    # (a) Prueba de mordida: sin la cota la orden R2 recibiría el hard-cap del 8% ($800.00).
    cartera = [
        {"id_partido": "H1-ALTA", "familia": "QBE-H1", "prob_exito_efectiva": 0.95},
        {"id_partido": "R2-CARNICERO", "familia": "QBE-R2", "prob_exito_efectiva": 0.42},
        {"id_partido": "R1-CARNICERO", "familia": "QBE-R1", "prob_exito_efectiva": 0.30},
    ]
    tope_ley3 = round(BANKROLL_JUEZ * CAP_UNDERDOG_LEY3_PCT, 2)
    asignados = asignar_capital_monotono_cartera(cartera, BANKROLL_JUEZ)

    for orden in asignados:
        if orden["familia"] in FAMILIAS_UNDERDOG_LEY3:
            assert orden["inversion_total"] <= tope_ley3 + 1e-9, (
                f"Cota Underdog violada en {orden['id_partido']}: "
                f"{orden['inversion_total']} > {tope_ley3}"
            )

    hibrida = next(o for o in asignados if o["familia"] == "QBE-H1")
    assert hibrida["inversion_total"] == 800.0, (
        "La cota Underdog NO debe tocar a las Híbridas (hard-cap del 8%)"
    )
    assert [o for o in asignados if o["familia"] == "QBE-R2"][0]["inversion_total"] <= tope_ley3

    # (b) Cero regresión sobre órdenes sin familia declarada (contrato heredado).
    heredado = asignar_capital_monotono_cartera(
        [{"id": "LEGACY", "prob_exito_efectiva": 0.90}], BANKROLL_JUEZ
    )
    assert heredado[0]["inversion_total"] == 800.0

    # (c) Cable real: sobre el corpus 1-11 el tope se aplica jornada a jornada.
    sim = ejecutar_simulacion_rentabilidad(
        bankroll_inicial=PATRIMONIO_BASE_SHIELD, jornadas=list(range(1, 12)), modo="compuesto"
    )
    operadas_r = 0
    for jornada in sim["jornadas_detalle"]:
        tope_jornada = round(jornada["base_dimensionamiento"] * CAP_UNDERDOG_LEY3_PCT, 2)
        for posicion in jornada["posiciones"]:
            if posicion["familia"] not in FAMILIAS_UNDERDOG_LEY3:
                continue
            operadas_r += 1
            assert posicion["inversion_total"] <= tope_jornada + TOLERANCIA_MXN, (
                f"Cota Underdog violada en {posicion['id_partido']} (J{jornada['jornada']}): "
                f"{posicion['inversion_total']} > {tope_jornada}"
            )
    assert operadas_r > 0, "La Familia R no operó en 1-11: la garantía sería vacua"


def test_invarianza_2_escudo_altitud_veta_la_hibrida_visitante():
    """[INVARIANZA 2 - TRAMPA DE ALTITUD]: ΔAlt+ >= 1000 m veta H2 con precedencia A1."""
    assert UMBRAL_VETO_ALTITUD_METROS == 1000.0, "El umbral legislado es 1000 m"

    # (a) Trampa certificada: Juárez (1120) vs Tijuana (30) => ΔAlt+ = 1090 m.
    veto = triaje_determinista_9_estrategias(
        _payload_juarez_tijuana(1090.0), CUOTAS_JUAREZ_TIJUANA, gamma=0.67
    )
    assert veto["codigo"] == "QBE-00", (
        f"El escudo no vetó la trampa de altitud: {veto.get('codigo')}"
    )
    assert veto["motivo"] == MOTIVO_VETO_ALTITUD
    assert veto["arquetipo_veto"] == ARQUETIPO_TRAMPA_ALTITUD
    assert veto["alpha"] == 0.0

    # (b) Justo por debajo del umbral: la H2 canónica subsiste (el escudo es de borde exacto).
    bajo = triaje_determinista_9_estrategias(
        _payload_juarez_tijuana(999.99), CUOTAS_JUAREZ_TIJUANA, gamma=0.67
    )
    assert bajo["codigo"] == "QBE-H2", (
        f"El escudo disparó por debajo de 1000 m: {bajo.get('codigo')}"
    )

    # (c) Sin evidencia de altitud no hay veto fabricado (GOVERNANCE-01).
    sin_dato = triaje_determinista_9_estrategias(
        _payload_juarez_tijuana(None), CUOTAS_JUAREZ_TIJUANA, gamma=0.67
    )
    assert sin_dato["codigo"] == "QBE-H2"
    assert "arquetipo_veto" not in sin_dato

    # (d) Precedencia estructural A1: el escudo se evalúa ANTES de exigir alpha_V > 0.
    from inspect import getsource

    fuente = getsource(triaje_determinista_9_estrategias)
    idx_rama = fuente.find('familia == "ASIMETRIA_VISITANTE"')
    idx_escudo = fuente.find(ARQUETIPO_TRAMPA_ALTITUD)
    idx_alpha = fuente.find("oX > theta_2 and aV > 0")
    idx_h2 = fuente.find('"QBE-H2"')
    assert 0 <= idx_rama < idx_escudo < idx_alpha, (
        "El Escudo de Altitud debe preceder la exigencia alpha_V > 0 (dictamen A1)"
    )
    assert idx_escudo < idx_h2, "El Escudo de Altitud debe preceder la emisión de QBE-H2"


@pytest.fixture(scope="module")
def sim_j11_def():
    """J11 con la ley defensiva V=0 (`DEF`) y Γ/certeza en su default neutro."""
    return ejecutar_simulacion_rentabilidad(
        bankroll_inicial=PATRIMONIO_BASE_SHIELD,
        jornadas=[11],
        modo="compuesto",
        modo_cobertura="DEF",
    )


@pytest.fixture(scope="module")
def sim_j11_bal():
    """J11 con cobertura dinámica balanceada (`BAL` ⇒ δ = 0.50·δ*)."""
    return ejecutar_simulacion_rentabilidad(
        bankroll_inicial=PATRIMONIO_BASE_SHIELD,
        jornadas=[11],
        modo="compuesto",
        modo_cobertura="BAL",
    )


def test_invarianza_3_cobertura_dinamica_def_vs_bal_reescribe_la_particion(sim_j11_def, sim_j11_bal):
    """[INVARIANZA 3 - COBERTURA DINÁMICA]: δ > 0 altera la partición y el PnL liquidado."""
    assert sim_j11_def["parametros_simulacion"]["modo_cobertura"] == "DEF"
    assert sim_j11_bal["parametros_simulacion"]["modo_cobertura"] == "BAL"

    posiciones_def = _posiciones(sim_j11_def)
    posiciones_bal = _posiciones(sim_j11_bal)
    assert posiciones_def, "J11 no produjo posiciones: el invariante sería vacuo"

    # DEF degenera exactamente al contrato defensivo sellado (δ = 0.0 en toda orden).
    assert all(p["delta_cobertura"] == 0.0 for p in posiciones_def), (
        "El modo DEF debe reproducir la ley V=0 con δ = 0.0000"
    )

    # BAL exige δ > 0 en al menos una orden con cobertura y un seguro estrictamente mayor.
    con_delta = [p for p in posiciones_bal if p["delta_cobertura"] > 0.0]
    assert con_delta, "El modo BAL no activó la cobertura dinámica (δ = 0 en toda la cartera)"

    mapa_def = {(p["id_partido"], p["familia"]): p for p in posiciones_def}
    comparadas = 0
    for posicion in con_delta:
        referencia = mapa_def.get((posicion["id_partido"], posicion["familia"]))
        if referencia is None:
            continue
        assert posicion["b_seg"] > referencia["b_seg"], (
            f"δ > 0 no incrementó el seguro en {posicion['id_partido']}"
        )
        assert posicion["b_prio"] < referencia["b_prio"], (
            f"δ > 0 no redujo el boleto de ataque en {posicion['id_partido']}"
        )
        comparadas += 1
    assert comparadas > 0, "No hubo posiciones comparables entre DEF y BAL"

    assert sim_j11_def["pnl_acumulado"] != sim_j11_bal["pnl_acumulado"], (
        "La cobertura dinámica no alteró el PnL: el parámetro δ no llegó a la partición"
    )


def test_invarianza_4_trinidad_de_certeza_y_trazabilidad_por_estrategia(sim_j11_def):
    """[INVARIANZA 4 - ADMISIÓN Y TRAZABILIDAD]: Trinidad §5.10 activa + resumen por estrategia."""
    parametros = sim_j11_def["parametros_simulacion"]
    for llave in (
        "gamma", "target_certeza_pct", "modo_certeza", "familias_vetadas_certeza",
        "modo_cobertura", "escudo_altitud_metros", "cap_underdog_ley3_pct", "delta_epist_origen",
    ):
        assert llave in parametros, f"Parámetro gobernante ausente del reporte: {llave}"

    assert parametros["gamma"] == 0.67
    assert parametros["modo_certeza"] == "CRECIMIENTO"
    assert parametros["familias_vetadas_certeza"] == []
    assert parametros["escudo_altitud_metros"] == UMBRAL_VETO_ALTITUD_METROS
    assert parametros["cap_underdog_ley3_pct"] == CAP_UNDERDOG_LEY3_PCT

    resumen = sim_j11_def["resumen_estrategias"]
    assert resumen, "El reporte no publica el desglose por estrategia"
    for codigo, bloque in resumen.items():
        for llave in ("posiciones", "inversion_total", "pnl_neto", "roi_pct", "tasa_acierto_pct"):
            assert llave in bloque, f"Bloque {codigo} sin la llave {llave}"
    assert sum(b["posiciones"] for b in resumen.values()) == sim_j11_def["posiciones_operables"]
    assert abs(sum(b["pnl_neto"] for b in resumen.values()) - sim_j11_def["pnl_acumulado"]) <= 0.05
    assert abs(
        sum(b["inversion_total"] for b in resumen.values())
        - sum(p["inversion_total"] for p in _posiciones(sim_j11_def))
    ) <= TOLERANCIA_MXN
