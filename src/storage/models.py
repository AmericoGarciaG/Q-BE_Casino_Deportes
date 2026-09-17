from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.storage.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class League(Base):
    __tablename__ = "leagues"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    country = Column(String, nullable=False)
    flag = Column(String, nullable=False)
    fotmob_id = Column(Integer, unique=True, nullable=False)
    caliente_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    fotmob_team_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)
    canonical_slug = Column(String, nullable=False)
    crest_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=utc_now)

class StandingSnapshot(Base):
    __tablename__ = "standings_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    season = Column(String, nullable=False)
    matchday = Column(Integer, nullable=False)
    captured_at = Column(DateTime, default=utc_now)
    positions_json = Column(JSON, nullable=False) # Lista con los 18 clubes completos

class FixtureSnapshot(Base):
    __tablename__ = "fixtures_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    matchday = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=utc_now)
    matches_json = Column(JSON, nullable=False) # Lista de partidos de la jornada

class PortfolioRecord(Base):
    __tablename__ = "portfolio_records"
    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    matchday = Column(Integer, nullable=False)
    bankroll = Column(Float, nullable=False)
    generated_at = Column(DateTime, default=utc_now)
    portfolio_json = Column(JSON, nullable=False)

class MatchdayState(Base):
    """
    [ARCH-1.5.5] Control de Ciclo de Vida de Jornada y Centinela de Caché.
    Puente de datos para el motor de calibración PM-FACE (Fase 7).
    """
    __tablename__ = "matchday_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    matchday_num = Column(Integer, nullable=False, default=8)
    season = Column(String(20), default="2026")
    status = Column(String(20), default="ACTIVA")  # ACTIVA, CONCLUIDA
    last_scraped_at = Column(DateTime, default=utc_now)
    total_matches = Column(Integer, default=9)
    finished_matches = Column(Integer, default=0)


class CurrentTeamStanding(Base):
    """
    [ARCH-1.5.6] Tabla Relacional Auditable de Posiciones y Métricas en Vivo.
    Centraliza número por número los datos exactos que alimentan el motor de cálculo.
    """
    __tablename__ = "current_team_standings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    team_name = Column(String, nullable=False, index=True)
    canonical_slug = Column(String, nullable=False, index=True)
    pos = Column(Integer, nullable=False)
    puntos = Column(Integer, nullable=False)
    pj = Column(Integer, nullable=False)
    pg = Column(Integer, nullable=False)
    pe = Column(Integer, nullable=False)
    pp = Column(Integer, nullable=False)
    gf = Column(Integer, nullable=False)
    gc = Column(Integer, nullable=False)
    dif = Column(Integer, nullable=False)
    forma_reciente = Column(String, nullable=False) # Ej. "G-E-G-P-G"
    xg = Column(Float, default=10.0)
    xga = Column(Float, default=8.0)
    xpts = Column(Float, default=10.0)
    proximo_rival = Column(String, nullable=True)
    proximo_escudo_url = Column(String, nullable=True)
    last_updated_at = Column(DateTime, default=datetime.utcnow)


class LLMTokenLedger(Base):
    __tablename__ = "llm_token_ledger"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    key_alias = Column(String(50), nullable=False)
    task_type = Column(String(50), nullable=False)  # 'TESIS', 'CURACION', 'AUDITORIA'
    model_name = Column(String(50), default="gemini-3.6-flash")
    prompt_tokens = Column(Integer, default=0)
    candidates_tokens = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    cost_usd = Column(Float, default=0.0)
    status = Column(String(20), default="SUCCESS")  # 'SUCCESS', 'COOLDOWN_429', 'FALLBACK'



