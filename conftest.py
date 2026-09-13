# -*- coding: utf-8 -*-
"""
conftest.py — Kybern Framework v12.0
Guard de Entorno para el Escudo de Pruebas.

Activa KYBERN_NO_SCRAPE=1 para toda la sesión de pytest,
impidiendo que `sync_league_live_board` lance Playwright/Chromium
durante los tests. Los tests de red real deben marcarse con
@pytest.mark.network y ejecutarse de forma manual con:
    KYBERN_NO_SCRAPE=0 pytest -m network
"""
import os
import pytest


def pytest_configure(config):
    """Activar el guard de scraping al iniciar pytest."""
    os.environ.setdefault("KYBERN_NO_SCRAPE", "1")
    config.addinivalue_line(
        "markers",
        "network: marca pruebas que requieren red/Playwright real (excluidas en CI)"
    )
