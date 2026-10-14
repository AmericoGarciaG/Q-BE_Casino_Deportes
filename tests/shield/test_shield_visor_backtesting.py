# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DEL VISOR DE BACKTESTING Y CALIBRACIÓN FACTUAL DE TEMPORADA
Contrato vigilado:
- [LN-QBE-100] Tasa de Coincidencia Fiduciaria Global (H_fid), Brier Score Multicategórico
  (BS_QBE vs BS_MKT) y Alpha de Calibración sobre resultados reales consumados.
- [ARCH-1.4.38] Endpoint REST de solo lectura `GET /api/markets/backtesting/calibration-report`.
- [VAULT-CORE-007-C] Desmarque proporcional de vig `desmarcar_cuotas_proporcional(oL, oX, oV)`.
Regímenes: [DIRGEN-STRICT] en la matemática de calibración (verbatim de bóveda),
[DBBD-FUNGIBLE] en la capa de presentación.
Gobierno: [GOV-TEST-01] Aislamiento hermético en memoria (cero red / cero navegador / cero tokens).
"""


def test_juez_1_desmarque_proporcional_de_vig():
    """
    [INVARIANZA 1 - DESMARQUE PROPORCIONAL DE VIG]:
    Dado un triplete de cuotas de ventanilla con comisión (oL=2.00, oX=3.40, oV=4.00),
    la función canónica debe extraer el consenso sin vig repartiendo el sobreprecio
    de forma estrictamente proporcional a la probabilidad implícita bruta.
    Sobreprecio de la casa: S = 1/2.00 + 1/3.40 + 1/4.00 = 1.0441 (> 1.0).
    """
    from src.core.contracts.portfolio_math import desmarcar_cuotas_proporcional

    ql, qe, qv = desmarcar_cuotas_proporcional(2.00, 3.40, 4.00)

    # 1. Preservación del orden fiduciario del mercado
    assert ql > qe > qv, f"El consenso desmarcado perdió el orden del mercado: {(ql, qe, qv)}"
    # 2. Reparto proporcional exacto contra el sobreprecio S = 1.0441
    assert abs(ql - (0.50 / 1.0441)) <= 0.001, f"q_LOCAL fuera de tolerancia: {ql}"
    # 3. Clausura estricta de la medida de probabilidad
    assert abs((ql + qe + qv) - 1.0) <= 0.001, f"El consenso no normaliza a 1.0: {ql + qe + qv}"


def test_juez_2_brier_multicategorico():
    """
    [INVARIANZA 2 - BRIER SCORE MULTICATEGÓRICO]:
    El evaluador debe promediar el error cuadrático de las 3 casillas (1, X, 2) con
    normalización 1/(3N), penalizando por igual la sobreconfianza y la subconfianza.
    Dos partidos sellados: (0.60/0.25/0.15 -> LOCAL) y (0.30/0.50/0.20 -> EMPATE)
    deben rendir BS = 0.1042 exacto.
    """
    from src.core.contracts.portfolio_math import calcular_brier_multicategorico

    partidos = [
        {"p_local": 0.60, "p_empate": 0.25, "p_visitante": 0.15, "resultado": "LOCAL"},
        {"p_local": 0.30, "p_empate": 0.50, "p_visitante": 0.20, "resultado": "EMPATE"},
    ]

    bs = calcular_brier_multicategorico(partidos)

    assert abs(bs - 0.1042) <= 0.001, f"Brier Score multicategórico desviado: {bs}"


def test_juez_3_endpoint_calibration_report_contrato():
    """
    [INVARIANZA 3 - ENDPOINT DE SOLO LECTURA Y CONTRATO FACTUAL]:
    El endpoint debe responder HTTP 200 (jamás 400/500) y emitir el contrato
    {resumen_temporada, jornadas} con las métricas macro de calibración.
    Universo auditable factual: jornadas J10 ∪ J11 de la bóveda viva (18 partidos concluidos).
    """
    from fastapi.testclient import TestClient
    from src.web.app import app

    client = TestClient(app)
    response = client.get("/api/markets/backtesting/calibration-report?league_id=1")

    assert response.status_code == 200, (
        f"🚨 ERROR EN ENDPOINT: Retornó {response.status_code} en lugar de 200 OK. "
        f"Detalle: {response.text}"
    )
    data = response.json()
    assert "resumen_temporada" in data, "Falta el bloque macro `resumen_temporada`"
    assert "jornadas" in data, "Falta la tabla meso `jornadas`"

    resumen = data["resumen_temporada"]
    for clave in (
        "total_partidos",
        "tasa_coincidencia_fiduciaria_pct",
        "brier_score_qbe",
        "brier_score_mercado",
    ):
        assert clave in resumen, f"Falta la métrica macro `{clave}` en el resumen de temporada"

    assert resumen["total_partidos"] >= 18, (
        "El universo auditable factual (J10 ∪ J11) no fue resuelto desde la bóveda: "
        f"total_partidos={resumen['total_partidos']}"
    )
    assert len(data["jornadas"]) >= 2, "Faltan las jornadas con resultados consumados"
