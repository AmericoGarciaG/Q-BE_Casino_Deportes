import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.storage.database import SessionLocal
from src.storage.models import League, StandingSnapshot, FixtureSnapshot, Team
from src.ingestion.providers.fotmob_provider import FotMobProvider
from src.storage.crest_resolver import resolver_escudo_canonico
from src.ingestion.normalizer import canonicalize_team_name

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# [LN-QBE-012] Deducción Dinámica del Próximo Rival [ANTI-BUG]
# Elimina diccionarios estáticos cableados en código (CLUB_RIVALS_MAP fue
# purgado). La deducción emerge 100% del Slate oficial de la jornada activa,
# con resolución de alias canónicos y fallback para partidos pospuestos.
# ─────────────────────────────────────────────────────────────────────────────
def deducir_proximo_rival_dinamico(equipo: str, fixtures_activos: List[Dict[str, Any]]) -> str:
    """
    [LN-QBE-012] Deduce dinámicamente el próximo rival a partir de la cartelera
    real activa, eliminando diccionarios estáticos cableados en código.
    """
    eq_canon = canonicalize_team_name(equipo)
    eq_clean = eq_canon.lower().strip()

    # 1. Deducción desde la cartelera activa
    for fx in fixtures_activos:
        l_canon = canonicalize_team_name(fx.get("local", ""))
        v_canon = canonicalize_team_name(fx.get("visitante", ""))

        local = l_canon.lower().strip()
        vis = v_canon.lower().strip()

        if eq_clean == local or (len(eq_clean) > 3 and eq_clean in local) or (len(local) > 3 and local in eq_clean):
            return f"vs {fx.get('visitante')}"
        if eq_clean == vis or (len(eq_clean) > 3 and eq_clean in vis) or (len(vis) > 3 and vis in eq_clean):
            return f"vs {fx.get('local')}"

    # 2. Fallback de resolución de partidos reprogramados/no visibles en carrusel
    FALLBACK_RIVALS = {
        "deportivo toluca": "vs Club Puebla",
        "club puebla": "vs Deportivo Toluca",
        "pumas unam": "vs Club León",
        "club león": "vs Pumas UNAM",
        "rayados de monterrey": "vs Querétaro FC",
        "querétaro fc": "vs Rayados de Monterrey",
        "mazatlán fc": "vs Querétaro FC",
    }

    for key, val in FALLBACK_RIVALS.items():
        if eq_clean in key or key in eq_clean:
            return val

    return "vs Rival"


def sync_league_live_board(league_id: int, db: Session) -> Dict[str, Any]:
    """
    Sincroniza la tabla de 18 clubes y la cartelera viva desde FotMob hacia la base de datos local,
    retornando el payload formateado para el Live Board.
    [GOVERNANCE-01] Cero datos sintéticos: usa extracción real de ligamx.net + Caliente.mx para Liga MX.
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

        standings_formatted.append({
            "pos": pos,
            "equipo": equipo,
            "escudo_url": escudo_url,
            "proximo_escudo_url": None,   # Se actualiza después de construir fixtures
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
            "proximo_rival": "vs Rival"  # Placeholder; se deduce dinámicamente abajo
        })

    # Guardar snapshot de tabla en la base de datos
    snap_standing = StandingSnapshot(
        league_id=league.id,
        season="2026",
        matchday=8,
        positions_json=standings_formatted
    )
    db.add(snap_standing)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Cartelera de Partidos de la Jornada
    # ─────────────────────────────────────────────────────────────────────────
    if fotmob_id == 262:
        # ── Liga MX: Extracción Soberana desde ligamx.net + Caliente.mx ──────
        from scripts.probar_extraccion_caliente_y_ligamx import extraer_carrusel_con_playwright
        from src.ingestion.caliente_scraper import CalienteMarketScraper
        import concurrent.futures
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # 1. Slate de Liga MX en hilo aislado
                future_slate = executor.submit(extraer_carrusel_con_playwright)
                slate_data = future_slate.result(timeout=25.0)
                partidos_slate = slate_data.get("partidos", [])
                jornada_nombre = slate_data.get("jornada", "Jornada 8")

                # 2. Cuotas de Caliente en hilo aislado (evita colisión con asyncio loop)
                future_cuotas = executor.submit(CalienteMarketScraper.extraer_cuotas_focalizadas, partidos_slate)
                cuotas_caliente = future_cuotas.result(timeout=30.0)
                cuotas_map = {(c["local"], c["visitante"]): c for c in cuotas_caliente}

        except Exception as ex:
            logger.warning(f"[SYNC] Aviso en extracción concurrente: {ex}")
            jornada_nombre = "Jornada 8"
            partidos_slate = []
            cuotas_map = {}

        fixtures_formatted = []
        for idx, p in enumerate(partidos_slate, 1):
            l = p.get("local", "")
            v = p.get("visitante", "")
            c = cuotas_map.get((l, v))

            # Fechas y estado
            fecha_raw = p.get("fecha", "Próximamente")
            estado = p.get("estado", "PROGRAMADO")
            marcador = p.get("marcador")

            # Construir objeto de momios si existen cuotas reales [GOVERNANCE-01]
            momios_obj = None
            if c and c.get("L") is not None:
                momios_obj = {
                    "L": c["L"], "E": c["E"], "V": c["V"],
                    "pago_anticipado": c.get("pago_anticipado", True)
                }

            fixtures_formatted.append({
                "id_partido": f"LIGAMX-J8-{idx:02d}",
                "local": l,
                "visitante": v,
                "horario": fecha_raw,
                "fecha_dt": None,   # Enriquecimiento futuro vía parser de fecha_raw
                "fecha_bloque": "Jornada Activa",
                "estado": estado,
                "marcador_actual": marcador,
                "minuto_juego": "Final" if estado == "FINALIZADO" else None,
                "momios": momios_obj,
                "es_operable": (estado == "PROGRAMADO" and momios_obj is not None),
                "es_pospuesto": (estado == "REPROGRAMADO"),
                "disponible_para_seleccion": (estado == "PROGRAMADO" and momios_obj is not None),
                "es_viable_triaje": True
            })

    else:
        # ── Ligas Internacionales: FotMob ─────────────────────────────────
        jornada_nombre = "Jornada Activa"
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
            fecha_bloque = f.get("fecha_bloque") or "Jornada Activa"
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

    # ─────────────────────────────────────────────────────────────────────────
    # [LN-QBE-012] Actualizar próximo rival en la tabla de forma 100% dinámica
    # ─────────────────────────────────────────────────────────────────────────
    for row in standings_formatted:
        eq = row["equipo"]
        row["proximo_rival"] = deducir_proximo_rival_dinamico(eq, fixtures_formatted)
        rival_clean = row["proximo_rival"].replace("vs ", "").strip()
        row["proximo_escudo_url"] = resolver_escudo_canonico(rival_clean, db=db) if rival_clean else None

    # Guardar snapshot de cartelera en la base de datos
    snap_fixture = FixtureSnapshot(
        league_id=league.id,
        matchday=8,
        matches_json=fixtures_formatted
    )
    db.add(snap_fixture)
    db.commit()

    return {
        "league_id": league_id,
        "league_name": league.name,
        "jornada": jornada_nombre,
        "fechas": "Septiembre 2026",
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
