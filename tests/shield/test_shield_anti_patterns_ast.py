"""
The Shield — Auditor Estático por Árbol Sintáctico (AST Hardcode Hunter).
[GOVERNANCE-01] [ANTI-BUG] [ALGO-PROTECTED]
Inspecciona todo el código en src/ y scripts/ para bloquear números mágicos y hardcodes en runtime.
"""

import ast
from pathlib import Path

ROOT_SRC = Path(__file__).resolve().parent.parent.parent / "src"
ROOT_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "scripts"


def test_no_hardcoded_magic_floats_in_portfolio_and_engine():
    """[SHIELD-AST] Prohíbe números fijos como 3.50 o 0.50 asignados a ganancias esperadas."""
    archivos_criticos = [
        ROOT_SRC / "core" / "portfolio.py",
        ROOT_SRC / "pipeline" / "engine.py"
    ]
    for filepath in archivos_criticos:
        if not filepath.exists():
            continue
        code = filepath.read_text(encoding="utf-8")
        tree = ast.parse(code, filename=str(filepath))

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "max":
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and arg.value in [3.50, 0.50, 3.5, 0.5]:
                        raise AssertionError(
                            f"Hardcode detectado en {filepath.name} (Línea {node.lineno}): "
                            f"Prohibido usar max({arg.value}, ...) para forzar pisos artificiales de ganancia."
                        )


def test_no_hardcoded_liga_mx_string_in_triage_and_pipeline():
    """[SHIELD-AST] Prohíbe hardcodear 'Liga MX' ignorando el torneo dinámico en origen."""
    archivos_ingesta = [
        ROOT_SCRIPTS / "run_pipeline.py",
        ROOT_SRC / "core" / "triage.py"
    ]
    for filepath in archivos_ingesta:
        if not filepath.exists():
            continue
        code = filepath.read_text(encoding="utf-8")
        assert '"liga": "Liga MX"' not in code, (
            f"Hardcode detectado en {filepath.name}: 'liga': 'Liga MX' debe ser dinámico (torneo_origen)."
        )


def test_no_p_fav_squared_penalty_in_portfolio():
    """[SHIELD-AST] Prohíbe castigar arbitrariamente a las apuestas directas con (p_fav ** 2)."""
    portfolio_file = ROOT_SRC / "core" / "portfolio.py"
    if portfolio_file.exists():
        code = portfolio_file.read_text(encoding="utf-8")
        assert "p_fav ** 2" not in code, (
            "Sesgo matemático detectado en portfolio.py: 'p_fav ** 2' está prohibido en cálculo de utilidad directa."
        )
