# -*- coding: utf-8 -*-
"""
Kybern Industrial — [LN-QBE-015] Curador Agéntico de Catálogos y Bóveda de Activos
[ARCH-1.5.2] Módulo Administrativo de Curación HITL
Base de Gobierno: Kybern Framework v8.0 / v12.0
"""
import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, List
import httpx
from sqlalchemy.orm import Session
from src.storage.models import League, Team

# ─── Directorios soberanos ────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = PROJECT_ROOT / "data"
CRESTS_DIR = PROJECT_ROOT / "src" / "web" / "static" / "img" / "crests"
CRESTS_DIR.mkdir(parents=True, exist_ok=True)
STAGING_DIR.mkdir(parents=True, exist_ok=True)

# ─── Catálogo Canónico Oficial FMF / Liga MX (Fuente de la Verdad) ───────────
PROSPECCION_LIGA_MX: List[Dict[str, Any]] = [
    {
        "name": "Club América", "short": "América", "slug": "america",
        "stadium": "Ciudad de los Deportes", "city": "Ciudad de México",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/1/1.png",
        "aliases": ["club-america", "aguilas", "america"],
    },
    {
        "name": "Atlas FC", "short": "Atlas", "slug": "atlas",
        "stadium": "Jalisco", "city": "Guadalajara",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/10445/10445.png",
        "aliases": ["atlas-fc", "zorros", "rojinegros"],
    },
    {
        "name": "Club Tijuana", "short": "Tijuana", "slug": "club-tijuana",
        "stadium": "Caliente", "city": "Tijuana",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/5/5.png",
        "aliases": ["tijuana", "xolos"],
    },
    {
        "name": "Cruz Azul", "short": "Cruz Azul", "slug": "cruz-azul",
        "stadium": "Ciudad de los Deportes", "city": "Ciudad de México",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/6/6.png",
        "aliases": ["cruzazul", "la-maquina", "cementeros"],
    },
    {
        "name": "Chivas Guadalajara", "short": "Chivas", "slug": "guadalajara",
        "stadium": "Akron", "city": "Zapopan",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/7/7.png",
        "aliases": ["chivas-guadalajara", "chivas", "guadalajara"],
    },
    {
        "name": "Club León", "short": "León", "slug": "leon",
        "stadium": "León", "city": "León",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/9/9.png",
        "aliases": ["club-leon", "la-fiera", "panzas-verdes"],
    },
    {
        "name": "Club Pachuca", "short": "Pachuca", "slug": "pachuca",
        "stadium": "Hidalgo", "city": "Pachuca",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/11/11.png",
        "aliases": ["club-pachuca", "tuzos"],
    },
    {
        "name": "Club Puebla", "short": "Puebla", "slug": "puebla",
        "stadium": "Cuauhtémoc", "city": "Puebla",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/12/12.png",
        "aliases": ["club-puebla", "la-franja", "camoteros"],
    },
    {
        "name": "Rayados de Monterrey", "short": "Monterrey", "slug": "monterrey",
        "stadium": "BBVA", "city": "Guadalupe",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/14/14.png",
        "aliases": ["rayados-de-monterrey", "rayados", "monterrey"],
    },
    {
        "name": "Santos Laguna", "short": "Santos", "slug": "santos-laguna",
        "stadium": "Corona", "city": "Torreón",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/15/15.png",
        "aliases": ["santos", "guerreros", "laguneros"],
    },
    {
        "name": "Tigres UANL", "short": "Tigres", "slug": "tigres-uanl",
        "stadium": "Universitario", "city": "San Nicolás de los Garza",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/16/16.png",
        "aliases": ["tigres", "felinos", "uanl"],
    },
    {
        "name": "Deportivo Toluca", "short": "Toluca", "slug": "toluca",
        "stadium": "Nemesio Díez", "city": "Toluca",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/17/17.png",
        "aliases": ["deportivo-toluca", "diablos-rojos", "toluca"],
    },
    {
        "name": "Pumas UNAM", "short": "Pumas", "slug": "pumas-unam",
        "stadium": "Olímpico Universitario", "city": "Ciudad de México",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/18/18.png",
        "aliases": ["pumas", "unam", "univ-nacional", "universitarios"],
    },
    {
        "name": "Necaxa", "short": "Necaxa", "slug": "necaxa",
        "stadium": "Victoria", "city": "Aguascalientes",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/29/29.png",
        "aliases": ["rayos-necaxa", "rayos"],
    },
    {
        "name": "Querétaro FC", "short": "Querétaro", "slug": "queretaro",
        "stadium": "Corregidora", "city": "Querétaro",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/13668/13668.png",
        "aliases": ["queretaro-fc", "gallos-blancos", "qro-fc"],
    },
    {
        "name": "Atlético San Luis", "short": "San Luis", "slug": "atletico-san-luis",
        "stadium": "Alfonso Lastras", "city": "San Luis Potosí",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/11220/11220.png",
        "aliases": ["san-luis", "atleti-san-luis", "potosinos"],
    },
    {
        "name": "Mazatlán FC", "short": "Mazatlán", "slug": "mazatlan",
        "stadium": "El Encanto", "city": "Mazatlán",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/12043/12043.png",
        "aliases": ["mazatlan-fc", "canoneros"],
    },
    {
        "name": "FC Juárez", "short": "Juárez", "slug": "fc-juarez",
        "stadium": "Benito Juárez", "city": "Ciudad Juárez",
        "crest_url": "https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/11790/11790.png",
        "aliases": ["juarez", "bravos"],
    },
]

# ─── Funciones de Curación IPO ────────────────────────────────────────────────

def ejecutar_prospeccion_liga(league_id: int) -> Dict[str, Any]:
    """Descubre clubes candidatos y genera data/.staging_catalogs_{league_id}.json."""
    staged = []
    for idx, c in enumerate(PROSPECCION_LIGA_MX, 1):
        staged.append({
            "id_candidato": f"CAND-{idx:02d}",
            "name": c["name"],
            "short_name": c["short"],
            "canonical_slug": c["slug"],
            "stadium": c["stadium"],
            "city": c["city"],
            "crest_candidate_url": c["crest_url"],
            "crest_url": f"/static/img/crests/{c['slug']}.png",
            "aliases": c["aliases"],
            "status": "APPROVED",
        })

    staging_path = STAGING_DIR / f".staging_catalogs_{league_id}.json"
    staging_path.write_text(
        json.dumps(staged, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {"status": "STAGED", "league_id": league_id, "candidates_count": len(staged)}


def obtener_staging_liga(league_id: int) -> List[Dict[str, Any]]:
    """Lee candidatos en staging; auto-ejecuta prospección si no existe."""
    staging_path = STAGING_DIR / f".staging_catalogs_{league_id}.json"
    if not staging_path.exists():
        ejecutar_prospeccion_liga(league_id)
    
    raw = json.loads(staging_path.read_text(encoding="utf-8"))
    teams = raw.get("teams", raw) if isinstance(raw, dict) else raw
    return teams


def sellar_catalogo_en_db(
    league_id: int,
    approved_teams: List[Dict[str, Any]],
    db: Session,
) -> Dict[str, Any]:
    """
    [Commit Inmutable HITL + Multi-Slug Mirroring]
    Descarga los escudos oficiales a disco con verificación de integridad y realiza
    el espejeo físico obligatorio a todos sus aliases reconocidos [ARCH-1.5.4].
    """
    league = db.query(League).filter(
        (League.fotmob_id == league_id) | (League.id == league_id)
    ).first()
    if not league:
        raise ValueError(f"Liga con id={league_id} no encontrada en la base de datos.")

    committed = 0
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://ligamx.net/"
    }

    with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
        for idx, t in enumerate(approved_teams):
            slug = t.get("canonical_slug") or t.get("slug")
            if not slug:
                continue
            crest_url = t.get("crest_candidate_url") or t.get("crest_url", "")
            local_filename = f"{slug}.png"
            local_path = CRESTS_DIR / local_filename

            # 1. Descarga soberana local (solo si no existe o es menor a 3 KB)
            if not local_path.exists() or local_path.stat().st_size < 3000:
                if crest_url and crest_url.startswith("http"):
                    try:
                        r = client.get(crest_url)
                        if r.status_code == 200 and len(r.content) > 3000 and r.content.startswith(b"\x89PNG"):
                            local_path.write_bytes(r.content)
                    except Exception as exc:
                        print(f"⚠️ [CURATION] Error descargando '{slug}': {exc}")

            # 2. [ARCH-1.5.4] Espejeo físico a todos los aliases (Anti-Archivos Fantasma)
            aliases = t.get("aliases", [])
            if local_path.exists() and local_path.stat().st_size >= 3000:
                for alias in aliases:
                    if alias and alias != slug:
                        alias_clean = alias.lower().replace(" ", "-")
                        alias_path = CRESTS_DIR / f"{alias_clean}.png"
                        shutil.copyfile(local_path, alias_path)

            # 3. Upsert inmutable en SQLite
            final_crest_url = f"/static/img/crests/{local_filename}"
            team_db = db.query(Team).filter(Team.canonical_slug == slug).first()
            if not team_db:
                team_db = Team(
                    league_id=league.id,
                    fotmob_team_id=10000 + idx,
                    name=t["name"],
                    short_name=t.get("short_name", t["name"][:10]),
                    canonical_slug=slug,
                    crest_url=final_crest_url,
                )
                db.add(team_db)
            else:
                team_db.name = t["name"]
                team_db.short_name = t.get("short_name", team_db.short_name)
                team_db.crest_url = final_crest_url

            committed += 1

    db.commit()
    print(f"✅ [CURATION INDUSTRIAL] Catálogo sellado: {committed} clubes en league_id={league_id}.")
    return {"status": "SEALED", "league_id": league_id, "teams_committed": committed}
