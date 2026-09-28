# -*- coding: utf-8 -*-
"""
HERRAMIENTA DE SANEAMIENTO Y PURGA SELECTIVA SQLITE [ARCH-1.6.10]
Doctrina: Kybern Framework v8.0 / v12.0
Resetea snapshots obsoletos (fixtures, standings, portfolio_records)
preservando de forma inmutable el catálogo de 'leagues' y 'teams'.
"""

import sys
import os
from pathlib import Path

# Agregar raíz al PATH
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.storage.database import SessionLocal
from src.storage.models import (
    FixtureSnapshot, StandingSnapshot, PortfolioRecord,
    CurrentTeamStanding, MatchdayState, Match,
    SovereignDistribution, Slate, SlateItem
)


def purgar_base_datos():
    """[ARCH-1.6.10-B] Purga atómica total de entidades 3NF y snapshots volátiles."""
    print("🧹 Iniciando protocolo de saneamiento y purga atómica 3NF...")
    session = SessionLocal()
    try:
        n_items = session.query(SlateItem).delete()
        n_slates = session.query(Slate).delete()
        n_dist = session.query(SovereignDistribution).delete()
        n_matches = session.query(Match).delete()
        n_fixtures = session.query(FixtureSnapshot).delete()
        n_standings = session.query(StandingSnapshot).delete()
        n_portfolio = session.query(PortfolioRecord).delete()
        n_current = session.query(CurrentTeamStanding).delete()
        n_states = session.query(MatchdayState).delete()

        session.commit()
        print("✅ Purga atómica 3NF completada:")
        print(f"   - SlateItems: {n_items} | Slates: {n_slates}")
        print(f"   - SovereignDistributions: {n_dist} | Matches: {n_matches}")
        print(f"   - Snapshots: {n_fixtures + n_standings} | Standings: {n_current}")
        print("🔒 Catálogos maestros de 'leagues' y 'teams' PRESERVADOS INTATCOS.")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    purgar_base_datos()
