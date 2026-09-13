# -*- coding: utf-8 -*-
"""
Kybern Industrial — Script 2: Diagnóstico Integral de Ingesta y Mercado (E2E)
Base de Gobierno: Kybern Framework v12.0
Responsabilidad: Extraer en vivo ligamx.net (Slate, Concluidos, Reprogramados),
FotMob (__NEXT_DATA__ forma 5P) y Caliente.mx (Cuotas focalizadas y PA).
"""
import os
import sys
import re
import time
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
from playwright.sync_api import sync_playwright

if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.ingestion.normalizer import canonicalize_team_name
from src.ingestion.caliente_scraper import CalienteMarketScraper
from src.storage.crest_resolver import STATIC_CRESTS_DIR
from src.storage.database import SessionLocal
from src.storage.models import StandingSnapshot, FixtureSnapshot, League

DB_PATH = os.path.join(PROJECT_ROOT, "data", "qbe_database.db")

HEADERS_CHROME = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-MX,es;q=0.9",
}

LIGAMX_LOGO_ID_MAP = {
    "1": "Club América", "2": "Atlas FC", "5": "Club Tijuana", "6": "Cruz Azul",
    "7": "Chivas Guadalajara", "9": "Club León", "11": "Club Pachuca", "12": "Club Puebla",
    "14": "Rayados de Monterrey", "15": "Santos Laguna", "16": "Tigres UANL", "17": "Deportivo Toluca",
    "18": "Pumas UNAM", "29": "Necaxa", "10445": "Atlas FC", "11220": "Atlético San Luis",
    "11550": "Club Puebla", "11790": "FC Juárez", "12043": "Mazatlán FC", "13668": "Querétaro FC",
    "14257": "Atlante"
}

def ejecutar_diagnostico_completo():
    print("\n" + "="*95)
    print("🌐 [SCRIPT 2] DIAGNÓSTICO INTEGRAL DE INGESTA DE MERCADO Y FEDERACIÓN (E2E)")
    print("="*95)

    partidos_slate = []
    jornada_nombre = "Jornada 8"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        context = browser.new_context(user_agent=HEADERS_CHROME["User-Agent"], locale="es-MX", viewport={"width": 1366, "height": 768})
        page = context.new_page()

        # ── 1. INGESTA DE LIGAMX.NET (SLATE, CONCLUIDOS Y REPROGRAMADOS) ──────
        try:
            print("📡 [1/3] Conectando a https://ligamx.net/ ...")
            page.goto("https://ligamx.net/", timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3500)

            # Cerrar popups
            page.evaluate("""() => {
                document.querySelectorAll('#ligamxPopup .close, .popup-overlay .close, .modal .close, [class*=close]').forEach(b => b.click());
                document.querySelectorAll('#ligamxPopup, .popup-overlay, .modal-backdrop').forEach(el => el.remove());
            }""")

            # Rollover si estuviera en J7 concluida
            content = page.content()
            if "JORNADA 7" in content and "MARCADOR OFICIAL" in content:
                fl = page.query_selector(".next, .carrusel-next, .slick-next, a:has-text('>')")
                if fl:
                    fl.click()
                    page.wait_for_timeout(2000)

            # Parsear tarjetas de jornada activa
            tarjetas = page.query_selector_all("li[id^='MrcdrPrtd_'], .barMarc, .slide, .item, .partido")
            for t in tarjetas:
                if not t.is_visible(): continue
                txt = t.inner_text().strip()
                txt_up = txt.upper()
                if not ("/" in txt and ":" in txt): continue
                if "REPROGRAMADO" in txt_up: continue

                estado = "PROGRAMADO"
                if "MARCADOR OFICIAL" in txt_up or "FINALIZADO" in txt_up:
                    estado = "FINALIZADO"
                elif "EN VIVO" in txt_up or "PRIMER TIEMPO" in txt_up or "SEGUNDO TIEMPO" in txt_up or "MEDIO TIEMPO" in txt_up:
                    estado = "EN_CURSO"

                # Marcador real multilínea
                marcador = None
                if estado in ["FINALIZADO", "EN_CURSO"]:
                    m_match = re.search(r'(?<!\d)(\d+)\s*\n*\s*[-–]\s*\n*\s*(\d+)(?!\d)', txt)
                    if m_match:
                        marcador = f"{m_match.group(1)} - {m_match.group(2)}"

                f_match = re.search(r'(\d{1,2}/\d{1,2})\s*(\d{1,2}:\d{2})\s*hr', txt)
                fecha_str = f_match.group(0) if f_match else "12/09 17:00 hr"

                # Extraer clubes
                imgs = t.query_selector_all("img")
                clubes = []
                for img in imgs:
                    alt = (img.get_attribute("alt") or img.get_attribute("title") or "").strip()
                    if alt and alt != "undefined" and len(alt) > 2:
                        c_clean = canonicalize_team_name(alt)
                        if c_clean and c_clean not in clubes: clubes.append(c_clean)

                if len(clubes) >= 2:
                    item = {"local": clubes[0], "visitante": clubes[1], "fecha": fecha_str, "estado": estado, "marcador": marcador, "es_pospuesto": False}
                    if not any(p["local"] == item["local"] and p["visitante"] == item["visitante"] for p in partidos_slate):
                        partidos_slate.append(item)

            print(f"  Partidos activos en jornada: {len(partidos_slate)}")

            # Activar y extraer PARTIDOS REPROGRAMADOS dinámicos
            page.evaluate("""() => {
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

                if ("JORNADA 7" in txt_up or "15/09" in txt or "28/10" in txt or "14/11" in txt or "REPROGRAMADO" in txt_up or "POSPUESTO" in txt_up or "PRÓXIMAMENTE" in txt_up):
                    f_match = re.search(r'(\d{1,2}/\d{1,2})\s*(\d{1,2}:\d{2})\s*hr', txt)
                    fecha_str = f_match.group(0) if f_match else "Fecha por Definir"

                    imgs = t.query_selector_all("img")
                    clubes_rep = []
                    for img in imgs:
                        src = img.get_attribute("src") or ""
                        alt = (img.get_attribute("alt") or img.get_attribute("title") or "").strip()
                        nom = None
                        if alt and alt != "undefined" and len(alt) > 2:
                            nom = canonicalize_team_name(alt)
                        else:
                            m_id = re.search(r'logos(?:64x64)?/(\d+)/', src)
                            if m_id and m_id.group(1) in LIGAMX_LOGO_ID_MAP:
                                nom = LIGAMX_LOGO_ID_MAP[m_id.group(1)]
                        if nom and nom not in clubes_rep: clubes_rep.append(nom)

                    if len(clubes_rep) >= 2:
                        item_r = {"local": clubes_rep[0], "visitante": clubes_rep[1], "fecha": fecha_str, "estado": "REPROGRAMADO", "marcador": None, "es_pospuesto": True}
                        if not any(p["local"] == item_r["local"] and p["visitante"] == item_r["visitante"] for p in partidos_slate):
                            partidos_slate.append(item_r)
                            print(f"  ⏳ [REPROGRAMADO] {item_r['local']} vs {item_r['visitante']} ({item_r['fecha']})")

        except Exception as e_fmf:
            print(f"⚠️ Error ligamx.net: {e_fmf}")

        # ── 2. INGESTA DE FOTMOB (__NEXT_DATA__ ID 230) ──────────────────────
        datos_fotmob = {}
        try:
            print("\n📡 [2/3] Conectando a FotMob (ID 230) para Forma 5P y Rival...")
            page.goto("https://www.fotmob.com/es-419/leagues/230/table/liga-mx", timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3500)

            next_data = page.query_selector("script#__NEXT_DATA__")
            if next_data:
                raw_json = json.loads(next_data.inner_text())
                table_obj = raw_json.get("props", {}).get("pageProps", {}).get("table", [{}])[0]
                teams_all = table_obj.get("data", {}).get("table", {}).get("all", [])
                team_form = table_obj.get("teamForm", {})
                next_opp = table_obj.get("nextOpponent", {})

                res_map = {"W": "G", "D": "E", "L": "P"}
                for tm in teams_all:
                    t_id = str(tm.get("id"))
                    t_name = canonicalize_team_name(tm.get("name", ""))
                    form_list = team_form.get(t_id, [])
                    forma = [res_map.get(str(m.get("resultString")).upper(), "E") for m in form_list if m.get("resultString")]
                    
                    opp_arr = next_opp.get(t_id, [])
                    opp_name = None
                    if opp_arr and len(opp_arr) >= 5:
                        h_t = opp_arr[3] if isinstance(opp_arr[3], dict) else {}
                        a_t = opp_arr[4] if isinstance(opp_arr[4], dict) else {}
                        opp_name = (a_t.get("name") or a_t.get("shortName")) if str(h_t.get("id")) == t_id else (h_t.get("name") or h_t.get("shortName"))
                    
                    datos_fotmob[t_name.lower().strip()] = {
                        "forma": forma[-5:] if len(forma) >= 5 else forma,
                        "rival": canonicalize_team_name(opp_name) if opp_name else None
                    }
                print(f"  Clubes con Forma 5P extraídos: {len(datos_fotmob)}")
        except Exception as e_fm:
            print(f"⚠️ Error FotMob: {e_fm}")

        # ── 3. CUOTAS CALIENTE.MX FOCALIZADAS ─────────────────────────────────
        browser.close()

    cuotas_caliente = []
    try:
        print("\n🎰 [3/3] Consultando Cuotas 1X2 y PA en Caliente.mx para el Slate...")
        cuotas_caliente = CalienteMarketScraper.extraer_cuotas_focalizadas(partidos_slate)
    except Exception as e_cal:
        print(f"⚠️ Error Caliente: {e_cal}")

    # ── 4. CLASIFICACIÓN Y DESPLIEGUE EN 4 GRUPOS ───────────────────────────
    cuotas_map = {(c["local"], c["visitante"]): c for c in cuotas_caliente}
    ahora = datetime.now()
    hoy_date = ahora.date()

    grupos = {"1_EN_VIVO": [], "2_PROGRAMADOS": [], "3_FINALIZADOS": [], "4_LEJANOS_REPROG": []}
    dias_semana = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}

    for p in partidos_slate:
        l = p["local"]
        v = p["visitante"]
        c = cuotas_map.get((l, v)) or cuotas_map.get((v, l))
        estado = p.get("estado", "PROGRAMADO")
        fecha_raw = p.get("fecha", "12/09 17:00 hr")

        m_f = re.search(r'(\d{1,2})/(\d{1,2})\s*(\d{1,2}):(\d{2})', fecha_raw)
        dia, mes, hora, minuto = (int(m_f.group(1)), int(m_f.group(2)), int(m_f.group(3)), int(m_f.group(4))) if m_f else (12, 9, 19, 0)
        dt_p = datetime(2026, mes, dia, hora, minuto)
        
        es_pospuesto = p.get("es_pospuesto", False) or (mes > 9) or (dia > 15 and mes == 9) or (dt_p.date() - hoy_date).days > 7
        if es_pospuesto: estado = "REPROGRAMADO"

        tiene_cuotas = (c is not None and c.get("L") is not None)
        # [LEY DE OPERABILIDAD TOTAL]: Si no ha terminado y tiene cuotas -> es operable
        es_operable = (estado != "FINALIZADO" and tiene_cuotas)

        item = {
            "partido": f"{l} vs {v}",
            "fecha": f"{dias_semana.get(dt_p.weekday(),'Día')} {dia:02d} ({fecha_raw})",
            "dt": dt_p,
            "estado": estado,
            "marcador": p.get("marcador") or "—",
            "L": f"{c['L']:.2f}" if tiene_cuotas else "—",
            "E": f"{c['E']:.2f}" if tiene_cuotas else "—",
            "V": f"{c['V']:.2f}" if tiene_cuotas else "—",
            "pa": "✅ ACTIVO" if (c and c.get("pago_anticipado")) else "❌ NO",
            "operabilidad": "✅ [OPERABLE]" if es_operable else ("🏁 [CONCLUIDO]" if estado == "FINALIZADO" else "⏳ [SIN CUOTAS]")
        }

        if estado == "EN_CURSO": grupos["1_EN_VIVO"].append(item)
        elif estado == "FINALIZADO": grupos["3_FINALIZADOS"].append(item)
        elif es_pospuesto: grupos["4_LEJANOS_REPROG"].append(item)
        else: grupos["2_PROGRAMADOS"].append(item)

    for g in grupos: grupos[g] = sorted(grupos[g], key=lambda x: x["dt"])

    # Imprimir tablas ejecutivas en consola
    print("\n" + "="*105)
    print(f"📊 RESUMEN EJECUTIVO: CARTELERA ACTIVA — {jornada_nombre}")
    print("="*105)

    _imprimir_g("🔴 [GRUPO 1: EN VIVO / EN JUEGO AHORA]", grupos["1_EN_VIVO"])
    _imprimir_g("🟢 [GRUPO 2: PRÓXIMOS OPERABLES (PRE-PARTIDO)]", grupos["2_PROGRAMADOS"])
    _imprimir_g("🏁 [GRUPO 3: FINALIZADOS (CONCLUIDOS CON MARCADOR REAL)]", grupos["3_FINALIZADOS"])
    _imprimir_g("⏳ [GRUPO 4: REPROGRAMADOS / FECHA LEJANA]", grupos["4_LEJANOS_REPROG"])

    # ── 5. ACTUALIZAR SQLITE (STANDINGS CON FORMA REAL Y SNAPSHOTS) ─────────
    if os.path.exists(DB_PATH) and datos_fotmob:
        db = SessionLocal()
        try:
            snap = db.query(StandingSnapshot).order_by(StandingSnapshot.captured_at.desc()).first()
            if snap and snap.positions_json:
                pos_list = list(snap.positions_json)
                for row in pos_list:
                    k = canonicalize_team_name(row["equipo"]).lower().strip()
                    if k in datos_fotmob:
                        if datos_fotmob[k]["forma"]: row["forma"] = datos_fotmob[k]["forma"]
                        if datos_fotmob[k]["rival"]:
                            row["proximo_rival"] = datos_fotmob[k]["rival"]
                            r_slug = canonicalize_team_name(datos_fotmob[k]["rival"]).lower().replace(" ", "-").replace(".", "")
                            row["proximo_escudo_url"] = f"/static/img/crests/{r_slug}.png"
                snap.positions_json = pos_list
                db.commit()
                print("\n💾 [DATABASE] SQLite actualizado: StandingSnapshot contiene Forma y Rivales 100% reales.")
        finally:
            db.close()

def _imprimir_g(titulo, lista):
    print(f"\n{titulo}")
    print("-" * 105)
    if not lista:
        print("   (Ningún partido en este grupo)")
        return
    print(f"   {'FECHA':<24} | {'PARTIDO':<32} | {'MARCADOR':<8} | {'L':^6} | {'E':^6} | {'V':^6} | {'PA':^8} | {'ESTADO OPERATIVO'}")
    print("   " + "-" * 102)
    for i in lista:
        print(f"   {i['fecha']:<24} | {i['partido']:<32} | {i['marcador']:<8} | {i['L']:^6} | {i['E']:^6} | {i['V']:^6} | {i['pa']:^8} | {i['operabilidad']}")

if __name__ == "__main__":
    ejecutar_diagnostico_completo()
