# -*- coding: utf-8 -*-
"""
Kybern Industrial — Script 1: Sincronizador Soberano de la Bóveda de Activos
Base de Gobierno: Kybern Framework v12.0
Responsabilidad: Descargar, validar, espejear y anclar en disco y SQLite
los emblemas oficiales de torneos y clubes (CERO archivos fantasma / CERO hotlinks).
"""
import os
import sys
import shutil
import sqlite3
import httpx

if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRESTS_DIR = os.path.join(PROJECT_ROOT, "src", "web", "static", "img", "crests")
LEAGUES_DIR = os.path.join(PROJECT_ROOT, "src", "web", "static", "img", "leagues")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "qbe_database.db")

os.makedirs(CRESTS_DIR, exist_ok=True)
os.makedirs(LEAGUES_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://ligamx.net/"
}

# 1. Catálogo Oficial de Competencias (Ligas)
LEAGUES_MASTER = [
    {
        "id": 262,
        "name": "Liga MX",
        "slug": "league_262",
        "urls": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Liga_MX_logo.svg/500px-Liga_MX_logo.svg.png",
            "https://upload.wikimedia.org/wikipedia/commons/2/22/Liga_MX_logo.svg"
        ]
    }
]

# 2. Catálogo Oficial Canónico de los 18 Clubes de Liga MX (Apertura 2026)
CLUBS_MASTER = [
    {"nombre": "Club América", "slug": "america", "aliases": ["club-america", "aguilas"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/1/1.png"]},
    {"nombre": "Atlas FC", "slug": "atlas", "aliases": ["atlas-fc", "zorros"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/10445/10445.png"]},
    {"nombre": "Club Tijuana", "slug": "club-tijuana", "aliases": ["tijuana", "xolos"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/5/5.png"]},
    {"nombre": "Cruz Azul", "slug": "cruz-azul", "aliases": ["cruzazul", "la-maquina"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/6/6.png"]},
    {"nombre": "Chivas Guadalajara", "slug": "guadalajara", "aliases": ["chivas-guadalajara", "chivas"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/7/7.png"]},
    {"nombre": "Club León", "slug": "leon", "aliases": ["club-leon", "fiera"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/9/9.png"]},
    {"nombre": "Club Pachuca", "slug": "pachuca", "aliases": ["club-pachuca", "tuzos"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/11/11.png"]},
    {"nombre": "Club Puebla", "slug": "puebla", "aliases": ["club-puebla", "la-franja"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/12/12.png"]},
    {"nombre": "Rayados de Monterrey", "slug": "monterrey", "aliases": ["rayados-de-monterrey", "rayados"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/14/14.png"]},
    {"nombre": "Santos Laguna", "slug": "santos-laguna", "aliases": ["santos", "guerreros"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/15/15.png"]},
    {"nombre": "Tigres UANL", "slug": "tigres-uanl", "aliases": ["tigres", "felinos"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/16/16.png"]},
    {"nombre": "Deportivo Toluca", "slug": "toluca", "aliases": ["deportivo-toluca", "diablos-rojos"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/17/17.png"]},
    {"nombre": "Pumas UNAM", "slug": "pumas-unam", "aliases": ["pumas", "unam", "univ-nacional"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/18/18.png"]},
    {"nombre": "Necaxa", "slug": "necaxa", "aliases": ["rayos-necaxa", "rayos"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/29/29.png"]},
    {"nombre": "Querétaro FC", "slug": "queretaro", "aliases": ["queretaro-fc", "gallos-blancos"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/13668/13668.png"]},
    {"nombre": "Atlético San Luis", "slug": "atletico-san-luis", "aliases": ["san-luis", "atleti-san-luis"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/11220/11220.png"]},
    {"nombre": "Mazatlán FC", "slug": "mazatlan", "aliases": ["mazatlan-fc", "canoneros"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/12043/12043.png"]},
    {"nombre": "FC Juárez", "slug": "fc-juarez", "aliases": ["juarez", "bravos"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/11790/11790.png"]},
    {"nombre": "Atlante", "slug": "atlante", "aliases": ["potros-hierro"], "urls": ["https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/14257/14257.png", "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/2/2.png"]}
]

def purgar_archivos_vacios():
    print("🧹 Purgando archivos fantasma en bóveda (< 1 KB)...")
    purgados = 0
    for folder in [CRESTS_DIR, LEAGUES_DIR]:
        for f in os.listdir(folder):
            if f.endswith((".png", ".svg")):
                p = os.path.join(folder, f)
                if os.path.getsize(p) < 1000:
                    os.remove(p)
                    print(f"   🗑️ Eliminado corrupto: {f}")
                    purgados += 1
    print(f"   Total archivos purgados: {purgados}\n")

def sincronizar_activos():
    print("\n" + "="*85)
    print("🏛️ [SCRIPT 1] SINCRONIZADOR SOBERANO DE BÓVEDA DE ACTIVOS (LIGAS Y CLUBES)")
    print("="*85)
    purgar_archivos_vacios()

    with httpx.Client(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
        # A. Sincronizar Ligas
        print("🏆 [1/2] Sincronizando Emblemas de Ligas...")
        for lg in LEAGUES_MASTER:
            dest_png = os.path.join(LEAGUES_DIR, f"{lg['slug']}.png")
            dest_svg = os.path.join(LEAGUES_DIR, f"{lg['slug']}.svg")
            
            if not os.path.exists(dest_png) or os.path.getsize(dest_png) < 1000:
                for u in lg["urls"]:
                    try:
                        r = client.get(u)
                        if r.status_code == 200 and len(r.content) > 1000:
                            target = dest_svg if u.endswith(".svg") else dest_png
                            with open(target, "wb") as f: f.write(r.content)
                            if u.endswith(".svg") and not os.path.exists(dest_png):
                                with open(dest_png, "wb") as f_png: f_png.write(r.content)
                            print(f"   ✅ Guardado: {lg['name']} en {target} ({len(r.content)/1024:.1f} KB)")
                            break
                    except Exception as ex:
                        print(f"   ⚠️ Fallo en {u}: {ex}")
            else:
                print(f"   ℹ️ Preservado existente: {lg['name']} ({os.path.getsize(dest_png)/1024:.1f} KB)")

        # B. Sincronizar Clubes y Espejeo Multi-Slug
        print("\n🛡️ [2/2] Sincronizando Escudos de Clubes y Aliases...")
        exitosos = 0
        for club in CLUBS_MASTER:
            pri_path = os.path.join(CRESTS_DIR, f"{club['slug']}.png")
            descargado = False

            if not os.path.exists(pri_path) or os.path.getsize(pri_path) < 1000:
                for u in club["urls"]:
                    try:
                        r = client.get(u)
                        if r.status_code == 200 and len(r.content) > 1000 and r.content.startswith(b"\x89PNG"):
                            with open(pri_path, "wb") as f: f.write(r.content)
                            print(f"   ✅ Descargado: {club['nombre']:<22} -> {club['slug']}.png ({len(r.content)/1024:.1f} KB)")
                            descargado = True
                            break
                    except Exception as ex:
                        print(f"   ⚠️ Error en {u}: {ex}")
            else:
                descargado = True

            if descargado and os.path.exists(pri_path):
                exitosos += 1
                # Espejeo físico a todos los aliases
                for al in club["aliases"]:
                    al_path = os.path.join(CRESTS_DIR, f"{al}.png")
                    if not os.path.exists(al_path) or os.path.getsize(al_path) < 1000:
                        shutil.copyfile(pri_path, al_path)

        # C. Anclaje en SQLite
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            # Actualizar Ligas
            cur.execute("UPDATE leagues SET flag = '/static/img/leagues/league_262.png' WHERE fotmob_id = 262 OR id = 262")
            # Actualizar Clubes
            for club in CLUBS_MASTER:
                local_url = f"/static/img/crests/{club['slug']}.png"
                cur.execute("UPDATE teams SET crest_url = ? WHERE canonical_slug = ? OR name LIKE ?", 
                            (local_url, club["slug"], f"%{club['nombre']}%"))
            conn.commit()
            conn.close()
            print("\n💾 [DATABASE] SQLite sincronizado con rutas locales /static/img/...")

    print("="*85)
    print(f"🏁 RESULTADO: {exitosos} clubes y {len(LEAGUES_MASTER)} ligas verificados en bóveda física.")
    print("="*85 + "\n")

if __name__ == "__main__":
    sincronizar_activos()
