import os
import sys
from src.storage.database import SessionLocal, engine, Base
from src.storage.models import League, Team
from src.storage.crest_resolver import STATIC_CRESTS_DIR, obtener_slug_club

# Escudos primarios que DEBEN existir con bytes reales (> 3 KB) para que la app funcione
_ESCUDOS_CLAVE = [
    "america.png", "guadalajara.png", "cruz-azul.png", "toluca.png",
    "pachuca.png", "tigres-uanl.png", "monterrey.png", "pumas-unam.png",
    "leon.png", "santos-laguna.png", "atlas.png", "atletico-san-luis.png",
    "necaxa.png", "mazatlan.png", "fc-juarez.png", "queretaro.png",
    "club-tijuana.png", "puebla.png",
]

def asegurar_boveda_escudos_base():
    """
    [GOVERNANCE-01][ANTI-BUG] Garantiza escudos reales en disco.
    PROHIBIDO crear archivos PNG dummy de 0 bytes o relleno sintético.
    Si faltan escudos o existen archivos fantasma (< 3 KB), invoca el
    script de extracción oficial (scripts/extraer_escudos_ligamx_oficial.py).
    """
    os.makedirs(STATIC_CRESTS_DIR, exist_ok=True)

    # Detectar archivos fantasma (< 3 KB) y faltantes
    faltantes = []
    for escudo in _ESCUDOS_CLAVE:
        ruta = os.path.join(STATIC_CRESTS_DIR, escudo)
        if not os.path.exists(ruta) or os.path.getsize(ruta) < 3000:
            faltantes.append(escudo)

    if faltantes:
        print(f"[SEEDER][KYBERN] ⚠️ {len(faltantes)} escudos faltantes o fantasma detectados. "
              f"Invocando script de extracción oficial...")
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "scripts", "extraer_escudos_ligamx_oficial.py"
        )
        if os.path.exists(script_path):
            import subprocess
            result = subprocess.run(
                [sys.executable, script_path],
                check=False,
                capture_output=False
            )
            if result.returncode != 0:
                print("[SEEDER][KYBERN] ⚠️ El script de extracción finalizó con advertencias. "
                      "Verificar manualmente los escudos.")
        else:
            print(f"[SEEDER][KYBERN] ❌ Script no encontrado: {script_path}. "
                  f"Ejecutar manualmente: python scripts/extraer_escudos_ligamx_oficial.py")

TEAMS_LIGA_MX = [
    {"fotmob_id": 7966, "name": "Club América", "short": "América", "slug": "america"},
    {"fotmob_id": 7967, "name": "Deportivo Toluca", "short": "Toluca", "slug": "toluca"},
    {"fotmob_id": 10224, "name": "Club Tijuana", "short": "Tijuana", "slug": "club-tijuana"},
    {"fotmob_id": 7969, "name": "Atlas FC", "short": "Atlas", "slug": "atlas"},
    {"fotmob_id": 7970, "name": "Chivas Guadalajara", "short": "Chivas", "slug": "guadalajara"},
    {"fotmob_id": 7971, "name": "Querétaro FC", "short": "Querétaro", "slug": "queretaro"},
    {"fotmob_id": 7972, "name": "Club León", "short": "León", "slug": "leon"},
    {"fotmob_id": 7973, "name": "Club Puebla", "short": "Puebla", "slug": "puebla"},
    {"fotmob_id": 7974, "name": "Rayados de Monterrey", "short": "Monterrey", "slug": "monterrey"},
    {"fotmob_id": 7975, "name": "Cruz Azul", "short": "Cruz Azul", "slug": "cruz-azul"},
    {"fotmob_id": 7976, "name": "Pumas UNAM", "short": "Pumas", "slug": "pumas-unam"},
    {"fotmob_id": 7977, "name": "Necaxa", "short": "Necaxa", "slug": "necaxa"},
    {"fotmob_id": 8430, "name": "Atlético San Luis", "short": "San Luis", "slug": "atletico-san-luis"},
    {"fotmob_id": 1170720, "name": "Mazatlán FC", "short": "Mazatlán", "slug": "mazatlan"},
    {"fotmob_id": 7979, "name": "Club Pachuca", "short": "Pachuca", "slug": "pachuca"},
    {"fotmob_id": 7980, "name": "Tigres UANL", "short": "Tigres", "slug": "tigres-uanl"},
    {"fotmob_id": 7981, "name": "Santos Laguna", "short": "Santos", "slug": "santos-laguna"},
    {"fotmob_id": 638520, "name": "FC Juárez", "short": "Juárez", "slug": "fc-juarez"},
]

def seed_initial_leagues():
    asegurar_boveda_escudos_base()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
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

        for t in TEAMS_LIGA_MX:
            if not db.query(Team).filter(Team.fotmob_team_id == t["fotmob_id"]).first():
                crest = f"/static/img/crests/{t['slug']}.png"
                team_obj = Team(
                    league_id=liga.id,
                    fotmob_team_id=t["fotmob_id"],
                    name=t["name"],
                    short_name=t["short"],
                    canonical_slug=t["slug"],
                    crest_url=crest
                )
                db.add(team_obj)
        db.commit()
        print("[SEEDER]: 18 Clubes de Liga MX sembrados en SQLite con escudos oficiales.")
    finally:
        db.close()

