# -*- coding: utf-8 -*-
"""
[LN-QBE-020-C] Kernel H2H Empírico en Eje Localía (Generador C).
[ARCH-1.4.26] Módulo puro del paquete `src/core/sovereign/` (Capa 4 — Sovereign Memory).
Régimen: [DIRGEN-STRICT] — [ALGO-PROTECTED]; legislado en `docs/LOGIC.md` ([LN-QBE-020-C]).

Relación con el canon sellado (composición, cero duplicación):
* La constante de decaimiento κ = ln(2)/180 días⁻¹ se REUTILIZA desde `[LN-QBE-020]`
  (`src/core/temporal.py: TemporalDecayEngine.KAPPA`), único origen de verdad del decaimiento.
* Este nodo NO reimplementa `[LN-QBE-020]`: aquel proyecta la evidencia sobre el eje
  FAVORITO/EMPATE/UNDERDOG (`H2HDecayResult`) y exige 5 partidos; éste proyecta sobre el eje
  LOCAL/EMPATE/VISITA del fixture evaluado (`H2HKernelResult`).
* La ausencia de evidencia jamás se rellena con partidos sintéticos: lista vacía ⇒ `ValueError`
  fail-loud (Ley Zero-H2H `[LN-QBE-020-B]`).

Pureza funcional: sin I/O, sin red, sin SQLAlchemy, sin imports de `src.storage` / `src.ingestion`.
"""

import math
from typing import Any, List, Sequence, Tuple

from src.core.temporal import TemporalDecayEngine
from src.models.analytics import H2HKernelResult

# Vida media sellada por `[LN-QBE-020]` (τ = 180 días).
TAU_HALF_LIFE_DEFAULT = TemporalDecayEngine.TAU_HALF_LIFE_DAYS


def _campo(partido: Any, nombre: str) -> Any:
    """Lectura tolerante de un enfrentamiento histórico (Mapping u objeto tipado)."""
    if isinstance(partido, dict):
        return partido[nombre]
    return getattr(partido, nombre)


def _kappa_para_tau(tau_dias: float) -> float:
    """κ-Decay (`[LN-QBE-020]`): κ = ln(2)/τ. Reutiliza la constante sellada si τ == 180.0."""
    tau = float(tau_dias)
    if tau <= 0.0:
        raise ValueError(f"[LN-QBE-020-C] Vida media τ inválida: {tau_dias}. Debe ser > 0.")
    if tau == TemporalDecayEngine.TAU_HALF_LIFE_DAYS:
        return TemporalDecayEngine.KAPPA
    return math.log(2.0) / tau


def calcular_matriz_h2h_empirica(
    h2h_matches: Sequence[Any],
    tau_dias: float = TAU_HALF_LIFE_DEFAULT,
) -> H2HKernelResult:
    """[LN-QBE-020-C] Matriz empírica H2H en el símplex Δ² (LOCAL / EMPATE / VISITA).

    Ponderación exponencial continua w_k = exp(-κ · Δt_k) con κ = ln(2)/τ (`[LN-QBE-020]`),
    normalizada sobre la masa efectiva observada. Los goles se leen en la perspectiva del
    fixture evaluado: `goles_local` = goles del club local actual en ese enfrentamiento.

    Levanta `ValueError` ante ausencia total de evidencia (fail-loud, cero fabricación).
    """
    partidos: List[Any] = list(h2h_matches or [])
    if not partidos:
        raise ValueError(
            "[LN-QBE-020-C] Sin enfrentamientos directos verificables: prohibido fabricar "
            "partidos sintéticos (Ley Zero-H2H `[LN-QBE-020-B]`)."
        )

    kappa = _kappa_para_tau(tau_dias)

    pesos: List[float] = []
    for partido in partidos:
        antiguedad = max(0.0, float(_campo(partido, "dias_antiguedad")))
        pesos.append(math.exp(-kappa * antiguedad))

    peso_total_efectivo = sum(pesos)
    if peso_total_efectivo <= 0.0:
        raise ValueError(
            f"[LN-QBE-020-C] Masa efectiva H2H no positiva ({peso_total_efectivo}): "
            "evidencia insuficiente para derivar el símplex."
        )

    masa_local = 0.0
    masa_empate = 0.0
    masa_visita = 0.0
    for peso, partido in zip(pesos, partidos):
        goles_local, goles_visita = _marcador(partido)
        if goles_local > goles_visita:
            masa_local += peso
        elif goles_local < goles_visita:
            masa_visita += peso
        else:
            masa_empate += peso

    p_local = masa_local / peso_total_efectivo
    p_empate = masa_empate / peso_total_efectivo
    p_visita = masa_visita / peso_total_efectivo
    suma_probabilidades = p_local + p_empate + p_visita

    return H2HKernelResult(
        p_local=p_local,
        p_empate=p_empate,
        p_visita=p_visita,
        suma_probabilidades=suma_probabilidades,
        peso_total_efectivo=peso_total_efectivo,
    )


def _marcador(partido: Any) -> Tuple[int, int]:
    """Extrae (goles_local, goles_visita) del enfrentamiento histórico."""
    return int(_campo(partido, "goles_local")), int(_campo(partido, "goles_visita"))
