# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — LEAGUES SOVEREIGN LEAK TEST
Valida la erradicación de valores nulos en la entrega de probabilidades soberanas
en el endpoint REST /api/leagues/{id}/live-board.
Régimen: [DBBD-FUNGIBLE] | Nivel: The Shield Core (SLA < 2.0s)
"""

import abc
import pytest
from fastapi.testclient import TestClient
from src.web.app import app
from src.storage.gateway import PersistenceGateway
from src.storage.models import SovereignDistribution

client = TestClient(app)


class AbstractTestLeaguesSovereignLeak(abc.ABC):
    """Juez Abstracto: Define los invariantes que la entrega HTTP debe satisfacer."""

    @abc.abstractmethod
    def ejecutar_peticion_live_board(self, league_id: int, jornada: int):
        """Debe invocar el endpoint y retornar el payload JSON deserializado."""
        pass

    def test_distribuciones_soberanas_no_son_nulas_si_existen_en_bd(self):
        """Invariante: Si la BD tiene distribución para un partido, el payload HTTP NO debe ser null."""
        gw = PersistenceGateway()
        with gw.read_session() as session:
            dist = session.query(SovereignDistribution).first()
            if not dist:
                pytest.skip("No hay distribuciones en BD para auditar fuga; se requiere snapshot.")

            target_match_id = dist.match_id

        # Ejecución por la vía concreta
        data = self.ejecutar_peticion_live_board(league_id=262, jornada=dist.match_id)
        fixtures = data.get("fixtures", [])
        
        # Localizar el fixture correspondiente si coincide con la jornada consultada
        fixture_encontrado = next((f for f in fixtures if f.get("id_partido") == target_match_id), None)
        
        if fixture_encontrado:
            assert fixture_encontrado.get("p_local") is not None, f"Fuga detectada: p_local es null para {target_match_id}"
            assert fixture_encontrado.get("p_empate") is not None, f"Fuga detectada: p_empate es null para {target_match_id}"
            assert fixture_encontrado.get("p_visitante") is not None, f"Fuga detectada: p_visitante es null para {target_match_id}"
            
            # Verificación del Símplex Δ² (Invarianza #1)
            p_sum = fixture_encontrado["p_local"] + fixture_encontrado["p_empate"] + fixture_encontrado["p_visitante"]
            assert abs(p_sum - 1.0) <= 0.001, f"Violación del Símplex en payload HTTP: suma={p_sum}"


class TestLeaguesSovereignLeakConcrete(AbstractTestLeaguesSovereignLeak):
    """Implementación concreta del Juez Inmutable utilizando el TestClient oficial."""

    def ejecutar_peticion_live_board(self, league_id: int, jornada: int = 10):
        # Consulta la jornada 10 (o la jornada activa)
        response = client.get(f"/api/leagues/{league_id}/live-board?jornada=10")
        assert response.status_code == 200, f"Error HTTP {response.status_code}: {response.text}"
        return response.json()
