# -*- coding: utf-8 -*-
"""
🏆 Q-BE SOVEREIGN FINANCIAL ENGINE — CONTRATOS MATEMÁTICOS DE PORTAFOLIO Y 9 ESTRATEGIAS
[ARCH-1.4.9] Biblioteca Funcional Pura de Asignación, Coberturas V=0, Kelly y Triaje Canónico.
[VAULT-CORE-070-TRIAJE], [VAULT-CORE-070-DUTCHING], [VAULT-CORE-070-RANKING],
[VAULT-CORE-070-KELLY], [VAULT-CORE-071-PISO]
Régimen: [DIRGEN-STRICT]
Axioma: Cero dependencias de base de datos. Cero I/O. Cero números mágicos.
"""

from typing import List, Dict, Tuple, Optional, Any


def calcular_alpha_edge(p: float, o: float) -> float:
    """[LN-QBE-007-C] Retorno neto esperado por unidad de capital (Edge)."""
    if p <= 0.0 or o <= 1.0:
        return -1.0
    return round(p * o - 1.0, 4)


def calcular_umbral_theta_estrella(o_fav: float) -> float:
    """[LN-QBE-050] Umbral de indiferencia theta* para cobertura viable en tablas."""
    if o_fav <= 1.0:
        return 999.0
    return round(o_fav / (o_fav - 1.0), 4)


def calcular_dutching_v0(b_total: float, o_fav: float, o_emp: float) -> Tuple[float, float, float, float]:
    """[LN-QBE-070] Resuelve importes y ROI garantizando V=0 en empate."""
    if o_emp <= 1.0 or o_fav <= 1.0 or b_total <= 0.0:
        return (0.0, 0.0, 0.0, 0.0)
    b_seg = round(b_total / o_emp, 2)
    b_prio = round(b_total - b_seg, 2)
    ganancia_neta = round((b_prio * o_fav) - b_total, 2)
    roi_pct = round((ganancia_neta / b_total) * 100.0, 2)
    return (b_prio, b_seg, ganancia_neta, roi_pct)


def escalar_a_piso_ventanilla(b_total: float, o_emp: float, piso_min: float = 2.00) -> Tuple[float, float, float]:
    """[LN-QBE-071] Reescalado proporcional si el seguro cae por debajo de $2.00 MXN preservando V=0."""
    if o_emp <= 1.0 or b_total <= 0.0:
        return (0.0, 0.0, 0.0)
    b_seg_teorico = b_total / o_emp
    if b_seg_teorico < piso_min:
        b_seg = float(piso_min)
        b_total_reescalado = round(b_seg * o_emp, 2)
        b_prio = round(b_total_reescalado - b_seg, 2)
        return (b_prio, b_seg, b_total_reescalado)

    b_seg = round(b_seg_teorico, 2)
    b_prio = round(b_total - b_seg, 2)
    return (b_prio, b_seg, round(b_total, 2))


def calcular_ganancia_cobertura_v0(
    ganancia_directa: float,
    inversion: float,
    p_draw: float
) -> float:
    """
    [LN-QBE-073-B] Prima Canónica de la Transmutación D→H (erradicación del factor mágico 0.70).

    Derivación exacta a partir de la identidad del Dutching V=0 a cuotas soberanas justas:
      - La estructura directa revela la cuota implícita favorable: O_fav = 1 + g/B.
      - A cuotas justas, el seguro del empate absorbe su propia masa de probabilidad:
        b_seguro = B · p_draw  ⟹  b_primario = B · (1 − p_draw).
      - Ganancia neta de la estructura cubierta (V=0):
        g_cob = b_primario · O_fav − B = g · (1 − p_draw) − B · p_draw.

    Cero constantes empíricas: la prima emerge de la masa de probabilidad transferida al empate.
    """
    g = float(ganancia_directa or 0.0)
    b = float(inversion or 0.0)
    p_x = float(p_draw or 0.0)
    if b <= 0.0:
        return 0.0
    p_x = min(1.0, max(0.0, p_x))
    o_fav_implicita = 1.0 + (g / b)
    b_seguro = b * p_x
    b_primario = b - b_seguro
    return round((g * (1.0 - p_x)) - (b * p_x), 2)


def triaje_determinista_9_estrategias(payload: dict, cuotas: dict) -> dict:
    """[LN-QBE-060-B] Clasificación en cascada pura de las 9 estrategias."""
    # 1. Cuarentena
    if not payload.get("es_operable", True) or payload.get("delta_epist", 0.0) > 0.12:
        return {"codigo": "QBE-00", "nombre": "Cuarentena Fiduciaria", "alpha": 0.0, "pa": False}

    p1, pX, p2 = payload["p_local"], payload["p_empate"], payload["p_visitante"]
    oL, oX, oV = cuotas.get("L", 0.0), cuotas.get("E", 0.0), cuotas.get("V", 0.0)
    delta_epist = payload.get("delta_epist", 0.0)
    pa = bool(cuotas.get("pa", False) or cuotas.get("pago_anticipado", False))

    aL = p1 * oL - 1.0 if oL > 1.0 else -1.0
    aV = p2 * oV - 1.0 if oV > 1.0 else -1.0

    # 2. Directas Régimen I
    if p1 >= 0.65 and delta_epist <= 0.04 and aL > 0.05:
        return {"codigo": "QBE-D1", "nombre": "Directa Local", "alpha": aL, "pa": pa}
    if p2 >= 0.65 and delta_epist <= 0.04 and aV > 0.05:
        return {"codigo": "QBE-D2", "nombre": "Directa Visita", "alpha": aV, "pa": pa}

    # 3. Underdogs Familia R
    if p1 >= 0.20 and oL >= 3.50 and aL >= 0.20 and delta_epist <= 0.05:
        return {"codigo": "QBE-R1", "nombre": "Reversa Local Underdog", "alpha": aL, "pa": pa}
    if p2 >= 0.20 and oV >= 3.50 and aV >= 0.20 and delta_epist <= 0.05:
        return {"codigo": "QBE-R2", "nombre": "Reversa Visita Underdog", "alpha": aV, "pa": pa}

    # 4. Híbridas Dutching V=0
    theta_1 = oL / (oL - 1.0) if oL > 1.0 else 99.0
    theta_2 = oV / (oV - 1.0) if oV > 1.0 else 99.0
    if 0.40 <= p1 < 0.65 and oX > theta_1 and aL > 0:
        return {"codigo": "QBE-H1", "nombre": "Híbrida Local + Empate V=0", "alpha": aL, "pa": pa}
    if 0.40 <= p2 < 0.65 and oX > theta_2 and aV > 0:
        return {"codigo": "QBE-H2", "nombre": "Híbrida Visita + Empate V=0", "alpha": aV, "pa": pa}

    # 5. DNB
    p_dnb_l = p1 / (p1 + p2) if (p1 + p2) > 0 else 0.0
    o_dnb_l = cuotas.get("DNB_L", oL * 0.75)
    if (p_dnb_l * o_dnb_l - 1.0) > 0.05:
        return {"codigo": "QBE-C1", "nombre": "Cobertura DNB", "alpha": (p_dnb_l * o_dnb_l - 1.0), "pa": False}

    # 6. Totales
    p_under = payload.get("p_under_25", 0.0)
    o_under = cuotas.get("Under_25", 0.0)
    if o_under > 1.0 and (p_under * o_under - 1.0) > 0.06:
        return {"codigo": "QBE-C2", "nombre": "Cobertura Derivada Totales", "alpha": (p_under * o_under - 1.0), "pa": False}

    # 7. Descarte
    return {"codigo": "QBE-00", "nombre": "Cuarentena / Sin Valor", "alpha": 0.0, "pa": False}


def calcular_ranking_friccion(partidos: List[dict]) -> List[dict]:
    """[LN-QBE-073-B] Ordenamiento por Calidad Distributiva descendente."""
    for p in partidos:
        alpha = max(0.0, float(p.get("alpha", 0.0)))
        delta_epist = max(0.0, float(p.get("delta_epist", 0.0)))
        psi = max(0.0, 1.0 - (delta_epist / 0.12) ** 2) if delta_epist <= 0.12 else 0.0
        score = (alpha / (delta_epist + 0.01)) * psi if p.get("codigo") != "QBE-00" else 0.0
        p["score_friccion"] = round(score, 4)
        p["psi_epist"] = round(psi, 4)
    return sorted(partidos, key=lambda x: x["score_friccion"], reverse=True)


def calcular_kelly_atenuado(p: float, o: float, delta_epist: float, gamma_kelly: float = 0.25) -> float:
    """[LN-QBE-070-B] Kelly Fraccional modulado por atenuación cuadrática de incertidumbre."""
    alpha = calcular_alpha_edge(p, o)
    if alpha <= 0.0 or o <= 1.0:
        return 0.0
    f_puro = alpha / (o - 1.0)
    psi = max(0.0, 1.0 - (delta_epist / 0.12) ** 2) if delta_epist <= 0.12 else 0.0
    f_adj = gamma_kelly * f_puro * psi
    return round(max(0.0, min(0.08, f_adj)), 4)


def aplicar_hard_caps_constitucionales(inversiones: List[float], bankroll: float) -> List[float]:
    """[LN-QBE-070-B] Aplica techo individual (8.0%) y prorrateo global de jornada (25.0%)."""
    if bankroll <= 0.0 or not inversiones:
        return [0.0] * len(inversiones)
    cap_indiv = bankroll * 0.0800
    cap_global = bankroll * 0.2500

    # 1. Cap individual
    acotadas = [min(max(0.0, float(inv)), cap_indiv) for inv in inversiones]
    total_inv = sum(acotadas)

    # 2. Cap global prorrateado
    if total_inv > cap_global and total_inv > 0.0:
        escala = cap_global / total_inv
        return [round(inv * escala, 2) for inv in acotadas]
    return [round(inv, 2) for inv in acotadas]
