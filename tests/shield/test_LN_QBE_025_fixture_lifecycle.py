# -*- coding: utf-8 -*-
"""
PRUEBA CONCRETA — EL PRISIONERO: [LN-QBE-025] Ciclo de Vida del Fixture
Hereda del Juez Inmutable AbstractTestLN_QBE_025_FixtureLifecycle.

ESTADO OBJETIVO: GREEN (EXIT CODE 0)
Versión: Materialización POST-Paso-3.
"""
from datetime import datetime
from typing import Dict, Any, List

from fastapi.testclient import TestClient

from tests.shield.abstract_test_LN_QBE_025_fixture_lifecycle import AbstractTestLN_QBE_025_FixtureLifecycle
from src.web.app import app
from src.storage.seeder import seed_initial_leagues


class TestLN_QBE_025_FixtureLifecycle_Concrete(AbstractTestLN_QBE_025_FixtureLifecycle):
    """
    El Prisionero: implementación concreta que consume el endpoint real del Live Board
    tras la materialización del Paso 3. Debe satisfacer las 5 invariantes del Juez Abstracto.
    """

    def setup_method(self):
        """Precondición: asegurar que la Liga MX esté sembrada en la base de datos."""
        seed_initial_leagues()

    def obtener_fixtures_live_board(self, league_id: int) -> List[Dict[str, Any]]:
        """
        Implementación concreta: consume GET /api/leagues/{league_id}/live-board
        y extrae la lista de fixtures con los campos semánticos canónicos [ARCH-1.6.3].
        """
        client = TestClient(app)
        resp = client.get(f"/api/leagues/{league_id}/live-board")
        assert resp.status_code == 200, (
            f"El endpoint /api/leagues/{league_id}/live-board retornó HTTP {resp.status_code}. "
            f"Detalle: {resp.text}"
        )
        data = resp.json()
        fixtures = data.get("fixtures", [])
        assert isinstance(fixtures, list), "El campo 'fixtures' en LiveBoardOut no es una lista."
        return fixtures

    def evaluar_es_hoy(self, fecha_partido_str: str) -> bool:
        """
        Implementación concreta de la evaluación dinámica de 'es_hoy' [ARCH-1.6.3].
        Compara la fecha del partido contra datetime.now().date() en tiempo de ejecución.
        """
        try:
            dt_partido = datetime.fromisoformat(fecha_partido_str)
            return dt_partido.date() == datetime.now().date()
        except ValueError:
            return False
