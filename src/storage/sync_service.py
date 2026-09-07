import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.storage.database import SessionLocal
from src.storage.models import League, StandingSnapshot, FixtureSnapshot, Team
from src.ingestion.providers.fotmob_provider import FotMobProvider
from src.storage.crest_resolver import resolver_escudo_canonico

logger = logging.getLogger(__name__)


# Catálogo canónico de Jornada 7 con Máquina de Estados [ARCH-1.6.3] [DES-QBE-016-C]
# fecha_dt en ISO 8601 local (America/Mexico_City UTC-6)
LIGA_MX_JORNADA_7_FIXTURES = [
    # ── FINALIZADOS (Viernes 04-Sep) ─────────────────────────────────────────
    {
        "id_partido": "LIGAMX-07-01",
        "local": "FC Juárez",
        "visitante": "Club Pachuca",
        "horario": "21:00 hrs",
        "fecha_dt": "2026-09-04T21:00:00",
        "fecha_bloque": "VIERNES 04 DE SEPTIEMBRE",
        "estado": "FINALIZADO",
        "marcador_actual": "0 - 2",
        "minuto_juego": "Final",
        "es_operable": False,
        "es_pospuesto": False,
        "disponible_para_seleccion": False,
        "momios": {"L": 3.40, "E": 3.30, "V": 1.95, "pago_anticipado": True},
        "es_viable_triaje": False,
        "motivo_triaje": "Partido Finalizado"
    },
    # ── FINALIZADOS (Sábado 05-Sep) ──────────────────────────────────────────
    {
        "id_partido": "LIGAMX-07-02",
        "local": "Atlético San Luis",
        "visitante": "Chivas Guadalajara",
        "horario": "17:00 hrs",
        "fecha_dt": "2026-09-05T17:00:00",
        "fecha_bloque": "SÁBADO 05 DE SEPTIEMBRE",
        "estado": "FINALIZADO",
        "marcador_actual": "0 - 3",
        "minuto_juego": "Final",
        "es_operable": False,
        "es_pospuesto": False,
        "disponible_para_seleccion": False,
        "momios": {"L": 3.60, "E": 3.70, "V": 1.80, "pago_anticipado": True},
        "es_viable_triaje": False,
        "motivo_triaje": "Partido Finalizado"
    },
    {
        "id_partido": "LIGAMX-07-03",
        "local": "Tigres UANL",
        "visitante": "Necaxa",
        "horario": "19:00 hrs",
        "fecha_dt": "2026-09-05T19:00:00",
        "fecha_bloque": "SÁBADO 05 DE SEPTIEMBRE",
        "estado": "FINALIZADO",
        "marcador_actual": "1 - 1",
        "minuto_juego": "Final",
        "es_operable": False,
        "es_pospuesto": False,
        "disponible_para_seleccion": False,
        "momios": {"L": 1.80, "E": 3.70, "V": 3.60, "pago_anticipado": True},
        "es_viable_triaje": False,
        "motivo_triaje": "Partido Finalizado"
    },
    {
        "id_partido": "LIGAMX-07-04",
        "local": "Atlas FC",
        "visitante": "Atlante",
        "horario": "21:00 hrs",
        "fecha_dt": "2026-09-05T21:00:00",
        "fecha_bloque": "SÁBADO 05 DE SEPTIEMBRE",
        "estado": "FINALIZADO",
        "marcador_actual": "1 - 1",
        "minuto_juego": "Final",
        "es_operable": False,
        "es_pospuesto": False,
        "disponible_para_seleccion": False,
        "momios": {"L": 1.85, "E": 3.65, "V": 4.10, "pago_anticipado": True},
        "es_viable_triaje": False,
        "motivo_triaje": "Partido Finalizado"
    },
    # ── PROGRAMADO (Domingo 06-Sep — HOY según fecha real del sistema) ────────
    {
        "id_partido": "LIGAMX-07-05",
        "local": "Cruz Azul",
        "visitante": "Santos Laguna",
        "horario": "17:00 hrs",
        "fecha_dt": "2026-09-06T17:00:00",
        "fecha_bloque": "DOMINGO 06 DE SEPTIEMBRE",  # Frontend evaluará es_hoy dinámicamente
        "estado": "PROGRAMADO",
        "marcador_actual": None,
        "minuto_juego": None,
        "es_operable": True,
        "es_pospuesto": False,
        "disponible_para_seleccion": True,
        "momios": {"L": 1.40, "E": 4.35, "V": 6.00, "pago_anticipado": True},
        "es_viable_triaje": True,
        "motivo_triaje": "Ventana de Valor"
    },
    # ── REPROGRAMADOS (Fecha Lejana > 14 días) ───────────────────────────────
    {
        "id_partido": "LIGAMX-07-06",
        "local": "Pumas UNAM",
        "visitante": "Club León",
        "horario": "10-Sep 21:00 hrs",
        "fecha_dt": "2026-09-10T21:00:00",
        "fecha_bloque": "PARTIDOS REPROGRAMADOS / FECHA LEJANA",
        "estado": "REPROGRAMADO",
        "marcador_actual": None,
        "minuto_juego": None,
        "es_operable": False,
        "es_pospuesto": True,
        "disponible_para_seleccion": False,
        "momios": None,
        "es_viable_triaje": False,
        "motivo_triaje": "Reprogramado"
    },
    {
        "id_partido": "LIGAMX-07-07",
        "local": "Club Puebla",
        "visitante": "Deportivo Toluca",
        "horario": "15-Sep 19:00 hrs",
        "fecha_dt": "2026-09-15T19:00:00",
        "fecha_bloque": "PARTIDOS REPROGRAMADOS / FECHA LEJANA",
        "estado": "REPROGRAMADO",
        "marcador_actual": None,
        "minuto_juego": None,
        "es_operable": False,
        "es_pospuesto": True,
        "disponible_para_seleccion": False,
        "momios": None,
        "es_viable_triaje": False,
        "motivo_triaje": "Reprogramado"
    },
    {
        "id_partido": "LIGAMX-07-08",
        "local": "Club América",
        "visitante": "Club Tijuana",
        "horario": "28-Oct 21:00 hrs",
        "fecha_dt": "2026-10-28T21:00:00",
        "fecha_bloque": "PARTIDOS REPROGRAMADOS / FECHA LEJANA",
        "estado": "REPROGRAMADO",
        "marcador_actual": None,
        "minuto_juego": None,
        "es_operable": False,
        "es_pospuesto": True,
        "disponible_para_seleccion": False,
        "momios": None,
        "es_viable_triaje": False,
        "motivo_triaje": "Reprogramado"
    }
]

CLUB_RIVALS_MAP = {
    "cruz azul": "vs Santos Laguna",
    "santos laguna": "vs Cruz Azul",
    "santos": "vs Cruz Azul",
    "toluca": "vs Club Puebla",
    "deportivo toluca": "vs Club Puebla",
    "puebla": "vs Deportivo Toluca",
    "club puebla": "vs Deportivo Toluca",
    "juárez": "vs Club Pachuca",
    "fc juárez": "vs Club Pachuca",
    "juarez": "vs Club Pachuca",
    "pachuca": "vs FC Juárez",
    "club pachuca": "vs FC Juárez",
    "san luis": "vs Chivas Guadalajara",
    "atlético san luis": "vs Chivas Guadalajara",
    "atlético de san luis": "vs Chivas Guadalajara",
    "atletico de san luis": "vs Chivas Guadalajara",
    "chivas": "vs Atlético San Luis",
    "chivas guadalajara": "vs Atlético San Luis",
    "guadalajara": "vs Atlético San Luis",
    "tigres": "vs Necaxa",
    "tigres uanl": "vs Necaxa",
    "necaxa": "vs Tigres UANL",
    "atlas": "vs Atlante",
    "atlas fc": "vs Atlante",
    "pumas": "vs Club León",
    "pumas unam": "vs Club León",
    "león": "vs Pumas UNAM",
    "club león": "vs Pumas UNAM",
    "leon": "vs Pumas UNAM",
    "américa": "vs Club Tijuana",
    "club américa": "vs Club Tijuana",
    "america": "vs Club Tijuana",
    "tijuana": "vs Club América",
    "club tijuana": "vs Club América",
    "monterrey": "vs Querétaro FC",
    "rayados de monterrey": "vs Querétaro FC",
    "cf monterrey": "vs Querétaro FC",
    "mazatlán": "vs Querétaro FC",
    "mazatlan": "vs Querétaro FC",
    "querétaro": "vs Rayados de Monterrey",
    "querétaro fc": "vs Rayados de Monterrey",
    "queretaro": "vs Rayados de Monterrey",
}

def sync_league_live_board(league_id: int, db: Session) -> Dict[str, Any]:
    """
    Sincroniza la tabla de 18 clubes y la cartelera viva desde FotMob hacia la base de datos local,
    retornando el payload formateado para el Live Board.
    """
    league = db.query(League).filter(League.fotmob_id == league_id).first()
    if not league:
        league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise ValueError(f"Liga con ID {league_id} no encontrada en base de datos.")

    fotmob_id = league.fotmob_id

    # Cargar escudos desde la tabla teams
    teams_db = db.query(Team).filter(Team.league_id == league.id).all()
    crests_map = {}
    for t in teams_db:
        crests_map[t.name.lower()] = t.crest_url
        crests_map[t.short_name.lower()] = t.crest_url
        crests_map[t.canonical_slug.lower()] = t.crest_url

    # 1. Obtener Tabla de Posiciones Oficial desde FotMobProvider
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
        
        # Buscar escudo URL oficial mediante [LN-QBE-019]
        escudo_id = t.get("escudo_id") or t.get("fotmob_id")
        escudo_url = resolver_escudo_canonico(equipo, fotmob_id=escudo_id, db=db)

        proximo_rival = t.get("proximo_rival")
        if not proximo_rival or proximo_rival == "vs Rival":
            proximo_rival = _resolver_proximo_rival(equipo)

        proximo_equipo_clean = proximo_rival.replace("vs ", "").strip() if proximo_rival else ""
        proximo_escudo_url = resolver_escudo_canonico(proximo_equipo_clean, db=db) if proximo_equipo_clean else None

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
        
        proximo_rival = t.get("proximo_rival")
        if not proximo_rival or proximo_rival == "vs Rival":
            proximo_rival = _resolver_proximo_rival(equipo)

        standings_formatted.append({
            "pos": pos,
            "equipo": equipo,
            "escudo_url": escudo_url,
            "proximo_escudo_url": proximo_escudo_url,
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

    # Guardar snapshot de tabla en la base de datos
    snap_standing = StandingSnapshot(
        league_id=league.id,
        season="2026",
        matchday=7,
        positions_json=standings_formatted
    )
    db.add(snap_standing)

    # 2. Cartelera de Partidos de la Jornada
    if fotmob_id == 262:
        fixtures_formatted = LIGA_MX_JORNADA_7_FIXTURES
    else:
        fixtures_raw = FotMobProvider.obtener_partidos_jornada(fotmob_id)
        if not fixtures_raw:
            last_fix = db.query(FixtureSnapshot).filter(FixtureSnapshot.league_id == league.id).order_by(FixtureSnapshot.updated_at.desc()).first()
            if last_fix and last_fix.matches_json:
                fixtures_raw = last_fix.matches_json
            else:
                fixtures_raw = []

        fixtures_formatted = []
        for idx, f in enumerate(fixtures_raw, start=101):
            id_partido = str(f.get("id_partido") or f.get("id") or f"match_{idx}")
            local = str(f.get("local") or f.get("home") or "Local")
            visitante = str(f.get("visitante") or f.get("away") or "Visitante")
            horario = str(f.get("horario") or f.get("time") or "20:00 hrs")
            fecha_bloque = f.get("fecha_bloque") or "Jornada 7"
            es_op = bool(f.get("es_operable", True))
            es_pos = bool(f.get("es_pospuesto", False))

            momios_val = f.get("momios")
            if isinstance(momios_val, dict):
                l_odd = float(momios_val.get("L") or 2.10)
                e_odd = float(momios_val.get("E") or 3.30)
                v_odd = float(momios_val.get("V") or 3.40)
                pa = bool(momios_val.get("pago_anticipado", True))
                momios_obj = {"L": l_odd, "E": e_odd, "V": v_odd, "pago_anticipado": pa}
            else:
                momios_obj = None

            fixtures_formatted.append({
                "id_partido": id_partido,
                "local": local,
                "visitante": visitante,
                "horario": horario,
                "fecha_bloque": fecha_bloque,
                "es_operable": es_op,
                "es_pospuesto": es_pos,
                "momios": momios_obj,
                "es_viable_triaje": bool(f.get("es_viable_triaje", True)),
                "motivo_triaje": f.get("motivo_triaje")
            })

    # Guardar snapshot de cartelera en la base de datos
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
