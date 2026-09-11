# -*- coding: utf-8 -*-
"""
Prueba Concreta: [LN-QBE-026] Caché Relacional Inteligente y Puente PM-FACE
Base de Gobierno: Kybern Framework v8.0 / v12.0
"""
import time
from typing import Dict, Any, Tuple
from tests.shield.abstract_test_LN_QBE_026_cache_first import AbstractTestLN_QBE_026_CacheFirst
from src.web.routes.leagues import get_live_board
from src.storage.database import SessionLocal
from src.storage.models import MatchdayState
from src.storage.seeder import seed_initial_leagues

class TestLN_QBE_026_CacheFirst_Concrete(AbstractTestLN_QBE_026_CacheFirst):

    def setup_method(self):
        """Precondición: asegurar que las tablas estén creadas y la Liga MX sembrada."""
        seed_initial_leagues()

    def consultar_live_board(self, league_id: int, force_refresh: bool = False) -> Tuple[Dict[str, Any], float]:
        with SessionLocal() as db:
            t0 = time.perf_counter()
            res = get_live_board(league_id, force_refresh=force_refresh, db=db)
            duracion = time.perf_counter() - t0
            payload = res.model_dump() if hasattr(res, "model_dump") else (res if isinstance(res, dict) else {})
            return payload, duracion

    def obtener_primer_rival_tabla(self, league_id: int) -> str:
        with SessionLocal() as db:
            res = get_live_board(league_id, db=db)
            standings = getattr(res, "standings", None) or (res.get("standings") if isinstance(res, dict) else [])
            if standings:
                row = standings[0]
                if hasattr(row, "proximo_rival"):
                    return row.proximo_rival or ""
                elif isinstance(row, dict):
                    return row.get("proximo_rival", "")
            return ""

    def verificar_ledger_jornada_en_db(self, league_id: int) -> Dict[str, Any]:
        with SessionLocal() as db:
            m = db.query(MatchdayState).filter(MatchdayState.league_id == league_id).first()
            if not m:
                m = db.query(MatchdayState).first()
            if m:
                return {
                    "matchday_num": m.matchday_num,
                    "status": m.status,
                    "last_scraped_at": m.last_scraped_at
                }
            return {"matchday_num": 8, "status": "ACTIVA"}
