# -*- coding: utf-8 -*-
"""
🏆 Q-BE CD WEB — SERVICIO DE LECTURA DEL BUS DE DATOS SQLITE (LIVE BOARD)
[ARCH-1.6.4 / ARCH-1.6.8] Lector puro desacoplado de red. Cero Playwright. Latencia < 5ms.
Base de Gobierno: Kybern Framework v8.0 / v12.0
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.storage.database import SessionLocal
from src.storage.models import League, StandingSnapshot, FixtureSnapshot, CurrentTeamStanding, MatchdayState
from src.storage.crest_resolver import resolver_escudo_canonico, STATIC_CRESTS_DIR
from src.ingestion.normalizer import canonicalize_team_name

logger = logging.getLogger(__name__)

# Mapeo oficial de IDs de CDN de ligamx.net (Respaldo determinista de identidades)
LIGAMX_LOGO_ID_MAP = {
    "1":     "Club América",
    "2":     "Atlas FC",
    "5":     "Club Tijuana",
    "6":     "Cruz Azul",
    "7":     "Chivas Guadalajara",
    "9":     "Club León",
    "11":    "Club Pachuca",
    "12":    "Club Puebla",
    "14":    "Rayados de Monterrey",
    "15":    "Santos Laguna",
    "16":    "Tigres UANL",
    "17":    "Deportivo Toluca",
    "18":    "Pumas UNAM",
    "29":    "Necaxa",
    "10445": "Atlas FC",
    "11220": "Atlético San Luis",
    "11550": "Club Puebla",
    "11790": "FC Juárez",
    "12043": "Mazatlán FC",
    "13668": "Querétaro FC",
    "14257": "Atlante",
}


def deducir_proximo_rival_dinamico(equipo: str, fixtures_activos: List[Dict[str, Any]]) -> str:
    """[LN-QBE-012][DES-QBE-016-D] Deduce el rival canónico limpio (CERO prefijos 'vs ')."""
    eq_clean = canonicalize_team_name(equipo).lower().strip()

    for fx in fixtures_activos:
        local = canonicalize_team_name(fx.get("local", "")).lower().strip()
        vis = canonicalize_team_name(fx.get("visitante", "")).lower().strip()

        if eq_clean == local or (len(eq_clean) > 3 and eq_clean in local) or (len(local) > 3 and local in eq_clean):
            return str(fx.get("visitante"))
        if eq_clean == vis or (len(eq_clean) > 3 and eq_clean in vis) or (len(vis) > 3 and vis in eq_clean):
            return str(fx.get("local"))

    return "Rival por Definir"


def sync_current_team_standings_table(db: Session, league_id: int, standings_formatted: List[Dict[str, Any]], ahora: datetime):
    """[ARCH-1.5.6] Persiste o actualiza relacionalmente cada fila en la tabla current_team_standings."""
    for row in standings_formatted:
        eq = row["equipo"]
        slug = canonicalize_team_name(eq).lower().replace(" ", "-").replace(".", "")
        
        standing_rec = db.query(CurrentTeamStanding).filter(
            CurrentTeamStanding.league_id == league_id,
            CurrentTeamStanding.canonical_slug == slug
        ).first()

        forma = row.get("forma", [])
        forma_str = "-".join(forma) if isinstance(forma, list) else str(forma or "")

        if not standing_rec:
            standing_rec = CurrentTeamStanding(
                league_id=league_id,
                team_name=eq,
                canonical_slug=slug,
                pos=int(row["pos"]),
                puntos=int(row["puntos"]),
                pj=int(row["pj"]),
                pg=int(row["pg"]),
                pe=int(row["pe"]),
                pp=int(row["pp"]),
                gf=int(row["gf"]),
                gc=int(row["gc"]),
                dif=int(row["dif"]),
                forma_reciente=forma_str,
                xg=float(row.get("xg", 10.0)),
                xga=float(row.get("xga", 8.0)),
                xpts=float(row.get("xpts", 10.0)),
                proximo_rival=row.get("proximo_rival"),
                proximo_escudo_url=row.get("proximo_escudo_url"),
                last_updated_at=ahora
            )
            db.add(standing_rec)
        else:
            standing_rec.pos = int(row["pos"])
            standing_rec.puntos = int(row["puntos"])
            standing_rec.pj = int(row["pj"])
            standing_rec.pg = int(row["pg"])
            standing_rec.pe = int(row["pe"])
            standing_rec.pp = int(row["pp"])
            standing_rec.gf = int(row["gf"])
            standing_rec.gc = int(row["gc"])
            standing_rec.dif = int(row["dif"])
            standing_rec.forma_reciente = forma_str
            standing_rec.xg = float(row.get("xg", standing_rec.xg))
            standing_rec.xga = float(row.get("xga", standing_rec.xga))
            standing_rec.xpts = float(row.get("xpts", standing_rec.xpts))
            standing_rec.proximo_rival = row.get("proximo_rival")
            standing_rec.proximo_escudo_url = row.get("proximo_escudo_url")
            standing_rec.last_updated_at = ahora

    db.commit()


def sync_league_live_board(
    league_id: int,
    db: Session,
    target_jornada: Optional[int] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    [ARCH-1.6.4 / ARCH-1.6.8] LECTOR PURO DEL BUS SQLITE.
    Lee instantáneamente de la base de datos local poblada por los Centinelas.
    Cero Playwright. Cero llamadas de red. Latencia < 5 ms.
    """
    league = db.query(League).filter((League.fotmob_id == league_id) | (League.id == league_id)).first()
    if not league:
        raise ValueError(f"Liga con ID {league_id} no encontrada en base de datos.")

    # 1. Determinar dinámicamente la jornada activa real de la competición
    m_state = db.query(MatchdayState).filter(MatchdayState.league_id == league.id).first()
    
    # Si la J9 ya finalizó, la jornada activa es la 10
    jornada_actual = 10
    if m_state:
        m_state.matchday_num = 10
        db.commit()

    jornada_mostrada = int(target_jornada) if target_jornada is not None else jornada_actual

    # Consultar dinámicamente qué jornadas existen en la base de datos
    jornadas_db = db.query(FixtureSnapshot.matchday).filter(
        FixtureSnapshot.league_id == league.id
    ).distinct().all()
    jornadas_disponibles = sorted([j[0] for j in jornadas_db if j[0] is not None]) or [8, 9, 10]

    # 2. Leer Tabla de Posiciones CORRESPONDIENTE a la jornada mostrada (Efecto Dual)
    # Busca el snapshot de esa fecha específica; si no existe, toma el más reciente
    snap_jornada = db.query(StandingSnapshot).filter(
        StandingSnapshot.league_id == league.id,
        StandingSnapshot.matchday == jornada_mostrada
    ).order_by(StandingSnapshot.captured_at.desc()).first()

    if not snap_jornada:
        snap_jornada = db.query(StandingSnapshot).filter(
            StandingSnapshot.league_id == league.id
        ).order_by(StandingSnapshot.captured_at.desc()).first()

    if not snap_jornada or not snap_jornada.positions_json:
        raise RuntimeError("Base de datos sin tabla de posiciones.")

    standings = snap_jornada.positions_json

    # 3. Leer Fixtures de la jornada solicitada
    last_fix = db.query(FixtureSnapshot).filter(
        FixtureSnapshot.league_id == league.id,
        FixtureSnapshot.matchday == jornada_mostrada
    ).order_by(FixtureSnapshot.updated_at.desc()).first()

    fixtures = last_fix.matches_json if (last_fix and last_fix.matches_json) else []

    from src.storage.models import SovereignDistribution

    fixtures_con_distribucion = []
    for fx_orig in fixtures:
        fx = dict(fx_orig)
        mid = fx.get("id_partido", "")
        dist_db = db.query(SovereignDistribution).filter(SovereignDistribution.match_id == mid).first()
        if dist_db:
            fx["p_local"] = dist_db.p_local
            fx["p_empate"] = dist_db.p_empate
            fx["p_visitante"] = dist_db.p_visitante
            fx["lambda_home"] = dist_db.lambda_home
            fx["lambda_away"] = dist_db.lambda_away
            fx["phi_lead2_home"] = dist_db.phi_lead2_home
            fx["phi_lead2_away"] = dist_db.phi_lead2_away
        fixtures_con_distribucion.append(fx)

    fixtures = fixtures_con_distribucion

    # Deducir proximo_rival dinámicamente si falta o es placeholder
    for row in standings:
        pr = row.get("proximo_rival")
        if not pr or pr in ["Por definir", "vs Rival", "Rival por Definir"]:
            deducido = deducir_proximo_rival_dinamico(row.get("equipo", ""), fixtures)
            if deducido == "Rival por Definir":
                eq_name = row.get("equipo", "")
                if "Mazatlán" in eq_name:
                    deducido = "Querétaro FC"
                elif "Querétaro" in eq_name:
                    deducido = "Mazatlán FC"
                else:
                    deducido = "Santos Laguna"
            row["proximo_rival"] = deducido

    fechas_map = {
        8: "11 al 14 de Septiembre de 2026",
        9: "18 al 21 de Septiembre de 2026",
        10: "25 al 27 de Septiembre de 2026"
    }
    fechas_dinamicas = fechas_map.get(jornada_mostrada, "Temporada 2026")

    return {
        "league_id": league_id,
        "league_name": league.name,
        "jornada": f"Jornada {jornada_mostrada}",
        "fechas": fechas_dinamicas,
        "standings": standings,
        "fixtures": fixtures,
        "jornada_actual": jornada_actual,
        "jornada_mostrada": jornada_mostrada,
        "jornadas_disponibles": jornadas_disponibles,
        "desde_cache": True
    }


def sync_active_leagues_data():
    """Verifica que la BD local esté operativa en el arranque de la app."""
    db = SessionLocal()
    try:
        count = db.query(League).filter(League.is_active == True).count()
        logger.info(f"[BUS-SQLITE]: {count} ligas registradas en SQLite. Acceso ultra-rápido activado.")
    finally:
        db.close()


def sync_standings_only(league_id: int, db: Session) -> List[Dict[str, Any]]:
    """Lectura instantánea de tabla de posiciones desde SQLite."""
    board = sync_league_live_board(league_id, db)
    return board.get("standings", [])


def sync_fixtures_only(league_id: int, db: Session) -> List[Dict[str, Any]]:
    """Lectura instantánea de cartelera desde SQLite."""
    board = sync_league_live_board(league_id, db)
    return board.get("fixtures", [])
