# Q-BE Casino Deportes — Metrics Engine (src/core/metrics.py)
"""
[LN-QBE-030] Métricas Sintéticas de Dominio Territorial y Peligro Ofensivo (FCF y E_att).
[ALGO-PROTECTED] Factor de Control de Cancha y Eficiencia Atacante con Clamps Inmutables.
"""

from src.models.analytics import SyntheticMetricsResult


class SyntheticMetricsEngine:
    FCF_MIN = 0.65
    FCF_MAX = 1.35
    E_ATT_MIN = 0.60
    E_ATT_MAX = 1.40

    @classmethod
    def compute_all(
        cls,
        poss_l: float,
        sot_l: float,
        sota_l: float,
        gf_l: float,
        poss_v: float,
        sot_v: float,
        sota_v: float,
        gf_v: float
    ) -> SyntheticMetricsResult:
        """
        Calcula FCF y E_att para equipo local y visitante aplicando los Clamps de seguridad.
        """
        fcf_l = cls._compute_fcf(poss_l, sot_l, sota_l)
        eatt_l = cls._compute_eatt(gf_l, sot_l)

        fcf_v = cls._compute_fcf(poss_v, sot_v, sota_v)
        eatt_v = cls._compute_eatt(gf_v, sot_v)

        return SyntheticMetricsResult(
            fcf_local=fcf_l,
            e_att_local=eatt_l,
            fcf_vis=fcf_v,
            e_att_vis=eatt_v
        )

    @classmethod
    def _compute_fcf(cls, poss_pct: float, sot: float, sota: float) -> float:
        denom = sot + sota + 2.0
        if denom <= 0:
            raw_fcf = 1.0
        else:
            raw_fcf = (poss_pct / 50.0) * ((2.0 * (sot + 1.0)) / denom)
        clamped_fcf = max(cls.FCF_MIN, min(cls.FCF_MAX, raw_fcf))
        return round(clamped_fcf, 4)

    @classmethod
    def _compute_eatt(cls, gf: float, sot: float) -> float:
        denom = 1.0 + (0.35 * sot)
        if denom <= 0:
            raw_eatt = 1.0
        else:
            raw_eatt = (gf + (0.35 * sot)) / denom
        clamped_eatt = max(cls.E_ATT_MIN, min(cls.E_ATT_MAX, raw_eatt))
        return round(clamped_eatt, 4)