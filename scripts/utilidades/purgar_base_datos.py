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
    FixtureSnapshot,
    StandingSnapshot,
    PortfolioRecord,
    CurrentTeamStanding,
    MatchdayState
)


def purgar_base_datos():
    """Ejecuta la purga selectiva de tablas volátiles en SQLite."""
    print("🧹 Iniciando protocolo de saneamiento y purga selectiva SQLite...")
    session = SessionLocal()
    try:
        n_fixtures = session.query(FixtureSnapshot).delete()
        n_standings = session.query(StandingSnapshot).delete()
        n_portfolio = session.query(PortfolioRecord).delete()
        n_current_standings = session.query(CurrentTeamStanding).delete()
        n_matchday_states = session.query(MatchdayState).delete()

        session.commit()

        print("✅ Purga selectiva ejecutada con éxito:")
        print(f"   - Fixture Snapshots eliminados: {n_fixtures}")
        print(f"   - Standing Snapshots eliminados: {n_standings}")
        print(f"   - Portfolio Records eliminados: {n_portfolio}")
        print(f"   - Current Team Standings eliminados: {n_current_standings}")
        print(f"   - Matchday States eliminados: {n_matchday_states}")
        print("🔒 Catálogos inmutables de 'leagues' y 'teams' PRESERVADOS INTACATOS.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error durante la purga de SQLite: {e}")
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    purgar_base_datos()
