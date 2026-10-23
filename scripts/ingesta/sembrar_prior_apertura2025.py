# -*- coding: utf-8 -*-
"""
Q-BE CD WEB — SEMBRADOR DEL PRIOR CONGELADO DE APERTURA 2025
[ARCH-1.4.69] / [LN-QBE-128] · Régimen: [DBBD-FUNGIBLE]

Misión
------
Publicar —UNA sola vez, congelado e inmutable— el agregado físico REAL del torneo anterior
(Apertura 2025, fase regular) para que el corte N−1 de las primeras jornadas deje de ser una
ignorancia estructural. El artefacto es DATO, no código: no contiene una sola fórmula del motor
soberano y jamás sustituye una magnitud medida.

Fuente única de verdad
----------------------
`data/cache_h2h_liga_mx_2026.json` (corpus `h2h_corpus_v1`, betexplorer.com · resultados
oficiales de Liga MX). Se extraen los partidos con `fase == "Apertura"` y fecha dentro de la
ventana `2025-07-01 .. 2025-12-31` (fase REGULAR de la temporada 2025-2026). Liguilla, Play-In y
Play-Offs quedan FUERA: no son muestra comparable con la fase regular.

Procedencias DECLARADAS (cero invención)
----------------------------------------
* `pj`, `gf`, `gc`, `pts`  ⇒ FACTUALES (conteo directo del corpus).
* `xg_per_match`           ⇒ `calibrado_gf` [ARCH-1.4.39]: `max(0.5, GF_por_partido · 1.05)`.
                              Es una ESTIMACIÓN declarada, jamás una métrica Opta.
* `xga_per_match`          ⇒ GC factual: el corpus no porta xG defensivo de 2025
                              ([VAR-2026-J7-HOMOLOGACION §6.1·E1] prohíbe publicar xGA al motor).
* `possession_pct`         ⇒ baseline neutro 50.0 declarado `NO MEDIDO`. El corpus NO publica
                              posesión de 2025: se publica el valor de ignorancia (cero
                              información diferencial) y `possession_es_medida = False`.
                              NUNCA se propaga al motor ni al catálogo 44V.

El resolvedor `_resolver_insumos_con_prior` de `scripts/ingesta/homologar_temporada_optah2h.py`
es el ÚNICO consumidor legislado de este artefacto.

Uso
---
    python -m scripts.ingesta.sembrar_prior_apertura2025
    python -m scripts.ingesta.sembrar_prior_apertura2025 --json
    python -m scripts.ingesta.sembrar_prior_apertura2025 --regen       # única llave de regeneración
    python -m scripts.ingesta.sembrar_prior_apertura2025 --salida data/otro_prior.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# [GOVERNANCE-01] Fuente ÚNICA de la relación calibrada: jamás se transcribe el factor aquí.
from scripts.ingesta.homologar_temporada_optah2h import (  # noqa: E402
    FACTOR_XG_CALIBRADO,
    XG_MINIMO_CALIBRADO,
)

# ─── Constantes legisladas ───────────────────────────────────────────────────────────────────
SONDA_PRIOR = "ARCH-1.4.69 · PRIOR-CONGELADO-APERTURA-2025"
ESQUEMA_PRIOR = "prior_apertura_v1"
LIGA_PRIOR = "MEX_LIGAMX"
TEMPORADA_PRIOR = "2025-2026"
FASE_PRIOR = "Apertura"
ALCANCE_PRIOR = "fase regular (liguilla, Play-In y Play-Offs excluidos)"
VENTANA_INICIO_DEFAULT = "2025-07-01"
VENTANA_FIN_DEFAULT = "2025-12-31"
RUTA_CORPUS_H2H_DEFAULT = os.path.join("data", "cache_h2h_liga_mx_2026.json")
RUTA_PRIOR_DEFAULT = os.path.join("data", "cache_prior_apertura2025_liga_mx.json")

# [LN-QBE-128] Posesión: el corpus NO mide posesión de 2025. Se publica el valor de ignorancia.
POSESION_BASELINE = 50.0
PROCEDENCIA_POSESION = (
    "SIN_MEDICION · baseline neutro 50.0 declarado NO MEDIDO "
    "(Apertura 2025 no porta posesión; jamás se propaga al motor ni al catálogo 44V)"
)
PROCEDENCIA_XG = (
    "calibrado_gf · [ARCH-1.4.39] xG = max(0.5, GF_por_partido · 1.05) "
    "— ESTIMACIÓN declarada, no métrica Opta (el corpus 2025 no porta xG)"
)
PROCEDENCIA_XGA = (
    "gc_factual · [VAR-2026-J7-HOMOLOGACION §6.1·E1] xGA no medido en 2025 ⇒ GC factual "
    "(telemetría de auditoría: NO viaja al motor)"
)

# Caché de proceso: un artefacto congelado se lee UNA vez por ruta.
_PRIOR_EN_MEMORIA: Dict[str, Dict[str, Any]] = {}


def _sha256_archivo(ruta: str) -> Optional[str]:
    """SHA-256 del corpus origen (`None` si no existe): sella la procedencia del dato."""
    if not os.path.exists(ruta):
        return None
    digest = hashlib.sha256()
    with open(ruta, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(65536), b""):
            digest.update(bloque)
    return digest.hexdigest()


def _sha256_payload(payload: Any) -> str:
    """SHA-256 canónico (claves ordenadas, UTF-8) del bloque `equipos`."""
    canonico = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def _partidos_fase_regular(
    partidos: Sequence[Dict[str, Any]], inicio: str = VENTANA_INICIO_DEFAULT, fin: str = VENTANA_FIN_DEFAULT
) -> List[Dict[str, Any]]:
    """Filtra el corpus a la fase REGULAR del torneo previo (Apertura 2025). Función pura."""
    seleccion = []
    for partido in partidos or []:
        if str(partido.get("fase") or "") != FASE_PRIOR:
            continue
        fecha = str(partido.get("fecha") or "")
        if not (inicio <= fecha <= fin):
            continue
        if partido.get("goles_local") is None or partido.get("goles_visita") is None:
            continue
        if not (partido.get("local_slug") and partido.get("visitante_slug")):
            continue
        seleccion.append(partido)
    seleccion.sort(key=lambda p: (str(p.get("fecha")), str(p.get("local_slug")), str(p.get("visitante_slug"))))
    return seleccion



def _agregar_equipos(partidos: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Agrega el bloque `equipos` por slug: conteos FACTUALES + magnitudes derivadas declaradas."""
    acumulado: Dict[str, Dict[str, Any]] = {}
    for partido in partidos:
        local = str(partido["local_slug"])
        visita = str(partido["visitante_slug"])
        goles_local = int(partido["goles_local"])
        goles_visita = int(partido["goles_visita"])
        for slug, nombre, gf, gc in (
            (local, str(partido.get("local") or local), goles_local, goles_visita),
            (visita, str(partido.get("visitante") or visita), goles_visita, goles_local),
        ):
            nodo = acumulado.setdefault(slug, {"nombre": nombre, "pj": 0, "gf": 0, "gc": 0, "pts": 0})
            nodo["nombre"] = nombre
            nodo["pj"] += 1
            nodo["gf"] += gf
            nodo["gc"] += gc
        if goles_local > goles_visita:
            acumulado[local]["pts"] += 3
        elif goles_local < goles_visita:
            acumulado[visita]["pts"] += 3
        else:
            acumulado[local]["pts"] += 1
            acumulado[visita]["pts"] += 1

    equipos: Dict[str, Dict[str, Any]] = {}
    for slug in sorted(acumulado):
        nodo = acumulado[slug]
        pj = int(nodo["pj"])
        if pj <= 0:
            continue
        gf_por_partido = nodo["gf"] / pj
        gc_por_partido = nodo["gc"] / pj
        equipos[slug] = {
            "nombre": nodo["nombre"],
            "pj": pj,
            "gf": int(nodo["gf"]),
            "gc": int(nodo["gc"]),
            "dg": int(nodo["gf"]) - int(nodo["gc"]),
            "pts": int(nodo["pts"]),
            "gf_per_match": round(gf_por_partido, 4),
            "gc_per_match": round(gc_por_partido, 4),
            "puntos_por_partido": round(nodo["pts"] / pj, 4),
            # [ARCH-1.4.39] Relación calibrada declarada (estimación, no métrica Opta).
            "xg_per_match": round(max(XG_MINIMO_CALIBRADO, gf_por_partido * FACTOR_XG_CALIBRADO), 4),
            # [§6.1·E1] El corpus 2025 no porta xGA: GC factual, sólo telemetría de auditoría.
            "xga_per_match": round(max(0.0, gc_por_partido), 4),
            # [LN-QBE-128] Posesión no medida: baseline neutro declarado.
            "possession_pct": round(float(POSESION_BASELINE), 4),
            "possession_es_medida": False,
            "procedencia_xg": PROCEDENCIA_XG,
            "procedencia_xga": PROCEDENCIA_XGA,
            "procedencia_possession": PROCEDENCIA_POSESION,
        }
    return equipos


def construir_prior_apertura2025(
    ruta_corpus: str = RUTA_CORPUS_H2H_DEFAULT,
    inicio: str = VENTANA_INICIO_DEFAULT,
    fin: str = VENTANA_FIN_DEFAULT,
) -> Dict[str, Any]:
    """Construye el artefacto completo (sin escribir): corpus → partidos → agregado → sellos."""
    if not os.path.exists(ruta_corpus):
        raise SystemExit(f"[ALTO AL FUEGO] Corpus H2H ausente: {ruta_corpus}")
    with open(ruta_corpus, encoding="utf-8") as archivo:
        corpus = json.load(archivo)
    partidos = _partidos_fase_regular(corpus.get("partidos") or [], inicio, fin)
    if not partidos:
        raise SystemExit(
            f"[ALTO AL FUEGO] El corpus no publica partidos de {FASE_PRIOR} en la ventana {inicio}..{fin}."
        )
    equipos = _agregar_equipos(partidos)
    totales = {
        "equipos": len(equipos),
        "partidos": len(partidos),
        "pj_total": sum(item["pj"] for item in equipos.values()),
        "gf_total": sum(item["gf"] for item in equipos.values()),
        "gc_total": sum(item["gc"] for item in equipos.values()),
        "pj_por_equipo": sorted({item["pj"] for item in equipos.values()}),
    }
    return {
        "sonda": SONDA_PRIOR,
        "esquema": ESQUEMA_PRIOR,
        "liga": LIGA_PRIOR,
        "temporada": TEMPORADA_PRIOR,
        "fase": FASE_PRIOR,
        "alcance": ALCANCE_PRIOR,
        "ventana": {"desde": inicio, "hasta": fin},
        "fuente": str(corpus.get("fuente") or "corpus H2H congelado"),
        "fuente_archivo": os.path.basename(ruta_corpus),
        "fuente_sha256": _sha256_archivo(ruta_corpus),
        "congelado_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ley_mezcla": {
            "peso_observado": "w = min(1, pj_observado / pj_suficiencia)",
            "pj_suficiencia": 3,
            "identidad": "pj_observado >= 3 ⇒ w = 1 ⇒ bloque observado sin claves añadidas",
        },
        "procedencias": {
            "pj_gf_gc_pts": "factual · conteo directo del corpus betexplorer.com",
            "xg_per_match": PROCEDENCIA_XG,
            "xga_per_match": PROCEDENCIA_XGA,
            "possession_pct": PROCEDENCIA_POSESION,
        },
        "totales": totales,
        "equipos": equipos,
        "hash_sha256": _sha256_payload(equipos),
    }


def guardar_prior(prior: Dict[str, Any], ruta: str) -> str:
    """Congela el artefacto en disco (UTF-8, JSON indentado, orden de claves estable)."""
    directorio = os.path.dirname(os.path.abspath(ruta))
    os.makedirs(directorio, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(prior, archivo, ensure_ascii=False, indent=2, sort_keys=False)
        archivo.write("\n")
    return os.path.abspath(ruta)


def cargar_o_generar_prior_apertura2025(
    ruta_salida: str = RUTA_PRIOR_DEFAULT,
    ruta_corpus: str = RUTA_CORPUS_H2H_DEFAULT,
    regenerar: bool = False,
) -> Dict[str, Any]:
    """Devuelve el artefacto CONGELADO: si existe se lee tal cual (nunca se re-escribe).

    Congelado = inmutable. La regeneración es un acto EXPLÍCITO (`regenerar=True`, CLI `--regen`):
    sólo tiene sentido cuando el corpus origen cambia de hash, y queda sellada en `congelado_at`.
    """
    ruta_absoluta = os.path.abspath(ruta_salida)
    if not regenerar:
        en_memoria = _PRIOR_EN_MEMORIA.get(ruta_absoluta)
        if en_memoria is not None:
            return en_memoria
        if os.path.exists(ruta_absoluta):
            with open(ruta_absoluta, encoding="utf-8") as archivo:
                prior = json.load(archivo)
            _PRIOR_EN_MEMORIA[ruta_absoluta] = prior
            return prior
    prior = construir_prior_apertura2025(ruta_corpus=ruta_corpus)
    guardar_prior(prior, ruta_salida)
    _PRIOR_EN_MEMORIA[ruta_absoluta] = prior
    return prior


def _imprimir_reporte(prior: Dict[str, Any], ruta: str) -> int:
    """Tablero ASCII de certificación del artefacto congelado."""
    totales = prior.get("totales") or {}
    equipos = prior.get("equipos") or {}
    print("=" * 96)
    print("🧊 Q-BE — PRIOR CONGELADO DE APERTURA 2025 [ARCH-1.4.69 / LN-QBE-128]")
    print("   Régimen: [DBBD-FUNGIBLE] · Artefacto = DATO · Cero matemática propia")
    print("=" * 96)
    print(f"  ARCHIVO   : {ruta}")
    print(f"  FUENTE    : {prior.get('fuente_archivo')} · sha256={str(prior.get('fuente_sha256'))[:16]}…")
    print(f"  TEMPORADA : {prior.get('temporada')} · fase {prior.get('fase')} · {prior.get('alcance')}")
    print(f"  VENTANA   : {prior.get('ventana', {}).get('desde')} → {prior.get('ventana', {}).get('hasta')}")
    print(
        f"  COBERTURA : {totales.get('equipos')} clubes · {totales.get('partidos')} partidos · "
        f"pj={totales.get('pj_por_equipo')}"
    )
    print(f"  HASH      : {str(prior.get('hash_sha256'))[:32]}…")
    print("-" * 96)
    print(f"  {'CLUB':30s} {'PJ':>3s} {'GF':>4s} {'GC':>4s} {'PTS':>4s} {'xG/p':>7s} {'xGA/p':>7s} {'POS':>6s}")
    for slug in sorted(equipos):
        nodo = equipos[slug]
        print(
            f"  {slug[:30]:30s} {nodo['pj']:3d} {nodo['gf']:4d} {nodo['gc']:4d} {nodo['pts']:4d} "
            f"{nodo['xg_per_match']:7.4f} {nodo['xga_per_match']:7.4f} {nodo['possession_pct']:6.1f}"
        )
    print("-" * 96)
    print("  PROCEDENCIAS DECLARADAS:")
    for clave, valor in (prior.get("procedencias") or {}).items():
        print(f"    · {clave:16s} {valor}")
    print("  LEY DE MEZCLA: w = min(1, pj_obs/3) · pj_obs >= 3 ⇒ identidad (cero claves añadidas)")
    print("=" * 96)
    return 0


def ejecutar(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada: congelar (o leer) el artefacto y publicar su tablero."""
    parser = argparse.ArgumentParser(
        description="Congela el prior de Apertura 2025 (agregado físico del torneo previo).",
    )
    parser.add_argument("--salida", default=RUTA_PRIOR_DEFAULT, help="ruta del artefacto congelado")
    parser.add_argument("--corpus", default=RUTA_CORPUS_H2H_DEFAULT, help="corpus H2H origen")
    parser.add_argument("--regen", action="store_true", help="regenerar el artefacto (llave explícita)")
    parser.add_argument("--json", action="store_true", dest="como_json", help="emitir el artefacto JSON")
    args = parser.parse_args(argv)

    prior = cargar_o_generar_prior_apertura2025(
        ruta_salida=args.salida, ruta_corpus=args.corpus, regenerar=args.regen
    )
    if args.como_json:
        print(json.dumps(prior, ensure_ascii=False, indent=2))
        return 0
    return _imprimir_reporte(prior, os.path.abspath(args.salida))


def main() -> int:
    """CLI: asegura UTF-8 (consola Windows cp1252) y delega en `ejecutar`."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass
    return ejecutar()


if __name__ == "__main__":
    raise SystemExit(main())
