# -*- coding: utf-8 -*-
"""
[LN-QBE-095] Guardas Léxicas de Identidad de Género y Categoría (Femenil, Filiales, Sub-20).
[ARCH-1.4.25] Submódulo sellado del paquete `src/normalization/` (Capa 2 — Identity Brain).
Régimen: [DIRGEN-STRICT] — Proceso legislado en `docs/LOGIC.md` (nodo [LN-QBE-095]).

Erradica colisiones de identidad entre clubes homónimos de distintas ramas o divisiones
mediante etiquetado canónico y derivación estricta de slugs (jamás se trunca el sufijo
de género: `club-america` ≠ `club-america-femenil`).
"""

import re
from typing import Dict, Pattern, Tuple

from src.ingestion.normalizer import canonicalize_team_name
from src.ingestion.schemas import CategorizedEntityDTO
from src.storage.crest_resolver import obtener_slug_club

CATEGORIA_FEMENIL = "FEMENIL"
CATEGORIA_FILIAL = "FILIAL"
CATEGORIA_SUB20 = "SUB20"
CATEGORIA_VARONIL_MAYOR = "VARONIL_MAYOR"

# Sufijo inmutable del slug canónico (LOGIC [LN-QBE-095].P.2). Conservado siempre.
_SUFIJO_SLUG: Dict[str, str] = {
    CATEGORIA_SUB20: "sub20",
    CATEGORIA_FEMENIL: "femenil",
    CATEGORIA_FILIAL: "b",
    CATEGORIA_VARONIL_MAYOR: "",
}

# Etiqueta de despliegue del nombre canónico (vocabulario de la bóveda de aliases oficiales).
_ETIQUETA_NOMBRE: Dict[str, str] = {
    CATEGORIA_SUB20: "Sub-20",
    CATEGORIA_FEMENIL: "Femenil",
    CATEGORIA_FILIAL: "B",
    CATEGORIA_VARONIL_MAYOR: "",
}

# Detección de patrones regex (case-insensitive), en precedencia estricta:
# formativas > género > filial (evita lecturas cruzadas en cadenas compuestas).
_PATRONES: Tuple[Tuple[str, Pattern], ...] = (
    (CATEGORIA_SUB20, re.compile(r"\b(sub-?20|sub-?23|u-?20|u-?23)\b", re.IGNORECASE)),
    (CATEGORIA_FEMENIL, re.compile(r"\b(femenil|fem|women|w)\b", re.IGNORECASE)),
    (CATEGORIA_FILIAL, re.compile(r"\b(b|ii|filial|promesas)\b", re.IGNORECASE)),
)


def detectar_categoria(raw_team_name: str) -> str:
    """[LN-QBE-095].P.1 — Aplica los patrones legislados y devuelve la categoría canónica."""
    texto = str(raw_team_name or "")
    for categoria, patron in _PATRONES:
        if patron.search(texto):
            return categoria
    return CATEGORIA_VARONIL_MAYOR


def _nombre_base(raw_team_name: str, categoria: str) -> str:
    """Despoja EXCLUSIVAMENTE el marcador de categoría, preservando el nombre del club."""
    texto = str(raw_team_name or "")
    for cat, patron in _PATRONES:
        if cat != categoria:
            continue
        coincidencia = patron.search(texto)
        if coincidencia:
            texto = f"{texto[:coincidencia.start()]} {texto[coincidencia.end():]}"
    texto = re.sub(r"^[\s\-_]+", "", texto)
    texto = re.sub(r"[\s\-_]+$", "", texto)
    return re.sub(r"\s{2,}", " ", texto).strip()


def categorizar_entidad_deportiva(raw_team_name: str) -> CategorizedEntityDTO:
    """[LN-QBE-095] Clasifica y sella la identidad canónica de un club (O del nodo).

    Composición sellada: normalizador canónico `[LN-QBE-012]` para el nombre base y autoridad
    de slug de la bóveda (`obtener_slug_club`) para el identificador físico del escudo.
    """
    categoria = detectar_categoria(raw_team_name)
    base = _nombre_base(raw_team_name, categoria)
    nombre_canonico = canonicalize_team_name(base) or base or str(raw_team_name or "").strip()

    sufijo = _SUFIJO_SLUG[categoria]
    etiqueta = _ETIQUETA_NOMBRE[categoria]

    slug = obtener_slug_club(nombre_canonico)
    if sufijo and not slug.endswith(f"-{sufijo}"):
        slug = f"{slug}-{sufijo}" if slug else sufijo
    if etiqueta and not nombre_canonico.endswith(etiqueta):
        nombre_canonico = f"{nombre_canonico} {etiqueta}".strip()

    return CategorizedEntityDTO(
        canonical_name=nombre_canonico,
        canonical_slug=slug,
        category=categoria,
    )
