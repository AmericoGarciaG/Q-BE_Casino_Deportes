"""
src/reporting/audit_exporter.py
================================
Modulo de Certificacion de Cartera -- Nodo IPO:
  Input  : lista de registros de portafolio + bankroll
  Process: calcula metricas QA (Kelly implicito, Poisson-edge, consistencia Dutching)
  Output : dict serializable con hash SHA-256 para certificacion forense

[GOVERNANCE] Prohibido hardcodear nombres de equipos o ligas.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any


def _kelly_fraction(prob: float, decimal_odd: float) -> float:
    if decimal_odd <= 1.0 or prob <= 0.0:
        return 0.0
    b = decimal_odd - 1.0
    return max(0.0, (prob * (b + 1) - 1) / b)


def _implied_prob(decimal_odd: float) -> float:
    if decimal_odd <= 0:
        return 0.0
    return 1.0 / decimal_odd


def generar_auditoria_portafolio(
    registros: list,
    bankroll: float,
) -> dict:
    """
    Genera el artefacto de auditoria completo para los registros del portafolio.

    Parametros
    ----------
    registros : list[dict]
        Cada elemento debe tener las claves:
        - encuentro (str)
        - estrategia (str)
        - momio_ganancia (float)
        - momio_seguro (float)
        - inversion (float)
        - prob_poisson (float)
    bankroll : float
        Bankroll total en MXN.

    Retorna
    -------
    dict con campos: timestamp, bankroll, registros_auditados, hash_sha256
    """
    if bankroll <= 0:
        raise ValueError("[AUDIT] Bankroll debe ser positivo.")
    if not registros:
        raise ValueError("[AUDIT] La lista de registros no puede estar vacia.")

    auditados = []
    total_expuesto = 0.0

    for idx, r in enumerate(registros):
        encuentro  = r.get("encuentro", f"ENCUENTRO_{idx}")
        estrategia = r.get("estrategia", "DESCONOCIDA")
        odd_win    = float(r.get("momio_ganancia", 0.0))
        odd_draw   = float(r.get("momio_seguro", 0.0))
        inversion  = float(r.get("inversion", 0.0))
        prob_model = float(r.get("prob_poisson", 0.0))

        prob_impl_win  = _implied_prob(odd_win)
        kelly_f        = _kelly_fraction(prob_model, odd_win)
        kelly_rec      = round(kelly_f * bankroll, 2)
        desviacion     = round(abs(inversion - kelly_rec), 2)
        edge           = round(prob_model - prob_impl_win, 4)
        exposicion_pct = round((inversion / bankroll) * 100, 2)
        total_expuesto += inversion

        auditados.append({
            "idx": idx + 1,
            "encuentro": encuentro,
            "estrategia": estrategia,
            "momio_ganancia": odd_win,
            "momio_seguro": odd_draw,
            "inversion_mxn": inversion,
            "prob_modelo_poisson": prob_model,
            "prob_implicita_mercado": round(prob_impl_win, 4),
            "edge_cuantitativo": edge,
            "kelly_fraccion": round(kelly_f, 4),
            "kelly_recomendado_mxn": kelly_rec,
            "desviacion_vs_kelly_mxn": desviacion,
            "exposicion_pct_bankroll": exposicion_pct,
            "estado_qa": "OK" if desviacion <= (bankroll * 0.05) else "REVISAR",
        })

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "bankroll_mxn": bankroll,
        "total_expuesto_mxn": round(total_expuesto, 2),
        "exposicion_total_pct": round((total_expuesto / bankroll) * 100, 2),
        "num_apuestas": len(auditados),
        "registros_auditados": auditados,
    }

    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    payload["hash_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload
