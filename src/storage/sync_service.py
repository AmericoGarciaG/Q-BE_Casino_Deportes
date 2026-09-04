import logging
from src.storage.database import SessionLocal
from src.storage.models import League, StandingSnapshot, FixtureSnapshot
from src.ingestion.providers.fotmob_provider import FotMobProvider

logger = logging.getLogger(__name__)

def sync_active_leagues_data():
    """Consulta FotMob y almacena en BD la tabla de posiciones y cartelera activa."""
    db = SessionLocal()
    try:
        active_leagues = db.query(League).filter(League.is_active == True).all()
        for league in active_leagues:
            print(f"🔄 [SYNC-STARTUP]: Sincronizando datos vivos para {league.name} (FotMob ID: {league.fotmob_id})...")
            
            # 1. Obtener tabla oficial
            tabla = FotMobProvider.obtener_tabla_posiciones(league.fotmob_id)
            if tabla and len(tabla) >= 18:
                snapshot = StandingSnapshot(
                    league_id=league.id,
                    season="2026",
                    matchday=7,
                    positions_json=tabla
                )
                db.add(snapshot)
                print(f"   ✅ [SYNC-OK]: Tabla de {len(tabla)} clubes guardada en BD.")
            else:
                print(f"   ⚠️ [SYNC-INFO]: Tabla obtenida con {len(tabla) if tabla else 0} clubes.")
                if tabla:
                    snapshot = StandingSnapshot(
                        league_id=league.id,
                        season="2026",
                        matchday=7,
                        positions_json=tabla
                    )
                    db.add(snapshot)
                    print(f"   ✅ [SYNC-OK]: Tabla guardada en BD.")

            # 2. Obtener cartelera
            partidos = FotMobProvider.obtener_partidos_jornada(league.fotmob_id)
            if partidos:
                f_snap = FixtureSnapshot(
                    league_id=league.id,
                    matchday=7,
                    matches_json=partidos
                )
                db.add(f_snap)
                print(f"   ✅ [SYNC-OK]: {len(partidos)} partidos de jornada guardados en BD.")

            db.commit()
    except Exception as e:
        logger.error(f"Error en sincronización startup: {e}")
        db.rollback()
    finally:
        db.close()
