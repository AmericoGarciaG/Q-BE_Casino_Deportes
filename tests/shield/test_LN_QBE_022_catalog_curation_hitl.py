"""
Kybern Industrial Governance — The Shield (Prisionero Concreto)
Prueba Concreta: [ARCH-1.5.2 / LN-QBE-015 / DES-QBE-018] Curación Agéntica HITL y Bóveda de Activos
ID de Prueba: SHIELD-TEST-LN-QBE-022-CATALOG-HITL

ESTADO ESPERADO: RED (Fallo Documentado)
RAZÓN: Los endpoints /api/admin/catalogs/* NO EXISTEN en src/web/routes/admin.py.
       Este estado RED certifica la ausencia de implementación y activa el Paso 3
       (Materialización) del Motor de 3 Pasos según GOVERNANCE.md §4.
"""

from typing import Dict, Any, List
from fastapi.testclient import TestClient

from tests.shield.abstract_test_LN_QBE_022_catalog_curation_hitl import (
    AbstractTestCatalogCurationHITL,
)
from src.web.app import app


class TestLN_QBE_022_CatalogCurationHITL_Concrete(AbstractTestCatalogCurationHITL):
    """
    Prisionero Concreto que hereda del Juez Abstracto.
    Conecta los métodos abstractos al TestClient de FastAPI.
    """

    @property
    def client(self) -> TestClient:
        return TestClient(app)

    def trigger_discovery_api(self, league_id: int) -> Dict[str, Any]:
        """POST /api/admin/catalogs/discover?league_id={id}"""
        resp = self.client.post(f"/api/admin/catalogs/discover?league_id={league_id}")
        assert resp.status_code == 200, (
            f"[RED ESPERADO] POST /api/admin/catalogs/discover retornó {resp.status_code}. "
            f"El endpoint aún no existe — materialización pendiente (Paso 3)."
        )
        return resp.json()

    def fetch_staging_api(self, league_id: int) -> List[Dict[str, Any]]:
        """GET /api/admin/catalogs/staging?league_id={id}"""
        resp = self.client.get(f"/api/admin/catalogs/staging?league_id={league_id}")
        assert resp.status_code == 200, (
            f"[RED ESPERADO] GET /api/admin/catalogs/staging retornó {resp.status_code}. "
            f"El endpoint aún no existe — materialización pendiente (Paso 3)."
        )
        return resp.json()

    def commit_catalog_api(self, league_id: int, approved_teams: List[Dict[str, Any]]) -> Dict[str, Any]:
        """POST /api/admin/catalogs/commit"""
        resp = self.client.post(
            "/api/admin/catalogs/commit",
            json={"league_id": league_id, "approved_teams": approved_teams},
        )
        assert resp.status_code == 200, (
            f"[RED ESPERADO] POST /api/admin/catalogs/commit retornó {resp.status_code}. "
            f"El endpoint aún no existe — materialización pendiente (Paso 3)."
        )
        return resp.json()

    def get_public_live_board(self, league_id: int) -> Dict[str, Any]:
        """GET /api/leagues/{id}/live-board"""
        resp = self.client.get(f"/api/leagues/{league_id}/live-board")
        assert resp.status_code == 200, (
            f"GET /api/leagues/{league_id}/live-board retornó {resp.status_code}."
        )
        return resp.json()
