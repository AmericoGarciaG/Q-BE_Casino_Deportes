# -*- coding: utf-8 -*-
"""[ARCH-1.4.44 / ARCH-1.6.13-C] Lector histórico H2H gobernado (núcleo).

[ARCH-1.6.4 · Enmienda Nudo 3] El proveedor H2H deja de depender de
`scripts/utilidades/`. La lectura del plano relacional se ejecuta con SQL de
proyección explícita —sin importar `src.storage` ni el metamodelo ORM— preservando
la pureza de `src/core/sovereign/` ([ARCH-1.4.26]): cero imports de `sqlalchemy`,
del metamodelo ORM o de `src.storage`.

Contrato (idéntico al que consumía el proveedor):
* `_catalogo_clubes_3nf(sesion, league_id)` → `[{name, short_name, canonical_slug}]`
* `_precargar_historial_consumado_sqlite(sesion, league_id)` → `[{local, visitante,
  goles_local, goles_visita, fecha}]` con marcadores oficiales consumados.
* `_historial_future_blind(sesion, league_id, fecha_ref)` → subconjunto con
  `fecha < kickoff` (futuro-ceguera estricta del backfill histórico).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("H2HHistoricalLoader")


def _catalogo_clubes_3nf(sesion: Any, league_id: int) -> List[Dict[str, Any]]:
    """Identidades publicadas por el catálogo `teams`, en lectura estrictamente pasiva."""
    if sesion is None:
        return []
    filas = (
        sesion.connection()
        .exec_driver_sql(
            "SELECT name, short_name, canonical_slug FROM teams WHERE league_id = ?",
            (int(league_id),),
        )
        .mappings()
        .all()
    )
    return [
        {
            "name": fila.get("name"),
            "short_name": fila.get("short_name"),
            "canonical_slug": fila.get("canonical_slug"),
        }
        for fila in filas
    ]


def _precargar_historial_consumado_sqlite(sesion: Any, league_id: int) -> List[Dict[str, Any]]:
    """[ARCH-1.6.13-C] Marcadores oficiales consumados sellados en `fixtures_snapshots`."""
    if sesion is None:
        return []
    filas = (
        sesion.connection()
        .exec_driver_sql(
            "SELECT matches_json FROM fixtures_snapshots WHERE league_id = ?",
            (int(league_id),),
        )
        .mappings()
        .all()
    )

    historial: List[Dict[str, Any]] = []
    for fila in filas:
        crudo = fila.get("matches_json")
        if isinstance(crudo, str):
            try:
                fixtures = json.loads(crudo)
            except (TypeError, ValueError):
                continue
        else:
            fixtures = crudo or []

        for fx in fixtures:
            if not isinstance(fx, dict) or fx.get("estado") != "FINALIZADO":
                continue
            partes = str(fx.get("marcador_actual") or "").split("-")
            if len(partes) != 2 or not partes[0].strip().isdigit() or not partes[1].strip().isdigit():
                continue
            try:
                fecha_partido = datetime.fromisoformat(str(fx.get("fecha_dt")))
            except (TypeError, ValueError):
                continue
            historial.append(
                {
                    "local": fx.get("local"),
                    "visitante": fx.get("visitante"),
                    "goles_local": int(partes[0].strip()),
                    "goles_visita": int(partes[1].strip()),
                    "fecha": fecha_partido,
                }
            )
    return historial


def _historial_future_blind(
    sesion: Any, league_id: int, fecha_ref: Optional[datetime]
) -> List[Dict[str, Any]]:
    """Memoria H2H acotada al estado de conocimiento del kickoff evaluado."""
    if fecha_ref is None:
        return []
    return [
        fila
        for fila in _precargar_historial_consumado_sqlite(sesion, league_id)
        if fila.get("fecha") and fila["fecha"] < fecha_ref
    ]
