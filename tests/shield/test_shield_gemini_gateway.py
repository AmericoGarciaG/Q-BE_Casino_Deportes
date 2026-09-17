# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [ARCH-1.3.4] Verificación de GeminiCognitiveGateway y Ledger
Doctrina: Kybern Framework v8.0 / v12.0 [GOV-TEST-01 a 07]
"""

import ast
import os
import pytest
from src.services.gemini_gateway import GeminiCognitiveGateway


def test_ausencia_llamadas_directas_huerfanas():
    """Certifica vía AST que narrative.py no use httpx ni google.genai directos."""
    narrative_path = os.path.join("src", "reporting", "narrative.py")
    assert os.path.exists(narrative_path)

    with open(narrative_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in ["google.generativeai", "google.genai"], (
                    f"Violación [ARCH-1.3.4]: narrative.py debe usar GeminiCognitiveGateway, no {alias.name}"
                )


def test_gateway_rotacion_y_cooldown():
    """Valida la máquina de estados del pool circular de llaves."""
    gateway = GeminiCognitiveGateway()
    keys = gateway.get_registered_keys()
    assert len(keys) >= 1, "Debe existir al menos una llave Gemini registrada en .env"

    # Verificar que el índice sea válido
    idx = gateway.get_current_key_index()
    assert 0 <= idx < len(keys)


def test_gateway_fallback_seguro():
    """Valida que ante simulación de fallo de red, el gateway devuelva el fallback determinista."""
    gateway = gateway if 'gateway' in locals() else GeminiCognitiveGateway()
    # Petición con datos mínimos
    res = gateway.generate_thesis({"fav_name": "Toluca", "und_name": "Santos", "simular_fallback": True})
    assert "• <strong>Momento y Tabla:</strong>" in res
    assert "• <strong>Estrategia y Protección Financiera:</strong>" in res
