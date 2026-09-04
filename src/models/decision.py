# Q-BE Casino Deportes — Decision Models (src/models/decision.py)
"""
Contratos Pydantic V2 para Órdenes de Ejecución y Gestión de Cartera.
[LN-QBE-070] [ARCH-PILLAR]
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class StrategySelection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    codigo: str
    nombre_oficial: str
    descripcion_ejecutiva: str
    linea_promocional: str


class KeyMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    score_calidad_S_i: float
    peso_portafolio_w_i: float
    phi_lead2_prob_ventaja_2_goles: float
    psi_downside_riesgo: float
    ev_neto_roi_porcentaje: float


class TicketOrder(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    seleccion: str
    momio: float = Field(ge=0.0)  # Permite 0.0 en boletos sin seguro (D1)
    monto_mxn: float = Field(ge=0.0)


class MatchTickets(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    inversion_partido_A_i: float = Field(ge=0.0)
    boleto_1_seguro: TicketOrder
    boleto_2_ganancia: TicketOrder


class Projections(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    ganancia_neta_principal_mxn: float
    roi_principal_porcentaje: float
    freeroll_doble_ganancia_mxn: float = 0.0
    freeroll_roi_porcentaje: float = 0.0
    resultado_tablas_mxn: float
    perdida_maxima_posible_mxn: float


class CashoutTargets(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    monto_salida_emergencia_tablas_mxn: float
    monto_salida_optima_min85: str
    instruccion_emergencia_rompequinielas: str
    instruccion_desarrollo_normal: str


class MatchExecutionOrder(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    id_partido: str
    partido: str
    horario_evento: str
    estrategia_seleccionada: StrategySelection
    metricas_clave: KeyMetrics
    forma_reciente_auditada: Dict[str, Any]
    boletos: MatchTickets
    proyecciones: Projections
    cashout_targets: CashoutTargets


class SatelliteModule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    autorizado: bool = False
    partido_seleccionado: str = "N/A"
    seleccion: str = "N/A"
    momio: float = 0.0
    monto_satelite_mxn: float = 0.0
    promocion: str = "Pago Anticipado"
    ganancia_potencial_neta_mxn: float = 0.0
    roi_potencial_porcentaje: float = 0.0
    justificacion_financiamiento: str


class PortfolioControl(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    modalidad: Literal["BANKROLL", "VAQUITA"]
    total_partidos_core_aprobados: int
    capital_total_core_mxn: float
    probabilidad_ruina_total_porcentaje: float
    blindaje_global_preservacion_porcentaje: float
    desglose_vaquita: Dict[str, Any]
    desglose_bankroll: Dict[str, Any]


class PortfolioBalance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    capital_total_comprometido_mxn: float
    ganancia_neta_esperada_jornada_mxn: float
    roi_global_esperado_porcentaje: float


class PortfolioExecutionPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    control_portafolio: PortfolioControl
    ordenes_ejecucion_partidos: List[MatchExecutionOrder]
    modulo_satelite_asimetrico: SatelliteModule
    balance_global_portafolio: PortfolioBalance