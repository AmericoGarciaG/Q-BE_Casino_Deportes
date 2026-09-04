import os
import pytest
from src.storage.seeder import seed_initial_leagues
from src.storage.sync_service import sync_active_leagues_data
from src.storage.database import SessionLocal
from src.storage.models import League, StandingSnapshot, FixtureSnapshot

def test_bootstrap_database_and_seeder():
    # 1. Ejecutar seeder
    seed_initial_leagues()
    
    db = SessionLocal()
    try:
        league = db.query(League).filter(League.fotmob_id == 262).first()
        assert league is not None
        assert league.name == "Liga MX"
        assert league.country == "México"

        # 2. Ejecutar sync service
        sync_active_leagues_data()

        standing = db.query(StandingSnapshot).filter(StandingSnapshot.league_id == league.id).first()
        assert standing is not None
        assert len(standing.positions_json) >= 18

        fixture = db.query(FixtureSnapshot).filter(FixtureSnapshot.league_id == league.id).first()
        assert fixture is not None
        assert len(fixture.matches_json) > 0
    finally:
        db.close()

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "ONLINE"
    assert json_data["database"] == "CONNECTED"

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Q-BE CASINO DEPORTES" in response.text

