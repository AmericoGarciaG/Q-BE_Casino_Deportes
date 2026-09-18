# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: Verificación de Sueño Profundo Familia R y Purga de Snapshots
Doctrina: Kybern Framework v8.0 / v12.0 [GOV-TEST-01 a 07]
"""

import pytest
from src.core.evaluator import evaluar_estrategia_individual


def test_familia_r_en_sueno_profundo():
    """Valida que QBE-R1 y QBE-R2 estén terminantemente desactivadas."""
    metricas_ejemplo = {
        "prob_fav": 0.30, "prob_emp": 0.35, "prob_und": 0.35,
        "edge_fav": -0.10, "edge_emp": 0.05, "edge_und": 0.10,
        "theta_req_und": 0.25, "fav_pts_pj": 0.8, "fav_gc_promedio": 1.9,
        "und_pts_pj": 1.2, "und_gc_promedio": 1.1, "peso_h2h": 0.0,
        "pago_anticipado": True
    }

    res_r1 = evaluar_estrategia_individual("QBE-R1", metricas_ejemplo)
    assert res_r1["viable"] is False
    assert "SUEÑO PROFUNDO" in res_r1["motivo"].upper()

    res_r2 = evaluar_estrategia_individual("QBE-R2", metricas_ejemplo)
    assert res_r2["viable"] is False
    assert "SUEÑO PROFUNDO" in res_r2["motivo"].upper()
