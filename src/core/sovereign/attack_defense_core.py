# -*- coding: utf-8 -*-
"""
⚔️ Q-BE SOVEREIGN · NÚCLEO CANÓNICO DE ATAQUE & DEFENSA (Fase 1 · Integración Maestra)
[LN-QBE-117] · [ARCH-1.4.55] · Migración VERBATIM de `[LN-QBE-108]` / `[ARCH-1.4.47]`.
Régimen: [DIRGEN-STRICT] para la colisión cruzada de fuerzas (cero margen creativo).

Contrato público:
  * `obtener_metricas_ataque_defensa(sesion, match_id, ...)` → bloque `ataque_defensa` del paquete
    `insumos_factivados` con V05 (xG/90), V06 (SoT/90), V10 (xGA/90) y V11 (SoTA/90), los factores
    estructurales sellados `[VAULT-CORE-005]` y la colisión cruzada `[LN-QBE-108]`.
  * `calcular_colision_fuerzas_cruzadas(A_h, D_a, A_a, D_h)` → choque complementario puro (sin I/O).

Fuentes de evidencia (SÓLO LECTURA, cero escritura, cero red):
  1. Bóveda 3NF (`matches`) vía la capa compartida de `context_provider` (corte futuro-ciego N−1).
  2. Corpus Opta congelado para xG/xGA (lector compartido de `trajectory_provider`).
  3. `match_telemetry` para SoT/SoTA vía la capa compartida de `telemetry_provider`.

Decreto VAR-2026-J7-HOMOLOGACION §E1: `xga` permanece FUERA del `raw_match_data` que consume el
motor sellado —el diagnóstico defensivo certificado no se altera—; el xGA se publica sólo como V10
(evidencia exhibida). El motor jamás ve una cifra que no esté homologada.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.core.sovereign.context_provider import (
    ESTADO_EXITO,
    ESTADO_PARCIAL,
    ESTADO_SIN_EVIDENCIA,
    TEMPORADA_DEFAULT,
    _r,
    leer_fixture_cartelera,
    partidos_terminales_de_club,
)
from src.core.sovereign.telemetry_provider import telemetria_de_club
from src.core.sovereign.trajectory_provider import cargar_corpus_opta, registro_opta
from src.core.sovereign_pipeline import derivar_factores_estructurales

__all__ = [
    "calcular_colision_fuerzas_cruzadas",
    "obtener_metricas_ataque_defensa",
]

# ── Nodos de gobierno y constantes legisladas ────────────────────────────────────────────────
NODOS_GOBIERNO: Tuple[str, ...] = ("LN-QBE-117", "ARCH-1.4.55", "LN-QBE-108", "ARCH-1.4.47")

ESTADO_EVALUADO = "EVALUADO"
NOTA_FASE_6 = "SIN EVIDENCIA (FASE 6)"
REGLA_CORTE = "matchday_num < N ∧ estado ∈ {FINALIZADO, FINISHED} (futuro-ceguera N−1)"
MU_LIGA_DEFAULT = 2.65           # [CONSTANTS] media de goles de la competición

NIVEL_VERDE = "VERDE"
NIVEL_AMARILLO = "AMARILLO"
NIVEL_NEUTRAL = "NEUTRAL"
GLIFO: Dict[str, str] = {
    NIVEL_VERDE: "🟢",
    NIVEL_AMARILLO: "🟡",
    NIVEL_NEUTRAL: "⚪",
    ESTADO_EVALUADO: "🟢",
    ESTADO_SIN_EVIDENCIA: "⚪",
    ESTADO_EXITO: "🟢",
    ESTADO_PARCIAL: "🟡",
}

# ── Taxonomía bipartita de las dimensiones nucleares ([LN-QBE-101] · 𝒯_Fin / 𝒯_Def) ──────────
# (id, nombre forense, unidad canónica, nota de procedencia)
_TAXONOMIA_DIM_2: Tuple[Tuple[str, str, str, str], ...] = (
    ("V05", "xG por 90 minutos (ancla npxG)", "npxG/90",
     "xG Opta de shotmap (agregación factual de disparos) por 90 min, corte N−1."),
    ("V06", "Tiros a puerta (SoT)", "SoT/90",
     "SoT por 90 min; fuente: match_telemetry 3NF (hoy vacía) / caché congelada."),
    ("V07", "xG a puerta (xGOT)", "xGOT/90",
     "SIN EVIDENCIA (FASE 6): el sensor congelado no publica xGOT. No se simula."),
    ("V08", "Grandes oportunidades creadas", "BC/90",
     "SIN EVIDENCIA (FASE 6): el sensor congelado no publica big chances creadas."),
    ("V09", "Grandes oportunidades falladas", "BC/90",
     "SIN EVIDENCIA (FASE 6): el sensor congelado no publica big chances falladas."),
)
_TAXONOMIA_DIM_3: Tuple[Tuple[str, str, str, str], ...] = (
    ("V10", "xGA por 90 minutos (ancla defensiva)", "xGA/90",
     "xGA Opta de shotmap por 90 min, corte N−1 (evidencia exhibida, no insumo del motor)."),
    ("V11", "Tiros a puerta concedidos (SoTA)", "SoTA/90",
     "SoTA por 90 min; fuente: match_telemetry 3NF (hoy vacía) / caché congelada."),
    ("V12", "PPDA (presión defensiva)", "índice",
     "SIN EVIDENCIA (FASE 6): el sensor congelado no publica PPDA."),
    ("V13", "Recuperaciones en tercio medio", "rec/90",
     "SIN EVIDENCIA (FASE 6): el sensor congelado no publica recuperaciones."),
    ("V14", "Grandes oportunidades concedidas", "BC/90",
     "SIN EVIDENCIA (FASE 6): el sensor congelado no publica big chances concedidas."),
)


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [LN-QBE-108] ARITMÉTICA PURA (sin estado, sin I/O — auditable por The Shield en aislamiento)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _celda(
    identificador: str,
    nombre: str,
    unidad: str,
    local: Optional[float],
    visita: Optional[float],
    nota: str,
) -> Dict[str, Any]:
    """Celda bipartita homogénea: `EVALUADO` sólo si AMBOS clubes publican magnitud real."""
    evaluada = local is not None and visita is not None
    return {
        "id": identificador,
        "variable": nombre,
        "unidad": unidad,
        "local": round(float(local), 4) if evaluada else None,
        "visita": round(float(visita), 4) if evaluada else None,
        "estado": ESTADO_EVALUADO if evaluada else ESTADO_SIN_EVIDENCIA,
        "nota": nota,
    }


def _tasa(total: Optional[float], pj: int) -> Optional[float]:
    """Tasa por partido (≈ por 90 min). `None` sin total o sin muestra: cero invención."""
    if total is None or pj <= 0:
        return None
    return float(total) / float(pj)


def _magnitud(bloque: Dict[str, Any], clave: str) -> Optional[float]:
    """Magnitud numérica publicada; `None` si la clave no existe (cero conversión inventada)."""
    valor = bloque.get(clave)
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return float(valor)
    return None


def calcular_colision_fuerzas_cruzadas(
    A_h: float,
    D_a: float,
    A_a: float,
    D_h: float,
) -> Dict[str, Any]:
    """Choque cruzado de la ecuación log-lineal: ataque de un bando contra defensa del otro.

    Definición sellada [LN-QBE-108]:
        empuje_ofensivo_local  = A_H − D_A        (ataque local contra defensa visita)
        empuje_ofensivo_visita = A_A − D_H        (ataque visita contra defensa local)
        diferencial_neto       = empuje_local − empuje_visita = (A_H − D_A) − (A_A − D_H)

    El signo del diferencial identifica al bando dominante. NO se restan ataques entre sí
    (eso violaría la estructura bipartita de V05-V14): sólo se cruzan fuerzas complementarias.
    """
    empuje_local = float(A_h) - float(D_a)
    empuje_visita = float(A_a) - float(D_h)
    diferencial = empuje_local - empuje_visita
    if diferencial > 1e-12:
        bando = "LOCAL"
    elif diferencial < -1e-12:
        bando = "VISITANTE"
    else:
        bando = "EQUILIBRADO"
    return {
        "A_home": round(float(A_h), 6),
        "D_away": round(float(D_a), 6),
        "A_away": round(float(A_a), 6),
        "D_home": round(float(D_h), 6),
        "empuje_ofensivo_local": round(empuje_local, 6),
        "empuje_ofensivo_visita": round(empuje_visita, 6),
        "diferencial_neto_partido": round(diferencial, 6),
        "magnitud_colision": round(abs(empuje_local) + abs(empuje_visita), 6),
        "bando_dominante": bando,
        "ecuacion_local": f"A_H − D_A = {float(A_h):+.4f} − ({float(D_a):+.4f})",
        "ecuacion_visita": f"A_A − D_H = {float(A_a):+.4f} − ({float(D_h):+.4f})",
    }


# ═════════════════════════════════════════════════════════════════════════════════════════════
# PROTOCOLO DE INGESTA FÁCTICA (corte N−1 + corpus congelado + telemetría 3NF, sólo lectura)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _bloque_sede(partidos: Sequence[Dict[str, Any]], es_local: bool) -> Dict[str, Any]:
    """Split de sede (`pj`, `gf`, `gc`, `pts`) exigido por `[LN-QBE-038]`; `{}` si está vacío."""
    tramo = [p for p in partidos if p["es_local"] is es_local]
    if not tramo:
        return {}
    return {
        "pj": len(tramo),
        "gf": sum(p["goles_favor"] for p in tramo),
        "gc": sum(p["goles_contra"] for p in tramo),
        "pts": sum(
            3 if p["goles_favor"] > p["goles_contra"] else (1 if p["goles_favor"] == p["goles_contra"] else 0)
            for p in tramo
        ),
    }


def _corte_club(
    partidos: Sequence[Dict[str, Any]],
    corpus: Dict[str, Any],
    telemetria: Dict[str, Any],
) -> Dict[str, Any]:
    """Corte N−1 de un club: goles reales + cobertura ÍNTEGRA de xG/xGA publicados.

    Regla dura: `xg_total`/`xga_total` sólo se publican si TODOS los partidos del corte traen la
    métrica Opta. Una sola ausencia ⇒ `None` (el motor cae a la ruta sellada con GF real).
    """
    pj = len(partidos)
    acumulado: Dict[str, Any] = {
        "pj": pj,
        "gf": sum(p["goles_favor"] for p in partidos),
        "gc": sum(p["goles_contra"] for p in partidos),
        "pts": sum(
            3 if p["goles_favor"] > p["goles_contra"] else (1 if p["goles_favor"] == p["goles_contra"] else 0)
            for p in partidos
        ),
        "xg_total": None,
        "xga_total": None,
        "cobertura_xg": {"cubiertos": 0, "total": pj, "faltantes": []},
        "sot_total": telemetria.get("sot_total"),
        "sota_total": telemetria.get("sota_total"),
        "cobertura_sot": {
            "cubiertos": int(telemetria.get("cubiertos") or 0),
            "total": int(telemetria.get("total") or pj),
            "faltantes": list(telemetria.get("faltantes") or []),
        },
        "partidos": [dict(p) for p in partidos],
    }
    cubiertos = 0
    faltantes: List[str] = []
    xg_suma = 0.0
    xga_suma = 0.0
    for partido in partidos:
        xg, xga = registro_opta(corpus, str(partido["match_id"]), bool(partido["es_local"]))
        if xg is None or xga is None:
            faltantes.append(str(partido["match_id"]))
            continue
        cubiertos += 1
        xg_suma += xg
        xga_suma += xga
    if pj > 0 and cubiertos == pj:
        acumulado["xg_total"] = round(xg_suma, 4)
        acumulado["xga_total"] = round(xga_suma, 4)
    acumulado["cobertura_xg"] = {"cubiertos": cubiertos, "total": pj, "faltantes": faltantes}
    return acumulado


def _bloque_factico(acumulado: Dict[str, Any]) -> Dict[str, Any]:
    """Bloque homologado §E1: publica `gf`, `gc`, `pj`, `pts` y `xg` — JAMÁS `xga`."""
    bloque: Dict[str, Any] = {
        "pj": int(acumulado["pj"]),
        "gf": int(acumulado["gf"]),
        "gc": int(acumulado["gc"]),
        "pts": int(acumulado["pts"]),
    }
    if acumulado.get("xg_total") is not None:
        bloque["xg"] = float(acumulado["xg_total"])
    return bloque


def _resumen_corte(acumulado: Dict[str, Any]) -> Dict[str, Any]:
    """Corte N−1 auditable: muestra, goles reales, tasas y cobertura de cada métrica."""
    pj = int(acumulado["pj"])
    partidos = acumulado["partidos"]
    jornadas = [p["jornada"] for p in partidos if p.get("jornada")]
    return {
        "pj": pj,
        "rango_jornadas": [min(jornadas), max(jornadas)] if jornadas else None,
        "gf": int(acumulado["gf"]),
        "gc": int(acumulado["gc"]),
        "pts": int(acumulado["pts"]),
        "gf_90": _r(_tasa(acumulado["gf"], pj)),
        "gc_90": _r(_tasa(acumulado["gc"], pj)),
        "xg_total": _r(acumulado.get("xg_total")),
        "xga_total": _r(acumulado.get("xga_total")),
        "npxg_90": _r(_tasa(acumulado.get("xg_total"), pj)),
        "xga_90": _r(_tasa(acumulado.get("xga_total"), pj)),
        "sot_total": _r(acumulado.get("sot_total")),
        "sota_total": _r(acumulado.get("sota_total")),
        "sot_90": _r(_tasa(acumulado.get("sot_total"), pj)),
        "sota_90": _r(_tasa(acumulado.get("sota_total"), pj)),
        "cobertura_xg": dict(acumulado["cobertura_xg"]),
        "cobertura_sot": dict(acumulado["cobertura_sot"]),
        "splits_sede": {
            "como_local": _bloque_sede(partidos, True),
            "como_visitante": _bloque_sede(partidos, False),
        },
    }


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [LN-QBE-108] COMPOSICIÓN DEL BLOQUE (dimensiones, insumos y semáforos)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _nota_faltante(
    acum_local: Dict[str, Any], acum_visita: Dict[str, Any], metrica: str
) -> str:
    """Nota honesta del faltante: publica la cobertura de AMBOS cortes, no sólo uno."""
    cobertura_h = acum_local.get(f"cobertura_{metrica}") or {}
    cobertura_v = acum_visita.get(f"cobertura_{metrica}") or {}
    return (
        f"{NOTA_FASE_6}: `match_telemetry` cubre "
        f"{int(cobertura_h.get('cubiertos') or 0)}/{int(cobertura_h.get('total') or acum_local['pj'])} "
        f"partidos del corte local y "
        f"{int(cobertura_v.get('cubiertos') or 0)}/{int(cobertura_v.get('total') or acum_visita['pj'])} "
        f"del corte visita."
    )


def _dimensiones(
    acum_local: Dict[str, Any], acum_visita: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Materializa V05-V09 (𝒯_Fin) y V10-V14 (𝒯_Def) en celdas bipartitas simétricas.

    V05/V10 se evalúan con la caché Opta congelada (cobertura íntegra obligatoria).
    V06/V11 se evalúan sólo si `match_telemetry` cubre TODOS los partidos del corte.
    El resto se declara `SIN EVIDENCIA (FASE 6)`: cero cifras inventadas `[GOVERNANCE-01]`.
    """
    pj_h, pj_v = int(acum_local["pj"]), int(acum_visita["pj"])
    xg_h = _tasa(acum_local.get("xg_total"), pj_h)
    xg_v = _tasa(acum_visita.get("xg_total"), pj_v)
    xga_h = _tasa(acum_local.get("xga_total"), pj_h)
    xga_v = _tasa(acum_visita.get("xga_total"), pj_v)
    sot_h = _tasa(acum_local.get("sot_total"), pj_h)
    sot_v = _tasa(acum_visita.get("sot_total"), pj_v)
    sota_h = _tasa(acum_local.get("sota_total"), pj_h)
    sota_v = _tasa(acum_visita.get("sota_total"), pj_v)

    dim_2: Dict[str, Any] = {}
    for identificador, nombre, unidad, nota in _TAXONOMIA_DIM_2:
        if identificador == "V05":
            dim_2["V05"] = _celda(identificador, nombre, unidad, xg_h, xg_v, nota)
        elif identificador == "V06":
            nota_v06 = (
                nota if (sot_h is not None and sot_v is not None)
                else _nota_faltante(acum_local, acum_visita, "sot")
            )
            dim_2["V06"] = _celda(identificador, nombre, unidad, sot_h, sot_v, nota_v06)
        else:
            dim_2[identificador] = _celda(identificador, nombre, unidad, None, None, nota)

    dim_3: Dict[str, Any] = {}
    for identificador, nombre, unidad, nota in _TAXONOMIA_DIM_3:
        if identificador == "V10":
            dim_3["V10"] = _celda(identificador, nombre, unidad, xga_h, xga_v, nota)
        elif identificador == "V11":
            nota_v11 = (
                nota if (sota_h is not None and sota_v is not None)
                else _nota_faltante(acum_local, acum_visita, "sot")
            )
            dim_3["V11"] = _celda(identificador, nombre, unidad, sota_h, sota_v, nota_v11)
        else:
            dim_3[identificador] = _celda(identificador, nombre, unidad, None, None, nota)
    return dim_2, dim_3


def _insumos_ataque_defensa(
    acum_local: Dict[str, Any],
    acum_visita: Dict[str, Any],
    colision: Dict[str, Any],
) -> Dict[str, Any]:
    """Insumos REALES consumidos por el motor sellado (claves planas heredadas `[LN-QBE-102]`).

    Las claves `xg_*_rate`, `xga_*_rate`, `gc_*_rate`, `sot_*`, `sota_*` y `pj_sede_*` conservan
    nombre y significado byte a byte para que el catálogo de 44 variables ilumine las MISMAS celdas.
    """
    pj_h, pj_v = int(acum_local["pj"]), int(acum_visita["pj"])
    splits_h = _bloque_sede(acum_local["partidos"], True)
    splits_v = _bloque_sede(acum_visita["partidos"], False)
    return {
        "xg_local_rate": _r(_tasa(acum_local.get("xg_total"), pj_h)),
        "xg_visita_rate": _r(_tasa(acum_visita.get("xg_total"), pj_v)),
        "xga_local_rate": _r(_tasa(acum_local.get("xga_total"), pj_h)),
        "xga_visita_rate": _r(_tasa(acum_visita.get("xga_total"), pj_v)),
        "gc_local_rate": _r(_tasa(acum_local["gc"], pj_h)),
        "gc_visita_rate": _r(_tasa(acum_visita["gc"], pj_v)),
        "sot_local": _r(_tasa(acum_local.get("sot_total"), pj_h)),
        "sot_visita": _r(_tasa(acum_visita.get("sot_total"), pj_v)),
        "sota_local": _r(_tasa(acum_local.get("sota_total"), pj_h)),
        "sota_visita": _r(_tasa(acum_visita.get("sota_total"), pj_v)),
        "pj_sede_local": int(splits_h.get("pj") or 0),
        "pj_sede_visita": int(splits_v.get("pj") or 0),
        "A_home": colision.get("A_home"),
        "D_away": colision.get("D_away"),
        "A_away": colision.get("A_away"),
        "D_home": colision.get("D_home"),
        "empuje_ofensivo_local": colision.get("empuje_ofensivo_local"),
        "empuje_ofensivo_visita": colision.get("empuje_ofensivo_visita"),
        "diferencial_neto_partido": colision.get("diferencial_neto_partido"),
        "magnitud_colision": colision.get("magnitud_colision"),
        "bando_dominante": colision.get("bando_dominante"),
        "cobertura_opta_local": dict(acum_local["cobertura_xg"]),
        "cobertura_opta_visita": dict(acum_visita["cobertura_xg"]),
        "cobertura_telemetria_local": dict(acum_local["cobertura_sot"]),
        "cobertura_telemetria_visita": dict(acum_visita["cobertura_sot"]),
        "xg_es_real_opta": (
            acum_local.get("xg_total") is not None and acum_visita.get("xg_total") is not None
        ),
    }


def _semaforo(nivel: str, detalle: str) -> Dict[str, str]:
    """Celda de salud fiduciaria homogénea (nivel + glifo + evidencia textual)."""
    return {"nivel": nivel, "glifo": GLIFO.get(nivel, "·"), "detalle": detalle}


def _semaforos(corte_local: Dict[str, Any], corte_visita: Dict[str, Any]) -> Dict[str, Any]:
    """Semáforos de cobertura: Opta (V05/V10) y telemetría 3NF (V06/V11)."""
    opta_h = int(corte_local["cobertura_xg"]["cubiertos"])
    opta_v = int(corte_visita["cobertura_xg"]["cubiertos"])
    total_h = int(corte_local["cobertura_xg"]["total"])
    total_v = int(corte_visita["cobertura_xg"]["total"])
    completa = opta_h == total_h and opta_v == total_v and total_h > 0 and total_v > 0
    opta = _semaforo(
        NIVEL_VERDE if completa else (NIVEL_AMARILLO if (opta_h or opta_v) else NIVEL_NEUTRAL),
        f"Opta local {opta_h}/{total_h} · visita {opta_v}/{total_v}.",
    )
    sot_h = int(corte_local["cobertura_sot"]["cubiertos"])
    sot_v = int(corte_visita["cobertura_sot"]["cubiertos"])
    tot_sot_h = int(corte_local["cobertura_sot"]["total"])
    tot_sot_v = int(corte_visita["cobertura_sot"]["total"])
    completa_sot = sot_h == tot_sot_h and sot_v == tot_sot_v and tot_sot_h > 0 and tot_sot_v > 0
    telemetria = _semaforo(
        NIVEL_VERDE if completa_sot else (NIVEL_AMARILLO if (sot_h or sot_v) else NIVEL_NEUTRAL),
        f"match_telemetry local {sot_h}/{tot_sot_h} · visita {sot_v}/{tot_sot_v}.",
    )
    return {"OPTA": opta, "TELEMETRIA": telemetria}


def _dimensiones_vacias(motivo: str) -> Dict[str, Any]:
    """Celdas apagadas de V05-V14 (taxonomía completa, cero cifras: `SIN EVIDENCIA`)."""
    vacias: Dict[str, Any] = {}
    for identificador, nombre, unidad, nota in _TAXONOMIA_DIM_2 + _TAXONOMIA_DIM_3:
        vacias[identificador] = _celda(identificador, nombre, unidad, None, None, motivo or nota)
    return vacias


def _bloque_vacio_ataque_defensa(match_id: str, motivo: str, temporada: str) -> Dict[str, Any]:
    """Bloque degradado honesto: cero factores, cero colisión, semáforo apagado."""
    return {
        "bloque": "ataque_defensa",
        "match_id": str(match_id),
        "temporada": str(temporada),
        "status": ESTADO_SIN_EVIDENCIA,
        "motivo": motivo,
        "fixture": None,
        "jornada": None,
        "cortes": {"local": None, "visita": None},
        "dimensiones": {"dim_2": None, "dim_3": None},
        "factores": {"A_home": None, "D_away": None, "A_away": None, "D_home": None},
        "colision": None,
        "semaforos": {
            "OPTA": _semaforo(NIVEL_NEUTRAL, motivo),
            "TELEMETRIA": _semaforo(NIVEL_NEUTRAL, motivo),
        },
        "insumos": {
            "xg_local_rate": None, "xg_visita_rate": None,
            "xga_local_rate": None, "xga_visita_rate": None,
            "gc_local_rate": None, "gc_visita_rate": None,
            "sot_local": None, "sot_visita": None,
            "sota_local": None, "sota_visita": None,
            "pj_sede_local": 0, "pj_sede_visita": 0,
            "A_home": None, "D_away": None, "A_away": None, "D_home": None,
            "empuje_ofensivo_local": None, "empuje_ofensivo_visita": None,
            "diferencial_neto_partido": None, "magnitud_colision": None,
            "bando_dominante": None, "xg_es_real_opta": False,
        },
        "variables": _dimensiones_vacias(motivo),
        "corpus_opta": {},
        "regla_corte": REGLA_CORTE,
        "nodos": list(NODOS_GOBIERNO),
    }


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [LN-QBE-117] CONTRATO PÚBLICO · bloque `ataque_defensa` del paquete `insumos_factivados`
# ═════════════════════════════════════════════════════════════════════════════════════════════
def obtener_metricas_ataque_defensa(
    sesion: Any,
    match_id: str,
    temporada: Optional[str] = None,
    jornada: Optional[int] = None,
    local_slug: Optional[str] = None,
    visita_slug: Optional[str] = None,
    limite: Optional[int] = None,
    directorio_datos: Optional[str] = None,
    ruta_corpus: Optional[str] = None,
    mu_liga: float = MU_LIGA_DEFAULT,
) -> Dict[str, Any]:
    """Bloque `ataque_defensa` del paquete `insumos_factivados` (sólo lectura, cero red).

    Migración VERBATIM de `[LN-QBE-108]` desde el sandbox de laboratorio: V05 (xG/90), V06 (SoT/90),
    V10 (xGA/90) y V11 (SoTA/90) sobre el corte futuro-ciego N−1, más los factores estructurales
    sellados `[VAULT-CORE-005]` y la colisión cruzada de fuerzas.

    * `jornada` ausente ⇒ se toma del snapshot de cartelera (`kickoff` nunca se lee).
    * `local_slug`/`visita_slug` ausentes ⇒ se toman del fixture de cartelera.
    * `limite` recorta la COLA del corte (ventana móvil de la fase de trayectoria).

    Degradación honesta: sin fixture, sin jornada computable o con un corte vacío el bloque sale
    con `status="SIN EVIDENCIA"`, factores en `None` y el motor sellado NUNCA se invoca (sus
    defaults fabricarían fuerza inexistente).
    """
    temporada_txt = str(temporada or TEMPORADA_DEFAULT)
    fixture = leer_fixture_cartelera(sesion, match_id)
    if fixture is None:
        return _bloque_vacio_ataque_defensa(
            match_id,
            "SIN EVIDENCIA: el fixture evaluado no existe en la cartelera 3NF.",
            temporada_txt,
        )
    jornada_corte = int(fixture.get("jornada") or 0) if jornada is None else int(jornada)
    if jornada_corte <= 1:
        return _bloque_vacio_ataque_defensa(
            match_id,
            f"SIN EVIDENCIA: jornada de corte N={jornada_corte} sin historia previa ({REGLA_CORTE}).",
            temporada_txt,
        )
    club_local = str(local_slug or fixture.get("local_slug") or "").lower().strip()
    club_visita = str(visita_slug or fixture.get("visitante_slug") or "").lower().strip()
    if not club_local or not club_visita:
        return _bloque_vacio_ataque_defensa(
            match_id,
            "SIN EVIDENCIA: el fixture no publica los slugs de ambos clubes.",
            temporada_txt,
        )
    partidos_local = partidos_terminales_de_club(sesion, club_local, jornada_corte, limite)
    partidos_visita = partidos_terminales_de_club(sesion, club_visita, jornada_corte, limite)
    if not partidos_local or not partidos_visita:
        return _bloque_vacio_ataque_defensa(
            match_id,
            "SIN EVIDENCIA: uno de los clubes no tiene partidos terminales previos en la bóveda.",
            temporada_txt,
        )

    corpus, meta_corpus = cargar_corpus_opta(temporada_txt, directorio_datos, ruta_corpus)
    corte_local = _corte_club(
        partidos_local, corpus, telemetria_de_club(sesion, partidos_local, club_local)
    )
    corte_visita = _corte_club(
        partidos_visita, corpus, telemetria_de_club(sesion, partidos_visita, club_visita)
    )

    # ── Insumos homologados (§E1: `xg` sí, `xga` JAMÁS) ──────────────────────────────────────
    crudo: Dict[str, Any] = {
        "home_team_stats": _bloque_factico(corte_local),
        "away_team_stats": _bloque_factico(corte_visita),
        "home_split_stats": _bloque_sede(corte_local["partidos"], True),
        "away_split_stats": _bloque_sede(corte_visita["partidos"], False),
        "xg_es_real_opta": (
            corte_local.get("xg_total") is not None and corte_visita.get("xg_total") is not None
        ),
    }

    # ── Motor sellado [VAULT-CORE-005]: invocación VERBATIM, cero reimplementación ────────────
    A_home, D_away, A_away, D_home = derivar_factores_estructurales(crudo, mu_liga=float(mu_liga))
    colision = calcular_colision_fuerzas_cruzadas(A_home, D_away, A_away, D_home)

    dim_2, dim_3 = _dimensiones(corte_local, corte_visita)
    insumos = _insumos_ataque_defensa(corte_local, corte_visita, colision)
    variables: Dict[str, Any] = {}
    variables.update(dim_2)
    variables.update(dim_3)

    publicadas = [celda for celda in variables.values() if celda.get("estado") == ESTADO_EVALUADO]
    cobertura_completa = (
        int(corte_local["cobertura_xg"]["cubiertos"]) == int(corte_local["pj"])
        and int(corte_visita["cobertura_xg"]["cubiertos"]) == int(corte_visita["pj"])
    )
    if cobertura_completa and len(publicadas) == 4:
        status = ESTADO_EXITO
        motivo = (
            "Cobertura íntegra: V05, V06, V10 y V11 evaluadas con evidencia real y la colisión "
            "cruzada calculada por los planos sellados."
        )
    elif publicadas:
        status = ESTADO_PARCIAL
        motivo = (
            "Cobertura parcial: sólo una parte de V05/V06/V10/V11 tiene feed íntegro en ambos "
            "cortes; las celdas faltantes se declaran SIN EVIDENCIA (cero cifras fabricadas)."
        )
    else:
        status = ESTADO_SIN_EVIDENCIA
        motivo = (
            "SIN EVIDENCIA: ni el corpus Opta ni `match_telemetry` publican las tasas íntegras "
            "para ambos cortes."
        )

    return {
        "bloque": "ataque_defensa",
        "match_id": str(match_id),
        "temporada": temporada_txt,
        "status": status,
        "motivo": motivo,
        "fixture": fixture,
        "jornada": jornada_corte,
        "cortes": {
            "local": _resumen_corte(corte_local),
            "visita": _resumen_corte(corte_visita),
        },
        "dimensiones": {
            "dim_2": {"taxonomia": "𝒯_Fin", "variables": list(dim_2.keys())},
            "dim_3": {"taxonomia": "𝒯_Def", "variables": list(dim_3.keys())},
        },
        "factores": {
            "A_home": colision["A_home"],
            "D_away": colision["D_away"],
            "A_away": colision["A_away"],
            "D_home": colision["D_home"],
            "mu_liga": float(mu_liga),
            "mezcla_sellada": "0.65·xG/90 + 0.35·GF/90 → log(tasa / (μ_liga/2)) [VAULT-CORE-005]",
            "nota_homologacion": (
                "Decreto VAR-2026-J7-HOMOLOGACION §E1: `xga` permanece fuera del `raw_match_data` "
                "para preservar el diagnóstico defensivo certificado; el xGA se publica sólo como V10."
            ),
        },
        "colision": colision,
        "semaforos": _semaforos(corte_local, corte_visita),
        "insumos": insumos,
        "variables": variables,
        "corpus_opta": dict(meta_corpus),
        "regla_corte": REGLA_CORTE,
        "nodos": list(NODOS_GOBIERNO),
    }
