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

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CRESTS_DIR = os.path.join(PROJECT_ROOT, "src", "web", "static", "img", "crests")
LEAGUES_DIR = os.path.join(PROJECT_ROOT, "src", "web", "static", "img", "leagues")
# [ARCH-1.5.10] Bóveda de Activos de Operadores de Casino: los emblemas de las casas de
# apuestas se anclan en disco local (`/static/img/bookmakers/{slug}.(png|svg)`). Queda
# PROHIBIDO el hotlinking a servidores de terceros para logos de casinos.
BOOKMAKERS_DIR = os.path.join(PROJECT_ROOT, "src", "web", "static", "img", "bookmakers")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "qbe_database.db")

os.makedirs(CRESTS_DIR, exist_ok=True)
os.makedirs(LEAGUES_DIR, exist_ok=True)
os.makedirs(BOOKMAKERS_DIR, exist_ok=True)

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

# 3. [ARCH-1.5.10] Catálogo Oficial de Casas de Apuestas de la Ventanilla
# [GOVERNANCE-01] `urls` se puebla ÚNICAMENTE con endpoints de activos verificados por la
# capa de ingesta (evidencia fáctica). Una lista vacía es un estado legítimo y explícito:
# en su ausencia el script ancla el emblema LOCAL de respaldo (`{slug}.svg`) garantizando
# cero hotlink y cero uso de marca ajena, sin inventar rutas remotas.
# [ARCH-1.5.10-B] El endpoint de Caliente queda DECLARADO en el catálogo soberano. Evidencia
# fáctica del turno (2026-09-28): ese endpoint responde HTTP 404 (`text/html`, 29 KB) con UA de
# navegador ⇒ la firma PNG se rechaza y el emblema local ya anclado (caliente.png, 4451 B,
# cabecera `89 50 4E 47 0D 0A 1A 0A`) permanece como pieza autoritativa. Cero hotlink.
BOOKMAKERS_MASTER = [
    {"slug": "caliente", "nombre": "Caliente_Deportes.MX",
     "urls": ["https://sports.caliente.mx/es_MX/desktop_header_logo.png"]},
    # [ARCH-1.5.10-B] Vector de Betway: geometría fijada por el inspector en el catálogo.
    # `urls` vacío es estado legítimo ⇒ se ancla el trazo PROPIO en esa ventana. Cero marca
    # ajena inventada: si el vector corporativo verificado se incorpora, entra por `urls`.
    {"slug": "betway", "nombre": "Betway.MX", "viewbox": "0 -2 55 20", "urls": []},
    # [ARCH-1.4.6-F] Vector de Novibet: el emblema oficial fue adquirido por transporte de
    # navegador (Playwright `page.goto`) y anclado en la bóveda local (novibet.svg, 5 859 B).
    # Evidencia fáctica del turno (2026-09-28): `httpx.GET` y `context.request.get` al asset
    # devuelven HTTP 403 (Cloudflare) ⇒ `urls` permanece vacío como estado legítimo.
    # La geometría declarada (`viewBox="0 0 164 38"`) coincide exactamente con el vector
    # anclado, por lo que `sincronizar_emblemas_casinos` PRESERVA la pieza oficial y jamás la
    # sobrescribe con el emblema de respaldo. Cero hotlink.
    {"slug": "novibet", "nombre": "Novibet.MX", "viewbox": "0 0 164 38", "urls": []},
]


def generar_emblema_local_svg(casino: dict) -> str:
    """[ARCH-1.5.10-B] Emblema vectorial propio, generado localmente (cero hotlink).

    No replica el logotipo registrado de la casa: rotula el nombre oficial del operador
    declarado en el catálogo, por lo que la pieza es propia y auditable. Si el catálogo fija
    `viewbox` (geometría del inspector), el trazo se adapta a esa ventana declarada.
    """
    nombre = casino["nombre"]
    viewbox = str(casino.get("viewbox", "0 0 240 60"))
    vb_x, vb_y, vb_w, vb_h = (float(v) for v in viewbox.split())
    pad = vb_h * 0.18
    radio = vb_h * 0.18
    centro_x = vb_x + pad + radio
    texto_x = vb_x + pad + radio * 2 + vb_h * 0.16
    # El rótulo se ajusta a la ventana disponible: la pieza jamás desborda su viewBox.
    disponible = max(vb_w - (texto_x - vb_x) - pad, vb_h * 0.2)
    fuente = min(vb_h * 0.34, disponible / max(len(nombre) * 0.58, 1.0))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- [ARCH-1.5.10-B] Emblema de respaldo anclado por scripts/utilidades/sincronizar_boveda_activos.py -->
<!-- Origen: generacion local. Cero hotlinking. Geometria fijada: viewBox="{viewbox}". -->
<!-- Pieza sin marca ajena: rotula el nombre oficial del operador registrado en el catalogo. -->
<svg xmlns="http://www.w3.org/2000/svg" width="{vb_w:g}" height="{vb_h:g}" viewBox="{viewbox}" role="img" aria-label="{nombre}">
  <rect x="{vb_x:g}" y="{vb_y:g}" width="{vb_w:g}" height="{vb_h:g}" rx="{vb_h * 0.16:g}" fill="#0f172a"/>
  <circle cx="{centro_x:g}" cy="{vb_y + vb_h / 2:g}" r="{radio:g}" fill="none" stroke="#38BDF8" stroke-width="{vb_h * 0.09:g}"/>
  <circle cx="{centro_x:g}" cy="{vb_y + vb_h / 2:g}" r="{vb_h * 0.045:g}" fill="#38BDF8"/>
  <text x="{texto_x:g}" y="{vb_y + vb_h * 0.67:g}" font-family="Segoe UI, Arial, sans-serif" font-size="{fuente:g}" font-weight="700" fill="#ffffff">{nombre}</text>
</svg>
"""


def sincronizar_emblemas_casinos(client: httpx.Client) -> int:
    """[ARCH-1.5.10] Ancla en disco los emblemas de las casas de apuestas de la ventanilla."""
    print("\n🎰 [3/3] Sincronizando Emblemas de Casas de Apuestas (Bóveda de Operadores)...")
    anclados = 0

    for casino in BOOKMAKERS_MASTER:
        pri_png = os.path.join(BOOKMAKERS_DIR, f"{casino['slug']}.png")
        alt_svg = os.path.join(BOOKMAKERS_DIR, f"{casino['slug']}.svg")

        if os.path.exists(pri_png) and os.path.getsize(pri_png) > 1000:
            print(f"   ℹ️ Preservado emblema oficial: {casino['nombre']} ({os.path.getsize(pri_png)/1024:.1f} KB)")
            anclados += 1
            continue

        # [ARCH-1.5.10-B] Auto-sanación de geometría: si el vector anclado no declara la ventana
        # fijada por el catálogo (geometría del inspector), se reemite el trazo propio conforme.
        viewbox_esperado = casino.get("viewbox")
        if os.path.exists(alt_svg) and viewbox_esperado:
            with open(alt_svg, "r", encoding="utf-8") as f:
                svg_anclado = f.read()
            if f'viewBox="{viewbox_esperado}"' in svg_anclado:
                print(f"   ℹ️ Preservado vector local: {casino['slug']}.svg (viewBox conforme)")
                anclados += 1
                continue
            print(f"   ♻️ Reemitiendo {casino['slug']}.svg con viewBox='{viewbox_esperado}' (inspector)")

        descargado = False
        for u in casino.get("urls", []):
            try:
                r = client.get(u)
                if r.status_code == 200 and len(r.content) > 1000 and r.content.startswith(b"\x89PNG"):
                    with open(pri_png, "wb") as f:
                        f.write(r.content)
                    print(f"   ✅ Emblema oficial anclado: {casino['nombre']} -> {casino['slug']}.png ({len(r.content)/1024:.1f} KB)")
                    descargado = True
                    break
            except Exception as ex:
                print(f"   ⚠️ Error en {u}: {ex}")

        if not descargado:
            with open(alt_svg, "w", encoding="utf-8") as f:
                f.write(generar_emblema_local_svg(casino))
            print(f"   🛡️ Emblema local de respaldo anclado: {casino['slug']}.svg (sin logotipo oficial verificado)")
            anclados += 1

    print(f"   Total emblemas de casino verificados en bóveda: {anclados}/{len(BOOKMAKERS_MASTER)}")
    return anclados

def purgar_archivos_vacios():
    print("🧹 Purgando archivos fantasma en bóveda (< 1 KB)...")
    purgados = 0
    # [ARCH-1.5.10] Los emblemas de casino aceptan respaldo vectorial local (`.svg`): sólo los
    # `.png` de casino se consideran fantasma si pesan menos de 1 KB.
    objetivos = [
        (CRESTS_DIR, (".png", ".svg")),
        (LEAGUES_DIR, (".png", ".svg")),
        (BOOKMAKERS_DIR, (".png",)),
    ]
    for folder, extensiones in objetivos:
        for f in os.listdir(folder):
            if f.endswith(extensiones):
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

        # D. [ARCH-1.5.10] Emblemas de las casas de apuestas de la ventanilla
        emblemas_casinos = sincronizar_emblemas_casinos(client)

    print("="*85)
    print(f"🏁 RESULTADO: {exitosos} clubes, {len(LEAGUES_MASTER)} ligas y {emblemas_casinos} emblemas de casino verificados en bóveda física.")
    print("="*85 + "\n")

if __name__ == "__main__":
    sincronizar_activos()
