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


# ── [ARCH-1.5.1] ESQUEMA RELACIONAL NORMALIZADO 3NF MULTI-TORNEO ──────────

class Competition(Base):
    __tablename__ = "competitions"
    id = Column(String(50), primary_key=True)  # Ej: 'MEX_LIGAMX', 'ENG_PL', 'ESP_LALIGA'
    name = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    macro_mu_liga = Column(Float, default=2.65)        # μ_liga (Goles promedio incondicionales)
    macro_gamma_home = Column(Float, default=0.15)    # γ_home (Efecto localía medio incondicional)
    created_at = Column(DateTime, default=datetime.utcnow)


class Season(Base):
    __tablename__ = "seasons"
    id = Column(String(50), primary_key=True)  # Ej: 'MEX_2026_APERTURA', 'ENG_2026_2027'
    competition_id = Column(String(50), ForeignKey("competitions.id"), nullable=False)
    year = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Match(Base):
    __tablename__ = "matches"
    id = Column(String(100), primary_key=True)  # Ej: 'MATCH_MEX_2026_J09_TOL_SAN'
    competition_id = Column(String(50), ForeignKey("competitions.id"), nullable=False)
    season_id = Column(String(50), ForeignKey("seasons.id"), nullable=True)
    matchday_num = Column(Integer, default=1)
    kickoff_utc = Column(DateTime, nullable=True)
    home_team_slug = Column(String(50), nullable=False)
    away_team_slug = Column(String(50), nullable=False)
    status = Column(String(20), default="SCHEDULED")  # 'SCHEDULED', 'IN_PLAY', 'FINISHED', 'POSTPONED'
    score_home = Column(Integer, nullable=True)
    score_away = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MatchTelemetry(Base):
    __tablename__ = "match_telemetry"
    match_id = Column(String(100), ForeignKey("matches.id"), primary_key=True)
    team_slug = Column(String(50), primary_key=True)
    xg = Column(Float, default=0.0)
    xga = Column(Float, default=0.0)
    sot = Column(Float, default=0.0)
    sota = Column(Float, default=0.0)
    possession_pct = Column(Float, default=50.0)
    fouls = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)


class SovereignDistribution(Base):
    __tablename__ = "sovereign_distributions"
    match_id = Column(String(100), ForeignKey("matches.id"), primary_key=True)
    model_version = Column(String(50), default="v13.0-DIRGEN")
    p_local = Column(Float, nullable=False)
    p_empate = Column(Float, nullable=False)
    p_visitante = Column(Float, nullable=False)
    lambda_home = Column(Float, nullable=False)
    lambda_away = Column(Float, nullable=False)
    phi_lead2_home = Column(Float, default=0.0)
    phi_lead2_away = Column(Float, default=0.0)
    epistemic_delta = Column(Float, default=0.0)
    audit_trace_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Slate(Base):
    __tablename__ = "slates"
    id = Column(String(50), primary_key=True)  # Ej: 'PROGOL_2245', 'PRONOSPORTS_754'
    name = Column(String(100), nullable=False)
    market_type = Column(String(50), default="PROGOL")  # 'PROGOL', 'PRONOSPORTS', 'MIXTO'
    closing_utc = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SlateItem(Base):
    __tablename__ = "slate_items"
    slate_id = Column(String(50), ForeignKey("slates.id"), primary_key=True)
    match_id = Column(String(100), ForeignKey("matches.id"), primary_key=True)
    item_order = Column(Integer, nullable=False)  # Orden 1 a 14 en la quiniela



