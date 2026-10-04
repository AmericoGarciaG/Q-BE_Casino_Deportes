# -*- coding: utf-8 -*-
"""
[ARCH-1.5.12] Bóveda Soberana de Activos Locales — resolución de URIs y auditoría física.
[ARCH-1.4.25] Submódulo sellado del paquete `src/normalization/` (Capa 2 — Identity Brain).
Régimen: [DIRGEN-STRICT].

Axiomas legislados:
* Entrega EXCLUSIVAMENTE URIs locales (`/static/img/crests/…`, `/static/img/leagues/…`).
* PROHIBIDO el hotlinking: cualquier URI remota es rechazada con excepción
  (`[ARCH-1.5.10]` / `[ARCH-1.5.10-B]`).
* La auditoría física certifica existencia, tamaño ≥ 2,500 bytes y cabecera real
  (PNG/SVG/JPEG), erradicando archivos fantasma (`[LN-QBE-019]`, anti-datos-sintéticos).
"""

import os
import re
import unicodedata
from typing import Any, Dict

from src.storage.crest_resolver import BASE_DIR

TIPO_EQUIPO = "team"
TIPO_LIGA = "league"

RUTA_WEB_POR_TIPO: Dict[str, str] = {
    TIPO_EQUIPO: "/static/img/crests",
    TIPO_LIGA: "/static/img/leagues",
}

DIRECTORIO_FISICO_POR_TIPO: Dict[str, str] = {
    TIPO_EQUIPO: os.path.join(BASE_DIR, "src", "web", "static", "img", "crests"),
    TIPO_LIGA: os.path.join(BASE_DIR, "src", "web", "static", "img", "leagues"),
}

# Piso físico sellado por `[LN-QBE-019]` (Juez de Bóveda de Escudos).
MIN_BYTES_ACTIVO = 2500

_PATRON_URI_REMOTA = re.compile(r"^\s*(?:[a-z][a-z0-9+.\-]*:)?//", re.IGNORECASE)
_PATRON_EXTENSION = re.compile(r"\.(png|svg|jpe?g|webp)$", re.IGNORECASE)


def es_uri_remota(uri: str) -> bool:
    """Detecta esquemas absolutos (`http://`, `https://`) y protocolo-relativas (`//host`)."""
    return bool(_PATRON_URI_REMOTA.match(str(uri or "")))


def _resolver_tipo(tipo: str) -> str:
    tipo_normalizado = str(tipo or TIPO_EQUIPO).strip().lower()
    if tipo_normalizado not in RUTA_WEB_POR_TIPO:
        raise ValueError(
            f"[ARCH-1.5.12] Tipo de activo no legislado: '{tipo}'. "
            f"Válidos: {sorted(RUTA_WEB_POR_TIPO)}."
        )
    return tipo_normalizado


def _normalizar_slug(slug: str) -> str:
    """Slug determinista (minúsculas, sin acentos ni separadores de ruta). Anti-traversal."""
    texto = unicodedata.normalize("NFKD", str(slug or "")).encode("ascii", "ignore").decode("ascii")
    texto = _PATRON_EXTENSION.sub("", texto.strip().lower())
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    return texto.strip("-")


def resolver_uri_activo_local(slug: str, tipo: str = TIPO_EQUIPO) -> str:
    """[ARCH-1.5.12] Devuelve la URI LOCAL canónica del activo de un club o de una liga.

    Levanta `ValueError` ante una URI remota (prohibición de hotlinking) o un tipo no legislado.
    """
    if es_uri_remota(slug):
        raise ValueError(
            f"[ARCH-1.5.12] Prohibido hotlinking: se recibió la URI remota '{slug}'. "
            "La bóveda entrega exclusivamente rutas estáticas locales."
        )
    tipo_normalizado = _resolver_tipo(tipo)
    slug_canonico = _normalizar_slug(slug)
    if not slug_canonico:
        raise ValueError(f"[ARCH-1.5.12] Slug vacío o no normalizable: '{slug}'.")
    return f"{RUTA_WEB_POR_TIPO[tipo_normalizado]}/{slug_canonico}.png"


def auditar_activo_fisico(slug: str, tipo: str = TIPO_EQUIPO) -> Dict[str, Any]:
    """Auditoría física de solo lectura del activo en disco (cero datos sintéticos).

    Retorna un informe fáctico: `existe`, `bytes`, `formato` y `valido` (≥ 2,500 bytes + cabecera
    real). Nunca escribe, descarga ni fabrica archivos: la descarga/curación es competencia del
    pipeline HITL de curación.
    """
    tipo_normalizado = _resolver_tipo(tipo)
    slug_canonico = _normalizar_slug(slug)
    ruta = os.path.join(DIRECTORIO_FISICO_POR_TIPO[tipo_normalizado], f"{slug_canonico}.png")

    informe: Dict[str, Any] = {
        "slug": slug_canonico,
        "tipo": tipo_normalizado,
        "ruta": ruta,
        "existe": False,
        "bytes": 0,
        "formato": "DESCONOCIDO",
        "valido": False,
    }

    if not slug_canonico or not os.path.isfile(ruta):
        return informe

    informe["existe"] = True
    informe["bytes"] = os.path.getsize(ruta)

    with open(ruta, "rb") as manejador:
        cabecera = manejador.read(512)

    if cabecera.startswith(b"\x89PNG"):
        formato = "PNG"
    elif cabecera.startswith(b"\xff\xd8\xff"):
        formato = "JPEG"
    elif b"<svg" in cabecera[:256] or (b"<?xml" in cabecera[:64] and b"svg" in cabecera[:256]):
        formato = "SVG"
    else:
        formato = "DESCONOCIDO"

    informe["formato"] = formato
    informe["valido"] = informe["bytes"] >= MIN_BYTES_ACTIVO and formato != "DESCONOCIDO"
    return informe
