# -*- coding: utf-8 -*-
"""
Q-BE — HIDRATACIÓN HISTÓRICA AISLADA POR TEMPORADA
[ARCH-1.4.73] / [LN-QBE-133] · [ARCH-1.4.39]

Misión
------
Poblar `data/qbe_historico.db` con `sovereign_distributions` para las 32 temporadas
2010/11–2025/26, reutilizando la lógica importada de `homologar_temporada_optah2h.py`
sin modificar el original ni `src/core/`.

Axiomas
-------
1. **Aislamiento temporal.** El corte `J(j−1)` de cada club se construye SOLO con los
   partidos de la temporada evaluada (`partidos_temporada`). El H2H y el descanso pueden
   mirar temporadas anteriores porque son futuro-ciegos por fecha; jamás miran el futuro.
2. **Cachés 2026 desactivadas.** No se carga `cache_optaxg_2026` ni `cache_macro_2026`;
   `cache` contiene únicamente `match_telemetry` de la temporada y `cache_macro={}`.
   El prior de Apertura 2025 se desactiva (`prior={}`).
3. **Cero imputación.** Los partidos 2010-2019 sin xG usan el respaldo sellado GF/GC del
   propio homologador. Las celdas sin telemetría quedan vacías en el dataset final.
4. **Una temporada, una transacción de lectura.** Los `SovereignDistribution` se escriben
   por el puente sellado `sincronizar_distribuciones_soberanas_partidos` con
   `origen_captura=HISTORICO_RECONSTRUIDO`.
5. **Alto al Fuego.** Cualquier error de dominio del motor se propaga; no se parchea.

Uso
---
    python -m scripts.ingesta.homologar_historico_aislado --temporada MEX_2015_2016_APERTURA --dry-run
    python -m scripts.ingesta.homologar_historico_aislado --temporada MEX_2015_2016_APERTURA
    python -m scripts.ingesta.homologar_historico_aislado --todas
    python -m scripts.ingesta.homologar_historico_aislado --todas --db data/qbe_historico.db --json
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import func
from sqlalchemy.orm.attributes import flag_modified

from src.storage.gateway import PersistenceGateway
from src.storage.models import (
    Base,
    Competition,
    FixtureSnapshot,
    League,
    Match,
    SovereignDistribution,
)

from scripts.ingesta.homologar_temporada_optah2h import (
    PROCEDENCIA_TELEMETRIA,
    _identidad_partidos,
    _sellar_procedencia,
    _telemetria_3nf,
    _vector_homologo,
)
from scripts.utilidades.poblar_temporada_completa_backtesting import (
    _macros_de_competencia,
    _proyectar_valores,
)
from src.core.sovereign_pipeline import ORIGEN_CAPTURA_HISTORICO
from src.storage.distribution_sync import sincronizar_distribuciones_soberanas_partidos

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HomologarHistoricoAislado")

RUTA_DB_DEFAULT = os.path.join("data", "qbe_historico.db")
LIGA_INTERNA = 1
COMPETENCIA = "MEX_LIGAMX"


def configurar_bd(ruta: str) -> PersistenceGateway:
    """Apunta el Gateway a la 3NF histórica, garantiza esquema y siembra la Liga MX."""
    import src.config as cfg

    absoluta = os.path.abspath(ruta)
    url = f"sqlite:///{absoluta.replace(os.sep, '/')}"
    cfg.settings.DATABASE_URL = url
    os.environ["DATABASE_URL"] = url
    PersistenceGateway._instance = None
    gateway = PersistenceGateway()
    Base.metadata.create_all(bind=gateway.engine)
    with gateway.write_transaction() as sesion:
        if sesion.get(Competition, COMPETENCIA) is None:
            sesion.add(Competition(id=COMPETENCIA, name="Liga MX", country="México"))
        if sesion.get(League, LIGA_INTERNA) is None:
            sesion.add(
                League(
                    id=LIGA_INTERNA,
                    name="Liga MX",
                    country="México",
                    flag="MEX",
                    fotmob_id=262,
                    is_active=False,
                )
            )
    return gateway


def _temporadas_disponibles(gateway: PersistenceGateway) -> List[str]:
    with gateway.read_session() as sesion:
        filas = (
            sesion.query(Match.season_id)
            .filter(Match.season_id.isnot(None))
            .distinct()
            .all()
        )
    return sorted({str(fila[0]) for fila in filas if fila[0]})


def _expandir_temporada(etiqueta: str) -> List[str]:
    limpia = str(etiqueta or "").strip()
    if not limpia:
        return []
    if limpia.upper().startswith("MEX_"):
        return [limpia]
    if "-" in limpia and "/" not in limpia:
        inicio, fin = limpia.split("-", 1)
        if inicio.isdigit() and fin.isdigit():
            return [f"MEX_{inicio}_{fin}_APERTURA", f"MEX_{inicio}_{fin}_CLAUSURA"]
    return [limpia]


def _partidos_por_temporada(sesion) -> Dict[str, List[Dict[str, Any]]]:
    """Partidos con marcador, agrupados por `season_id` y ordenados por jornada/fecha."""
    filas = (
        sesion.query(Match)
        .filter(
            Match.season_id.isnot(None),
            Match.score_home.isnot(None),
            Match.score_away.isnot(None),
        )
        .order_by(Match.season_id.asc(), Match.matchday_num.asc(), Match.kickoff_utc.asc())
        .all()
    )
    agrupados: Dict[str, List[Dict[str, Any]]] = {}
    for fila in filas:
        temporada = str(fila.season_id)
        agrupados.setdefault(temporada, []).append(
            {
                "match_id": str(fila.id),
                "season_id": temporada,
                "jornada": int(fila.matchday_num or 0),
                "home_team_slug": str(fila.home_team_slug),
                "away_team_slug": str(fila.away_team_slug),
                "goles_local": int(fila.score_home),
                "goles_visita": int(fila.score_away),
                "kickoff_utc": fila.kickoff_utc,
                "status": str(fila.status or ""),
            }
        )
    return agrupados


def _cache_por_temporada(
    sesion, agrupados: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Dict[str, Any]]:
    """Telemetría 3NF filtrada por temporada; cero caché Opta/Macro 2026."""
    identidad = {
        partido["match_id"]: (partido["home_team_slug"], partido["away_team_slug"])
        for partidos in agrupados.values()
        for partido in partidos
    }
    telemetria = _telemetria_3nf(sesion, identidad)
    cache: Dict[str, Dict[str, Any]] = {}
    for temporada, partidos in agrupados.items():
        ids = {partido["match_id"] for partido in partidos}
        cache[temporada] = {
            match_id: registro
            for match_id, registro in telemetria.items()
            if match_id in ids
        }
    return cache


def _fixture_de_partido(partido: Dict[str, Any]) -> Dict[str, Any]:
    fecha = partido.get("kickoff_utc")
    return {
        "id_partido": partido["match_id"],
        "home_team_slug": partido["home_team_slug"],
        "away_team_slug": partido["away_team_slug"],
        "local": partido["home_team_slug"],
        "visitante": partido["away_team_slug"],
        "fecha_dt": fecha.isoformat() if hasattr(fecha, "isoformat") else "",
        "jornada": int(partido["jornada"]),
    }


def _crear_snapshots(gateway: PersistenceGateway, agrupados: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
    """Un snapshot por temporada con la identidad/resultado de todos sus partidos.

    H2H lee `fixtures_snapshots` para reconstruir la memoria previa; el reporte de
    calibración indexa `matches_json` por `id_partido`. No se inventan momios.
    """
    ids: Dict[str, int] = {}
    with gateway.write_transaction() as sesion:
        sesion.query(FixtureSnapshot).filter(FixtureSnapshot.league_id == LIGA_INTERNA).delete()
        for temporada, partidos in sorted(agrupados.items()):
            fixtures = []
            for partido in partidos:
                fecha = partido.get("kickoff_utc")
                fixtures.append(
                    {
                        "id_partido": partido["match_id"],
                        "local": partido["home_team_slug"],
                        "visitante": partido["away_team_slug"],
                        "home_team_slug": partido["home_team_slug"],
                        "away_team_slug": partido["away_team_slug"],
                        "fecha_dt": fecha.isoformat() if hasattr(fecha, "isoformat") else "",
                        "jornada": int(partido["jornada"]),
                        "estado": "FINALIZADO",
                        "is_finished": True,
                        "marcador_actual": f'{partido["goles_local"]}-{partido["goles_visita"]}',
                        "goles_local": int(partido["goles_local"]),
                        "goles_visita": int(partido["goles_visita"]),
                        "origen_captura": ORIGEN_CAPTURA_HISTORICO,
                    }
                )
            snapshot = FixtureSnapshot(
                league_id=LIGA_INTERNA,
                matchday=0,
                matches_json=fixtures,
            )
            sesion.add(snapshot)
            sesion.flush()
            ids[temporada] = int(snapshot.id)
    return ids


def _armar_items(
    sesion,
    temporada: str,
    partidos: Sequence[Dict[str, Any]],
    cache: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Construye los `raw_match_data` de la temporada con corte estrictamente intra-temporada."""
    cache_volumen = _sellar_procedencia(cache, PROCEDENCIA_TELEMETRIA)
    items: List[Dict[str, Any]] = []
    errores: List[Dict[str, Any]] = []
    ordenados = sorted(
        partidos,
        key=lambda p: (int(p["jornada"]), str(p.get("kickoff_utc") or ""), str(p["match_id"])),
    )
    for partido in ordenados:
        fixture = _fixture_de_partido(partido)
        try:
            armado = _vector_homologo(
                sesion,
                LIGA_INTERNA,
                int(partido["jornada"]),
                fixture,
                partidos,
                cache,
                PROCEDENCIA_TELEMETRIA,
                cache_volumen,
                {},  # cache_macro 2026 desactivada
                {},  # prior Apertura 2025 desactivado
            )
        except Exception as error:
            errores.append(
                {
                    "match_id": partido["match_id"],
                    "temporada": temporada,
                    "error": f"{type(error).__name__}: {error}",
                }
            )
            continue
        if armado is None:
            errores.append(
                {
                    "match_id": partido["match_id"],
                    "temporada": temporada,
                    "error": "vector_homologo devolvió None",
                }
            )
            continue
        items.append(armado[0])
    return items, errores


def procesar_temporada(
    gateway: PersistenceGateway,
    temporada: str,
    partidos: Sequence[Dict[str, Any]],
    cache: Dict[str, Any],
    snapshot_id: int,
    *,
    dry_run: bool = False,
    limite: int = 0,
) -> Dict[str, Any]:
    """Hidrata una temporada: vector homólogo → motor → 3NF + snapshot sellado."""
    seleccion = list(partidos[: int(limite)] if int(limite) > 0 else partidos)
    with gateway.read_session() as sesion:
        items, errores = _armar_items(sesion, temporada, seleccion, cache)

    if not items:
        raise RuntimeError(
            f"[{temporada}] el homologador no produjo ningún vector; "
            f"errores={errores[:3]}"
        )

    mu_liga, gamma_home = _macros_de_competencia(gateway)
    valores, suficiencias = _proyectar_valores(items, mu_liga, gamma_home)

    if dry_run:
        return {
            "temporada": temporada,
            "partidos": len(seleccion),
            "items": len(items),
            "errores": errores,
            "mu_liga": mu_liga,
            "gamma_home": gamma_home,
            "p_prima": valores,
            "suficiencia": suficiencias,
            "escritura": {"modo": "dry-run", "3nf_exitosos": 0},
        }

    puente = sincronizar_distribuciones_soberanas_partidos(
        items, gateway=gateway, origen_captura=ORIGEN_CAPTURA_HISTORICO
    )
    if puente.get("errores"):
        raise RuntimeError(
            f"[{temporada}] fallo del motor/puente soberano: {puente['errores'][:3]}"
        )

    with gateway.write_transaction() as sesion:
        snapshot = sesion.get(FixtureSnapshot, int(snapshot_id))
        if snapshot is None:
            raise RuntimeError(f"[{temporada}] snapshot {snapshot_id} ausente")
        fixtures = list(snapshot.matches_json or [])
        actualizados = 0
        for fixture in fixtures:
            match_id = str(fixture.get("id_partido") or "")
            if match_id not in valores:
                continue
            p = valores[match_id]
            fixture.update(
                {
                    "p_local": p["p_local"],
                    "p_empate": p["p_empate"],
                    "p_visitante": p["p_visitante"],
                    "lambda_home": p["lambda_home"],
                    "lambda_away": p["lambda_away"],
                    "phi_lead2_home": p["phi_lead2_home"],
                    "suficiencia_S_I": int(suficiencias.get(match_id, 0)),
                    "origen_p_prima": "SOBERANA",
                }
            )
            actualizados += 1
        snapshot.matches_json = fixtures
        # El tipo JSON no marca el atributo como sucio con la asignación de una lista nueva
        # (SQLAlchemy compara el contenedor y puede no detectar el cambio): se fuerza el flag.
        flag_modified(snapshot, "matches_json")

    return {
        "temporada": temporada,
        "partidos": len(seleccion),
        "items": len(items),
        "errores": errores,
        "mu_liga": mu_liga,
        "gamma_home": gamma_home,
        "escritura": {
            "modo": "produccion",
            "3nf_procesados": puente.get("procesados", 0),
            "3nf_exitosos": puente.get("exitosos", 0),
            "snapshot_actualizados": actualizados,
        },
    }


def ejecutar(
    *,
    db: str = RUTA_DB_DEFAULT,
    temporadas: Optional[Sequence[str]] = None,
    todas: bool = False,
    dry_run: bool = False,
    limite: int = 0,
) -> Dict[str, Any]:
    gateway = configurar_bd(db)
    disponibles = _temporadas_disponibles(gateway)
    if todas or not temporadas:
        seleccionadas = disponibles
    else:
        seleccionadas = []
        for etiqueta in temporadas:
            seleccionadas.extend(_expandir_temporada(etiqueta))
        seleccionadas = [t for t in seleccionadas if t in disponibles]
    if not seleccionadas:
        raise RuntimeError("No hay temporadas seleccionadas disponibles en la 3NF histórica.")

    with gateway.read_session() as sesion:
        agrupados = _partidos_por_temporada(sesion)
        cache = _cache_por_temporada(sesion, agrupados)

    snapshots = _crear_snapshots(gateway, agrupados)

    reportes: List[Dict[str, Any]] = []
    for posicion, temporada in enumerate(seleccionadas, 1):
        logger.info("📡 [%d/%d] %s", posicion, len(seleccionadas), temporada)
        reporte = procesar_temporada(
            gateway,
            temporada,
            agrupados.get(temporada, []),
            cache.get(temporada, {}),
            snapshots[temporada],
            dry_run=dry_run,
            limite=limite,
        )
        reportes.append(reporte)
        logger.info(
            "   ✓ items=%d · 3nf_exitosos=%s",
            reporte["items"],
            reporte["escritura"].get("3nf_exitosos", 0),
        )

    with gateway.read_session() as sesion:
        total_soberanas = (
            sesion.query(func.count(Match.id)).filter(Match.season_id.isnot(None)).scalar() or 0
        )
        con_distribucion = (
            sesion.query(func.count(SovereignDistribution.match_id)).scalar() or 0
        )

    return {
        "sonda": "ARCH-1.4.73 · HIDRATACION-HISTORICA-AISLADA",
        "db": os.path.abspath(db),
        "dry_run": bool(dry_run),
        "temporadas_solicitadas": seleccionadas,
        "temporadas_disponibles": len(disponibles),
        "partidos_historicos": total_soberanas,
        "con_distribucion": con_distribucion,
        "reportes": reportes,
        "resumen": {
            "temporadas": len(reportes),
            "items": sum(r["items"] for r in reportes),
            "3nf_exitosos": sum(r["escritura"].get("3nf_exitosos", 0) for r in reportes),
            "errores": sum(len(r["errores"]) for r in reportes),
        },
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Hidratación histórica aislada por temporada.")
    parser.add_argument("--db", default=RUTA_DB_DEFAULT)
    parser.add_argument("--temporada", action="append", default=None)
    parser.add_argument("--todas", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limite", type=int, default=0)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        reporte = ejecutar(
            db=str(args.db),
            temporadas=args.temporada,
            todas=bool(args.todas),
            dry_run=bool(args.dry_run),
            limite=int(args.limite),
        )
    except Exception as error:
        logger.error("❌ ALTO AL FUEGO: %s", error)
        return 2

    if args.json:
        print(json.dumps(reporte, ensure_ascii=False, indent=2, default=str))
    else:
        resumen = reporte["resumen"]
        print("\n" + "=" * 84)
        print("💧 [ARCH-1.4.73] HIDRATACIÓN HISTÓRICA AISLADA")
        print("=" * 84)
        print(f"  DB: {reporte['db']}")
        print(f"  Temporadas: {resumen['temporadas']} · items: {resumen['items']} · 3NF: {resumen['3nf_exitosos']}")
        print(f"  Partidos históricos: {reporte['partidos_historicos']} · con distribución: {reporte['con_distribucion']}")
        for r in reporte["reportes"]:
            print(f"  {r['temporada']:<28} items={r['items']:>3} 3nf={r['escritura'].get('3nf_exitosos',0):>3}")
        print("=" * 84)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
