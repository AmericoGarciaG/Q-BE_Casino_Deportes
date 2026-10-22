# -*- coding: utf-8 -*-
"""
🧪 Q-BE SOVEREIGN · PROVEEDOR CANÓNICO DE VOLUMEN TERRITORIAL & PORTERÍA (Fase 1)
[LN-QBE-117] · [ARCH-1.4.50] · Migración VERBATIM de `[LN-QBE-111]` (sandbox de laboratorio).
Régimen: `[HÍBRIDO DUAL-TRACK]`

* `[DIRGEN-STRICT]`: el Factor de Control de Cancha y el Save % NO se reimplementan. El FCF se
  consume VERBATIM de `SyntheticMetricsEngine._compute_fcf` (`[LN-QBE-030]`, clamps inmutables
  `[0.65, 1.35]`) y de él se deriva el residuo ortogonal `v_Vol⊥ = FCF − 1.0 ∈ [−0.35, +0.35]`.
* `[DBBD-FUNGIBLE]`: composición del corte N−1, celdas V01/V16 y notas de cobertura.

Contrato público:
  * `obtener_metricas_volumen_porteria(sesion, match_id, ...)` → bloque `volumen_porteria` del
    paquete `insumos_factivados` con V01 (posesión media), V16 (Save %) y el residuo ortogonal.
  * `telemetria_de_club(sesion, partidos, slug)` → capa de lectura compartida de la fase sobre
    `match_telemetry` (la consumen también los proveedores de trayectoria y ataque/defensa).

Axiomas operativos (idénticos al plano sellado):
  1. Sólo lectura: la bóveda 3NF se lee a través del adaptador `src/core/sovereign_reads.py`, que
     entrega diccionarios planos; este paquete puro jamás importa `sqlalchemy` ni `src.storage`
     (`[ARCH-1.4.26]`). Cero caché congelada, cero red, cero escrituras.
  2. Futuro-ceguera N−1: el corte de cada club son los partidos TERMINALES con `matchday_num < N`;
     el fixture evaluado jamás alimenta su propia acumulación.
  3. Cobertura ÍNTEGRA: una sola ausencia de telemetría degrada la tasa completa a `None`
     (`SIN EVIDENCIA`). Jamás se promedia una submuestra ni se imputa un cero
     (`[GOVERNANCE-01]`).
  4. Una fila con los defaults del esquema ORM (`possession_pct=50.0`, `sot=0.0`, `sota=0.0`) NO es
     evidencia: se descarta y se declara en la cobertura `cubiertos/total`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.core.metrics import SyntheticMetricsEngine
from src.core.sovereign.context_provider import (
    ESTADO_EXITO,
    ESTADO_PARCIAL,
    ESTADO_SIN_EVIDENCIA,
    TEMPORADA_DEFAULT,
    _r,
    leer_fixture_cartelera,
    partidos_terminales_de_club,
)
from src.core.sovereign_reads import leer_telemetria

__all__ = [
    "calcular_delta_posesion",
    "calcular_save_percentage",
    "calcular_residuo_volumen_ortogonal",
    "telemetria_de_club",
    "obtener_metricas_volumen_porteria",
]

# ── Nodos de gobierno ─────────────────────────────────────────────────────────────────────────
NODOS_GOBIERNO: Tuple[str, ...] = ("LN-QBE-117", "ARCH-1.4.50", "LN-QBE-111", "LN-QBE-030")

ESTADO_EVALUADO = "EVALUADO"
NOTA_FASE_6 = "SIN EVIDENCIA (FASE 6)"
REGLA_CORTE = "matchday_num < N ∧ estado ∈ {FINALIZADO, FINISHED} (futuro-ceguera N−1)"

# Clamps inmutables del plano sellado [LN-QBE-030] — sólo se LEEN, jamás se redefinen.
FCF_MIN = SyntheticMetricsEngine.FCF_MIN
FCF_MAX = SyntheticMetricsEngine.FCF_MAX
COTA_RESIDUO: Tuple[float, float] = (round(FCF_MIN - 1.0, 4), round(FCF_MAX - 1.0, 4))

# Defaults del esquema ORM: una fila así NO es evidencia (cero conversión inventada).
_POSS_DEFAULT = 50.0
_SOT_DEFAULT = 0.0
_SOTA_DEFAULT = 0.0

UMBRAL_DELTA_POSESION = 5.0     # lectura forense del ΔPosición (puntos porcentuales)
UMBRAL_RESIDUO = 0.05           # banda neutra del residuo ortogonal

# ── Taxonomía bipartita de las dimensiones ([LN-QBE-111] · 𝒯_Vol / 𝒯_Gk) ──────────────────────
# (id, nombre forense, unidad canónica, nota de procedencia)
_TAXONOMIA_DIM_1: Tuple[Tuple[str, str, str, str], ...] = (
    ("V01", "Posesión efectiva de balón", "%",
     "Posesión media del corte N−1; fuente: match_telemetry.possession_pct con cobertura íntegra."),
    ("V02", "Toques en el área rival", "toques/90",
     "SIN EVIDENCIA (FASE 6): el sensor congelado no publica toques en área."),
    ("V03", "Pases progresivos completados", "pases/90",
     "SIN EVIDENCIA (FASE 6): el sensor congelado no publica pases progresivos."),
    ("V04", "Entradas al último tercio", "entradas/90",
     "SIN EVIDENCIA (FASE 6): el sensor congelado no publica entradas al último tercio."),
)
_TAXONOMIA_DIM_4: Tuple[Tuple[str, str, str, str], ...] = (
    ("V15", "Goles prevenidos (xGOT − GC)", "xGOT−GC/90",
     "SIN EVIDENCIA (FASE 6): el sensor congelado no publica xGOT (post-shot)."),
    ("V16", "Porcentaje de atajadas (Save %)", "%",
     "Save% = 100·(SoTA − GC)/SoTA sobre el corte N−1, cobertura íntegra de SoTA."),
    ("V17", "Salidas exitosas por alto", "salidas/90",
     "SIN EVIDENCIA (FASE 6): el sensor congelado no publica high claims."),
)


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [LN-QBE-111] ARITMÉTICA PURA (sin estado, sin I/O — auditable por The Shield en aislamiento)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def calcular_delta_posesion(poss_local: float, poss_visita: float) -> float:
    """ΔPosición = `Poss_local − Poss_visita`, acotado por construcción a [−100, +100].

    Valores fuera de `[0, 100]` son un error de contrato (la posesión es un porcentaje) y se
    rechazan en voz alta: nunca se silencia un dato corrupto.
    """
    for nombre, valor in (("poss_local", poss_local), ("poss_visita", poss_visita)):
        if valor is None:
            raise ValueError(f"ΔPosición requiere {nombre}: la ausencia se declara, no se imputa.")
        numero = float(valor)
        if numero < 0.0 or numero > 100.0:
            raise ValueError(f"ΔPosición fuera de contrato: {nombre}={numero} ∉ [0, 100].")
    return round(float(poss_local) - float(poss_visita), 4)


def calcular_save_percentage(sota: float, gc: float) -> float:
    """Save % = 100·(SoTA − GC)/SoTA, saturado en [0, 100].

    * `SoTA = 0` ⇒ `100.0` (sin remates a puerta no hay nada que atajar; no es un fallo).
    * `GC > SoTA` (autogoles o datos sucios) ⇒ `0.0` por saturación inferior: un porcentaje de
      atajadas negativo no tiene lectura futbolística.
    * Entradas negativas ⇒ `ValueError`: son un error de contrato, no un caso de negocio.
    """
    sota_num = float(sota)
    gc_num = float(gc)
    if sota_num < 0.0 or gc_num < 0.0:
        raise ValueError(f"Save% requiere magnitudes no negativas: SoTA={sota_num}, GC={gc_num}.")
    if sota_num == 0.0:
        return 100.0
    bruto = 100.0 * (sota_num - gc_num) / sota_num
    return round(max(0.0, min(100.0, bruto)), 4)


def calcular_residuo_volumen_ortogonal(poss_pct: float, sot: float, sota: float) -> float:
    """`v_Vol⊥ = FCF − 1.0` delegando VERBATIM en `SyntheticMetricsEngine._compute_fcf`.

    El FCF sellado ya aplica los clamps `[0.65, 1.35]`, por lo que el residuo está garantizado en
    `[−0.35, +0.35]` sin re-clampear localmente: cero margen para divergir del servidor central.
    * `v_Vol⊥ > 0` ⇒ dominio territorial CONVERTIDO en peligro (volumen eficiente).
    * `v_Vol⊥ < 0` ⇒ presión ESTÉRIL: se domina el balón sin traducirlo en remates a puerta.
    """
    poss_num = float(poss_pct)
    if poss_num < 0.0 or poss_num > 100.0:
        raise ValueError(f"FCF fuera de contrato: poss_pct={poss_num} ∉ [0, 100].")
    if float(sot) < 0.0 or float(sota) < 0.0:
        raise ValueError(f"FCF requiere SoT/SoTA no negativos: SoT={sot}, SoTA={sota}.")
    fcf = SyntheticMetricsEngine._compute_fcf(poss_num, float(sot), float(sota))
    return round(float(fcf) - 1.0, 6)


def _lectura_residuo(valor: Optional[float]) -> str:
    """Traducción forense del residuo ortogonal a lenguaje de cuerpo técnico."""
    if valor is None:
        return NOTA_FASE_6
    if valor >= UMBRAL_RESIDUO:
        return "DOMINIO CONVERTIDO"
    if valor <= -UMBRAL_RESIDUO:
        return "PRESIÓN ESTÉRIL"
    return "NEUTRAL TERRITORIAL"


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [LN-QBE-117] CAPA DE LECTURA COMPARTIDA SOBRE `match_telemetry` (sólo lectura, 3NF)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _valor_telemetria(fila: Dict[str, Any], atributo: str) -> Optional[float]:
    """Magnitud numérica de una columna de `match_telemetry`; `None` si no está publicada."""
    valor = fila.get(atributo)
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return float(valor)
    return None


def telemetria_de_club(
    sesion: Any, partidos: Sequence[Dict[str, Any]], slug: str
) -> Dict[str, Any]:
    """Agrega posesión/SoT/SoTA desde `match_telemetry` con cobertura ÍNTEGRA obligatoria.

    Las tres magnitudes se exigen juntas: la posesión sin el reparto de remates no permite
    construir el FCF (`[LN-QBE-030]`), y el SoTA sin posesión no permite diagnosticar el volumen.
    Una fila creada con los defaults del esquema (`0.0` / `0.0` / `50.0`) no es evidencia y se
    descarta. Cobertura incompleta ⇒ `poss_sum`/`sot_total`/`sota_total` quedan `None`.
    """
    ids = [str(partido["match_id"]) for partido in partidos]
    resultado: Dict[str, Any] = {
        "fuente": "match_telemetry",
        "club_slug": str(slug or ""),
        "cubiertos": 0,
        "total": len(ids),
        "poss_sum": None,
        "sot_total": None,
        "sota_total": None,
        "faltantes": list(ids),
    }
    if not ids:
        return resultado
    # Adaptador soberano de lectura: la capa pura recibe diccionarios planos ([ARCH-1.4.26]).
    filas = leer_telemetria(sesion, ids, slug)
    indice = {str(fila["match_id"]): fila for fila in filas}
    validas: Dict[str, Tuple[float, float, float]] = {}
    for identificador in ids:
        fila = indice.get(identificador)
        if fila is None:
            continue
        poss = _valor_telemetria(fila, "possession_pct")
        sot = _valor_telemetria(fila, "sot")
        sota = _valor_telemetria(fila, "sota")
        if poss is None or sot is None or sota is None:
            continue
        if sot == _SOT_DEFAULT and sota == _SOTA_DEFAULT and poss == _POSS_DEFAULT:
            # Defaults del esquema: fila huérfana, NO evidencia fáctica.
            continue
        validas[identificador] = (poss, sot, sota)
    faltantes = [identificador for identificador in ids if identificador not in validas]
    resultado["cubiertos"] = len(validas)
    resultado["faltantes"] = faltantes
    if faltantes or not validas:
        # Cobertura incompleta ⇒ NO se publica la tasa: mezclar submuestras sesga el corte.
        return resultado
    resultado["poss_sum"] = round(sum(triple[0] for triple in validas.values()), 4)
    resultado["sot_total"] = round(sum(triple[1] for triple in validas.values()), 4)
    resultado["sota_total"] = round(sum(triple[2] for triple in validas.values()), 4)
    return resultado


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [LN-QBE-117] CORTE N−1 DEL CLUB (goles reales + telemetría con cobertura íntegra)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _corte_club(
    sesion: Any, partidos: Sequence[Dict[str, Any]], slug: str
) -> Dict[str, Any]:
    """Acumulado del corte futuro-ciego de un club (cero imputación, cero defaults del esquema).

    `poss_pct` es la media de los porcentajes por partido; `sot`/`sota` se publican como total del
    corte y como tasa por partido (≈ por 90 min). Cualquier ausencia de cobertura deja las tres
    magnitudes en `None`: el FCF no se inventa.
    """
    telemetria = telemetria_de_club(sesion, partidos, slug)
    pj = len(partidos)
    corte: Dict[str, Any] = {
        "club_slug": str(slug or ""),
        "pj": pj,
        "gf": sum(int(partido["goles_favor"]) for partido in partidos),
        "gc": sum(int(partido["goles_contra"]) for partido in partidos),
        "pts": sum(
            3 if partido["goles_favor"] > partido["goles_contra"]
            else (1 if partido["goles_favor"] == partido["goles_contra"] else 0)
            for partido in partidos
        ),
        "poss_pct": None,
        "sot_total": telemetria.get("sot_total"),
        "sota_total": telemetria.get("sota_total"),
        "sot_rate": None,
        "sota_rate": None,
        "cobertura_telemetria": {
            "cubiertos": int(telemetria.get("cubiertos") or 0),
            "total": int(telemetria.get("total") or pj),
            "faltantes": list(telemetria.get("faltantes") or []),
        },
        "partidos": [dict(partido) for partido in partidos],
    }
    poss_sum = telemetria.get("poss_sum")
    if poss_sum is not None and pj > 0:
        corte["poss_pct"] = round(float(poss_sum) / float(pj), 4)
    if corte["sot_total"] is not None and pj > 0:
        corte["sot_rate"] = round(float(corte["sot_total"]) / float(pj), 4)
    if corte["sota_total"] is not None and pj > 0:
        corte["sota_rate"] = round(float(corte["sota_total"]) / float(pj), 4)
    return corte


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [LN-QBE-117] CELDAS V01/V16, RESIDUO ORTOGONAL Y ΔPOSICIÓN
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _celda(
    identificador: str,
    nombre: str,
    unidad: str,
    local: Optional[float],
    visita: Optional[float],
    nota: str,
    formato: str = "num",
) -> Dict[str, Any]:
    """Celda bipartita homogénea: `EVALUADO` sólo si AMBOS clubes publican magnitud real.

    `formato="pct"` publica la magnitud de presentación con sufijo `%` (contrato del Juez) y
    replica el valor numérico en `local_num`/`visita_num` para el consumo máquina.
    """
    evaluada = local is not None and visita is not None
    local_num = round(float(local), 4) if evaluada else None
    visita_num = round(float(visita), 4) if evaluada else None
    if formato == "pct":
        local_pub = f"{local_num:.1f}%" if evaluada else None
        visita_pub = f"{visita_num:.1f}%" if evaluada else None
    else:
        local_pub, visita_pub = local_num, visita_num
    return {
        "id": identificador,
        "variable": nombre,
        "unidad": unidad,
        "local": local_pub,
        "visita": visita_pub,
        "local_num": local_num,
        "visita_num": visita_num,
        "estado": ESTADO_EVALUADO if evaluada else ESTADO_SIN_EVIDENCIA,
        "origen": "match_telemetry",
        "impacto": "H_vol" if identificador.startswith("V0") else "H_gk",
        "nota": nota,
        "glifo": "🟢" if evaluada else "⚪",
    }


def _nota_cobertura(
    corte_local: Dict[str, Any], corte_visita: Dict[str, Any], sujeto: str
) -> str:
    """Nota de degradación con la cobertura explícita `cubiertos/total` de AMBOS cortes."""
    cob_local = corte_local.get("cobertura_telemetria") or {}
    cob_visita = corte_visita.get("cobertura_telemetria") or {}
    return (
        f"{NOTA_FASE_6}: `{sujeto}` cubre "
        f"{int(cob_local.get('cubiertos') or 0)}/{int(cob_local.get('total') or corte_local.get('pj') or 0)} "
        f"partidos del corte local y "
        f"{int(cob_visita.get('cubiertos') or 0)}/{int(cob_visita.get('total') or corte_visita.get('pj') or 0)} "
        "del corte visita. Cero imputación [GOVERNANCE-01]."
    )


def _save_de_corte(corte: Dict[str, Any]) -> Optional[float]:
    """Save % del corte N−1; `None` si el club-corte no publica SoTA (ausencia declarada)."""
    sota = corte.get("sota_total")
    if sota is None or int(corte.get("pj") or 0) <= 0:
        return None
    return calcular_save_percentage(float(sota), float(corte.get("gc") or 0.0))


def _lado_residuo(corte: Dict[str, Any], etiqueta: str) -> Dict[str, Any]:
    """Un club-corte del bloque ortogonal: insumos → FCF sellado → `v_Vol⊥` → lectura forense."""
    poss = corte.get("poss_pct")
    sot = corte.get("sot_total")
    sota = corte.get("sota_total")
    bloque: Dict[str, Any] = {
        "etiqueta": etiqueta,
        "club_slug": corte.get("club_slug"),
        "poss_pct": _r(poss),
        "sot": _r(sot),
        "sota": _r(sota),
        "fcf": None,
        "residuo": None,
        "lectura": NOTA_FASE_6,
        "nota": None,
    }
    if poss is None or sot is None or sota is None:
        bloque["nota"] = (
            f"{NOTA_FASE_6}: el corte no publica posesión/SoT/SoTA íntegros; "
            "el FCF no se inventa."
        )
        return bloque
    residuo = calcular_residuo_volumen_ortogonal(poss, sot, sota)
    bloque.update({
        "fcf": round(residuo + 1.0, 6),
        "residuo": residuo,
        "lectura": _lectura_residuo(residuo),
    })
    return bloque


def _bloque_residuo(
    corte_local: Dict[str, Any], corte_visita: Dict[str, Any]
) -> Dict[str, Any]:
    """Residuo de Volumen Ortogonal: separa el DOMINIO del PELIGRO REAL ([LN-QBE-111])."""
    lado_local = _lado_residuo(corte_local, "LOCAL")
    lado_visita = _lado_residuo(corte_visita, "VISITA")
    if lado_local["residuo"] is None or lado_visita["residuo"] is None:
        delta = None
    else:
        delta = round(lado_local["residuo"] - lado_visita["residuo"], 6)
    return {
        "local": lado_local,
        "visita": lado_visita,
        "delta": delta,
        "lectura_delta": _lectura_residuo(delta),
        "formula": "v_Vol⊥ = FCF − 1.0; FCF = clamp[(Poss/50)·(2·(SoT+1)/(SoT+SoTA+2)), 0.65, 1.35]",
        "delegacion": "SyntheticMetricsEngine._compute_fcf ([LN-QBE-030])",
        "cotas": [COTA_RESIDUO[0], COTA_RESIDUO[1]],
    }


def _bloque_delta_posesion(
    corte_local: Dict[str, Any], corte_visita: Dict[str, Any], celda_v01: Dict[str, Any]
) -> Dict[str, Any]:
    """ΔPosición bipartita con la MISMA fuente que publica V01 (coherencia interna garantizada)."""
    poss_local = corte_local.get("poss_pct")
    poss_visita = corte_visita.get("poss_pct")
    bloque: Dict[str, Any] = {
        "valor": None,
        "local": _r(poss_local),
        "visita": _r(poss_visita),
        "lectura": NOTA_FASE_6,
        "nota": None,
        "estado": celda_v01.get("estado"),
    }
    if poss_local is None or poss_visita is None:
        bloque["nota"] = f"{NOTA_FASE_6}: ΔPosición no computable sin posesión íntegra de ambos cortes."
        return bloque
    valor = calcular_delta_posesion(poss_local, poss_visita)
    if valor >= UMBRAL_DELTA_POSESION:
        lectura = "DOMINIO LOCAL"
    elif valor <= -UMBRAL_DELTA_POSESION:
        lectura = "DOMINIO VISITA"
    else:
        lectura = "PARIDAD TERRITORIAL"
    bloque.update({"valor": valor, "lectura": lectura})
    return bloque


def _dimension_volumen(
    corte_local: Dict[str, Any], corte_visita: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """𝒯_Vol · DIM 1 (V01-V04): sólo V01 tiene feed en esta fase del corpus."""
    nota_v01 = _TAXONOMIA_DIM_1[0][3]
    if corte_local.get("poss_pct") is None or corte_visita.get("poss_pct") is None:
        nota_v01 = _nota_cobertura(corte_local, corte_visita, "match_telemetry.possession_pct")
    celdas: Dict[str, Dict[str, Any]] = {
        "V01": _celda(
            "V01", _TAXONOMIA_DIM_1[0][1], _TAXONOMIA_DIM_1[0][2],
            corte_local.get("poss_pct"), corte_visita.get("poss_pct"), nota_v01, formato="pct",
        )
    }
    for identificador, nombre, unidad, nota in _TAXONOMIA_DIM_1[1:]:
        celdas[identificador] = _celda(identificador, nombre, unidad, None, None, nota)
    return celdas


def _dimension_porteria(
    corte_local: Dict[str, Any], corte_visita: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """𝒯_Gk · DIM 4 (V15-V17): sólo V16 tiene feed (Save % sobre SoTA del corte)."""
    save_local = _save_de_corte(corte_local)
    save_visita = _save_de_corte(corte_visita)
    nota_v16 = _TAXONOMIA_DIM_4[1][3]
    if save_local is None or save_visita is None:
        nota_v16 = _nota_cobertura(corte_local, corte_visita, "match_telemetry.sota")
    celdas: Dict[str, Dict[str, Any]] = {}
    for identificador, nombre, unidad, nota in _TAXONOMIA_DIM_4:
        if identificador == "V16":
            celdas[identificador] = _celda(
                identificador, nombre, unidad, save_local, save_visita, nota_v16, formato="pct"
            )
        else:
            celdas[identificador] = _celda(identificador, nombre, unidad, None, None, nota)
    return celdas


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [LN-QBE-117] CONTRATO PÚBLICO · bloque `volumen_porteria` del paquete `insumos_factivados`
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _insumos_volumen(
    corte_local: Dict[str, Any], corte_visita: Dict[str, Any]
) -> Dict[str, Any]:
    """Insumos planos que consume el motor + el transcriptor de 44 variables (`[LN-QBE-102]`).

    Claves heredadas respetadas al carácter (`poss_local`, `sot_local`, `sota_local`, ...) para que
    `_FORMATO_INSUMO` de `factor_attribution` encienda V01/V06/V11 sin traducción adicional.
    """
    poss_local = corte_local.get("poss_pct")
    poss_visita = corte_visita.get("poss_pct")
    lado_local = _lado_residuo(corte_local, "LOCAL")
    lado_visita = _lado_residuo(corte_visita, "VISITA")
    delta_poss = (
        calcular_delta_posesion(poss_local, poss_visita)
        if poss_local is not None and poss_visita is not None
        else None
    )
    delta_vol = (
        round(lado_local["residuo"] - lado_visita["residuo"], 6)
        if lado_local["residuo"] is not None and lado_visita["residuo"] is not None
        else None
    )
    return {
        # [LN-QBE-102] V01 · posesión media del corte
        "poss_local": _r(poss_local),
        "poss_visita": _r(poss_visita),
        "poss_diff": _r(delta_poss),
        # [LN-QBE-102] V06/V11 · tiros a puerta por partido (tasa del corte)
        "sot_local": _r(corte_local.get("sot_rate")),
        "sot_visita": _r(corte_visita.get("sot_rate")),
        "sota_local": _r(corte_local.get("sota_rate")),
        "sota_visita": _r(corte_visita.get("sota_rate")),
        # Acumulados del corte (auditoría forense; jamás se usan como tasa)
        "sot_total_local": _r(corte_local.get("sot_total")),
        "sot_total_visita": _r(corte_visita.get("sot_total")),
        "sota_total_local": _r(corte_local.get("sota_total")),
        "sota_total_visita": _r(corte_visita.get("sota_total")),
        "pj_local": int(corte_local.get("pj") or 0),
        "pj_visita": int(corte_visita.get("pj") or 0),
        "gc_local": int(corte_local.get("gc") or 0),
        "gc_visita": int(corte_visita.get("gc") or 0),
        # V16 · Save % saturado [0, 100]
        "save_local": _r(_save_de_corte(corte_local)),
        "save_visita": _r(_save_de_corte(corte_visita)),
        # Residuo ortogonal (FCF sellado − 1.0)
        "fcf_local": lado_local["fcf"],
        "fcf_visita": lado_visita["fcf"],
        "v_vol_local": lado_local["residuo"],
        "v_vol_visita": lado_visita["residuo"],
        "v_vol_delta": delta_vol,
        # Cobertura declarada (base del semáforo de la fase)
        "cobertura_local": dict(corte_local.get("cobertura_telemetria") or {}),
        "cobertura_visita": dict(corte_visita.get("cobertura_telemetria") or {}),
    }


def _semaforo_volumen(insumos: Dict[str, Any]) -> Dict[str, Any]:
    """Semáforo de la fase: 🟢 cobertura íntegra bilateral · 🟡 parcial · 🔴 sin evidencia."""
    cob_local = insumos.get("cobertura_local") or {}
    cob_visita = insumos.get("cobertura_visita") or {}
    evaluadas_local = int(cob_local.get("cubiertos") or 0)
    evaluadas_visita = int(cob_visita.get("cubiertos") or 0)
    total_local = int(cob_local.get("total") or 0)
    total_visita = int(cob_visita.get("total") or 0)
    integra = (
        total_local > 0 and total_visita > 0
        and evaluadas_local == total_local and evaluadas_visita == total_visita
    )
    if integra:
        glifo, lectura = "🟢", "COBERTURA ÍNTEGRA BILATERAL"
    elif evaluadas_local > 0 and evaluadas_visita > 0:
        glifo, lectura = "🟡", "COBERTURA PARCIAL (submuestra no publicada)"
    else:
        glifo, lectura = "🔴", NOTA_FASE_6
    return {
        "glifo": glifo,
        "lectura": lectura,
        "cubiertos_local": evaluadas_local,
        "total_local": total_local,
        "cubiertos_visita": evaluadas_visita,
        "total_visita": total_visita,
    }


def _dimensiones_vacias_volumen(motivo: str) -> Dict[str, Any]:
    """Celdas apagadas de las dos dimensiones con feed, para el bloque degradado honesto."""
    celdas: Dict[str, Any] = {}
    for identificador, nombre, unidad, _ in _TAXONOMIA_DIM_1:
        celdas[identificador] = _celda(identificador, nombre, unidad, None, None, motivo)
    for identificador, nombre, unidad, _ in _TAXONOMIA_DIM_4:
        celdas[identificador] = _celda(identificador, nombre, unidad, None, None, motivo)
    return celdas


def _bloque_vacio_volumen(match_id: str, motivo: str, temporada: str) -> Dict[str, Any]:
    """Bloque degradado honesto: cero cifras, cero defaults, semáforo apagado."""
    return {
        "bloque": "volumen_porteria",
        "match_id": str(match_id),
        "temporada": str(temporada),
        "status": ESTADO_SIN_EVIDENCIA,
        "motivo": motivo,
        "fixture": None,
        "jornada": None,
        "cortes": {"local": None, "visita": None},
        "dimensiones": {"dim_1": None, "dim_4": None},
        "residuo": None,
        "delta_posesion": None,
        "semaforo": {
            "glifo": "🔴", "lectura": motivo,
            "cubiertos_local": 0, "total_local": 0,
            "cubiertos_visita": 0, "total_visita": 0,
        },
        "insumos": {
            "poss_local": None, "poss_visita": None, "poss_diff": None,
            "sot_local": None, "sot_visita": None,
            "sota_local": None, "sota_visita": None,
            "save_local": None, "save_visita": None,
            "v_vol_local": None, "v_vol_visita": None, "v_vol_delta": None,
            "cobertura_local": {"cubiertos": 0, "total": 0, "faltantes": []},
            "cobertura_visita": {"cubiertos": 0, "total": 0, "faltantes": []},
        },
        "variables": _dimensiones_vacias_volumen(motivo),
    }


def obtener_metricas_volumen_porteria(
    sesion: Any,
    match_id: str,
    temporada: Optional[str] = None,
    jornada: Optional[int] = None,
    local_slug: Optional[str] = None,
    visita_slug: Optional[str] = None,
    limite: Optional[int] = None,
) -> Dict[str, Any]:
    """[LN-QBE-117] Bloque `volumen_porteria` del paquete `insumos_factivados` (sólo lectura).

    Migración VERBATIM de `[LN-QBE-111]` desde el sandbox de laboratorio: V01 (posesión media),
    V16 (Save %) y el residuo ortogonal `v_Vol⊥ = FCF − 1.0` sobre el corte futuro-ciego N−1.

    * `jornada` ausente ⇒ se toma de `matches.matchday_num` (`kickoff` nunca se lee).
    * `local_slug`/`visita_slug` ausentes ⇒ se toman del fixture de cartelera.
    * `limite` recorta la COLA del corte (ventana móvil de la fase de trayectoria).

    Degradación honesta: sin fixture, sin jornada computable o con cortes vacíos el bloque sale
    con `status="SIN EVIDENCIA"` y todas las magnitudes en `None`. Nunca se inventa un cero.
    """
    temporada_txt = str(temporada or TEMPORADA_DEFAULT)
    fixture = leer_fixture_cartelera(sesion, match_id)
    if fixture is None:
        return _bloque_vacio_volumen(
            match_id,
            "SIN EVIDENCIA: el fixture evaluado no existe en la cartelera 3NF.",
            temporada_txt,
        )
    jornada_corte = int(fixture.get("jornada") or 0) if jornada is None else int(jornada)
    if jornada_corte <= 1:
        return _bloque_vacio_volumen(
            match_id,
            f"SIN EVIDENCIA: jornada de corte N={jornada_corte} sin historia previa ({REGLA_CORTE}).",
            temporada_txt,
        )
    club_local = str(local_slug or fixture.get("local_slug") or "").lower().strip()
    club_visita = str(visita_slug or fixture.get("visitante_slug") or "").lower().strip()
    if not club_local or not club_visita:
        return _bloque_vacio_volumen(
            match_id,
            "SIN EVIDENCIA: el fixture no publica los slugs de ambos clubes.",
            temporada_txt,
        )
    partidos_local = partidos_terminales_de_club(sesion, club_local, jornada_corte, limite)
    partidos_visita = partidos_terminales_de_club(sesion, club_visita, jornada_corte, limite)
    if not partidos_local or not partidos_visita:
        return _bloque_vacio_volumen(
            match_id,
            "SIN EVIDENCIA: uno de los clubes no tiene partidos terminales previos en la bóveda.",
            temporada_txt,
        )

    corte_local = _corte_club(sesion, partidos_local, club_local)
    corte_visita = _corte_club(sesion, partidos_visita, club_visita)
    dim_volumen = _dimension_volumen(corte_local, corte_visita)
    dim_porteria = _dimension_porteria(corte_local, corte_visita)
    insumos = _insumos_volumen(corte_local, corte_visita)
    publicadas = [
        celda
        for celda in list(dim_volumen.values()) + list(dim_porteria.values())
        if celda["estado"] == ESTADO_EVALUADO
    ]
    if len(publicadas) >= 2:
        status = ESTADO_EXITO
        motivo = "V01 y V16 publicadas con cobertura íntegra bilateral [LN-QBE-117]."
    elif publicadas:
        status = ESTADO_PARCIAL
        motivo = "Cobertura parcial: sólo una de las tasas tiene feed íntegro [LN-QBE-117]."
    else:
        status = ESTADO_SIN_EVIDENCIA
        motivo = (
            "SIN EVIDENCIA: el corpus no publica posesión/SoT/SoTA íntegros para ambos cortes."
        )

    variables: Dict[str, Any] = {}
    variables.update(dim_volumen)
    variables.update(dim_porteria)
    return {
        "bloque": "volumen_porteria",
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
            "dim_1": {"taxonomia": "𝒯_Vol", "variables": list(dim_volumen.keys())},
            "dim_4": {"taxonomia": "𝒯_Gk", "variables": list(dim_porteria.keys())},
        },
        "residuo": _bloque_residuo(corte_local, corte_visita),
        "delta_posesion": _bloque_delta_posesion(corte_local, corte_visita, dim_volumen["V01"]),
        "semaforo": _semaforo_volumen(insumos),
        "insumos": insumos,
        "variables": variables,
        "regla_corte": REGLA_CORTE,
        "nodos": list(NODOS_GOBIERNO),
    }


def _resumen_corte(corte: Dict[str, Any]) -> Dict[str, Any]:
    """Vista pública y acotada del corte (sin la lista completa de partidos)."""
    return {
        "club_slug": corte.get("club_slug"),
        "pj": int(corte.get("pj") or 0),
        "gf": int(corte.get("gf") or 0),
        "gc": int(corte.get("gc") or 0),
        "pts": int(corte.get("pts") or 0),
        "poss_pct": _r(corte.get("poss_pct")),
        "sot_rate": _r(corte.get("sot_rate")),
        "sota_rate": _r(corte.get("sota_rate")),
        "cobertura_telemetria": dict(corte.get("cobertura_telemetria") or {}),
    }






