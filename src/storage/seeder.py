from src.storage.database import SessionLocal, engine, Base
from src.storage.models import League, Team

TEAMS_LIGA_MX = [
    {"fotmob_id": 7966, "name": "Club América", "short": "América", "slug": "club-america"},
    {"fotmob_id": 7967, "name": "Deportivo Toluca", "short": "Toluca", "slug": "deportivo-toluca"},
    {"fotmob_id": 10224, "name": "Club Tijuana", "short": "Tijuana", "slug": "club-tijuana"},
    {"fotmob_id": 7969, "name": "Atlas FC", "short": "Atlas", "slug": "atlas-fc"},
    {"fotmob_id": 7970, "name": "Chivas Guadalajara", "short": "Chivas", "slug": "chivas-guadalajara"},
    {"fotmob_id": 7971, "name": "Querétaro FC", "short": "Querétaro", "slug": "queretaro-fc"},
    {"fotmob_id": 7972, "name": "Club León", "short": "León", "slug": "club-leon"},
    {"fotmob_id": 7973, "name": "Club Puebla", "short": "Puebla", "slug": "club-puebla"},
    {"fotmob_id": 7974, "name": "Rayados de Monterrey", "short": "Monterrey", "slug": "rayados-de-monterrey"},
    {"fotmob_id": 7975, "name": "Cruz Azul", "short": "Cruz Azul", "slug": "cruz-azul"},
    {"fotmob_id": 7976, "name": "Pumas UNAM", "short": "Pumas", "slug": "pumas-unam"},
    {"fotmob_id": 7977, "name": "Necaxa", "short": "Necaxa", "slug": "necaxa"},
    {"fotmob_id": 8430, "name": "Atlético San Luis", "short": "San Luis", "slug": "atletico-san-luis"},
    {"fotmob_id": 1170720, "name": "Mazatlán FC", "short": "Mazatlán", "slug": "mazatlan-fc"},
    {"fotmob_id": 7979, "name": "Club Pachuca", "short": "Pachuca", "slug": "club-pachuca"},
    {"fotmob_id": 7980, "name": "Tigres UANL", "short": "Tigres", "slug": "tigres-uanl"},
    {"fotmob_id": 7981, "name": "Santos Laguna", "short": "Santos", "slug": "santos-laguna"},
    {"fotmob_id": 638520, "name": "FC Juárez", "short": "Juárez", "slug": "fc-juarez"},
]

def seed_initial_leagues():
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
                crest = f"https://images.fotmob.com/image_resources/logo/teamlogo/{t['fotmob_id']}.png"
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
        print("🌱 [SEEDER]: 18 Clubes de Liga MX sembrados en SQLite con escudos oficiales.")
    finally:
        db.close()
