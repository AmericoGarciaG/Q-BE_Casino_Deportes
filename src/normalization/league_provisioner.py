# -*- coding: utf-8 -*-
"""
[ARCH-1.5.12] Aprovisionador JIT de Ligas y Bóveda Soberana de Activos de Clubes.
[ARCH-1.4.25] Submódulo sellado del paquete `src/normalization/` (Capa 2 — Identity Brain).
Régimen: [DIRGEN-STRICT] — Composición pura de APIs selladas, cero invención [GOVERNANCE-01].

Primitivas compuestas (jamás reimplementadas):
* `registrar_liga_descubierta_si_no_existe()` — `[ARCH-1.4.21]` (cero ligas zombis).
* Convención 3NF `Competition.id = f"FOTMOB_{fotmob_league_id}"` y `macro_gamma_home = 0.15`
  — `[ARCH-1.5.1]` / `[ARCH-1.6.19-B]`.
* μ macro desde la propiedad gobernada `League.mu_liga` — `[LN-QBE-089]` (2.65 Liga MX, 2.60 resto).
* Identidad categorizada de cada club (`[LN-QBE-095]`) y escudo por la escalera sellada
  `resolver_escudo_canonico()` (`[LN-QBE-019]`).

Cero invención de identificadores: el `Season.id` de 3NF NUNCA se fabrica; sólo se registra
si el llamador lo aporta (derivado de metadatos oficiales).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.ingestion.progol_resolver import registrar_liga_descubierta_si_no_existe
from src.normalization.asset_vault_service import (
    auditar_activo_fisico,
    es_uri_remota,
    resolver_uri_activo_local,
)
from src.normalization.gender_guards import categorizar_entidad_deportiva
from src.storage.crest_resolver import resolver_escudo_canonico
from src.storage.gateway import PersistenceGateway
from src.storage.models import Competition, Season, Team

logger = logging.getLogger("LeagueProvisioner")

# [ARCH-1.5.1] Efecto localía medio incondicional por defecto para competiciones descubiertas.
GAMMA_HOME_DEFAULT = 0.15


def provisionar_competicion_y_clubes_jit(
    fotmob_league_id: int,
    league_name: str,
    country: str,
    clubes: Optional[List[Dict[str, Any]]] = None,
    session: Optional[Session] = None,
    mu_liga: Optional[float] = None,
    season_id: Optional[str] = None,
    season_year: Optional[int] = None,
    season_name: Optional[str] = None,
) -> Dict[str, Any]:
    """[ARCH-1.5.12] Registro idempotente de liga + competición (+ temporada) + clubes.

    * Si `session` es provisto, opera en la transacción del llamador (sin commit propio).
    * Si `session` es `None`, abre una `write_transaction()` atómica del Gateway (commit/rollback).
    """
    objetivo_id = int(fotmob_league_id)
    resumen: Dict[str, Any] = {
        "fotmob_league_id": objetivo_id,
        "league_id": None,
        "competition_id": None,
        "season_id": None,
        "mu_liga_efectiva": None,
        "clubes_registrados": [],
        "clubes_actualizados": [],
        "clubes_omitidos": [],
        "activos_ancorados": [],
        "activos_pendientes": [],
    }

    def _ejecutar(tx: Session) -> Dict[str, Any]:
        ahora = datetime.now(timezone.utc).replace(tzinfo=None)

        # 1. Liga base: API sellada [ARCH-1.4.21] (idempotente por `fotmob_id`).
        datos_liga: Dict[str, Any] = {
            "fotmob_league_id": objetivo_id,
            "league_name": str(league_name or "").strip() or f"Liga FotMob {objetivo_id}",
            "country": str(country or "").strip() or "Internacional",
        }
        if mu_liga is not None:
            datos_liga["mu_liga"] = float(mu_liga)
        liga = registrar_liga_descubierta_si_no_existe(tx, datos_liga)
        resumen["league_id"] = liga.id

        # 2. Competición 3NF + parámetros macro gobernados [LN-QBE-089] / [ARCH-1.5.1].
        mu_efectiva = float(mu_liga) if mu_liga is not None else float(liga.mu_liga)
        comp_id = f"FOTMOB_{objetivo_id}"
        competicion = tx.query(Competition).filter(Competition.id == comp_id).first()
        if competicion is None:
            competicion = Competition(
                id=comp_id,
                name=datos_liga["league_name"],
                country=datos_liga["country"],
                macro_mu_liga=mu_efectiva,
                macro_gamma_home=GAMMA_HOME_DEFAULT,
                created_at=ahora,
            )
            tx.add(competicion)
        else:
            competicion.name = datos_liga["league_name"]
            competicion.country = datos_liga["country"]
            competicion.macro_mu_liga = mu_efectiva
            competicion.macro_gamma_home = GAMMA_HOME_DEFAULT
        tx.flush()
        resumen["competition_id"] = comp_id
        resumen["mu_liga_efectiva"] = mu_efectiva
        # 3. Temporada 3NF: SÓLO si el llamador aporta el identificador oficial (cero invención).
        if season_id:
            id_temporada = str(season_id).strip()
            temporada = tx.query(Season).filter(Season.id == id_temporada).first()
            if temporada is None:
                temporada = Season(
                    id=id_temporada,
                    competition_id=comp_id,
                    year=int(season_year or datetime.now(timezone.utc).year),
                    name=str(season_name or id_temporada),
                    created_at=ahora,
                )
                tx.add(temporada)
            else:
                temporada.competition_id = comp_id
                if season_year is not None:
                    temporada.year = int(season_year)
                if season_name:
                    temporada.name = str(season_name)
            tx.flush()
            resumen["season_id"] = id_temporada

        # 4. Clubes: identidad categorizada [LN-QBE-095] + bóveda soberana [ARCH-1.5.12].
        for club in clubes or []:
            crudo_id = club.get("fotmob_team_id")
            if crudo_id is None:
                resumen["clubes_omitidos"].append(str(club.get("name") or "SIN_FOTMOB_ID"))
                continue
            fotmob_team_id = int(crudo_id)
            nombre_crudo = str(club.get("name") or club.get("team_name") or "").strip()
            if not nombre_crudo:
                resumen["clubes_omitidos"].append(str(fotmob_team_id))
                continue

            entidad = categorizar_entidad_deportiva(nombre_crudo)
            slug = entidad.canonical_slug

            auditoria = auditar_activo_fisico(slug, tipo="team")
            if auditoria["valido"]:
                crest_url = resolver_uri_activo_local(slug, tipo="team")
                resumen["activos_ancorados"].append(slug)
            else:
                resumen["activos_pendientes"].append(slug)
                crest_url = ""
                semilla = str(club.get("crest_url") or "").strip()
                if semilla and not es_uri_remota(semilla):
                    crest_url = semilla  # Sólo rutas locales/Data-URI: anti-hotlinking.
                if not crest_url:
                    # [LN-QBE-095] + ALT-1 (VAR-2026-LN-QBE-019-CATEGORY-AWARE-CREST): la escalera
                    # sellada recibe la CATEGORÍA de la entidad; para ramas no neutras exige primero
                    # el activo categorizado y degrada de forma gobernada al activo plano.
                    crest_url = resolver_escudo_canonico(
                        entidad.canonical_name,
                        fotmob_id=fotmob_team_id,
                        db=tx,
                        categoria=entidad.category,
                    )

            fila = tx.query(Team).filter(Team.fotmob_team_id == fotmob_team_id).first()
            if fila is None:
                tx.add(Team(
                    league_id=liga.id,
                    fotmob_team_id=fotmob_team_id,
                    name=entidad.canonical_name,
                    short_name=str(club.get("short_name") or entidad.canonical_name)[:60],
                    canonical_slug=slug,
                    crest_url=crest_url,
                    created_at=ahora,
                ))
                resumen["clubes_registrados"].append(slug)
            else:
                fila.league_id = liga.id
                fila.name = entidad.canonical_name
                fila.canonical_slug = slug
                if crest_url:
                    fila.crest_url = crest_url
                resumen["clubes_actualizados"].append(slug)

        tx.flush()
        return resumen

    if session is not None:
        return _ejecutar(session)

    with PersistenceGateway().write_transaction() as tx:
        resultado = _ejecutar(tx)
    logger.info(
        "🏛️ [ARCH-1.5.12] Aprovisionamiento JIT consumado: %s (FotMob %s) — %d clubes registrados.",
        resultado["competition_id"], objetivo_id, len(resultado["clubes_registrados"]),
    )
    return resultado

