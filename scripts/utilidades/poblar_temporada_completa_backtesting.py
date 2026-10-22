# -*- coding: utf-8 -*-
"""
Q-BE CD WEB — UTILIDAD GOBERNADA: POBLADO DE TEMPORADA COMPLETA PARA EL VISOR DE BACKTESTING
[ARCH-1.4.36-ext · UTIL-POBLADO-01] Backfill de jornadas concluidas ya capturadas en la bóveda
(`fixtures_snapshots` / `standings_snapshots`) pero SIN plano 3NF (`matches`) ni captura de P′.

Régimen: [HÍBRIDO DUAL-TRACK] — transporte/identidad/inyección `[DBBD-FUNGIBLE]`;
toda la matemática (P′, corte, desmarque de vig, Brier) se DELEGA íntegra a planos sellados
`[DIRGEN-STRICT]`. Esta utilidad no reimplementa una sola fórmula.

Objetivo: que el Visor de Backtesting
(`GET /api/markets/backtesting/calibration-report`, [ARCH-1.4.38] / [LN-QBE-100]) exhiba la
temporada completa J1..JN sin inventar un solo número.

Axiomas operativos
------------------
1. Cero invención de identidades: el calendario `matches` se materializa EXCLUSIVAMENTE desde la
   identidad ya sellada en `fixtures_snapshots.matches_json` (`id_partido` `LIGAMX-J{n}-{nn}` +
   `home_team_slug`/`away_team_slug` del catálogo 3NF). Espejo exacto de la ruta viva
   (`centinela_deportivo.persistir_en_sqlite`): mismo `id`, misma jornada, mismo `status`, sin
   `kickoff_utc` (que la ruta viva tampoco sella).
2. Futuro-ceguera estricta: la evidencia de la jornada N es (a) el corte acumulado J(N-1)
   certificado en `standings_snapshots` —autoridad de bóveda, `captured_at DESC`— y (b) los duelos
   directos consumados con `fecha` ESTRICTAMENTE anterior al kickoff del fixture evaluado.
   Sin el filtro temporal, un backfill histórico incluiría el propio partido en su memoria H2H
   (fuga de 0 días): la ruta viva no lo ve porque el partido evaluado está `PROGRAMADO`.
3. Cero reimplementación matemática: P′ se genera con el puente sellado
   `sincronizar_distribuciones_soberanas_partidos` ([ARCH-1.6.11]) hacia la 3NF
   `sovereign_distributions`, y la captura del snapshot se sella con la RELECTURA bit-idéntica de
   esas filas: ambos planos portan exactamente los mismos números.
4. Marcadores y cuotas: delegados a `rellenar_marcadores_3nf` (fill-if-null, cero sobreescritura)
   y `persistir_cuotas_en_fixtures_3nf` (enriquecimiento de huecos con procedencia declarada
   `betexplorer`, cero cuotas prestadas a casas locales).
5. Idempotente y no destructivo: P′ y cuotas se sellan SOLO si el fixture no los porta; un marcador
   ya registrado se preserva; una segunda pasada escribe cero. Excepción legislada por Orden
   Ejecutiva del Director (llave maestra de sobreescritura): `--forzar` SUSPENDE la ley
   `fill-if-absent` sobre el contrato de captura P′ (7 claves) y lo sincroniza campo por campo con la
   verdad fáctica nueva de la 3NF — sigue siendo idempotente: si el valor ya coincide, cero escritura.
6. Contrato de captura ampliado por Decreto `VAR-2026-PREFLIGHT-LEGITIMATE-ENVELOPE` §1.2: además de
   las 6 claves numéricas de P′, el fixture sella el séptimo campo `suficiencia_S_I` ∈ {0, 1}
   transcrito *verbatim* de la traza sellada (`audit_trace_json` del puente) y también `fill-if-absent`:
   sin él ningún consumidor puede distinguir ignorancia declarada (Prior Fiduciario) de mala predicción.
7. Cero red salvo fuente viva explícita (`--offline-html` ausente ⇒ descarga `--url`).

Uso:
    python -m scripts.utilidades.poblar_temporada_completa_backtesting --dry-run
    python -m scripts.utilidades.poblar_temporada_completa_backtesting --offline-html scratch/betexplorer_results_raw.html
    python -m scripts.utilidades.poblar_temporada_completa_backtesting --jornadas 1-9 --json
    python -m scripts.utilidades.poblar_temporada_completa_backtesting --jornadas 1-11 --forzar
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Planos sellados: matemática y sincronización (cero reimplementación).
from src.core.sovereign_pipeline import (
    ORIGEN_CAPTURA_HISTORICO,
    evaluar_suficiencia_informativa,
    generar_distribucion_soberana,
)
from src.storage.distribution_sync import sincronizar_distribuciones_soberanas_partidos
from src.storage.gateway import PersistenceGateway
from src.storage.models import (
    Competition,
    FixtureSnapshot,
    Match,
    SovereignDistribution,
    StandingSnapshot,
    Team,
)

# Sensores sellados reutilizados (la matemática del corte y la memoria H2H viven ahí, no aquí).
from scripts.daemons.centinela_deportivo import (
    _h2h_desde_historial,
    _precargar_historial_consumado_sqlite,
)
from scripts.ingesta.ingestar_historico_betexplorer import (
    COMPETENCIA_CANONICA,
    LIGA_ID_CANONICA,
    OPERADOR_FUENTE_CUOTAS,
    URL_RESULTADOS_BETEXPLORER,
    canonizar_partidos,
    cargar_html_local,
    clubes_desde_boveda,
    construir_catalogo_3nf,
    descargar_resultados_betexplorer,
    parsear_resultados_betexplorer,
    persistir_cuotas_en_fixtures_3nf,
    rellenar_marcadores_3nf,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PoblarTemporadaBacktesting")

# Contrato de captura de P′ sellado por la ruta viva (claves EXACTAS del daemon: cero campos extra).
# [Decreto `VAR-2026-PREFLIGHT-LEGITIMATE-ENVELOPE` §1.2] El contrato se amplía con el séptimo campo
# `suficiencia_S_I` ∈ {0, 1}, transcrito *verbatim* de `audit_trace.suficiencia_S_I` del motor.
CLAVES_CAPTURA_P_PRIMA: Tuple[str, ...] = (
    "p_local",
    "p_empate",
    "p_visitante",
    "lambda_home",
    "lambda_away",
    "phi_lead2_home",
)
CLAVE_SUFICIENCIA_SI = "suficiencia_S_I"
# Ley de sellado del contrato de captura: por defecto `fill-if-absent` POR CAMPO; la llave maestra
# `--forzar` (Orden Ejecutiva del Director) la suspende y sincroniza el JSON con la verdad de la 3NF.
LEY_SELLADO_FILL_IF_ABSENT = "fill-if-absent"
LEY_SELLADO_FORZADO = "overwrite-forzado (--forzar)"
RANGO_JORNADAS_DEFAULT = "1-9"
MU_LIGA_DEFAULT = 2.65
GAMMA_HOME_DEFAULT = 0.15


def _parsear_rango_jornadas(texto: str) -> List[int]:
    """Traduce `'1-9'` / `'3'` / `'1,4,7'` a la lista ordenada de jornadas objetivo."""
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


def _capturas_por_jornada(sesion, league_id: int, jornadas: Sequence[int]) -> Dict[int, List[Dict[str, Any]]]:
    """Fixtures sellados de la bóveda por jornada (ante duplicados rige el snapshot más reciente)."""
    por_jornada: Dict[int, List[Dict[str, Any]]] = {}
    for jornada in jornadas:
        snapshot = (
            sesion.query(FixtureSnapshot)
            .filter(
                FixtureSnapshot.league_id == league_id,
                FixtureSnapshot.matchday == int(jornada),
            )
            .order_by(FixtureSnapshot.updated_at.desc())
            .first()
        )
        fixtures = (snapshot.matches_json if snapshot else None) or []
        por_jornada[int(jornada)] = [dict(fx) for fx in fixtures if isinstance(fx, dict)]
    return por_jornada


def _corte_certificado(sesion, league_id: int, jornada: int) -> Dict[str, Dict[str, Any]]:
    """Corte acumulado J`jornada` certificado en `standings_snapshots`, indexado por club.

    Jornada 0 ⇒ `{}`: sin temporada previa capturada la suficiencia S(I) = 0 y el motor publica
    ignorancia canónica (una sola firma de λ y símplex uniforme); cero estadísticas fabricadas.
    """
    if int(jornada) < 1:
        return {}
    snapshot = (
        sesion.query(StandingSnapshot)
        .filter(
            StandingSnapshot.league_id == league_id,
            StandingSnapshot.matchday == int(jornada),
        )
        .order_by(StandingSnapshot.captured_at.desc())
        .first()
    )
    if snapshot is None or not snapshot.positions_json:
        return {}
    return {
        str(fila.get("equipo")): dict(fila)
        for fila in snapshot.positions_json
        if isinstance(fila, dict) and fila.get("equipo")
    }


def _catalogo_clubes_3nf(sesion, league_id: int) -> List[Dict[str, Any]]:
    """Identidades publicadas por el catálogo `teams`: `name`, `short_name`, `canonical_slug`.

    [ARCH-1.4.26] Viva aquí, no en `src/core/sovereign/`: el puente de identidad requiere el plano
    ORM (`src.storage.models`), y los módulos del núcleo puro tienen prohibido importarlo. El
    proveedor H2H `[ARCH-1.4.44]` consume esta lectura y aplica su propia normalización.
    Lectura estrictamente pasiva: sin escrituras, sin flush y sin red.
    """
    if sesion is None:
        return []
    filas = sesion.query(Team).filter(Team.league_id == int(league_id)).all()
    return [
        {
            "name": getattr(equipo, "name", None),
            "short_name": getattr(equipo, "short_name", None),
            "canonical_slug": getattr(equipo, "canonical_slug", None),
        }
        for equipo in filas
    ]


def _historial_future_blind(sesion, league_id: int, fecha_ref: Optional[datetime]) -> List[Dict[str, Any]]:
    """Memoria H2H sellada de SQLite acotada al estado de conocimiento del kickoff evaluado.

    La extracción de marcadores consumados es la del plano sellado
    `_precargar_historial_consumado_sqlite`; esta utilidad agrega el único filtro que la ruta viva
    no necesita: `fecha < kickoff` (anti-fuga temporal en un backfill histórico).
    """
    if fecha_ref is None:
        return []
    historial = _precargar_historial_consumado_sqlite(sesion, league_id)
    return [h for h in historial if h.get("fecha") and h["fecha"] < fecha_ref]


def _items_soberanos(
    capturas: Dict[int, List[Dict[str, Any]]],
    cortes: Dict[int, Dict[str, Dict[str, Any]]],
    historial: List[Dict[str, Any]],
    jornadas: Sequence[int],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Construye el `raw_match_data` canónico de cada fixture bajo futuro-ceguera estricta.

    Contrato sellado (idéntico a `centinela_deportivo.persistir_en_sqlite`):
    `home_team_stats` / `away_team_stats` = corte J(n-1) certificado; `*_split_stats` = los mismos
    bloques cuando el corte los porta (J1..J9 no los portan ⇒ `{}` ⇒ degradación limpia de Nivel 1,
    `w_sede = 0`); `h2h_matches` = duelos consumados previos al kickoff (ley Zero-H2H si no hay).
    Cero estadísticas sintéticas: un corte vacío entra como `{}` y el motor publica su ignorancia.

    `cortes` llega YA indexado por la jornada EVALUADA (la resta vive en `ejecutar`): el snapshot
    etiquetado J`m` porta la tabla con `pj = m` ⇒ es el corte de quien evalúa J(m+1).
    """
    items: List[Dict[str, Any]] = []
    vacios = []
    for jornada in jornadas:
        corte = cortes.get(int(jornada), {})
        for fx in capturas.get(int(jornada), []):
            id_partido = str(fx.get("id_partido") or "")
            local = fx.get("local")
            visitante = fx.get("visitante")
            if not (id_partido and local and visitante):
                continue
            try:
                fecha_ref = datetime.fromisoformat(str(fx.get("fecha_dt")))
            except (TypeError, ValueError):
                fecha_ref = None
            h_st = dict(corte.get(str(local), {}))
            a_st = dict(corte.get(str(visitante), {}))
            if not h_st or not a_st:
                vacios.append(id_partido)
            items.append(
                {
                    "match_id": id_partido,
                    "competition_id": COMPETENCIA_CANONICA,
                    "jornada": int(jornada),
                    "home_team_stats": h_st,
                    "away_team_stats": a_st,
                    "home_split_stats": h_st.get("home_split_stats") or {},
                    "away_split_stats": a_st.get("away_split_stats") or {},
                    "home_team_slug": fx.get("home_team_slug") or "",
                    "h2h_matches": _h2h_desde_historial(historial, str(local), str(visitante), fecha_ref),
                }
            )
    return items, vacios


def _asegurar_calendario_3nf(
    sesion,
    capturas: Dict[int, List[Dict[str, Any]]],
    jornadas: Sequence[int],
    simular: bool = False,
) -> Dict[str, Any]:
    """Materializa las filas de `matches` ausentes desde la identidad sellada del snapshot.

    Espejo exacto de la ruta viva: `id` = `id_partido`, `matchday_num` = jornada del snapshot,
    slugs del catálogo 3NF, `status` = `estado` capturado (`FINALIZADO` / `PROGRAMADO`),
    `kickoff_utc` sin sellar (la ruta viva tampoco lo sella) y marcador delegado a
    `rellenar_marcadores_3nf` (fill-if-null). Insert-if-absent: fila existente ⇒ preservada.
    """
    reporte: Dict[str, Any] = {"insertados": 0, "preservados": 0, "sin_identidad": [], "por_jornada": {}}
    for jornada in jornadas:
        nuevos = 0
        for fx in capturas.get(int(jornada), []):
            id_partido = str(fx.get("id_partido") or "")
            slug_local = str(fx.get("home_team_slug") or "")
            slug_visita = str(fx.get("away_team_slug") or "")
            if not (id_partido and slug_local and slug_visita):
                reporte["sin_identidad"].append({"jornada": int(jornada), "id_partido": id_partido})
                continue
            if sesion.query(Match).filter(Match.id == id_partido).first():
                reporte["preservados"] += 1
                continue
            if not simular:
                sesion.add(
                    Match(
                        id=id_partido,
                        competition_id=COMPETENCIA_CANONICA,
                        matchday_num=int(jornada),
                        home_team_slug=slug_local,
                        away_team_slug=slug_visita,
                        status=str(fx.get("estado") or "SCHEDULED"),
                    )
                )
            reporte["insertados"] += 1
            nuevos += 1
        reporte["por_jornada"][int(jornada)] = {"insertados": nuevos}
    if not simular:
        sesion.flush()
    return reporte


def _macros_de_competencia(gateway: PersistenceGateway) -> Tuple[float, float]:
    """Parámetros macro (μ_liga, γ_home) del plano 3NF: mismos valores que consume el puente."""
    mu_liga, gamma_home = MU_LIGA_DEFAULT, GAMMA_HOME_DEFAULT
    with gateway.read_session() as sesion:
        comp = sesion.query(Competition).filter(Competition.id == COMPETENCIA_CANONICA).first()
        if comp:
            mu_liga = float(comp.macro_mu_liga or MU_LIGA_DEFAULT)
            gamma_home = float(comp.macro_gamma_home or GAMMA_HOME_DEFAULT)
    return mu_liga, gamma_home


def _leer_valores_3nf(gateway: PersistenceGateway, ids: Sequence[str]) -> Dict[str, Dict[str, float]]:
    """Relectura bit-idéntica de `sovereign_distributions` (sello de paridad 3NF ↔ snapshot)."""
    valores: Dict[str, Dict[str, float]] = {}
    if not ids:
        return valores
    with gateway.read_session() as sesion:
        filas = (
            sesion.query(SovereignDistribution)
            .filter(SovereignDistribution.match_id.in_(list(ids)))
            .all()
        )
        for fila in filas:
            valores[str(fila.match_id)] = {
                clave: float(getattr(fila, clave) or 0.0) for clave in CLAVES_CAPTURA_P_PRIMA
            }
    return valores


def _leer_suficiencia_3nf(gateway: PersistenceGateway, ids: Sequence[str]) -> Dict[str, int]:
    """Relectura del sello de suficiencia S(I) desde la traza sellada de la 3NF.

    Cero reimplementación: el valor se transcribe del JSON forense que el puente escribió
    (`SovereignDistributionOutput.audit_trace.model_dump()` → `audit_trace_json`). Un registro sin
    traza simplemente NO aporta sello: la captura queda sin el campo y el auditor no degrada por
    ausencia de señal (jamás se inventa un S(I)).
    """
    suficiencias: Dict[str, int] = {}
    if not ids:
        return suficiencias
    with gateway.read_session() as sesion:
        filas = (
            sesion.query(SovereignDistribution)
            .filter(SovereignDistribution.match_id.in_(list(ids)))
            .all()
        )
        for fila in filas:
            traza = fila.audit_trace_json if isinstance(fila.audit_trace_json, dict) else {}
            if traza.get(CLAVE_SUFICIENCIA_SI) is not None:
                suficiencias[str(fila.match_id)] = int(traza[CLAVE_SUFICIENCIA_SI])
    return suficiencias


def _suficiencia_de_traza(dist_out: Any) -> int:
    """Transcribe *verbatim* S(I) ∈ {0, 1} de la traza sellada del motor (`[VAULT-CORE-005]`).

    Cero reimplementación: si la traza no porta el marcador, se degrada al discriminante canónico
    publicado por el propio motor (Prior Fiduciario `p_local == 0.3333` ⇒ S(I) = 0).
    """
    traza = getattr(dist_out, "audit_trace", None)
    if traza is not None and getattr(traza, "suficiencia_S_I", None) is not None:
        return int(getattr(traza, "suficiencia_S_I"))
    return 0 if float(getattr(dist_out, "p_local", 0.0) or 0.0) == 0.3333 else 1


def _proyectar_valores(
    items: Sequence[Dict[str, Any]], mu_liga: float, gamma_home: float
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, int]]:
    """Proyección `--dry-run`: mismo motor sellado y mismos argumentos que el puente, sin escritura.

    Devuelve (captura de P′ de 6 claves, sello S(I)) en una sola pasada: ambos planos provienen de la
    MISMA llamada sellada, garantizando la paridad bit-a-bit que después se exige en la bóveda.
    """
    valores: Dict[str, Dict[str, float]] = {}
    suficiencias: Dict[str, int] = {}
    for item in items:
        dist_out = generar_distribucion_soberana(
            match_id=item["match_id"],
            raw_match_data=item,
            mu_liga=mu_liga,
            gamma_home_base=gamma_home,
        )
        valores[item["match_id"]] = {clave: float(getattr(dist_out, clave)) for clave in CLAVES_CAPTURA_P_PRIMA}
        suficiencias[item["match_id"]] = _suficiencia_de_traza(dist_out)
    return valores, suficiencias


def _sellar_p_prima_en_capturas(
    sesion,
    league_id: int,
    jornadas: Sequence[int],
    valores: Dict[str, Dict[str, float]],
    suficiencias: Optional[Dict[str, int]] = None,
    simular: bool = False,
    forzar: bool = False,
) -> Dict[str, Any]:
    """Sella en `fixtures_snapshots.matches_json` la captura de P′ y el sello de suficiencia S(I).

    Contrato de captura idéntico al de la ruta viva: 6 claves numéricas de P′ + el séptimo campo
    `suficiencia_S_I` ∈ {0, 1} (Decreto `VAR-2026-PREFLIGHT-LEGITIMATE-ENVELOPE` §1.2). El sellado es
    `fill-if-absent` **por campo**: un fixture que ya porta P′ se preserva intacto y sólo recibe el
    sello S(I) si le falta ⇒ segunda pasada = cero escrituras (idempotencia verificable en cada campo).
    [VAR-2026-J7-HOMOLOGACION §6.5 · E5] La unidad del `fill-if-absent` es el CAMPO, no el fixture:
    un contrato mutilado (p. ej. `suficiencia_S_I` presente y P′ ausente) se COMPLETA en las claves
    ausentes en lugar de preservarse a medias — las claves ya selladas jamás se sobreescriben.

    `--forzar` (llave maestra de sobreescritura ordenada por el Director): cuando `forzar=True` la ley
    `fill-if-absent` se SUSPENDE y la captura se sincroniza con la verdad fáctica NUEVA de la 3NF —
    sobreescritura destructiva de las 7 claves del contrato, una por una. Cero invención: sólo se
    escribe lo que la 3NF porta; un campo sin valor nuevo en la 3NF no se borra ni se fabrica. La
    idempotencia se preserva intacta: si el valor capturado YA coincide, no hay escritura (una segunda
    pasada forzada escribe cero).
    """
    reporte: Dict[str, Any] = {
        "selladas": 0,
        "preservadas": 0,
        "sin_valor": [],
        "sin_snapshot": [],
        "suficiencia_selladas": 0,
        "suficiencia_preservadas": 0,
        "sin_suficiencia": [],
        "por_jornada": {},
        "forzar": bool(forzar),
        "ley": LEY_SELLADO_FORZADO if forzar else LEY_SELLADO_FILL_IF_ABSENT,
    }
    suficiencias = suficiencias or {}
    for jornada in jornadas:
        snapshot = (
            sesion.query(FixtureSnapshot)
            .filter(
                FixtureSnapshot.league_id == league_id,
                FixtureSnapshot.matchday == int(jornada),
            )
            .order_by(FixtureSnapshot.updated_at.desc())
            .first()
        )
        if snapshot is None:
            reporte["sin_snapshot"].append(int(jornada))
            continue
        fixtures = [dict(fx) for fx in (snapshot.matches_json or []) if isinstance(fx, dict)]
        selladas_jornada = 0
        suficiente_jornada = 0
        for fx in fixtures:
            id_partido = str(fx.get("id_partido") or "")
            valores_fila = valores.get(id_partido)
            if not valores_fila:
                reporte["sin_valor"].append(id_partido)
            else:
                # [VAR-2026-J7-HOMOLOGACION §6.5 · E5] Fill-if-absent POR CAMPO ([Pilar 4]): un
                # fixture con contrato MUTILADO (p. ej. sólo `suficiencia_S_I`) recibe únicamente
                # las claves ausentes; las ya selladas jamás se sobreescriben.
                completadas = 0
                for clave, valor in valores_fila.items():
                    # [--forzar] sobreescritura destructiva de la clave; sin el flag, `fill-if-absent`
                    # por campo. En ambos regímenes: si el valor capturado YA coincide, cero escritura.
                    if forzar or fx.get(clave) is None:
                        if fx.get(clave) != valor:
                            fx[clave] = valor
                            completadas += 1
                if completadas:
                    reporte["selladas"] += 1
                    selladas_jornada += 1
                else:
                    reporte["preservadas"] += 1
            # Sello de suficiencia S(I): campo independiente, `fill-if-absent` (o sobreescritura bajo
            # `--forzar`) y transcripción literal de la traza sellada — cero invención de S(I).
            si_capturado = fx.get(CLAVE_SUFICIENCIA_SI)
            si_sellado = int(suficiencias[id_partido]) if id_partido in suficiencias else None
            if si_sellado is None:
                if si_capturado is None:
                    reporte["sin_suficiencia"].append(id_partido)
                else:
                    reporte["suficiencia_preservadas"] += 1
            elif (forzar or si_capturado is None) and si_capturado != si_sellado:
                fx[CLAVE_SUFICIENCIA_SI] = si_sellado
                reporte["suficiencia_selladas"] += 1
                suficiente_jornada += 1
            else:
                reporte["suficiencia_preservadas"] += 1
        if (selladas_jornada or suficiente_jornada) and not simular:
            snapshot.matches_json = fixtures
        reporte["por_jornada"][int(jornada)] = {
            "selladas": selladas_jornada,
            "fixtures": len(fixtures),
            "suficiencia_selladas": suficiente_jornada,
        }
    if not simular:
        sesion.flush()
    return reporte

def _construir_por_jornada(
    capturas: Dict[int, List[Dict[str, Any]]],
    canonico: Dict[int, List[Dict[str, Any]]],
    items: Sequence[Dict[str, Any]],
    calendario: Dict[str, Any],
    captura_p: Dict[str, Any],
    jornadas: Sequence[int],
) -> Dict[int, Dict[str, int]]:
    """Tabla de trazabilidad por jornada (evidencia fáctica: nada se agrega por estimación)."""
    suficiencia = {int(j): 0 for j in jornadas}
    for item in items:
        if evaluar_suficiencia_informativa(item):
            suficiencia[int(item["jornada"])] = suficiencia.get(int(item["jornada"]), 0) + 1
    filas: Dict[int, Dict[str, int]] = {}
    for jornada in jornadas:
        j = int(jornada)
        filas[j] = {
            "fixtures": len(capturas.get(j, [])),
            "partidos_publicados": len(canonico.get(j, [])),
            "matches_insertados": int((calendario.get("por_jornada", {}).get(j, {}) or {}).get("insertados", 0)),
            "p_prima_selladas": int((captura_p.get("por_jornada", {}).get(j, {}) or {}).get("selladas", 0)),
            "suficiencia_selladas": int(
                (captura_p.get("por_jornada", {}).get(j, {}) or {}).get("suficiencia_selladas", 0)
            ),
            "con_suficiencia": int(suficiencia.get(j, 0)),
        }
    return filas


def _imprimir_reporte(reporte: Dict[str, Any]) -> None:
    """Bitácora legible del poblado (misma evidencia que el reporte JSON)."""
    sep = "=" * 88
    print("\n" + sep)
    print("🧪 Q-BE CD WEB — POBLADO GOBERNADO DE TEMPORADA COMPLETA PARA EL VISOR DE BACKTESTING")
    print(f"   [ARCH-1.4.36-ext · UTIL-POBLADO-01] · Régimen [HÍBRIDO DUAL-TRACK] · Modo: {reporte['modo']}")
    print(sep)
    print(f"📂 Fuente de resultados: {reporte['fuente']}")
    print(f"🏛️  Identidad 3NF: {reporte['identidad']['clubes']} clubes | "
          f"partidos publicados en las jornadas objetivo: {reporte['identidad']['partidos_publicados']}")
    print(f"🎯 Planos sellados: rellenar_marcadores_3nf · persistir_cuotas_en_fixtures_3nf · "
          f"sincronizar_distribuciones_soberanas_partidos")
    print("-" * 88)
    print(f"   {'J':>2} {'FX':>4} {'PUB':>4} {'NEW':>4} {'P′':>4} {'S(I)':>5}  DICTAMEN")
    for jornada, fila in sorted(reporte["por_jornada"].items()):
        dictamen = "evidencia real" if fila["con_suficiencia"] else "ignorancia canónica S(I)=0"
        print(f"   {int(jornada):>2} {fila['fixtures']:>4} {fila['partidos_publicados']:>4} "
              f"{fila['matches_insertados']:>4} {fila['p_prima_selladas']:>4} {fila['con_suficiencia']:>5}  {dictamen}")
    print("-" * 88)
    cal = reporte["calendario_3nf"]
    mar = reporte["marcadores_3nf"]
    cuo = reporte["cuotas_1x2"]
    dist = reporte["distribuciones_3nf"]
    dis = reporte["captura_p_prima"]
    print(f"1) CALENDARIO 3NF `matches` (insert-if-absent): insertados={cal['insertados']} "
          f"preservados={cal['preservados']} sin_identidad={len(cal['sin_identidad'])}")
    print(f"2) MARCADORES 3NF (fill-if-null): actualizados={mar['actualizados']} preservados={mar['preservados']} "
          f"invertidos={mar['invertidos']} sin_fila_3nf={len(mar['sin_fila_3nf'])}")
    print(f"3) CUOTAS 1X2 (procedencia {OPERADOR_FUENTE_CUOTAS}): escritas={cuo['cuotas_escritas']} "
          f"preservadas={cuo['preservadas']} sin_snapshot={len(cuo['sin_snapshot'])} "
          f"incompletas={len(cuo['cuotas_incompletas'])}")
    print(f"4) DISTRIBUCIONES P′ `sovereign_distributions`: procesados={dist['procesados']} "
          f"exitosos={dist['exitosos']} errores={len(dist['errores'])}")
    print(f"5) CAPTURA P′ EN SNAPSHOT (ley: {dis.get('ley', LEY_SELLADO_FILL_IF_ABSENT)}): "
          f"selladas={dis['selladas']} "
          f"preservadas={dis['preservadas']} sin_valor={len(dis['sin_valor'])}")
    print(f"6) SELLO DE SUFICIENCIA S(I) ∈ {{0, 1}} (ley: {dis.get('ley', LEY_SELLADO_FILL_IF_ABSENT)}, "
          f"transcripción literal): "
          f"selladas={dis.get('suficiencia_selladas', 0)} "
          f"preservadas={dis.get('suficiencia_preservadas', 0)} "
          f"sin_sello={len(dis.get('sin_suficiencia', []))}")
    print("-" * 88)
    print(f"📊 Partidos auditables del rango {reporte['jornadas'][0]}..{reporte['jornadas'][-1]}: "
          f"{reporte['auditables_esperados']} | evidencia real: {reporte['suficiencia']['con_evidencia']} | "
          f"ignorancia canónica: {reporte['suficiencia']['ignorancia_canonica']}")
    for etiqueta, avisos in (
        ("⚠️  Identidad sin slug (fixtures NO materializados)", cal["sin_identidad"]),
        ("⚠️  Pares publicados sin fila 3NF", mar["sin_fila_3nf"]),
        ("⚠️  Errores del puente soberano", dist["errores"]),
    ):
        if avisos:
            print(f"{etiqueta}: {avisos[:5]} (total {len(avisos)})")
    if reporte["modo"] == "DRY-RUN":
        print("🧪 MODO DRY-RUN: proyección matemática sin un solo byte escrito en la bóveda.")
        print("   Nota: en dry-run la simulación no encadena la inserción del calendario, por lo que")
        print("   `sin_fila_3nf` refleja sólo el estado PREVIO de `matches` (en escritura el calendario")
        print("   se materializa primero dentro de la misma Unit of Work y ese contador cae a 0).")
    print(sep + "\n")

def _parser() -> argparse.ArgumentParser:
    """CLI de la utilidad (cero red por defecto sólo si se declara `--offline-html`)."""
    parser = argparse.ArgumentParser(
        prog="poblar_temporada_completa_backtesting",
        description="[ARCH-1.4.36-ext · UTIL-POBLADO-01] Poblado gobernado de jornadas concluidas "
                    "para el Visor de Backtesting (identidad 3NF + marcadores + cuotas + P′).",
    )
    parser.add_argument("--jornadas", default=RANGO_JORNADAS_DEFAULT,
                        help="Jornadas objetivo: '1-9' (rango), '3' (una) o '1,4,7' (lista).")
    parser.add_argument("--liga-id", type=int, default=LIGA_ID_CANONICA,
                        help="league_id de la bóveda multi-torneo (default: %(default)s = Liga MX).")
    parser.add_argument("--url", default=URL_RESULTADOS_BETEXPLORER,
                        help="Fuente viva de resultados publicados (default: BetExplorer Liga MX).")
    parser.add_argument("--offline-html", default="",
                        help="Evidencia local de la fuente (cero red): ruta a un HTML capturado.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Proyecta el poblado completo sin escribir en la bóveda.")
    parser.add_argument("--forzar", action="store_true",
                        help="Llave maestra de sobreescritura: SUSPENDE el `fill-if-absent` y sincroniza "
                             "las 7 claves del contrato de captura P′ con la verdad nueva de la 3NF "
                             "(destructivo por campo e idempotente: valor igual ⇒ cero escritura).")
    parser.add_argument("--json", action="store_true",
                        help="Emite el reporte máquina (JSON) por stdout en lugar de la bitácora.")
    return parser


def ejecutar(argv: Optional[List[str]] = None) -> int:
    """Orquesta el poblado: fuente -> identidad 3NF -> calendario -> marcadores -> cuotas -> P′.

    Todo el cálculo y toda la escritura delegada pasan por planos sellados; esta función sólo
    gobierna el orden transaccional y la trazabilidad.
    """
    args = _parser().parse_args(argv)
    forzar = bool(args.forzar)
    jornadas = _parsear_rango_jornadas(args.jornadas)
    if not jornadas:
        print("❌ [ABORTO] Rango de jornadas vacío: nada que poblar.")
        return 2

    # ── 1. FUENTE DE RESULTADOS (cero red si hay evidencia offline declarada) ──────────────
    if args.offline_html:
        fuente = args.offline_html
        logger.info("📂 Fuente offline declarada: %s", fuente)
        html = cargar_html_local(fuente)
    else:
        fuente = args.url
        logger.info("📡 Fuente viva declarada: %s", fuente)
        html = descargar_resultados_betexplorer(args.url)
    bloques = parsear_resultados_betexplorer(html)
    if not bloques:
        print("❌ [ABORTO] La fuente no publicó resultados parseables (cero filas inventadas).")
        return 2

    # ── 2. LECTURA DEL ESTADO DE LA BÓVEDA (identidad, capturas y cortes certificados) ─────
    gateway = PersistenceGateway()
    # [ARCH-1.4.55] Continuidad de operación: respaldo atómico ANTES de escribir (API online de
    # SQLite verificada con `PRAGMA quick_check`). El DRY-RUN no muta la bóveda ⇒ no respalda.
    if not args.dry_run:
        logger.info(
            "🛡️ Respaldo atómico previo al lote verificado: %s",
            gateway.crear_backup_boveda_sqlite(),
        )
    with gateway.read_session() as sesion:
        catalogo = construir_catalogo_3nf(sesion, args.liga_id)
        clubes = clubes_desde_boveda(sesion, args.liga_id)
        capturas = _capturas_por_jornada(sesion, args.liga_id, jornadas)
        # Corte certificado de la jornada EVALUADA J(n) = snapshot etiquetado J(n-1) (tabla con pj = n-1):
        # evidencia estrictamente anterior al inicio de J(n) ⇒ cero fuga de futuro. J1 ⇒ snapshot J0 inexistente ⇒ {}.
        cortes = {int(j): _corte_certificado(sesion, args.liga_id, int(j) - 1) for j in jornadas}
        historial = _precargar_historial_consumado_sqlite(sesion, args.liga_id)
    if not catalogo:
        print("❌ [ABORTO] Catálogo 3NF vacío: no hay identidades contra las que canonizar.")
        return 2

    canonico = canonizar_partidos(bloques, catalogo)
    objetivo = {int(j) for j in jornadas}
    canonico = {int(j): partidos for j, partidos in canonico.items() if int(j) in objetivo}
    if not canonico:
        print("❌ [ABORTO] Ningún partido publicado pertenece a las jornadas objetivo.")
        return 2

    items, vacios = _items_soberanos(capturas, cortes, historial, jornadas)
    if not items:
        print("❌ [ABORTO] La bóveda no porta fixtures para las jornadas objetivo (cero filas inventadas).")
        return 2
    ids = [item["match_id"] for item in items]
    mu_liga, gamma_home = _macros_de_competencia(gateway)
    logger.info(
        "🔬 Fixtures objetivo=%d | partidos publicados=%d | mu_liga=%.3f gamma_home=%.3f",
        len(items), sum(len(v) for v in canonico.values()), mu_liga, gamma_home,
    )

    # ── 3. EJECUCIÓN ──────────────────────────────────────────────────────────────────────
    if args.dry_run:
        valores, suficiencias = _proyectar_valores(items, mu_liga, gamma_home)
        with gateway.read_session() as sesion:
            calendario = _asegurar_calendario_3nf(sesion, capturas, jornadas, simular=True)
            marcadores = rellenar_marcadores_3nf(sesion, args.liga_id, canonico, simular=True)
            cuotas = persistir_cuotas_en_fixtures_3nf(sesion, args.liga_id, canonico, simular=True)
            captura_p = _sellar_p_prima_en_capturas(
                sesion, args.liga_id, jornadas, valores, suficiencias, simular=True, forzar=forzar
            )
        distribuciones: Dict[str, Any] = {"procesados": len(items), "exitosos": len(valores), "errores": []}
    else:
        with gateway.write_transaction() as tx:
            calendario = _asegurar_calendario_3nf(tx, capturas, jornadas, simular=False)
            marcadores = rellenar_marcadores_3nf(tx, args.liga_id, canonico, simular=False)
            cuotas = persistir_cuotas_en_fixtures_3nf(tx, args.liga_id, canonico, simular=False)
        # [ARCH-1.6.11] Puente sellado: genera y sella P′ en `sovereign_distributions`.
        # [LN-QBE-102 / ARCH-1.4.43] Menor Privilegio explícito: este lote RECONSTRUYE historia
        # (jamás captura en ventanilla) ⇒ jamás podrá sobreescribir una fila `EN_VIVO`.
        distribuciones = sincronizar_distribuciones_soberanas_partidos(
            items, gateway=gateway, origen_captura=ORIGEN_CAPTURA_HISTORICO
        )
        valores = _leer_valores_3nf(gateway, ids)
        # [Decreto `VAR-2026-PREFLIGHT-LEGITIMATE-ENVELOPE` §1.2] Séptimo campo: el sello S(I) se relee
        # de la traza sellada del puente (transcripción literal, cero invención) y se captura junto a P′.
        suficiencias = _leer_suficiencia_3nf(gateway, ids)
        # [PARIDAD 3NF <-> SNAPSHOT] La captura del fixture porta EXACTAMENTE los números sellados.
        with gateway.write_transaction() as tx:
            captura_p = _sellar_p_prima_en_capturas(
                tx, args.liga_id, jornadas, valores, suficiencias, simular=False, forzar=forzar
            )

    con_evidencia = sum(1 for item in items if evaluar_suficiencia_informativa(item))
    reporte: Dict[str, Any] = {
        "sonda": "ARCH-1.4.36-ext · UTIL-POBLADO-01",
        "regimen": "HIBRIDO DUAL-TRACK",
        "modo": "DRY-RUN" if args.dry_run else "ESCRITURA",
        "jornadas": [int(j) for j in jornadas],
        "fuente": fuente,
        "liga_id": int(args.liga_id),
        "identidad": {
            "clubes": len(clubes),
            "partidos_publicados": sum(len(v) for v in canonico.values()),
        },
        "calendario_3nf": calendario,
        "marcadores_3nf": marcadores,
        "cuotas_1x2": cuotas,
        "distribuciones_3nf": distribuciones,
        "captura_p_prima": captura_p,
        "suficiencia": {
            "con_evidencia": con_evidencia,
            "ignorancia_canonica": len(items) - con_evidencia,
            "fixtures_sin_corte": vacios,
        },
        "por_jornada": _construir_por_jornada(capturas, canonico, items, calendario, captura_p, jornadas),
        "auditables_esperados": len(items),
    }

    if args.json:
        print(json.dumps(reporte, ensure_ascii=False, indent=2, default=str))
    else:
        _imprimir_reporte(reporte)
    return 0


def main() -> int:
    """Punto de entrada CLI."""
    return ejecutar()


if __name__ == "__main__":
    raise SystemExit(main())
