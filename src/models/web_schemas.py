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

    # ── [CAMPOS SOBERANOS TRATADO VOL. I] ──
    p_local: Optional[float] = Field(default=None, description="Probabilidad soberana local")
    p_empate: Optional[float] = Field(default=None, description="Probabilidad soberana empate")
    p_visitante: Optional[float] = Field(default=None, description="Probabilidad soberana visitante")
    lambda_home: Optional[float] = Field(default=None, description="Intensidad de gol local")
    lambda_away: Optional[float] = Field(default=None, description="Intensidad de gol visita")
    phi_lead2_home: Optional[float] = Field(default=None, description="Probabilidad de ventaja +2 local")


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


class IngestionExtractRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    url: Optional[str] = None
    imagen_path: Optional[str] = None