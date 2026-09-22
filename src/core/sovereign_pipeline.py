# -*- coding: utf-8 -*-
"""
🏆 Q-BE SOVEREIGN ENGINE — REGISTRO DE VARIABLES, SUFICIENCIA S(I) Y ORQUESTADOR SOBERANO
[VAULT-CORE-005] Generador Soberano Universal de la Distribución del Partido y Traza Forense.
Base de Gobierno: Kybern Framework v12.0 [ARCH-1.3.4] / Tratado Volumen I (Sección 2.13.1, 4.5, 5.20)
"""

import math
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

from src.core.intensity_canonical_loglink import estimar_intensidades_loglineal
from src.core.distribution_dixon_coles import calcular_matriz_dixon_coles, colapsar_matriz_a_simplex
from src.core.andre_early_payout import calcular_probabilidad_pago_anticipado


class StochasticAuditTrace(BaseModel):
    """Traza forense inmutable de la generación de la distribución soberana."""
    match_id: str
    suficiencia_S_I: int = Field(description="1 si satisface datos mínimos, 0 si entra en ignorancia")
    factores_entrada: Dict[str, float]
    intensidades: Dict[str, float]
    distribucion_simplex: Dict[str, float]
    phi_lead2: Dict[str, float]
    matriz_resumen: Dict[str, float]


class SovereignDistributionOutput(BaseModel):
    """Contrato formal de salida de la Capa Probabilística Soberana."""
    match_id: str
    p_local: float
    p_empate: float
    p_visitante: float
    lambda_home: float
    lambda_away: float
    phi_lead2_home: float
    phi_lead2_away: float
    es_operable: bool
    audit_trace: StochasticAuditTrace


def evaluar_suficiencia_informativa(raw_match_data: Dict[str, Any]) -> bool:
    """
    [Sección 2.13.1] Evalúa la función indicadora S(I_i) in {0, 1}.
    Requiere al menos 3 partidos jugados por equipo y datos básicos de goles.
    """
    h_data = raw_match_data.get("home_team_stats", {})
    a_data = raw_match_data.get("away_team_stats", {})

    pj_h = int(h_data.get("pj", 0) or 0)
    pj_a = int(a_data.get("pj", 0) or 0)

    if pj_h < 3 or pj_a < 3:
        return False
    return True


def derivar_factores_estructurales(raw_match_data: Dict[str, Any], mu_liga: float = 2.65) -> Tuple[float, float, float, float]:
    """
    [Sección 4.5 y 4.6] Convierte métricas de Nivel 1 en factores log-diferenciales centrados en media cero:
    Retorna: (A_home, D_away, A_away, D_home)
    """
    h = raw_match_data.get("home_team_stats", {})
    a = raw_match_data.get("away_team_stats", {})

    pj_h = max(1, int(h.get("pj", 8)))
    pj_a = max(1, int(a.get("pj", 8)))

    mu_base_equipo = max(0.5, mu_liga / 2.0)

    # 1. Ataque Local (Tasa por partido)
    gf_h_per_game = float(h.get("gf", 10)) / pj_h
    xg_total_h = float(h.get("xg", 0.0) or 0.0)
    xg_h_per_game = (xg_total_h / pj_h) if xg_total_h > 5.0 else (xg_total_h or gf_h_per_game)
    att_h_rate = (0.65 * xg_h_per_game) + (0.35 * gf_h_per_game)
    A_home = math.log(max(0.2, att_h_rate) / mu_base_equipo)

    # 2. Defensa Visita (Tasa por partido)
    gc_a_per_game = float(a.get("gc", 12)) / pj_a
    xga_total_a = float(a.get("xga", 0.0) or 0.0)
    xga_a_per_game = (xga_total_a / pj_a) if xga_total_a > 5.0 else (xga_total_a or gc_a_per_game)
    def_a_rate = (0.65 * xga_a_per_game) + (0.35 * gc_a_per_game)
    D_away = -math.log(max(0.2, def_a_rate) / mu_base_equipo)

    # 3. Ataque Visita
    gf_a_per_game = float(a.get("gf", 7)) / pj_a
    xg_total_a = float(a.get("xg", 0.0) or 0.0)
    xg_a_per_game = (xg_total_a / pj_a) if xg_total_a > 5.0 else (xg_total_a or gf_a_per_game)
    att_a_rate = (0.65 * xg_a_per_game) + (0.35 * gf_a_per_game)
    A_away = math.log(max(0.2, att_a_rate) / mu_base_equipo)

    # 4. Defensa Local
    gc_h_per_game = float(h.get("gc", 10)) / pj_h
    xga_total_h = float(h.get("xga", 0.0) or 0.0)
    xga_h_per_game = (xga_total_h / pj_h) if xga_total_h > 5.0 else (xga_total_h or gc_h_per_game)
    def_h_rate = (0.65 * xga_h_per_game) + (0.35 * gc_h_per_game)
    D_home = -math.log(max(0.2, def_h_rate) / mu_base_equipo)

    return round(A_home, 4), round(D_away, 4), round(A_away, 4), round(D_home, 4)


def generar_distribucion_soberana(
    match_id: str,
    raw_match_data: Dict[str, Any],
    mu_liga: float = 2.65,
    gamma_home_base: float = 0.15,
    delta_alt_metros: float = 0.0,
    delta_descanso_dias: float = 0.0,
    q_mod_h: float = 1.0,
    q_mod_a: float = 1.0,
    rho: float = -0.05
) -> SovereignDistributionOutput:
    """
    [TRATADO VOLUMEN I] Generador Soberano Universal de la Distribución del Partido.
    Pipeline completo: Datos -> S(I) -> Factores -> Intensidades acotadas -> Dixon-Coles 2D -> André -> Simplex.
    """
    # 1. Comprobación de Suficiencia Fáctica S(I_i)
    if not evaluar_suficiencia_informativa(raw_match_data):
        trace_insuf = StochasticAuditTrace(
            match_id=match_id,
            suficiencia_S_I=0,
            factores_entrada={},
            intensidades={"lambda_h": 1.325, "lambda_a": 1.325},
            distribucion_simplex={"p_1": 0.3333, "p_X": 0.3333, "p_2": 0.3334},
            phi_lead2={"phi_h": 0.0, "phi_a": 0.0},
            matriz_resumen={}
        )
        return SovereignDistributionOutput(
            match_id=match_id,
            p_local=0.3333, p_empate=0.3333, p_visitante=0.3334,
            lambda_home=1.325, lambda_away=1.325,
            phi_lead2_home=0.0, phi_lead2_away=0.0,
            es_operable=False,
            audit_trace=trace_insuf
        )

    # 2. Derivación de Factores Estructurales
    A_h, D_a, A_a, D_h = derivar_factores_estructurales(raw_match_data, mu_liga)

    # 3. Estimación de Intensidades con Ligadura de alpha y Damping tanh
    lh, la = estimar_intensidades_loglineal(
        A_home=A_h, D_away=D_a,
        A_away=A_a, D_home=D_h,
        mu_liga=mu_liga, gamma_home_base=gamma_home_base,
        delta_alt_metros=delta_alt_metros,
        delta_descanso_dias=delta_descanso_dias,
        q_mod_h=q_mod_h, q_mod_a=q_mod_a
    )

    # 4. Construcción de la Matriz Conjunta Dixon-Coles 2D
    matriz_2d = calcular_matriz_dixon_coles(lambda_h=lh, lambda_a=la, rho=rho, k_max=6)

    # 5. Colapso Geométrico al Símplex Delta^2
    p1, pX, p2 = colapsar_matriz_a_simplex(matriz_2d)

    # 6. Evaluación de la Cláusula de Pago Anticipado (Operador de André en O(1))
    phi_h = calcular_probabilidad_pago_anticipado(matriz_2d, es_local=True)
    phi_a = calcular_probabilidad_pago_anticipado(matriz_2d, es_local=False)

    # 7. Consolidación de Traza Forense
    trace = StochasticAuditTrace(
        match_id=match_id,
        suficiencia_S_I=1,
        factores_entrada={"A_home": A_h, "D_away": D_a, "A_away": A_a, "D_home": D_h},
        intensidades={"lambda_home": lh, "lambda_away": la, "ratio": round(lh / la, 2)},
        distribucion_simplex={"p_1": p1, "p_X": pX, "p_2": p2},
        phi_lead2={"phi_home": phi_h, "phi_away": phi_a},
        matriz_resumen={"0_0": round(matriz_2d[0][0], 4), "1_0": round(matriz_2d[1][0], 4), "1_1": round(matriz_2d[1][1], 4)}
    )

    return SovereignDistributionOutput(
        match_id=match_id,
        p_local=p1, p_empate=pX, p_visitante=p2,
        lambda_home=lh, lambda_away=la,
        phi_lead2_home=phi_h, phi_lead2_away=phi_a,
        es_operable=True,
        audit_trace=trace
    )
