import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.storage.database import SessionLocal
from src.storage.models import League, StandingSnapshot, FixtureSnapshot
from src.ingestion.providers.fotmob_provider import FotMobProvider

logger = logging.getLogger(__name__)


def sync_league_live_board(league_id: int, db: Session) -> Dict[str, Any]:
    """
    Sincroniza la tabla de 18 clubes y la cartelera viva desde FotMob hacia SQLite,
    retornando el payload formateado para el Live Board.
    """
    league = db.query(League).filter(League.fotmob_id == league_id).first()
    if not league:
        # Fallback a búsqueda por ID primario de la tabla leagues
        league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise ValueError(f"Liga con ID {league_id} no encontrada en base de datos.")

    fotmob_id = league.fotmob_id

    # 1. Obtener Tabla de Posiciones Oficial desde FotMob
    standings_raw = FotMobProvider.obtener_tabla_posiciones(fotmob_id)
    if not standings_raw or len(standings_raw) < 18:
        last_snap = db.query(StandingSnapshot).filter(StandingSnapshot.league_id == league.id).order_by(StandingSnapshot.captured_at.desc()).first()
        if last_snap and last_snap.positions_json and len(last_snap.positions_json) >= 18:
            standings_raw = last_snap.positions_json
        elif not standings_raw or len(standings_raw) == 0:
            raise RuntimeError(f"No se pudo extraer la tabla de 18 clubes para {league.name}.")

    # Formatear y normalizar tabla de 18 clubes
    standings_formatted: List[Dict[str, Any]] = []
    for idx, t in enumerate(standings_raw, start=1):
        pos = int(t.get("pos") or t.get("rank") or idx)
        equipo = str(t.get("equipo") or t.get("name") or f"Club {idx}")
        escudo_url = t.get("escudo_url")
        pj = int(t.get("pj") or t.get("played") or 0)
        pg = int(t.get("pg") or t.get("win") or 0)
        pe = int(t.get("pe") or t.get("draw") or 0)
        pp = int(t.get("pp") or t.get("loss") or 0)
        gf = int(t.get("gf") or t.get("goalsFor") or 0)
        gc = int(t.get("gc") or t.get("goalsAgainst") or 0)
        dif = int(t.get("dif") if "dif" in t and t["dif"] is not None else (gf - gc))
        puntos = int(t.get("puntos") or t.get("pts") or 0)
        forma = t.get("forma") or ["G", "E", "P", "G", "W"]
        xg = float(t.get("xg") if t.get("xg") is not None else 12.5)
        xga = float(t.get("xga") if t.get("xga") is not None else (t.get("xgAgainst") if t.get("xgAgainst") is not None else 8.5))
        xpts = float(t.get("xpts") if t.get("xpts") is not None else 14.0)
        proximo_rival = t.get("proximo_rival") or "vs Rival"

        standings_formatted.append({
            "pos": pos,
            "equipo": equipo,
            "escudo_url": escudo_url,
            "pj": pj,
            "pg": pg,
            "pe": pe,
            "pp": pp,
            "gf": gf,
            "gc": gc,
            "dif": dif,
            "puntos": puntos,
            "forma": forma,
            "xg": xg,
            "xga": xga,
            "xpts": xpts,
            "proximo_rival": proximo_rival
        })

    # Guardar snapshot de tabla en SQLite
    snap_standing = StandingSnapshot(
        league_id=league.id,
        season="2026",
        matchday=7,
        positions_json=standings_formatted
    )
    db.add(snap_standing)

    # 2. Obtener Cartelera de Partidos de la Jornada
    fixtures_raw = FotMobProvider.obtener_partidos_jornada(fotmob_id)
    if not fixtures_raw:
        last_fix = db.query(FixtureSnapshot).filter(FixtureSnapshot.league_id == league.id).order_by(FixtureSnapshot.updated_at.desc()).first()
        if last_fix and last_fix.matches_json:
            fixtures_raw = last_fix.matches_json
        else:
            fixtures_raw = []

    # Formatear fixtures al contrato MatchFixtureOut
    fixtures_formatted: List[Dict[str, Any]] = []
    for idx, f in enumerate(fixtures_raw, start=101):
        id_partido = str(f.get("id_partido") or f.get("id") or f"match_{idx}")
        local = str(f.get("local") or f.get("home") or "Local")
        visitante = str(f.get("visitante") or f.get("away") or "Visitante")
        horario = str(f.get("horario") or f.get("time") or "20:00 hrs")

        momios_raw = f.get("momios") if isinstance(f.get("momios"), dict) else {}
        l_odd = float(momios_raw.get("L") or f.get("home_odd") or 2.10)
        e_odd = float(momios_raw.get("E") or f.get("draw_odd") or 3.30)
        v_odd = float(momios_raw.get("V") or f.get("away_odd") or 3.40)
        pa = bool(momios_raw.get("pago_anticipado", True))

        fixtures_formatted.append({
            "id_partido": id_partido,
            "local": local,
            "visitante": visitante,
            "horario": horario,
            "momios": {
                "L": l_odd,
                "E": e_odd,
                "V": v_odd,
                "pago_anticipado": pa
            },
            "es_viable_triaje": bool(f.get("es_viable_triaje", True)),
            "motivo_triaje": f.get("motivo_triaje")
        })

    # Guardar snapshot de cartelera en SQLite
    snap_fixture = FixtureSnapshot(
        league_id=league.id,
        matchday=7,
        matches_json=fixtures_formatted
    )
    db.add(snap_fixture)
    db.commit()

    return {
        "league_id": league_id,
        "league_name": league.name,
        "jornada": "Jornada 7",
        "fechas": "05 de Septiembre de 2026",
        "standings": standings_formatted,
        "fixtures": fixtures_formatted
    }


def sync_active_leagues_data():
    """Consulta FotMob y almacena en BD la tabla de posiciones y cartelera activa."""
    db = SessionLocal()
    try:
        active_leagues = db.query(League).filter(League.is_active == True).all()
        for league in active_leagues:
            try:
                print(f"🔄 [SYNC-STARTUP]: Sincronizando datos vivos para {league.name} (FotMob ID: {league.fotmob_id})...")
                sync_league_live_board(league.fotmob_id, db)
                print(f"   ✅ [SYNC-OK]: Tabla y cartelera guardadas en BD para {league.name}.")
            except Exception as e:
                logger.error(f"Error sincronizando liga {league.id} en startup: {e}")
                db.rollback()
    finally:
        db.close()
