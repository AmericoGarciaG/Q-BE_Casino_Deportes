# -*- coding: utf-8 -*-
"""
[LN-QBE-112] / [ARCH-1.4.51] SANDBOX MICRO-DINÁMICAS & CIERRE — PIPELINE AUTÓNOMO CLI-FIRST.

Misión
------
Cerrar el soporte de laboratorio de las 12 dimensiones del Tratado Vol. I modelando las 15
variables restantes: Balón Parado (Dimensión 5, 𝒯_Spc, V18-V21), Fricción Disciplinaria
(Dimensión 6, 𝒯_Dsc, V22-V24), Cronometría (Dimensión 9, 𝒯_Time, V33-V36), Banca
(Dimensión 10, 𝒯_Sub, V37-V38) y Cierre Tardío (Dimensión 12, 𝒯_Cls, V43-V44).

Régimen: `[HÍBRIDO DUAL-TRACK]`
* `[DIRGEN-STRICT]`: la aritmética legislada por `[LN-QBE-112]` —ratio 1T/2T con guardas y
  clamp, índice de rotación del XI y umbral de fragilidad de cierre `xGA₈₀₋₉₀ ≥ 0.35`— vive en
  funciones puras. No se toca `src/core/` ni se reimplementa λ.
* `[DBBD-FUNGIBLE]`: composición del corte, celdas bipartitas, semáforos, CLI y tablero ASCII.

Axiomas operativos
------------------
1. **Sólo lectura:** `PersistenceGateway.read_session()` + `json.load` del corpus congelado.
   Prohibido escribir en `data/qbe_database.db`; prohibido abrir red.
2. **Futuro-ceguera (N−1):** el corte de cada club son los partidos con `matchday_num < N` en
   estado terminal. El fixture evaluado jamás alimenta su propia acumulación.
3. **Cobertura íntegra:** una variable sólo publica magnitud si TODOS los partidos del corte de
   AMBOS clubes traen la clave granular. Una sola ausencia ⇒ `None`.
4. **Cero defaults como evidencia:** `0` de `fouls`/`red_cards` y `50.0` de posesión son
   centinelas del esquema ORM, no mediciones (`[GOVERNANCE-01]`).
5. **Bipartita simétrica:** `EVALUADO` exige magnitud real en AMBOS clubes; en caso contrario
   `SIN EVIDENCIA (FASE 6)` con `local = visita = None`. Prohibida la imputación.
6. **Sin señal a λ:** las 15 variables son diagnóstico; `[VAULT-CORE-001/005]` no se tocan.

Uso:
    python -m scripts.laboratorio.sandbox_micro_dinamicas_pipeline --partido LIGAMX-J11-07
    python -m scripts.laboratorio.sandbox_micro_dinamicas_pipeline --jornada 11
    python -m scripts.laboratorio.sandbox_micro_dinamicas_pipeline --partido LIGAMX-J11-07 --json
    python -m scripts.laboratorio.sandbox_micro_dinamicas_pipeline --jornada 11 --temporada 2026
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import or_, select

from src.storage.gateway import PersistenceGateway
from src.storage.models import FixtureSnapshot, Match, MatchTelemetry

logger = logging.getLogger("SandboxMicroDinamicas")

# ── Rutas, estados y presentación ──────────────────────────────────────────────────────────────
RUTA_CACHE_OPTA_PLANTILLA = os.path.join("data", "cache_optaxg_liga_mx_{temporada}.json")
RUTA_CACHE_TELEMETRIA_PLANTILLA = os.path.join("data", "cache_telemetria_liga_mx_{temporada}.json")
TEMPORADA_DEFAULT = "2026"

ESTADO_EVALUADO = "EVALUADO"
ESTADO_SIN_EVIDENCIA = "SIN EVIDENCIA"
NOTA_FASE_6 = "SIN EVIDENCIA (FASE 6)"
ESTADOS_TERMINALES = ("FINALIZADO", "FINISHED")

NIVEL_VERDE = "VERDE"
NIVEL_AMARILLO = "AMARILLO"
NIVEL_NEUTRAL = "NEUTRAL"
NIVEL_ROJO = "ROJO"
GLIFO = {
    NIVEL_VERDE: "🟢", NIVEL_AMARILLO: "🟡", NIVEL_NEUTRAL: "⚪", NIVEL_ROJO: "🔴",
    ESTADO_EVALUADO: "🟢", ESTADO_SIN_EVIDENCIA: "⚪",
}
ANCHO_TABLERO = 94
HORIZONTE = "─" * (ANCHO_TABLERO - 4)

# Defaults del esquema ORM: una fila así NO es evidencia (cero conversión inventada).
_POSS_DEFAULT = 50.0
_SOT_DEFAULT = 0.0
_SOTA_DEFAULT = 0.0

# ── Cotas [DIRGEN-STRICT] de `[LN-QBE-112]`: se LEEN, jamás se recalibran ──────────────────────
COTA_RATIO_1T_2T = 10.0          # clamp de contención del ratio 1T/2T (guardas de /0)
RATIO_NEUTRO = 1.0               # 0/0 = producción nula en ambos tiempos
UMBRAL_XGA_CIERRE = 0.35         # xGA 80'-90'+ ⇒ alerta de quiebre del Pago Anticipado
UMBRAL_INDICE_ROJA = 0.25        # rojas/PJ ⇒ alerta de asimetría numérica

REGLA_CORTE = "matchday_num < N ∧ estado ∈ {FINALIZADO, FINISHED} (futuro-ceguera N−1)"
NODOS_GOBERNANZA = ("LN-QBE-112", "ARCH-1.4.51")
NODO_PAGO_ANTICIPADO = "LN-QBE-083"

# ── Taxonomía de las 15 micro-dinámicas (`[LN-QBE-112]`) ───────────────────────────────────────
# `claves` son las llaves granulares ACEPTADAS del corpus congelado; la primera publicada gana.
_TAXONOMIA: Dict[str, Dict[str, Any]] = {
    "V18": {
        "variable": "xG a balón parado", "unidad": "xG/90",
        "claves": ("xg_set_piece", "xg_balon_parado"),
        "nota_evidencia": "xG a balón parado por 90' del corte N−1 (cobertura íntegra).",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): el corpus congelado sólo publica xG total; no existe split de balón parado.",
    },
    "V19": {
        "variable": "xGA a balón parado", "unidad": "xGA/90",
        "claves": ("xga_set_piece", "xga_balon_parado"),
        "nota_evidencia": "xGA concedido a balón parado por 90' del corte N−1 (cobertura íntegra).",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): el corpus congelado sólo publica xGA total; no existe split de balón parado.",
    },
    "V20": {
        "variable": "Córners a favor", "unidad": "córners/90",
        "claves": ("corners", "corneres", "corners_90"),
        "nota_evidencia": "Córners por 90' del corte N−1 (cobertura íntegra).",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): el sensor congelado no publica córners.",
    },
    "V21": {
        "variable": "Penales a favor", "unidad": "pen/PJ",
        "claves": ("penalties_won", "penales_favor", "penales"),
        "nota_evidencia": "Penales a favor por partido del corte N−1 (cobertura íntegra).",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): el sensor congelado no publica penales.",
    },
    "V22": {
        "variable": "Faltas en tercio defensivo", "unidad": "faltas/90",
        "claves": ("fouls_def_third", "faltas_tercio_defensivo"),
        "nota_evidencia": "Faltas en tercio defensivo por 90' del corte N−1 (cobertura íntegra).",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): no existe feed de faltas por tercio; `match_telemetry.fouls` permanece en el default del esquema y no es evidencia.",
    },
    "V23": {
        "variable": "Tarjetas amarillas", "unidad": "TA/90",
        "claves": ("yellow_cards", "tarjetas_amarillas"),
        "nota_evidencia": "Amarillas por 90' del corte N−1 (cobertura íntegra).",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): el sensor congelado no publica tarjetas amarillas.",
    },
    "V24": {
        "variable": "Índice de expulsión", "unidad": "rojas/PJ",
        "claves": ("red_cards", "tarjetas_rojas"),
        "nota_evidencia": "Rojas por partido del corte N−1 (cobertura íntegra); alerta si > 0.25.",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): `match_telemetry.red_cards` no es evidencia (default 0 sin ingestión) y el corpus no publica rojas granulares.",
    },
    "V33": {
        "variable": "Ratio xG 1T/2T", "unidad": "ratio",
        "claves": ("xg_1t", "xg_2t"),
        "nota_evidencia": "Ratio xG 1T/2T con clamp [0.1, 10.0] y guarda de división por cero.",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): el corpus no publica reparto de xG por tiempo.",
    },
    "V34": {
        "variable": "Ratio xGA 1T/2T", "unidad": "ratio",
        "claves": ("xga_1t", "xga_2t"),
        "nota_evidencia": "Ratio xGA 1T/2T con clamp [0.1, 10.0] y guarda de división por cero.",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): el corpus no publica reparto de xGA por tiempo.",
    },
    "V35": {
        "variable": "Goles anotados 0-15'", "unidad": "goles/90",
        "claves": ("goals_0_15", "goles_0_15"),
        "nota_evidencia": "Goles anotados en 0-15' por 90' del corte N−1 (cobertura íntegra).",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): `matches` sólo publica marcador final; no hay goles por intervalo.",
    },
    "V36": {
        "variable": "Goles concedidos 0-15'", "unidad": "goles/90",
        "claves": ("goals_conceded_0_15", "goles_concedidos_0_15"),
        "nota_evidencia": "Goles concedidos en 0-15' por 90' del corte N−1 (cobertura íntegra).",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): `matches` sólo publica marcador final; no hay goles por intervalo.",
    },
    "V37": {
        "variable": "xG de suplentes", "unidad": "xG/90",
        "claves": ("subs_xg", "xg_suplentes"),
        "nota_evidencia": "xG aportado por suplentes por 90' del corte N−1 (cobertura íntegra).",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): no existe feed de xG por suplente ni acta de cambios.",
    },
    "V38": {
        "variable": "Rotación del XI", "unidad": "índice 0-1",
        "claves": ("lineup", "xi"),
        "nota_evidencia": "Índice 1 − Jaccard promedio entre alineaciones consecutivas del corte N−1.",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): no existe feed de alineaciones titulares.",
    },
    "V43": {
        "variable": "xG 80'-90'+ (clutch)", "unidad": "xG/90",
        "claves": ("xg_80_90", "xg_clutch"),
        "nota_evidencia": "xG producido en 80'-90'+ por 90' del corte N−1 (cobertura íntegra).",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): el corpus no publica reparto de xG por minuto.",
    },
    "V44": {
        "variable": "xGA 80'-90'+ (fragilidad)", "unidad": "xGA/90",
        "claves": ("xga_80_90", "xga_tardio"),
        "nota_evidencia": "xGA permitido en 80'-90'+ por 90' del corte N−1 (cobertura íntegra).",
        "nota_fase_6": "SIN EVIDENCIA (FASE 6): el corpus no publica reparto de xGA por minuto.",
    },
}

# ── Agrupación por dimensión (contrato de salida del Juez) ─────────────────────────────────────
_DIMENSIONES: Dict[str, Tuple[str, ...]] = {
    "dimension_5_balon_parado": ("V18", "V19", "V20", "V21"),
    "dimension_6_disciplina": ("V22", "V23", "V24"),
    "dimension_9_cronometria": ("V33", "V34", "V35", "V36"),
    "dimension_10_banca": ("V37", "V38"),
    "dimension_12_cierre": ("V43", "V44"),
}
TOTAL_VARIABLES = sum(len(ids) for ids in _DIMENSIONES.values())


# ═════════════════════════════════════════════════════════════════════════════════════════════════
# CELDAS BIPARTITAS Y ARITMÉTICA DE PRESENTACIÓN (pura, sin I/O)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def _clamp(valor: float, minimo: float, maximo: float) -> float:
    """Contención numérica pura (sin saneamiento silencioso de entradas inválidas)."""
    return max(minimo, min(maximo, float(valor)))


def _redondear(valor: Optional[float], decimales: int = 4) -> Optional[float]:
    """Redondeo de presentación; `None` atraviesa intacto (cero invención)."""
    return None if valor is None else round(float(valor), decimales)


def _tasa(total: Optional[float], pj: int) -> Optional[float]:
    """Tasa por partido (≈ por 90 min). `None` sin total o sin muestra."""
    if total is None or pj <= 0:
        return None
    return float(total) / float(pj)


def _celda(identificador: str, local: Optional[float], visita: Optional[float]) -> Dict[str, Any]:
    """Celda bipartita homogénea `{id, variable, unidad, local, visita, estado, nota}`.

    `EVALUADO` sólo si AMBOS clubes publican magnitud real; en caso contrario la celda degrada
    completa a `SIN EVIDENCIA (FASE 6)` con `local = visita = None` — jamás un cero ficticio.
    """
    definicion = _TAXONOMIA[identificador]
    evaluada = local is not None and visita is not None
    local_num = _redondear(local) if evaluada else None
    visita_num = _redondear(visita) if evaluada else None
    return {
        "id": identificador,
        "variable": definicion["variable"],
        "unidad": definicion["unidad"],
        "local": local_num,
        "visita": visita_num,
        "local_num": local_num,
        "visita_num": visita_num,
        "estado": ESTADO_EVALUADO if evaluada else ESTADO_SIN_EVIDENCIA,
        "nota": definicion["nota_evidencia"] if evaluada else definicion["nota_fase_6"],
    }

# ═════════════════════════════════════════════════════════════════════════════════════════════════
# PROTOCOLO DE INGESTA FÁCTICA (caché congelada + 3NF, todo en SÓLO LECTURA)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def ruta_cache_opta(temporada: str = TEMPORADA_DEFAULT) -> str:
    """Ruta absoluta del artefacto Opta congelado `[ARCH-1.4.39]` para la temporada declarada."""
    return os.path.join(PROJECT_ROOT, RUTA_CACHE_OPTA_PLANTILLA.format(temporada=str(temporada)))


def ruta_cache_telemetria(temporada: str = TEMPORADA_DEFAULT) -> str:
    """Ruta absoluta del artefacto de telemetría congelada para la temporada declarada."""
    return os.path.join(PROJECT_ROOT, RUTA_CACHE_TELEMETRIA_PLANTILLA.format(temporada=str(temporada)))


def cargar_corpus(ruta: str, etiqueta: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Lee un artefacto congelado y publica su procedencia (`fuente`, `generado_at`, partidos).

    Artefacto ausente o ilegible ⇒ mapa vacío + `disponible = False`: el reporte degrada a
    `SIN EVIDENCIA`. Jamás se fabrica una cifra para tapar la ausencia de feed.
    """
    meta: Dict[str, Any] = {
        "etiqueta": etiqueta,
        "ruta": os.path.relpath(ruta, PROJECT_ROOT).replace(os.sep, "/"),
        "disponible": False,
        "fuente": None,
        "generado_at": None,
        "partidos": 0,
        "error": None,
    }
    if not os.path.exists(ruta):
        meta["error"] = f"Artefacto congelado ausente: {meta['ruta']}"
        return {}, meta
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            artefacto = json.load(fh)
    except (OSError, ValueError) as exc:
        meta["error"] = f"{type(exc).__name__}: {exc}"
        return {}, meta
    partidos = artefacto.get("partidos") if isinstance(artefacto, dict) else None
    if not isinstance(partidos, dict):
        meta["error"] = "El artefacto no publica el mapa 'partidos'."
        return {}, meta
    meta.update({
        "disponible": True,
        "fuente": artefacto.get("fuente"),
        "generado_at": artefacto.get("generado_at"),
        "partidos": len(partidos),
    })
    return partidos, meta


def _registro(cache: Dict[str, Any], match_id: str, lado: str) -> Dict[str, Any]:
    """Bloque `home` | `away` del partido en el corpus congelado; `{}` si no está publicado."""
    registro = cache.get(str(match_id))
    if not isinstance(registro, dict):
        return {}
    bloque = registro.get(lado)
    return bloque if isinstance(bloque, dict) else {}


def _magnitud(bloque: Dict[str, Any], claves: Sequence[str]) -> Optional[float]:
    """Primera magnitud numérica publicada entre las claves aceptadas; `None` si no hay feed."""
    for clave in claves:
        valor = bloque.get(clave)
        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            return float(valor)
    return None


def _partidos_de_club(sesion: Any, slug: str, jornada_corte: int) -> List[Dict[str, Any]]:
    """Corte futuro-ciego N−1: partidos TERMINALES del club con `matchday_num < N`."""
    consulta = (
        select(Match)
        .where(
            Match.matchday_num.isnot(None),
            Match.matchday_num < int(jornada_corte),
            Match.status.in_(ESTADOS_TERMINALES),
            or_(Match.home_team_slug == slug, Match.away_team_slug == slug),
        )
        .order_by(Match.matchday_num, Match.id)
    )
    partidos: List[Dict[str, Any]] = []
    for registro in sesion.execute(consulta).scalars().all():
        es_local = registro.home_team_slug == slug
        goles_favor = registro.score_home if es_local else registro.score_away
        goles_contra = registro.score_away if es_local else registro.score_home
        if goles_favor is None or goles_contra is None:
            logger.warning("[LN-QBE-112] Partido sin marcador terminal: %s", registro.id)
            continue
        partidos.append({
            "match_id": str(registro.id),
            "jornada": int(registro.matchday_num or 0),
            "es_local": bool(es_local),
            "rival": str(registro.away_team_slug if es_local else registro.home_team_slug),
            "goles_favor": int(goles_favor),
            "goles_contra": int(goles_contra),
        })
    return partidos

# ═════════════════════════════════════════════════════════════════════════════════════════════════
# AGREGACIÓN GRANULAR DE CORTE (cobertura íntegra obligatoria)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def _serie_club(
    partidos: Sequence[Dict[str, Any]],
    cache: Dict[str, Any],
    claves: Sequence[str],
) -> Dict[str, Any]:
    """Suma una clave granular con cobertura ÍNTEGRA sobre el corte de un club.

    Publica `total` sólo si TODOS los partidos del corte traen la clave; cualquier ausencia deja
    `total = None` y enumera los `faltantes` (trazabilidad de la degradación, no imputación).
    """
    suma = 0.0
    faltantes: List[str] = []
    for partido in partidos:
        lado = "home" if partido["es_local"] else "away"
        valor = _magnitud(_registro(cache, partido["match_id"], lado), claves)
        if valor is None:
            faltantes.append(partido["match_id"])
            continue
        suma += valor
    completo = bool(partidos) and not faltantes
    return {
        "claves": list(claves),
        "pj": len(partidos),
        "cubiertos": len(partidos) - len(faltantes),
        "total": round(suma, 6) if completo else None,
        "faltantes": faltantes,
    }


def _alineaciones_club(
    partidos: Sequence[Dict[str, Any]], cache: Dict[str, Any]
) -> List[Tuple[str, ...]]:
    """XI titular de cada partido del corte en orden cronológico; `[]` si falta UNA alineación."""
    alineaciones: List[Tuple[str, ...]] = []
    for partido in partidos:
        lado = "home" if partido["es_local"] else "away"
        bloque = _registro(cache, partido["match_id"], lado)
        xi = bloque.get("lineup") or bloque.get("xi")
        if not isinstance(xi, (list, tuple)) or len(xi) < 11:
            return []
        alineaciones.append(tuple(str(jugador) for jugador in list(xi)[:11]))
    return alineaciones


def _ratio_de_club(
    partidos: Sequence[Dict[str, Any]], cache: Dict[str, Any], clave_1t: str, clave_2t: str
) -> Tuple[Optional[float], Dict[str, Any]]:
    """Ratio 1T/2T de un club con doble cobertura íntegra (numerador y denominador)."""
    serie_1t = _serie_club(partidos, cache, (clave_1t,))
    serie_2t = _serie_club(partidos, cache, (clave_2t,))
    detalle: Dict[str, Any] = {
        clave_1t: serie_1t["total"],
        clave_2t: serie_2t["total"],
        "pj": serie_1t["pj"],
        "cubiertos": min(serie_1t["cubiertos"], serie_2t["cubiertos"]),
        "faltantes": sorted(set(serie_1t["faltantes"]) | set(serie_2t["faltantes"])),
    }
    if serie_1t["total"] is None or serie_2t["total"] is None:
        detalle["ratio"] = None
        return None, detalle
    ratio = calcular_ratio_cronometria(serie_1t["total"], serie_2t["total"])
    detalle["ratio"] = ratio
    return ratio, detalle

# ═════════════════════════════════════════════════════════════════════════════════════════════════
# ARITMÉTICA [DIRGEN-STRICT] — `[LN-QBE-112]` (pura, determinista, sin I/O)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def calcular_ratio_cronometria(xg_1t: float, xg_2t: float) -> float:
    """Ratio de cronometría `1T/2T` con guardas de división por cero y clamp simétrico.

    * `1T = 2T = 0` ⇒ `RATIO_NEUTRO` (1.0): no hay producción que comparar.
    * `2T = 0 ∧ 1T > 0` ⇒ saturación en `COTA_RATIO_1T_2T` (10.0), jamás `inf`.
    * Resultado acotado a `[1/COTA_RATIO_1T_2T, COTA_RATIO_1T_2T]` = `[0.1, 10.0]`.

    Entradas negativas violan el dominio (xG no puede ser negativo) y levantan `ValueError`:
    no se sanean en silencio.
    """
    if float(xg_1t) < 0.0 or float(xg_2t) < 0.0:
        raise ValueError("xG por tiempo no puede ser negativo [LN-QBE-112].")
    if float(xg_2t) == 0.0:
        if float(xg_1t) == 0.0:
            return RATIO_NEUTRO
        return COTA_RATIO_1T_2T
    ratio = float(xg_1t) / float(xg_2t)
    return round(_clamp(ratio, 1.0 / COTA_RATIO_1T_2T, COTA_RATIO_1T_2T), 6)


def evaluar_alerta_fragilidad_cierre(xga_80_90: Optional[float]) -> Dict[str, Any]:
    """Semáforo de fragilidad tardía (`[LN-QBE-112]` §5, salpicadura a `[LN-QBE-083]`).

    Regla fiduciaria: `xGA₈₀₋₉₀ ≥ 0.35` ⇒ riesgo de perder ventajas de 2 goles en el cierre y
    habilitación del Doble Cobro (+PA) bajo vigilancia. `None` ⇒ ni alerta ni absolución.
    """
    if xga_80_90 is None:
        return {
            "xga_80_90": None,
            "umbral": UMBRAL_XGA_CIERRE,
            "riesgo_quiebre_pa": None,
            "diagnostico": f"{NOTA_FASE_6}: sin reparto de xGA por minuto no se puede auditar el cierre.",
            "cobertura_pa": "NO COMPUTABLE — SIN EVIDENCIA",
            "glifo": GLIFO[NIVEL_NEUTRAL],
            "lectura": "Ni alerta ni absolución: ausencia declarada.",
        }
    valor = float(xga_80_90)
    if valor < 0.0:
        raise ValueError("xGA tardío no puede ser negativo [LN-QBE-112].")
    riesgo = valor >= UMBRAL_XGA_CIERRE
    if riesgo:
        diagnostico = (
            f"FRAGILIDAD DE CIERRE: xGA 80'-90'+ = {valor:.4f} ≥ {UMBRAL_XGA_CIERRE:.2f}; "
            "alta probabilidad de perder ventajas de 2 goles en el tramo final."
        )
        cobertura = f"DOBLE COBRO (+PA) HABILITADO CON VIGILANCIA [{NODO_PAGO_ANTICIPADO}]"
        glifo = GLIFO[NIVEL_ROJO]
        lectura = "Riesgo de quiebre del Pago Anticipado."
    else:
        diagnostico = (
            f"CIERRE SÓLIDO: xGA 80'-90'+ = {valor:.4f} < {UMBRAL_XGA_CIERRE:.2f}; "
            "el cerrojo defensivo sostiene la ventaja en el tramo final."
        )
        cobertura = "COBERTURA +PA SIN ALERTA"
        glifo = GLIFO[NIVEL_VERDE]
        lectura = "Sin señal de fragilidad tardía."
    return {
        "xga_80_90": round(valor, 4),
        "umbral": UMBRAL_XGA_CIERRE,
        "riesgo_quiebre_pa": bool(riesgo),
        "diagnostico": diagnostico,
        "cobertura_pa": cobertura,
        "glifo": glifo,
        "lectura": lectura,
    }


def calcular_indice_rotacion_xi(alineaciones: Sequence[Sequence[str]]) -> Optional[float]:
    """Índice de rotación del XI: `1 − Jaccard` promedio entre alineaciones consecutivas.

    `None` si hay menos de dos alineaciones comparables; el resultado se acota a `[0, 1]`.
    """
    comparables: List[Tuple[str, ...]] = []
    for xi in alineaciones:
        limpio = tuple(str(jugador) for jugador in xi if str(jugador).strip())
        if limpio:
            comparables.append(limpio)
    if len(comparables) < 2:
        return None
    indices: List[float] = []
    for previa, actual in zip(comparables, comparables[1:]):
        conjunto_previo, conjunto_actual = set(previa), set(actual)
        union = conjunto_previo | conjunto_actual
        if not union:
            continue
        indices.append(1.0 - (len(conjunto_previo & conjunto_actual) / len(union)))
    if not indices:
        return None
    return round(_clamp(sum(indices) / len(indices), 0.0, 1.0), 4)

# ═════════════════════════════════════════════════════════════════════════════════════════════════
# RESOLUCIÓN DE FIXTURE Y COBERTURA DECLARADA (3NF + caché, sólo lectura)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def _fixture_de_partido(sesion: Any, match_id: str) -> Tuple[Dict[str, Any], Optional[Any]]:
    """Busca el fixture en `fixtures_snapshots.matches_json` (snapshot más reciente primero)."""
    consulta = (
        select(FixtureSnapshot)
        .order_by(FixtureSnapshot.updated_at.desc(), FixtureSnapshot.id.desc())
    )
    for snapshot in sesion.execute(consulta).scalars().all():
        for item in (snapshot.matches_json or []):
            if isinstance(item, dict) and str(item.get("id_partido")) == str(match_id):
                return dict(item), snapshot
    return {}, None


def _cobertura_telemetria(
    sesion: Any, ids: Sequence[str], slug: str
) -> Dict[str, Any]:
    """Cobertura de `match_telemetry` y detección de feeds disciplinarios publicados.

    Una fila con la tripleta default (`sot = 0.0`, `sota = 0.0`, `possession_pct = 50.0`) NO es
    una medición: se contabiliza como ausente. `fouls`/`red_cards` sólo se declaran publicados con
    un valor estrictamente positivo (un `0` es indistinguible del centinela del esquema).
    """
    resultado: Dict[str, Any] = {
        "pj": len(ids),
        "cubiertos": 0,
        "publica_fouls": False,
        "publica_rojas": False,
    }
    if not ids:
        return resultado
    consulta = select(MatchTelemetry).where(
        MatchTelemetry.match_id.in_(list(ids)),
        MatchTelemetry.team_slug == slug,
    )
    for fila in sesion.execute(consulta).scalars().all():
        sot = getattr(fila, "sot", None)
        sota = getattr(fila, "sota", None)
        poss = getattr(fila, "possession_pct", None)
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (sot, sota, poss)):
            if not (
                float(sot) == _SOT_DEFAULT
                and float(sota) == _SOTA_DEFAULT
                and float(poss) == _POSS_DEFAULT
            ):
                resultado["cubiertos"] += 1
        faltas = getattr(fila, "fouls", None)
        rojas = getattr(fila, "red_cards", None)
        if isinstance(faltas, (int, float)) and float(faltas) > 0.0:
            resultado["publica_fouls"] = True
        if isinstance(rojas, (int, float)) and float(rojas) > 0.0:
            resultado["publica_rojas"] = True
    return resultado


def _cobertura_xg_base(
    partidos: Sequence[Dict[str, Any]], cache: Dict[str, Any]
) -> Dict[str, Any]:
    """Cobertura del xG/xGA agregado (soporte del corpus, NO evidencia de las 15 variables)."""
    cubiertos = 0
    for partido in partidos:
        lado = "home" if partido["es_local"] else "away"
        bloque = _registro(cache, partido["match_id"], lado)
        if _magnitud(bloque, ("xg",)) is not None and _magnitud(bloque, ("xga",)) is not None:
            cubiertos += 1
    return {"pj": len(partidos), "cubiertos": cubiertos}


# ═════════════════════════════════════════════════════════════════════════════════════════════════
# CONSTRUCCIÓN DE DIMENSIONES (composición DBBD; aritmética DIRGEN delegada)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def _celdas_por_tasa(
    partidos_local: Sequence[Dict[str, Any]],
    partidos_visita: Sequence[Dict[str, Any]],
    cache: Dict[str, Any],
    identificadores: Sequence[str],
) -> Dict[str, Dict[str, Any]]:
    """Celdas tasa/90 o /partido: cobertura íntegra en los DOS cortes o degradación honesta."""
    celdas: Dict[str, Dict[str, Any]] = {}
    for identificador in identificadores:
        claves = _TAXONOMIA[identificador]["claves"]
        serie_local = _serie_club(partidos_local, cache, claves)
        serie_visita = _serie_club(partidos_visita, cache, claves)
        celdas[identificador] = _celda(
            identificador,
            _tasa(serie_local["total"], serie_local["pj"]),
            _tasa(serie_visita["total"], serie_visita["pj"]),
        )
    return celdas


def _construir_dimension_5(
    partidos_local: Sequence[Dict[str, Any]],
    partidos_visita: Sequence[Dict[str, Any]],
    cache: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Dimensión 5 (`𝒯_Spc`): balón parado y penales (V18-V21)."""
    return _celdas_por_tasa(
        partidos_local, partidos_visita, cache, _DIMENSIONES["dimension_5_balon_parado"]
    )


def _construir_dimension_6(
    partidos_local: Sequence[Dict[str, Any]],
    partidos_visita: Sequence[Dict[str, Any]],
    cache: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Dimensión 6 (`𝒯_Dsc`): fricción disciplinaria y riesgo de expulsión (V22-V24)."""
    return _celdas_por_tasa(
        partidos_local, partidos_visita, cache, _DIMENSIONES["dimension_6_disciplina"]
    )

def _construir_dimension_9(
    partidos_local: Sequence[Dict[str, Any]],
    partidos_visita: Sequence[Dict[str, Any]],
    cache: Dict[str, Any],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """Dimensión 9 (`𝒯_Time`): cronometría de gol y ratios de desgaste (V33-V36)."""
    celdas = _celdas_por_tasa(partidos_local, partidos_visita, cache, ("V35", "V36"))
    ratio_33_local, detalle_33_local = _ratio_de_club(partidos_local, cache, "xg_1t", "xg_2t")
    ratio_33_visita, detalle_33_visita = _ratio_de_club(partidos_visita, cache, "xg_1t", "xg_2t")
    ratio_34_local, detalle_34_local = _ratio_de_club(partidos_local, cache, "xga_1t", "xga_2t")
    ratio_34_visita, detalle_34_visita = _ratio_de_club(partidos_visita, cache, "xga_1t", "xga_2t")
    celdas["V33"] = _celda("V33", ratio_33_local, ratio_33_visita)
    celdas["V34"] = _celda("V34", ratio_34_local, ratio_34_visita)
    ratios = {
        "V33": {"local": detalle_33_local, "visita": detalle_33_visita},
        "V34": {"local": detalle_34_local, "visita": detalle_34_visita},
    }
    return celdas, ratios


def _construir_dimension_10(
    partidos_local: Sequence[Dict[str, Any]],
    partidos_visita: Sequence[Dict[str, Any]],
    cache: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Dimensión 10 (`𝒯_Sub`): banca y rotación del XI (V37-V38)."""
    celdas = _celdas_por_tasa(partidos_local, partidos_visita, cache, ("V37",))
    rotacion_local = calcular_indice_rotacion_xi(_alineaciones_club(partidos_local, cache))
    rotacion_visita = calcular_indice_rotacion_xi(_alineaciones_club(partidos_visita, cache))
    celdas["V38"] = _celda("V38", rotacion_local, rotacion_visita)
    return celdas


def _construir_dimension_12(
    partidos_local: Sequence[Dict[str, Any]],
    partidos_visita: Sequence[Dict[str, Any]],
    cache: Dict[str, Any],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """Dimensión 12 (`𝒯_Cls`): cierre tardío y salpicadura al Pago Anticipado (V43-V44)."""
    celdas = _celdas_por_tasa(partidos_local, partidos_visita, cache, ("V43", "V44"))
    alerta_local = evaluar_alerta_fragilidad_cierre(celdas["V44"]["local_num"])
    alerta_visita = evaluar_alerta_fragilidad_cierre(celdas["V44"]["visita_num"])
    riesgos = [
        alerta["riesgo_quiebre_pa"]
        for alerta in (alerta_local, alerta_visita)
        if alerta["riesgo_quiebre_pa"] is not None
    ]
    riesgo_global = any(riesgos) if riesgos else None
    if riesgo_global is None:
        diagnostico = f"{NOTA_FASE_6}: ningún club publica xGA tardío; cobertura +PA no computable."
        glifo = GLIFO[NIVEL_NEUTRAL]
    elif riesgo_global:
        diagnostico = (
            "FRAGILIDAD DE CIERRE en al menos un club; +PA bajo vigilancia "
            f"[{NODO_PAGO_ANTICIPADO}]."
        )
        glifo = GLIFO[NIVEL_ROJO]
    else:
        diagnostico = "CIERRE SÓLIDO en ambos clubes; sin señal de quiebre del +PA."
        glifo = GLIFO[NIVEL_VERDE]
    alerta = {
        "umbral": UMBRAL_XGA_CIERRE,
        "local": alerta_local,
        "visita": alerta_visita,
        "riesgo_global": None if riesgo_global is None else bool(riesgo_global),
        "diagnostico": diagnostico,
        "glifo": glifo,
        "cobertura_pa": (
            "NO COMPUTABLE — SIN EVIDENCIA"
            if riesgo_global is None
            else (
                f"DOBLE COBRO (+PA) HABILITADO CON VIGILANCIA [{NODO_PAGO_ANTICIPADO}]"
                if riesgo_global
                else "COBERTURA +PA SIN ALERTA"
            )
        ),
    }
    return celdas, alerta


def _delta_corners(dimension_5: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """ΔCórners = Córners_H − Córners_A (`[LN-QBE-112]` §1); `None` sin cobertura doble."""
    celda = dimension_5.get("V20") or {}
    local, visita = celda.get("local_num"), celda.get("visita_num")
    if local is None or visita is None:
        return {
            "local": None, "visita": None, "delta": None,
            "estado": ESTADO_SIN_EVIDENCIA,
            "nota": f"{NOTA_FASE_6}: ΔCórners no computable sin feed de córners en ambos clubes.",
        }
    return {
        "local": local, "visita": visita, "delta": round(local - visita, 4),
        "estado": ESTADO_EVALUADO,
        "nota": "ΔCórners = Córners_H − Córners_A del corte N−1.",
    }


def _indice_riesgo_roja(dimension_6: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Alerta de asimetría numérica: rojas/PJ > 0.25 en cualquiera de los dos clubes."""
    celda = dimension_6.get("V24") or {}
    local, visita = celda.get("local_num"), celda.get("visita_num")
    if local is None or visita is None:
        return {
            "umbral": UMBRAL_INDICE_ROJA, "local": None, "visita": None, "alerta": None,
            "diagnostico": f"{NOTA_FASE_6}: sin rojas por partido no se audita la asimetría numérica.",
        }
    alerta = local > UMBRAL_INDICE_ROJA or visita > UMBRAL_INDICE_ROJA
    diagnostico = (
        "ALERTA DE ASIMETRÍA NUMÉRICA: al menos un club supera 0.25 rojas/partido."
        if alerta
        else "Disciplina contenida: ambos clubes por debajo de 0.25 rojas/partido."
    )
    return {
        "umbral": UMBRAL_INDICE_ROJA, "local": local, "visita": visita,
        "alerta": bool(alerta), "diagnostico": diagnostico,
    }

# ═════════════════════════════════════════════════════════════════════════════════════════════════
# SEMÁFOROS DE GOBERNANZA (presentación pura sobre el reporte, cero recálculo)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
_ETIQUETAS_SEMAFORO: Dict[str, str] = {
    "cobertura_granular": "COBERTURA GRANULAR",
    "muestra_corte": "MUESTRA CORTE N−1",
    "corpus_congelado": "CORPUS CONGELADO",
    "degradacion_fase_6": "DEGRADACIÓN FASE 6",
    "alerta_cierre_pa": "ALERTA CIERRE +PA",
    "disciplina_roja": "DISCIPLINA (ROJAS)",
}


def _semaforo(nivel: str, etiqueta: str, detalle: str) -> Dict[str, Any]:
    """Lectura homogénea `{nivel, glifo, etiqueta, detalle}`."""
    return {"nivel": nivel, "glifo": GLIFO.get(nivel, "·"), "etiqueta": etiqueta, "detalle": detalle}


def _semaforos(reporte: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Seis semáforos de gobernanza derivados del reporte ya construido."""
    total = int(reporte.get("celdas_totales") or TOTAL_VARIABLES)
    evaluadas = int(reporte.get("celdas_evaluadas") or 0)
    degradadas = max(0, total - evaluadas)

    if evaluadas >= total:
        cobertura = _semaforo(
            NIVEL_VERDE, f"Cobertura granular {evaluadas}/{total}",
            "Las 15 micro-dinámicas publican magnitud real en ambos clubes.",
        )
    elif evaluadas == 0:
        cobertura = _semaforo(
            NIVEL_NEUTRAL, f"Cobertura granular 0/{total}",
            "Ningún feed granular presente: las 15 celdas degradan sin imputación.",
        )
    else:
        cobertura = _semaforo(
            NIVEL_AMARILLO, f"Cobertura granular {evaluadas}/{total}",
            f"{degradadas} celdas degradadas a {NOTA_FASE_6}. Cobertura parcial declarada.",
        )

    corte = reporte.get("corte_n_1") or {}
    pj_local = int((corte.get("local") or {}).get("pj") or 0)
    pj_visita = int((corte.get("visita") or {}).get("pj") or 0)
    minimo = min(pj_local, pj_visita)
    if minimo >= 5:
        muestra = _semaforo(
            NIVEL_VERDE, f"Muestra N−1 {pj_local}/{pj_visita} PJ",
            "Ambos cortes superan el mínimo operativo de 5 partidos terminales.",
        )
    elif minimo > 0:
        muestra = _semaforo(
            NIVEL_AMARILLO, f"Muestra N−1 {pj_local}/{pj_visita} PJ",
            "Al menos un corte tiene menos de 5 partidos: lectura descriptiva, no inferencial.",
        )
    else:
        muestra = _semaforo(
            NIVEL_NEUTRAL, f"Muestra N−1 {pj_local}/{pj_visita} PJ",
            "Sin partidos terminales previos: no hay corte N−1 que agregar.",
        )

    cache_opta = reporte.get("cache_opta") or {}
    cache_tele = reporte.get("cache_telemetria") or {}
    if cache_opta.get("disponible") and cache_tele.get("disponible"):
        corpus = _semaforo(
            NIVEL_VERDE, "Corpus congelado íntegro",
            f"Opta {cache_opta.get('partidos')} partidos · telemetría {cache_tele.get('partidos')} partidos.",
        )
    else:
        ausentes = [
            etiqueta for etiqueta, meta in (
                ("Opta", cache_opta), ("telemetría", cache_tele)
            ) if not meta.get("disponible")
        ]
        corpus = _semaforo(
            NIVEL_AMARILLO, "Corpus congelado incompleto",
            f"Artefactos ausentes o ilegibles: {', '.join(ausentes) or 'ninguno'}.",
        )

    if degradadas == 0:
        degradacion = _semaforo(
            NIVEL_VERDE, "Degradación 0/15",
            "Ninguna celda requiere el axioma de degradación fiduciaria.",
        )
    elif evaluadas == 0:
        degradacion = _semaforo(
            NIVEL_NEUTRAL, f"Degradación {degradadas}/15",
            f"Todas las celdas declaran {NOTA_FASE_6}: cero invención de cifras.",
        )
    else:
        degradacion = _semaforo(
            NIVEL_AMARILLO, f"Degradación {degradadas}/15",
            f"{evaluadas} celdas con evidencia real; el resto declara {NOTA_FASE_6}.",
        )

    alerta_cierre = reporte.get("alerta_cierre") or {}
    riesgo = alerta_cierre.get("riesgo_global")
    if riesgo is True:
        cierre = _semaforo(
            NIVEL_ROJO, "Fragilidad de cierre +PA",
            f"xGA 80'-90'+ ≥ {UMBRAL_XGA_CIERRE:.2f} en al menos un club: vigilancia "
            f"[{NODO_PAGO_ANTICIPADO}].",
        )
    elif riesgo is False:
        cierre = _semaforo(
            NIVEL_VERDE, "Cierre sólido",
            f"Ambos clubes por debajo de {UMBRAL_XGA_CIERRE:.2f} xGA en 80'-90'+.",
        )
    else:
        cierre = _semaforo(
            NIVEL_NEUTRAL, "Cierre no computable",
            f"{NOTA_FASE_6}: sin xGA tardío no se emite juicio sobre el Pago Anticipado.",
        )

    indice_roja = reporte.get("indice_riesgo_roja") or {}
    alerta_roja = indice_roja.get("alerta")
    if alerta_roja is True:
        disciplina = _semaforo(
            NIVEL_ROJO, "Asimetría numérica",
            f"Rojas/partido > {UMBRAL_INDICE_ROJA:.2f} en al menos un club.",
        )
    elif alerta_roja is False:
        disciplina = _semaforo(
            NIVEL_VERDE, "Disciplina contenida",
            f"Ambos clubes por debajo de {UMBRAL_INDICE_ROJA:.2f} rojas/partido.",
        )
    else:
        disciplina = _semaforo(
            NIVEL_NEUTRAL, "Disciplina no computable",
            f"{NOTA_FASE_6}: sin rojas granulares no hay índice de expulsión.",
        )

    return {
        "cobertura_granular": cobertura,
        "muestra_corte": muestra,
        "corpus_congelado": corpus,
        "degradacion_fase_6": degradacion,
        "alerta_cierre_pa": cierre,
        "disciplina_roja": disciplina,
    }

# ═════════════════════════════════════════════════════════════════════════════════════════════════
# ORQUESTADOR DE PARTIDO (`MicroDinamicasResult` como dict serializable)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def _dimensiones_degradadas() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Las 5 dimensiones con las 15 celdas en `SIN EVIDENCIA` (contrato mínimo del reporte)."""
    return {
        clave: {
            identificador: _celda(identificador, None, None)
            for identificador in identificadores
        }
        for clave, identificadores in _DIMENSIONES.items()
    }


def _resumen_corte(partidos: Sequence[Dict[str, Any]], slug: Optional[str]) -> Dict[str, Any]:
    """Resumen del corte N−1 de un club (sin recalcular λ ni tocar la persistencia)."""
    return {
        "slug": slug,
        "pj": len(partidos),
        "gf": sum(partido["goles_favor"] for partido in partidos),
        "gc": sum(partido["goles_contra"] for partido in partidos),
        "jornadas": [partido["jornada"] for partido in partidos],
        "partidos": [partido["match_id"] for partido in partidos],
    }


def _reporte_no_encontrado(
    match_id: str,
    temporada: str,
    meta_opta: Dict[str, Any],
    meta_telemetria: Dict[str, Any],
    motivo: Optional[str] = None,
) -> Dict[str, Any]:
    """Reporte de degradación total cuando el fixture no puede resolverse (contrato completo)."""
    dimensiones = _dimensiones_degradadas()
    alerta_nula = evaluar_alerta_fragilidad_cierre(None)
    reporte: Dict[str, Any] = {
        "status": "NO_ENCONTRADO",
        "motivo": motivo or (
            f"El fixture '{match_id}' no existe en `matches` ni en `fixtures_snapshots`."
        ),
        "temporada": str(temporada),
        "match": {
            "match_id": str(match_id), "jornada": None, "estado": None, "marcador": None,
            "local": {"slug": None, "nombre": None}, "visita": {"slug": None, "nombre": None},
        },
        "regla_corte": REGLA_CORTE,
        "corte_n_1": {
            "local": _resumen_corte([], None), "visita": _resumen_corte([], None),
        },
        "cobertura": {
            "granular": {
                "local": {"pj": 0, "celdas_evaluadas": 0, "celdas_totales": TOTAL_VARIABLES},
                "visita": {"pj": 0, "celdas_evaluadas": 0, "celdas_totales": TOTAL_VARIABLES},
            },
            "telemetria": {
                "local": {"pj": 0, "cubiertos": 0, "publica_fouls": False, "publica_rojas": False},
                "visita": {"pj": 0, "cubiertos": 0, "publica_fouls": False, "publica_rojas": False},
            },
            "opta_xg": {"local": {"pj": 0, "cubiertos": 0}, "visita": {"pj": 0, "cubiertos": 0}},
        },
        "cache_opta": meta_opta,
        "cache_telemetria": meta_telemetria,
        **dimensiones,
        "ratios_cronometria": {"V33": {"local": {}, "visita": {}}, "V34": {"local": {}, "visita": {}}},
        "alerta_cierre": {
            "umbral": UMBRAL_XGA_CIERRE,
            "local": alerta_nula,
            "visita": dict(alerta_nula),
            "riesgo_global": None,
            "diagnostico": f"{NOTA_FASE_6}: fixture irresoluble; cierre +PA no computable.",
            "glifo": GLIFO[NIVEL_NEUTRAL],
            "cobertura_pa": "NO COMPUTABLE — SIN EVIDENCIA",
        },
        "delta_corners": _delta_corners(dimensiones["dimension_5_balon_parado"]),
        "indice_riesgo_roja": _indice_riesgo_roja(dimensiones["dimension_6_disciplina"]),
        "celdas_evaluadas": 0,
        "celdas_totales": TOTAL_VARIABLES,
        "escritura_bd": False,
        "llamadas_red": False,
        "nodos_gobernanza": list(NODOS_GOBERNANZA),
    }
    reporte["semaforos"] = _semaforos(reporte)
    return reporte

def ejecutar_sandbox_micro_dinamicas_partido(
    match_id: str, temporada: str = TEMPORADA_DEFAULT
) -> Dict[str, Any]:
    """Evalúa las 15 micro-dinámicas de un fixture en corte N−1 (sólo lectura, cero red)."""
    identificador = str(match_id)
    cache_opta, meta_opta = cargar_corpus(ruta_cache_opta(temporada), "Opta xG congelado")
    cache_telemetria, meta_telemetria = cargar_corpus(
        ruta_cache_telemetria(temporada), "Telemetría congelada"
    )

    gateway = PersistenceGateway()
    with gateway.read_session() as sesion:
        partido = sesion.get(Match, identificador)
        fixture, snapshot = _fixture_de_partido(sesion, identificador)
        if partido is None and not fixture:
            return _reporte_no_encontrado(identificador, temporada, meta_opta, meta_telemetria)

        slug_local = str(
            getattr(partido, "home_team_slug", None) or fixture.get("home_team_slug") or ""
        ).strip()
        slug_visita = str(
            getattr(partido, "away_team_slug", None) or fixture.get("away_team_slug") or ""
        ).strip()
        jornada = getattr(partido, "matchday_num", None)
        if jornada is None and snapshot is not None:
            jornada = getattr(snapshot, "matchday", None)
        if not slug_local or not slug_visita or jornada is None:
            return _reporte_no_encontrado(
                identificador, temporada, meta_opta, meta_telemetria,
                motivo="Fixture sin sede, slugs o jornada resolubles en la persistencia.",
            )
        jornada = int(jornada)
        partidos_local = _partidos_de_club(sesion, slug_local, jornada)
        partidos_visita = _partidos_de_club(sesion, slug_visita, jornada)
        telemetria = {
            "local": _cobertura_telemetria(
                sesion, [registro["match_id"] for registro in partidos_local], slug_local
            ),
            "visita": _cobertura_telemetria(
                sesion, [registro["match_id"] for registro in partidos_visita], slug_visita
            ),
        }

    dimension_5 = _construir_dimension_5(partidos_local, partidos_visita, cache_opta)
    dimension_6 = _construir_dimension_6(partidos_local, partidos_visita, cache_opta)
    dimension_9, ratios = _construir_dimension_9(partidos_local, partidos_visita, cache_opta)
    dimension_10 = _construir_dimension_10(partidos_local, partidos_visita, cache_opta)
    dimension_12, alerta_cierre = _construir_dimension_12(
        partidos_local, partidos_visita, cache_opta
    )
    dimensiones = {
        "dimension_5_balon_parado": dimension_5,
        "dimension_6_disciplina": dimension_6,
        "dimension_9_cronometria": dimension_9,
        "dimension_10_banca": dimension_10,
        "dimension_12_cierre": dimension_12,
    }

    celdas = [celda for dimension in dimensiones.values() for celda in dimension.values()]
    evaluadas = sum(1 for celda in celdas if celda["estado"] == ESTADO_EVALUADO)
    degradadas = len(celdas) - evaluadas
    if evaluadas == len(celdas):
        status = "EXITO"
        motivo = f"{evaluadas}/{TOTAL_VARIABLES} celdas con evidencia fáctica íntegra en ambos clubes."
    elif evaluadas == 0:
        status = "SIN_EVIDENCIA"
        motivo = (
            f"0/{TOTAL_VARIABLES} celdas con evidencia: el corpus sólo publica xG/xGA agregados; "
            "no existen feeds de balón parado, córners, penales, faltas por tercio, tarjetas, "
            "intervalos de gol, suplentes, alineaciones ni tramos 80'-90'+."
        )
    else:
        status = "PARCIAL"
        motivo = (
            f"{evaluadas}/{TOTAL_VARIABLES} celdas con evidencia; {degradadas} degradadas a "
            f"{NOTA_FASE_6}."
        )

    marcador = None
    if partido is not None and partido.score_home is not None and partido.score_away is not None:
        marcador = f"{partido.score_home}-{partido.score_away}"
    estado_partido = getattr(partido, "status", None) or fixture.get("estado")

    reporte: Dict[str, Any] = {
        "status": status,
        "motivo": motivo,
        "temporada": str(temporada),
        "match": {
            "match_id": identificador,
            "jornada": jornada,
            "estado": estado_partido,
            "marcador": marcador,
            "local": {
                "slug": slug_local,
                "nombre": fixture.get("local") or slug_local,
            },
            "visita": {
                "slug": slug_visita,
                "nombre": fixture.get("visitante") or slug_visita,
            },
        },
        "regla_corte": REGLA_CORTE,
        "corte_n_1": {
            "local": _resumen_corte(partidos_local, slug_local),
            "visita": _resumen_corte(partidos_visita, slug_visita),
        },
        "cobertura": {
            "granular": {
                "local": {
                    "pj": len(partidos_local),
                    "celdas_evaluadas": evaluadas,
                    "celdas_totales": TOTAL_VARIABLES,
                },
                "visita": {
                    "pj": len(partidos_visita),
                    "celdas_evaluadas": evaluadas,
                    "celdas_totales": TOTAL_VARIABLES,
                },
            },
            "telemetria": telemetria,
            "opta_xg": {
                "local": _cobertura_xg_base(partidos_local, cache_opta),
                "visita": _cobertura_xg_base(partidos_visita, cache_opta),
            },
        },
        "cache_opta": meta_opta,
        "cache_telemetria": meta_telemetria,
        **dimensiones,
        "ratios_cronometria": ratios,
        "alerta_cierre": alerta_cierre,
        "delta_corners": _delta_corners(dimension_5),
        "indice_riesgo_roja": _indice_riesgo_roja(dimension_6),
        "celdas_evaluadas": evaluadas,
        "celdas_totales": TOTAL_VARIABLES,
        "escritura_bd": False,
        "llamadas_red": False,
        "nodos_gobernanza": list(NODOS_GOBERNANZA),
    }
    reporte["semaforos"] = _semaforos(reporte)
    return reporte


def ejecutar_sandbox_micro_dinamicas_jornada(
    jornada: int, temporada: str = TEMPORADA_DEFAULT
) -> List[Dict[str, Any]]:
    """Ejecuta el sandbox para cada partido de la jornada (orden por `match_id`)."""
    gateway = PersistenceGateway()
    with gateway.read_session() as sesion:
        identificadores = sesion.execute(
            select(Match.id)
            .where(Match.matchday_num == int(jornada))
            .order_by(Match.id)
        ).scalars().all()
        if not identificadores:
            snapshot = sesion.execute(
                select(FixtureSnapshot)
                .where(FixtureSnapshot.matchday == int(jornada))
                .order_by(FixtureSnapshot.updated_at.desc(), FixtureSnapshot.id.desc())
            ).scalars().first()
            if snapshot is not None:
                identificadores = [
                    str(item.get("id_partido"))
                    for item in (snapshot.matches_json or [])
                    if isinstance(item, dict) and item.get("id_partido")
                ]
    return [
        ejecutar_sandbox_micro_dinamicas_partido(str(identificador), temporada)
        for identificador in identificadores
    ]

# ═════════════════════════════════════════════════════════════════════════════════════════════════
# [ARCH-1.4.51] TABLERO ASCII DE CONSOLA (presentación pura, cero cálculo)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def _ancho_visible(texto: str) -> int:
    """Ancho de desplazamiento en terminal (glifos anchos y emoji cuentan 2 columnas)."""
    ancho = 0
    for caracter in texto:
        codigo = ord(caracter)
        if codigo in (0xFE0F, 0x200D) or 0x0300 <= codigo <= 0x036F:
            continue
        if (
            0x1F000 <= codigo <= 0x1FAFF
            or 0x2600 <= codigo <= 0x27BF
            or 0x2B00 <= codigo <= 0x2BFF
            or 0x2E80 <= codigo <= 0xA4CF
        ):
            ancho += 2
        else:
            ancho += 1
    return ancho


def _pad(texto: str, ancho: int) -> str:
    """Relleno derecho por ancho VISIBLE (no por longitud de cadena)."""
    relleno = max(0, ancho - _ancho_visible(texto))
    return texto + (" " * relleno)


def _recortar(texto: str, ancho: int) -> str:
    """Recorta a ancho visible (red de seguridad para no romper el borde de la caja)."""
    if _ancho_visible(texto) <= ancho:
        return texto
    salida = ""
    for caracter in texto:
        if _ancho_visible(salida + caracter) > ancho - 1:
            break
        salida += caracter
    return salida + "…"


def _caja(titulo: str, filas: Sequence[str]) -> None:
    """Caja ASCII/Unicode de ancho fijo (94 columnas) con título embebido."""
    interior = ANCHO_TABLERO - 2
    encabezado = f"─ {titulo} "
    print("┌" + encabezado + ("─" * max(0, interior - _ancho_visible(encabezado))) + "┐")
    for fila in filas:
        print("│ " + _pad(_recortar(fila, interior - 2), interior - 2) + " │")
    print("└" + ("─" * interior) + "┘")


def _linea(etiqueta: str, texto: str) -> str:
    """Fila etiqueta/valor del bloque de contexto (etiqueta alineada en 10 columnas)."""
    return f"{_pad(etiqueta, 10)}{texto}"


def _texto_magnitud(valor: Any, ancho: int) -> str:
    """Celda de tabla: numérico a 4 decimales, `None` como `—`."""
    if valor is None:
        return "—".rjust(ancho)
    if isinstance(valor, str):
        return valor.rjust(ancho)
    return f"{float(valor):.4f}".rjust(ancho)


def _glifo_celda(celda: Dict[str, Any]) -> str:
    """Glifo de estado de una celda Vxx (🟢 evaluada / ⚪ sin evidencia)."""
    return GLIFO.get(str(celda.get("estado")), "·")


def _fila_celda(celda: Dict[str, Any]) -> str:
    """Fila de tabla: ID · variable · unidad · LOCAL · VISITA · estado."""
    return (
        f"{_pad(str(celda['id']), 5)}"
        f"{_pad(str(celda['variable'])[:37], 38)}"
        f"{_pad(str(celda['unidad'])[:11], 11)}"
        f"{_texto_magnitud(celda.get('local'), 9)}"
        f"{_texto_magnitud(celda.get('visita'), 9)}"
        f"  {_glifo_celda(celda)} {celda['estado']}"
    )


def _encabezado_dimension(etiqueta: str) -> str:
    """Cabecera de tabla de dimensión, alineada con `_fila_celda`."""
    return (
        f"{_pad(etiqueta, 5)}{_pad('VARIABLE', 38)}{_pad('UNIDAD', 11)}"
        f"{'LOCAL'.rjust(9)}{'VISITA'.rjust(9)}  ESTADO"
    )


def _envolver(texto: str, ancho: int = ANCHO_TABLERO - 14) -> List[str]:
    """Envuelve texto largo respetando palabras (sin dependencias externas)."""
    palabras = str(texto).split()
    lineas: List[str] = []
    actual = ""
    for palabra in palabras:
        candidata = f"{actual} {palabra}".strip()
        if _ancho_visible(candidata) <= ancho:
            actual = candidata
            continue
        if actual:
            lineas.append(actual)
        actual = palabra
    if actual:
        lineas.append(actual)
    return lineas or [""]

# ── Bloques temáticos del tablero ──────────────────────────────────────────────────────────────
def _bloque_contexto(reporte: Dict[str, Any]) -> None:
    """Contexto del fixture, regla de corte y cobertura declarada."""
    partido = reporte.get("match") or {}
    local = partido.get("local") or {}
    visita = partido.get("visita") or {}
    corte = reporte.get("corte_n_1") or {}
    corte_local = corte.get("local") or {}
    corte_visita = corte.get("visita") or {}
    cache_opta = reporte.get("cache_opta") or {}
    cache_tele = reporte.get("cache_telemetria") or {}
    cobertura = reporte.get("cobertura") or {}
    opta_xg = cobertura.get("opta_xg") or {}
    xg_local = opta_xg.get("local") or {}
    xg_visita = opta_xg.get("visita") or {}
    telemetria = cobertura.get("telemetria") or {}
    tele_local = telemetria.get("local") or {}
    tele_visita = telemetria.get("visita") or {}
    pj_local = corte_local.get("pj")
    pj_visita = corte_visita.get("pj")
    filas = [
        _linea("PARTIDO", f"{partido.get('match_id')}  ·  J{partido.get('jornada')}  ·  {partido.get('estado') or '—'}"),
        _linea("SEDE", f"{local.get('nombre')} vs {visita.get('nombre')}"),
        _linea("MARCADOR", partido.get("marcador") or "—"),
        *_envolver(_linea("CORTE", f"{REGLA_CORTE}  ·  N = {partido.get('jornada')}")),
        _linea("MUESTRA", (
            f"local {corte_local.get('pj')} PJ (GF {corte_local.get('gf')} / GC {corte_local.get('gc')})"
            f"  ·  visita {corte_visita.get('pj')} PJ (GF {corte_visita.get('gf')} / GC {corte_visita.get('gc')})"
        )),
        *_envolver(_linea("CORPUS", (
            f"Opta {cache_opta.get('partidos', 0)} partidos "
            f"({'OK' if cache_opta.get('disponible') else 'AUSENTE'})"
            f"  ·  telemetría {cache_tele.get('partidos', 0)} "
            f"({'OK' if cache_tele.get('disponible') else 'AUSENTE'})"
        ))),
        *_envolver(_linea("COBERTURA", (
            f"granular {reporte.get('celdas_evaluadas')}/{reporte.get('celdas_totales')} celdas"
            f"  ·  xG base {xg_local.get('cubiertos', 0)}/{xg_local.get('pj', 0)}"
            f" + {xg_visita.get('cubiertos', 0)}/{xg_visita.get('pj', 0)}"
            f"  ·  telemetría {tele_local.get('cubiertos', 0)}/{pj_local}"
            f" + {tele_visita.get('cubiertos', 0)}/{pj_visita}"
        ))),
        _linea("ESTADO", f"{reporte.get('status')}"),
    ]
    filas.extend(_envolver(f"MOTIVO: {reporte.get('motivo')}"))
    _caja(f"[CONTEXTO] {partido.get('match_id')} · N−1 · SÓLO LECTURA", filas)


def _bloque_dimension(reporte: Dict[str, Any], clave: str, titulo: str) -> None:
    """Caja de una dimensión completa con pie de cobertura declarada."""
    dimension = reporte.get(clave) or {}
    filas: List[str] = [_encabezado_dimension("ID"), HORIZONTE]
    evaluadas = 0
    for identificador in sorted(dimension.keys()):
        celda = dimension[identificador]
        if celda["estado"] == ESTADO_EVALUADO:
            evaluadas += 1
        filas.append(_fila_celda(celda))
    filas.append(HORIZONTE)
    filas.append(
        f"COBERTURA: {evaluadas}/{len(dimension)} variables con evidencia fáctica · "
        f"degradación declarada sin imputación."
    )
    _caja(titulo, filas)


def _bloque_cronometria(reporte: Dict[str, Any]) -> None:
    """Dimensión 9 con el detalle numérico de los ratios 1T/2T."""
    dimension = reporte.get("dimension_9_cronometria") or {}
    filas: List[str] = [_encabezado_dimension("ID"), HORIZONTE]
    evaluadas = sum(
        1 for celda in dimension.values() if celda["estado"] == ESTADO_EVALUADO
    )
    for identificador in sorted(dimension.keys()):
        filas.append(_fila_celda(dimension[identificador]))
    filas.append(HORIZONTE)
    for clave in ("V33", "V34"):
        detalle = (reporte.get("ratios_cronometria") or {}).get(clave) or {}
        for lado in ("local", "visita"):
            datos = detalle.get(lado) or {}
            claves_temporales = sorted(
                k for k in datos if k not in ("pj", "cubiertos", "faltantes", "ratio")
            )
            pares = "  ".join(
                f"{k}={_texto_magnitud(datos.get(k), 8).strip()}" for k in claves_temporales
            )
            filas.append(
                f"{clave} {lado.upper():<6} {pares}  ratio={_texto_magnitud(datos.get('ratio'), 8)}"
                f"  cobertura={datos.get('cubiertos', 0)}/{datos.get('pj', 0)}"
            )
    filas.append(
        f"COBERTURA: {evaluadas}/{len(dimension)} variables con evidencia fáctica · "
        "ratio neutro 1.0 y clamp [0.1, 10.0]."
    )
    _caja("[D9] 𝒯_Time · CRONOMETRÍA Y RATIOS 1T/2T (V33-V36)", filas)


def _bloque_alertas(reporte: Dict[str, Any]) -> None:
    """ΔCórners, riesgo de expulsión y fragilidad de cierre (+PA)."""
    delta = reporte.get("delta_corners") or {}
    roja = reporte.get("indice_riesgo_roja") or {}
    alerta = reporte.get("alerta_cierre") or {}
    filas = [
        f"ΔCÓRNERS  local {_texto_magnitud(delta.get('local'), 8)}  ·  "
        f"visita {_texto_magnitud(delta.get('visita'), 8)}  ·  "
        f"Δ {_texto_magnitud(delta.get('delta'), 9)}  ·  {delta.get('estado')}",
        f"ROJAS     umbral {UMBRAL_INDICE_ROJA:.2f}  ·  "
        f"local {_texto_magnitud(roja.get('local'), 8)}  ·  "
        f"visita {_texto_magnitud(roja.get('visita'), 8)}  ·  {roja.get('diagnostico')}",
        f"CIERRE    umbral {UMBRAL_XGA_CIERRE:.2f}  ·  {alerta.get('glifo')} {alerta.get('diagnostico')}",
        f"+PA       {alerta.get('cobertura_pa')}",
    ]
    filas = [linea for fila in filas for linea in _envolver(fila)]
    _caja("[ALERTAS] ΔCÓRNERS · RIESGO DE ROJA · FRAGILIDAD DE CIERRE", filas)


def _bloque_semaforos(reporte: Dict[str, Any]) -> None:
    """Semáforos de gobernanza del reporte."""
    filas: List[str] = []
    for clave, semaforo in (reporte.get("semaforos") or {}).items():
        filas.append(
            f"{semaforo['glifo']} {_pad(_ETIQUETAS_SEMAFORO.get(clave, clave.upper()), 26)}"
            f"{_pad(semaforo['nivel'], 11)}{semaforo['etiqueta']}"
        )
        filas.extend("   " + linea for linea in _envolver(semaforo["detalle"], ANCHO_TABLERO - 18))
    _caja("[SEMÁFOROS] GOBERNANZA DE LA EVIDENCIA", filas)

# ── Impresión de tableros ─────────────────────────────────────────────────────────────────────
def imprimir_tablero_micro_dinamicas_consola(reporte: Dict[str, Any]) -> None:
    """Tablero completo de un partido (contexto + 5 dimensiones + alertas + semáforos)."""
    partido = reporte.get("match") or {}
    print()
    _caja(
        f"[LN-QBE-112] MICRO-DINÁMICAS & CIERRE · {partido.get('match_id')} · {reporte.get('status')}",
        [
            f"REGLA DE CORTE: {REGLA_CORTE}",
            *(_envolver(f"MOTIVO: {reporte.get('motivo')}")),
            f"Gobernanza: [LN-QBE-112] · [ARCH-1.4.51]",
            f"escritura_bd={reporte.get('escritura_bd')} · llamadas_red={reporte.get('llamadas_red')} · temporada={reporte.get('temporada')}",
        ],
    )
    _bloque_contexto(reporte)
    _bloque_dimension(
        reporte, "dimension_5_balon_parado",
        "[D5] 𝒯_Spc · BALÓN PARADO Y PENALES (V18-V21)",
    )
    _bloque_dimension(
        reporte, "dimension_6_disciplina",
        "[D6] 𝒯_Dsc · FRICCIÓN DISCIPLINARIA (V22-V24)",
    )
    _bloque_cronometria(reporte)
    _bloque_dimension(
        reporte, "dimension_10_banca",
        "[D10] 𝒯_Sub · BANCA Y ROTACIÓN DEL XI (V37-V38)",
    )
    _bloque_dimension(
        reporte, "dimension_12_cierre",
        "[D12] 𝒯_Cls · CIERRE TARDÍO (V43-V44)",
    )
    _bloque_alertas(reporte)
    _bloque_semaforos(reporte)
    _caja(
        "[CIERRE] AXIOMAS DE LA SESIÓN",
        [
            "Sólo lectura: read_session() + json.load; cero escritura en la 3NF.",
            "Futuro-ceguera: el fixture evaluado nunca alimenta su propio corte.",
            "Cobertura íntegra: una ausencia degrada la celda completa a None.",
            "Cero defaults como evidencia: 0 y 50.0 son centinelas, no mediciones.",
            "Sin señal a λ: estas 15 variables no se reinyectan al motor sellado.",
        ],
    )


def imprimir_tablero_jornada(jornada: int, reportes: Sequence[Dict[str, Any]]) -> None:
    """Tablero-resumen de la jornada: celdas evaluadas por dimensión y estado global."""
    filas: List[str] = [
        f"{_pad('MATCH ID', 14)}{_pad('LOCAL', 17)}{_pad('VISITA', 17)}"
        f"{'D5'.rjust(4)}{'D6'.rjust(4)}{'D9'.rjust(4)}{'D10'.rjust(5)}{'D12'.rjust(5)}  ESTADO",
        HORIZONTE,
    ]
    totales = [0] * len(_DIMENSIONES)
    for reporte in reportes:
        partido = reporte.get("match") or {}
        local = (partido.get("local") or {}).get("nombre") or "—"
        visita = (partido.get("visita") or {}).get("nombre") or "—"
        conteo = [
            sum(
                1 for celda in (reporte.get(clave) or {}).values()
                if celda["estado"] == ESTADO_EVALUADO
            )
            for clave in _DIMENSIONES
        ]
        totales = [acumulado + actual for acumulado, actual in zip(totales, conteo)]
        filas.append(
            f"{_pad(_recortar(str(partido.get('match_id') or '—'), 13), 14)}"
            f"{_pad(_recortar(str(local), 16), 17)}{_pad(_recortar(str(visita), 16), 17)}"
            f"{str(conteo[0]).rjust(4)}{str(conteo[1]).rjust(4)}{str(conteo[2]).rjust(4)}"
            f"{str(conteo[3]).rjust(5)}{str(conteo[4]).rjust(5)}  {reporte.get('status')}"
        )
    filas.append(HORIZONTE)
    sin_evidencia = sum(
        1 for reporte in reportes if reporte.get("status") == "SIN_EVIDENCIA"
    )
    filas.append(
        f"{_pad('TOTAL JORNADA', 48)}"
        f"{str(totales[0]).rjust(4)}{str(totales[1]).rjust(4)}{str(totales[2]).rjust(4)}"
        f"{str(totales[3]).rjust(5)}{str(totales[4]).rjust(5)}  "
        f"{sin_evidencia}/{len(reportes)} SIN EVIDENCIA"
    )
    _caja(
        f"[J{jornada}] MICRO-DINÁMICAS · {len(reportes)} PARTIDOS · CELDAS EVALUADAS POR DIMENSIÓN",
        filas,
    )
    print(
        "   D5 = 𝒯_Spc (4) · D6 = 𝒯_Dsc (3) · D9 = 𝒯_Time (4) · "
        "D10 = 𝒯_Sub (2) · D12 = 𝒯_Cls (2)  ·  corte N−1 futuro-ciego"
    )

# ═════════════════════════════════════════════════════════════════════════════════════════════════
# CLI (`[ARCH-1.4.51]`: --partido | --jornada | --temporada | --json)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def _construir_parser() -> argparse.ArgumentParser:
    """Parser CLI del laboratorio (operaciones mutuamente excluyentes)."""
    parser = argparse.ArgumentParser(
        prog="sandbox_micro_dinamicas_pipeline",
        description=(
            "[LN-QBE-112] Laboratorio de micro-dinámicas: D5 balón parado, D6 disciplina, "
            "D9 cronometría, D10 banca y D12 cierre. Sólo lectura."
        ),
    )
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument(
        "--partido", metavar="MATCH_ID",
        help="Evalúa un fixture (p. ej. LIGAMX-J11-07).",
    )
    grupo.add_argument(
        "--jornada", type=int, metavar="N",
        help="Evalúa todos los partidos de la jornada N.",
    )
    parser.add_argument(
        "--temporada", default=TEMPORADA_DEFAULT,
        help=f"Temporada del corpus congelado (default: {TEMPORADA_DEFAULT}).",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emite el reporte estructurado JSON (sin tablero ASCII).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada CLI. `0` si el reporte es honesto (EXITO/PARCIAL/SIN_EVIDENCIA)."""
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    argumentos = _construir_parser().parse_args(argv)

    if argumentos.partido:
        reporte = ejecutar_sandbox_micro_dinamicas_partido(
            argumentos.partido, argumentos.temporada
        )
        if argumentos.json:
            print(json.dumps(reporte, ensure_ascii=False, indent=2, default=str))
        else:
            imprimir_tablero_micro_dinamicas_consola(reporte)
        return 0 if reporte.get("status") in ("EXITO", "PARCIAL", "SIN_EVIDENCIA") else 1

    reportes = ejecutar_sandbox_micro_dinamicas_jornada(
        argumentos.jornada, argumentos.temporada
    )
    if argumentos.json:
        print(json.dumps(reportes, ensure_ascii=False, indent=2, default=str))
    else:
        imprimir_tablero_jornada(argumentos.jornada, reportes)
    if not reportes:
        print(f"⚠️  Jornada {argumentos.jornada} sin partidos en la persistencia.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
