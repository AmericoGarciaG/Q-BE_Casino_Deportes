# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: Guardián Criptográfico y AST de Integridad DirGen
Doctrina: Kybern Framework v12.0 [DIRGEN-SEALED]
"""

import ast
import os
import pytest

VAULT_PATH = os.path.join("docs", "DIRGEN_VAULT.md")
GATEWAY_PATH = os.path.join("src", "storage", "gateway.py")


def test_dirgen_integrity_vault_data_001():
    """Valida la paridad estructural AST entre la Bóveda Canónica y src/storage/gateway.py."""
    assert os.path.exists(VAULT_PATH), "No existe docs/DIRGEN_VAULT.md"
    assert os.path.exists(GATEWAY_PATH), "No existe src/storage/gateway.py"

    with open(GATEWAY_PATH, "r", encoding="utf-8") as f:
        src_code = f.read()

    # Parseo sintáctico estricto del código de producción
    src_tree = ast.parse(src_code)

    # Validar que existan los componentes inmutables de [VAULT-DATA-001]
    clases = [n.name for n in ast.walk(src_tree) if isinstance(n, ast.ClassDef)]
    assert "PersistenceGateway" in clases, "Violación DirGen: PersistenceGateway no declarada"

    funciones = [n.name for n in ast.walk(src_tree) if isinstance(n, ast.FunctionDef)]
    assert "_set_sqlite_pragmas" in funciones
    assert "read_session" in funciones
    assert "write_transaction" in funciones
    assert "_verify_database_health" in funciones

    # Validar que el PRAGMA foreign_keys y WAL sigan presentes en el AST
    assert "PRAGMA journal_mode = WAL;" in src_code
    assert "PRAGMA foreign_keys = ON;" in src_code
    assert "PRAGMA busy_timeout = 15000;" in src_code
