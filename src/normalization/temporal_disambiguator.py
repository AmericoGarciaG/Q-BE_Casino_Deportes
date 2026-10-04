# -*- coding: utf-8 -*-
"""
[LN-QBE-094] Algoritmo de Desambiguación Temporal en Ventana Crítica [t_cierre ± 72h].
[ARCH-1.4.25] Submódulo sellado del paquete `src/normalization/` (Capa 2 — Identity Brain).
Régimen: [DIRGEN-STRICT] — Algoritmo protegido [ALGO-PROTECTED]; transcripción exacta del
plano canónico de `docs/LOGIC.md` (nodo [LN-QBE-094]). Cero margen creativo.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Sequence, Tuple

from src.ingestion.normalizer import canonicalize_team_name
from src.ingestion.schemas import DisambiguatedMatchDTO, ScheduledMatchDTO

logger = logging.getLogger("TemporalDisambiguator")

# [LN-QBE-094].P.1 — Ventana Crítica de Disputa W = [t_cierre − 24 h, t_cierre + 72 h].
VENTANA_HORAS_PREVIA = 24
VENTANA_HORAS_POSTERIOR = 72


def _a_utc(valor: datetime) -> datetime:
    """Normaliza a UTC consciente; un `kickoff_utc` naive se interpreta como UTC."""
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def _mismo_club(nombre_a: str, nombre_b: str) -> bool:
    """Cotejo de identidad por normalizador canónico sellado ([LN-QBE-012])."""
    canonico_a = canonicalize_team_name(str(nombre_a or ""))
    canonico_b = canonicalize_team_name(str(nombre_b or ""))
    return bool(canonico_a) and canonico_a == canonico_b


def _participa(candidato: ScheduledMatchDTO, team_a: str, team_b: str) -> bool:
    """Verdadero si AMBOS clubes participan, en cualquier orden de localía."""
    local = getattr(candidato, "home_team", "")
    visitante = getattr(candidato, "away_team", "")
    directo = _mismo_club(local, team_a) and _mismo_club(visitante, team_b)
    invertido = _mismo_club(local, team_b) and _mismo_club(visitante, team_a)
    return bool(directo or invertido)


def desambiguar_partido_por_ventana(
    team_a: str,
    team_b: str,
    t_cierre: datetime,
    candidatos: Sequence[ScheduledMatchDTO],
) -> Optional[DisambiguatedMatchDTO]:
    """[LN-QBE-094] Pasos 1–5 legislados. Devuelve `None` (no indexado) si W está vacía.

    * |M| == 1 → vínculo unívoco con su `competition_id` (`is_ambiguous=False`).
    * |M| > 1  → `argmin |m.t_kickoff − t_cierre|` (`is_ambiguous=True`: hubo pluralidad).
    * |M| == 0 → `None`: degradación al Prior Fiduciario `[LN-QBE-075]`.
    """
    cierre = _a_utc(t_cierre)
    limite_inferior = cierre - timedelta(hours=VENTANA_HORAS_PREVIA)
    limite_superior = cierre + timedelta(hours=VENTANA_HORAS_POSTERIOR)

    admisibles: List[Tuple[timedelta, datetime, ScheduledMatchDTO]] = []
    for candidato in candidatos or []:
        kickoff = getattr(candidato, "kickoff_utc", None)
        if kickoff is None or not _participa(candidato, team_a, team_b):
            continue
        kickoff_utc = _a_utc(kickoff)
        if limite_inferior <= kickoff_utc <= limite_superior:
            admisibles.append((abs(kickoff_utc - cierre), kickoff_utc, candidato))

    if not admisibles:
        logger.warning(
            "[LN-QBE-094] Ventana crítica vacía para %s vs %s: partido NO indexado; "
            "se degrada al Prior Fiduciario [LN-QBE-075].", team_a, team_b,
        )
        return None

    admisibles.sort(key=lambda item: item[0])
    _, kickoff_utc, elegido = admisibles[0]

    return DisambiguatedMatchDTO(
        match_id=str(getattr(elegido, "match_id", "")),
        competition_id=getattr(elegido, "tournament_id", None),
        kickoff_utc=kickoff_utc,
        is_ambiguous=len(admisibles) > 1,
    )
