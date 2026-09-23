# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [ARCH-1.6.13 / VAULT-DAEMON-001-B] Verificacion de Ingesta Total (J1 a J17)
Doctrina: Kybern Framework v12.0 [DIRGEN-SEALED] [GOV-TEST-01 a 07]
Regimen: [DIRGEN-STRICT]
VARIANZA RESUELTA: league_id se resuelve via fotmob_id=262 (FK interna id=1, no hardcodeada).
"""

import pytest
from src.storage.gateway import PersistenceGateway
from src.storage.models import FixtureSnapshot, StandingSnapshot, League


def test_base_de_datos_contiene_multiples_jornadas_y_tablas():
    """Valida que existan fixtures y tablas para al menos 3 jornadas distintas en SQLite."""
    gateway = PersistenceGateway()

    with gateway.read_session() as session:
        # Resolver league_id interno via fotmob_id soberano (fotmob_id=262 -> liga.id interno)
        liga = session.query(League).filter(League.fotmob_id == 262).first()
        assert liga is not None, "Liga MX (fotmob_id=262) no encontrada en SQLite"
        lid = liga.id

        # 1. Verificar fixtures para al menos jornadas 8, 9 y 10
        jornadas_fixtures = session.query(FixtureSnapshot.matchday).filter(
            FixtureSnapshot.league_id == lid
        ).distinct().all()
        j_nums = [j[0] for j in jornadas_fixtures if j[0] is not None]

        assert len(j_nums) >= 3, f"Fallo de cobertura: solo existen jornadas {j_nums}"
        assert 8 in j_nums and 9 in j_nums and 10 in j_nums

        # 2. Verificar que cada jornada tenga sus partidos
        snap_j8 = session.query(FixtureSnapshot).filter(FixtureSnapshot.matchday == 8, FixtureSnapshot.league_id == lid).first()
        snap_j9 = session.query(FixtureSnapshot).filter(FixtureSnapshot.matchday == 9, FixtureSnapshot.league_id == lid).first()
        snap_j10 = session.query(FixtureSnapshot).filter(FixtureSnapshot.matchday == 10, FixtureSnapshot.league_id == lid).first()

        assert snap_j8 and len(snap_j8.matches_json) >= 9
        assert snap_j9 and len(snap_j9.matches_json) >= 9
        assert snap_j10 and len(snap_j10.matches_json) >= 9

        # 3. Validar que la tabla historica de la J8 tenga 8 PJ y la de la J9 tenga 9 PJ
        snap_t8 = session.query(StandingSnapshot).filter(StandingSnapshot.matchday == 8, StandingSnapshot.league_id == lid).first()
        snap_t9 = session.query(StandingSnapshot).filter(StandingSnapshot.matchday == 9, StandingSnapshot.league_id == lid).first()

        # Si aun no se han poblado snapshots historicos diferenciados, este test debe fallar
        assert snap_t8 is not None, "Falta snapshot historico de tabla para Jornada 8"
        assert snap_t9 is not None, "Falta snapshot historico de tabla para Jornada 9"

        t8_pj = snap_t8.positions_json[0]["pj"]
        t9_pj = snap_t9.positions_json[0]["pj"]
        assert t8_pj == 8, f"La tabla de J8 debio tener 8 PJ, tiene {t8_pj}"
        assert t9_pj == 9, f"La tabla de J9 debio tener 9 PJ, tiene {t9_pj}"
