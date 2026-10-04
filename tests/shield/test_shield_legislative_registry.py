# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DE REGISTRO LEGISLATIVO (PASO 0)
Gobernanza Constitucional de docs/LOGIC.md y docs/ARCH.md.
Audita:
1. Unicidad absoluta de identificadores [LN-QBE-xxx] y [ARCH-x.x.x].
2. Ausencia de referencias colgantes a Fichas de Varianza inexistentes.
3. Correspondencia estricta entre DTOs legislados y materializados.
"""

import re
from pathlib import Path
import pytest

DOCS_DIR = Path("docs")
LOGIC_PATH = DOCS_DIR / "LOGIC.md"
ARCH_PATH = DOCS_DIR / "ARCH.md"


def test_unique_logical_nodes_registry():
    """Audita que ningún [LN-QBE-xxx] esté duplicado en LOGIC.md."""
    assert LOGIC_PATH.exists(), "Falta docs/LOGIC.md"
    content = LOGIC_PATH.read_text(encoding="utf-8")

    # Extraer encabezados de nodos: ### ID: [LN-QBE-XXX]
    pattern = r'###\s+ID:\s+\[(LN-QBE-[A-Za-z0-9_\-]+)\]'
    matches = re.findall(pattern, content)

    seen = set()
    duplicates = []
    for node_id in matches:
        if node_id in seen:
            duplicates.append(node_id)
        seen.add(node_id)

    assert not duplicates, f"🚨 REGISTRO CORRUPTO: Nodos lógicos duplicados en LOGIC.md: {duplicates}"


def test_unique_architectural_nodes_registry():
    """Audita que ningún [ARCH-x.x.x] esté duplicado en ARCH.md."""
    assert ARCH_PATH.exists(), "Falta docs/ARCH.md"
    content = ARCH_PATH.read_text(encoding="utf-8")

    # Extraer encabezados arquitectónicos: ### [ARCH-X.X.X]
    pattern = r'###\s+\[(ARCH-[0-9A-Za-z\.\-_]+)\]'
    matches = re.findall(pattern, content)

    seen = set()
    duplicates = []
    for arch_id in matches:
        if arch_id in seen:
            duplicates.append(arch_id)
        seen.add(arch_id)

    assert not duplicates, f"🚨 REGISTRO CORRUPTO: Nodos arquitectónicos duplicados en ARCH.md: {duplicates}"


def test_zero_hanging_variance_references():
    """Audita que toda Ficha de Varianza citada en docs/ exista físicamente en disco."""
    corpus = ""
    if LOGIC_PATH.exists():
        corpus += LOGIC_PATH.read_text(encoding="utf-8")
    if ARCH_PATH.exists():
        corpus += ARCH_PATH.read_text(encoding="utf-8")

    # Buscar menciones a docs/DIRGEN_VARIANCE_REQUEST_*.md
    var_citations = re.findall(r'(docs/DIRGEN_VARIANCE_REQUEST_[A-Za-z0-9\._\-]+\.md)', corpus)

    missing_files = []
    for filepath_str in set(var_citations):
        file_path = Path(filepath_str)
        if not file_path.exists():
            missing_files.append(filepath_str)

    assert not missing_files, f"🚨 REFERENCIAS COLGANTES: Fichas de Varianza citadas pero no materializadas: {missing_files}"


def test_legislated_dtos_must_be_tested_or_materialized():
    """Audita que los DTOs prometidos en LOGIC/ARCH existan en schemas.py."""
    schemas_path = Path("src/ingestion/schemas.py")
    if not schemas_path.exists():
        pytest.skip("src/ingestion/schemas.py no materializado aún.")

    schemas_code = schemas_path.read_text(encoding="utf-8")

    # DTOs que la legislación declara formalmente
    dtos_legislados = [
        "ScheduledMatchDTO",
        "SeasonOverviewDTO",
        "ProgolContestDTO",
        "Odds1X2DTO"
    ]

    for dto in dtos_legislados:
        assert f"class {dto}" in schemas_code, f"🚨 DTO HUÉRFANO: {dto} está legislado pero no existe en schemas.py"
