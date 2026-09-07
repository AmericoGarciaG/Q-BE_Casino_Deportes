# -*- coding: utf-8 -*-
"""
Script Oficial: Extracción Soberana de Escudos desde ligamx.net (cldrsrcs.apilmx.com)
Base de Gobierno: Kybern Framework v8.0 / v12.0
Protocolo Sherlock - Purga de Archivos Fantasma y Espejeo de Aliases
"""
import os
import sys
import json
import shutil
import sqlite3
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRESTS_DIR = os.path.join(PROJECT_ROOT, "src", "web", "static", "img", "crests")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "qbe_database.db")
STAGING_JSON = os.path.join(PROJECT_ROOT, "data", ".staging_catalogs_262.json")

os.makedirs(CRESTS_DIR, exist_ok=True)

# Catálogo Maestro: ID oficial Liga MX (cldrsrcs.apilmx.com) + Fallbacks ESPN verificados + Aliases
LIGA_MX_MASTER = [
    {
        "nombre": "Club América",
        "slug_primario": "america",
        "aliases": ["club-america"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/1/1.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/227.png"
        ],
        "estadio": "Ciudad de los Deportes",
        "ciudad": "Ciudad de México"
    },
    {
        "nombre": "Atlas FC",
        "slug_primario": "atlas",
        "aliases": ["atlas-fc"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/10445/10445.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/217.png"
        ],
        "estadio": "Jalisco",
        "ciudad": "Guadalajara"
    },
    {
        "nombre": "Club Tijuana",
        "slug_primario": "club-tijuana",
        "aliases": ["tijuana", "xolos"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/5/5.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/9789.png"
        ],
        "estadio": "Caliente",
        "ciudad": "Tijuana"
    },
    {
        "nombre": "Cruz Azul",
        "slug_primario": "cruz-azul",
        "aliases": ["cruzazul"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/6/6.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/221.png"
        ],
        "estadio": "Ciudad de los Deportes",
        "ciudad": "Ciudad de México"
    },
    {
        "nombre": "Chivas Guadalajara",
        "slug_primario": "guadalajara",
        "aliases": ["chivas-guadalajara", "chivas"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/7/7.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/218.png"
        ],
        "estadio": "Akron",
        "ciudad": "Guadalajara"
    },
    {
        "nombre": "Club León",
        "slug_primario": "leon",
        "aliases": ["club-leon"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/9/9.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/223.png"
        ],
        "estadio": "León",
        "ciudad": "León"
    },
    {
        "nombre": "Club Pachuca",
        "slug_primario": "pachuca",
        "aliases": ["club-pachuca"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/11/11.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/225.png"
        ],
        "estadio": "Hidalgo",
        "ciudad": "Pachuca"
    },
    {
        "nombre": "Club Puebla",
        "slug_primario": "puebla",
        "aliases": ["club-puebla"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/12/12.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/222.png"
        ],
        "estadio": "Cuauhtémoc",
        "ciudad": "Puebla"
    },
    {
        "nombre": "Rayados de Monterrey",
        "slug_primario": "monterrey",
        "aliases": ["rayados-de-monterrey", "rayados"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/14/14.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/224.png"
        ],
        "estadio": "BBVA",
        "ciudad": "Monterrey"
    },
    {
        "nombre": "Santos Laguna",
        "slug_primario": "santos-laguna",
        "aliases": ["santos"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/15/15.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/228.png"
        ],
        "estadio": "Corona",
        "ciudad": "Torreón"
    },
    {
        "nombre": "Tigres UANL",
        "slug_primario": "tigres-uanl",
        "aliases": ["tigres"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/16/16.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/229.png"
        ],
        "estadio": "Universitario",
        "ciudad": "San Nicolás de los Garza"
    },
    {
        "nombre": "Deportivo Toluca",
        "slug_primario": "toluca",
        "aliases": ["deportivo-toluca"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/17/17.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/230.png"
        ],
        "estadio": "Nemesio Díez",
        "ciudad": "Toluca"
    },
    {
        "nombre": "Pumas UNAM",
        "slug_primario": "pumas-unam",
        "aliases": ["pumas", "unam"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/18/18.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/226.png"
        ],
        "estadio": "Olímpico Universitario",
        "ciudad": "Ciudad de México"
    },
    {
        "nombre": "Necaxa",
        "slug_primario": "necaxa",
        "aliases": ["rayos-necaxa"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/29/29.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/219.png"
        ],
        "estadio": "Victoria",
        "ciudad": "Aguascalientes"
    },
    {
        "nombre": "Querétaro FC",
        "slug_primario": "queretaro",
        "aliases": ["queretaro-fc"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/13668/13668.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/231.png"
        ],
        "estadio": "Corregidora",
        "ciudad": "Querétaro"
    },
    {
        "nombre": "Atlético San Luis",
        "slug_primario": "atletico-san-luis",
        "aliases": ["san-luis"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/11220/11220.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/18630.png"
        ],
        "estadio": "Alfonso Lastras",
        "ciudad": "San Luis Potosí"
    },
    {
        "nombre": "Mazatlán FC",
        "slug_primario": "mazatlan",
        "aliases": ["mazatlan-fc"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/12043/12043.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/20824.png"
        ],
        "estadio": "El Encanto",
        "ciudad": "Mazatlán"
    },
    {
        "nombre": "FC Juárez",
        "slug_primario": "fc-juarez",
        "aliases": ["juarez"],
        "urls": [
            "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/11790/11790.png",
            "https://a.espncdn.com/i/teamlogos/soccer/500/18629.png"
        ],
        "estadio": "Benito Juárez",
        "ciudad": "Ciudad Juárez"
    }
]


def purgar_archivos_vacios():
    """Elimina cualquier archivo .png de 0 bytes o menor a 1 KB."""
    print("🧹 [PURGA] Limpiando archivos fantasma en:", CRESTS_DIR)
    purgados = 0
    for f in os.listdir(CRESTS_DIR):
        if f.endswith(".png"):
            path = os.path.join(CRESTS_DIR, f)
            if os.path.getsize(path) < 1000:
                os.remove(path)
                print(f"   🗑️ Eliminado archivo fantasma (0 bytes): {f}")
                purgados += 1
    print(f"   Total archivos purgados: {purgados}\n")


def ejecutar_extraccion_y_espejeo():
    purgar_archivos_vacios()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://ligamx.net/"
    }

    print("=" * 85)
    print("🚀 [KYBERN] INICIANDO EXTRACCIÓN SOBERANA LIGAMX.NET Y ESPEJEO DE ALIASES")
    print("=" * 85)

    exitosos = 0
    staging_teams = []

    with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
        for club in LIGA_MX_MASTER:
            nombre = club["nombre"]
            slug_pri = club["slug_primario"]
            aliases = club["aliases"]
            urls = club["urls"]
            archivo_primario = os.path.join(CRESTS_DIR, f"{slug_pri}.png")

            print(f"\nProcesando: {nombre:<24} | Archivo: {slug_pri}.png")
            descargado = False

            # Intentar descargar de las URLs oficiales
            for u in urls:
                try:
                    res = client.get(u)
                    if res.status_code == 200 and len(res.content) > 3000 and res.content.startswith(b"\x89PNG"):
                        with open(archivo_primario, "wb") as f_out:
                            f_out.write(res.content)
                        size_kb = len(res.content) / 1024
                        print(f"  ✅ Descargado OK ({size_kb:.1f} KB) desde {u}")
                        descargado = True
                        break
                except Exception as ex:
                    print(f"  ⚠️ Intento fallido en {u}: {ex}")

            # Si ya existía un archivo válido en disco y las URLs fallaron, preservarlo
            if not descargado and os.path.exists(archivo_primario) and os.path.getsize(archivo_primario) > 3000:
                print(f"  ℹ️ Preservando archivo local existente ({os.path.getsize(archivo_primario)/1024:.1f} KB)")
                descargado = True

            if descargado:
                exitosos += 1
                # ESPEJEO FÍSICO A TODOS LOS ALIASES (Cero archivos vacíos)
                for alias in aliases:
                    alias_path = os.path.join(CRESTS_DIR, f"{alias}.png")
                    shutil.copyfile(archivo_primario, alias_path)
                    print(f"  📋 Espejeado a alias: {alias}.png ({os.path.getsize(alias_path)/1024:.1f} KB)")

                staging_teams.append({
                    "id": slug_pri,
                    "id_candidato": f"CAND-{exitosos:02d}",
                    "name": nombre,
                    "short_name": nombre.split()[0],
                    "canonical_slug": slug_pri,
                    "crest_candidate_url": f"/static/img/crests/{slug_pri}.png",
                    "crest_url": f"/static/img/crests/{slug_pri}.png",
                    "stadium": club.get("estadio", "Estadio Oficial"),
                    "city": club.get("ciudad", "México"),
                    "aliases": [slug_pri] + aliases,
                    "status": "APPROVED"
                })
            else:
                print(f"  ❌ ERROR: No se pudo obtener escudo válido para {nombre}")

    # Actualizar Staging JSON
    if staging_teams:
        with open(STAGING_JSON, "w", encoding="utf-8") as f:
            json.dump(staging_teams, f, indent=2, ensure_ascii=False)
        print(f"\n📦 Staging JSON actualizado en: {STAGING_JSON}")

    # Actualizar SQLite
    if os.path.exists(DB_PATH) and staging_teams:
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            for t in staging_teams:
                cur.execute("""
                    UPDATE teams
                    SET crest_url = ?
                    WHERE canonical_slug = ? OR name LIKE ?
                """, (t["crest_url"], t["canonical_slug"], f"%{t['name']}%"))
            conn.commit()
            conn.close()
            print("💾 [DATABASE] SQLite teams actualizado con rutas locales certificadas.")
        except Exception as e:
            print(f"⚠️ Error al actualizar SQLite: {e}")

    print("=" * 85)
    print(f"🏁 RESULTADO: {exitosos}/18 clubes procesados con escudos reales y aliases espejeados.")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    ejecutar_extraccion_y_espejeo()
