# -*- coding: utf-8 -*-
"""
Kybern Industrial — Seeder de Base de Datos y Bóveda de Activos [ARCH-1.5.0]
Base de Gobierno: Kybern Framework v8.0 / v12.0
"""
import os
import sys
from src.storage.database import SessionLocal, engine, Base
from src.storage.models import League, Team, StandingSnapshot
from src.storage.crest_resolver import STATIC_CRESTS_DIR, obtener_slug_club
from src.ingestion.normalizer import canonicalize_team_name

# Escudos primarios que DEBEN existir con bytes reales (> 3 KB) para que la app funcione.
# [ALT-8-C RATIFICADA — DICTAMEN DEL DIRECTOR 2026-10-04] Nombres alineados a los SLUGS
# CANÓNICOS de la identidad fáctica FotMob (`TEAMS_LIGA_MX`). Con los slugs legados la
# verificación daba falso positivo permanente (archivos inexistentes) y disparaba
# `sellar_catalogo_en_db` en cada arranque, que fabricaba clubes con `fotmob_team_id = 10000 + idx`
# ([GOVERNANCE-01] / VARIANZA-08-D): 10 tuplas residuales en `teams` y ruptura de LN-QBE-019.
_ESCUDOS_CLAVE = [
    "club-america.png", "chivas-guadalajara.png", "cruz-azul.png", "deportivo-toluca.png",
    "club-pachuca.png", "tigres-uanl.png", "rayados-de-monterrey.png", "pumas-unam.png",
    "club-leon.png", "santos-laguna.png", "atlas-fc.png", "atletico-san-luis.png",
    "necaxa.png", "fc-juarez.png", "queretaro-fc.png",
    "club-tijuana.png", "club-puebla.png", "atlante.png"
]

def asegurar_boveda_escudos_base():
    """
    [GOVERNANCE-01] Garantiza escudos reales de forma nativa sin llamadas a subprocesos de terminal.
    """
    os.makedirs(STATIC_CRESTS_DIR, exist_ok=True)
    faltantes = [
        e for e in _ESCUDOS_CLAVE 
        if not os.path.exists(os.path.join(STATIC_CRESTS_DIR, e)) or os.path.getsize(os.path.join(STATIC_CRESTS_DIR, e)) < 3000
    ]

    if faltantes:
        print(f"[SEEDER] ⚠️ {len(faltantes)} escudos faltantes en bóveda. Ejecutando extracción nativa...")
        from src.storage.curation_service import PROSPECCION_LIGA_MX, sellar_catalogo_en_db
        db = SessionLocal()
        try:
            sellar_catalogo_en_db(262, PROSPECCION_LIGA_MX, db)
        except Exception as exc:
            print(f"[SEEDER] ⚠️ Aviso en sellado nativo: {exc}")
        finally:
            db.close()

# [ALT-8-C RATIFICADA — DICTAMEN DEL DIRECTOR 2026-10-04] Catálogo de identidad FÁCTICA de los
# 18 clubes de la Liga MX. Fuente: respuesta oficial de FotMob capturada por
# `scripts/daemons/centinela_deportivo.py` (Fase 4). Sustituye al catálogo legado
# (7966…7981 / 8430 / 10014 / 638520), cuyos identificadores YA NO corresponden a la identidad
# publicada hoy por la fuente (p. ej. Club Tijuana: legado 10224 vs fáctico 162418) y
# provocaban residuos duplicados en cada arranque. [GOVERNANCE-01] Cero identificadores fabricados.
TEAMS_LIGA_MX = [
    {"fotmob_id": 1841, "name": "Club León", "short": "León", "slug": "club-leon"},
    {"fotmob_id": 1842, "name": "Necaxa", "short": "Necaxa", "slug": "necaxa"},
    {"fotmob_id": 1942, "name": "Atlante", "short": "Atlante", "slug": "atlante"},
    {"fotmob_id": 1943, "name": "Querétaro FC", "short": "Querétaro", "slug": "queretaro-fc"},
    {"fotmob_id": 1946, "name": "Pumas UNAM", "short": "Pumas", "slug": "pumas-unam"},
    {"fotmob_id": 6358, "name": "Atlético San Luis", "short": "San Luis", "slug": "atletico-san-luis"},
    {"fotmob_id": 6576, "name": "Club América", "short": "América", "slug": "club-america"},
    {"fotmob_id": 6577, "name": "Atlas FC", "short": "Atlas", "slug": "atlas-fc"},
    {"fotmob_id": 6578, "name": "Cruz Azul", "short": "Cruz Azul", "slug": "cruz-azul"},
    {"fotmob_id": 6618, "name": "Deportivo Toluca", "short": "Toluca", "slug": "deportivo-toluca"},
    {"fotmob_id": 7807, "name": "Chivas Guadalajara", "short": "Chivas", "slug": "chivas-guadalajara"},
    {"fotmob_id": 7847, "name": "Club Puebla", "short": "Puebla", "slug": "club-puebla"},
    {"fotmob_id": 7848, "name": "Club Pachuca", "short": "Pachuca", "slug": "club-pachuca"},
    {"fotmob_id": 7849, "name": "Rayados de Monterrey", "short": "Monterrey", "slug": "rayados-de-monterrey"},
    {"fotmob_id": 7857, "name": "Santos Laguna", "short": "Santos", "slug": "santos-laguna"},
    {"fotmob_id": 8561, "name": "Tigres UANL", "short": "Tigres", "slug": "tigres-uanl"},
    {"fotmob_id": 162418, "name": "Club Tijuana", "short": "Tijuana", "slug": "club-tijuana"},
    {"fotmob_id": 649424, "name": "FC Juárez", "short": "Juárez", "slug": "fc-juarez"},
]

# [VARIANZA-09 / 12.7 RATIFICADA — DICTAMEN DEL DIRECTOR 2026-10-04] Proyección de identidad
# fáctica `nombre canónico → fotmob_id` derivada del catálogo ratificado (ALT-8-C). Sustituye la
# fabricación `10000 + pos` del snapshot de arranque ([GOVERNANCE-01]): el identificador de club
# NUNCA se inventa, se toma de la evidencia oficial de FotMob.
_FOTMOB_ID_POR_NOMBRE = {t["name"]: t["fotmob_id"] for t in TEAMS_LIGA_MX}

# Snapshot certificado de Tabla General oficial tras concluir la Jornada 7 [PARIDAD FÁCTICA FMF]
TABLA_OFICIAL_J7_CONCLUIDA = [
    {"pos": 1, "equipo": "Club América", "pj": 6, "pg": 5, "pe": 1, "pp": 0, "gf": 12, "gc": 2, "dif": 10, "puntos": 16, "xg": 12.8, "xga": 7.3, "xpts": 16.0},
    {"pos": 2, "equipo": "Chivas Guadalajara", "pj": 7, "pg": 4, "pe": 2, "pp": 1, "gf": 12, "gc": 6, "dif": 6, "puntos": 14, "xg": 11.5, "xga": 6.8, "xpts": 14.0},
    {"pos": 3, "equipo": "Deportivo Toluca", "pj": 6, "pg": 4, "pe": 1, "pp": 1, "gf": 12, "gc": 4, "dif": 8, "puntos": 13, "xg": 10.7, "xga": 5.7, "xpts": 13.0},
    {"pos": 4, "equipo": "Club Tijuana", "pj": 6, "pg": 4, "pe": 1, "pp": 1, "gf": 10, "gc": 7, "dif": 3, "puntos": 13, "xg": 10.2, "xga": 6.1, "xpts": 13.0},
    {"pos": 5, "equipo": "Atlas FC", "pj": 7, "pg": 4, "pe": 1, "pp": 2, "gf": 10, "gc": 9, "dif": 1, "puntos": 13, "xg": 7.8, "xga": 9.9, "xpts": 13.0},
    {"pos": 6, "equipo": "Cruz Azul", "pj": 7, "pg": 4, "pe": 0, "pp": 3, "gf": 12, "gc": 11, "dif": 1, "puntos": 12, "xg": 12.1, "xga": 8.6, "xpts": 12.0},
    {"pos": 7, "equipo": "Pumas UNAM", "pj": 7, "pg": 3, "pe": 2, "pp": 2, "gf": 11, "gc": 9, "dif": 2, "puntos": 11, "xg": 8.4, "xga": 8.5, "xpts": 11.0},
    {"pos": 8, "equipo": "Querétaro FC", "pj": 6, "pg": 3, "pe": 1, "pp": 2, "gf": 9, "gc": 7, "dif": 2, "puntos": 10, "xg": 9.6, "xga": 9.3, "xpts": 10.0},
    {"pos": 9, "equipo": "Club Puebla", "pj": 6, "pg": 3, "pe": 1, "pp": 2, "gf": 9, "gc": 9, "dif": 0, "puntos": 10, "xg": 7.2, "xga": 8.1, "xpts": 10.0},
    {"pos": 10, "equipo": "Club León", "pj": 7, "pg": 3, "pe": 1, "pp": 3, "gf": 9, "gc": 9, "dif": 0, "puntos": 10, "xg": 8.2, "xga": 9.1, "xpts": 10.0},
    {"pos": 11, "equipo": "Rayados de Monterrey", "pj": 6, "pg": 3, "pe": 0, "pp": 3, "gf": 13, "gc": 10, "dif": 3, "puntos": 9, "xg": 11.2, "xga": 8.7, "xpts": 9.0},
    {"pos": 12, "equipo": "Club Pachuca", "pj": 7, "pg": 2, "pe": 2, "pp": 3, "gf": 10, "gc": 8, "dif": 2, "puntos": 8, "xg": 9.1, "xga": 9.8, "xpts": 8.0},
    {"pos": 13, "equipo": "Necaxa", "pj": 7, "pg": 2, "pe": 2, "pp": 3, "gf": 9, "gc": 12, "dif": -3, "puntos": 8, "xg": 10.8, "xga": 8.9, "xpts": 8.0},
    {"pos": 14, "equipo": "Atlante", "pj": 7, "pg": 1, "pe": 4, "pp": 2, "gf": 7, "gc": 9, "dif": -2, "puntos": 7, "xg": 6.8, "xga": 8.8, "xpts": 7.0},
    {"pos": 15, "equipo": "Tigres UANL", "pj": 7, "pg": 1, "pe": 3, "pp": 3, "gf": 9, "gc": 11, "dif": -2, "puntos": 6, "xg": 10.9, "xga": 8.3, "xpts": 6.0},
    {"pos": 16, "equipo": "Atlético San Luis", "pj": 7, "pg": 1, "pe": 3, "pp": 3, "gf": 8, "gc": 13, "dif": -5, "puntos": 6, "xg": 7.6, "xga": 10.5, "xpts": 6.0},
    {"pos": 17, "equipo": "Santos Laguna", "pj": 7, "pg": 0, "pe": 1, "pp": 6, "gf": 4, "gc": 12, "dif": -8, "puntos": 1, "xg": 7.5, "xga": 9.4, "xpts": 1.0},
    {"pos": 18, "equipo": "FC Juárez", "pj": 7, "pg": 0, "pe": 0, "pp": 7, "gf": 3, "gc": 21, "dif": -18, "puntos": 0, "xg": 3.6, "xga": 14.8, "xpts": 0.0},
]

def seed_initial_data(db):
    """Siembra la liga, clubes y el snapshot oficial de la jornada con paridad fáctica."""
    liga = db.query(League).filter(League.fotmob_id == 262).first()
    if not liga:
        liga = League(
            name="Liga MX",
            country="México",
            flag="🇲🇽",
            fotmob_id=262,
            caliente_url="https://sports.caliente.mx/es_MX/Futbol/Mexico/Liga-MX",
            is_active=True
        )
        db.add(liga)
        db.commit()
        db.refresh(liga)

    # 1. [ALT-8-B RATIFICADA — DICTAMEN DEL DIRECTOR 2026-10-04] Upsert IDEMPOTENTE del catálogo
    # fáctico de clubes (ALT-8-C). PROHIBIDO el borrado destructivo
    # (`~Team.canonical_slug.in_(...)`): amputaba las filas sembradas por la ingesta viva
    # (`centinela_deportivo.py`, Fase 4) y dejaba 27 filas (9 fácticas + 18 legadas) en cada
    # arranque del servidor (`src/web/app.py:34`) y en las suites compuestas de The Shield.
    # Clave de reconciliación DUAL: `canonical_slug` OR `fotmob_team_id` ⇒ si el club ya existe
    # sólo se actualizan metadatos; si la bóveda es virgen, se da de alta con su identidad
    # fáctica. Idempotente: con los 18 clubes ya presentes no genera tuplas residuales.
    for t in TEAMS_LIGA_MX:
        crest = f"/static/img/crests/{t['slug']}.png"
        team_rec = db.query(Team).filter(
            (Team.canonical_slug == t["slug"]) | (Team.fotmob_team_id == t["fotmob_id"])
        ).first()
        if not team_rec:
            db.add(Team(
                league_id=liga.id,
                fotmob_team_id=t["fotmob_id"],
                name=t["name"],
                short_name=t["short"],
                canonical_slug=t["slug"],
                crest_url=crest
            ))
        else:
            team_rec.league_id = liga.id
            team_rec.fotmob_team_id = t["fotmob_id"]
            team_rec.name = t["name"]
            team_rec.short_name = t["short"]
            team_rec.canonical_slug = t["slug"]
            team_rec.crest_url = crest
    db.commit()

    # 2. Formatear filas con escudos locales válidos
    standings_iniciales = []
    for row in TABLA_OFICIAL_J7_CONCLUIDA:
        eq = row["equipo"]
        slug = canonicalize_team_name(eq).lower().replace(" ", "-").replace(".", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        standings_iniciales.append({
            "pos": row["pos"],
            "equipo": eq,
            # [VARIANZA-09 / 12.7 RATIFICADA — DICTAMEN DEL DIRECTOR 2026-10-04] Erradicada la
            # fabricación `10000 + pos` ([GOVERNANCE-01]): la identidad se proyecta desde el
            # catálogo fáctico ratificado (ALT-8-C) por nombre canónico. Cero IDs inventados.
            "fotmob_id": _FOTMOB_ID_POR_NOMBRE.get(eq),
            "escudo_url": f"/static/img/crests/{slug}.png",
            "proximo_escudo_url": None,
            "pj": row["pj"],
            "pg": row["pg"],
            "pe": row["pe"],
            "pp": row["pp"],
            "gf": row["gf"],
            "gc": row["gc"],
            "dif": row["dif"],
            "puntos": row["puntos"],
            "forma": ["G", "E", "G", "P", "G"],
            "xg": row["xg"],
            "xga": row["xga"],
            "xpts": row["xpts"],
            "proximo_rival": "Por definir"
        })

    # Guardar snapshot solo si la base de datos está totalmente vacía (Cold Start)
    snap_existente = db.query(StandingSnapshot).filter(StandingSnapshot.league_id == liga.id).first()
    if not snap_existente:
        db.add(StandingSnapshot(league_id=liga.id, season="2026", matchday=8, positions_json=standings_iniciales))
        db.commit()
        print("[SEEDER]: Snapshot inicial de posiciones sembrado en SQLite.")
    else:
        print("[SEEDER]: Snapshot de posiciones existente preservado en SQLite.")

    # Guardar fixture snapshot si la base de datos no tiene partidos
    from src.storage.models import FixtureSnapshot
    fix_existente = db.query(FixtureSnapshot).filter(FixtureSnapshot.league_id == liga.id).first()
    if not fix_existente:
        fixtures_iniciales_j8 = [
            {
                "id_partido": "j8_01",
                "local": "Deportivo Toluca",
                "visitante": "Santos Laguna",
                "horario": "Sábado 19:00",
                "fecha_bloque": "Sábado 12 de Septiembre",
                "fecha_dt": "2026-09-12T19:00:00",
                "estado": "PROGRAMADO",
                "disponible_para_seleccion": True,
                "local_escudo_url": "/static/img/crests/toluca.png",
                "visitante_escudo_url": "/static/img/crests/santos-laguna.png",
                "momios": {"L": 1.70, "E": 3.60, "V": 4.50, "pago_anticipado": True}
            },
            {
                "id_partido": "j8_02",
                "local": "Club América",
                "visitante": "Chivas Guadalajara",
                "horario": "Sábado 21:00",
                "fecha_bloque": "Sábado 12 de Septiembre",
                "fecha_dt": "2026-09-12T21:00:00",
                "estado": "PROGRAMADO",
                "disponible_para_seleccion": True,
                "local_escudo_url": "/static/img/crests/america.png",
                "visitante_escudo_url": "/static/img/crests/guadalajara.png",
                "momios": {"L": 2.10, "E": 3.25, "V": 3.40, "pago_anticipado": True}
            },
            {
                "id_partido": "j8_03",
                "local": "Cruz Azul",
                "visitante": "Pumas UNAM",
                "horario": "Domingo 12:00",
                "fecha_bloque": "Domingo 13 de Septiembre",
                "fecha_dt": "2026-09-13T12:00:00",
                "estado": "PROGRAMADO",
                "disponible_para_seleccion": True,
                "local_escudo_url": "/static/img/crests/cruz-azul.png",
                "visitante_escudo_url": "/static/img/crests/pumas-unam.png",
                "momios": {"L": 1.95, "E": 3.40, "V": 3.80, "pago_anticipado": True}
            },
            {
                "id_partido": "j8_04",
                "local": "Tigres UANL",
                "visitante": "Club León",
                "horario": "Domingo 17:00",
                "fecha_bloque": "Domingo 13 de Septiembre",
                "fecha_dt": "2026-09-13T17:00:00",
                "estado": "PROGRAMADO",
                "disponible_para_seleccion": True,
                "local_escudo_url": "/static/img/crests/tigres-uanl.png",
                "visitante_escudo_url": "/static/img/crests/leon.png",
                "momios": {"L": 1.85, "E": 3.50, "V": 4.10, "pago_anticipado": True}
            },
            {
                "id_partido": "j8_05",
                "local": "Rayados de Monterrey",
                "visitante": "Club Puebla",
                "horario": "Domingo 19:00",
                "fecha_bloque": "Domingo 13 de Septiembre",
                "fecha_dt": "2026-09-13T19:00:00",
                "estado": "PROGRAMADO",
                "disponible_para_seleccion": True,
                "local_escudo_url": "/static/img/crests/monterrey.png",
                "visitante_escudo_url": "/static/img/crests/puebla.png",
                "momios": {"L": 1.65, "E": 3.75, "V": 4.80, "pago_anticipado": True}
            },
            {
                "id_partido": "j8_06",
                "local": "Club Tijuana",
                "visitante": "Atlas FC",
                "horario": "Viernes 21:00",
                "fecha_bloque": "Viernes 11 de Septiembre",
                "fecha_dt": "2026-09-11T21:00:00",
                "estado": "PROGRAMADO",
                "disponible_para_seleccion": True,
                "local_escudo_url": "/static/img/crests/club-tijuana.png",
                "visitante_escudo_url": "/static/img/crests/atlas.png",
                "momios": {"L": 2.05, "E": 3.30, "V": 3.50, "pago_anticipado": True}
            },
            {
                "id_partido": "j8_07",
                "local": "Atlético San Luis",
                "visitante": "Necaxa",
                "horario": "Sábado 17:00",
                "fecha_bloque": "Sábado 12 de Septiembre",
                "fecha_dt": "2026-09-12T17:00:00",
                "estado": "PROGRAMADO",
                "disponible_para_seleccion": True,
                "local_escudo_url": "/static/img/crests/atletico-san-luis.png",
                "visitante_escudo_url": "/static/img/crests/necaxa.png",
                "momios": {"L": 2.45, "E": 3.10, "V": 2.90, "pago_anticipado": True}
            },
            {
                "id_partido": "j8_08",
                "local": "Club Pachuca",
                "visitante": "FC Juárez",
                "horario": "Sábado 19:05",
                "fecha_bloque": "Sábado 12 de Septiembre",
                "fecha_dt": "2026-09-12T19:05:00",
                "estado": "PROGRAMADO",
                "disponible_para_seleccion": True,
                "local_escudo_url": "/static/img/crests/pachuca.png",
                "visitante_escudo_url": "/static/img/crests/fc-juarez.png",
                "momios": {"L": 1.75, "E": 3.50, "V": 4.50, "pago_anticipado": True}
            }
        ]
        db.add(FixtureSnapshot(league_id=liga.id, matchday=8, matches_json=fixtures_iniciales_j8))
        db.commit()
        print("[SEEDER]: Snapshot inicial de partidos (Jornada 8) sembrado en SQLite.")


def seed_initial_leagues():
    asegurar_boveda_escudos_base()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from src.storage.curation_service import asegurar_logo_liga_incremental
        seed_initial_data(db)
        asegurar_logo_liga_incremental(262, db)
    finally:
        db.close()
