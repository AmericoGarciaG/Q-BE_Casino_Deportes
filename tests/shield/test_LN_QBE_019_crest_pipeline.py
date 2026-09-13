# -*- coding: utf-8 -*-
"""
Prueba Concreta: [LN-QBE-019] Pipeline de Resolución de Escudos y Bóveda Soberana
Base de Gobierno: Kybern Framework v8.0 / v12.0
"""
import os
from typing import Dict, Any, List
from tests.shield.abstract_test_LN_QBE_019_crest_pipeline import AbstractTestLN_QBE_019_CrestPipeline
from src.storage.crest_resolver import resolver_escudo_canonico, STATIC_CRESTS_DIR
from src.storage.database import SessionLocal
from src.storage.seeder import asegurar_boveda_escudos_base

class TestLN_QBE_019_CrestPipeline_Concrete(AbstractTestLN_QBE_019_CrestPipeline):

    def setup_method(self):
        # Garantizar que la bóveda física base esté inicializada para los tests
        asegurar_boveda_escudos_base()

    def resolver_escudo(self, equipo_nombre: str, fotmob_id: int = None) -> str:
        with SessionLocal() as db:
            return resolver_escudo_canonico(equipo_nombre, fotmob_id=fotmob_id, db=db)

    def obtener_live_board_standings(self, league_id: int) -> List[Dict[str, Any]]:
        # Simula los 18 clubes oficiales de la Liga MX resolviendo con el pipeline de producción
        clubes_liga_mx = [
            "América", "Guadalajara", "Cruz Azul", "Tigres UANL", "Monterrey",
            "Toluca", "Pachuca", "Pumas UNAM", "León", "Santos Laguna",
            "Atlas", "Atlético San Luis", "Necaxa", "Mazatlán", "FC Juárez",
            "Querétaro", "Tijuana", "Puebla"
        ]
        
        resultado = []
        with SessionLocal() as db:
            for idx, club in enumerate(clubes_liga_mx, 1):
                safe_url = resolver_escudo_canonico(club, db=db)
                resultado.append({
                    "pos": idx,
                    "equipo": club,
                    "escudo_url": safe_url,
                    "puntos": 30 - idx
                })
        return resultado
    def get_teams_from_db(self, league_id: int = 262) -> List[Dict[str, Any]]:
        from sqlalchemy import text
        from src.storage.models import League
        db = SessionLocal()
        try:
            league = db.query(League).filter((League.fotmob_id == league_id) | (League.id == league_id)).first()
            lid = league.id if league else league_id
            result = db.execute(
                text(
                    "SELECT id, league_id, fotmob_team_id, name, short_name, canonical_slug, crest_url FROM teams WHERE league_id = :lid"
                ),
                {"lid": lid},
            )
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception:
            return []
        finally:
            db.close()

    def get_live_board_payload(self, league_id: int = 262) -> Dict[str, Any]:
        from fastapi.testclient import TestClient
        from src.web.app import app
        client = TestClient(app)
        resp = client.get(f"/api/leagues/{league_id}/live-board")
        assert resp.status_code == 200, f"Error al consultar live-board: {resp.text}"
        return resp.json()


def test_invariante_cero_archivos_fantasma_o_vacios():
    """
    [INVARIANZA CRÍTICA - ANTI-BUG][GOVERNANCE-01]
    Ningún archivo de escudo en src/web/static/img/crests/ puede ser de 0 bytes
    o menor a 2.5 KB. Garantiza la ausencia total de archivos fantasma / dummies
    creados por seeders que violan el Axioma de Cero Datos Sintéticos.
    """
    assert os.path.exists(STATIC_CRESTS_DIR), (
        f"El directorio de escudos no existe: {STATIC_CRESTS_DIR}"
    )
    archivos_png = [f for f in os.listdir(STATIC_CRESTS_DIR) if f.endswith(".png")]
    assert len(archivos_png) >= 18, (
        f"Se esperaban al menos 18 escudos PNG en bóveda, se encontraron {len(archivos_png)}. "
        f"Ejecutar: python scripts/extraer_escudos_ligamx_oficial.py"
    )

    for archivo in archivos_png:
        path = os.path.join(STATIC_CRESTS_DIR, archivo)
        tamano = os.path.getsize(path)
        assert tamano > 2500, (
            f"Violación de Integridad [GOVERNANCE-01]: El archivo '{archivo}' es un archivo "
            f"fantasma de solo {tamano} bytes. Todos los escudos deben ser PNGs reales (> 2.5 KB). "
            f"Ejecutar: python scripts/extraer_escudos_ligamx_oficial.py"
        )
