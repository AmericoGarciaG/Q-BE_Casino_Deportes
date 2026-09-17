# -*- coding: utf-8 -*-
"""
CENTINELA FORENSE AST: Verificación de Desacoplamiento de Scraping en Web
Doctrina: Kybern Framework v8.0 / v12.0 [ARCH-1.6.4]
Certifica que sync_service.py no importe playwright ni librerías de red síncronas.
"""

import ast
import os
import pytest

def test_sync_service_no_contiene_playwright_ni_scrapers():
    """Audita el árbol de sintaxis abstracta de sync_service.py."""
    sync_service_path = os.path.join("src", "storage", "sync_service.py")
    assert os.path.exists(sync_service_path), "No existe sync_service.py"

    with open(sync_service_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=sync_service_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "playwright" not in alias.name.lower(), f"Violación [ARCH-1.6.4]: Importación prohibida '{alias.name}' en sync_service.py"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert "playwright" not in node.module.lower(), f"Violación [ARCH-1.6.4]: Importación 'from {node.module}' prohibida en sync_service.py"
                assert "caliente_scraper" not in node.module.lower(), "Violación [ARCH-1.6.4]: caliente_scraper no debe importarse en plano web"
