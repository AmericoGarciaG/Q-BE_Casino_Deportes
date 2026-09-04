# Q-BE Casino Deportes — Analytics Models (src/models/analytics.py)
"""
Contratos Pydantic V2 para Salidas de Motores Matemáticos y Estocásticos.
[LN-QBE-020 .. LN-QBE-050] [ALGO-PROTECTED]
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class H2HDecayResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    p_fav: float = Field(ge=0.0, le=1.0)
    p_emp: float = Field(ge=0.0, le=1.0)
    p_und: float = Field(ge=0.0, le=1.0)
    antiguedad_promedio_dias: float = Field(ge=0.0)
    gf_h2h_local: float = Field(ge=0.0)
    gf_h2h_visita: float = Field(ge=0.0)


class SyntheticMetricsResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    fcf_local: float = Field(ge=0.65, le=1.35)
    e_att_local: float = Field(ge=0.60, le=1.40)
    fcf_vis: float = Field(ge=0.65, le=1.35)
    e_att_vis: float = Field(ge=0.60, le=1.40)


class PoissonModulationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    lambda_local: float = Field(ge=0.05, le=6.00)
    mu_visitante: float = Field(ge=0.05, le=6.00)
    goles_esperados_totales: float
    peso_h2h: float = Field(ge=0.15, le=0.50)
    peso_liga: float = Field(ge=0.50, le=0.85)
    omega_perf_local: float = Field(ge=0.40, le=1.60)
    omega_perf_vis: float = Field(ge=0.40, le=1.60)

    # Probabilidades Poisson puras
    p_poisson_fav: float = Field(ge=0.0, le=1.0)
    p_poisson_emp: float = Field(ge=0.0, le=1.0)
    p_poisson_und: float = Field(ge=0.0, le=1.0)

    # Probabilidades Híbridas finales
    prob_hibrida_fav: float = Field(ge=0.0, le=1.0)
    prob_hibrida_empate: float = Field(ge=0.0, le=1.0)
    prob_hibrida_und: float = Field(ge=0.0, le=1.0)

    # Variables avanzadas
    phi_lead2: float = Field(ge=0.0, le=1.0)
    psi_ruina: float = Field(ge=0.0, le=1.0)
    d_mkt: float = Field(gt=0.0)
    edge_fav: float
    edge_empate: float
    edge_und: float
    candidato_satelite: bool = False


# Alias para retrocompatibilidad total
PoissonModulatedResult = PoissonModulationResult


class BreakevenThresholdsResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    theta_fav_h1: float = Field(ge=0.0, le=1.0)
    theta_emp_h2: float = Field(ge=0.0, le=1.0)
    theta_emp_pa_h2_plus: float = Field(ge=0.0, le=1.0)
    theta_und_r1: float = Field(ge=0.0, le=1.0)
    denom_h1: Optional[float] = None
    denom_h2: Optional[float] = None
    denom_h2_pa: Optional[float] = None
    denom_r1: Optional[float] = None
    momio_sintetico_x2: float = Field(default=1.0, ge=1.0)