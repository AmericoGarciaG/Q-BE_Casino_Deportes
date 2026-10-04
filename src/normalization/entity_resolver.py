# -*- coding: utf-8 -*-
"""
[ARCH-1.4.25] Resolutor de Entidades Deportivas — jerga de quinielas → identidad oficial.
Submódulo del paquete `src/normalization/` (Capa 2 — Identity Brain).

Composición pura de primitivas selladas, cero invención [GOVERNANCE-01]:
1. `traducir_jerga_global_progol()` — `[ARCH-1.5.11]` catálogo determinista `PROGOL_GLOBAL_ALIASES`.
2. `canonicalize_team_name()`        — `[LN-QBE-012]` normalizador canónico de clubes.
3. `categorizar_entidad_deportiva()` — `[LN-QBE-095]` guardas de género y categoría.
"""

from typing import Iterable, List

from src.ingestion.progol_resolver import traducir_jerga_global_progol
from src.ingestion.schemas import CategorizedEntityDTO
from src.normalization.gender_guards import categorizar_entidad_deportiva


def resolver_entidad_oficial(raw_team_name: str) -> CategorizedEntityDTO:
    """[ARCH-1.4.25] Traduce la jerga oficial de Progol y sella la identidad categorizada."""
    jerga_oficial = traducir_jerga_global_progol(raw_team_name)
    return categorizar_entidad_deportiva(jerga_oficial or str(raw_team_name or ""))


def resolver_entidades_oficiales(raw_team_names: Iterable[str]) -> List[CategorizedEntityDTO]:
    """Resuelve una colección completa de casillas (21 casillas de un concurso de Progol)."""
    return [resolver_entidad_oficial(nombre) for nombre in raw_team_names]
