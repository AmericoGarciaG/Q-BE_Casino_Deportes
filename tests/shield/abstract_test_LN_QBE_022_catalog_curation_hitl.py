"""
Kybern Industrial Governance — Twin-Test Protocol
Juez Inmutable: [ARCH-1.5.2 / LN-QBE-015 / DES-QBE-018] Curación Agéntica HITL y Bóveda de Activos
ID de Prueba: SHIELD-TEST-LN-QBE-022-CATALOG-HITL
"""
import abc
from typing import Dict, Any, List


class AbstractTestCatalogCurationHITL(abc.ABC):
    """
    Juez Abstracto que audita:
    1. Pipeline de prospección: Agente devuelve candidatos estructurados con nombre, aliases y URL de escudo.
    2. Aislamiento de Staging: Candidatos no aprobados NO se filtran a la API pública de Live Board.
    3. Commit Administrativo: Al confirmar candidatos, se escriben en la tabla `teams` de SQLite y se persisten localmente.
    4. Integridad de Activos: Los escudos guardados tienen tamaño real y extensión válida (.png).
    """

    @abc.abstractmethod
    def trigger_discovery_api(self, league_id: int) -> Dict[str, Any]:
        """Debe invocar POST /api/admin/catalogs/discover."""
        pass

    @abc.abstractmethod
    def fetch_staging_api(self, league_id: int) -> List[Dict[str, Any]]:
        """Debe invocar GET /api/admin/catalogs/staging."""
        pass

    @abc.abstractmethod
    def commit_catalog_api(self, league_id: int, approved_teams: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Debe invocar POST /api/admin/catalogs/commit."""
        pass

    @abc.abstractmethod
    def get_public_live_board(self, league_id: int) -> Dict[str, Any]:
        """Debe invocar GET /api/leagues/{id}/live-board."""
        pass

    # ══════════════════════════════════════════════════════════════════
    # ASERCIONES INMUTABLES DE CURACIÓN HITL
    # ══════════════════════════════════════════════════════════════════

    def test_discovery_pipeline_populates_staging_correctly(self):
        """[SHIELD-INVARIANTE] La prospección debe entregar clubes candidatos con aliases y URLs de escudos."""
        resp = self.trigger_discovery_api(262)
        assert resp.get("status") in ["STAGED", "SUCCESS"]

        staged_teams = self.fetch_staging_api(262)
        assert len(staged_teams) >= 18, f"Se esperaban al menos 18 clubes en staging, obtenidos: {len(staged_teams)}."

        sample = staged_teams[0]
        assert "name" in sample and "canonical_slug" in sample
        assert "crest_candidate_url" in sample and sample["crest_candidate_url"].startswith("http")
        assert "aliases" in sample and isinstance(sample["aliases"], list)

    def test_commit_persists_teams_and_seals_catalog_in_db(self):
        """[SHIELD-INVARIANTE] El commit administrativo debe escribir en SQLite y sellar el catálogo."""
        staged_teams = self.fetch_staging_api(262)
        assert len(staged_teams) >= 18

        commit_resp = self.commit_catalog_api(262, staged_teams)
        assert commit_resp.get("status") == "SEALED"
        assert commit_resp.get("teams_committed") >= 18

        # Validar que los clubes ahora se reflejen en la API pública
        board = self.get_public_live_board(262)
        assert len(board.get("standings", [])) == 18
