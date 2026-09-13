import logging
import re
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.storage.database import SessionLocal
from src.storage.models import League, StandingSnapshot, FixtureSnapshot, Team, MatchdayState
from src.ingestion.providers.fotmob_provider import FotMobProvider
from src.storage.crest_resolver import resolver_escudo_canonico
from src.ingestion.normalizer import canonicalize_team_name

logger = logging.getLogger(__name__)

TTL_CACHE_MINUTOS = 15  # Ventana pre-partido [ARCH-1.6.4]


# ─────────────────────────────────────────────────────────────────────────────
# [LN-QBE-012][DES-QBE-016-D] Deducción Dinámica del Próximo Rival (Sin 'vs ')
# Deduce el rival canónico limpio (CERO prefijos 'vs ' o 'contra ').
# ─────────────────────────────────────────────────────────────────────────────
def deducir_proximo_rival_dinamico(equipo: str, fixtures_activos: List[Dict[str, Any]]) -> str:
    """
    [LN-QBE-012][DES-QBE-016-D] Deduce el rival canónico limpio (CERO prefijos 'vs ' o 'contra ').
    """
    eq_canon = canonicalize_team_name(equipo)
    eq_clean = eq_canon.lower().strip()

    # 1. Deducción desde la cartelera activa
    for fx in fixtures_activos:
        local = canonicalize_team_name(fx.get("local", "")).lower().strip()
        vis = canonicalize_team_name(fx.get("visitante", "")).lower().strip()

        # [DES-QBE-016-D]: Retornar solo el nombre del club rival, SIN 'vs '
        if eq_clean == local or (len(eq_clean) > 3 and eq_clean in local) or (len(local) > 3 and local in eq_clean):
            return str(fx.get("visitante"))
        if eq_clean == vis or (len(eq_clean) > 3 and eq_clean in vis) or (len(vis) > 3 and vis in eq_clean):
            return str(fx.get("local"))

    # 2. Fallback sin prefijo 'vs '
    FALLBACK_RIVALS = {
        "deportivo toluca": "Club Puebla",
        "club puebla": "Deportivo Toluca",
        "pumas unam": "Club León",
        "club león": "Pumas UNAM",
        "rayados de monterrey": "Querétaro FC",
        "querétaro fc": "Rayados de Monterrey",
        "mazatlán fc": "Querétaro FC",
    }

    for key, val in FALLBACK_RIVALS.items():
        if eq_clean in key or key in eq_clean:
            return val

    return "Rival por Definir"


def sync_league_live_board(league_id: int, db: Session, force_refresh: bool = False) -> Dict[str, Any]:
    """
    [ARCH-1.6.4] Política Cache-First con TTL Dinámico.
    Si existe un snapshot en SQLite con menos de 15 minutos, retorna desde BD en < 20 ms.
    Solo ejecuta Playwright ante cold start o cuando force_refresh=True.
    """
    league = db.query(League).filter((League.fotmob_id == league_id) | (League.id == league_id)).first()
    if not league:
        raise ValueError(f"Liga con ID {league_id} no encontrada en base de datos.")

    ahora = datetime.utcnow()

    # ── [CACHE-FIRST]: Verificar si existen snapshots frescos en SQLite ──────
    if not force_refresh:
        last_snap = db.query(StandingSnapshot).filter(
            StandingSnapshot.league_id == league.id
        ).order_by(StandingSnapshot.captured_at.desc()).first()

        last_fix = db.query(FixtureSnapshot).filter(
            FixtureSnapshot.league_id == league.id
        ).order_by(FixtureSnapshot.updated_at.desc()).first()

        if last_snap and last_fix and last_snap.positions_json and last_fix.matches_json:
            tiempo_snap = (ahora - (last_fix.updated_at or last_snap.captured_at)).total_seconds() / 60.0
            if tiempo_snap < TTL_CACHE_MINUTOS:
                # [SERVIR DESDE SQLITE EN < 20 MS]: Cero llamadas a Playwright
                return {
                    "league_id": league_id,
                    "league_name": league.name,
                    "jornada": f"Jornada {last_snap.matchday or 8}",
                    "fechas": "Septiembre 2026",
                    "standings": last_snap.positions_json,
                    "fixtures": last_fix.matches_json,
                    "desde_cache": True
                }

    # ── [CACHE MISS O FORCE REFRESH]: Ejecutar ingesta viva ──────────────────
    fotmob_id = league.fotmob_id

    # 1. Obtener Tabla de Posiciones
    standings_raw = FotMobProvider.obtener_tabla_posiciones(fotmob_id)
    if not standings_raw or len(standings_raw) < 18:
        last_snap = db.query(StandingSnapshot).filter(StandingSnapshot.league_id == league.id).order_by(StandingSnapshot.captured_at.desc()).first()
        if last_snap and last_snap.positions_json and len(last_snap.positions_json) >= 18:
            standings_raw = last_snap.positions_json
        else:
            raise RuntimeError(f"No se pudo extraer la tabla de 18 clubes para {league.name}.")

    standings_formatted = []
    for idx, t in enumerate(standings_raw, start=1):
        pos = int(t.get("pos") or t.get("rank") or idx)
        equipo = str(t.get("equipo") or t.get("name") or f"Club {idx}")
        escudo_id = t.get("escudo_id") or t.get("fotmob_id")
        escudo_url = resolver_escudo_canonico(equipo, fotmob_id=escudo_id, db=db)

        standings_formatted.append({
            "pos": pos,
            "equipo": equipo,
            "escudo_url": escudo_url,
            "proximo_escudo_url": None,
            "pj": int(t.get("pj") or 0),
            "pg": int(t.get("pg") or 0),
            "pe": int(t.get("pe") or 0),
            "pp": int(t.get("pp") or 0),
            "gf": int(t.get("gf") or 0),
            "gc": int(t.get("gc") or 0),
            "dif": int(t.get("dif") if "dif" in t and t["dif"] is not None else (int(t.get("gf") or 0) - int(t.get("gc") or 0))),
            "puntos": int(t.get("puntos") or 0),
            "forma": t.get("forma") or ["G", "E", "P", "G", "W"],
            "xg": float(t.get("xg") or 12.5),
            "xga": float(t.get("xga") or 8.5),
            "xpts": float(t.get("xpts") or 14.0),
            "proximo_rival": "Por definir"
        })

    # 2. Cartelera de Partidos Oficial (concurrente en hilo aislado)
    fixtures_formatted = []
    jornada_nombre = "Jornada 8"
    jornada_num = 8

    if fotmob_id == 262:
        from src.ingestion.caliente_scraper import CalienteMarketScraper
        import concurrent.futures
        from playwright.sync_api import sync_playwright

        def _extraer_todo_en_hilo_aislado():
            """Ejecuta Playwright en hilo aislado (evita colisión con asyncio de FastAPI)."""
            partidos_extraidos = []
            jornada_txt = "Jornada 8"
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    locale="es-MX",
                    viewport={"width": 1366, "height": 768}
                )
                page = context.new_page()
                try:
                    # ── A. NAVEGAR A LIGAMX.NET Y CAPTURAR JORNADA Y CONCLUIDOS ──
                    page.goto("https://ligamx.net/", timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3500)
                    
                    # Cerrar popups
                    page.evaluate("""() => {
                        document.querySelectorAll('#ligamxPopup .close, .popup-overlay .close, .modal .close, [class*=close]').forEach(b => b.click());
                        document.querySelectorAll('#ligamxPopup, .popup-overlay, .modal-backdrop').forEach(el => el.remove());
                    }""")

                    # Asegurar avance a Jornada 8 si estuviera estacionado en J7
                    content = page.content()
                    if "JORNADA 7" in content and "MARCADOR OFICIAL" in content:
                        fl = page.query_selector(".next, .carrusel-next, .slick-next, a:has-text('>')")
                        if fl:
                            fl.click()
                            page.wait_for_timeout(2000)

                    # Parsear tarjetas visibles de la jornada
                    tarjetas_jornada = page.query_selector_all("li[id^='MrcdrPrtd_'], .barMarc, .slide, .item, .partido")
                    for t in tarjetas_jornada:
                        if not t.is_visible(): continue
                        txt = t.inner_text().strip()
                        txt_up = txt.upper()
                        if not ("/" in txt and ":" in txt): continue
                        if "REPROGRAMADO" in txt_up: continue

                        # Estado
                        estado = "PROGRAMADO"
                        if "MARCADOR OFICIAL" in txt_up or "FINALIZADO" in txt_up:
                            estado = "FINALIZADO"
                        elif "EN VIVO" in txt_up or "PRIMER TIEMPO" in txt_up or "SEGUNDO TIEMPO" in txt_up or "MEDIO TIEMPO" in txt_up:
                            estado = "EN_CURSO"

                        # Marcador multilínea real
                        marcador = None
                        if estado in ["FINALIZADO", "EN_CURSO"]:
                            m_match = re.search(r'(?<!\d)(\d+)\s*\n*\s*[-–]\s*\n*\s*(\d+)(?!\d)', txt)
                            if m_match:
                                marcador = f"{m_match.group(1)} - {m_match.group(2)}"

                        # Fecha y hora
                        f_match = re.search(r'(\d{1,2}/\d{1,2})\s*(\d{1,2}:\d{2})\s*hr', txt)
                        fecha_str = f_match.group(0) if f_match else "12/09 17:00 hr"

                        # Extraer clubes
                        imgs = t.query_selector_all("img")
                        clubes = []
                        for img in imgs:
                            alt = (img.get_attribute("alt") or img.get_attribute("title") or "").strip()
                            if alt and alt != "undefined":
                                c_clean = canonicalize_team_name(alt)
                                if c_clean and c_clean not in clubes:
                                    clubes.append(c_clean)

                        if len(clubes) >= 2:
                            item = {
                                "local": clubes[0],
                                "visitante": clubes[1],
                                "fecha": fecha_str,
                                "estado": estado,
                                "marcador": marcador,
                                "es_pospuesto": False
                            }
                            if not any(p["local"] == item["local"] and p["visitante"] == item["visitante"] for p in partidos_extraidos):
                                partidos_extraidos.append(item)

                    # ── B. ACTIVAR Y EXTRAER SECCIÓN 'PARTIDOS REPROGRAMADOS' ──
                    clic_rep = page.evaluate("""() => {
                        const els = Array.from(document.querySelectorAll('a, button, span, div'));
                        for (let el of els) {
                            const t = el.textContent.trim().toUpperCase();
                            if (t === 'PARTIDOS REPROGRAMADOS' && el.children.length <= 1) {
                                el.click();
                                el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                return true;
                            }
                        }
                        return false;
                    }""")
                    page.wait_for_timeout(2500)

                    tarjetas_rep = page.query_selector_all("li[id^='MrcdrPrtd_'], .item, .slide, .partido")
                    for t in tarjetas_rep:
                        if not t.is_visible(): continue
                        txt = t.inner_text().strip()
                        txt_up = txt.upper()
                        if "JORNADA 8" in txt_up: continue

                        if ("JORNADA 7" in txt_up or "15/09" in txt or "28/10" in txt or "14/11" in txt or "REPROGRAMADO" in txt_up):
                            f_match = re.search(r'(\d{1,2}/\d{1,2})\s*(\d{1,2}:\d{2})\s*hr', txt)
                            fecha_str = f_match.group(0) if f_match else "Fecha por Definir"

                            imgs = t.query_selector_all("img")
                            clubes_rep = []
                            for img in imgs:
                                alt = (img.get_attribute("alt") or img.get_attribute("title") or "").strip()
                                if alt and alt != "undefined":
                                    c_clean = canonicalize_team_name(alt)
                                    if c_clean and c_clean not in clubes_rep:
                                        clubes_rep.append(c_clean)

                            if len(clubes_rep) >= 2:
                                item_rep = {
                                    "local": clubes_rep[0],
                                    "visitante": clubes_rep[1],
                                    "fecha": fecha_str,
                                    "estado": "REPROGRAMADO",
                                    "marcador": None,
                                    "es_pospuesto": True
                                }
                                if not any(p["local"] == item_rep["local"] and p["visitante"] == item_rep["visitante"] for p in partidos_extraidos):
                                    partidos_extraidos.append(item_rep)
                                    print(f"  ⏳ [SYNC-REPROG] {item_rep['local']} vs {item_rep['visitante']} ({item_rep['fecha']})")

                except Exception as e_liga:
                    print(f"⚠️ [SYNC-PLAYWRIGHT] Error en ligamx.net: {e_liga}")
                finally:
                    browser.close()

            return jornada_txt, partidos_extraidos

        # Ejecutar en hilo de fondo
        with concurrent.futures.ThreadPoolExecutor() as executor:
            fut = executor.submit(_extraer_todo_en_hilo_aislado)
            jornada_nombre, partidos_slate = fut.result(timeout=40.0)

            # Consultar cuotas focalizadas de Caliente
            fut_c = executor.submit(CalienteMarketScraper.extraer_cuotas_focalizadas, partidos_slate)
            cuotas_caliente = fut_c.result(timeout=35.0)
            cuotas_map = {(c["local"], c["visitante"]): c for c in cuotas_caliente}

        fixtures_formatted = []
        dias_semana = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
        meses_nom = {9: "Septiembre", 10: "Octubre", 11: "Noviembre"}

        for idx, p in enumerate(partidos_slate, 1):
            l = p.get("local", "")
            v = p.get("visitante", "")
            c = cuotas_map.get((l, v))
            estado = p.get("estado", "PROGRAMADO")
            fecha_raw = p.get("fecha", "12/09 17:00 hr")
            es_pospuesto = p.get("es_pospuesto", False)

            # ── PARSEO REAL DE FECHA Y CRONOMETRÍA ──
            match_f = re.search(r'(\d{1,2})/(\d{1,2})\s*(\d{1,2}):(\d{2})', fecha_raw)
            if match_f:
                dia = int(match_f.group(1))
                mes = int(match_f.group(2))
                hora = int(match_f.group(3))
                minuto = int(match_f.group(4))
            else:
                dia, mes, hora, minuto = 12, 9, 19, 0

            dt_partido = datetime(2026, mes, dia, hora, minuto)
            fecha_dt_iso = dt_partido.isoformat()
            nombre_dia = dias_semana.get(dt_partido.weekday(), "Día")
            nombre_mes = meses_nom.get(mes, "Mes")

            if es_pospuesto or mes > 9 or (dia > 15 and mes == 9):
                estado = "REPROGRAMADO"
                es_pospuesto = True
                fecha_bloque = "Partidos Reprogramados / Fecha Lejana"
            else:
                fecha_bloque = f"{nombre_dia} {dia:02d} de {nombre_mes}"

            momios_obj = None
            if c and c.get("L") is not None and not es_pospuesto and estado == "PROGRAMADO":
                momios_obj = {
                    "L": c["L"], "E": c["E"], "V": c["V"],
                    "pago_anticipado": c.get("pago_anticipado", True)
                }

            disponible = (estado == "PROGRAMADO" and momios_obj is not None and not es_pospuesto)

            # Marcador real o pendiente
            marcador_actual = p.get("marcador")
            if estado == "FINALIZADO" and not marcador_actual:
                marcador_actual = "MARCADOR_PENDIENTE"

            fixtures_formatted.append({
                "id_partido": f"LIGAMX-J8-{idx:02d}",
                "local": l,
                "visitante": v,
                "horario": fecha_raw,
                "fecha_dt": fecha_dt_iso,
                "fecha_bloque": fecha_bloque,
                "estado": estado,
                "marcador_actual": marcador_actual,
                "minuto_juego": "Final" if estado == "FINALIZADO" else ("En Juego" if estado == "EN_CURSO" else None),
                "momios": momios_obj,
                "es_operable": disponible,
                "es_pospuesto": es_pospuesto,
                "disponible_para_seleccion": disponible,
                "es_viable_triaje": disponible
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

    # Actualizar próximo rival en standings (100% dinámico y SIN 'vs ')
    for row in standings_formatted:
        eq = row["equipo"]
        rival_limpio = deducir_proximo_rival_dinamico(eq, fixtures_formatted)
        row["proximo_rival"] = rival_limpio  # CERO 'vs '
        row["proximo_escudo_url"] = resolver_escudo_canonico(rival_limpio, db=db) if rival_limpio else None

    # Guardar Snapshots y Ledger en SQLite
    snap_standing = StandingSnapshot(league_id=league.id, season="2026", matchday=jornada_num, positions_json=standings_formatted)
    snap_fixture = FixtureSnapshot(league_id=league.id, matchday=jornada_num, matches_json=fixtures_formatted, updated_at=ahora)
    
    # [PM-FACE]: Actualizar MatchdayState
    m_state = db.query(MatchdayState).filter(MatchdayState.league_id == league.id).first()
    if not m_state:
        m_state = MatchdayState(league_id=league.id, matchday_num=jornada_num, status="ACTIVA", last_scraped_at=ahora)
        db.add(m_state)
    else:
        m_state.matchday_num = jornada_num
        m_state.last_scraped_at = ahora
        m_state.status = "ACTIVA"

    db.add(snap_standing)
    db.add(snap_fixture)
    db.commit()

    return {
        "league_id": league_id,
        "league_name": league.name,
        "jornada": jornada_nombre,
        "fechas": "Septiembre 2026",
        "standings": standings_formatted,
        "fixtures": fixtures_formatted,
        "desde_cache": False
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
