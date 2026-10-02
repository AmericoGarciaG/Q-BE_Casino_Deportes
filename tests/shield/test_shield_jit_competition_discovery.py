
"""
🛡️ THE SHIELD — TWIN-TEST: DESCUBRIMIENTO JIT DE COMPETICIONES Y MULTI-LIGA
[LN-QBE-088, LN-QBE-089] & [ARCH-1.4.21, ARCH-1.6.19]
Régimen: [DIRGEN-STRICT]
Axioma: Cero llamadas de red en pruebas unitarias. Resiliencia total ante clubes no indexados.
"""

import os
import pytest
from abc import ABC, abstractmethod


class AbstractTestJITCompetitionDiscovery(ABC):
    """Juez Abstracto que audita la resolución JIT y la ingesta por demanda."""

    def test_parseo_fotmob_search_api_response(self):
        """Verifica que el parser extraiga el torneo y equipo de la respuesta de FotMob."""
        from src.ingestion.progol_resolver import parsear_respuesta_search_fotmob

        mock_fotmob_resp = {
            "teams": [
                {
                    "id": 9812,
                    "name": "Girona",
                    "leagueId": 47,
                    "leagueName": "LaLiga"
                }
            ]
        }

        res = parsear_respuesta_search_fotmob(mock_fotmob_resp, "Girona")
        assert res is not None
        assert res["fotmob_team_id"] == 9812
        assert res["team_name"] == "Girona"
        assert res["fotmob_league_id"] == 47
        assert res["league_name"] == "LaLiga"

    def test_resiliencia_club_bizarro_sin_resultados_search(self):
        """Verifica que si la búsqueda arroja vacío, retorne None (activando prior fiduciario)."""
        from src.ingestion.progol_resolver import parsear_respuesta_search_fotmob


        mock_vacio = {"teams": []}
        res = parsear_respuesta_search_fotmob(mock_vacio, "Durango")
        assert res is None

    def test_auto_registro_liga_en_sqlite_3nf(self):
        """Verifica que el resolver inserte la competición en la tabla League si no existe."""
        from src.ingestion.progol_resolver import registrar_liga_descubierta_si_no_existe
        from src.storage.gateway import PersistenceGateway
        from src.storage.models import League

        gateway = PersistenceGateway()
        datos_liga = {
            "fotmob_league_id": 47,
            "league_name": "LaLiga EA Sports",
            "country": "Spain",
        }

        with gateway.write_transaction() as session:

            session.query(League).filter(League.fotmob_id == 47).delete()


            liga_obj = registrar_liga_descubierta_si_no_existe(session, datos_liga)
            assert liga_obj is not None
            assert liga_obj.fotmob_id == 47
            assert "LaLiga" in liga_obj.name
            assert liga_obj.mu_liga == 2.60

            # [ANEXO-A — DICTAMEN ARCH-1.6.19-B] Directiva de sandbox: el Juez ejercita el auto-registro
            # sobre la MISMA transacción de la ingesta (flush, sin commit) y la revierte explícitamente
            # para no contaminar la bóveda de producción (data/qbe_database.db). El `commit()` del
            # contexto cierra una transacción vacía (los asertos corren EN MEMORIA antes del rollback).
            session.rollback()

    def test_centinela_deportivo_soporte_modo_multi_liga(self):
        """Verifica mediante inspección de código que centinela_deportivo admita modo multi-liga."""
        cd_path = os.path.join("scripts", "daemons", "centinela_deportivo.py")
        assert os.path.exists(cd_path), "centinela_deportivo.py no encontrado"

        with open(cd_path, "r", encoding="utf-8") as f:
            code = f.read()


        assert "sincronizar_todas_las_ligas" in code or "League.all" in code or "--liga" in code or "ligas_db" in code, \
            "Violación ARCH-1.6.19: centinela_deportivo sigue atado exclusivamente a Liga MX (LEAGUE_ID=262)"


class TestJITCompetitionDiscovery(AbstractTestJITCompetitionDiscovery):
    """Implementación concreta en The Shield."""
    pass

