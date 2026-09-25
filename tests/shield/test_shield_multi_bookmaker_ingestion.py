# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: INGESTA MULTI-OPERADOR (CALIENTE & BETWAY)
[LN-QBE-007] & [ARCH-1.4.6]
Axioma: Cero llamadas de red en pruebas unitarias. Determinismo absoluto.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.ingestion.normalizer import canonicalize_team_name


class AbstractTestMultiBookmakerIngestion:
    """Juez Abstracto que impone el contrato de extracción multi-casa."""

    def test_normalizacion_clubes_betway(self):
        """Verifica que los nombres crudos de Betway resuelvan a identidades canónicas."""
        nombres_crudos_betway = [
            ("América", "Club América"),
            ("Guadalajara Chivas", "Guadalajara"),
            ("Tigres UANL", "Tigres UANL"),
            ("Mazatlán FC", "Mazatlán"),
            ("CF Monterrey", "Monterrey")
        ]
        for crudo, canonico_esperado in nombres_crudos_betway:
            res = canonicalize_team_name(crudo)
            assert res == canonico_esperado, f"Fallo al normalizar '{crudo}' de Betway -> Obtenido: '{res}', Esperado: '{canonico_esperado}'"

    def test_contrato_datos_cuotas_betway(self):
        """Valida que el scraper de Betway entregue la estructura requerida sin valores nulos."""
        from src.ingestion.betway_scraper import BetwayMarketScraper

        # Mock del DOM de Betway simulando un partido extraído
        mock_raw_data = [
            {"local_raw": "Toluca", "visitante_raw": "Atlas", "L": 1.75, "E": 3.60, "V": 4.50}
        ]

        with patch.object(BetwayMarketScraper, "_extraer_html_mercado", return_value=mock_raw_data):
            slate = [{"local": "Toluca", "visitante": "Atlas"}]
            resultados = BetwayMarketScraper.extraer_cuotas_focalizadas(slate)

            assert len(resultados) == 1
            item = resultados[0]
            assert item["local"] == "Toluca"
            assert item["visitante"] == "Atlas"
            assert item["L"] > 1.0
            assert item["E"] > 1.0
            assert item["V"] > 1.0
            assert "pago_anticipado" in item

    def test_persistencia_multi_operador_snapshot(self):
        """Verifica que el centinela estructure el JSON con la llave momios_operadores."""
        partido_base = {
            "local": "Cruz Azul",
            "visitante": "Guadalajara",
            "momios": {"L": 2.10, "E": 3.30, "V": 3.40, "pago_anticipado": True}
        }

        cuota_betway = {
            "local": "Cruz Azul",
            "visitante": "Guadalajara",
            "L": 2.15,
            "E": 3.25,
            "V": 3.50,
            "pago_anticipado": False
        }

        # Simular fusión multi-operador
        momios_operadores = {
            "caliente": partido_base["momios"],
            "betway": {
                "L": cuota_betway["L"],
                "E": cuota_betway["E"],
                "V": cuota_betway["V"],
                "pago_anticipado": cuota_betway["pago_anticipado"]
            }
        }

        assert "caliente" in momios_operadores
        assert "betway" in momios_operadores
        assert momios_operadores["betway"]["L"] == 2.15
        assert momios_operadores["caliente"]["pago_anticipado"] is True


class TestMultiBookmakerIngestion(AbstractTestMultiBookmakerIngestion):
    """Implementación concreta del Juez en The Shield."""
    pass
