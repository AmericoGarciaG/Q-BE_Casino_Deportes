from src.storage.database import SessionLocal, engine, Base
from src.storage.models import League

def seed_initial_leagues():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(League).filter(League.fotmob_id == 262).first():
            liga_mx = League(
                name="Liga MX",
                country="México",
                flag="🇲🇽",
                fotmob_id=262,
                caliente_url="https://sports.caliente.mx/es_MX/Futbol/Mexico/Liga-MX",
                is_active=True
            )
            db.add(liga_mx)
            db.commit()
            print("🌱 [SEEDER]: Liga MX inicializada en Base de Datos.")
    finally:
        db.close()
