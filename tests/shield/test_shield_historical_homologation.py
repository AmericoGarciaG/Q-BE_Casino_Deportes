# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [ARCH-1.4.39] Homologación Histórica y Principio de Paridad Factual
Base de Gobierno: docs/ARCH.md [ARCH-1.4.39] / docs/GOVERNANCE.md [GOVERNANCE-01]
Autoridad: Américo García Guerrero (Director Humano)
Régimen: [DIRGEN-STRICT] — Inmutable, Cero Mocks.
"""

import pytest
from src.core.sovereign_pipeline import generar_distribucion_soberana
from src.storage.gateway import PersistenceGateway
from src.storage.models import FixtureSnapshot


def test_invarianza_rectificacion_puebla_vs_toluca_j7():
    """
    [INVARIANZA 1 - RECTIFICACIÓN FACTUAL HOMÓLOGA]:
    En la Jornada 7, Toluca era el líder del torneo con xG ofensivo masivo (2.10 xG),
    mientras Puebla concedía > 1.80 xG en casa.
    El modelo homólogo NO puede calificar a Puebla como favorito (47.3% vs 31.4%).
    Debe asignar obligatoriamente el favoritismo a Toluca: P'_visita >= 50.0% y P'_local <= 30.0%.
    """
    # Perfil homólogo de la Jornada 7 con métricas Opta y Splits reales al corte J6
    raw_data_homologo_j7 = {
        "home_team_stats": {"pj": 6, "gf": 6, "gc": 9, "xg": 5.4, "pts": 5},     # Puebla General
        "away_team_stats": {"pj": 6, "gf": 15, "gc": 6, "xg": 13.8, "pts": 14},   # Toluca General
        "home_split_stats": {"pj": 3, "gf": 3, "gc": 5, "xg": 2.8},              # Puebla en Casa
        "away_split_stats": {"pj": 3, "gf": 7, "gc": 3, "xg": 6.9},              # Toluca de Visita
        "home_team_slug": "club-puebla",
        "away_team_slug": "deportivo-toluca",
        "h2h_matches": [
            {"goles_local": 1, "goles_visita": 2, "dias_antiguedad": 180},
            {"goles_local": 1, "goles_visita": 1, "dias_antiguedad": 360},
            {"goles_local": 0, "goles_visita": 2, "dias_antiguedad": 540},
        ]
    }
    
    dist_out = generar_distribucion_soberana(
        match_id="LIGAMX-J07-PUE-TOL",
        raw_match_data=raw_data_homologo_j7,
        mu_liga=2.65,
        gamma_home_base=0.15
    )
    
    assert dist_out.p_visitante >= 0.5000, (
        f"🚨 FALLO DE HOMOLOGACIÓN: Toluca debe ser favorito sólido (P'_visita >= 0.50). "
        f"Obtenido: {dist_out.p_visitante:.4f}"
    )
    assert dist_out.p_local <= 0.3000, (
        f"🚨 SESGO CIEGO PERSISTENTE: Puebla no puede tener P'_local={dist_out.p_local:.4f}. Debe ser <= 0.30."
    )


def test_invarianza_boveda_j7_actual_contiene_datos_degradados_que_deben_fallar():
    """
    [INVARIANZA 2 - CERTIFICACIÓN DEL ESTADO ROJO EN LA BASE VIVA]:
    Comprueba que en la base de datos viva actual, el fixture de Puebla vs Toluca
    en la Jornada 7 portaba la distribución degradada errónea (P_local = 47.3%).
    Este test DEBE FALLAR para exigir la re-homologación fáctica de la bóveda.
    """
    gw = PersistenceGateway()
    with gw.read_session() as session:
        snap_j7 = session.query(FixtureSnapshot).filter(
            FixtureSnapshot.league_id == 1,
            FixtureSnapshot.matchday == 7
        ).first()
        
        assert snap_j7 is not None, "Snapshot J7 debe existir en la bóveda"
        
        # Buscar el partido Puebla vs Toluca
        puebla_toluca = next(
            (fx for fx in snap_j7.matches_json if "Puebla" in fx.get("local", "") and "Toluca" in fx.get("visitante", "")),
            None
        )
        assert puebla_toluca is not None, "Puebla vs Toluca debe existir en J7"
        
        p_visita_guardada = float(puebla_toluca.get("p_visitante", 0.0))
        
        # En la base actual, p_visitante es 0.3140 (Toluca underdog).
        # Exigimos que la base ya esté homologada con p_visitante >= 0.50.
        # ESTE ASSERT DEBE FALLAR EN ROJO (assert 0.3140 >= 0.50).
        assert p_visita_guardada >= 0.5000, (
            f"🚨 BÓVEDA DEGRADADA: El snapshot de la J7 en SQLite tiene a Toluca con "
            f"p_visitante={p_visita_guardada:.4f} (< 0.50). Requiere re-homologación con Opta xG."
        )
