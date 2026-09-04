from __future__ import annotations

# Q-BE Casino Deportes — Poisson Engine (src/core/poisson.py)
"""
Modulación de Desempeño, Goles Esperados y Matriz Poisson Bivariada (6x6).
[LN-QBE-040] [BIZ-LOGIC] [ALGO-PROTECTED]
Incorpora calibración cruzada de xG/xGA Opta (FotMob) para proyección estocástica pura.
"""

import math
import numpy as np
from scipy.stats import poisson
from src.models.analytics import (
    H2HDecayResult,
    SyntheticMetricsResult,
    PoissonModulationResult
)


class PoissonBivariateEngine:
    @classmethod
    def compute_modulations(
        cls,
        h2h: H2HDecayResult,
        metrics: SyntheticMetricsResult,
        gf_local_10p: float,
        gf_vis_10p: float,
        pts_pj_local: float,
        pts_pj_vis: float,
        jornada_tabla: int,
        q_mod_local: float,
        q_mod_vis: float,
        is_fav_local: bool,
        odd_fav: float,
        odd_emp: float,
        odd_und: float,
        pago_anticipado_activo: bool,
        local_xg: float | None = None,
        vis_xga: float | None = None,
        vis_xg: float | None = None,
        local_xga: float | None = None,
        local_gc_10p: float | None = None,
        vis_gc_10p: float | None = None,
        xg_local_prom: float | None = None,
        xga_vis_prom: float | None = None
    ) -> PoissonModulationResult:
        # Resolver alias de nombres Opta
        loc_xg = xg_local_prom if xg_local_prom is not None else local_xg
        v_xga = xga_vis_prom if xga_vis_prom is not None else vis_xga

        # 1. Ponderación adaptativa H2H vs Liga
        w_h2h = max(0.15, 0.50 * math.exp(-h2h.antiguedad_promedio_dias / 300.0))
        w_liga = 1.0 - w_h2h

        # 2. Modulador de tabla
        madurez = min(1.0, float(jornada_tabla) / 6.0)
        mod_tabla_l = 1.0 + madurez * ((pts_pj_local / 1.35) - 1.0)
        mod_tabla_v = 1.0 + madurez * ((pts_pj_vis / 1.35) - 1.0)

        # 3. Multiplicador compuesto (Omega)
        omega_l = float(np.clip(metrics.fcf_local * metrics.e_att_local * mod_tabla_l * q_mod_local, 0.40, 1.60))
        omega_v = float(np.clip(metrics.fcf_vis * metrics.e_att_vis * mod_tabla_v * q_mod_vis, 0.40, 1.60))

        # 4. Goles esperados (lambda, mu) con calibración cruzada Opta xG [LN-QBE-040]
        if loc_xg is not None and v_xga is not None:
            gc_v = vis_gc_10p if vis_gc_10p is not None else 1.0
            base_att_l = 0.65 * loc_xg + 0.35 * gf_local_10p
            base_def_v = 0.65 * v_xga + 0.35 * gc_v
            lambda_base = math.sqrt(max(0.01, base_att_l * base_def_v))
        else:
            lambda_base = gf_local_10p

        if vis_xg is not None and local_xga is not None:
            gc_l = local_gc_10p if local_gc_10p is not None else 1.0
            base_att_v = 0.65 * vis_xg + 0.35 * gf_vis_10p
            base_def_l = 0.65 * local_xga + 0.35 * gc_l
            mu_base = math.sqrt(max(0.01, base_att_v * base_def_l))
        else:
            mu_base = gf_vis_10p

        raw_lambda = ((w_h2h * h2h.gf_h2h_local) + (w_liga * lambda_base)) * omega_l
        raw_mu = ((w_h2h * h2h.gf_h2h_visita) + (w_liga * mu_base)) * omega_v

        lambda_loc = float(np.clip(raw_lambda, 0.05, 6.00))
        mu_vis = float(np.clip(raw_mu, 0.05, 6.00))

        # 5. Matriz Poisson Bivariada 6x6
        p_mat = np.zeros((6, 6))
        for x in range(6):
            for y in range(6):
                p_mat[x, y] = poisson.pmf(x, lambda_loc) * poisson.pmf(y, mu_vis)

        # Normalizar matriz truncada
        p_mat /= np.sum(p_mat)

        p_poi_loc = float(np.sum(np.tril(p_mat, -1)))
        p_poi_emp = float(np.sum(np.diag(p_mat)))
        p_poi_vis = float(np.sum(np.triu(p_mat, 1)))

        if is_fav_local:
            p_poi_fav, p_poi_und = p_poi_loc, p_poi_vis
        else:
            p_poi_fav, p_poi_und = p_poi_vis, p_poi_loc

        # 6. Probabilidades Híbridas
        p_hib_fav = (w_h2h * h2h.p_fav) + (w_liga * p_poi_fav)
        p_hib_emp = (w_h2h * h2h.p_emp) + (w_liga * p_poi_emp)
        p_hib_und = (w_h2h * h2h.p_und) + (w_liga * p_poi_und)

        # Invarianza de masa de probabilidad
        p_sum = p_hib_fav + p_hib_emp + p_hib_und
        p_hib_fav /= p_sum
        p_hib_emp /= p_sum
        p_hib_und /= p_sum

        # 7. Variables Avanzadas
        gamma_inplay = min(0.28, (lambda_loc + mu_vis) / 14.0)

        # Suma de marcadores con ventaja >= 2 goles para el favorito
        lead2_sum = 0.0
        for x in range(6):
            for y in range(6):
                diff = (x - y) if is_fav_local else (y - x)
                if diff >= 2:
                    lead2_sum += p_mat[x, y]

        # Tránsito dinámico in-play
        p_1_0_fav = p_mat[1, 0] if is_fav_local else p_mat[0, 1]
        p_emp_transit = p_mat[1, 1] + p_mat[2, 2] + p_mat[3, 3]
        phi_lead2 = float(np.clip(lead2_sum + gamma_inplay * (p_1_0_fav + p_emp_transit), 0.0, 1.0))

        psi_ruina = p_hib_und * 0.98
        d_mkt = (1.0 / odd_fav) / p_hib_fav if p_hib_fav > 0 else 99.0

        edge_fav = p_hib_fav - (1.0 / odd_fav)
        edge_emp = p_hib_emp - (1.0 / odd_emp)
        edge_und = p_hib_und - (1.0 / odd_und)

        candidato_satelite = bool(odd_und >= 4.50 and pago_anticipado_activo and edge_und >= 0.05 and q_mod_vis >= 0.95)

        return PoissonModulationResult(
            lambda_local=lambda_loc,
            mu_visitante=mu_vis,
            goles_esperados_totales=lambda_loc + mu_vis,
            peso_h2h=w_h2h,
            peso_liga=w_liga,
            omega_perf_local=omega_l,
            omega_perf_vis=omega_v,
            p_poisson_fav=p_poi_fav,
            p_poisson_emp=p_poi_emp,
            p_poisson_und=p_poi_und,
            prob_hibrida_fav=p_hib_fav,
            prob_hibrida_empate=p_hib_emp,
            prob_hibrida_und=p_hib_und,
            phi_lead2=phi_lead2,
            psi_ruina=psi_ruina,
            d_mkt=d_mkt,
            edge_fav=edge_fav,
            edge_empate=edge_emp,
            edge_und=edge_und,
            candidato_satelite=candidato_satelite
        )