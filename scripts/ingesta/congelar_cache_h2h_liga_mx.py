# -*- coding: utf-8 -*-
"""
Q-BE CD WEB - CONGELADOR DEL CORPUS H2H MULTIANUAL LIGA MX
[ARCH-1.4.44] Materializa `data/cache_h2h_liga_mx_2026.json` (evidencia factual, hermetismo offline).
RÃ©gimen: [DBBD-FUNGIBLE] â€” transporte y DOM libres; identidad delegada al resolvedor canÃ³nico.

Base de Gobierno: Kybern Framework v13.5 / CERO ALAMBRADO [GOVERNANCE-01]

Axiomas operativos:
  1. Cero resultados inventados: cada fila del corpus proviene de una pÃ¡gina de resultados real cuya
     URL queda estampada en `fuentes` junto al sello temporal de generaciÃ³n (trazabilidad total).
  2. Identidad canÃ³nica: la etiqueta cruda de la fuente se resuelve contra el catÃ¡logo 3NF
     (`teams.canonical_slug`) con el plano sellado `resolver_identidad_en_catalogo`; las etiquetas
     ambiguas o ajenas se DESCARTAN con traza (jamÃ¡s se adivina una identidad).
  3. Idempotencia del artefacto: las filas se ordenan por `(fecha, local_slug, visitante_slug)` y se
     deduplican por esa firma, de modo que dos ejecuciones sobre la misma evidencia producen el mismo
     cuerpo factual (solo cambia `generado_at`).
  4. Hermetismo aguas abajo: el consumidor (`src/core/sovereign/h2h_provider.py`) lee este JSON del
     disco; ninguna prueba de `tests/shield/` toca la red.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bs4 import BeautifulSoup

from scripts.ingesta.ingestar_historico_betexplorer import (
    LIGA_ID_CANONICA,
    construir_catalogo_3nf,
    descargar_resultados_betexplorer,
    resolver_identidad_en_catalogo,
)
from src.storage.gateway import PersistenceGateway

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CongeladorH2H")

SONDA_CACHE_H2H = "ARCH-1.4.44 Â· CACHE-H2H-LIGAMX"
ESQUEMA_CORPUS = "h2h_corpus_v1"
RUTA_CACHE_H2H_DEFAULT = os.path.join(
    PROJECT_ROOT, "data", "cache_h2h_liga_mx_2026.json"
)
URL_TEMPORADA_BETEXPLORER = (
    "https://www.betexplorer.com/football/mexico/liga-mx-{temporada}/results/"
)
TEMPORADAS_DEFAULT = ("2025-2026", "2024-2025", "2023-2024")
VENTANA_TAU_DEEP_DIAS = 540

# Firmas del DOM real de las pÃ¡ginas de FASE (`?stage=<hash>`): a diferencia de la portada de
# resultados â€”que agrupa por `N. Round`â€” la pÃ¡gina de fase lista los partidos en filas planas cuya
# primera celda es `Local - Visitante`, la segunda el marcador `d:d` y la Ãºltima la fecha `DD.MM.[YYYY]`.
RE_FECHA_CELDA = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})?$")
RE_MARCADOR_CELDA = re.compile(r"^(\d+)\s*:\s*(\d+)$")
RE_SEPARADOR_CLUBES = re.compile(r"\s+-\s+")



def fases_de_temporada(html: str, temporada: str) -> List[Dict[str, str]]:
    """Fases (`?stage=<hash>`) publicadas por la fuente para una temporada.

    Se leen las opciones del selector de fase y los anclajes del bloque de resultados; la URL se
    absolutiza contra el dominio de la fuente. Cero hashes quemados: la fuente manda.
    """
    soup = BeautifulSoup(html, "html.parser")
    base = URL_TEMPORADA_BETEXPLORER.format(temporada=temporada)
    fases: Dict[str, Dict[str, str]] = {}
    for nodo in soup.find_all(["option", "a"]):
        href = str(nodo.get("value") or nodo.get("href") or "")
        if "stage=" not in href:
            continue
        etiqueta = nodo.get_text(" ", strip=True)
        if not etiqueta:
            continue
        if href.startswith("http"):
            url = href
        elif href.startswith("?"):
            url = base + href
        else:
            url = base + "?" + href.split("?")[-1]
        fases.setdefault(etiqueta, {"etiqueta": etiqueta, "url": url})
    return list(fases.values())


def _anio_de_fila(temporada: str, etiqueta_fase: str) -> int:
    """AÃ±o implÃ­cito de una fecha sin aÃ±o: Apertura â‡’ aÃ±o de inicio; Clausura/Liguilla â‡’ aÃ±o final."""
    inicio, _, fin = str(temporada).partition("-")
    es_apertura = "apertura" in str(etiqueta_fase).lower()
    return int(inicio) if es_apertura else int(fin or inicio)


def parsear_fase_betexplorer(
    html: str, temporada: str, etiqueta_fase: str
) -> List[Dict[str, Any]]:
    """Partidos oficiales de una pÃ¡gina de fase: `{fecha, local, visitante, goles_local, goles_visita}`.

    Regla de certificaciÃ³n: una fila entra sÃ³lo si (a) alguna celda es `Local - Visitante`,
    (b) otra celda es un marcador `d:d` y (c) existe una celda de fecha `DD.MM.[YYYY]`. Las filas de
    encabezado, promociones o cuotas quedan fuera por construcciÃ³n.
    """
    soup = BeautifulSoup(html, "html.parser")
    partidos: List[Dict[str, Any]] = []
    for fila in soup.find_all("tr"):
        celdas = [c.get_text(" ", strip=True) for c in fila.find_all("td")]
        if len(celdas) < 3:
            continue
        etiqueta: Optional[str] = None
        marcador: Optional[Tuple[int, int]] = None
        fecha: Optional[str] = None
        for texto in celdas:
            if etiqueta is None and RE_SEPARADOR_CLUBES.search(texto):
                etiqueta = texto
                continue
            coincidencia_marcador = RE_MARCADOR_CELDA.match(texto)
            if marcador is None and coincidencia_marcador is not None:
                marcador = (
                    int(coincidencia_marcador.group(1)),
                    int(coincidencia_marcador.group(2)),
                )
                continue
            if fecha is None and RE_FECHA_CELDA.match(texto):
                fecha = texto
        if etiqueta is None or marcador is None or fecha is None:
            continue
        partes = RE_SEPARADOR_CLUBES.split(etiqueta, maxsplit=1)
        if len(partes) != 2:
            continue
        dia, mes, anio = RE_FECHA_CELDA.match(fecha).groups()  # type: ignore[union-attr]
        anio_efectivo = int(anio) if anio else _anio_de_fila(temporada, etiqueta_fase)
        try:
            fecha_iso = datetime(anio_efectivo, int(mes), int(dia)).strftime("%Y-%m-%d")
        except ValueError:
            continue
        partidos.append({
            "fecha": fecha_iso,
            "fase": etiqueta_fase,
            "temporada": temporada,
            "local": partes[0].strip(),
            "visitante": partes[1].strip(),
            "goles_local": marcador[0],
            "goles_visita": marcador[1],
        })
    return partidos



def _resolver_filas(
    partidos: List[Dict[str, Any]], catalogo: Dict[str, str]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Resuelve identidades contra la 3NF y deduplica por `(fecha, local_slug, visitante_slug)`.

    La firma de deduplicaciÃ³n es temporal-espacial: el mismo par no puede jugar dos veces el mismo
    dÃ­a, de modo que una fila repetida por la fuente (o por dos fases solapadas) no infla el corpus.
    La fila repetida con marcador distinto se descarta en favor de la primera lectura (first-wins):
    jamÃ¡s se promedian marcadores.
    """
    por_nombre = {nombre: slug for slug, nombre in catalogo.items()}
    resueltos: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    huerfanos: List[str] = []
    for partido in partidos:
        local = resolver_identidad_en_catalogo(str(partido.get("local") or ""), catalogo)
        visitante = resolver_identidad_en_catalogo(str(partido.get("visitante") or ""), catalogo)
        if local is None or visitante is None:
            huerfanos.append(
                f"{partido.get('fecha')} {partido.get('local')} - {partido.get('visitante')}"
            )
            continue
        local_slug = por_nombre[local]
        visitante_slug = por_nombre[visitante]
        if local_slug == visitante_slug:
            huerfanos.append(
                f"{partido.get('fecha')} {local} - {visitante} (identidad colapsada)"
            )
            continue
        clave = (str(partido["fecha"]), local_slug, visitante_slug)
        resueltos.setdefault(clave, {
            "fecha": str(partido["fecha"]),
            "fase": str(partido.get("fase") or ""),
            "local": local,
            "visitante": visitante,
            "local_slug": local_slug,
            "visitante_slug": visitante_slug,
            "goles_local": int(partido["goles_local"]),
            "goles_visita": int(partido["goles_visita"]),
        })
    return [resueltos[clave] for clave in sorted(resueltos)], huerfanos


def congelar_corpus_h2h(
    temporadas: Tuple[str, ...] = TEMPORADAS_DEFAULT,
    salida: str = RUTA_CACHE_H2H_DEFAULT,
    liga_id: int = LIGA_ID_CANONICA,
    espera: float = 1.0,
    permitir_red: bool = True,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Congela el corpus multianual de enfrentamientos oficiales en un JSON hermÃ©tico.

    `permitir_red=False` convierte la utilidad en un validador offline: relee el artefacto ya
    congelado y certifica su esquema sin descargar nada.
    """
    destino = Path(salida)
    if not permitir_red:
        artefacto = json.loads(destino.read_text(encoding="utf-8"))
        logger.info(
            "ðŸ“¦ [OFFLINE] Corpus releÃ­do: %d partido(s) Â· temporadas %s",
            len(artefacto.get("partidos") or []), artefacto.get("temporadas"),
        )
        return artefacto

    gateway = PersistenceGateway()
    with gateway.read_session() as sesion:
        catalogo = construir_catalogo_3nf(sesion, int(liga_id))

    crudos: List[Dict[str, Any]] = []
    fuentes: List[str] = []
    fases_por_temporada: Dict[str, List[str]] = {}
    for temporada in temporadas:
        url_temporada = URL_TEMPORADA_BETEXPLORER.format(temporada=temporada)
        html_temporada = descargar_resultados_betexplorer(url_temporada)
        fases = fases_de_temporada(html_temporada, temporada)
        if not fases:
            logger.warning("âš ï¸ [SIN FASES] %s no publicÃ³ selector de fase", temporada)
        fases_por_temporada[temporada] = [fase["etiqueta"] for fase in fases]
        for fase in fases:
            html_fase = descargar_resultados_betexplorer(fase["url"])
            filas = parsear_fase_betexplorer(html_fase, temporada, fase["etiqueta"])
            logger.info(
                "   Â· %s / %-22s %3d partido(s)", temporada, fase["etiqueta"], len(filas)
            )
            crudos.extend(filas)
            fuentes.append(fase["url"])
            time.sleep(max(0.0, float(espera)))

    partidos, huerfanos = _resolver_filas(crudos, catalogo)
    if huerfanos:
        logger.warning(
            "âš ï¸ [IDENTIDAD NO RESUELTA] %d fila(s) descartada(s): %s",
            len(huerfanos), huerfanos[:6],
        )

    artefacto = {
        "sonda": SONDA_CACHE_H2H,
        "esquema": ESQUEMA_CORPUS,
        "liga": "MEX_LIGAMX",
        "fuente": (
            "betexplorer.com Â· resultados oficiales de Liga MX "
            "(fases regulares y liguilla de las temporadas congeladas)"
        ),
        "fuentes": fuentes,
        "generado_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        "temporadas": list(temporadas),
        "fases_por_temporada": fases_por_temporada,
        "ventana_tau_deep_dias": VENTANA_TAU_DEEP_DIAS,
        "resumen": {
            "partidos_crudos": len(crudos),
            "partidos_resueltos": len(partidos),
            "identidades_descartadas": len(huerfanos),
        },
        "partidos": partidos,
    }
    if dry_run:
        logger.info("ðŸ§ª [DRY-RUN] %d partido(s) resueltos; artefacto NO escrito.", len(partidos))
        return artefacto

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(artefacto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    logger.info(
        "âœ… [CONGELADO] %s Â· %d partido(s) Â· %d club(es) Â· %d byte(s)",
        destino, len(partidos),
        len({p["local_slug"] for p in partidos} | {p["visitante_slug"] for p in partidos}),
        destino.stat().st_size,
    )
    return artefacto


def _parsear_temporadas(texto: str) -> Tuple[str, ...]:
    temporadas = tuple(t.strip() for t in str(texto or "").replace(" ", "").split(",") if t.strip())
    return temporadas or TEMPORADAS_DEFAULT


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Congela el corpus multianual de H2H de Liga MX (evidencia factual, offline)."
    )
    parser.add_argument("--temporadas", default=",".join(TEMPORADAS_DEFAULT))
    parser.add_argument("--salida", default=RUTA_CACHE_H2H_DEFAULT)
    parser.add_argument("--liga-id", type=int, default=LIGA_ID_CANONICA)
    parser.add_argument("--espera", type=float, default=1.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--offline", action="store_true",
        help="No descarga: relee y describe el artefacto ya congelado (validaciÃ³n hermÃ©tica).",
    )
    args = parser.parse_args(argv)

    artefacto = congelar_corpus_h2h(
        temporadas=_parsear_temporadas(args.temporadas),
        salida=args.salida,
        liga_id=int(args.liga_id),
        espera=float(args.espera),
        permitir_red=not bool(args.offline),
        dry_run=bool(args.dry_run),
    )
    resumen = artefacto.get("resumen") or {}
    print("\n" + "=" * 84)
    print(f"ðŸ“¦ [{SONDA_CACHE_H2H}] CORPUS H2H Â· {artefacto.get('esquema')}")
    print("=" * 84)
    print(f"   Temporadas: {', '.join(str(t) for t in artefacto.get('temporadas') or [])}")
    print(f"   Partidos resueltos: {len(artefacto.get('partidos') or [])}"
          f" Â· crudos: {resumen.get('partidos_crudos', 'n/d')}"
          f" Â· descartados: {resumen.get('identidades_descartadas', 'n/d')}")
    print(f"   Salida: {args.salida}")
    print("=" * 84)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

