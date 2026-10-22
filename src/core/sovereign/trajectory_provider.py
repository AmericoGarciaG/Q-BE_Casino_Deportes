# -*- coding: utf-8 -*-
"""
🧭 Q-BE SOVEREIGN · PROVEEDOR CANÓNICO DE TRAYECTORIA & MOMENTO (Fase 1 · Integración Maestra)
[LN-QBE-117] · [ARCH-1.4.55] · Migración VERBATIM de `[LN-QBE-110]` (sandbox de laboratorio).
Régimen: `[HÍBRIDO DUAL-TRACK]`

* `[DIRGEN-STRICT]`: la pendiente OLS de la ventana móvil (`m = Σ(t−t̄)(y_t−ȳ)/Σ(t−t̄)²`, con
  denominador exacto `10.0` para n = 5 y `t = 1..5`) y el diagnóstico ΔxPTS = PTS − xPTS con cota
  `±3.0` se transcriben sin una sola coma de diferencia del plano sellado.
* `[DBBD-FUNGIBLE]`: composición del bloque, celdas `V31`/`V32` (catálogo `[LN-QBE-122]`) con sus
  auxiliares sin código (`AUX_M_XG`, `AUX_M_XGA`) y notas de cobertura.

Contrato público:
  * `obtener_metricas_trayectoria(sesion, match_id, ...)` → bloque `trayectoria` del paquete
    `insumos_factivados` con `V31` (forma 5P), `AUX_M_XG` (pendiente xG), `AUX_M_XGA` (pendiente
    xGA) y `V32` (ΔxPTS).
  * `calcular_pendiente_lineal_5p(serie)` / `evaluar_diagnostico_xpts(pts, xpts)` → aritmética pura.
  * `cargar_corpus_opta(temporada, ...)` → lectura de sólo lectura del corpus xG/xGA congelado
    (compartida con `attack_defense_core`; una sola implementación, cero duplicación).

Fuentes de evidencia (todas de sólo lectura, vía el adaptador `src/core/sovereign_reads.py`; este
paquete puro jamás importa `sqlalchemy` ni `src.storage`, `[ARCH-1.4.26]`):
  1. Bóveda 3NF (`matches`) vía la capa compartida de `context_provider` (corte futuro-ciego N−1).
  2. `standings_snapshots` para PTS y xPTS con `matchday ≤ N−1` (nunca la tabla viva).
  3. Corpus Opta congelado `data/cache_optaxg_liga_mx_{temporada}.json` para las series xG/xGA.
     `match_telemetry.xg` / `xga` están vacíos en la bóveda viva: no se imputan.

Axioma de degradación ([LN-QBE-117].P.4): con menos de `VENTANA_TRAYECTORIA = 5` partidos
terminales, o con una sola ausencia de xG/xGA en la ventana, `V31` y los dos auxiliares de
pendiente se declaran `SIN EVIDENCIA`. Jamás se rellena la ventana ni se extrapola una pendiente.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.core.sovereign.context_provider import (
    ESTADO_EXITO,
    ESTADO_PARCIAL,
    ESTADO_SIN_EVIDENCIA,
    TEMPORADA_DEFAULT,
    VENTANA_TRAYECTORIA,
    _r,
    identidad_coincide,
    leer_fixture_cartelera,
    partidos_terminales_de_club,
)
from src.core.sovereign.factor_attribution import nombre_de_celda
from src.core.sovereign_reads import leer_snapshots_posiciones

__all__ = [
    "calcular_pendiente_lineal_5p",
    "evaluar_diagnostico_xpts",
    "ruta_corpus_opta",
    "cargar_corpus_opta",
    "registro_opta",
    "obtener_metricas_trayectoria",
]

# ── Nodos de gobierno ─────────────────────────────────────────────────────────────────────────
NODOS_GOBIERNO: Tuple[str, ...] = ("LN-QBE-117", "ARCH-1.4.55", "LN-QBE-110", "ARCH-1.4.49")

ESTADO_EVALUADO = "EVALUADO"
DENOMINADOR_PENDIENTE_5P = 10.0   # [LN-QBE-110] Σ(t − 3)² con t = 1..5
UMBRAL_XPTS = 3.0                 # [LN-QBE-110] cota de sobre/sub-rendimiento
TOLERANCIA_PENDIENTE = 1e-12      # frontera numérica de la tendencia estable

NIVEL_VERDE = "VERDE"
NIVEL_AMARILLO = "AMARILLO"
NIVEL_ROJO = "ROJO"
NIVEL_NEUTRAL = "NEUTRAL"
GLIFO: Dict[str, str] = {
    NIVEL_VERDE: "🟢",
    NIVEL_AMARILLO: "🟡",
    NIVEL_ROJO: "🔴",
    NIVEL_NEUTRAL: "⚪",
    ESTADO_EVALUADO: "🟢",
    ESTADO_SIN_EVIDENCIA: "⚪",
    ESTADO_EXITO: "🟢",
    ESTADO_PARCIAL: "🟡",
}

RUTA_CORPUS_OPTA_PLANTILLA = os.path.join("data", "cache_optaxg_liga_mx_{temporada}.json")
REGLA_CORTE = "matchday_num < N ∧ estado ∈ {FINALIZADO, FINISHED} (futuro-ceguera N−1)"


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [LN-QBE-110] ARITMÉTICA PURA (sin estado, sin I/O — auditable por The Shield en aislamiento)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def calcular_pendiente_lineal_5p(serie_valores: Sequence[float]) -> float:
    """Pendiente de mínimos cuadrados sobre la ventana móvil de 5 partidos.

    Definición sellada [LN-QBE-110]:
        m = Σ(t − t̄)(y_t − ȳ) / Σ(t − t̄)²

    Para n = 5 y t = 1..5 el denominador es exactamente 10. Si la serie publica menos de
    5 puntos se calcula sobre los disponibles (misma fórmula exacta, t = 1..n); con n < 2
    no existe pendiente y se retorna 0.0 (sin evidencia, jamás una cifra inventada).
    """
    valores: List[float] = []
    for valor in serie_valores:
        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            valores.append(float(valor))
    if len(valores) > VENTANA_TRAYECTORIA:
        valores = valores[-VENTANA_TRAYECTORIA:]
    n = len(valores)
    if n < 2:
        return 0.0
    t_barra = (n + 1) / 2.0
    y_barra = sum(valores) / n
    numerador = sum(
        (t - t_barra) * (y - y_barra) for t, y in enumerate(valores, start=1)
    )
    denominador = sum((t - t_barra) ** 2 for t in range(1, n + 1))
    if denominador <= 0:
        return 0.0
    return numerador / denominador


def evaluar_diagnostico_xpts(puntos_reales: float, xpts: float) -> Dict[str, Any]:
    """Diagnóstico de varianza ΔxPTS = PTS − xPTS conforme a [LN-QBE-110].

    Δ ≥ +3.0  ⇒ SOBRERRENDIMIENTO (alerta de regresión a la baja)
    Δ ≤ −3.0  ⇒ SUBRRENDIMIENTO   (alerta de rebote al alza)
    |Δ| < 3.0 ⇒ NEUTRAL / ALINEADO
    """
    delta = float(puntos_reales) - float(xpts)
    if delta >= UMBRAL_XPTS:
        diagnostico = "SOBRERRENDIMIENTO"
        alerta = (
            "Regresión a la baja inminente: los puntos superan el nivel de juego; "
            "la cosecha se sostiene en varianza favorable, no en calidad estructural."
        )
        nivel = NIVEL_AMARILLO
    elif delta <= -UMBRAL_XPTS:
        diagnostico = "SUBRRENDIMIENTO"
        alerta = (
            "Rebote al alza inminente: el equipo juega para más de lo que suma; "
            "los puntos perdidos son varianza adversa, no deterioro estructural."
        )
        nivel = NIVEL_AMARILLO
    else:
        diagnostico = "NEUTRAL / ALINEADO"
        alerta = (
            "Sin alerta: los puntos reales están alineados con los puntos esperados."
        )
        nivel = NIVEL_VERDE
    return {
        "puntos_reales": round(float(puntos_reales), 4),
        "xpts": round(float(xpts), 4),
        "delta_xpts": round(delta, 6),
        "diagnostico": diagnostico,
        "alerta": alerta,
        "umbral": UMBRAL_XPTS,
        "nivel": nivel,
        "glifo": GLIFO.get(nivel, "·"),
    }


def _direccion_xg(pendiente: Optional[float]) -> Dict[str, str]:
    """Lectura ofensiva de la pendiente xG [LN-QBE-110]."""
    if pendiente is None:
        return {"clave": "SIN_EVIDENCIA", "etiqueta": "Sin evidencia", "flecha": "·"}
    if pendiente > TOLERANCIA_PENDIENTE:
        return {"clave": "ACELERACION", "etiqueta": "Aceleración ofensiva", "flecha": "↗"}
    if pendiente < -TOLERANCIA_PENDIENTE:
        return {"clave": "DESACELERACION", "etiqueta": "Desaceleración ofensiva", "flecha": "↘"}
    return {"clave": "ESTABLE", "etiqueta": "Tendencia estable", "flecha": "➔"}


def _direccion_xga(pendiente: Optional[float]) -> Dict[str, str]:
    """Lectura defensiva de la pendiente xGA [LN-QBE-110]: bajar es mejorar."""
    if pendiente is None:
        return {"clave": "SIN_EVIDENCIA", "etiqueta": "Sin evidencia", "flecha": "·"}
    if pendiente < -TOLERANCIA_PENDIENTE:
        return {"clave": "CONSOLIDACION", "etiqueta": "Consolidación defensiva (mejora)", "flecha": "↘"}
    if pendiente > TOLERANCIA_PENDIENTE:
        return {"clave": "RESQUEBRAJAMIENTO", "etiqueta": "Resquebrajamiento defensivo", "flecha": "↗"}
    return {"clave": "ESTABLE", "etiqueta": "Defensa estable", "flecha": "➔"}


def _bando(
    valor_local: Optional[float], valor_visita: Optional[float], mayor_es_mejor: bool = True
) -> str:
    """Lectura comparada de dos métricas simétricas (empate técnico ⇒ EQUILIBRADO)."""
    if valor_local is None or valor_visita is None:
        return ESTADO_SIN_EVIDENCIA
    if abs(float(valor_local) - float(valor_visita)) <= 1e-9:
        return "EQUILIBRADO"
    if mayor_es_mejor:
        return "LOCAL" if float(valor_local) > float(valor_visita) else "VISITANTE"
    return "LOCAL" if float(valor_local) < float(valor_visita) else "VISITANTE"


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [LN-QBE-110] CORPUS OPTA CONGELADO Y SNAPSHOT DE POSICIONES (lectura hermética, cero red)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def ruta_corpus_opta(temporada: str, directorio_datos: Optional[str] = None) -> str:
    """Ruta absoluta del corpus Opta congelado para la temporada (sin tocar la red)."""
    plantilla = RUTA_CORPUS_OPTA_PLANTILLA.format(temporada=str(temporada))
    if directorio_datos:
        return os.path.join(os.path.abspath(directorio_datos), os.path.basename(plantilla))
    raiz = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    return os.path.join(raiz, plantilla)


def cargar_corpus_opta(
    temporada: str, directorio_datos: Optional[str] = None, ruta_corpus: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Carga el corpus Opta (xG/xGA por partido) sin red y sin escritura."""
    ruta = ruta_corpus or ruta_corpus_opta(temporada, directorio_datos)
    meta: Dict[str, Any] = {
        "disponible": False,
        "ruta": ruta,
        "generado_at": None,
        "fuente": None,
        "partidos_en_corpus": 0,
    }
    if not os.path.exists(ruta):
        return {}, meta
    try:
        with open(ruta, "r", encoding="utf-8") as manejador:
            crudo = json.load(manejador)
    except (OSError, ValueError):
        return {}, meta
    partidos = crudo.get("partidos") if isinstance(crudo, dict) else crudo
    if not isinstance(partidos, dict):
        return {}, meta
    meta.update(
        {
            "disponible": True,
            "generado_at": crudo.get("generado_at") if isinstance(crudo, dict) else None,
            "fuente": crudo.get("fuente") if isinstance(crudo, dict) else None,
            "partidos_en_corpus": len(partidos),
        }
    )
    return partidos, meta


def _a_float(valor: Any) -> Optional[float]:
    """Coerción numérica estricta (bool y texto no numérico ⇒ None)."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            return None
        try:
            return float(texto)
        except ValueError:
            return None
    return None


def registro_opta(
    partidos_corpus: Dict[str, Any], match_id: str, es_local: bool
) -> Tuple[Optional[float], Optional[float]]:
    """Serie (xG, xGA) de un club en un partido del corpus congelado (lado explícito)."""
    bloque = (
        partidos_corpus.get(str(match_id)) if isinstance(partidos_corpus, dict) else None
    )
    if not isinstance(bloque, dict):
        return None, None
    lado = bloque.get("home" if es_local else "away")
    if not isinstance(lado, dict):
        return None, None
    return _a_float(lado.get("xg")), _a_float(lado.get("xga"))


def _entradas_snapshot(snapshot: Optional[Dict[str, Any]], campo: str) -> List[Dict[str, Any]]:
    """Deserializa el JSON de un snapshot (listas directas o diccionarios envolventes)."""
    crudo = snapshot.get(campo) if isinstance(snapshot, dict) else None
    if crudo is None:
        return []
    if isinstance(crudo, str):
        try:
            crudo = json.loads(crudo)
        except (TypeError, ValueError):
            return []
    if isinstance(crudo, dict):
        for clave in ("partidos", "matches", "posiciones", "standings"):
            contenido = crudo.get(clave)
            if isinstance(contenido, list):
                return [entrada for entrada in contenido if isinstance(entrada, dict)]
        return []
    if isinstance(crudo, list):
        return [entrada for entrada in crudo if isinstance(entrada, dict)]
    return []


def _snapshot_corte(
    sesion: Any, jornada_corte: Optional[int], temporada: str
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Snapshot de posiciones más reciente con `matchday ≤ N−1` (corte futuro-ciego)."""
    corte = int(jornada_corte or 0)
    if corte < 1:
        return None, []
    # Adaptador soberano de lectura: la capa pura recibe diccionarios planos ([ARCH-1.4.26]).
    filas = leer_snapshots_posiciones(sesion, corte)
    respaldo: Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]] = (None, [])
    for snapshot in filas:
        entradas = _entradas_snapshot(snapshot, "positions_json")
        if not entradas:
            continue
        if str(snapshot.get("season") or "") == str(temporada):
            return snapshot, entradas
        if respaldo[0] is None:
            respaldo = (snapshot, entradas)
    return respaldo


def _entrada_posiciones(
    entradas: Sequence[Dict[str, Any]], slug: str
) -> Optional[Dict[str, Any]]:
    """Localiza la fila del club en el snapshot casando identidades normalizadas."""
    for fila in entradas:
        for clave in ("equipo", "short_name", "slug", "canonical_slug", "team_slug"):
            if clave in fila and identidad_coincide(fila.get(clave), slug):
                return fila
    return None


def _puntos_y_xpts(
    entrada: Optional[Dict[str, Any]],
) -> Tuple[Optional[float], Optional[float]]:
    """Extrae (PTS, xPTS) de la fila del club en el snapshot del corte."""
    if entrada is None:
        return None, None
    return _a_float(entrada.get("puntos")), _a_float(entrada.get("xpts"))


def _ventana_5p(
    sesion: Any,
    slug: str,
    jornada_corte: Optional[int],
    partidos_corpus: Dict[str, Any],
) -> Dict[str, Any]:
    """Ventana móvil de 5 partidos con sus series de xG/xGA (lookup en el corpus congelado)."""
    partidos = partidos_terminales_de_club(
        sesion, slug, jornada_corte, limite=VENTANA_TRAYECTORIA
    )
    detalle: List[Dict[str, Any]] = []
    for partido in partidos:
        xg, xga = registro_opta(partidos_corpus, partido["match_id"], partido["es_local"])
        detalle.append(
            {
                **partido,
                "lado_corpus": "home" if partido["es_local"] else "away",
                "xg": _r(xg, 4),
                "xga": _r(xga, 4),
            }
        )

    integro = bool(detalle) and all(
        partido["xg"] is not None and partido["xga"] is not None for partido in detalle
    )
    serie_xg = [partido["xg"] for partido in detalle]
    serie_xga = [partido["xga"] for partido in detalle]
    pendiente_xg = calcular_pendiente_lineal_5p(serie_xg) if integro else None
    pendiente_xga = calcular_pendiente_lineal_5p(serie_xga) if integro else None
    return {
        "slug": slug,
        "partidos": detalle,
        "serie_xg": serie_xg,
        "serie_xga": serie_xga,
        "muestra": len(detalle),
        "ventana_completa": len(detalle) == VENTANA_TRAYECTORIA,
        "integro": integro,
        "pendiente_xg": _r(pendiente_xg, 6),
        "pendiente_xga": _r(pendiente_xga, 6),
        "promedio_xg": (
            _r(sum(serie_xg) / len(serie_xg), 4) if integro and serie_xg else None
        ),
        "promedio_xga": (
            _r(sum(serie_xga) / len(serie_xga), 4) if integro and serie_xga else None
        ),
    }


def _forma_5p(partidos: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """V29 desde marcadores reales: puntos y racha de la ventana (máximo 15)."""
    puntos = 0
    for partido in partidos:
        if partido["resultado"] == "G":
            puntos += 3
        elif partido["resultado"] == "E":
            puntos += 1
    return {
        "puntos": puntos,
        "racha": "".join(partido["resultado"] for partido in partidos) or "—",
        "partidos": list(partidos),
        "muestra": len(partidos),
    }


def _sintesis_momento(
    v29: Dict[str, Any], v30: Dict[str, Any], v31: Dict[str, Any], v32: Dict[str, Any]
) -> Dict[str, Any]:
    """Cruce de las 4 variables: momento, pulso ofensivo, solidez y respaldo estructural."""
    delta_puntos = v29.get("delta_puntos")
    if delta_puntos is None:
        momento = ESTADO_SIN_EVIDENCIA
    elif delta_puntos > 0:
        momento = "LOCAL"
    elif delta_puntos < 0:
        momento = "VISITANTE"
    else:
        momento = "EQUILIBRADO"

    pulso = _bando(v30.get("pendiente_local"), v30.get("pendiente_visita"), True)
    solidez = _bando(v31.get("pendiente_local"), v31.get("pendiente_visita"), False)
    respaldo = _bando(v32.get("delta_xpts_local"), v32.get("delta_xpts_visita"), False)

    if ESTADO_SIN_EVIDENCIA in (momento, respaldo):
        divergencia = ESTADO_SIN_EVIDENCIA
    elif respaldo == "EQUILIBRADO":
        divergencia = "SIN SESGO ESTRUCTURAL"
    elif momento == respaldo:
        divergencia = "ALINEADO"
    else:
        divergencia = "DIVERGENTE"

    return {
        "momento_5p": momento,
        "pulso_ofensivo": pulso,
        "solidez_defensiva": solidez,
        "respaldo_estructural": respaldo,
        "divergencia": divergencia,
        "lectura": (
            f"Forma {momento}; pulso ofensivo {pulso}; solidez {solidez}; "
            f"respaldo estructural {respaldo}; veredicto {divergencia}."
        ),
        "nota": (
            "Un ΔxPTS bajo indica menos sobre-rendimiento (cosecha respaldada); "
            "un ΔxPTS alto delata puntos inflados por varianza favorable."
        ),
    }


def _semaforo(nivel: str, detalle: str) -> Dict[str, str]:
    return {"nivel": nivel, "glifo": GLIFO.get(nivel, "·"), "detalle": detalle}


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [LN-QBE-117] INSUMOS PLANOS DEL BLOQUE (claves heredadas, cero colisión con otros proveedores)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _insumos_trayectoria(
    v29: Dict[str, Any],
    v30: Dict[str, Any],
    v31: Dict[str, Any],
    v32: Dict[str, Any],
    meta_corpus: Dict[str, Any],
) -> Dict[str, Any]:
    """Claves planas que el paquete `insumos_factivados` expone en la raíz ([ARCH-1.4.55])."""
    return {
        "pts_last5_local": v29.get("puntos_local"),
        "pts_last5_visita": v29.get("puntos_visita"),
        "delta_pts_5p": v29.get("delta_puntos"),
        "racha_local": v29.get("racha_local"),
        "racha_visita": v29.get("racha_visita"),
        "xg_trend_local": v30.get("pendiente_local"),
        "xg_trend_visita": v30.get("pendiente_visita"),
        "xg_promedio_local": v30.get("promedio_local"),
        "xg_promedio_visita": v30.get("promedio_visita"),
        "xga_trend_local": v31.get("pendiente_local"),
        "xga_trend_visita": v31.get("pendiente_visita"),
        "xga_promedio_local": v31.get("promedio_local"),
        "xga_promedio_visita": v31.get("promedio_visita"),
        "xpts_diff_local": v32.get("delta_xpts_local"),
        "xpts_diff_visita": v32.get("delta_xpts_visita"),
        "xpts_neto": v32.get("delta_xpts_neto"),
        "xpts_umbral": UMBRAL_XPTS,
        "muestra_local": v29.get("muestra_local"),
        "muestra_visita": v29.get("muestra_visita"),
        "ventana_completa": v29.get("ventana_completa"),
        "corpus_opta_disponible": bool(meta_corpus.get("disponible")),
        "corpus_opta_partidos": meta_corpus.get("partidos_en_corpus", 0),
    }


def _bloque_vacio_trayectoria(
    match_id: str,
    temporada: str,
    motivo: str,
    semaforos: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Bloque `trayectoria` degradado: cero cifras inventadas, cero defaults de esquema."""
    return {
        "nodos_gobernanza": list(NODOS_GOBIERNO),
        "proveedor": "TRAJECTORY_PROVIDER",
        "modo": "SOLO_LECTURA",
        "temporada": str(temporada),
        "match": {"id": str(match_id)},
        "corte_n_1": {
            "jornada_corte": None,
            "regla": REGLA_CORTE,
            "partidos_local": [],
            "partidos_visita": [],
            "muestra_local": 0,
            "muestra_visita": 0,
            "ventana_completa": False,
        },
        "corpus_opta": {"disponible": False, "partidos_en_corpus": 0},
        "dimension_8_trayectoria": {},
        "sintesis_momento": {},
        "semaforos": dict(semaforos or {}),
        "insumos": _insumos_trayectoria({}, {}, {}, {}, {}),
        "status": ESTADO_SIN_EVIDENCIA,
        "motivo": motivo,
        "escritura_bd": False,
        "llamadas_red": False,
    }


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [LN-QBE-117] CONTRATO PÚBLICO · bloque `trayectoria` del paquete `insumos_factivados`
# ═════════════════════════════════════════════════════════════════════════════════════════════
def obtener_metricas_trayectoria(
    sesion: Any,
    match_id: str,
    temporada: Optional[str] = None,
    jornada: Optional[int] = None,
    local_slug: Optional[str] = None,
    visita_slug: Optional[str] = None,
    directorio_datos: Optional[str] = None,
    ruta_corpus: Optional[str] = None,
) -> Dict[str, Any]:
    """Bloque `trayectoria` del paquete `insumos_factivados` (sólo lectura, cero red).

    Migración VERBATIM de `[LN-QBE-110]`: `V31` (forma 5P), `AUX_M_XG` (pendiente xG),
    `AUX_M_XGA` (pendiente xGA) y `V32` (ΔxPTS), con corte futuro-ciego N−1 y degradación íntegra
    a `SIN EVIDENCIA`.
    """
    temporada = str(temporada or TEMPORADA_DEFAULT)
    fixture = leer_fixture_cartelera(sesion, match_id) if sesion is not None else None
    if fixture is None:
        return _bloque_vacio_trayectoria(
            match_id,
            temporada,
            f"El fixture `{match_id}` no existe en `matches`: trayectoria sin evidencia.",
        )

    jornada = int(jornada or fixture.get("jornada") or 0)
    local = str(local_slug or fixture.get("local_slug") or "").lower().strip()
    visita = str(visita_slug or fixture.get("visitante_slug") or "").lower().strip()
    corte = jornada - 1 if jornada >= 2 else None
    partidos_corpus, meta_corpus = cargar_corpus_opta(
        temporada, directorio_datos, ruta_corpus
    )

    ventana_local = _ventana_5p(sesion, local, corte, partidos_corpus)
    ventana_visita = _ventana_5p(sesion, visita, corte, partidos_corpus)

    snapshot, entradas = _snapshot_corte(sesion, corte, temporada)
    pj_max = max((int(fila.get("pj") or 0) for fila in entradas), default=0)
    matchday_snapshot = int(snapshot["matchday"]) if snapshot is not None else None
    estricto = bool(matchday_snapshot is not None and pj_max <= matchday_snapshot)
    fidelidad = {
        "snapshot_id": (snapshot or {}).get("id"),
        "matchday_snapshot": matchday_snapshot,
        "captured_at": str((snapshot or {}).get("captured_at") or ""),
        "pj_max": pj_max,
        "corte_solicitado": corte,
        "estricto": estricto,
        "advertencia": (
            ""
            if estricto or snapshot is None
            else (
                f"El snapshot J{matchday_snapshot} publica clubes con pj_max={pj_max} "
                f"(> corte {matchday_snapshot}): la foto incluye resultados posteriores. "
                "Se conserva la etiqueta del snapshot como testigo y se advierte la "
                "contaminación; la ventana de trayectoria sí respeta J < N."
            )
        ),
    }
    entrada_local = _entrada_posiciones(entradas, local)
    entrada_visita = _entrada_posiciones(entradas, visita)

    # ── V31 · Forma 5P (puntos reales de la ventana) ────────────────────────────────────────
    forma_local = _forma_5p(ventana_local["partidos"])
    forma_visita = _forma_5p(ventana_visita["partidos"])
    evidencia_forma = (
        forma_local["muestra"] == VENTANA_TRAYECTORIA
        and forma_visita["muestra"] == VENTANA_TRAYECTORIA
    )
    v29 = {
        "id": "V31",
        "variable": nombre_de_celda("V31", "Forma 5P (Puntos Recientes)"),
        "unidad": "puntos",
        "estado": ESTADO_EVALUADO if evidencia_forma else ESTADO_SIN_EVIDENCIA,
        "puntos_local": forma_local["puntos"] if forma_local["muestra"] else None,
        "puntos_visita": (
            forma_visita["puntos"] if forma_visita["muestra"] else None
        ),
        "delta_puntos": (
            forma_local["puntos"] - forma_visita["puntos"]
            if evidencia_forma
            else None
        ),
        "racha_local": forma_local["racha"],
        "racha_visita": forma_visita["racha"],
        "muestra_local": forma_local["muestra"],
        "muestra_visita": forma_visita["muestra"],
        "ventana_completa": (
            forma_local["muestra"] == VENTANA_TRAYECTORIA
            and forma_visita["muestra"] == VENTANA_TRAYECTORIA
        ),
        "partidos_local": forma_local["partidos"],
        "partidos_visita": forma_visita["partidos"],
        "nota": (
            "Pts5P = 3G + 1E por club; ventana = últimos 5 partidos terminales con J < N. "
            "El campo `forma` del snapshot sólo se usa como testigo de contraste."
        ),
    }

    # ── AUX_M_XG · Pendiente de peligro ofensivo (xG, sin celda en el catálogo) ───────────────────────────────────────────
    m_xg_local = ventana_local["pendiente_xg"]
    m_xg_visita = ventana_visita["pendiente_xg"]
    direccion_xg_local = _direccion_xg(m_xg_local)
    direccion_xg_visita = _direccion_xg(m_xg_visita)
    evidencia_xg = (
        ventana_local["ventana_completa"]
        and ventana_local["integro"]
        and ventana_visita["ventana_completa"]
        and ventana_visita["integro"]
    )
    v30 = {
        "id": "AUX_M_XG",
        "variable": "Pendiente xG 5P (m_xG)",
        "unidad": "xG/partido",
        "estado": ESTADO_EVALUADO if evidencia_xg else ESTADO_SIN_EVIDENCIA,
        "pendiente_local": m_xg_local,
        "pendiente_visita": m_xg_visita,
        "direccion_local": direccion_xg_local["etiqueta"],
        "direccion_visita": direccion_xg_visita["etiqueta"],
        "clave_local": direccion_xg_local["clave"],
        "clave_visita": direccion_xg_visita["clave"],
        "flecha_local": direccion_xg_local["flecha"],
        "flecha_visita": direccion_xg_visita["flecha"],
        "serie_local": ventana_local["serie_xg"],
        "serie_visita": ventana_visita["serie_xg"],
        "promedio_local": ventana_local["promedio_xg"],
        "promedio_visita": ventana_visita["promedio_xg"],
        "muestra_local": ventana_local["muestra"],
        "muestra_visita": ventana_visita["muestra"],
        "nota": (
            "OLS exacta sobre t=1..5 (denominador 10); m>0 ⇒ aceleración ofensiva, "
            "m<0 ⇒ desaceleración. xG del corpus Opta congelado, jamás imputado."
        ),
    }

    # ── AUX_M_XGA · Pendiente de vulnerabilidad defensiva (xGA, sin celda) ──────────────────────────────────
    m_xga_local = ventana_local["pendiente_xga"]
    m_xga_visita = ventana_visita["pendiente_xga"]
    direccion_xga_local = _direccion_xga(m_xga_local)
    direccion_xga_visita = _direccion_xga(m_xga_visita)
    evidencia_xga = (
        ventana_local["ventana_completa"]
        and ventana_local["integro"]
        and ventana_visita["ventana_completa"]
        and ventana_visita["integro"]
    )
    v31 = {
        "id": "AUX_M_XGA",
        "variable": "Pendiente xGA 5P (m_xGA)",
        "unidad": "xGA/partido",
        "estado": ESTADO_EVALUADO if evidencia_xga else ESTADO_SIN_EVIDENCIA,
        "pendiente_local": m_xga_local,
        "pendiente_visita": m_xga_visita,
        "direccion_local": direccion_xga_local["etiqueta"],
        "direccion_visita": direccion_xga_visita["etiqueta"],
        "clave_local": direccion_xga_local["clave"],
        "clave_visita": direccion_xga_visita["clave"],
        "flecha_local": direccion_xga_local["flecha"],
        "flecha_visita": direccion_xga_visita["flecha"],
        "serie_local": ventana_local["serie_xga"],
        "serie_visita": ventana_visita["serie_xga"],
        "promedio_local": ventana_local["promedio_xga"],
        "promedio_visita": ventana_visita["promedio_xga"],
        "muestra_local": ventana_local["muestra"],
        "muestra_visita": ventana_visita["muestra"],
        "nota": (
            "OLS exacta sobre t=1..5 (denominador 10); m<0 ⇒ consolidación defensiva, "
            "m>0 ⇒ resquebrajamiento. xGA del corpus Opta congelado."
        ),
    }

    # ── V32 · ΔxPTS (PTS − xPTS) con auditoría de fidelidad del corte ──────────────────────
    pts_local, xpts_local = _puntos_y_xpts(entrada_local)
    pts_visita, xpts_visita = _puntos_y_xpts(entrada_visita)
    diagnostico_local = (
        evaluar_diagnostico_xpts(pts_local, xpts_local)
        if pts_local is not None and xpts_local is not None
        else None
    )
    diagnostico_visita = (
        evaluar_diagnostico_xpts(pts_visita, xpts_visita)
        if pts_visita is not None and xpts_visita is not None
        else None
    )
    evidencia_xpts = (
        diagnostico_local is not None and diagnostico_visita is not None
    )
    v32 = {
        "id": "V32",
        "variable": nombre_de_celda("V32", "Varianza ΔxPTS"),
        "unidad": "puntos",
        "estado": ESTADO_EVALUADO if evidencia_xpts else ESTADO_SIN_EVIDENCIA,
        "puntos_local": _r(pts_local, 4),
        "xpts_local": _r(xpts_local, 4),
        "delta_xpts_local": (
            diagnostico_local["delta_xpts"] if diagnostico_local else None
        ),
        "diagnostico_local": (
            diagnostico_local["diagnostico"]
            if diagnostico_local
            else ESTADO_SIN_EVIDENCIA
        ),
        "alerta_local": (
            diagnostico_local["alerta"]
            if diagnostico_local
            else "Sin fila del club en el snapshot de posiciones del corte."
        ),
        "nivel_local": (
            diagnostico_local["nivel"] if diagnostico_local else NIVEL_NEUTRAL
        ),
        "glifo_local": (
            diagnostico_local["glifo"]
            if diagnostico_local
            else GLIFO[NIVEL_NEUTRAL]
        ),
        "puntos_visita": _r(pts_visita, 4),
        "xpts_visita": _r(xpts_visita, 4),
        "delta_xpts_visita": (
            diagnostico_visita["delta_xpts"] if diagnostico_visita else None
        ),
        "diagnostico_visita": (
            diagnostico_visita["diagnostico"]
            if diagnostico_visita
            else ESTADO_SIN_EVIDENCIA
        ),
        "alerta_visita": (
            diagnostico_visita["alerta"]
            if diagnostico_visita
            else "Sin fila del club en el snapshot de posiciones del corte."
        ),
        "nivel_visita": (
            diagnostico_visita["nivel"] if diagnostico_visita else NIVEL_NEUTRAL
        ),
        "glifo_visita": (
            diagnostico_visita["glifo"]
            if diagnostico_visita
            else GLIFO[NIVEL_NEUTRAL]
        ),
        "delta_xpts_neto": (
            round(
                float(diagnostico_local["delta_xpts"])
                - float(diagnostico_visita["delta_xpts"]),
                6,
            )
            if evidencia_xpts
            else None
        ),
        "umbral": UMBRAL_XPTS,
        "fuente": (
            f"standings_snapshots#{(snapshot or {}).get('id')} (J{matchday_snapshot})"
            if snapshot is not None
            else "standings_snapshots (sin snapshot ≤ corte)"
        ),
        "fidelidad_corte": fidelidad,
        "nota": (
            "PTS y xPTS se leen del snapshot histórico ≤ N−1; no se sustituyen por la "
            "tabla viva. Δ ≥ +3 ⇒ sobre-rendimiento; Δ ≤ −3 ⇒ sub-rendimiento."
        ),
    }

    # `[LN-QBE-122]` Claves del bloque: `V31`/`V32` son celdas del catálogo; las pendientes
    # `m_xG`/`m_xGA` no tienen casilla y viajan como auxiliares sin código.
    dimension_8 = {"V31": v29, "AUX_M_XG": v30, "AUX_M_XGA": v31, "V32": v32}
    sintesis = _sintesis_momento(v29, v30, v31, v32)
    evaluadas = sum(
        1 for celda in dimension_8.values() if celda["estado"] == ESTADO_EVALUADO
    )
    if evaluadas == len(dimension_8):
        status = ESTADO_EXITO
        motivo = (
            "Las 4 celdas de trayectoria (V31 · AUX_M_XG · AUX_M_XGA · V32) quedaron "
            "evaluadas con evidencia íntegra."
        )
    elif evaluadas:
        status = ESTADO_PARCIAL
        motivo = f"{evaluadas}/4 variables evaluadas; el resto degradó a SIN EVIDENCIA."
    else:
        status = ESTADO_SIN_EVIDENCIA
        motivo = (
            "No hay ventana previa ni snapshot ≤ N−1 para evaluar la trayectoria."
        )

    cobertura_integra = bool(ventana_local["integro"] and ventana_visita["integro"])
    cobertura_completa = bool(
        ventana_local["ventana_completa"] and ventana_visita["ventana_completa"]
    )
    nivel_trayectoria = (
        NIVEL_VERDE
        if evaluadas == len(dimension_8)
        else (NIVEL_AMARILLO if evaluadas else NIVEL_NEUTRAL)
    )
    nivel_corte = (
        NIVEL_VERDE
        if estricto
        else (NIVEL_AMARILLO if snapshot is not None else NIVEL_NEUTRAL)
    )
    nivel_cobertura = (
        NIVEL_VERDE
        if cobertura_integra and cobertura_completa
        else (
            NIVEL_AMARILLO
            if (ventana_local["muestra"] or ventana_visita["muestra"])
            else NIVEL_NEUTRAL
        )
    )
    semaforos = {
        "TRAYECTORIA": _semaforo(
            nivel_trayectoria, f"{evaluadas}/4 celdas de trayectoria evaluadas."
        ),
        "CORTE": _semaforo(
            nivel_corte,
            (
                f"Snapshot J{matchday_snapshot} estricto (pj_max={pj_max})."
                if estricto
                else (fidelidad["advertencia"] or "Sin snapshot ≤ corte.")
            ),
        ),
        "COBERTURA_OPTA": _semaforo(
            nivel_cobertura,
            (
                f"Local {ventana_local['muestra']}/5 · "
                f"Visita {ventana_visita['muestra']}/5 · "
                f"series íntegras: {cobertura_integra}."
            ),
        ),
    }

    return {
        "nodos_gobernanza": list(NODOS_GOBIERNO),
        "proveedor": "TRAJECTORY_PROVIDER",
        "modo": "SOLO_LECTURA",
        "temporada": temporada,
        "match": fixture,
        "corte_n_1": {
            "jornada_corte": corte,
            "regla": REGLA_CORTE,
            "partidos_local": ventana_local["partidos"],
            "partidos_visita": ventana_visita["partidos"],
            "muestra_local": ventana_local["muestra"],
            "muestra_visita": ventana_visita["muestra"],
            "ventana_completa": cobertura_completa,
        },
        "corpus_opta": meta_corpus,
        "dimension_8_trayectoria": dimension_8,
        "sintesis_momento": sintesis,
        "semaforos": semaforos,
        "insumos": _insumos_trayectoria(v29, v30, v31, v32, meta_corpus),
        "status": status,
        "motivo": motivo,
        "escritura_bd": False,
        "llamadas_red": False,
    }









