# -*- coding: utf-8 -*-
"""
Módulo de Resolución Canónica de Escudos y Bóveda Soberana [LN-QBE-019]
Base de Gobierno: Kybern Framework v8.0 / v12.0
"""
import os
import logging
import urllib.parse
from typing import Optional
from sqlalchemy.orm import Session
from src.ingestion.normalizer import canonicalize_team_name

logger = logging.getLogger("CrestResolver")

# Directorio raíz del proyecto y carpeta de assets estáticos
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STATIC_CRESTS_DIR = os.path.join(BASE_DIR, "src", "web", "static", "img", "crests")

def _generar_svg_fallback(iniciales: str, club_nombre: str) -> str:
    """Genera un Data URI SVG determinista Dark Mode Fintech para clubes sin escudo físico."""
    svg_raw = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
      <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#1C2541" />
          <stop offset="100%" stop-color="#0B132B" />
        </linearGradient>
      </defs>
      <circle cx="24" cy="24" r="22" fill="url(#grad)" stroke="#38BDF8" stroke-width="2"/>
      <text x="50%" y="54%" text-anchor="middle" dominant-baseline="middle" 
            fill="#FFFFFF" font-family="Inter, system-ui, sans-serif" font-size="14" font-weight="700">
        {iniciales[:3]}
      </text>
    </svg>"""
    encoded = urllib.parse.quote(svg_raw)
    return f"data:image/svg+xml;utf8,{encoded}"

def obtener_slug_club(nombre: str) -> str:
    """Genera un slug limpio y canónico a partir del nombre del club."""
    nombre_canonico = canonicalize_team_name(nombre)
    slug = (
        nombre_canonico.lower()
        .replace(" ", "-")
        .replace(".", "")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )
    return slug

def resolver_escudo_canonico(
    equipo_nombre: str,
    fotmob_id: Optional[int] = None,
    db: Optional[Session] = None
) -> str:
    """
    [LN-QBE-019] Resuelve la URI de escudo bajo la escalera de precedencia legislada:
    1. Bóveda Local (/static/img/crests/{slug}.png) con verificación física (>= 3 KB).
    2. Consulta en base de datos SQLite (Team.canonical_slug y Team.name).
    3. Fallback a SVG Data URI.
    """
    if not equipo_nombre:
        return _generar_svg_fallback("QBE", "Club")

    slug = obtener_slug_club(equipo_nombre)
    os.makedirs(STATIC_CRESTS_DIR, exist_ok=True)

    # Nivel 1: Verificación de archivo primario en disco
    archivo_fisico = os.path.join(STATIC_CRESTS_DIR, f"{slug}.png")
    if os.path.exists(archivo_fisico) and os.path.getsize(archivo_fisico) > 3000:
        return f"/static/img/crests/{slug}.png"

    # Nivel 1B: Verificación de aliases conocidos en disco
    for extension in [f"club-{slug}.png", f"{slug}-fc.png", f"deportivo-{slug}.png"]:
        alias_fisico = os.path.join(STATIC_CRESTS_DIR, extension)
        if os.path.exists(alias_fisico) and os.path.getsize(alias_fisico) > 3000:
            return f"/static/img/crests/{extension}"

    # Nivel 2: Consulta en base de datos SQLite
    if db is not None:
        try:
            from src.storage.models import Team
            # [CORRECCIÓN INDUSTRIAL]: Usar Team.canonical_slug y Team.name reales
            team_rec = db.query(Team).filter(
                (Team.canonical_slug == slug) | (Team.name == equipo_nombre) | (Team.short_name == equipo_nombre)
            ).first()
            if team_rec and team_rec.crest_url:
                c_url = team_rec.crest_url
                if "fotmob.com" not in c_url.lower():
                    if c_url.startswith("/static/") or c_url.startswith("data:image/svg+xml"):
                        return c_url
        except Exception as ex:
            logger.warning(f"Aviso en consulta SQLite para '{equipo_nombre}': {ex}")

    # Nivel 3: Fallback a SVG determinista estilizado
    palabras = equipo_nombre.strip().split()
    if len(palabras) >= 2:
        iniciales = f"{palabras[0][0]}{palabras[1][0]}".upper()
    else:
        iniciales = equipo_nombre[:3].upper()

    return _generar_svg_fallback(iniciales, equipo_nombre)
