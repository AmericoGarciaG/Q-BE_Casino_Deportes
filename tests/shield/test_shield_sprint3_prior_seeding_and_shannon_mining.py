# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — SPRINT 3: PRIOR SEEDING (APERTURA 2025) & SHANNON MINING SUITE
Juez Inmutable: [LN-QBE-128] / [LN-QBE-129] / [ARCH-1.4.69] / [ARCH-1.4.70]
Base de Gobierno: Kybern Framework v13.5 [GOV-TEST-01]
"""

import os
import json
import pytest
from scripts.ingesta.sembrar_prior_apertura2025 import cargar_o_generar_prior_apertura2025
from scripts.investigacion.mineria_factores_shannon import ejecutar_mineria_shannon

def test_invarianza_artefacto_prior_apertura2025_completo():
    """[INVARIANZA 1 - PRIOR SEED]: El artefacto del torneo previo debe contener los 17 clubes de Apertura 2025."""
    ruta_prior = os.path.join("data", "cache_prior_apertura2025_liga_mx.json")
    prior = cargar_o_generar_prior_apertura2025(ruta_salida=ruta_prior)
    
    assert prior is not None
    assert os.path.exists(ruta_prior), f"Falta el archivo {ruta_prior}"
    assert "equipos" in prior
    equipos = prior["equipos"]
    
    assert len(equipos) >= 17, f"Se esperaban al menos 17 clubes, encontrados: {len(equipos)}"
    
    for slug, stats in equipos.items():
        assert "xg_per_match" in stats and stats["xg_per_match"] > 0.0
        assert "xga_per_match" in stats and stats["xga_per_match"] > 0.0
        assert "possession_pct" in stats and stats["possession_pct"] > 0.0

def test_invarianza_jornada_1_alcanza_suficiencia_factica():
    """[INVARIANZA 2 - CERO COLD START]: Con el prior sembrado, un fixture de J1 sin Atlante debe evaluar S(I) == 1."""
    from scripts.ingesta.homologar_temporada_optah2h import _resolver_insumos_con_prior
    
    stats_j1 = _resolver_insumos_con_prior(
        team_slug="club-america",
        stats_actuales={"pj": 0, "gf": 0, "gc": 0},
        torneo_actual_pj=0
    )
    
    assert stats_j1["suficiencia_S_I"] == 1, "J1 debe alcanzar suficiencia fáctica mediante el prior sembrado"
    assert stats_j1["xg"] > 0.0
    assert stats_j1["xga"] > 0.0

def test_invarianza_mineria_shannon_procesa_matriz_sin_nans():
    """[INVARIANZA 3 - SHANNON MINING]: La minería sobre research_feature_matrix debe ranquear variables."""
    ruta_dataset = os.path.join("data", "output", "research_feature_matrix.csv")
    res = ejecutar_mineria_shannon(ruta_dataset=ruta_dataset)
    
    assert res is not None
    assert res["status"] == "EXITO"
    assert "ranking_informacion_mutua" in res
    ranking = res["ranking_informacion_mutua"]
    
    assert len(ranking) >= 15, "Deben evaluarse al menos 15 características predictivas"
    im_ant = float("inf")
    for item in ranking:
        im_act = item["informacion_mutua_bits"]
        assert im_act <= im_ant + 1e-6, "Ranking de Shannon debe ser monótono descendente"
        im_ant = im_act

def test_invarianza_arbol_esparso_induce_reglas_veto():
    """[INVARIANZA 4 - REGLAS ESPARSAS]: El árbol esparso debe emitir al menos 2 reglas de veto interpretables."""
    ruta_dataset = os.path.join("data", "output", "research_feature_matrix.csv")
    res = ejecutar_mineria_shannon(ruta_dataset=ruta_dataset)
    
    assert "reglas_veto_inducidas" in res
    reglas = res["reglas_veto_inducidas"]
    assert len(reglas) >= 2, "Deben inducirse al menos 2 reglas de veto transparentes"
    for r in reglas:
        assert "condicion_booleana" in r
        assert "tasa_ruptura_pct" in r
        assert r["tasa_ruptura_pct"] >= 50.0
