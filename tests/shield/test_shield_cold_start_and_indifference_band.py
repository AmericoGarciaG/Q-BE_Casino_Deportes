# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DE LA BANDA DE INDIFERENCIA FIDUCIARIA Y DEL COLD START SINCERO
Contratos vigilados:
- [LN-QBE-124] `resolver_orden_fiduciario_con_indiferencia` (banda ε = 1.00 % + desempate por
  altitud ΔAlt⁺ ≥ 1000 msnm sobre el par {LOCAL, EMPATE}); P_max jamás se altera y la masa de
  cobertura P_max + P_mid es invariante bajo la permutación.
- [LN-QBE-125] Cold Start Sincero: derogación de la sustitución `p_* ← q_*` y doble agregado
  declarado (`resumen_calibrado` vs `resumen_global`, con `resumen_temporada` como alias).
- [ARCH-1.4.64] Delegación del orden al plano canónico y precedencia declarada del desnivel.
Regímenes: [DIRGEN-STRICT] en la matemática de la banda, [DBBD-FUNGIBLE] en la vitrina.
Gobierno: [GOV-TEST-01] hermetismo (cero red / cero navegador / cero tokens).
"""

EPS = 0.0100
ALTURA_RESCATE = 1000.0


def test_juez_1_rescate_territorial_promueve_al_local_a_pmid():
    """
    [INVARIANZA 1 - RESCATE TERRITORIAL]: con P′ = (0.2554, 0.2601, 0.4845) — frontera
    P_mid/P_low plana de 0.0047 (⊂ banda ε = 0.01) — y ΔAlt⁺ = 1700 msnm, el LOCAL se promueve a
    P_mid y el EMPATE desciende a P_low. P_max (VISITANTE, 0.4845) NO se mueve y la masa de
    cobertura (P_max + P_mid) queda exactamente igual: la banda permuta, no reescribe.
    """
    from src.core.contracts.portfolio_math import (
        BANDA_INDIFERENCIA_EPSILON,
        UMBRAL_ALTITUD_RESCATE_METROS,
        resolver_orden_fiduciario_con_indiferencia,
    )

    # Manifiesto declarado de la ley: constantes propias, jamás el umbral del Escudo de Altitud.
    assert BANDA_INDIFERENCIA_EPSILON == EPS
    assert UMBRAL_ALTITUD_RESCATE_METROS == ALTURA_RESCATE

    p1, px, p2 = 0.2554, 0.2601, 0.4845
    orden = resolver_orden_fiduciario_con_indiferencia(p1, px, p2, delta_alt=1700.0)

    assert orden["r_max"] == "VISITANTE"
    assert orden["p_max_val"] == p2, "🚨 P_max fue alterado por la banda (prohibido)."
    assert orden["r_mid"] == "LOCAL"
    assert orden["p_mid_val"] == p1
    assert orden["r_low"] == "EMPATE"
    assert orden["p_low_val"] == px
    assert orden["rescate_indiferencia"] is True
    assert orden["delta_alt_metros"] == 1700.0
    assert orden["separacion_mid_low"] == 0.0047

    # Masa de cobertura INVARIANTE (misma antes y después de la permutación).
    assert orden["masa_cobertura_pct"] == round((p2 + p1) * 100.0, 2)


def test_juez_2_banda_inerte_sin_altitud_fuera_de_banda_o_fuera_del_eje_localia():
    """
    [INVARIANZA 2 - EL RESCATE ES CONJUNTIVO]: sin desnivel (ΔAlt⁺ = 0 o < 1000 m), con la
    frontera fuera de la banda (separación 0.0399 > ε) o con el par en disputa distinto de
    {LOCAL, EMPATE}, el orden aritmético estricto manda y `rescate_indiferencia` es False.
    """
    from src.core.contracts.portfolio_math import (
        BANDA_INDIFERENCIA_EPSILON,
        resolver_orden_fiduciario_con_indiferencia,
    )

    # (a) Vector de Atlante SIN altitud: banda plana pero rescate inerte.
    sin_altitud = resolver_orden_fiduciario_con_indiferencia(0.2554, 0.2601, 0.4845, delta_alt=0.0)
    assert sin_altitud["r_mid"] == "EMPATE"
    assert sin_altitud["r_low"] == "LOCAL"
    assert sin_altitud["rescate_indiferencia"] is False

    # (b) Borde inferior del umbral: 999.9 msnm NO habilita el rescate (borde ≥ 1000).
    borde = resolver_orden_fiduciario_con_indiferencia(0.2554, 0.2601, 0.4845, delta_alt=999.9)
    assert borde["rescate_indiferencia"] is False
    assert borde["r_mid"] == "EMPATE"

    # (c) Separación mayor a la banda: la altitud extrema no rescata lo que ya está separado.
    fuera_banda = resolver_orden_fiduciario_con_indiferencia(
        0.3000, 0.2601, 0.4399, delta_alt=3500.0
    )
    assert abs(0.3000 - 0.2601) > BANDA_INDIFERENCIA_EPSILON
    assert fuera_banda["rescate_indiferencia"] is False
    assert fuera_banda["r_mid"] == "LOCAL"   # orden aritmético puro, no rescate

    # (d) Par en disputa {LOCAL, VISITANTE}: el rescate es exclusivo del eje localía.
    eje_visitante = resolver_orden_fiduciario_con_indiferencia(
        0.3300, 0.0500, 0.3200, delta_alt=3000.0
    )
    assert eje_visitante["r_max"] == "LOCAL"
    assert (eje_visitante["r_mid"], eje_visitante["r_low"]) == ("VISITANTE", "EMPATE")
    assert eje_visitante["rescate_indiferencia"] is False

    # (e) Desnivel negativo (anfitrión a menor altitud) jamás se convierte en bono.
    negativo = resolver_orden_fiduciario_con_indiferencia(
        0.2554, 0.2601, 0.4845, delta_alt=-1700.0
    )
    assert negativo["delta_alt_metros"] == 0.0
    assert negativo["rescate_indiferencia"] is False


def test_juez_3_cold_start_sincero_y_doble_agregado_declarado():
    """
    [INVARIANZA 3 - COLD START SINCERO]: el endpoint de calibración declara la ceguera
    (`es_cold_start` + `alpha_etiqueta == "COLD_START"` en las jornadas ciegas) y sirve el doble
    agregado `resumen_calibrado` (sólo S(I)=1) vs `resumen_global`, conservando `resumen_temporada`
    como alias byte-idéntico del global (tres consumidores sellados lo leen).
    """
    from fastapi.testclient import TestClient
    from src.web.app import app

    client = TestClient(app)
    resp = client.get("/api/markets/backtesting/calibration-report?league_id=1")
    assert resp.status_code == 200
    data = resp.json()

    for clave in ("resumen_temporada", "resumen_calibrado", "resumen_global", "jornadas"):
        assert clave in data, f"🚨 FALTA el bloque `{clave}` en el reporte de calibración"

    global_, calibrado = data["resumen_global"], data["resumen_calibrado"]
    assert data["resumen_temporada"] == global_, (
        "El alias sellado `resumen_temporada` dejó de ser idéntico a `resumen_global`."
    )

    # El universo calibrado es un subconjunto ESTRICTO del global (la ceguera aporta N).
    assert calibrado["total_partidos"] < global_["total_partidos"], (
        "La muestra calibrada no excluye ningún partido ciego: la segmentación no opera."
    )

    # Jornadas ciegas declaradas (J1–J3 de la bóveda viva) y fuera de la muestra calibrada.
    ciegas = [j for j in data["jornadas"] if j.get("es_cold_start")]
    assert len(ciegas) >= 3, "🚨 No se declaró la ceguera de las jornadas de Cold Start"
    for jornada in ciegas:
        assert jornada["alpha_etiqueta"] == "COLD_START"
    jornadas_calibradas = set(calibrado["jornadas_auditadas"])
    assert jornadas_calibradas.isdisjoint({j["jornada"] for j in ciegas}), (
        "Una jornada ciega contaminó la muestra calibrada [LN-QBE-125]."
    )

    # Conteo del universo calibrado = partidos realmente informados en la tabla meso.
    informados = sum(
        1
        for j in data["jornadas"]
        for p in j.get("partidos", [])
        if p.get("suficiencia_S_I") == 1
    )
    assert calibrado["total_partidos"] == informados
    # Invarianza de la taxonomía de vértices dentro de la muestra calibrada.
    assert calibrado["total_p_mid"] == (
        calibrado["total_p_mid_empate"] + calibrado["total_p_mid_rival"]
    )
    suma_pct = (
        calibrado["p_max_aciertos_pct"]
        + calibrado["p_mid_rescate_pct"]
        + calibrado["p_low_ruptura_pct"]
    )
    assert abs(suma_pct - 100.0) <= 0.25, (
        f"🚨 RUPTURA SUMA en la muestra calibrada: P_max+P_mid+P_low={suma_pct}% != 100%"
    )

def test_juez_4_atlante_cian_con_rescate_y_cero_sustitucion_de_vectores():
    """
    [INVARIANZA 4 - MICRO-TARJETA HONESTA]: `LIGAMX-J10-01` (Atlante, 4-2, ΔAlt⁺ = 1700 msnm)
    se sirve con el vértice consumado en `P_MID` (`r_mid = LOCAL`, `rescate_indiferencia = True`)
    y con su P′ SOBERANA intacta — 0.2554 / 0.2601 / 0.4845, jamás q_mkt. Ningún partido ciego
    puede reproducir la firma artefactual BS_QBE ≡ BS_MKT del prior sustituido.
    """
    from pathlib import Path

    from fastapi.testclient import TestClient
    from src.web.app import app

    client = TestClient(app)
    resp = client.get("/api/markets/backtesting/calibration-report?league_id=1")
    assert resp.status_code == 200
    data = resp.json()

    partidos = [p for j in data["jornadas"] for p in j.get("partidos", [])]
    atlante = next((p for p in partidos if p.get("id_partido") == "LIGAMX-J10-01"), None)
    assert atlante is not None, "La bóveda viva no sirve `LIGAMX-J10-01` en el Visor"

    assert atlante["clasificacion_triada"] == "P_MID", (
        "El rescate territorial no promovió a Atlante a la cobertura secundaria [LN-QBE-124]."
    )
    assert atlante["r_mid"] == "LOCAL" and atlante["r_low"] == "EMPATE"
    assert atlante["rescate_indiferencia"] is True
    assert float(atlante["delta_alt_metros"]) >= ALTURA_RESCATE
    assert (atlante["p_local"], atlante["p_empate"], atlante["p_visitante"]) == (
        0.2554, 0.2601, 0.4845
    ), "🚨 La P′ servida no es la soberana: hubo sustitución de vectores."

    # Cero sustitución: en los partidos ciegos el vector servido NO es el consenso del mercado
    # (con la sustitución derogada, el Brier de Q-BE deja de ser idéntico al del mercado).
    ciegos = [p for p in partidos if p.get("suficiencia_S_I") == 0]
    assert len(ciegos) >= 27, "El Juez exige ≥ 27 partidos ciegos (J1–J3) en la bóveda viva"
    divergentes = [
        p for p in ciegos
        if abs(float(p["brier_qbe"]) - float(p["brier_mercado"])) > 0.001
    ]
    assert divergentes, (
        "🚨 FALLO [LN-QBE-125]: ningún partido ciego diverge del mercado — la sustitución sigue viva."
    )

    # Guardián de código: el bloque derogado no puede reaparecer en el controlador.
    markets = Path("src/web/routes/markets.py").read_text(encoding="utf-8")
    assert "p_local, p_empate, p_visitante = q_local, q_empate, q_visitante" not in markets, (
        "🚨 Reapareció la sustitución de [LN-QBE-100] derogada por [LN-QBE-125]."
    )

