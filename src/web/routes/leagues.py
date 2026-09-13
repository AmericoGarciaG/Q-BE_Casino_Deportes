from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from src.storage.database import get_db
from src.storage.models import League
from src.storage.sync_service import sync_league_live_board
from src.storage.crest_resolver import resolver_escudo_canonico
from src.models.web_schemas import LeagueOut, LiveBoardOut, MatchFixtureOut

router = APIRouter(prefix="/api/leagues", tags=["Leagues & Live Board"])


@router.get("", response_model=List[LeagueOut])
@router.get("/", response_model=List[LeagueOut], include_in_schema=False)
def get_leagues(db: Session = Depends(get_db)):
    """Retorna todas las ligas activas registradas en SQLite."""
    leagues = db.query(League).filter(League.is_active == True).all()
    return leagues


# [ARCH-1.6.3] Orden de prioridad topológica inmutable
_ORDEN_TOPOLOGICO = {"EN_CURSO": 1, "PROGRAMADO": 2, "REPROGRAMADO": 3, "FINALIZADO": 4}


@router.get("/{league_id}/live-board", response_model=LiveBoardOut)
def get_live_board(
    league_id: int,
    force_refresh: bool = Query(default=False),
    db: Session = Depends(get_db)
):
    """
    [ARCH-1.6.4] Cache-First: responder en < 25ms si el snapshot está fresco.
    Solo ejecuta Playwright ante cold start o cuando force_refresh=True.
    Aplica la Máquina de Estados [ARCH-1.6.3]: clasifica cada fixture como
    PROGRAMADO / EN_CURSO / FINALIZADO / REPROGRAMADO, evalúa es_hoy de forma
    dinámica y aplica el Ordenamiento Topológico canónico antes de retornar.
    """
    try:
        board_data = sync_league_live_board(league_id, db, force_refresh=force_refresh)

        # ── Resolver escudos de la tabla de posiciones ─────────────────────
        standings = board_data.get("standings", [])
        for row in standings:
            equipo = row.get("equipo", "")
            fotmob_id = row.get("fotmob_id")
            row["escudo_url"] = resolver_escudo_canonico(equipo, fotmob_id=fotmob_id, db=db)
            rival_limpio = row.get("proximo_rival", "")
            if rival_limpio and rival_limpio != "Por definir":
                row["proximo_escudo_url"] = resolver_escudo_canonico(rival_limpio, db=db)

        # ── Procesar fixtures con Máquina de Estados [ARCH-1.6.3] ─────────
        ahora = datetime.now()
        hoy_date = ahora.date()
        fixtures_raw = board_data.get("fixtures", [])
        fixtures_procesados: List[MatchFixtureOut] = []

        for fx in fixtures_raw:
            # Parsear fecha_dt ISO 8601
            dt_partido = None
            fecha_dt_str = fx.get("fecha_dt")
            if fecha_dt_str:
                try:
                    dt_partido = datetime.fromisoformat(fecha_dt_str)
                except (ValueError, TypeError):
                    pass

            # Calcular es_hoy de forma strictly dinámica [ARCH-1.6.3]
            es_hoy = (dt_partido.date() == hoy_date) if dt_partido else False

            # Leer estado declarado en el catálogo; si hay fecha_dt, validar
            # contra el Axioma Anti-Degradación [GOVERNANCE-01]
            estado = fx.get("estado", "PROGRAMADO")
            marcador = fx.get("marcador_actual")
            minuto = fx.get("minuto_juego")

            if dt_partido and estado not in ("REPROGRAMADO", "FINALIZADO", "EN_CURSO"):
                dif_horas = (ahora - dt_partido).total_seconds() / 3600.0
                if dif_horas > 2.5:
                    estado = "FINALIZADO"
                    if not marcador:
                        marcador = "MARCADOR_PENDIENTE"  # CERO "0 - 0" INVENTADOS
                    if not minuto:
                        minuto = "Final"
                elif dif_horas >= 0:
                    estado = "EN_CURSO"
                    if not minuto:
                        minuto = "En Juego"

            # Resolver escudos de ambos equipos [ARCH-1.5.3]
            local_escudo = resolver_escudo_canonico(fx.get("local", ""), db=db)
            vis_escudo = resolver_escudo_canonico(fx.get("visitante", ""), db=db)

            # Construir momios tipados si existen
            momios_raw = fx.get("momios")
            momios_obj = None
            if isinstance(momios_raw, dict) and momios_raw.get("L"):
                from src.models.web_schemas import Odds1X2
                try:
                    momios_obj = Odds1X2(
                        L=float(momios_raw["L"]),
                        E=float(momios_raw["E"]),
                        V=float(momios_raw["V"]),
                        pago_anticipado=bool(momios_raw.get("pago_anticipado", True))
                    )
                except Exception:
                    momios_obj = None

            # [CORRECCIÓN FINANCIERA]: Solo es operable si está PROGRAMADO Y TIENE CUOTAS REALES
            disponible = (estado == "PROGRAMADO" and momios_obj is not None)
            es_operable = disponible
            es_pospuesto = bool(fx.get("es_pospuesto", estado == "REPROGRAMADO"))

            fixtures_procesados.append(MatchFixtureOut(
                id_partido=fx.get("id_partido", ""),
                local=fx.get("local", ""),
                visitante=fx.get("visitante", ""),
                local_escudo_url=local_escudo,
                visitante_escudo_url=vis_escudo,
                horario=fx.get("horario", ""),
                fecha_dt=dt_partido.isoformat() if dt_partido else None,
                fecha_bloque=fx.get("fecha_bloque"),
                momios=momios_obj,
                es_viable_triaje=bool(fx.get("es_viable_triaje", True)),
                motivo_triaje=fx.get("motivo_triaje"),
                estado=estado,
                marcador_actual=marcador,
                minuto_juego=minuto,
                es_hoy=es_hoy,
                disponible_para_seleccion=disponible,
                es_operable=es_operable,
                es_pospuesto=es_pospuesto,
            ))

        # ── Ordenamiento Topológico [ARCH-1.6.3] ──────────────────────────
        fixtures_ordenados = sorted(
            fixtures_procesados,
            key=lambda x: (
                _ORDEN_TOPOLOGICO.get(x.estado, 99),
                x.fecha_dt or "9999-99-99"
            )
        )

        return {
            "league_id": board_data.get("league_id", league_id),
            "league_name": board_data.get("league_name", ""),
            "jornada": board_data.get("jornada", ""),
            "fechas": board_data.get("fechas", ""),
            "standings": standings,
            "fixtures": [f.model_dump() for f in fixtures_ordenados],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
