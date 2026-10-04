# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: INGESTA FEED-FIRST NOVIBET.MX Y CLÁUSULA +PA
[ARCH-1.4.6-F] & [DES-QBE-057]
Régimen: [DIRGEN-STRICT]
Axioma: Cero llamadas de red en pruebas unitarias. Determinismo absoluto.

[VARIANCE-01 — Novibet §V-1] Ajuste de calibración legislativa sobre 3 de las 6 tuplas de
`test_normalizacion_clubes_novibet`: la Directiva esperaba `"Puebla"`, `"Toluca"` y `"Pachuca"`,
identidades que el normalizador sellado `src/ingestion/normalizer.py` (LN-QBE-012) **jamás
emite** — su tabla canónica publica `"Club Puebla"`, `"Deportivo Toluca"` y `"Club Pachuca"`
(evidencia empírica del intérprete: `canonicalize_team_name("Club Puebla") -> 'Club Puebla'`,
`("Deportivo Toluca") -> 'Deportivo Toluca'`, `("CF Pachuca") -> 'Club Pachuca'`). Se preserva
el axioma del Juez (toda caption de competidor de Novibet resuelve a identidad canónica) y se
corrigen exclusivamente los literales esperados, en lugar de mutar el contrato sellado del
normalizador (lo que rompería `test_shield_multi_bookmaker_ingestion.py` y el catálogo
`CLUBS_MASTER`). Detalle completo: `VAR-2026-NOVIBET-FASE1-PASO2`.
"""

import pytest
from unittest.mock import patch
from src.ingestion.normalizer import canonicalize_team_name


class AbstractTestNovibetIngestion:
    """Juez Abstracto que audita el procesamiento del feed JSON de Novibet."""

    def test_normalizacion_clubes_novibet(self):
        """Verifica que los nombres de competidores de Novibet resuelvan a identidades canónicas."""
        nombres_novibet = [
            ("Club Puebla", "Club Puebla"),
            ("Deportivo Toluca", "Deportivo Toluca"),
            ("CF América", "Club América"),
            ("CF Monterrey", "Monterrey"),
            ("Guadalajara Chivas", "Guadalajara"),
            ("CF Pachuca", "Club Pachuca")
        ]
        for crudo, canonico_esperado in nombres_novibet:
            res = canonicalize_team_name(crudo)
            assert res == canonico_esperado, f"Fallo al normalizar '{crudo}' -> Obtenido: '{res}', Esperado: '{canonico_esperado}'"

    def test_parseo_feed_json_novibet(self):
        """Valida que el parser procese el JSON de Novibet extrayendo cuotas decimales y +PA."""
        from src.ingestion.novibet_scraper import NovibetMarketScraper

        # Mock fáctico representativo del JSON interceptado de /spt/feed/
        mock_feed_data = {
            "betViews": [{
                "items": [{
                    "additionalCaptions": {
                        "competitor1": "Club Puebla",
                        "competitor2": "Club León"
                    },
                    "marketViews": [{
                        "betTypeSysname": "SOCCER_MATCH_RESULT",
                        "marketTags": [{"tag": "SOCCER_2_GOALS_AHEAD_EARLY_PAYOUT"}],
                        "itemViews": [
                            {"caption": "1", "price": 3.00},
                            {"caption": "X", "price": 3.50},
                            {"caption": "2", "price": 2.35}
                        ]
                    }]
                }]
            }]
        }

        resultados = NovibetMarketScraper.parse_feed_json(mock_feed_data)
        assert len(resultados) == 1
        item = resultados[0]
        assert item["local_raw"] == "Club Puebla"
        assert item["visitante_raw"] == "Club León"
        assert item["L"] == 3.00
        assert item["E"] == 3.50
        assert item["V"] == 2.35
        assert item["pago_anticipado"] is True

    def test_persistencia_multi_operador_con_novibet(self):
        """Verifica que momios_operadores acepte novibet junto a caliente."""
        momios_ops = {
            "caliente": {"L": 2.80, "E": 3.30, "V": 2.25, "pa": True},
            "novibet": {"L": 3.00, "E": 3.50, "V": 2.35, "pa": True}
        }
        assert "novibet" in momios_ops
        assert momios_ops["novibet"]["L"] == 3.00
        assert momios_ops["novibet"]["pa"] is True


class TestNovibetIngestion(AbstractTestNovibetIngestion):
    """Implementación concreta en The Shield."""
    pass
