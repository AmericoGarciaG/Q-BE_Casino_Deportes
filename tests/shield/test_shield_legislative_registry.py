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
    """Audita que toda Ficha de Varianza citada exista físicamente en disco.

    Barrido ampliado (Decreto Sprint 3, enmienda autorizada): `docs/LOGIC.md` + `docs/ARCH.md`
    + `tests/**/*.py`, de modo que las citas dentro de los propios Jueces queden blindadas contra
    referencias fantasma.
    """
    archivos_corpus = [LOGIC_PATH, ARCH_PATH]
    archivos_corpus.extend(sorted(Path("tests").rglob("*.py")))

    corpus = ""
    for archivo in archivos_corpus:
        if archivo.exists():
            corpus += archivo.read_text(encoding="utf-8")

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


def test_registry_covers_total_node_universe():
    """Consolidación al 100%: todo nodo sellado en los Libros debe estar anclado en el Registro Maestro.

    Barrido inverso (Decreto Sprint 3, Task 2): se extraen TODOS los encabezados de nodo publicados
    en `docs/LOGIC.md` y `docs/ARCH.md` y se exige que cada símbolo figure en `docs/ID_REGISTRY.md`.
    Un nodo legislado sin fila en el registro es una **ceguera de colisión** (el riesgo histórico que
    el Paso 0 existe para eliminar): el asignador `max + 1` volvería a operar sobre una vista parcial.
    Anclaje simbólico obligatorio (R-2): el libro dueño + el símbolo, jamás `archivo:línea` que rota.
    """
    registry_path = DOCS_DIR / "ID_REGISTRY.md"
    assert registry_path.exists(), "Falta docs/ID_REGISTRY.md (Registro Maestro del Paso 0)"
    registro = registry_path.read_text(encoding="utf-8")

    nodos_logicos = re.findall(
        r'###\s+ID:\s+\[(LN-QBE-[A-Za-z0-9_\-]+)\]', LOGIC_PATH.read_text(encoding="utf-8")
    )
    nodos_arquitectonicos = re.findall(
        r'###\s+\[(ARCH-[0-9A-Za-z\.\-_]+)\]', ARCH_PATH.read_text(encoding="utf-8")
    )

    assert nodos_logicos, "docs/LOGIC.md no publica ningún nodo [LN-QBE-*]"
    assert nodos_arquitectonicos, "docs/ARCH.md no publica ningún nodo [ARCH-*]"

    universo = list(dict.fromkeys(nodos_logicos + nodos_arquitectonicos))
    huerfanos = [nodo for nodo in universo if nodo not in registro]

    assert not huerfanos, (
        "🚨 REGISTRO INCOMPLETO (ceguera de colisión): nodos sellados sin anclaje en "
        f"docs/ID_REGISTRY.md: {huerfanos}"
    )


class TestRegistrySincronizacionMecanica:
    """[P2-7] El Registro Maestro es un artefacto de compilación, no un documento editable."""

    def test_registry_cubre_total_node_universe(self):
        """Todo encabezado de nodo en LOGIC.md/ARCH.md debe tener fila en ID_REGISTRY.md.

        Se ancla por encabezado (`###`/`####`), no por mención inline: los identificadores
        declarados "no asignados", los placeholders (`LN-QBE-XXX`) y las referencias cruzadas
        no son nodos legislados y no deben inventarse en el registro.
        """
        registro_path = DOCS_DIR / "ID_REGISTRY.md"
        assert registro_path.exists(), "Falta docs/ID_REGISTRY.md (Registro Maestro del Paso 0)"
        registro = registro_path.read_text(encoding="utf-8")
        ids_registrados = set()
        for linea in registro.splitlines():
            coincidencia_fila = re.match(r"^\|\s*`?\[([^\]]+)\]`?\s*\|", linea.strip())
            if coincidencia_fila:
                ids_registrados.add(coincidencia_fila.group(1))

        patron_encabezado = re.compile(
            r"^#{3,4}\s+(?:ID:\s+)?.*?\[(LN-QBE-[A-Za-z0-9_\-]+|ARCH-[0-9A-Za-z\.\-_]+)\]"
        )
        nodos = set()
        for ruta in (LOGIC_PATH, ARCH_PATH):
            for linea in ruta.read_text(encoding="utf-8").splitlines():
                coincidencia = patron_encabezado.match(linea)
                if coincidencia:
                    nodos.add(coincidencia.group(1))

        assert nodos, "Los Libros no publican ningún encabezado de nodo reconocible."
        faltantes = sorted(nodos - ids_registrados)
        assert len(faltantes) == 0, (
            "🚨 REGISTRO DESACTUALIZADO: nodos legislados sin fila en docs/ID_REGISTRY.md: "
            f"{faltantes}. Ejecute `python scripts/auditoria/reconciliar_registro_legislativo.py --write`."
        )

