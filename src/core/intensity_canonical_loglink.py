# -*- coding: utf-8 -*-
"""
🏆 Q-BE SOVEREIGN ENGINE — INTENSIDADES LOG-LINEALES Y LIGADURA DE ALFA
[VAULT-CORE-001] Ecuación Log-Lineal Canónica, Ligadura de alpha y Damping tanh.
Base de Gobierno: Kybern Framework v12.0 [ARCH-1.3.4] / Tratado Volumen I (Sección 4.9 y 4.12)
"""

import math
from typing import Tuple, Optional


def calcular_alpha_ligadura(mu_liga: float = 2.65, gamma_home: float = 0.15) -> float:
    """
    [Sección 4.9.1] Ecuación de Ligadura Estructural de Q-BE:
    alpha = ln(mu_liga) - ln(1.0 + exp(gamma_home))
    Garantiza analíticamente la conservación de masa de goles de la competición.
    """
    gamma_val = float(gamma_home) if gamma_home is not None else 0.15
    mu_val = float(mu_liga) if mu_liga is not None else 2.65
    return math.log(mu_val) - math.log(1.0 + math.exp(gamma_val))


def aplicar_damping_hiperbolico(factor_crudo: float, sigma_liga: float = 1.0, kappa_mult: float = 2.5) -> float:
    """
    [Sección 4.12] Compresión Hiperbólica Simétrica:
    A = kappa * tanh(A_crudo / kappa), donde kappa = 2.5 * sigma_liga.
    Preserva strictly la media cero E[A] = 0 y acota divergencias asintóticas.
    """
    kappa = float(kappa_mult * sigma_liga)
    if kappa <= 0.0:
        return 0.0
    return kappa * math.tanh(float(factor_crudo) / kappa)


def estimar_intensidades_loglineal(
    A_home: float,
    D_away: float,
    A_away: float,
    D_home: float,
    mu_liga: float = 2.65,
    gamma_home_base: float = 0.15,
    delta_alt_metros: float = 0.0,
    delta_descanso_dias: float = 0.0,
    q_mod_h: float = 1.0,
    q_mod_a: float = 1.0,
    sigma_A: float = 0.25,
    sigma_D: float = 0.25
) -> Tuple[float, float]:
    """
    [Sección 4.9] Arquitectura Canónica Log-Lineal:
    ln(lambda_H) = alpha + gamma_home + A_H - D_A + C_H
    ln(lambda_A) = alpha + A_A - D_H + C_A
    """
    # 1. Ligadura estructural
    alpha = calcular_alpha_ligadura(mu_liga, gamma_home_base)

    # 2. Damping hiperbólico aguas arriba en factores
    A_h_damped = aplicar_damping_hiperbolico(A_home, sigma_A)
    D_a_damped = aplicar_damping_hiperbolico(D_away, sigma_D)
    A_a_damped = aplicar_damping_hiperbolico(A_away, sigma_A)
    D_h_damped = aplicar_damping_hiperbolico(D_home, sigma_D)

    # 3. Operador vectorial de localía (Sección 4.7)
    delta_alt_term = 0.03 * max(0.0, delta_alt_metros / 1000.0)
    delta_rest_term = 0.02 * max(-3.0, min(3.0, delta_descanso_dias))
    gamma_contextual = gamma_home_base + delta_alt_term + delta_rest_term

    # 4. Factores contextuales en espacio logarítmico
    q_h_clamped = max(0.90, min(1.05, float(q_mod_h)))
    q_a_clamped = max(0.90, min(1.05, float(q_mod_a)))
    C_h = math.log(q_h_clamped)
    C_a = math.log(q_a_clamped)

    # 5. Formulación log-lineal canónica
    eta_h = alpha + gamma_contextual + A_h_damped - D_a_damped + C_h
    eta_a = alpha + A_a_damped - D_h_damped + C_a

    # 6. Transformación exponencial e Invariante I6 (Positividad estricta acotada)
    lambda_h = max(0.15, min(4.50, math.exp(eta_h)))
    lambda_a = max(0.15, min(4.50, math.exp(eta_a)))

    return round(lambda_h, 4), round(lambda_a, 4)
