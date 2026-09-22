# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [GOVERNANCE-01 / ARCH-1.6.12] Verificación de Cero Alambrado en Centinela Deportivo
Doctrina: Kybern Framework v12.0 [DIRGEN-SEALED]
"""

import ast
import os
import pytest

CENTINELA_PATH = os.path.join("scripts", "daemons", "centinela_deportivo.py")


def test_centinela_no_contiene_funciones_certificadas_quemadas():
    """Valida vía AST que se hayan extirpado todas las funciones de tuplas estáticas."""
    assert os.path.exists(CENTINELA_PATH), "No existe centinela_deportivo.py"

    with open(CENTINELA_PATH, "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Prohibidas las funciones de respaldo quemado
    assert "_obtener_fixtures_certificados_j8" not in src, (
        "Violación [GOVERNANCE-01]: _obtener_fixtures_certificados_j8 detectada en código."
    )
    assert "_obtener_fixtures_certificados_j9" not in src, (
        "Violación [GOVERNANCE-01]: _obtener_fixtures_certificados_j9 detectada en código."
    )

    # 2. Parseo de AST para auditar literales de tuplas sospechosas
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            assert not node.name.startswith("_obtener_fixtures_certificados"), (
                f"Violación DirGen: Función de alambrado detectada: {node.name}"
            )

    # 3. Validar presencia del conversor dinámico oficial
    funciones = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert "_convertir_match_fotmob" in funciones, (
        "Falta función canónica _convertir_match_fotmob para ingesta dinámica."
    )
