# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — SANDBOX DE RENTABILIDAD RETROSPECTIVA SUITE
Juez Inmutable: [LN-QBE-107] / [ARCH-1.4.46]
Base de Gobierno: Kybern Framework v13.5 [GOV-TEST-01] (Pure Read-Only / In-Memory Test)

Invariantes legisladas:
1. Liquidación factual en los CINCO desenlaces canónicos con indemnidad V=0 en tablas.
2. Cota dura de cartera (25%) y cadena rodante de capital jornada a jornada.
3. Contrato de salida: siete llaves maestras + bloque de proyección anualizada.
4. No-ruina, determinismo estricto y conservación del PnL acumulado.
5. Veto fiduciario selectivo por familia estratégica (`[LN-QBE-113]`): cero capital a códigos vetados.
"""

from scripts.laboratorio.sandbox_rentabilidad_pipeline import (
    ESCENARIO_COBERTURA_V0,
    ESCENARIO_DOBLE_COBRO_PA,
    ESCENARIO_NO_LIQUIDABLE,
    ESCENARIO_RUPTURA,
    ESCENARIO_VICTORIA,
    PATRIMONIO_BASE_SHIELD,
    ejecutar_simulacion_rentabilidad,
    liquidar_posicion_factual,
)

TOLERANCIA_V0_MXN = 0.08  # [LN-QBE-107] holgura de redondeo del piso de ventanilla


def _posicion_h1(pago_anticipado: bool = False) -> dict:
    """Posición H1 canónica: B_i = $100, O_fav = 2.00, O_empate = 3.50 (partición V=0 sellada)."""
    return {
        "id_partido": "TEST-H1",
        "familia": "QBE-H1",
        "inversion_total": 100.0,
        "b_prio": 71.43,
        "b_seg": 28.57,
        "cuota_ataque": 2.00,
        "cuota_empate": 3.50,
        "lado_ataque": "LOCAL",
        "pago_anticipado": pago_anticipado,
        "cubre_empate": True,
    }


def test_invarianza_1_liquidacion_factual_cinco_desenlaces():
    """[INVARIANZA 1 - V=0]: tablas en familia con cobertura preservan el capital (|PnL| <= $0.08)."""
    # 1. COBERTURA V=0: empate 1-1 en familia H1 -> recupera el 100% del capital.
    res_empate = liquidar_posicion_factual(_posicion_h1(), 1, 1)
    assert res_empate["escenario"] == ESCENARIO_COBERTURA_V0
    assert abs(res_empate["pnl_mxn"]) <= TOLERANCIA_V0_MXN, (
        f"🚨 RUPTURA V=0: el empate cubierto no indemnizó el capital (PnL {res_empate['pnl_mxn']})"
    )

    # 2. VICTORIA: gana la pierna de ataque -> cobro íntegro de B_prio · O_ataque.
    res_victoria = liquidar_posicion_factual(_posicion_h1(), 2, 0)
    assert res_victoria["escenario"] == ESCENARIO_VICTORIA
    assert res_victoria["cobro_mxn"] == 142.86
    assert res_victoria["pago_anticipado_acreditado"] is False

    # 3. DOBLE COBRO PA: tablas con ventaja in-play de 2 goles acreditada por traza.
    res_pa = liquidar_posicion_factual(
        _posicion_h1(pago_anticipado=True), 1, 1, ventaja_maxima_favorito=2
    )
    assert res_pa["escenario"] == ESCENARIO_DOBLE_COBRO_PA
    assert res_pa["cobro_mxn"] == 242.86
    assert res_pa["pago_anticipado_acreditado"] is True

    # 4. RUPTURA: gana el bando no cubierto -> pérdida íntegra del stake.
    res_ruptura = liquidar_posicion_factual(_posicion_h1(), 0, 1)
    assert res_ruptura["escenario"] == ESCENARIO_RUPTURA
    assert res_ruptura["cobro_mxn"] == 0.0
    assert res_ruptura["pnl_mxn"] == -100.0

    # 5. NO LIQUIDABLE: sin marcador oficial jamás se fabrica un 0-0 (capital devuelto).
    res_nulo = liquidar_posicion_factual(_posicion_h1(), None, None)
    assert res_nulo["escenario"] == ESCENARIO_NO_LIQUIDABLE
    assert res_nulo["pnl_mxn"] == 0.0
    assert res_nulo["capital_devuelto"] is True

    escenarios = {
        res_empate["escenario"], res_victoria["escenario"], res_pa["escenario"],
        res_ruptura["escenario"], res_nulo["escenario"],
    }
    assert escenarios == {
        ESCENARIO_VICTORIA, ESCENARIO_COBERTURA_V0, ESCENARIO_DOBLE_COBRO_PA,
        ESCENARIO_RUPTURA, ESCENARIO_NO_LIQUIDABLE,
    }, f"La partición de liquidación no es colectivamente exhaustiva: {sorted(escenarios)}"


def test_invarianza_2_cota_dura_y_cadena_rodante_de_capital():
    """[INVARIANZA 2 - HARD CAP]: ninguna jornada despliega más del 25% del capital disponible."""
    reporte = ejecutar_simulacion_rentabilidad(
        bankroll_inicial=PATRIMONIO_BASE_SHIELD, jornadas=list(range(1, 12)), modo="compuesto"
    )
    assert reporte["status"] == "EXITO"
    detalle = reporte["jornadas_detalle"]
    assert len(detalle) == 11, f"La simulación perdió jornadas: {len(detalle)}"

    assert detalle[0]["bankroll_disponible"] == PATRIMONIO_BASE_SHIELD
    for idx, jornada in enumerate(detalle):
        # Cota constitucional de `[LN-QBE-082]` + residuo de redondeo del prorrateo sellado:
        # el asignador redondea CADA posición a centavos, por lo que la suma agregada puede
        # exceder la bolsa en, cuando mucho, $0.01 por boleto (residuo aritmético, no desvío).
        residuo_redondeo = 0.01 * max(1, len(jornada["posiciones"])) + 0.01
        tope_cartera = round(0.25 * jornada["base_dimensionamiento"], 2) + residuo_redondeo
        assert 0.0 <= jornada["inversion_total"] <= tope_cartera, (
            f"🚨 VIOLACIÓN HARD CAP en J{jornada['jornada']}: "
            f"inv={jornada['inversion_total']} > tope={tope_cartera}"
        )
        suma_posiciones = round(sum(p["inversion_total"] for p in jornada["posiciones"]), 2)
        assert abs(suma_posiciones - jornada["inversion_total"]) <= 0.02
        if idx > 0:
            assert jornada["bankroll_disponible"] == detalle[idx - 1]["bankroll_final"], (
                "La cadena rodante de capital está rota en J" + str(jornada["jornada"])
            )
            assert jornada["base_dimensionamiento"] == jornada["bankroll_disponible"]

    assert reporte["posiciones_operables"] > 0, "El dataset real no produjo posiciones operables"
    assert reporte["capital_no_desplegado"] >= 0.0


def test_invarianza_3_contrato_de_llaves_maestras_y_proyeccion():
    """[INVARIANZA 3 - CONTRATO]: siete llaves maestras + proyeccion_anual serializable."""
    reporte = ejecutar_simulacion_rentabilidad(
        bankroll_inicial=PATRIMONIO_BASE_SHIELD, jornadas=[1, 2, 3], modo="compuesto"
    )
    for llave in (
        "bankroll_final", "pnl_acumulado", "roi_acumulado_pct", "drawdown_maximo_pct",
        "resumen_coberturas", "jornadas_detalle", "curva_bankroll",
    ):
        assert llave in reporte, f"Llave maestra ausente del contrato [LN-QBE-107]: {llave}"

    proyeccion = reporte["proyeccion_anual"]
    for llave in ("lineal_mxn", "compuesta_mxn", "roi_anual_compuesto_pct"):
        assert llave in proyeccion, f"Llave de proyección ausente: {llave}"
        assert isinstance(proyeccion[llave], (int, float))

    assert len(reporte["curva_bankroll"]) == len(reporte["jornadas_detalle"]) + 1
    assert reporte["curva_bankroll"][0] == PATRIMONIO_BASE_SHIELD
    assert reporte["curva_bankroll"][-1] == reporte["bankroll_final"]
    assert set(reporte["resumen_coberturas"]).issuperset(
        {ESCENARIO_VICTORIA, ESCENARIO_COBERTURA_V0, ESCENARIO_DOBLE_COBRO_PA,
         ESCENARIO_RUPTURA, ESCENARIO_NO_LIQUIDABLE}
    )

    import json
    json.dumps(reporte, ensure_ascii=False)  # contrato JSON estricto: cero objetos opacos


def test_invarianza_4_no_ruina_determinismo_y_conservacion():
    """[INVARIANZA 4 - FIDUCIA]: cero ruina, ejecución determinista y PnL acumulado conservado."""
    primero = ejecutar_simulacion_rentabilidad(
        bankroll_inicial=PATRIMONIO_BASE_SHIELD, jornadas=list(range(1, 12)), modo="plano"
    )
    segundo = ejecutar_simulacion_rentabilidad(
        bankroll_inicial=PATRIMONIO_BASE_SHIELD, jornadas=list(range(1, 12)), modo="plano"
    )
    assert primero["bankroll_final"] > 0.0, "🚨 RUTA DE RUINA: el fondo se extinguió"
    assert primero["bankroll_final"] == segundo["bankroll_final"], "La simulación no es determinista"
    assert 0.0 <= primero["drawdown_maximo_pct"] <= 100.0

    pnl_suma = round(sum(j["pnl_jornada"] for j in primero["jornadas_detalle"]), 2)
    assert abs(pnl_suma - primero["pnl_acumulado"]) <= 0.05, (
        f"Conservación rota: suma de jornadas {pnl_suma} ≠ acumulado {primero['pnl_acumulado']}"
    )
    assert primero["resumen_coberturas"][ESCENARIO_NO_LIQUIDABLE] == sum(
        1 for j in primero["jornadas_detalle"] for p in j["posiciones"]
        if p["escenario"] == ESCENARIO_NO_LIQUIDABLE
    )


def test_invarianza_5_veto_fiduciario_excluye_familia_r():
    """[INVARIANZA 5 - VETO SELECTIVO]: Si se excluye la Familia R, no debe haber órdenes QBE-R1 ni QBE-R2 en la cartera."""
    from scripts.laboratorio.sandbox_rentabilidad_pipeline import ejecutar_simulacion_rentabilidad

    sim = ejecutar_simulacion_rentabilidad(
        bankroll_inicial=PATRIMONIO_BASE_SHIELD,
        jornadas=list(range(1, 12)),
        modo="compuesto",
        excluir_estrategias=["QBE-R1", "QBE-R2"],
    )

    assert sim["status"] == "EXITO"
    assert sim["exclusiones_activas"] == ["QBE-R1", "QBE-R2"], (
        "El reporte no declara el filtro de exclusión activo ([ARCH-1.4.52])"
    )

    # Auditar cada orden generada en el histórico de la simulación
    ordenes_operadas = 0
    for jornada in sim["jornadas_detalle"]:
        for orden in jornada["posiciones"]:
            codigo = orden.get("estrategia_codigo") or orden.get("familia") or ""
            # Garantía Absoluta: Ninguna orden de la Familia R puede recibir capital
            assert codigo not in ["QBE-R1", "QBE-R2"], (
                f"Violación de Veto Fiduciario: Se encontró una orden {codigo}"
            )
            ordenes_operadas += 1

    # Cero vacuidad: sobre el corpus real 1-11 la Familia R opera (18 de 30 órdenes en la
    # línea base), por lo que un veto con cero intercepciones es una prueba inconclusa.
    assert ordenes_operadas > 0, "La cartera depurada quedó vacía: no hay evidencia que auditar"
    assert sim["vetos_aplicados"] > 0, (
        "El veto no interceptó ninguna posición: la garantía sería vacua"
    )

    vetos = [
        descarte for j in sim["jornadas_detalle"] for descarte in j["descartes"]
        if descarte.get("veto_fiduciario")
    ]
    assert len(vetos) == sim["vetos_aplicados"], (
        "El contador de vetos no coincide con las abstenciones declaradas"
    )
    assert all(d.get("familia_vetada") in ("QBE-R1", "QBE-R2") for d in vetos), (
        "Un veto fiduciario se aplicó fuera de la lista de exclusión"
    )

