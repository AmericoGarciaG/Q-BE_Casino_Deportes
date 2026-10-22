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
    [INVARIANZA 2 - CEGUERA DECLARADA + SEGMENTACIÓN]: J1–J3 (S(I) = 0) portan
    `es_cold_start = True` y `alpha_etiqueta = "COLD_START"`; el reporte expone el doble agregado
    `resumen_calibrado` ≠ `resumen_global`, con `resumen_temporada` como alias del global.
    """
    data = _reporte()
    assert "resumen_calibrado" in data and "resumen_global" in data
    assert data["resumen_temporada"] == data["resumen_global"]

    ciegas = [j for j in data["jornadas"] if j.get("es_cold_start")]
    assert len(ciegas) >= 3, "El test requiere al menos 3 jornadas ciegas (J1-J3) en la BD"
    for jornada in ciegas:
        assert jornada["alpha_etiqueta"] == "COLD_START"
        assert all(
            p.get("suficiencia_S_I") == 0 for p in jornada.get("partidos", [])
        ), "Una jornada declarada ciega contiene partidos informados."

    calibrado = data["resumen_calibrado"]
    assert calibrado["total_partidos"] < data["resumen_global"]["total_partidos"]
    assert set(calibrado["jornadas_auditadas"]).isdisjoint({j["jornada"] for j in ciegas})


def test_cold_start_mide_en_vez_de_maquillar():
    """
    [INVARIANZA 3 - MEDICIÓN HONESTA]: con la sustitución derogada, la ignorancia deja de ser
    paridad con el mercado. Se exige que al menos un partido ciego publique
    |BS_QBE − BS_MKT| > 0.001, es decir, que la degradación del prior puro SE MIDA
    [GOVERNANCE-01].
    """
    data = _reporte()
    ciegos = [
        p
        for j in data["jornadas"]
        for p in j.get("partidos", [])
        if p.get("suficiencia_S_I") == 0
    ]
    assert len(ciegos) >= 27, "El test requiere al menos 27 partidos ciegos (J1-J3) en la BD"
    divergentes = [
        p for p in ciegos
        if abs(float(p.get("brier_qbe", 0.0)) - float(p.get("brier_mercado", 0.0))) > 0.001
    ]
    assert divergentes, (
        "🚨 FALLO COLD START: todos los partidos ciegos igualan el Brier del mercado — "
        "la P′ sigue siendo sustituida (artefacto Alpha ≡ 0.00%)."
    )
    # El sello de ceguera se conserva en el micro-DTO (la vitrina lo declara).
    assert all(p.get("suficiencia_S_I") == 0 for p in ciegos)

