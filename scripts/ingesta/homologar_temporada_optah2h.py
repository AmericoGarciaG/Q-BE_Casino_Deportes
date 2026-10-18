# -*- coding: utf-8 -*-
"""
Q-BE CD WEB — HOMOLOGACIÓN HISTÓRICA INTEGRAL DE TEMPORADA (OPTA xG + KERNEL H2H)
[ARCH-1.4.39] Homologación Histórica y Principio de Paridad Factual.
Base de Gobierno: docs/ARCH.md [ARCH-1.4.39] / docs/GOVERNANCE.md [GOVERNANCE-01]
Autoridad: Américo García Guerrero (Director Humano) — Decreto ALT-A ratificado.

Régimen: [HÍBRIDO DUAL-TRACK]
  * Pilares 1..4 (reconstrucción de cortes, caché de transporte, memoria H2H, doble
    persistencia) ⇒ [DBBD-FUNGIBLE]: identidad y transporte, CERO matemática propia.
  * Toda la matemática (A/D log-diferenciales [LN-QBE-035-B], Poisson bivariado + Dixon-Coles,
    Residuo Ortogonal GSL-3D [LN-QBE-039], Δ_epist [LN-QBE-020-C] y colapso al símplex Δ²)
    se DELEGA ÍNTEGRA a los planos sellados [DIRGEN-STRICT]:
    `generar_distribucion_soberana` ([VAULT-CORE-005]) y
    `sincronizar_distribuciones_soberanas_partidos` ([ARCH-1.6.11]).
    Este script no reimplementa una sola fórmula: la homologación es una operación de
    SUMINISTRO FÁCTICO (métricas de entrada), no de ingeniería matemática.

Pilares legislados por [ARCH-1.4.39]
------------------------------------
1. Splits de Sede Progresivos (N−1): `home_split_stats` / `away_split_stats` se reconstruyen
   desde SQLite 3NF acumulando los partidos jugados en casa y de gira de las jornadas 1..j−1.
   Invariante: PJ_local + PJ_visita ≡ PJ_total (verificado por el propio reporte).
2. Caché Fáctica de Métricas Opta (xG / SoT): cadena de procedencia DECLARADA y auditable
   (jamás inventa un número):
     (a) `data/cache_optaxg_liga_mx_2026.json` — caché congelada (formato documentado abajo);
     (b) `match_telemetry` 3NF — evidencia real por partido sellada por la ruta viva;
     (c) sensor FotMob/Opta best-effort (`--permitir-red`, OFF por defecto) que agrega el xG por
         disparo del `shotmap` OFICIAL (suma factual por equipo; fuente **D-ii ratificada** por
         Decreto `VAR-2026-J7-HOMOLOGACION` §3). Si la fuente no responde, NO publica nada (cero
         derivación especulativa);
     (d) RELACIÓN OPTA CALIBRADA declarada por [ARCH-1.4.39]: xG = max(0.5, GF · 1.05).
   La procedencia efectiva de cada club-corte se publica en el reporte (`procedencia_xg`). El
   vector homólogo publica **xG y NO xGA** (E1): el plano sellado degrada por su propia ruta
   interna a GC y el xGA publicado invertía el diagnóstico defensivo.
   Congelación reproducible: `--congelar-cache` descarga UNA vez y sella el artefacto (Pilar 2).
3. Kernel H2H Profundo (τ = 540 d): los últimos 5 enfrentamientos directos oficiales, extraídos
   de la memoria sellada `_precargar_historial_consumado_sqlite` + `_h2h_desde_historial`
   ([ARCH-1.6.13-C]) y recortados por el filtro anti-fuga `_historial_future_blind`
   (fecha < kickoff evaluado). Ley Zero-H2H [LN-QBE-020-B] si no hay duelos.
4. Doble Persistencia (Decreto ALT-A): el resultado del motor se sella SIMULTÁNEAMENTE en
   * la tabla relacional 3NF `sovereign_distributions` (fuente de verdad analítica), y
   * el payload de captura `fixtures_snapshots.matches_json` (vehículo de despacho del Visor),
   con paridad bit-a-bit garantizada por RELECTURA de la 3NF y sellado `fill-if-absent`
   (idempotencia y cero sobreescritura del contrato de captura de 7 campos).
   * `--forzar` (llave maestra de sobreescritura, Orden Ejecutiva del Director): SUSPENDE la ley
     `fill-if-absent` y fuerza la sincronización del JSON de captura con la verdad fáctica NUEVA de
     la 3NF — sobreescritura destructiva de las 7 claves, campo por campo, e idempotente (valor que
     ya coincide ⇒ cero escritura).

Axiomas operativos
------------------
* Futuro-ceguera estricta: el corte de la jornada evaluada J(j) sólo ve jornadas ≤ j−1 y la
  memoria H2H sólo ve kickoffs ESTRICTAMENTE anteriores. En un backfill histórico, el partido
  evaluado ya está consumado en `matches`: sin el filtro temporal se auto-alimentaría (fuga de
  0 días). La ruta viva no lo ve porque el fixture está `PROGRAMADO`.
* Cero invención de identidades ni de métricas: toda identidad emana del snapshot sellado
  (`id_partido`, `home_team_slug`, `away_team_slug`) y toda métrica de un plano fáctico declarado.
* Cero red por defecto: la cadena Opta degrada offline hasta el respaldo calibrado declarado.
* Paridad declarada: cada fixture sellado certifica igualdad exacta 3NF ↔ snapshot; una captura
  preexistente preservada se reporta como tal (idempotencia) y, si difiere del recálculo, se
  publica como `divergencia_declarada` (transparencia total, cero silencio).

Formato de la caché Opta congelada (`data/cache_optaxg_liga_mx_2026.json`)
--------------------------------------------------------------------------
{
  "sonda": "ARCH-1.4.39 · CACHE-OPTAXG",
  "fuente": "<procedencia factual declarada>",
  "generado_at": "YYYY-MM-DDTHH:MM:SS",
  "partidos": {
     "LIGAMX-J7-07": {
        "home": {"xg": 0.94, "xga": 1.42, "sot": 3.0, "possession": 44.0},
        "away": {"xg": 1.87, "xga": 0.71, "sot": 6.0, "possession": 56.0}
     }
  }
}
La acumulación xG/xGA de un club al corte J(j−1) exige cobertura ÍNTEGRA de sus partidos
cualificados: si a un solo partido le falta xG, ese club-corte degrada por completo al respaldo
calibrado (nunca se mezclan fuentes dentro de una misma acumulación).

Uso:
    python -m scripts.ingesta.homologar_temporada_optah2h --dry-run
    python -m scripts.ingesta.homologar_temporada_optah2h                 # J1..J17 (temporada completa)
    python -m scripts.ingesta.homologar_temporada_optah2h --jornadas 7 --json
    python -m scripts.ingesta.homologar_temporada_optah2h --jornadas 1-9 --congelar-cache
    python -m scripts.ingesta.homologar_temporada_optah2h --jornadas 1-11 --forzar  # sobreescritura forzada
    python -m scripts.ingesta.homologar_temporada_optah2h --permitir-red  # sensor FotMob/Opta
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.storage.gateway import PersistenceGateway
from src.storage.models import Match

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HomologarTemporadaOptaH2H")

# ─── Constantes legisladas ───────────────────────────────────────────────────────────────────
COMPETENCIA_CANONICA = "MEX_LIGAMX"
LIGA_ID_CANONICA = 1
RANGO_JORNADAS_DEFAULT = "1-17"
MU_LIGA_DEFAULT = 2.65
GAMMA_HOME_DEFAULT = 0.15
RUTA_CACHE_OPTA_DEFAULT = os.path.join("data", "cache_optaxg_liga_mx_2026.json")
# [VAR-2026-J7-HOMOLOGACION §6.2 · E2] Endpoints VIGENTES verificados en esta estación (HTTP 200).
URL_SENSOR_FOTMOB_FECHA = "https://www.fotmob.com/api/data/matches?date={fecha}"
URL_SENSOR_FOTMOB_PARTIDO = "https://www.fotmob.com/api/data/matchDetails?matchId={match_id}"
ETIQUETA_OFICIAL_XG = "Expected goals (xG)"
FACTOR_XG_CALIBRADO = 1.05          # [ARCH-1.4.39] relación Opta calibrada declarada
XG_MINIMO_CALIBRADO = 0.5
SEDES = ("todo", "local", "visita")
PROCEDENCIA_CACHE = "cache_local"
PROCEDENCIA_TELEMETRIA = "telemetria_3nf"
PROCEDENCIA_SENSOR = "sensor_fotmob"
PROCEDENCIA_CALIBRADA = "calibrado_gf"
# [VAR-2026-J7-HOMOLOGACION §5 · E3] Rótulo de fuente declarado en el artefacto congelado.
ETIQUETA_FUENTE_CACHE = (
    "sensor_fotmob_shotmap_optaxg · fuente D-ii ratificada (Decreto VAR-2026-J7-HOMOLOGACION §3)"
)
# [ARCH-1.4.44] Taxonomía cerrada de la procedencia xG: SÓLO las fuentes fácticas certifican
# métrica Opta real. El respaldo `calibrado_gf` (1.05·GF) declara una estimación, jamás un dato.
PROCEDENCIAS_OPTA_REALES = frozenset(
    (PROCEDENCIA_CACHE, PROCEDENCIA_TELEMETRIA, PROCEDENCIA_SENSOR)
)


def es_procedencia_opta_real(procedencia: Any) -> bool:
    """`True` sólo si la procedencia declarada pertenece a la taxonomía fáctica FotMob/Opta.

    El respaldo calibrado (`calibrado_gf`), el vacío, `None` y cualquier etiqueta desconocida se
    declaran NO reales: cero promoción de una estimación a métrica certificada.
    """
    if not isinstance(procedencia, str):
        return False
    return procedencia.strip().lower() in PROCEDENCIAS_OPTA_REALES


# ═════════════════════════════════════════════════════════════════════════════════════════════
# UTILIDADES DE IDENTIDAD Y RANGO
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _parsear_rango_jornadas(texto: str) -> List[int]:
    """Traduce `'1-10'` / `'7'` / `'1,7,10'` a la lista ordenada de jornadas objetivo."""
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


def _a_flotante(valor: Any) -> Optional[float]:
    """Conversión numérica tolerante (porcentajes '12%' y decimales) sin fabricar ceros."""
    if isinstance(valor, bool) or valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace("%", "")
    try:
        return float(texto)
    except ValueError:
        return None


# ═════════════════════════════════════════════════════════════════════════════════════════════
# PILAR 1 — RECONSTRUCTOR PROGRESIVO DE CORTES Y SPLITS DE SEDE (SQLite 3NF, CERO red)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _partidos_consumados(sesion, competition_id: str) -> List[Dict[str, Any]]:
    """Resultados oficiales sellados en 3NF (`matches`), ordenados por jornada.

    Cero red: la fuente es el calendario relacional ya persistido (marcadores `FINALIZADO`).
    """
    filas = (
        sesion.query(Match)
        .filter(
            Match.competition_id == competition_id,
            Match.score_home.isnot(None),
            Match.score_away.isnot(None),
        )
        .order_by(Match.matchday_num)
        .all()
    )
    return [
        {
            "match_id": str(f.id),
            "jornada": int(f.matchday_num or 0),
            "home_team_slug": str(f.home_team_slug),
            "away_team_slug": str(f.away_team_slug),
            "goles_local": int(f.score_home),
            "goles_visita": int(f.score_away),
        }
        for f in filas
    ]


def _partidos_de_club(
    partidos: Sequence[Dict[str, Any]], slug: str, hasta_jornada_exclusiva: int, sede: str = "todo"
) -> List[Dict[str, Any]]:
    """Partidos cualificados de un club ESTRICTAMENTE anteriores a la jornada evaluada.

    `hasta_jornada_exclusiva` = jornada evaluada j ⇒ corte J(j−1): futuro-ceguera estricta.
    `sede` ∈ {`todo`, `local`, `visita`} filtra el bloque de sede del Pilar 1.
    """
    cualificados: List[Dict[str, Any]] = []
    for p in partidos:
        if int(p["jornada"]) >= int(hasta_jornada_exclusiva):
            continue
        es_local = p["home_team_slug"] == slug
        es_visita = p["away_team_slug"] == slug
        if not (es_local or es_visita):
            continue
        if sede == "local" and not es_local:
            continue
        if sede == "visita" and not es_visita:
            continue
        cualificados.append({**p, "es_local": es_local})
    return cualificados


def _acumular_corte(cualificados: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    """Acumulado 3NF de un bloque (`pj`, `gf`, `gc`, `pts`, `pg`, `pe`, `pp`) en la sede filtrada."""
    corte = {"pj": 0, "gf": 0, "gc": 0, "pts": 0, "pg": 0, "pe": 0, "pp": 0}
    for p in cualificados:
        es_local = bool(p["es_local"])
        gf = int(p["goles_local"]) if es_local else int(p["goles_visita"])
        gc = int(p["goles_visita"]) if es_local else int(p["goles_local"])
        corte["pj"] += 1
        corte["gf"] += gf
        corte["gc"] += gc
        if gf > gc:
            corte["pg"] += 1
            corte["pts"] += 3
        elif gf == gc:
            corte["pe"] += 1
            corte["pts"] += 1
        else:
            corte["pp"] += 1
    return corte


def _bloque_sede(cualificados: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Bloque de sede publicable: `{}` sin muestra (ignorancia canónica) o el acumulado 3NF.

    Sin muestras se devuelve `{}` — la degradación limpia de Nivel 1 (`w_sede = 0`) del plano
    sellado [LN-QBE-038]; jamás se fabrica un split.
    """
    if not cualificados:
        return {}
    corte = _acumular_corte(cualificados)
    return {"pj": corte["pj"], "gf": corte["gf"], "gc": corte["gc"], "pts": corte["pts"]}


# ═════════════════════════════════════════════════════════════════════════════════════════════
# PILAR 2 — CADENA DE PROCEDENCIA DE MÉTRICAS OPTA (xG / SoT) · CERO INVENCIÓN
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _cargar_cache_opta(ruta: str) -> Tuple[Dict[str, Any], str]:
    """Nivel (a): caché Opta congelada. Retorna `({}, '')` si no existe o es ilegible."""
    if not os.path.isfile(ruta):
        return {}, ""
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            datos = json.load(fh)
    except (OSError, ValueError) as ex:
        logger.warning("Caché Opta ilegible (%s): %s", ruta, ex)
        return {}, ""
    if not isinstance(datos, dict):
        return {}, ""
    partidos = datos.get("partidos")
    if not isinstance(partidos, dict) or not partidos:
        return {}, ""
    return partidos, str(datos.get("fuente") or "caché congelada sin rótulo de fuente")


def _telemetria_3nf(sesion, identidad: Dict[str, Tuple[str, str]]) -> Dict[str, Any]:
    """Nivel (b): evidencia Opta por partido sellada en la 3NF (`match_telemetry`).

    La tabla es relacional `(match_id, team_slug)`; el lado (local/visita) se resuelve con la
    identidad canónica de `matches` y JAMÁS por heurística.
    """
    try:
        from src.storage.models import MatchTelemetry
    except ImportError:  # pragma: no cover - contrato 3NF ausente
        return {}
    partidos: Dict[str, Any] = {}
    for fila in sesion.query(MatchTelemetry).all():
        match_id = str(fila.match_id)
        home_slug, away_slug = identidad.get(match_id, ("", ""))
        team_slug = str(fila.team_slug)
        lado = "home" if team_slug == home_slug else ("away" if team_slug == away_slug else None)
        if lado is None:
            continue
        registro = partidos.setdefault(match_id, {})
        registro[lado] = {
            "xg": _a_flotante(fila.xg),
            "xga": _a_flotante(fila.xga),
            "sot": _a_flotante(fila.sot),
        }
    return partidos


def _buscar_por_etiqueta(nodo: Any, etiqueta: str) -> Optional[float]:
    """Búsqueda tolerante y acotada de una etiqueta oficial (p. ej. 'Expected goals (xG)').

    No asume rutas profundas del payload de la fuente (no verificables sin red): localiza el
    rótulo oficial y devuelve su valor numérico. Ausencia ⇒ `None` (cero derivación especulativa).
    """
    objetivo = etiqueta.strip().lower()
    if isinstance(nodo, dict):
        for clave, valor in nodo.items():
            if str(clave).strip().lower() == objetivo:
                numero = _a_flotante(valor if not isinstance(valor, dict) else valor.get("value"))
                if numero is not None:
                    return numero
        for valor in nodo.values():
            hallado = _buscar_por_etiqueta(valor, etiqueta)
            if hallado is not None:
                return hallado
    elif isinstance(nodo, list):
        for valor in nodo:
            hallado = _buscar_por_etiqueta(valor, etiqueta)
            if hallado is not None:
                return hallado
    return None


def _explorar_disparos(
    nodo: Any,
    hallados: List[Tuple[int, Dict[str, Any]]],
    clave_padre: str = "",
    dentro_periodos: bool = False,
) -> None:
    """Recorrido recursivo del payload: registra cada contenedor de disparos con su profundidad.

    Un contenedor válido porta xG y equipo y cuelga de una clave `shotmap`; se prohíbe reentrar por
    una clave de periodo (mitades) porque replican los mismos disparos.
    """
    if isinstance(nodo, dict):
        tiene_xg = any("expectedgoal" in str(k).replace("_", "").lower() for k in nodo)
        tiene_equipo = any(str(k).lower() in ("teamid", "team", "teamslug", "teamname") for k in nodo)
        if tiene_xg and tiene_equipo and "shotmap" in clave_padre and not dentro_periodos:
            hallados.append((len([s for s in clave_padre.split(".") if s]), nodo))
        for clave, valor in nodo.items():
            clave_norm = str(clave).lower()
            _explorar_disparos(
                valor,
                hallados,
                f"{clave_padre}.{clave_norm}",
                dentro_periodos or ("period" in clave_norm and "shotmap" in clave_padre),
            )
    elif isinstance(nodo, list):
        for valor in nodo:
            _explorar_disparos(valor, hallados, clave_padre, dentro_periodos)


def _recolectar_disparos(
    nodo: Any, salida: List[Dict[str, Any]], clave_padre: str = "", dentro_periodos: bool = False
) -> None:
    """Recolecta los disparos del `shotmap` DE PARTIDO: un disparo cuenta UNA sola vez.

    [VAR-2026-J7-HOMOLOGACION §6.2 · E2/D-ii] Evidencia forense (`scratch/evidencia_sensor_traza.txt`,
    partido `1000014503`): el payload espeja el MISMO disparo en varias vistas —
    `content.shotmap.shots` (canónica: 26 nodos), `content.playerStats.<id>.shotmap` (25),
    `content.matchFacts.*` (5) y `content.shotmap.Periods.*` (mitades)— y sumarlas todas multiplicaba
    el xG hasta 3× (magnitudes imposibles: 15.6 xG por equipo en un partido).
    Criterio factual adoptado: la vista de PARTIDO es la de **mínima profundidad** bajo la raíz; el
    resto son vistas derivadas por entidad/periodo. Se recolectan sólo los nodos de ese nivel.
    """
    hallados: List[Tuple[int, Dict[str, Any]]] = []
    _explorar_disparos(nodo, hallados, clave_padre, dentro_periodos)
    if not hallados:
        return
    profundidad_minima = min(profundidad for profundidad, _ in hallados)
    salida.extend(cuerpo for profundidad, cuerpo in hallados if profundidad == profundidad_minima)


def _nombre_y_id(bloque: Any) -> Tuple[str, str]:
    """Extrae (nombre, id) de un bloque de equipo de la fuente, sin heurísticas agresivas."""
    if isinstance(bloque, dict):
        nombre = bloque.get("name") or bloque.get("teamName") or bloque.get("longName")
        ident = bloque.get("id", bloque.get("teamId"))
        return (str(nombre) if nombre else "", str(ident) if ident is not None else "")
    if isinstance(bloque, str):
        return bloque, ""
    return "", ""


def _indice_fotmob_por_pareja(nodo: Any, salida: Dict[Tuple[str, str], str], resolver) -> None:
    """Índice `(slug_local, slug_visita) -> match_id oficial` de un payload de la fuente.

    La identidad se normaliza con el resolvedor canónico de clubes (`obtener_slug_club`):
    cero tablas de alias paralelas, cero mapeos inventados.

    [VAR-2026-J7-HOMOLOGACION §6.2 · E2] SUPERSEDIDA por `_indice_fotmob_de_fecha` (identidad por
    ID FotMob + ventana de calendario + filtro de competición). Se conserva sólo como utilidad de
    introspección: la ruta del sensor ya NO la invoca (el mapeo por nombre admite homónimos).
    """
    if isinstance(nodo, dict):
        pareja: Optional[Tuple[str, str]] = None
        for clave_local in ("home", "homeTeam", "home_team"):
            for clave_visita in ("away", "awayTeam", "away_team"):
                if clave_local in nodo and clave_visita in nodo:
                    nombre_l, _ = _nombre_y_id(nodo[clave_local])
                    nombre_v, _ = _nombre_y_id(nodo[clave_visita])
                    if nombre_l and nombre_v:
                        pareja = (resolver(nombre_l), resolver(nombre_v))
        ident = nodo.get("id", nodo.get("matchId"))
        if pareja and all(pareja) and ident is not None:
            salida.setdefault(pareja, str(ident))
        for valor in nodo.values():
            _indice_fotmob_por_pareja(valor, salida, resolver)
    elif isinstance(nodo, list):
        for valor in nodo:
            _indice_fotmob_por_pareja(valor, salida, resolver)


def _xg_por_lado(cuerpo: Any, identidad_fotmob: Dict[str, str]) -> Optional[Dict[str, Dict[str, float]]]:
    """Suma por equipo el xG de los disparos del `shotmap` oficial. `None` si no hay cobertura.

    La suma de xG por disparo ES la métrica Opta del equipo: agregación factual, no estimación.
    Sin AMBOS lados identificables el partido queda sin métrica (cobertura íntegra obligatoria).
    """
    disparos: List[Dict[str, Any]] = []
    _recolectar_disparos(cuerpo, disparos)
    por_equipo: Dict[str, float] = {}
    for disparo in disparos:
        # [VAR-2026-J7-HOMOLOGACION §6.2 · E2] Clave DOCUMENTADA primero (`expectedGoals`): el nodo
        # también porta `expectedGoalsOnTarget` y el orden de claves no es contrato de la fuente.
        valor_xg = _a_flotante(disparo.get("expectedGoals"))
        if valor_xg is None:
            for clave, valor in disparo.items():
                if "expectedgoal" in str(clave).replace("_", "").lower():
                    valor_xg = _a_flotante(valor)
                    break
        ident = ""
        for clave in ("teamId", "team_id", "team"):
            if clave in disparo:
                candidato = disparo[clave]
                ident = str(candidato.get("id") if isinstance(candidato, dict) else candidato)
                break
        if valor_xg is None or not ident:
            continue
        por_equipo[ident] = round(por_equipo.get(ident, 0.0) + valor_xg, 4)
    lados = [(identidad_fotmob[k], v) for k, v in por_equipo.items() if identidad_fotmob.get(k)]
    if len(lados) != 2:
        return None
    (slug_a, xg_a), (slug_b, xg_b) = lados
    return {slug_a: {"xg": xg_a, "xga": xg_b}, slug_b: {"xg": xg_b, "xga": xg_a}}


def _slug_fotmob(nombre: str) -> str:
    """Normalizador canónico de clubes ([ARCH-1.4.0]); fallo ⇒ cadena vacía (nunca un slug inventado)."""
    from src.storage.crest_resolver import obtener_slug_club

    try:
        return obtener_slug_club(str(nombre or ""))
    except (TypeError, ValueError, KeyError):
        return ""


def _desplazar_fecha(fecha: str, dias: int) -> str:
    """Desplaza `YYYYMMDD` con aritmética de CALENDARIO real (cero acarreo entero sobre el texto).

    `int('20260731') + 1 = 20260732` no es una fecha: la navegación de días exige `timedelta`.
    """
    try:
        base = datetime.strptime(str(fecha), "%Y%m%d")
    except (TypeError, ValueError):
        return str(fecha)
    return (base + timedelta(days=int(dias))).strftime("%Y%m%d")


def _nombre_canonico_liga(sesion) -> str:
    """Rótulo canónico de la competición según la 3NF (`competitions.name`); `''` si es ilegible.

    Única fuente admitida para discriminar competiciones HOMÓNIMAS en el payload de la fuente: la
    rama femenil publica los mismos nombres de club (evidencia: `'Puebla (W)'` ⇒ `club-puebla`).
    Cero etiquetas inventadas por este script.
    """
    from src.storage.models import Competition

    fila = sesion.query(Competition).filter(Competition.id == COMPETENCIA_CANONICA).first()
    return str(fila.name).strip() if fila is not None and fila.name else ""


def _pareja_identidades(
    partido: Dict[str, Any], identidad_fotmob: Dict[str, str]
) -> Optional[Tuple[str, str]]:
    """Identidades canónicas `(local, visita)` de un partido de la fuente: ID FotMob con autoridad.

    La 3NF manda (`teams.fotmob_team_id`): si la fuente publica ID de equipo, ese ID DECIDE y su
    ausencia en la 3NF DESCARTA el partido — jamás se admite un homónimo por nombre. El nombre
    canónico sólo decide cuando la fuente no publica ningún ID.
    """
    for clave_local in ("home", "homeTeam", "home_team"):
        for clave_visita in ("away", "awayTeam", "away_team"):
            if clave_local not in partido or clave_visita not in partido:
                continue
            nombre_l, id_l = _nombre_y_id(partido[clave_local])
            nombre_v, id_v = _nombre_y_id(partido[clave_visita])
            if id_l and id_v:
                mapeados = (identidad_fotmob.get(id_l, ""), identidad_fotmob.get(id_v, ""))
                return mapeados if all(mapeados) else None
            slugs = (_slug_fotmob(nombre_l), _slug_fotmob(nombre_v))
            if all(slugs):
                return slugs
    return None


def _ligas_de_competicion(payload: Any, nombre_liga: str) -> List[Dict[str, Any]]:
    """Bloques de liga del payload que corresponden a la competición canónica.

    Filtro EXACTO por rótulo cuando la 3NF lo aporta. Si la fuente no publica bloques `leagues` o
    la 3NF no aporta rótulo, se devuelven todos: la identidad por ID FotMob sigue blindando cada
    asignación. Un rótulo ausente en el payload ⇒ cero ligas (cobertura declarada, jamás un match
    ajeno).
    """
    ligas = [lg for lg in ((payload or {}).get("leagues") or []) if isinstance(lg, dict)] \
        if isinstance(payload, dict) else []
    if not ligas or not nombre_liga:
        return ligas
    objetivo = nombre_liga.strip().lower()
    return [lg for lg in ligas if str(lg.get("name") or "").strip().lower() == objetivo]


def _indice_fotmob_de_fecha(
    cliente,
    fecha: str,
    nombre_liga: str,
    identidad_fotmob: Dict[str, str],
    memo: Dict[str, Dict[Tuple[str, str], str]],
) -> Dict[Tuple[str, str], str]:
    """Índice `(slug_local, slug_visita) -> match_id oficial` de una fecha (memoizado).

    Cualquier carencia (fuente inalcanzable, HTTP != 200, payload no JSON) deja el índice vacío y
    la cadena degrada declarando ausencia: cero reintentos silenciosos, cero datos inventados.
    """
    if fecha in memo:
        return memo[fecha]
    indice: Dict[Tuple[str, str], str] = {}
    try:
        respuesta = cliente.get(URL_SENSOR_FOTMOB_FECHA.format(fecha=fecha))
    except Exception as ex:  # noqa: BLE001 — la red jamás gobierna el flujo
        logger.info("Sensor FotMob %s inalcanzable: %s", fecha, ex)
        memo[fecha] = indice
        return indice
    if respuesta.status_code != 200:
        logger.info("Sensor FotMob %s -> HTTP %s (sin datos publicados).", fecha, respuesta.status_code)
        memo[fecha] = indice
        return indice
    try:
        payload = respuesta.json()
    except ValueError:
        logger.info("Sensor FotMob %s -> payload no JSON.", fecha)
        memo[fecha] = indice
        return indice
    for liga in _ligas_de_competicion(payload, nombre_liga):
        for partido in liga.get("matches") or []:
            if not isinstance(partido, dict):
                continue
            ident = partido.get("id", partido.get("matchId"))
            pareja = _pareja_identidades(partido, identidad_fotmob)
            if pareja and ident is not None:
                indice.setdefault(pareja, str(ident))
    memo[fecha] = indice
    return indice


def _sensor_fotmob_opta(
    candidatos: Sequence[Dict[str, Any]],
    identidad_fotmob: Dict[str, str],
    permitir_red: bool,
    nombre_liga: str = "",
    timeout: float = 8.0,
) -> Dict[str, Any]:
    """Nivel (c): sensor FotMob/Opta best-effort (sólo con `--permitir-red`).

    Identidad por ID FotMob (`teams.fotmob_team_id`, autoridad 3NF), ventana de calendario ±1 día y
    filtro por rótulo de competición; agregación = suma del xG por disparo del `shotmap` OFICIAL
    (fuente D-ii ratificada por Decreto `VAR-2026-J7-HOMOLOGACION` §3: la suma por disparo ES la
    métrica Opta del equipo). Cualquier carencia —fuente inalcanzable, identidad no mapeada o
    cobertura parcial— deja el partido FUERA de la caché y el club-corte degrada al respaldo
    calibrado declarado. Cero valores derivados, cero aproximaciones, cero reintentos silenciosos.
    """
    if not permitir_red:
        return {}
    try:
        import httpx
    except ImportError:
        logger.warning("httpx no disponible: sensor FotMob omitido (cadena offline intacta).")
        return {}

    por_fecha: Dict[str, List[Dict[str, Any]]] = {}
    for cand in candidatos:
        fecha = str(cand.get("fecha_dt") or "")[:10].replace("-", "")
        if len(fecha) == 8 and fecha.isdigit():
            por_fecha.setdefault(fecha, []).append(cand)
    if not por_fecha:
        return {}

    cache: Dict[str, Any] = {}
    memo: Dict[str, Dict[Tuple[str, str], str]] = {}
    cabeceras = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    with httpx.Client(timeout=timeout, headers=cabeceras, follow_redirects=True) as cliente:
        for fecha, del_dia in sorted(por_fecha.items()):
            indice: Dict[Tuple[str, str], str] = {}
            # [VAR-2026-J7-HOMOLOGACION §6.2 · E2] Ventana de CALENDARIO ±1 día: el endpoint agrupa
            # por día de publicación y la captura porta el kickoff LOCAL; el desfase de zona horaria
            # desplaza el partido de día (evidencia: `LIGAMX-J3-01` con `fecha_dt` 2026-07-31 se
            # publica el 2026-08-01). Sin esta ventana, 4 de cada 9 jornadas quedaban sin métrica.
            for desplazamiento in (0, 1, -1):
                for pareja, ident in _indice_fotmob_de_fecha(
                    cliente,
                    _desplazar_fecha(fecha, desplazamiento),
                    nombre_liga,
                    identidad_fotmob,
                    memo,
                ).items():
                    indice.setdefault(pareja, ident)
            for cand in del_dia:
                id_oficial = indice.get((cand.get("home_team_slug"), cand.get("away_team_slug")))
                if not id_oficial:
                    continue
                try:
                    detalle = cliente.get(URL_SENSOR_FOTMOB_PARTIDO.format(match_id=id_oficial))
                except Exception as ex:  # noqa: BLE001
                    logger.info("Sensor FotMob partido %s inalcanzable: %s", id_oficial, ex)
                    continue
                if detalle.status_code != 200:
                    continue
                try:
                    cuerpo = detalle.json()
                except ValueError:
                    continue
                metrica = _xg_por_lado(cuerpo, identidad_fotmob)
                if not metrica:
                    continue
                home = metrica.get(cand.get("home_team_slug"))
                away = metrica.get(cand.get("away_team_slug"))
                # [VAR-2026-J7-HOMOLOGACION §6.2 · E2] Clave canónica = `id_partido` de la captura,
                # que ES el `matches.id` de la 3NF (verificado 9/9 en J6 y J7). Los fixtures del
                # snapshot NO portan `match_id`: sin este fallback la caché nacía con clave "None"
                # y toda la cadena Opta degradaba al respaldo calibrado declarado.
                id_canonico = str(cand.get("match_id") or cand.get("id_partido") or "")
                if home and away and id_canonico:
                    cache[id_canonico] = {"home": home, "away": away}
    return cache


def congelar_cache_opta(
    jornadas: Sequence[int],
    liga_id: int = LIGA_ID_CANONICA,
    ruta_cache: str = RUTA_CACHE_OPTA_DEFAULT,
    timeout: float = 20.0,
) -> Dict[str, Any]:
    """[Pilar 2 · E3 — Decreto `VAR-2026-J7-HOMOLOGACION` §3] Descarga UNA vez y congela la caché.

    Fuente ratificada: **D-ii** (suma del `shotmap` OFICIAL por equipo = agregación factual de
    disparos, no estimación). El artefacto sella `fuente`, `generado_at` y el mapa `partidos` en el
    formato documentado en la cabecera del módulo, de modo que toda homologación posterior corra
    OFFLINE, reproducible y auditable (Pilar 2: "descargada una vez y congelada").
    Sin cobertura factual NO se escribe artefacto (cero fabricación, cero silencio).
    """
    gateway = PersistenceGateway()
    with gateway.read_session() as sesion:
        capturas = _capturas_por_jornada(sesion, int(liga_id), jornadas)
        identidad_fotmob = _identidad_fotmob(sesion)
        nombre_liga = _nombre_canonico_liga(sesion)
        candidatos = [fx for j in jornadas for fx in capturas.get(int(j), [])]
    cache = _sensor_fotmob_opta(
        candidatos, identidad_fotmob, permitir_red=True, nombre_liga=nombre_liga, timeout=timeout
    )
    cobertura = {
        int(j): sum(1 for fx in capturas.get(int(j), []) if str(fx.get("id_partido")) in cache)
        for j in jornadas
    }
    parte: Dict[str, Any] = {
        "candidatos": len(candidatos),
        "cacheados": len(cache),
        "cobertura_por_jornada": {str(k): v for k, v in sorted(cobertura.items())},
        "ruta": ruta_cache,
        "fuente_declarada": ETIQUETA_FUENTE_CACHE,
        "escrito": False,
    }
    if not cache:
        logger.warning("Congelación abortada: el sensor no publicó ninguna métrica (cero fabricación).")
        return parte
    artefacto = {
        "fuente": ETIQUETA_FUENTE_CACHE,
        "generado_at": datetime.now().isoformat(timespec="seconds"),
        "partidos": cache,
    }
    directorio = os.path.dirname(ruta_cache)
    if directorio:
        os.makedirs(directorio, exist_ok=True)
    with open(ruta_cache, "w", encoding="utf-8") as fh:
        json.dump(artefacto, fh, ensure_ascii=False, indent=1, sort_keys=True)
    parte["escrito"] = True
    logger.info("Caché Opta congelada en %s (%s partidos).", ruta_cache, len(cache))
    return parte


def _xg_acumulado(
    cualificados: Sequence[Dict[str, Any]], cache: Dict[str, Any], etiqueta: str
) -> Tuple[float, float, str]:
    """Acumula (xG, xGA) del club al corte con COBERTURA ÍNTEGRA obligatoria.

    Si a un solo partido cualificado le falta la métrica, el club-corte degrada COMPLETO al
    respaldo calibrado declarado: jamás se mezclan fuentes dentro de una misma acumulación.
    """
    xg = 0.0
    xga = 0.0
    cubiertos = 0
    niveles: set = set()
    for p in cualificados:
        lado = "home" if p["es_local"] else "away"
        registro = (cache.get(p["match_id"]) or {}).get(lado) or {}
        valor_xg = registro.get("xg")
        if valor_xg is None:
            return 0.0, 0.0, PROCEDENCIA_CALIBRADA
        xg += float(valor_xg)
        xga += float(registro.get("xga") or 0.0)
        niveles.add(str(registro.get("procedencia") or etiqueta))
        cubiertos += 1
    if not cubiertos:
        return 0.0, 0.0, PROCEDENCIA_CALIBRADA
    unico = niveles.pop() if len(niveles) == 1 else "factual_mixto"
    return round(xg, 3), round(xga, 3), unico


def _bloque_general(
    cualificados: Sequence[Dict[str, Any]], cache: Dict[str, Any], etiqueta: str
) -> Tuple[Dict[str, Any], str]:
    """Bloque general del club al corte: acumulado 3NF + xG factual o respaldo calibrado declarado.

    Corte sin muestra ⇒ `{}` (ignorancia canónica: el motor publica su Prior Fiduciario con S(I)=0).
    Respaldo [ARCH-1.4.39]: `xG = max(0.5, GF · 1.05)`. El xGA NO se fabrica: el plano sellado
    degrada por su propia ruta interna a GC (`xga_total <= 5.0`), sin intervención de este script.
    """
    if not cualificados:
        return {}, PROCEDENCIA_CALIBRADA
    corte = _acumular_corte(cualificados)
    bloque: Dict[str, Any] = {
        "pj": corte["pj"],
        "gf": corte["gf"],
        "gc": corte["gc"],
        "pts": corte["pts"],
    }
    xg, _xga, procedencia = _xg_acumulado(cualificados, cache, etiqueta)
    if procedencia != PROCEDENCIA_CALIBRADA:
        # [VAR-2026-J7-HOMOLOGACION §6.1 · E1] Se publica SÓLO `xg` (vector legislado `xG_Opta`):
        # el xGA no viaja en el vector homólogo — el plano sellado degrada por su propia ruta
        # interna a GC. Publicarlo invertía el diagnóstico defensivo (medido: 0.5102 → 0.4825).
        bloque["xg"] = xg
    else:
        bloque["xg"] = round(max(XG_MINIMO_CALIBRADO, corte["gf"] * FACTOR_XG_CALIBRADO), 3)
    return bloque, procedencia


def _bloque_sede_con_opta(
    cualificados: Sequence[Dict[str, Any]], cache: Dict[str, Any], etiqueta: str
) -> Dict[str, Any]:
    """Split de sede del Pilar 1 enriquecido con la métrica Opta factual cuando existe cobertura.

    La métrica de sede NO es un insumo del Residuo Ortogonal GSL-3D ([LN-QBE-039] consume GF/GC de
    sede): se publica por paridad del contrato de captura del vector homólogo y por trazabilidad.
    """
    bloque = _bloque_sede(cualificados)
    if not bloque:
        return {}
    xg, _xga, procedencia = _xg_acumulado(cualificados, cache, etiqueta)
    if procedencia != PROCEDENCIA_CALIBRADA:
        # [VAR-2026-J7-HOMOLOGACION §6.1 · E1] Paridad de contrato con el bloque general: SÓLO `xg`.
        bloque["xg"] = xg
    return bloque


# ═════════════════════════════════════════════════════════════════════════════════════════════
# PILAR 3 — KERNEL H2H PROFUNDO (τ = 540 d · Ley Zero-H2H [LN-QBE-020-B])
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _memoria_h2h(
    sesion, league_id: int, fecha_ref: Optional[datetime], local: str, visitante: str
) -> List[Dict[str, Any]]:
    """Últimos enfrentamientos oficiales entre ambos clubes, ciegos al futuro del kickoff.

    [ARCH-1.4.44] Delegación íntegra en el proveedor unificado `h2h_provider`, que fusiona las dos
    autoridades legisladas: la bóveda 3NF (`_historial_future_blind`, marcador oficial) y el corpus
    longitudinal congelado (`h2h_corpus_v1`) que el diseño monotorneo de `matches` hace
    inalcanzable. El puente de identidad (`teams`) canonicaliza nombres de exhibición y slugs antes
    de cruzar. La ponderación profunda τ_deep = 540 d sigue siendo competencia del kernel
    `[LN-QBE-020-C]`; aquí sólo se recupera evidencia, nunca se fabrica (Ley Zero-H2H).
    """
    if fecha_ref is None:
        return []
    from src.core.sovereign.h2h_provider import obtener_h2h_unificado

    return obtener_h2h_unificado(sesion, local, visitante, fecha_ref, league_id=int(league_id))


# ═════════════════════════════════════════════════════════════════════════════════════════════
# PILAR 4 — DOBLE PERSISTENCIA (Decreto ALT-A): 3NF `sovereign_distributions` + CAPTURA
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _sellar_procedencia(cache: Dict[str, Any], etiqueta: str) -> Dict[str, Any]:
    """Estampa el nivel de procedencia de la métrica en cada registro (traza por partido)."""
    sellado: Dict[str, Any] = {}
    for match_id, lados in (cache or {}).items():
        if not isinstance(lados, dict):
            continue
        registro: Dict[str, Any] = {"procedencia": etiqueta}
        for lado in ("home", "away"):
            if isinstance(lados.get(lado), dict):
                registro[lado] = lados[lado]
        sellado[str(match_id)] = registro
    return sellado


def _capturas_por_jornada(
    sesion, league_id: int, jornadas: Sequence[int]
) -> Dict[int, List[Dict[str, Any]]]:
    """Fixtures de la captura VIGENTE (snapshot más reciente) de cada jornada.

    Es la identidad canónica del calendario (`id_partido`, slugs y `fecha_dt`): cero identidades
    paralelas construidas por este script.
    """
    from src.storage.models import FixtureSnapshot

    capturas: Dict[int, List[Dict[str, Any]]] = {}
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
        fixtures = (snapshot.matches_json or []) if snapshot is not None else []
        capturas[int(jornada)] = [fx for fx in fixtures if isinstance(fx, dict)]
    return capturas


def _identidad_partidos(partidos: Sequence[Dict[str, Any]]) -> Dict[str, Tuple[str, str]]:
    """Índice `match_id -> (slug_local, slug_visita)` del calendario 3NF sellado."""
    return {p["match_id"]: (p["home_team_slug"], p["away_team_slug"]) for p in partidos}


def _identidad_fotmob(sesion) -> Dict[str, str]:
    """Índice `fotmob_team_id -> slug canónico` desde la 3NF de clubes (cero mapeos inventados)."""
    from src.storage.models import Team

    return {
        str(t.fotmob_team_id): str(t.canonical_slug)
        for t in sesion.query(Team).all()
        if t.fotmob_team_id is not None and t.canonical_slug
    }


def _vector_homologo(
    sesion,
    league_id: int,
    jornada: int,
    fixture: Dict[str, Any],
    partidos: Sequence[Dict[str, Any]],
    cache: Dict[str, Any],
    etiqueta_respaldo: str,
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Ensambla el `raw_match_data` homólogo de un fixture (Pilares 1..3) y su traza fáctica.

    Corte de cada club = jornadas 1..j−1 (futuro-ceguera estricta); splits de sede del Pilar 1;
    memoria H2H profunda del Pilar 3. Cero estadística sintética: un corte vacío entra como `{}`.
    """
    id_partido = str(fixture.get("id_partido") or "")
    local = str(fixture.get("home_team_slug") or "")
    visitante = str(fixture.get("away_team_slug") or "")
    if not (id_partido and local and visitante):
        return None
    try:
        fecha_ref: Optional[datetime] = datetime.fromisoformat(str(fixture.get("fecha_dt")))
    except (TypeError, ValueError):
        fecha_ref = None

    h_st, proc_h = _bloque_general(_partidos_de_club(partidos, local, jornada), cache, etiqueta_respaldo)
    a_st, proc_a = _bloque_general(
        _partidos_de_club(partidos, visitante, jornada), cache, etiqueta_respaldo
    )
    h_split = _bloque_sede_con_opta(
        _partidos_de_club(partidos, local, jornada, "local"), cache, etiqueta_respaldo
    )
    a_split = _bloque_sede_con_opta(
        _partidos_de_club(partidos, visitante, jornada, "visita"), cache, etiqueta_respaldo
    )
    h2h = _memoria_h2h(sesion, int(league_id), fecha_ref, local, visitante)
    gira_local = _bloque_sede(_partidos_de_club(partidos, local, jornada, "visita"))
    casa_visita = _bloque_sede(_partidos_de_club(partidos, visitante, jornada, "local"))

    item: Dict[str, Any] = {
        "match_id": id_partido,
        "competition_id": COMPETENCIA_CANONICA,
        "jornada": int(jornada),
        "home_team_stats": h_st,
        "away_team_stats": a_st,
        "home_split_stats": h_split,
        "away_split_stats": a_split,
        "home_team_slug": local,
        "h2h_matches": h2h,
        # [ARCH-1.4.44] Sello de procedencia Opta REAL: exige certificación bilateral de la
        # taxonomía fáctica FotMob/Opta. Una sola plaza calibrada degrada el sello a `False`
        # (nunca se promedia un dato con una estimación presentándolos como métrica real).
        "xg_es_real_opta": bool(
            es_procedencia_opta_real(proc_h) and es_procedencia_opta_real(proc_a)
        ),
        "h2h_conteo": len(h2h),
    }
    traza: Dict[str, Any] = {
        "id_partido": id_partido,
        "jornada": int(jornada),
        "local": local,
        "visitante": visitante,
        "pj_corte_local": int(h_st.get("pj", 0) or 0),
        "pj_corte_visita": int(a_st.get("pj", 0) or 0),
        "pj_casa_local": int(h_split.get("pj", 0) or 0),
        "pj_gira_local": int(gira_local.get("pj", 0) or 0),
        "pj_casa_visita": int(casa_visita.get("pj", 0) or 0),
        "pj_gira_visita": int(a_split.get("pj", 0) or 0),
        "pj_sede_local": int(h_split.get("pj", 0) or 0),
        "pj_sede_visita": int(a_split.get("pj", 0) or 0),
        "gf_gc_local": (h_st.get("gf", 0), h_st.get("gc", 0)),
        "gf_gc_visita": (a_st.get("gf", 0), a_st.get("gc", 0)),
        "xg_local": h_st.get("xg"),
        "xg_visita": a_st.get("xg"),
        "procedencia_xg_local": proc_h,
        "procedencia_xg_visita": proc_a,
        "xg_es_real_opta": bool(
            es_procedencia_opta_real(proc_h) and es_procedencia_opta_real(proc_a)
        ),
        "h2h_duelos": len(h2h),
        "h2h_conteo": len(h2h),
    }
    # [ARCH-1.4.39] Invariante del Pilar 1: PJ_casa + PJ_gira ≡ PJ_corte (por club, por corte).
    traza["invariante_sede"] = all(
        (
            int(h_split.get("pj", 0) or 0) + int(gira_local.get("pj", 0) or 0) == int(h_st.get("pj", 0) or 0),
            int(casa_visita.get("pj", 0) or 0) + int(a_split.get("pj", 0) or 0) == int(a_st.get("pj", 0) or 0),
        )
    )
    return item, traza


def _verificar_paridad(
    gateway: PersistenceGateway, liga_id: int, jornadas: Sequence[int], valores: Dict[str, Dict[str, float]]
) -> Dict[str, Any]:
    """Certificación de paridad 3NF ↔ captura: igualdad exacta de las 6 claves por fixture.

    Una captura PREEXISTENTE preservada que difiera del recálculo se publica como divergencia
    declarada (idempotencia + transparencia: jamás se silencia, jamás se sobreescribe en silencio).
    """
    with gateway.read_session() as sesion:
        capturas = _capturas_por_jornada(sesion, int(liga_id), jornadas)
    identicas = 0
    divergentes: List[Dict[str, Any]] = []
    ausentes: List[str] = []
    for jornada in jornadas:
        for fx in capturas.get(int(jornada), []):
            id_partido = str(fx.get("id_partido") or "")
            esperado = valores.get(id_partido)
            if not esperado:
                ausentes.append(id_partido)
                continue
            capturado = {clave: fx.get(clave) for clave in esperado}
            if any(valor is None for valor in capturado.values()):
                ausentes.append(id_partido)
            elif all(abs(float(capturado[c]) - float(esperado[c])) <= 1e-9 for c in esperado):
                identicas += 1
            else:
                divergentes.append({"id_partido": id_partido, "3nf": esperado, "captura": capturado})
    return {"identicas": identicas, "divergentes": divergentes, "ausentes": ausentes}


# ═════════════════════════════════════════════════════════════════════════════════════════════
# ORQUESTADOR DE HOMOLOGACIÓN
# ═════════════════════════════════════════════════════════════════════════════════════════════
def homologar(
    jornadas: Sequence[int],
    liga_id: int = LIGA_ID_CANONICA,
    ruta_cache: str = RUTA_CACHE_OPTA_DEFAULT,
    permitir_red: bool = False,
    dry_run: bool = False,
    forzar: bool = False,
) -> Dict[str, Any]:
    """Ejecuta la homologación integral (Pilares 1..4) y retorna el parte de certificación.

    Toda la matemática se delega a los planos sellados: el puente `[ARCH-1.6.11]` para la 3NF y
    la MISMA función de sellado canónica de la utilidad de poblado para la captura del Visor.

    `forzar=True` (llave maestra de sobreescritura): la captura `fixtures_snapshots.matches_json`
    deja de preservar P′ preexistente y se sincroniza campo por campo con la relectura bit-idéntica
    de la 3NF. Cero matemática nueva: sólo se propaga la verdad fáctica ya sellada.
    """
    from scripts.utilidades.poblar_temporada_completa_backtesting import (
        _leer_suficiencia_3nf,
        _leer_valores_3nf,
        _macros_de_competencia,
        _proyectar_valores,
        _sellar_p_prima_en_capturas,
    )
    from src.core.sovereign_pipeline import ORIGEN_CAPTURA_HISTORICO
    from src.storage.distribution_sync import sincronizar_distribuciones_soberanas_partidos

    gateway = PersistenceGateway()
    mu_liga, gamma_home = _macros_de_competencia(gateway)

    with gateway.read_session() as sesion:
        partidos = _partidos_consumados(sesion, COMPETENCIA_CANONICA)
        capturas = _capturas_por_jornada(sesion, int(liga_id), jornadas)
        identidad = _identidad_partidos(partidos)
        identidad_fotmob = _identidad_fotmob(sesion)
        nombre_liga = _nombre_canonico_liga(sesion)
        cache_local, fuente_cache = _cargar_cache_opta(ruta_cache)
        telemetria = _telemetria_3nf(sesion, identidad)
        candidatos = [fx for j in jornadas for fx in capturas.get(int(j), [])]
        sensor = _sensor_fotmob_opta(
            candidatos, identidad_fotmob, permitir_red, nombre_liga=nombre_liga
        )
        # Precedencia legislada: caché congelada > telemetría 3NF > sensor vivo (todas factuales).
        cache = {
            **_sellar_procedencia(sensor, PROCEDENCIA_SENSOR),
            **_sellar_procedencia(telemetria, PROCEDENCIA_TELEMETRIA),
            **_sellar_procedencia(cache_local, PROCEDENCIA_CACHE),
        }
        dominante = (
            PROCEDENCIA_CACHE
            if cache_local
            else PROCEDENCIA_TELEMETRIA
            if telemetria
            else PROCEDENCIA_SENSOR
            if sensor
            else PROCEDENCIA_CALIBRADA
        )
        items: List[Dict[str, Any]] = []
        trazas: List[Dict[str, Any]] = []
        for jornada in jornadas:
            for fixture in capturas.get(int(jornada), []):
                armado = _vector_homologo(
                    sesion, int(liga_id), int(jornada), fixture, partidos, cache, dominante
                )
                if armado is None:
                    continue
                items.append(armado[0])
                trazas.append(armado[1])

    parte: Dict[str, Any] = {
        "sonda": "ARCH-1.4.39 · HOMOLOGACION-TEMPORADA-OPTA-H2H",
        "jornadas": [int(j) for j in jornadas],
        "liga_id": int(liga_id),
        "dry_run": bool(dry_run),
        "forzar": bool(forzar),
        "partidos_consumados_3nf": len(partidos),
        "fixtures_homologados": len(items),
        "opta": {
            "fuente_cache": fuente_cache or "sin caché congelada",
            "partidos_cache": len(cache_local),
            "partidos_telemetria": len(telemetria),
            "partidos_sensor": len(sensor),
            "nivel_dominante": dominante,
        },
        "mu_liga": mu_liga,
        "gamma_home": gamma_home,
        "trazas": trazas,
    }

    if dry_run:
        valores, suficiencias = _proyectar_valores(items, mu_liga, gamma_home)
        parte["p_prima_proyectada"] = valores
        parte["suficiencia_proyectada"] = suficiencias
        parte["escritura"] = {"modo": "dry-run", "3nf_exitosos": 0, "capturas_selladas": 0}
        return parte

    # [LN-QBE-102 / ARCH-1.4.43] Regla de Menor Privilegio escrita en el código: esta cadena es
    # una RECONSTRUCCIÓN posterior, jamás una captura de ventanilla. El candado
    # `LIVE_PROTECTION_LOCK` vetará cualquier intento de sobreescribir evidencia `EN_VIVO`.
    puente = sincronizar_distribuciones_soberanas_partidos(
        items, gateway=gateway, origen_captura=ORIGEN_CAPTURA_HISTORICO
    )
    ids = [str(item["match_id"]) for item in items]
    valores = _leer_valores_3nf(gateway, ids)
    suficiencias = _leer_suficiencia_3nf(gateway, ids)
    with gateway.write_transaction() as tx:
        captura = _sellar_p_prima_en_capturas(
            tx, int(liga_id), list(jornadas), valores, suficiencias, forzar=forzar
        )
    parte["escritura"] = {
        "modo": "produccion",
        "3nf_procesados": puente.get("procesados", 0),
        "3nf_exitosos": puente.get("exitosos", 0),
        "3nf_errores": puente.get("errores", []),
        "capturas": captura,
    }
    parte["p_prima_sellada"] = valores
    parte["suficiencia_sellada"] = suficiencias
    parte["paridad"] = _verificar_paridad(gateway, int(liga_id), jornadas, valores)
    return parte


# ═════════════════════════════════════════════════════════════════════════════════════════════
# PARTE DE CERTIFICACIÓN (CONSOLA) Y CLI
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _imprimir_parte(parte: Dict[str, Any]) -> None:
    """Publica el parte de certificación en consola (formato de auditoría)."""
    jornadas = parte["jornadas"]
    opta = parte["opta"]
    trazas = parte.get("trazas", [])
    invariantes = sum(1 for t in trazas if t.get("invariante_sede"))
    con_h2h = sum(1 for t in trazas if int(t.get("h2h_duelos", 0) or 0) > 0)
    print("\n" + "=" * 78)
    print("HOMOLOGACIÓN HISTÓRICA INTEGRAL DE TEMPORADA [ARCH-1.4.39]")
    print("Régimen [HÍBRIDO DUAL-TRACK] · Decreto ALT-A (doble persistencia) · [GOVERNANCE-01]")
    print("=" * 78)
    print(f"Jornadas objetivo        : {jornadas[0]}..{jornadas[-1]} ({len(jornadas)} jornadas)")
    print(f"Partidos consumados 3NF  : {parte['partidos_consumados_3nf']}")
    print(f"Fixtures homologados     : {parte['fixtures_homologados']}")
    print(f"Macros de competencia    : mu_liga={parte['mu_liga']} · gamma_home={parte['gamma_home']}")
    print(
        "Pilar 2 (Opta xG)        : nivel={nivel} · caché={c} · telemetría={t} · sensor={s}".format(
            nivel=opta["nivel_dominante"],
            c=opta["partidos_cache"],
            t=opta["partidos_telemetria"],
            s=opta["partidos_sensor"],
        )
    )
    print(f"  fuente de la caché     : {opta['fuente_cache']}")
    print(f"Pilar 1 (splits de sede) : {invariantes}/{len(trazas)} fixtures con PJ_casa + PJ_gira ≡ PJ_corte")
    print(f"Pilar 3 (memoria H2H)    : {con_h2h}/{len(trazas)} fixtures con duelos directos previos")
    if parte.get("dry_run"):
        print(f"\nPROYECCIÓN --DRY-RUN    : {len(parte.get('p_prima_proyectada', {}))} distribuciones "
              "calculadas por el motor sellado (SIN ESCRITURA).")
        print("=" * 78 + "\n")
        return
    escritura = parte.get("escritura", {})
    capturas = escritura.get("capturas", {}) or {}
    paridad = parte.get("paridad", {}) or {}
    print("\nPilar 4 (Doble Persistencia ALT-A)")
    print(f"  · 3NF sovereign_distributions : procesados={escritura.get('3nf_procesados')} "
          f"exitosos={escritura.get('3nf_exitosos')} errores={len(escritura.get('3nf_errores') or [])}")
    print(f"  · fixtures_snapshots.matches_json : P′ selladas={capturas.get('selladas')} "
          f"preservadas={capturas.get('preservadas')} · S(I) selladas={capturas.get('suficiencia_selladas')} "
          f"preservadas={capturas.get('suficiencia_preservadas')}")
    print(f"  · LEY DE SELLADO DE LA CAPTURA : {capturas.get('ley', 'fill-if-absent')}"
          f"{'  ⚠️  SOBREESCRITURA FORZADA (--forzar)' if parte.get('forzar') else ''}")
    if capturas.get("por_jornada"):
        for jornada, fila in sorted(capturas["por_jornada"].items()):
            print(
                f"      J{jornada:<2} fixtures={fila.get('fixtures')} P′_selladas={fila.get('selladas')} "
                f"S(I)_selladas={fila.get('suficiencia_selladas')}"
            )
    print(f"  · Paridad 3NF ↔ captura       : idénticas={paridad.get('identicas')} "
          f"divergentes={len(paridad.get('divergentes') or [])} ausentes={len(paridad.get('ausentes') or [])}")
    for divergencia in (paridad.get("divergentes") or [])[:5]:
        print(f"      ⚠ divergencia declarada preservada: {divergencia['id_partido']} "
              f"3NF={divergencia['3nf']} captura={divergencia['captura']}")
    print("=" * 78 + "\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada CLI: `python -m scripts.ingesta.homologar_temporada_optah2h`."""
    analizador = argparse.ArgumentParser(
        description="[ARCH-1.4.39] Homologación histórica integral de temporada (Opta xG + Kernel H2H)."
    )
    analizador.add_argument("--jornadas", default=RANGO_JORNADAS_DEFAULT, help="rango explícito (ej. '1-17')")
    analizador.add_argument("--liga-id", type=int, default=LIGA_ID_CANONICA, help="liga de la captura")
    analizador.add_argument("--cache", default=RUTA_CACHE_OPTA_DEFAULT, help="ruta de la caché Opta")
    analizador.add_argument("--permitir-red", action="store_true", help="habilita el sensor FotMob/Opta")
    analizador.add_argument(
        "--congelar-cache", action="store_true",
        help="[Pilar 2 · E3] descarga el sensor y CONGELA la caché Opta declarada; termina sin sellar",
    )
    analizador.add_argument(
        "--forzar", action="store_true",
        help="llave maestra de sobreescritura: SUSPENDE el `fill-if-absent` y sincroniza el JSON de "
             "captura con la verdad fáctica nueva de la 3NF (7 claves, destructivo e idempotente)",
    )
    analizador.add_argument("--dry-run", action="store_true", help="proyecta y certifica sin escribir")
    analizador.add_argument("--json", action="store_true", help="emite el parte completo en JSON")
    argumentos = analizador.parse_args(argv)

    jornadas = _parsear_rango_jornadas(argumentos.jornadas)
    if not jornadas:
        logger.error("Rango de jornadas vacío: nada que homologar.")
        return 2
    if argumentos.congelar_cache:
        parte_congelacion = congelar_cache_opta(
            jornadas, liga_id=int(argumentos.liga_id), ruta_cache=argumentos.cache
        )
        print(json.dumps(parte_congelacion, ensure_ascii=False, indent=2, default=str))
        return 0
    logger.info("Homologación %s en jornadas %s (liga %s, dry_run=%s, forzar=%s)",
                COMPETENCIA_CANONICA, jornadas, argumentos.liga_id, argumentos.dry_run,
                argumentos.forzar)
    parte = homologar(
        jornadas=jornadas,
        liga_id=int(argumentos.liga_id),
        ruta_cache=argumentos.cache,
        permitir_red=bool(argumentos.permitir_red),
        dry_run=bool(argumentos.dry_run),
        forzar=bool(argumentos.forzar),
    )
    if argumentos.json:
        print(json.dumps(parte, ensure_ascii=False, indent=2, default=str))
    else:
        _imprimir_parte(parte)
    return 1 if (parte.get("escritura", {}) or {}).get("3nf_errores") else 0


if __name__ == "__main__":
    raise SystemExit(main())
