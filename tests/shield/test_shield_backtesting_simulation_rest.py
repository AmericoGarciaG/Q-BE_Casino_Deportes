# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — PASARELA REST DE SIMULACIÓN FINANCIERA RETROSPECTIVA
Juez Inmutable: [LN-QBE-114] / [DES-QBE-068] / [DES-QBE-069]

Invariantes legisladas:
1. Contrato financiero expuesto: `POST /api/markets/backtesting/simulate` responde 200 y publica
   el contrato de siete llaves de `[LN-QBE-107]` (curva, PnL, ROI, drawdown y detalle meso).
2. Veto fiduciario a través del cable: `excluir_estrategias=["QBE-R1","QBE-R2"]` altera el
   resultado económico y declara la intercepción — la capa web NO reimplementa aritmética,
   sólo transporta el payload hacia `ejecutar_simulacion_rentabilidad`.
"""


def _payload(**overrides):
    """Payload canónico: patrimonio base del Juez, temporada completa y modo compuesto."""
    base = {
        "bankroll_inicial": 10000.0,
        "rango_jornadas": "1-11",
        "modo_interes": "compuesto",
        "excluir_estrategias": [],
    }
    base.update(overrides)
    return base


def _post_simular(payload):
    from fastapi.testclient import TestClient

    from src.web.app import app

    cliente = TestClient(app)
    return cliente.post("/api/markets/backtesting/simulate", json=payload)


def test_invarianza_1_endpoint_publica_contrato_financiero():
    """[INVARIANZA 1 - CONTRATO]: el endpoint devuelve el reporte íntegro del motor, sin recortes."""
    respuesta = _post_simular(_payload())

    assert respuesta.status_code == 200, (
        f"La pasarela REST no responde: {respuesta.status_code} {respuesta.text[:400]}"
    )

    data = respuesta.json()
    assert data["status"] == "EXITO", f"El motor reportó un estado no exitoso: {data.get('status')}"

    # Llaves maestras del contrato [LN-QBE-107] (transcripción, no recálculo).
    for llave in (
        "bankroll_inicial",
        "bankroll_final",
        "pnl_acumulado",
        "roi_acumulado_pct",
        "drawdown_maximo_pct",
        "curva_bankroll",
        "jornadas_detalle",
        "exclusiones_activas",
        "vetos_aplicados",
    ):
        assert llave in data, f"Contrato incompleto: falta la llave '{llave}'"

    assert data["bankroll_inicial"] == 10000.0
    assert data["exclusiones_activas"] == []
    assert data["vetos_aplicados"] == 0

    # Detalle meso apto para la curva de capital (Chart.js lee `bankroll_final` por jornada).
    detalle = data["jornadas_detalle"]
    assert detalle, "El detalle meso quedó vacío: no hay evidencia que graficar"
    for jornada in detalle:
        assert "jornada" in jornada
        assert "bankroll_final" in jornada
        assert "pnl_jornada" in jornada
        assert "inversion_total" in jornada
    assert detalle[-1]["bankroll_final"] == data["bankroll_final"], (
        "La curva no cierra en el bankroll final: la UI graficaría una trayectoria falsa"
    )


def test_invarianza_2_veto_fiduciario_por_el_cable_altera_el_pnl():
    """[INVARIANZA 2 - VETO]: excluir la Familia R cambia el PnL y se declara en el reporte."""
    base = _post_simular(_payload())
    vetado = _post_simular(
        _payload(excluir_estrategias=["QBE-R1", "QBE-R2"])
    )

    assert base.status_code == 200
    assert vetado.status_code == 200

    sin_veto = base.json()
    con_veto = vetado.json()

    assert con_veto["exclusiones_activas"] == ["QBE-R1", "QBE-R2"], (
        "La pasarela no transportó la lista de exclusión fiduciaria"
    )
    assert con_veto["vetos_aplicados"] > 0, (
        "Sobre el corpus real 1-11 el veto debe interceptar posiciones: garantía vacua"
    )
    assert con_veto["pnl_acumulado"] != sin_veto["pnl_acumulado"], (
        "El veto no alteró el PnL: o el payload se perdió en el cable o la capa web lo ignoró"
    )
    assert con_veto["posiciones_operables"] < sin_veto["posiciones_operables"], (
        "El veto no redujo las posiciones operables: no hubo intercepción real"
    )

    codigos = {
        (posicion.get("estrategia_codigo") or posicion.get("familia") or "")
        for jornada in con_veto["jornadas_detalle"]
        for posicion in jornada["posiciones"]
    }
    assert "QBE-R1" not in codigos and "QBE-R2" not in codigos, (
        f"Capital asignado a una familia vetada: {sorted(codigos)}"
    )
