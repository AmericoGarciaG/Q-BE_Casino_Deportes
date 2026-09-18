# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [LN-QBE-060 / ARCH-1.6.9] Candado 4 Anti-Contracorriente y Herencia PA
Doctrina: Kybern Framework v8.0 / v12.0 [GOV-TEST-01 a 07]
"""

import pytest
from src.core.evaluator import evaluar_estrategia_individual
from src.reporting.narrative import generar_tesis_madlibs_fallback


def test_candado_4_veta_familia_r_en_probabilidad_dominante():
    """
    Sad Path / Edge Case: San Luis vs Necaxa.
    San Luis es favorito por momio y mantiene P_Fav (35.9%) > P_Und (30.1%),
    pero Necaxa tiene Edge negativo (-3.69%).
    Debe VETAR R1 y R2 terminantemente.
    """
    metricas_san_luis = {
        "prob_fav": 0.359,
        "prob_emp": 0.340,
        "prob_und": 0.301,
        "edge_fav": -0.0834,
        "edge_emp": +0.0582,
        "edge_und": -0.0369,
        "theta_req_fav": 0.40,
        "theta_req_emp": 0.30,
        "theta_req_und": 0.35,
        "fav_pts_pj": 0.75,
        "fav_gc_promedio": 1.87,
        "und_pts_pj": 1.00,
        "und_gc_promedio": 1.62,
        "peso_h2h": 0.0,
        "pago_anticipado": True
    }

    # Evaluar QBE-R2
    res_r2 = evaluar_estrategia_individual("QBE-R2", metricas_san_luis)
    assert res_r2["viable"] is False, "QBE-R2 no debe ser viable en Sueño Profundo / Candado 4"
    assert "SUEÑO PROFUNDO" in res_r2.get("motivo", "").upper() or "ANTI-CONTRACORRIENTE" in res_r2.get("motivo", "").upper()

    # Evaluar QBE-R1
    res_r1 = evaluar_estrategia_individual("QBE-R1", metricas_san_luis)
    assert res_r1["viable"] is False, "QBE-R1 no debe ser viable en Sueño Profundo"


def test_herencia_y_propagacion_pago_anticipado_en_boletos():
    """[ARCH-1.6.9] Valida que la insignia y el sufijo '+ PA' se propaguen a las órdenes de ejecución."""
    from src.core.portfolio import PortfolioEngine

    partido_ejemplo = [{
        "id_partido": "P1",
        "partido_nombre": "Toluca vs Santos",
        "horario": "Sábado 19:00",
        "strategy_code": "QBE-D1+",
        "strategy_nombre": "Favorito Directo Potenciado",
        "ev_neto_roi": 0.15,
        "psi_downside": 0.05,
        "phi_lead2": 0.50,
        "odd_fav": 1.70,
        "odd_emp": 3.60,
        "odd_und": 4.50,
        "fav_name": "Toluca",
        "und_name": "Santos",
        "pago_anticipado": True
    }]

    plan = PortfolioEngine.build_plan(partido_ejemplo, bankroll=200.0)
    orden = plan.ordenes_ejecucion_partidos[0]

    assert orden.estrategia_seleccionada.linea_promocional == "Pago Anticipado (+2 goles)"
    assert "+ PA" in orden.boletos.boleto_2_ganancia.seleccion


def test_madlibs_no_alucina_puntos_si_favorito_esta_abajo():
    """Certifica que el fallback no afirme que el favorito tiene más puntos si está abajo."""
    datos_partido = {
        "fav_name": "Atlético San Luis",
        "und_name": "Necaxa",
        "fav_pts": 6,
        "und_pts": 8,
        "fav_puesto": 16,
        "und_puesto": 13,
        "codigo_estrategia": "QBE-00",
        "prob_fav": 0.359,
        "inversion_total": 0.0,
        "ganancia_neta": 0.0
    }

    tesis = generar_tesis_madlibs_fallback(datos_partido)
    # NO debe afirmar que Atlético San Luis llega consolidando una efectividad superior
    assert "Atlético San Luis llega consolidando una efectividad superior" not in tesis
    # Debe reflejar que Necaxa supera en puntos a San Luis
    assert "Necaxa" in tesis
