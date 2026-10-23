# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [LN-QBE-125] Cold Start Sincero (RECONVERTIDO por BR-1 opción b)
Régimen: [DIRGEN-STRICT]

Historia del Juez: hasta el Sprint 27 este archivo vigilaba el *Axioma del Prior de Mercado*
(`[LN-QBE-100]`), exigiendo que todo partido con S(I) = 0 sirviera `BS_QBE == BS_MKT` porque su
P′ había sido SUSTITUIDA por q_mkt. El Sprint 28 derogó expresamente esa regla (`[LN-QBE-125]`):
la identidad de Brier era un artefacto algebraico, no una medición. El Juez NO se elimina ni se
deja en rojo: se reconvierte en guardián de la nueva ley.
"""

from fastapi.testclient import TestClient
from src.web.app import app


def _reporte() -> dict:
    client = TestClient(app)
    resp = client.get("/api/markets/backtesting/calibration-report?league_id=1")
    assert resp.status_code == 200
    return resp.json()


def test_sin_sustitucion_de_vectores_en_el_controlador():
    """
    [INVARIANZA 1 - DEROGACIÓN EFECTIVA]: `markets.py` no puede volver a sustituir la P′ soberana
    por el consenso desmarcado q_mkt. La regla derogada no admite reubicación ni rama muerta.
    """
    from pathlib import Path

    markets = Path("src/web/routes/markets.py").read_text(encoding="utf-8")
    assert "p_local, p_empate, p_visitante = q_local, q_empate, q_visitante" not in markets, (
        "🚨 La sustitución de [LN-QBE-100] derogada por [LN-QBE-125] reapareció en el controlador."
    )
    assert "resolver_orden_fiduciario_con_indiferencia" in markets, (
        "El Visor no delega el orden fiduciario al plano canónico [LN-QBE-124] / [ARCH-1.4.64]."
    )


def test_jornadas_ciegas_declaradas_y_muestra_calibrada_expuesta():
    """
    [INVARIANZA 2 - CEGUERA DECLARADA + SEGMENTACIÓN · RECONVERTIDA por [LN-QBE-128]]:
    con el prior congelado de Apertura 2025 sembrado ([ARCH-1.4.69]) NINGUNA jornada es ya
    estructuralmente ciega (`es_cold_start` vacío, `alpha_etiqueta == "MEDIDO"`). La ceguera que
    subsiste es FÁCTICA y acotada: los partidos del club ausente del prior (Atlante) se declaran con
    `suficiencia_S_I == 0` y quedan fuera del doble agregado `resumen_calibrado` ≠ `resumen_global`,
    con `resumen_temporada` como alias del global.
    """
    data = _reporte()
    assert "resumen_calibrado" in data and "resumen_global" in data
    assert data["resumen_temporada"] == data["resumen_global"]

    # (a) Cero cold start ESTRUCTURAL: ninguna jornada queda íntegramente ciega.
    ciegas = [j for j in data["jornadas"] if j.get("es_cold_start")]
    assert not ciegas, (
        "🚨 COLD START ESTRUCTURAL: la(s) jornada(s) "
        f"{[j['jornada'] for j in ciegas]} siguen sin evidencia pese al prior sembrado [LN-QBE-128]."
    )
    for jornada in data["jornadas"]:
        assert jornada["alpha_etiqueta"] == "MEDIDO"

    # (b) La ceguera residual es FÁCTICA (club sin prior) y está acotada al frente de Atlante.
    partidos = [p for j in data["jornadas"] for p in j.get("partidos", [])]
    ciegos = [p for p in partidos if p.get("suficiencia_S_I") == 0]
    assert len(ciegos) <= 3, (
        f"🚨 CEGUERA RESIDUAL FUERA DE COTA: {len(ciegos)} partidos ciegos; el prior sólo deja "
        "ciegos los duelos del club ausente de Apertura 2025 (Atlante)."
    )
    assert len(ciegos) < len(partidos), "La muestra calibrada debe ser no vacía."
    for partido in ciegos:
        duelo = f"{partido.get('local')} {partido.get('visitante')}".lower()
        assert "atlante" in duelo, (
            f"🚨 CEGUERA NO DECLARADA: `{partido.get('id_partido')}` ({duelo}) es ciego y no "
            "corresponde al club ausente del prior."
        )

    # (c) Segmentación: el universo calibrado excluye EXACTAMENTE los partidos ciegos.
    informados = [p for p in partidos if p.get("suficiencia_S_I") == 1]
    calibrado = data["resumen_calibrado"]
    assert calibrado["total_partidos"] < data["resumen_global"]["total_partidos"]
    assert calibrado["total_partidos"] == len(informados)
    # J1-J3 ya pertenecen a la muestra calibrada (eran las jornadas ciegas de la ruta previa).
    assert {1, 2, 3}.issubset(set(calibrado["jornadas_auditadas"])), (
        "Las jornadas 1-3 no ingresaron al segmento calibrado: el prior no movió el sello S(I)."
    )


def test_cold_start_mide_en_vez_de_maquillar():
    """
    [INVARIANZA 3 - MEDICIÓN HONESTA · RECONVERTIDA por [LN-QBE-128]]: la ceguera residual de
    Atlante sigue MIDIENDO su degradación frente al mercado. Se exige que al menos un partido ciego
    publique |BS_QBE − BS_MKT| > 0.001: la P′ del prior puro NO es el consenso desmarcado
    [GOVERNANCE-01] y la derogación de `[LN-QBE-125]` permanece efectiva.
    """
    data = _reporte()
    ciegos = [
        p
        for j in data["jornadas"]
        for p in j.get("partidos", [])
        if p.get("suficiencia_S_I") == 0
    ]
    assert 1 <= len(ciegos) <= 3, (
        "La ceguera residual debe existir (Atlante no disputó Apertura 2025) y ser ≤ 3 partidos."
    )
    divergentes = [
        p
        for p in ciegos
        if abs(float(p.get("brier_qbe") or 0.0) - float(p.get("brier_mercado") or 0.0)) > 0.001
    ]
    assert divergentes, (
        "🚨 FALLO COLD START RESIDUAL: todos los partidos ciegos igualan el Brier del mercado — "
        "la P′ sigue siendo sustituida (artefacto Alpha ≡ 0.00%)."
    )
    # El sello de ceguera se conserva en el micro-DTO (la vitrina lo declara).
    assert all(p.get("suficiencia_S_I") == 0 for p in ciegos)

