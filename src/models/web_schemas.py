# Q-BE Casino Deportes — Web Schemas (src/models/web_schemas.py)
"""
[ARCH-PILLAR] Contratos Pydantic V2 para la Capa Web y Endpoints REST de FastAPI.
Gobierna los esquemas de entrada y salida del cliente SPA reactivo.
"""

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, ConfigDict


class LeagueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id: int
    name: str
    country: str
    flag: str
    fotmob_id: int
    is_active: bool


class StandingRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    pos: int
    equipo: str
    escudo_url: Optional[str] = None
    pj: int
    pg: int
    pe: int
    pp: int
    gf: int
    gc: int
    dif: int
    puntos: int
    forma: List[str] = Field(default_factory=list)  # ["G", "E", "P", ...]
    xg: Optional[float] = None
    xga: Optional[float] = None
    xpts: Optional[float] = None
    proximo_rival: Optional[str] = None
    proximo_escudo_url: Optional[str] = None  # <-- [DES-QBE-016-B] Campo obligatorio agregado


class Odds1X2(BaseModel):
    model_config = ConfigDict(extra="ignore")
    L: float = Field(gt=1.0)
    E: float = Field(gt=1.0)
    V: float = Field(gt=1.0)
    pago_anticipado: bool = True


class MatchFixtureOut(BaseModel):
    """
    [ARCH-1.6.3] Contrato canónico de fixture con Máquina de Estados semántica.
    Campos obligatorios para el ciclo de vida completo del partido en el Live Board.
    """
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id_partido: str
    local: str
    visitante: str
    local_escudo_url: Optional[str] = None
    visitante_escudo_url: Optional[str] = None
    horario: str
    fecha_dt: Optional[str] = None              # ISO 8601: "YYYY-MM-DDTHH:MM:SS"
    fecha_bloque: Optional[str] = None          # Etiqueta de agrupación (retrocompat.)
    momios: Optional[Union[Odds1X2, Dict[str, Any]]] = None
    es_viable_triaje: bool = True
    motivo_triaje: Optional[str] = None
    sub_badge: Optional[str] = None

    # [ARCH-1.6.3] Máquina de Estados del Fixture
    estado: Literal["PROGRAMADO", "EN_CURSO", "FINALIZADO", "REPROGRAMADO"] = "PROGRAMADO"
    marcador_actual: Optional[str] = None       # Ej. "0 - 2", "1 - 1" (solo FINALIZADO/EN_CURSO)
    minuto_juego: Optional[str] = None          # Ej. "75'", "Medio Tiempo", "Final"
    es_hoy: bool = False                        # True si fecha_dt.date() == datetime.now().date()
    disponible_para_seleccion: bool = True      # False si FINALIZADO o REPROGRAMADO [BIZ-LOGIC]
    es_operable: bool = True
    es_pospuesto: bool = False

    # ── [CAMPOS SOBERANOS TRATADO VOL. I - ENMIENDA SOBERANA ARCH-1.4.5-B] ──
    p_local: Optional[float] = Field(default=None, description="Probabilidad soberana victoria local")
    p_empate: Optional[float] = Field(default=None, description="Probabilidad soberana empate")
    p_visitante: Optional[float] = Field(default=None, description="Probabilidad soberana victoria visitante")
    lambda_home: Optional[float] = Field(default=None, description="Intensidad de gol esperada local")
    lambda_away: Optional[float] = Field(default=None, description="Intensidad de gol esperada visitante")
    phi_lead2_home: Optional[float] = Field(default=None, description="Probabilidad de ventaja >=2 goles local (André)")
    phi_lead2_away: Optional[float] = Field(default=None, description="Probabilidad de ventaja >=2 goles visitante (André)")

    # ── [BENCHMARK DE MERCADO - DES-QBE-039 & ARCH-1.4.8] ──
    consenso_mercado: Optional["MarketConsensusOut"] = None
    momios_operadores: Optional[Dict[str, Any]] = None


class MarketConsensusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    p_L_mercado: float = 0.0
    p_E_mercado: float = 0.0
    p_V_mercado: float = 0.0
    delta_L: float = 0.0
    delta_E: float = 0.0
    delta_V: float = 0.0



class LiveBoardOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    league_id: int
    league_name: str
    jornada: str
    fechas: str
    standings: List[StandingRowOut]
    fixtures: List[MatchFixtureOut]
    # Nuevos campos legislados Fase 4: [ARCH-1.6.8]
    jornada_actual: int = Field(default=8, description="Jornada administrativa de la liga")
    jornada_mostrada: int = Field(default=8, description="Jornada desplegada actualmente en cartelera")
    jornadas_disponibles: List[int] = Field(default_factory=lambda: [8, 9], description="Jornadas seleccionables")



# Alias para retrocompatibilidad total
LiveBoardResponse = LiveBoardOut


class GeneratePortfolioRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    league_id: int = Field(default=262)
    selected_match_ids: List[str] = Field(default_factory=list)
    bankroll: float = Field(default=200.0, ge=10.0)
    mode: str = Field(default="BANKROLL", pattern="^(BANKROLL|VAQUITA)$")
    # [ARCH-1.4.30] Parámetro interactivo de concentración de masa Γ (Capa 0).
    gamma_slider: Optional[float] = Field(0.67, ge=0.67, le=0.75, description="Umbral de concentración de masa Capa 0")
    # [ARCH-1.4.37] Parámetro de Cobertura Dinámica δ (Dutching con Rendimiento, [LN-QBE-077-B]).
    # `DEF` = indemnidad pura V=0 (contrato sellado) | `BAL` = 50% de δ* | `AGR` = δ* |
    # `CUSTOM` = δ explícito resuelto por la ley pura `calcular_particion_dutching_dinamico()`.
    modo_cobertura: Optional[str] = Field(
        "DEF", description="DEF (V=0), BAL (50% delta*), AGR (delta*)"
    )


class IngestionExtractRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    url: Optional[str] = None
    imagen_path: Optional[str] = None


# ── [ARCH-1.4.38 / LN-QBE-100] VISOR DE BACKTESTING (CALIBRACIÓN FACTUAL) ─────
class CalibrationMatchOut(BaseModel):
    """
    [LN-QBE-100] Casilla micro estilo BetExplorer: P' fiduciaria vs consenso de mercado (q_mkt),
    resultado real consumado y error de Brier de ambas predicciones.
    """
    model_config = ConfigDict(extra="ignore")
    id_partido: str
    jornada: int
    local: str
    visitante: str
    local_escudo_url: Optional[str] = None
    visitante_escudo_url: Optional[str] = None
    marcador: str
    goles_local: int
    goles_visitante: int
    resultado_real: Literal["LOCAL", "EMPATE", "VISITANTE"]
    favorito_designado: Literal["LOCAL", "VISITANTE"]
    tipo_resultado: Literal["FAVORITO", "EMPATE", "UNDERDOG"]
    p_local: float
    p_empate: float
    p_visitante: float
    q_local: float
    q_empate: float
    q_visitante: float
    momios: Dict[str, float] = Field(default_factory=dict)
    brier_qbe: float
    brier_mercado: float
    acierto: bool
    # [LN-QBE-100 · Axioma del Prior de Mercado (Cold Start Resolution)] Sello de suficiencia
    # fáctica S(I) del partido: 0 = ignorancia declarada ⇒ P′ fue sustituida por q_mkt (Cold Start).
    suficiencia_S_I: Optional[int] = None
    # [ARCH-1.4.38 · REFACTOR-TRIADA-PMAX-PMID-PLOW] Vértices del símplex Δ² ordenados por
    # probabilidad fiduciaria descendente (P_max ≥ P_mid ≥ P_low) y vértice consumado en cancha.
    r_max: Optional[Literal["LOCAL", "EMPATE", "VISITANTE"]] = None
    r_mid: Optional[Literal["LOCAL", "EMPATE", "VISITANTE"]] = None
    r_low: Optional[Literal["LOCAL", "EMPATE", "VISITANTE"]] = None
    clasificacion_triada: Optional[Literal["P_MAX", "P_MID", "P_LOW"]] = None
    masa_cobertura_pct: Optional[float] = None
    p_low_ruptura_pct: Optional[float] = None


class CalibrationJornadaOut(BaseModel):
    """[LN-QBE-100] Fila meso: calibración agregada de una jornada concluida."""
    model_config = ConfigDict(extra="ignore")
    jornada: int
    total_partidos: int
    aciertos_cobertura: int
    tasa_cobertura_pct: float
    desglose: Dict[str, int] = Field(default_factory=dict)
    # [ARCH-1.4.38 · REFACTOR-TRIADA-PMAX-PMID-PLOW] Desglose cuantitativo puro de la jornada:
    # masa de cobertura (% P_max + % P_mid), porcentaje por vértice y conteos enteros, incluida la
    # procedencia del rescate secundario (empate vs rival).
    masa_cobertura_pct: float = 0.0
    pct_p_max: float = 0.0
    pct_p_mid: float = 0.0
    pct_p_low: float = 0.0
    n_p_max: int = 0
    n_p_mid: int = 0
    n_p_low: int = 0
    n_p_mid_empate: int = 0
    n_p_mid_rival: int = 0
    brier_score_qbe: float
    brier_score_mercado: float
    alpha_calibracion_pct: float
    partidos: List[CalibrationMatchOut] = Field(default_factory=list)


class CalibrationSummaryOut(BaseModel):
    """[LN-QBE-100] Bloque macro de temporada (H_fid, Brier de Q-BE vs mercado y Alpha)."""
    model_config = ConfigDict(extra="ignore")
    total_partidos: int
    partidos_favorito: int
    partidos_empate: int
    partidos_underdog: int
    tasa_coincidencia_fiduciaria_pct: float
    # [ARCH-1.4.38 · REFACTOR-TRIADA-PMAX-PMID-PLOW] Taxonomía macro de vértices del símplex Δ²:
    # masa de cobertura (P_max + P_mid ≡ 100% − P_low), tasas puras por vértice y conteos enteros
    # con el desglose de la procedencia del rescate secundario (empate vs rival).
    masa_cobertura_pct: float = 0.0
    p_max_aciertos_pct: float = 0.0
    p_mid_rescate_pct: float = 0.0
    p_mid_empate_pct: float = 0.0
    p_mid_rival_pct: float = 0.0
    p_low_ruptura_pct: float = 0.0
    total_p_max: int = 0
    total_p_mid: int = 0
    total_p_low: int = 0
    total_p_mid_empate: int = 0
    total_p_mid_rival: int = 0
    brier_score_qbe: float
    brier_score_mercado: float
    alpha_calibracion_pct: float
    partidos_pendientes_captura: int = 0
    jornadas_auditadas: List[int] = Field(default_factory=list)


class CalibrationReportResponse(BaseModel):
    """
    [ARCH-1.4.38] Contrato REST del Visor de Backtesting (solo lectura):
    resumen macro de temporada + tabla meso por jornada con parrilla micro embebida.
    """
    model_config = ConfigDict(extra="ignore")
    resumen_temporada: CalibrationSummaryOut
    jornadas: List[CalibrationJornadaOut] = Field(default_factory=list)
