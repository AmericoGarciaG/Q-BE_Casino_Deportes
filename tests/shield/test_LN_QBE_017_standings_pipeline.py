# -*- coding: utf-8 -*-
"""
Prueba Concreta: [LN-QBE-017] Ingesta Fáctica Soberana de la Tabla General
Base de Gobierno: Kybern Framework v8.0 / v12.0
"""
from typing import Dict, Any, List
from tests.shield.abstract_test_LN_QBE_017_standings_pipeline import AbstractTestLN_QBE_017_StandingsPipeline
from src.storage.sync_service import sync_league_live_board
from src.storage.database import SessionLocal
import src.ingestion.providers.fotmob_provider as f_module

class TestLN_QBE_017_StandingsPipeline_Concrete(AbstractTestLN_QBE_017_StandingsPipeline):

    def obtener_tabla_posiciones_liga_mx(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            board = sync_league_live_board(league_id=262, db=db, force_refresh=force_refresh)
            return board.get("standings", [])

    def verificar_presencia_mock_estatico(self) -> bool:
        # Verifica que la constante LIGA_MX_CLUBS_DYNAMIC_FALLBACK ya no exista en fotmob_provider
        return hasattr(f_module, "LIGA_MX_CLUBS_DYNAMIC_FALLBACK")
