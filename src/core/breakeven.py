# Q-BE Casino Deportes — Breakeven Engine (src/core/breakeven.py)
"""
[LN-QBE-050] Ecuaciones de Breakeven Dinámico Continuo (theta*).
[BIZ-LOGIC] [ANTI-BUG] [ALGO-PROTECTED] Derivación analítica de umbrales EV=0 acotados en [0.0, 1.0].
Calcula los límites exactos de rentabilidad matemática neutralizando la comisión del casino.
"""

from src.models.analytics import BreakevenThresholdsResult


class BreakevenEngine:
    @classmethod
    def compute_thresholds(
        cls,
        odd_fav: float,
        odd_emp: float,
        odd_und: float,
        psi_ruina: float,
        phi_lead2: float,
        p_hib_fav: float
    ) -> BreakevenThresholdsResult:
        # 1. Familia H1 (Favorito con Seguro en Empate)
        inv_emp = (1.0 / odd_emp) if odd_emp > 0 else 1.0
        denom_h1 = ((1.0 - inv_emp) * odd_fav) - 1.0
        if denom_h1 <= 0.0:
            theta_fav = 1.0
        else:
            theta_fav = min(1.0, max(0.0, psi_ruina / denom_h1))

        # 2. Familia H2 (Empate de Valor con Seguro en Favorito)
        inv_fav = (1.0 / odd_fav) if odd_fav > 0 else 1.0
        denom_h2 = ((1.0 - inv_fav) * odd_emp) - 1.0
        if denom_h2 <= 0.0:
            theta_emp = 1.0
        else:
            theta_emp = min(1.0, max(0.0, psi_ruina / denom_h2))

        # 3. Familia H2+ (Freeroll Doble Impacto con Pago Anticipado)
        denom_h2_pa = denom_h2 + phi_lead2
        if denom_h2_pa <= 0.0:
            theta_emp_pa = 1.0
        else:
            theta_emp_pa = min(1.0, max(0.0, psi_ruina / denom_h2_pa))

        # 4. Familia R1 (Valor en No-Favorito con Seguro en Empate)
        denom_r1 = ((1.0 - inv_emp) * odd_und) - 1.0
        if denom_r1 <= 0.0:
            theta_und = 1.0
        else:
            theta_und = min(1.0, max(0.0, p_hib_fav / denom_r1))

        # Momio Sintético X2
        inv_sum = ((1.0 / odd_und) if odd_und > 0 else 0.0) + ((1.0 / odd_emp) if odd_emp > 0 else 0.0)
        momio_sint_x2 = round(1.0 / inv_sum, 4) if inv_sum > 0 else 1.0

        return BreakevenThresholdsResult(
            theta_fav_h1=round(theta_fav, 6),
            theta_emp_h2=round(theta_emp, 6),
            theta_emp_pa_h2_plus=round(theta_emp_pa, 6),
            theta_und_r1=round(theta_und, 6),
            denom_h1=round(denom_h1, 6),
            denom_h2=round(denom_h2, 6),
            denom_h2_pa=round(denom_h2_pa, 6),
            denom_r1=round(denom_r1, 6),
            momio_sintetico_x2=momio_sint_x2
        )