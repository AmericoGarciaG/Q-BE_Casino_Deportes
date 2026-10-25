# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [ARCH-1.4.73] / [LN-QBE-133] — Ingesta Histórica Masiva de FotMob
Base de Gobierno: docs/ARCH.md [ARCH-1.4.73] / docs/LOGIC.md [LN-QBE-133]
Régimen: [DIRGEN-STRICT] — Inmutable, cero mocks, base SQLite real y efímera.

Los tres jueces certifican:
  1. El parser del `__NEXT_DATA__` de una temporada antigua (2015/16) reconoce los
     fixtures y la telemetría con la estructura moderna, sin depender de la red.
  2. La persistencia es idempotente: dos pasadas sobre la misma temporada no duplican
     filas en `matches` ni en `match_telemetry`.
  3. Un club extinto o sin alias canónico se marca explícitamente `unmapped` y se
     excluye del upsert, preservando la integridad foránea.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator, List

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.storage.database import Base
from src.storage.models import Competition, Match, MatchTelemetry, Season

from scripts.ingesta.ingestar_historico_fotmob import (
    parsear_next_data,
    persistir_partidos,
    resolver_equipo,
)


# ── Utilidades del Juez ───────────────────────────────────────────────────────────────────────
def _entrada_stats(posesion: List[int], sot: List[int], xg: List[Any]) -> Dict[str, Any]:
    """Construye el bloque `content.stats.Periods.All` con la forma moderna de FotMob."""
    return {
        "content": {
            "stats": {
                "Periods": {
                    "All": {
                        "stats": [
                            {
                                "title": "Top stats",
                                "stats": [
                                    {
                                        "key": "BallPossesion",
                                        "title": "Ball possession",
                                        "stats": posesion,
                                        "rawStats": [{"value": p} for p in posesion],
                                    },
                                    {
                                        "key": "ShotsOnTarget",
                                        "title": "Shots on target",
                                        "stats": sot,
                                        "rawStats": [{"value": s} for s in sot],
                                    },
                                    {
                                        "key": "expected_goals",
                                        "title": "Expected goals (xG)",
                                        "stats": [str(x) for x in xg],
                                        "rawStats": [{"value": x} for x in xg],
                                    },
                                ],
                            }
                        ]
                    }
                }
            }
        }
    }


def _partido(
    match_id: int,
    jornada: str,
    local: str,
    visitante: str,
    goles_local: int,
    goles_visita: int,
    utc: str,
    *,
    terminado: bool = True,
) -> Dict[str, Any]:
    return {
        "id": match_id,
        "round": jornada,
        "home": {"id": 1, "name": local},
        "away": {"id": 2, "name": visitante},
        "status": {
            "finished": terminado,
            "scoreStr": f"{goles_local} - {goles_visita}",
            "utcTime": utc,
        },
    }


def _next_data(partidos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Simula el `__NEXT_DATA__` de la página de liga con pageProps reales."""
    return {
        "props": {
            "pageProps": {
                "details": {
                    "id": 230,
                    "name": "Liga MX",
                    "selectedSeason": "2015/2016 - Apertura",
                },
                "allAvailableSeasons": [
                    "2015/2016 - Clausura",
                    "2015/2016 - Apertura",
                ],
                "fixtures": {"allMatches": partidos},
            }
        }
    }


def _payload_temporada_2015() -> Dict[str, Any]:
    """Dos partidos válidos y uno no terminado, con telemetría moderna completa."""
    partidos = [
        _partido(1984280, "5", "Tigres", "Pumas", 4, 1, "2015-08-16T00:05:00.000Z"),
        _partido(1984281, "6", "Toluca", "Cruz Azul", 2, 2, "2015-08-23T00:00:00.000Z"),
        _partido(1984282, "7", "Puebla", "Atlas", 0, 0, "2015-08-30T00:00:00.000Z", terminado=False),
    ]
    detalles = {
        "1984280": _entrada_stats([58, 42], [6, 4], [1.8, 0.9]),
        "1984281": _entrada_stats([45, 55], [3, 5], [0.8, 1.2]),
    }
    return {"next_data": _next_data(partidos), "detalles": detalles}


def _payload_extintos() -> Dict[str, Any]:
    """Dos partidos con clubes que [LN-QBE-012] no puede resolver."""
    partidos = [
        _partido(2140941, "1/4", "Monarcas Morelia", "Tigres", 0, 1, "2015-11-29T00:00:00.000Z"),
        _partido(2140942, "1/4", "Jaguares de Chiapas", "Pumas", 1, 1, "2015-11-29T00:00:00.000Z"),
    ]
    return {"next_data": _next_data(partidos), "detalles": {}}


@pytest.fixture()
def fabrica_sesiones() -> Iterator[sessionmaker]:
    """Base SQLite real en memoria (StaticPool) con la competición canónica sembrada."""
    motor = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(motor)
    fabrica = sessionmaker(bind=motor, autocommit=False, autoflush=False, expire_on_commit=False)
    with fabrica() as sesion:
        sesion.add(Competition(id="MEX_LIGAMX", name="Liga MX", country="México"))
        sesion.commit()
    try:
        yield fabrica
    finally:
        motor.dispose()


@contextmanager
def _sesion(fabrica: sessionmaker) -> Iterator[Session]:
    sesion = fabrica()
    try:
        yield sesion
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()


# ── Juez 1: estructura histórica ─────────────────────────────────────────────────────────────
def test_extraccion_temporada_antigua():
    """El parser reconoce fixtures y telemetría de 2015/16 con la estructura moderna."""
    payload = _payload_temporada_2015()
    partidos = parsear_next_data(payload["next_data"], payload["detalles"])

    assert len(partidos) == 2, "Solo deben sobrevivir los dos partidos terminados."

    primero = partidos[0]
    assert primero["match_id"] == "FOTMOB-1984280"
    assert primero["season_id"] == "MEX_2015_2016_APERTURA"
    assert primero["jornada"] == 5
    assert primero["home_team_slug"] == "tigres-uanl"
    assert primero["away_team_slug"] == "pumas-unam"
    assert (primero["score_home"], primero["score_away"]) == (4, 1)
    assert primero["status"] == "FINISHED"
    assert primero["kickoff_utc"] is not None
    assert primero["estado_identidad"] == "OK"

    telemetria = {fila["team_slug"]: fila for fila in primero["telemetria"]}
    assert set(telemetria) == {"tigres-uanl", "pumas-unam"}
    local, visita = telemetria["tigres-uanl"], telemetria["pumas-unam"]
    assert local["possession_pct"] == 58.0
    assert local["sot"] == 6.0 and local["sota"] == 4.0
    assert local["xg"] == pytest.approx(1.8) and local["xga"] == pytest.approx(0.9)
    assert visita["possession_pct"] == 42.0
    assert visita["sot"] == 4.0 and visita["sota"] == 6.0
    assert visita["xg"] == pytest.approx(0.9) and visita["xga"] == pytest.approx(1.8)
    assert local["possession_pct"] + visita["possession_pct"] == 100.0

    segundo = partidos[1]
    assert segundo["match_id"] == "FOTMOB-1984281"
    assert (segundo["score_home"], segundo["score_away"]) == (2, 2)
    assert len(segundo["telemetria"]) == 2


# ── Juez 2: idempotencia ─────────────────────────────────────────────────────────────────────
def test_idempotencia_ingesta(fabrica_sesiones):
    """Dos pasadas sobre la misma temporada no duplican `matches` ni `match_telemetry`."""
    payload = _payload_temporada_2015()
    partidos = parsear_next_data(payload["next_data"], payload["detalles"])

    with _sesion(fabrica_sesiones) as sesion:
        primera = persistir_partidos(sesion, partidos)
    assert primera["matches_insertados"] == 2
    assert primera["telemetria_insertadas"] == 4

    with _sesion(fabrica_sesiones) as sesion:
        segunda = persistir_partidos(sesion, partidos)
    assert segunda["matches_insertados"] == 0
    assert segunda["matches_actualizados"] == 2
    assert segunda["telemetria_insertadas"] == 0
    assert segunda["telemetria_actualizadas"] == 4

    with _sesion(fabrica_sesiones) as sesion:
        total_matches = sesion.execute(select(func.count()).select_from(Match)).scalar_one()
        total_telemetria = sesion.execute(select(func.count()).select_from(MatchTelemetry)).scalar_one()
        total_temporadas = sesion.execute(select(func.count()).select_from(Season)).scalar_one()
        ids = sesion.execute(select(Match.id).order_by(Match.id)).scalars().all()

    assert total_matches == 2, "La segunda pasada no puede duplicar partidos."
    assert total_telemetria == 4, "La segunda pasada no puede duplicar telemetría."
    assert total_temporadas == 1, "La temporada debe resolverse por PK, no duplicarse."
    assert len(ids) == len(set(ids)) == 2


# ── Juez 3: clubes extintos / sin alias ───────────────────────────────────────────────────────
def test_mapeo_equipos_historicos(fabrica_sesiones):
    """Morelia y Jaguares caen explícitamente en `unmapped` y no rompen la FK."""
    canonico, slug, error = resolver_equipo("Tigres")
    assert error is None
    assert canonico == "Tigres UANL"
    assert slug == "tigres-uanl"

    for nombre in ("Monarcas Morelia", "Jaguares de Chiapas"):
        canonico, slug, error = resolver_equipo(nombre)
        assert canonico is None and slug is None
        assert error, f"'{nombre}' debe declarar el fallo de normalización."

    payload = _payload_extintos()
    partidos = parsear_next_data(payload["next_data"], payload["detalles"])
    assert len(partidos) == 2
    assert all(partido["estado_identidad"] == "UNMAPPED" for partido in partidos)
    nombres_unmapped = {nombre for partido in partidos for nombre in partido["unmapped"]}
    assert "Monarcas Morelia" in nombres_unmapped
    assert "Jaguares de Chiapas" in nombres_unmapped
    assert all(partido["home_team_slug"] is None for partido in partidos)

    with _sesion(fabrica_sesiones) as sesion:
        contadores = persistir_partidos(sesion, partidos)

    assert contadores["omitidos"] == 2
    assert contadores["matches_insertados"] == 0
    assert contadores["telemetria_insertadas"] == 0

    with _sesion(fabrica_sesiones) as sesion:
        total_matches = sesion.execute(select(func.count()).select_from(Match)).scalar_one()
        total_telemetria = sesion.execute(select(func.count()).select_from(MatchTelemetry)).scalar_one()

    assert total_matches == 0, "Un club `unmapped` no puede dejar una FK rota ni una fila huérfana."
    assert total_telemetria == 0
