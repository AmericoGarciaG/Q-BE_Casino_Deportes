# Q-BE Casino Deportes — Strategy Evaluator Engine (src/core/evaluator.py)
"""
Evaluador Determinista de las 9 Estrategias del Catálogo Maestro Q-BE.
[LN-QBE-060] [BIZ-LOGIC] [ALGO-PROTECTED]
Evalúa el cumplimiento booleano estricto sin umbrales arbitrarios, aplicando
candados de jerarquía y el Triple Candado Fáctico para la Familia R.
"""

from typing import Dict, Any
from src.core.catalog import STRATEGY_CATALOG


class StrategyEvaluatorEngine:
    @classmethod
    def evaluate_all(
        cls,
        p_fav: float,
        p_emp: float,
        p_und: float,
        o_fav: float,
        o_emp: float,
        o_und: float,
        theta_fav_h1: float,
        theta_emp_h2: float,
        theta_emp_pa_h2_plus: float,
        theta_und_r1: float,
        momio_sintetico_x2: float,
        phi_lead2: float,
        psi_ruina: float,
        d_mkt: float,
        pago_anticipado: bool,
        pts_pj_fav: float = 1.0,
        gc_10p_fav: float = 1.5,
        q_mod_fav: float = 0.90,
        h2h_x2_prob: float = 0.50
    ) -> Dict[str, Dict[str, Any]]:
        results = {}

        edge_fav = p_fav - (1.0 / o_fav)
        edge_emp = p_emp - (1.0 / o_emp)
        edge_und = p_und - (1.0 / o_und)

        # 1. QBE-D1 (Favorito Directo Puro) — Sin umbral rígido artificial de 70%
        breakeven_directo = 1.0 / o_fav
        es_mas_probable = bool((p_fav > p_emp) and (p_fav > p_und))
        d1_viable = bool(es_mas_probable and p_fav >= breakeven_directo and edge_fav > 0.0 and psi_ruina <= 0.10 and o_fav >= 1.25)
        d1_ev = float((p_fav * (o_fav - 1.0)) - ((1.0 - p_fav) * 1.0)) if d1_viable else 0.0
        results["QBE_D1"] = {
            "viable": d1_viable,
            "ev_neto_roi": d1_ev,
            "nombre_oficial": STRATEGY_CATALOG["QBE-D1"].nombre_oficial,
            "motivo_diagnostico": "Aprobado por alta convicción" if d1_viable else "No supera checklist D1 (favorito más probable, cuota por encima del breakeven, EV > 0 y momio >= 1.25)"
        }

        # 2. QBE-D1+ (Favorito Directo Potenciado) — Candado Jerárquico: Requiere D1 == True
        d1_plus_viable = bool(d1_viable and phi_lead2 >= 0.45 and pago_anticipado)
        d1_plus_ev = float((p_fav * (o_fav - 1.0)) - ((1.0 - p_fav) * 1.08)) if d1_plus_viable else 0.0
        results["QBE_D1_plus"] = {
            "viable": d1_plus_viable,
            "ev_neto_roi": d1_plus_ev,
            "nombre_oficial": STRATEGY_CATALOG["QBE-D1+"].nombre_oficial,
            "motivo_diagnostico": "Aprobado con bono de Pago Anticipado" if d1_plus_viable else "Requiere D1 viable y Phi_lead2 >= 45% con Pago Anticipado activo"
        }

        # 3. QBE-H1 (Favorito con Seguro en Empate)
        denom_h1 = (1.0 - 1.0 / o_emp) * o_fav - 1.0
        h1_viable = bool(p_fav >= theta_fav_h1 and edge_fav > 0.0 and psi_ruina <= 0.15 and d_mkt <= 1.25 and denom_h1 > 0.0)
        roi_neto_fav = denom_h1
        h1_ev = float(min(roi_neto_fav, (p_fav * roi_neto_fav) - psi_ruina)) if h1_viable else 0.0
        results["QBE_H1"] = {
            "viable": h1_viable,
            "ev_neto_roi": h1_ev,
            "nombre_oficial": STRATEGY_CATALOG["QBE-H1"].nombre_oficial,
            "motivo_diagnostico": "Aprobado con cobertura en empate" if h1_viable else "P_fav inferior a theta* o margen de cobertura no rentable"
        }

        # 4. QBE-H1+ (Favorito Potenciado con Seguro) — Candado Jerárquico: Requiere H1 == True
        h1_plus_viable = bool(h1_viable and phi_lead2 >= 0.38 and pago_anticipado)
        raw_h1_plus_ev = ((p_fav + phi_lead2 * p_emp) * roi_neto_fav) - psi_ruina
        h1_plus_ev = float(min(roi_neto_fav, raw_h1_plus_ev)) if h1_plus_viable else 0.0
        results["QBE_H1_plus"] = {
            "viable": h1_plus_viable,
            "ev_neto_roi": h1_plus_ev,
            "nombre_oficial": STRATEGY_CATALOG["QBE-H1+"].nombre_oficial,
            "motivo_diagnostico": "Aprobado con cobertura y Pago Anticipado" if h1_plus_viable else "Requiere H1 viable y Phi_lead2 >= 38% con Pago Anticipado activo"
        }

        # 5. QBE-H2 (Empate de Valor con Seguro Fav)
        denom_h2 = (1.0 - 1.0 / o_fav) * o_emp - 1.0
        h2_viable = bool(p_emp >= theta_emp_h2 and edge_emp > 0.0 and psi_ruina <= 0.15 and denom_h2 > 0.0)
        roi_neto_emp = denom_h2
        h2_ev = float((p_emp * roi_neto_emp) - psi_ruina) if h2_viable else 0.0
        results["QBE_H2"] = {
            "viable": h2_viable,
            "ev_neto_roi": h2_ev,
            "nombre_oficial": STRATEGY_CATALOG["QBE-H2"].nombre_oficial,
            "motivo_diagnostico": "Aprobado: valor en empate cubriendo favorito" if h2_viable else "P_emp inferior a theta* o cuota de favorito sin margen para cubrir"
        }

        # 6. QBE-H2+ (Freeroll Doble Impacto - Joya) — Candado Jerárquico: Requiere H2 == True
        h2_plus_viable = bool(h2_viable and p_emp >= theta_emp_pa_h2_plus and phi_lead2 >= 0.38 and psi_ruina <= 0.12 and pago_anticipado)
        if h2_plus_viable:
            h2_plus_ev = float(((phi_lead2 * p_emp) * (roi_neto_emp + 1.0)) + ((p_emp * (1.0 - phi_lead2)) * roi_neto_emp) - psi_ruina)
        else:
            h2_plus_ev = 0.0
        results["QBE_H2_plus"] = {
            "viable": h2_plus_viable,
            "ev_neto_roi": h2_plus_ev,
            "nombre_oficial": STRATEGY_CATALOG["QBE-H2+"].nombre_oficial,
            "motivo_diagnostico": "Aprobado: Joya de la Corona con Freeroll Topológico" if h2_plus_viable else "Requiere H2 viable, Psi <= 12% y Phi_lead2 >= 38%"
        }

        # --- TRIPLE CANDADO FÁCTICO FAMILIA R ---
        candado_1 = bool(p_fav <= 0.4800)
        senales_crisis = sum([
            bool(pts_pj_fav <= 1.40),
            bool(gc_10p_fav >= 1.30),
            bool(q_mod_fav <= 0.95)
        ])
        candado_2 = bool(senales_crisis >= 2)
        candado_3 = bool(h2h_x2_prob >= 0.4000)
        triple_candado_superado = bool(candado_1 and candado_2 and candado_3)

        motivo_falla_candado = ""
        if not candado_1:
            motivo_falla_candado = f"Rechazado por Candado 1: P_fav ({p_fav*100:.2f}%) > 48.0% (Techo de dominancia)"
        elif not candado_2:
            motivo_falla_candado = f"Rechazado por Candado 2: Favorito sólido ({senales_crisis}/3 señales de crisis, requiere >= 2)"
        elif not candado_3:
            motivo_falla_candado = f"Rechazado por Candado 3: Inmunidad H2H insuficiente (P_H2H(X2) = {h2h_x2_prob*100:.1f}% < 40.0%)"

        # 7. QBE-R1 (Asalto al No-Favorito con Seguro en Empate)
        denom_r1 = (1.0 - 1.0 / o_emp) * o_und - 1.0
        roi_neto_und = denom_r1
        r1_ev_calc = (p_und * roi_neto_und) - p_fav
        r1_math_ok = bool(p_und >= theta_und_r1 and edge_und > 0.0 and o_und >= 3.50 and denom_r1 > 0.0 and r1_ev_calc > 0.0)
        r1_viable = bool(triple_candado_superado and r1_math_ok)
        r1_ev = float(r1_ev_calc) if r1_viable else 0.0

        if r1_viable:
            r1_motivo = "Aprobado: Asalto a cuota de Underdog con seguro en empate (Triple Candado superado)"
        elif not triple_candado_superado:
            r1_motivo = f"QBE-R1 {motivo_falla_candado}"
        else:
            r1_motivo = "No supera checklist matemático R1 (P_und >= theta*, Edge > 0, O_und >= 3.50, EV > 0)"

        results["QBE_R1"] = {
            "viable": r1_viable,
            "ev_neto_roi": r1_ev,
            "nombre_oficial": STRATEGY_CATALOG["QBE-R1"].nombre_oficial,
            "motivo_diagnostico": r1_motivo
        }

        # 8. QBE-R2 (Doble Oportunidad Sintética X2)
        p_x2 = p_und + p_emp
        r2_ev_calc = (p_x2 * (momio_sintetico_x2 - 1.0)) - p_fav
        r2_math_ok = bool(p_x2 >= 0.4800 and p_x2 >= (1.0 / momio_sintetico_x2) and momio_sintetico_x2 >= 1.60 and r2_ev_calc > 0.0)
        r2_viable = bool(triple_candado_superado and r2_math_ok)
        r2_ev = float(r2_ev_calc) if r2_viable else 0.0

        if r2_viable:
            r2_motivo = "Aprobado: Doble Oportunidad sintética rentable (Triple Candado superado)"
        elif not triple_candado_superado:
            r2_motivo = f"QBE-R2 {motivo_falla_candado}"
        else:
            r2_motivo = "No supera checklist matemático R2 (P(X2) >= 48%, Cuota Sintética >= 1.60, Edge X2 > 0, EV > 0)"

        results["QBE_R2"] = {
            "viable": r2_viable,
            "ev_neto_roi": r2_ev,
            "nombre_oficial": STRATEGY_CATALOG["QBE-R2"].nombre_oficial,
            "motivo_diagnostico": r2_motivo
        }

        # 9. QBE-00 (Veto Preventivo de Capital)
        ninguna_viable = not any(res["viable"] for k, res in results.items() if k != "QBE_00")
        results["QBE_00"] = {
            "viable": ninguna_viable,
            "ev_neto_roi": 0.0,
            "nombre_oficial": STRATEGY_CATALOG["QBE-00"].nombre_oficial,
            "motivo_diagnostico": "Operación vetada: ninguna estrategia cumple checklist de seguridad (+EV)" if ninguna_viable else "Estrategias viables identificadas"
        }

        return results