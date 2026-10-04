# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DE LA CAPA 1 (DATA NEXUS)
Audita [ARCH-1.4.24] (Contrato Hexagonal de Proveedores y DTOs) y [LN-QBE-093]
(Axioma de Pureza de Sensores: cero acoplamiento a persistencia en providers/).
Base de Gobierno: Kybern Framework v8.0 / v12.0
"""
import ast
import os
import pytest
from pathlib import Path
from pydantic import BaseModel


def test_arch_1_4_24_schemas_dtos_must_exist_and_be_pydantic():
    """[ARCH-1.4.24] Los DTOs de Capa 1 deben existir en src/ingestion/schemas.py y ser Pydantic V2."""
    from src.ingestion.schemas import (
        ScheduledMatchDTO,
        SeasonOverviewDTO,
        ProgolContestDTO,
        Odds1X2DTO,
    )

    for dto in (ScheduledMatchDTO, SeasonOverviewDTO, ProgolContestDTO, Odds1X2DTO):
        assert isinstance(dto, type) and issubclass(dto, BaseModel), \
            f"❌ [ARCH-1.4.24] {getattr(dto, '__name__', dto)} no es un contrato Pydantic V2."

    assert set(Odds1X2DTO.model_fields) >= {"L", "E", "V", "pago_anticipado", "bookmaker"}, \
        "❌ [ARCH-1.4.24] Odds1X2DTO no materializa el contrato 1X2 completo."


def test_ln_qbe_093_zero_db_coupling_in_providers_ast():
    """
    [LN-QBE-093] Escanea el Árbol de Sintaxis Abstracta (AST) de los sensores de ingesta pura.
    Prohibido el acoplamiento estático a la capa de persistencia (`src.storage`, `sqlalchemy`)
    y el I/O de escritura a disco: el acceso a datos certificados se canaliza por Inversión de Dependencias.
    """
    providers_dir = Path("src/ingestion/providers")

    if not providers_dir.exists() or not any(providers_dir.iterdir()):
        pytest.fail("❌ [LN-QBE-093] El directorio src/ingestion/providers/ no existe o está vacío.")

    for py_file in providers_dir.rglob("*.py"):
        with open(py_file, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(py_file))
            except SyntaxError:
                pytest.fail(f"Error de sintaxis parseando el archivo {py_file.name}")

        for node in ast.walk(tree):
            # 1. Import directo evasivo: `import src.storage.database as d` / `import sqlalchemy`
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "sqlalchemy" not in alias.name.lower(), \
                        f"❌ [{py_file.name}:{node.lineno}] Import prohibido de sqlalchemy."
                    assert "src.storage" not in alias.name.lower(), \
                        f"❌ [{py_file.name}:{node.lineno}] Import prohibido de src.storage."

            # 2. `from src.storage.X import Y` / `from src import storage` / `from sqlalchemy import Z`
            if isinstance(node, ast.ImportFrom):
                module_name = (node.module or "").lower()
                assert "sqlalchemy" not in module_name, \
                    f"❌ [{py_file.name}:{node.lineno}] 'from sqlalchemy import ...' prohibido."
                assert not module_name.startswith("src.storage"), \
                    f"❌ [{py_file.name}:{node.lineno}] 'from src.storage... import ...' prohibido."
                if module_name == "src":
                    for alias in node.names:
                        assert alias.name.lower() != "storage", \
                            f"❌ [{py_file.name}:{node.lineno}] 'from src import storage' prohibido."

            # 3. I/O de escritura a disco en sensores puros: open(modo w/a/+) / write_text / write_bytes
            if isinstance(node, ast.Call):
                func_name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                if func_name == "open":
                    modos = []
                    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                        modos.append(str(node.args[1].value))
                    for kw in node.keywords:
                        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                            modos.append(str(kw.value.value))
                    for modo in modos:
                        assert not any(flag in modo for flag in ("w", "a", "+")), \
                            f"❌ [{py_file.name}:{node.lineno}] I/O de escritura prohibido en sensores puros (modo '{modo}')."
                assert func_name not in ("write_text", "write_bytes"), \
                    f"❌ [{py_file.name}:{node.lineno}] I/O de escritura prohibido en sensores puros."


def test_providers_inherit_from_abstract_base_class():
    """[LN-QBE-093] Todo sensor de ingesta pura hereda del contrato abstracto canónico."""
    import inspect
    from src.ingestion.providers.base_provider import BaseSportsDataProvider
    from src.ingestion.providers.fotmob_provider import FotMobProvider

    assert inspect.isabstract(BaseSportsDataProvider), \
        "❌ [ARCH-1.4.24] BaseSportsDataProvider debe ser un contrato abstracto (abc.ABC)."
    assert issubclass(FotMobProvider, BaseSportsDataProvider), \
        "❌ [ARCH-1.4.24] FotMobProvider no hereda de BaseSportsDataProvider."
