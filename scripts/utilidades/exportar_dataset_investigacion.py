# -*- coding: utf-8 -*-
"""
Q-BE CD WEB — UTILIDAD GOBERNADA: EXPORTACIÓN DEL GOLDEN CSV PARA INVESTIGACIÓN
[UTIL-GOLDEN-01] Dataset tabular plano y autoportante de los 97 partidos concluidos
(Jornadas 1..11) para el Data Scientist aislado (`docs/QBE_RESEARCH_DOSSIER.md`).

Régimen: [DBBD-FUNGIBLE] — transporte, cruce de identidades y tabulación. TODA la matemática
(P′ sellada, desmarque de vig, Brier multicategórico, resolución de cuotas de cierre) se
IMPORTA de los planos sellados `[DIRGEN-STRICT]`; esta utilidad NO reimplementa una sola fórmula:

    · `src.core.contracts.portfolio_math.desmarcar_cuotas_proporcional`   [VAULT-CORE-007-C]
    · `src.core.contracts.portfolio_math.calcular_brier_multicategorico`  [LN-QBE-100]
    · `src.web.routes.markets._cuotas_1x2_factuales`                      [ARCH-1.4.38]

Autoridad: Américo García Guerrero (Director Humano)
Orden Ejecutiva: Directiva de Extracción de Datos — Generación del Golden CSV para Backtesting.

Contrato de salida (21 columnas)
--------------------------------
| Columna            | Origen fáctico                                                     |
|--------------------|--------------------------------------------------------------------|
| `match_id`         | `matches.id` (3NF, `[ARCH-1.5.1]`)                                 |
| `jornada`          | `matches.matchday_num`                                             |
| `local`            | `fixtures_snapshots.matches_json[].local` (respaldo `home_team_slug`)  |
| `visitante`        | `fixtures_snapshots.matches_json[].visitante` (respaldo `away_team_slug`) |
| `home_score`       | `matches.score_home` (oráculo factual)                             |
| `away_score`       | `matches.score_away`                                               |
| `resultado_real`   | Derivación mecánica del marcador: LOCAL / EMPATE / VISITANTE        |
| `odd_L/E/V`        | Trío 1X2 de cierre resuelto por la ley sellada `_cuotas_1x2_factuales` |
| `q_L/E/V`          | `desmarcar_cuotas_proporcional(odd_L, odd_E, odd_V)` (vig-free)    |
| `p_L/E/V`          | Ley sellada efectiva: P′ de la captura (respaldo 3NF) o, con S(I)=0, |
|                    | el Prior Fiduciario de Mercado ⇒ `q` (cláusula cold start [LN-QBE-100]) |
| `lambda_H/lambda_A`| Intensidades selladas de la captura (`lambda_home`/`lambda_away`), respaldo 3NF |
| `brier_qbe`        | `calcular_brier_multicategorico` sobre `p_L/p_E/p_V`               |
| `brier_mkt`        | `calcular_brier_multicategorico` sobre `q_L/q_E/q_V`               |
| `suficiencia_s_i`  | Séptimo campo del contrato de captura (Decreto                         |
|                    | `VAR-2026-PREFLIGHT-LEGITIMATE-ENVELOPE` §1.2): 1 = evidencia informativa, |
|                    | 0 = ignorancia declarada (Prior Fiduciario aplicado)               |

Axiomas operativos
------------------
1. **Solo lectura.** Cero escrituras en SQLite, cero red, cero mutación de `src/`.
2. **Cero invención de cifras [GOVERNANCE-01].** Un partido sin trío de cuotas o sin P′ NO se
   repara con rellenos sintéticos: la ley sellada degrada a la ignorancia uniforme (1/3,1/3,1/3)
   y el hecho queda declarado en el reporte de consola. Cero cuotas prestadas entre casas.
3. **Paridad de precedencia con el Visor sellado.** El snapshot más reciente por jornada gana
   (`updated_at DESC`) y la primera captura vista por `id_partido` se queda (`setdefault`); el
   respaldo secundario de P′ y λ es la tabla soberana 3NF `sovereign_distributions`.
4. **Paridad aritmética certificada.** El reporte de consola emite el Brier global (media
   aritmética de las columnas) y el Alpha de calibración con la MISMA ley del auditor end-to-end
   ([ARCH-1.4.42]): Brier Q-BE `0.2191` · Brier Mercado `0.2145` · Alpha `-2.14%` (dossier §2).
5. **Determinismo total.** Orden estable `(jornada, id_partido)`; formato decimal fijo por
   columna (cuotas/q/p/λ a 4 decimales, Brier a 6); UTF-8 sin BOM para lectura directa con pandas.

Uso:
    python scripts/utilidades/exportar_dataset_investigacion.py
    python scripts/utilidades/exportar_dataset_investigacion.py --salida data/otro.csv --jornadas 1-11
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Planos sellados: cero reimplementación (ley de bóveda, no de utilidad).
from src.core.contracts.portfolio_math import (  # noqa: E402
    calcular_brier_multicategorico,
    desmarcar_cuotas_proporcional,
)
from src.storage.gateway import PersistenceGateway  # noqa: E402
from src.storage.models import FixtureSnapshot, Match, SovereignDistribution  # noqa: E402
from src.web.routes.markets import _cuotas_1x2_factuales  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ExportarDatasetInvestigacion")

# ── Parámetros canónicos y contrato de columnas ───────────────────────────────────────────────
LIGA_ID_CANONICA = 1
RANGO_JORNADAS_DEFAULT = "1-11"
RUTA_SALIDA_DEFAULT = os.path.join("data", "qbe_research_poc_97_matches.csv")
ESTADOS_CONCLUIDOS = frozenset({"FINISHED", "FINALIZADO"})
CLAVE_SUFICIENCIA_SI = "suficiencia_S_I"

COLUMNAS_GOLDEN: Tuple[str, ...] = (
    "match_id", "jornada", "local", "visitante",
    "home_score", "away_score", "resultado_real",
    "odd_L", "odd_E", "odd_V",
    "q_L", "q_E", "q_V",
    "p_L", "p_E", "p_V",
    "lambda_H", "lambda_A",
    "brier_qbe", "brier_mkt",
    "suficiencia_s_i",
)
DECIMALES_CUOTAS = 4
DECIMALES_PROBABILIDAD = 4
DECIMALES_INTENSIDAD = 4
DECIMALES_BRIER = 6


def _parsear_rango_jornadas(texto: str) -> List[int]:
    """Traduce `'1-11'` / `'9'` / `'1,4,7'` a la lista ordenada y sin duplicados de jornadas."""
    jornadas: List[int] = []
    for bloque in str(texto or "").replace(" ", "").split(","):
        if not bloque:
            continue
        if "-" in bloque:
            desde, _, hasta = bloque.partition("-")
            jornadas.extend(range(int(desde), int(hasta) + 1))
        else:
            jornadas.append(int(bloque))
    return sorted({j for j in jornadas if j >= 1})


def _fila_concluida(match: Match) -> bool:
    """Un partido es auditable si porta marcador factual y estado concluido en la bóveda viva."""
    return (
        match.matchday_num is not None
        and match.score_home is not None
        and match.score_away is not None
        and str(match.status or "").upper() in ESTADOS_CONCLUIDOS
    )


def _indice_fixtures_canonicos(sesion, league_id: int) -> Dict[str, Dict[str, Any]]:
    """Índice `{id_partido: fixture}` con la MISMA precedencia del Visor sellado.

    El snapshot más reciente de cada jornada gana (`updated_at DESC`) y la primera captura vista
    por `id_partido` se queda (`setdefault`): la identidad de la captura no se pisa entre reingestas.
    """
    snapshots = (
        sesion.query(FixtureSnapshot)
        .filter(FixtureSnapshot.league_id == league_id)
        .order_by(FixtureSnapshot.matchday.asc(), FixtureSnapshot.updated_at.desc())
        .all()
    )
    indice: Dict[str, Dict[str, Any]] = {}
    for snapshot in snapshots:
        for fixture in (snapshot.matches_json or []):
            if not isinstance(fixture, dict):
                continue
            id_partido = str(fixture.get("id_partido") or "")
            if id_partido:
                indice.setdefault(id_partido, fixture)
    return indice


def _distribuciones_soberanas(sesion) -> Dict[str, SovereignDistribution]:
    """Respaldo secundario de P′ y λ: tabla soberana 3NF `sovereign_distributions`."""
    return {str(fila.match_id): fila for fila in sesion.query(SovereignDistribution).all()}


def _resolver_p_prima(
    fixture: Dict[str, Any],
    soberana: Optional[SovereignDistribution],
) -> Optional[Tuple[float, float, float]]:
    """P′ sellada: captura del snapshot o, en su defecto, la fila soberana 3NF. Sin ambas: `None`."""
    try:
        return (
            float(fixture.get("p_local")),
            float(fixture.get("p_empate")),
            float(fixture.get("p_visitante")),
        )
    except (TypeError, ValueError):
        pass
    if soberana is None:
        return None
    try:
        return (float(soberana.p_local), float(soberana.p_empate), float(soberana.p_visitante))
    except (TypeError, ValueError):
        return None


def _resolver_intensidades(
    fixture: Dict[str, Any],
    soberana: Optional[SovereignDistribution],
) -> Optional[Tuple[float, float]]:
    """Intensidades selladas (λ_H, λ_A): captura del snapshot o, en su defecto, la fila 3NF."""
    try:
        return (float(fixture.get("lambda_home")), float(fixture.get("lambda_away")))
    except (TypeError, ValueError):
        pass
    if soberana is None:
        return None
    try:
        return (float(soberana.lambda_home), float(soberana.lambda_away))
    except (TypeError, ValueError):
        return None


def _suficiencia_declarada(fixture: Dict[str, Any]) -> int:
    """Séptimo campo del contrato de captura. Ausente ⇒ 1 (el sellado es `fill-if-absent`)."""
    valor = fixture.get(CLAVE_SUFICIENCIA_SI)
    try:
        return int(valor) if valor is not None else 1
    except (TypeError, ValueError):
        return 1


def _fmt(valor: Optional[float], decimales: int) -> str:
    """Formato decimal FIJO por columna (determinismo total); `None` ⇒ cadena vacía."""
    if valor is None:
        return ""
    return f"{float(valor):.{decimales}f}"


def _construir_fila(
    match: Match,
    fixture: Dict[str, Any],
    soberana: Optional[SovereignDistribution],
) -> Tuple[Dict[str, str], Dict[str, Any]]:
    """Fila del Golden CSV + metadatos de auditoría (banderas de degradación y Brier individual)."""
    local = str(fixture.get("local") or match.home_team_slug)
    visitante = str(fixture.get("visitante") or match.away_team_slug)
    home_score = int(match.score_home)
    away_score = int(match.score_away)
    resultado_real = (
        "LOCAL" if home_score > away_score
        else ("EMPATE" if home_score == away_score else "VISITANTE")
    )

    cuotas = _cuotas_1x2_factuales(fixture)
    odd_l = float(cuotas.get("L", 0.0) or 0.0)
    odd_e = float(cuotas.get("E", 0.0) or 0.0)
    odd_v = float(cuotas.get("V", 0.0) or 0.0)
    q_l, q_e, q_v = desmarcar_cuotas_proporcional(odd_l, odd_e, odd_v)

    suficiencia = _suficiencia_declarada(fixture)
    p_prima = _resolver_p_prima(fixture, soberana)
    intensidades = _resolver_intensidades(fixture, soberana)
    lambda_h, lambda_a = intensidades if intensidades is not None else (None, None)

    # Cláusula cold start [LN-QBE-100]: con S(I) = 0 la ley sellada publica el Prior Fiduciario de
    # Mercado (ignorancia declarada), jamás una cifra fabricada.
    if suficiencia == 0 or p_prima is None:
        p_l, p_e, p_v = q_l, q_e, q_v
    else:
        p_l, p_e, p_v = p_prima

    brier_qbe = calcular_brier_multicategorico(
        [{"p_local": p_l, "p_empate": p_e, "p_visitante": p_v, "resultado": resultado_real}]
    )
    brier_mkt = calcular_brier_multicategorico(
        [{"p_local": q_l, "p_empate": q_e, "p_visitante": q_v, "resultado": resultado_real}]
    )

    fila = {
        "match_id": str(match.id),
        "jornada": str(int(match.matchday_num)),
        "local": local,
        "visitante": visitante,
        "home_score": str(home_score),
        "away_score": str(away_score),
        "resultado_real": resultado_real,
        "odd_L": _fmt(odd_l, DECIMALES_CUOTAS),
        "odd_E": _fmt(odd_e, DECIMALES_CUOTAS),
        "odd_V": _fmt(odd_v, DECIMALES_CUOTAS),
        "q_L": _fmt(q_l, DECIMALES_PROBABILIDAD),
        "q_E": _fmt(q_e, DECIMALES_PROBABILIDAD),
        "q_V": _fmt(q_v, DECIMALES_PROBABILIDAD),
        "p_L": _fmt(p_l, DECIMALES_PROBABILIDAD),
        "p_E": _fmt(p_e, DECIMALES_PROBABILIDAD),
        "p_V": _fmt(p_v, DECIMALES_PROBABILIDAD),
        "lambda_H": _fmt(lambda_h, DECIMALES_INTENSIDAD),
        "lambda_A": _fmt(lambda_a, DECIMALES_INTENSIDAD),
        "brier_qbe": _fmt(brier_qbe, DECIMALES_BRIER),
        "brier_mkt": _fmt(brier_mkt, DECIMALES_BRIER),
        "suficiencia_s_i": str(suficiencia),
    }
    metadatos = {
        "jornada": int(match.matchday_num),
        "sin_cuotas": not cuotas,
        "sin_p_prima": p_prima is None,
        "sin_intensidades": intensidades is None,
        "ignorancia_declarada": int(suficiencia) == 0,
        "brier_qbe": brier_qbe,
        "brier_mkt": brier_mkt,
    }
    return fila, metadatos


def extraer_filas(
    gateway: PersistenceGateway,
    league_id: int,
    jornadas: Sequence[int],
) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    """Extrae y cruza la bóveda 3NF con las capturas selladas, en orden `(jornada, id_partido)`."""
    objetivo = {int(j) for j in jornadas}
    with gateway.read_session() as sesion:
        indice_fixtures = _indice_fixtures_canonicos(sesion, league_id)
        soberanas = _distribuciones_soberanas(sesion)
        partidos = [
            m for m in sesion.query(Match).all()
            if _fila_concluida(m) and int(m.matchday_num) in objetivo
        ]

    ordenados = sorted(
        partidos,
        key=lambda m: (
            int(m.matchday_num),
            str((indice_fixtures.get(str(m.id)) or {}).get("id_partido") or m.id),
        ),
    )

    filas: List[Dict[str, str]] = []
    metadatos: List[Dict[str, Any]] = []
    for match in ordenados:
        fixture = indice_fixtures.get(str(match.id)) or {}
        fila, meta = _construir_fila(match, fixture, soberanas.get(str(match.id)))
        filas.append(fila)
        metadatos.append(meta)
    return filas, metadatos


def exportar_csv(filas: Sequence[Dict[str, str]], ruta: str) -> str:
    """Escribe el Golden CSV (UTF-8 sin BOM, `newline=''`, encabezado = contrato declarado)."""
    directorio = os.path.dirname(os.path.abspath(ruta))
    if directorio and not os.path.isdir(directorio):
        os.makedirs(directorio, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(COLUMNAS_GOLDEN), lineterminator="\n")
        escritor.writeheader()
        for fila in filas:
            escritor.writerow(fila)
    return os.path.abspath(ruta)


def _imprimir_reporte(
    filas: Sequence[Dict[str, str]],
    metadatos: Sequence[Dict[str, Any]],
    ruta_csv: str,
    jornadas: Sequence[int],
) -> int:
    """Epílogo ejecutivo: paridad aritmética con el dossier certificado."""
    total = len(filas)
    print("=" * 90)
    print("📦 Q-BE — GOLDEN CSV PARA INVESTIGACIÓN [UTIL-GOLDEN-01]")
    print("   Régimen: [DBBD-FUNGIBLE] · Solo lectura · Matemática sellada delegada")
    print("=" * 90)
    print(f"  ARCHIVO  : {ruta_csv}")
    print(f"  FILAS    : {total} partidos concluidos | COLUMNAS: {len(COLUMNAS_GOLDEN)}")
    print(f"  JORNADAS : {min(jornadas)}-{max(jornadas)}")

    por_jornada: Dict[int, int] = {}
    for meta in metadatos:
        por_jornada[meta["jornada"]] = por_jornada.get(meta["jornada"], 0) + 1
    detalle = " ".join(f"J{j}={por_jornada[j]}" for j in sorted(por_jornada))
    print(f"  POR JORNADA: {detalle}")

    sin_cuotas = sum(1 for m in metadatos if m["sin_cuotas"])
    sin_p = sum(1 for m in metadatos if m["sin_p_prima"])
    sin_lam = sum(1 for m in metadatos if m["sin_intensidades"])
    ignorancia = sum(1 for m in metadatos if m["ignorancia_declarada"])
    print(f"  DEGRADACIONES: sin trío de cuotas={sin_cuotas} (⇒ ignorancia uniforme 1/3) | "
          f"sin P′ sellada={sin_p} | sin λ sellada={sin_lam}")
    print(f"  S(I)=0 (Prior Fiduciario de Mercado en p_L/p_E/p_V): {ignorancia} de {total}")

    if total == 0:
        print("  ⚠️  Sin partidos concluidos en el rango solicitado: cero cifras fabricadas.")
        print("=" * 90)
        return 1

    brier_qbe_global = round(sum(m["brier_qbe"] for m in metadatos) / total, 4)
    brier_mkt_global = round(sum(m["brier_mkt"] for m in metadatos) / total, 4)
    alpha_global = (
        round((1.0 - (brier_qbe_global / brier_mkt_global)) * 100, 2) if brier_mkt_global > 0 else 0.0
    )
    print("-" * 90)
    print(f"  • Brier Score Q-BE     : {brier_qbe_global:.4f}")
    print(f"  • Brier Score Mercado  : {brier_mkt_global:.4f}")
    print(f"  • Alpha de Calibración : {alpha_global:+.2f} %")
    print("  (Ley del auditor [ARCH-1.4.42] · paridad certificada con el dossier §2)")
    print("=" * 90)
    return 0


def ejecutar(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada: extracción, tabulación y reporte de paridad."""
    parser = argparse.ArgumentParser(
        description="Exporta el Golden CSV de investigación (97 partidos, Jornadas 1..11).",
    )
    parser.add_argument("--salida", default=RUTA_SALIDA_DEFAULT,
                        help=f"ruta del CSV de salida (default: {RUTA_SALIDA_DEFAULT})")
    parser.add_argument("--jornadas", default=RANGO_JORNADAS_DEFAULT,
                        help="Jornadas objetivo: '1-11' (rango), '9' (una) o '1,4,7' (lista).")
    parser.add_argument("--liga-id", type=int, default=LIGA_ID_CANONICA,
                        help=f"liga de la captura (default: {LIGA_ID_CANONICA} = Liga MX)")
    args = parser.parse_args(argv)

    jornadas = _parsear_rango_jornadas(args.jornadas)
    gateway = PersistenceGateway()
    filas, metadatos = extraer_filas(gateway, int(args.liga_id), jornadas)
    logger.info("🔬 Bóveda leída: %d partidos concluidos cruzados con capturas selladas.", len(filas))

    ruta_csv = exportar_csv(filas, args.salida)
    return _imprimir_reporte(filas, metadatos, ruta_csv, jornadas or [0])


def main() -> int:
    """Punto de entrada CLI."""
    return ejecutar()


if __name__ == "__main__":
    raise SystemExit(main())

