# -*- coding: utf-8 -*-
"""
Q-BE CD WEB — EXTRACTOR HISTÓRICO MASIVO DE FOTMOB
[ARCH-1.4.73] / [LN-QBE-133] Ingesta fáctica profunda 2010/11 → actualidad.

Régimen: [HÍBRIDO DUAL-TRACK]
  · [DBBD-FUNGIBLE] — transporte, parser, CLI y reporte.
  · [DIRGEN-STRICT] — `PersistenceGateway` y `[LN-QBE-012]` se INVOCAN sin modificar;
    la escritura ocurre dentro de `write_transaction()` y la identidad se resuelve con
    el normalizador canónico. `src/` permanece intacto.

Axiomas operativos
------------------
1. **Cero datos inventados.** Una métrica ausente se escribe `NULL` o se omite; jamás se
   sustituye por `0.0`, `50.0` o un marcador fabricado. Si el bloque de stats no existe,
   el partido entra con resultado y se declara `sin_telemetria`.
2. **Identidad fail-loud.** Un club que `[LN-QBE-012]` no resuelve se marca `UNMAPPED`,
   se excluye del upsert y se reporta con su nombre crudo. No se insertan slugs crudos.
3. **Idempotencia.** `matches` se llavea por `FOTMOB-<matchId>`; `match_telemetry` por
   `(match_id, team_slug)`; `seasons` por PK. Dos corridas no duplican filas.
4. **Una transacción por temporada.** La persistencia usa `PersistenceGateway.write_transaction()`;
   cualquier excepción revierte la temporada completa.
5. **Estructura desconocida = Alto al Fuego.** Si el `__NEXT_DATA__` no porta
   `props.pageProps.fixtures.allMatches`, se lanza `ValueError`; no se adivina.

Uso
---
    python -m scripts.ingesta.ingestar_historico_fotmob --temporada 2015-2016 --dry-run
    python -m scripts.ingesta.ingestar_historico_fotmob --temporada 2015-2016
    python -m scripts.ingesta.ingestar_historico_fotmob --desde 2010 --hasta 2026 --json
    python -m scripts.ingesta.ingestar_historico_fotmob --temporada 2018/2019\\ -\\ Apertura --telemetria si
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from src.ingestion.normalizer import NormalizationException, canonicalize_team_name
from src.storage.crest_resolver import obtener_slug_club
from src.storage.gateway import PersistenceGateway
from src.storage.models import Match, MatchTelemetry, Season

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IngestaHistoricoFotMob")

LIGA_FOTMOB_ID = 230
COMPETITION_ID = "MEX_LIGAMX"
URL_OVERVIEW = "https://www.fotmob.com/leagues/230/overview/liga-mx"
URL_TEMPORADA = "https://www.fotmob.com/leagues/230/overview/liga-mx?season={temporada}"
URL_PARTIDO = "https://www.fotmob.com/api/data/matchDetails?matchId={match_id}"
RUTA_HISTORICO_DEFAULT = os.path.join("data", "qbe_historico.db")
CABECERAS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Referer": "https://www.fotmob.com/",
}
CLAVES_POSESION = ("BallPossesion", "BallPossession", "ball_possession")
CLAVES_SOT = ("ShotsOnTarget", "shots_on_target")
CLAVES_XG = ("expected_goals", "Expected goals (xG)", "xg")
UMBRAL_TELEMETRIA = 2018


# ═════════════════════════════════════════════════════════════════════════════════════════════
# TRANSPORTE
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _descargar_texto(
    url: str, *, timeout: float = 30.0, reintentos: int = 3, espera: float = 1.0
) -> str:
    """GET de texto con reintentos acotados; agota los intentos ⇒ `RuntimeError`."""
    ultimo_error: Optional[Exception] = None
    for intento in range(1, max(1, reintentos) + 1):
        try:
            peticion = Request(url, headers=CABECERAS_HTTP)
            with urlopen(peticion, timeout=timeout) as respuesta:
                return respuesta.read().decode("utf-8", "replace")
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            ultimo_error = error
            if intento < reintentos:
                pausa = espera * intento
                logger.warning(
                    "⚠️  [RED] %s (intento %d/%d) · reintento en %.1fs",
                    type(error).__name__, intento, reintentos, pausa,
                )
                time.sleep(pausa)
    raise RuntimeError(f"No se pudo descargar {url}: {ultimo_error}") from ultimo_error


def _descargar_json(url: str, **kwargs: Any) -> Dict[str, Any]:
    """GET JSON con la misma política de reintentos."""
    texto = _descargar_texto(url, **kwargs)
    try:
        return json.loads(texto)
    except ValueError as error:
        raise RuntimeError(f"Respuesta JSON inválida de {url}: {error}") from error


# ═════════════════════════════════════════════════════════════════════════════════════════════
# PARSER PURO
# ═════════════════════════════════════════════════════════════════════════════════════════════
def extraer_next_data(html: str) -> Dict[str, Any]:
    """Extrae y valida el bloque `<script id="__NEXT_DATA__">` de la página de liga."""
    coincidencia = re.search(
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        str(html or ""),
        re.DOTALL,
    )
    if not coincidencia:
        raise ValueError("La página no publica `__NEXT_DATA__`; Alto al Fuego estructural.")
    try:
        return json.loads(coincidencia.group(1))
    except ValueError as error:
        raise ValueError(f"`__NEXT_DATA__` no es JSON válido: {error}") from error


def _a_numero(valor: Any) -> Optional[float]:
    """Conversión estricta a número; `None` para cualquier valor no legible."""
    if isinstance(valor, bool) or valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, dict):
        return _a_numero(valor.get("value"))
    if isinstance(valor, str):
        limpio = valor.strip().replace("%", "").replace(",", ".")
        try:
            return float(limpio)
        except ValueError:
            return None
    return None


def _a_entero(valor: Any) -> Optional[int]:
    """Entero legible (admite `'1/4'` extrayendo el primer entero)."""
    numero = _a_numero(valor)
    if numero is not None:
        return int(round(numero))
    if isinstance(valor, str):
        coincidencia = re.search(r"\d+", valor)
        if coincidencia:
            return int(coincidencia.group(0))
    return None


def _fecha_utc(texto: Any) -> Optional[datetime]:
    """ISO-8601 de FotMob → `datetime` UTC naive (la columna 3NF no porta zona)."""
    if not texto:
        return None
    try:
        fecha = datetime.fromisoformat(str(texto).replace("Z", "+00:00"))
    except ValueError:
        return None
    if fecha.tzinfo is not None:
        fecha = fecha.astimezone(timezone.utc).replace(tzinfo=None)
    return fecha


def _marcador(entrada: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    """Marcador terminal: `scoreStr` → `home.score`/`away.score`; `(None, None)` si no existe."""
    estado = entrada.get("status") or {}
    texto = str(estado.get("scoreStr") or "")
    coincidencia = re.search(r"(\d+)\s*-\s*(\d+)", texto)
    if coincidencia:
        return int(coincidencia.group(1)), int(coincidencia.group(2))
    local = _a_entero((entrada.get("home") or {}).get("score"))
    visita = _a_entero((entrada.get("away") or {}).get("score"))
    return local, visita


def _temporada_canonica(etiqueta: str) -> Tuple[str, int, str]:
    """`'2015/2016 - Apertura'` → `(MEX_2015_2016_APERTURA, 2015, 'Apertura 2015/2016')`."""
    coincidencia = re.search(
        r"(?P<inicio>\d{4})\s*/\s*(?P<fin>\d{4})\s*-\s*(?P<fase>Apertura|Clausura)",
        str(etiqueta or ""),
        re.IGNORECASE,
    )
    if not coincidencia:
        raise ValueError(f"Etiqueta de temporada no reconocida: '{etiqueta}'")
    inicio = int(coincidencia.group("inicio"))
    fin = int(coincidencia.group("fin"))
    fase = coincidencia.group("fase").capitalize()
    season_id = f"MEX_{inicio}_{fin}_{fase.upper()}"
    return season_id, inicio, f"{fase} {inicio}/{fin}"


def resolver_equipo(nombre: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Resuelve identidad con `[LN-QBE-012]`; devuelve `(canónico, slug, error)`."""
    if not nombre:
        return None, None, "nombre vacío"
    try:
        canonico = canonicalize_team_name(nombre)
        slug = obtener_slug_club(canonico)
        if not slug:
            return None, None, f"slug vacío para '{canonico}'"
        return canonico, str(slug), None
    except NormalizationException as error:
        return None, None, str(error)
    except Exception as error:  # aduana de identidad: cualquier fallo es `unmapped`
        return None, None, f"{type(error).__name__}: {error}"


def _plano_stats(detalle: Dict[str, Any]) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
    """Aplana `content.stats.Periods.All.stats` a `{clave: (local, visita)}`."""
    stats = (detalle.get("content") or {}).get("stats")
    if not isinstance(stats, dict):
        stats = detalle.get("stats")
    if not isinstance(stats, dict):
        return {}
    periods = stats.get("Periods") or {}
    all_period = periods.get("All") or {}
    grupos = all_period.get("stats")
    if not isinstance(grupos, list):
        return {}

    plano: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
    for grupo in grupos:
        if not isinstance(grupo, dict):
            continue
        for entrada in grupo.get("stats") or []:
            if not isinstance(entrada, dict):
                continue
            clave = str(entrada.get("key") or "").strip()
            if not clave:
                continue
            valores = entrada.get("stats")
            crudos = entrada.get("rawStats")
            pares: List[Optional[float]] = []
            for indice in (0, 1):
                valor = None
                if isinstance(crudos, list) and len(crudos) > indice:
                    valor = _a_numero(crudos[indice])
                if valor is None and isinstance(valores, list) and len(valores) > indice:
                    valor = _a_numero(valores[indice])
                pares.append(valor)
            par = (pares[0], pares[1])
            anterior = plano.get(clave)
            if anterior is None or all(valor is None for valor in anterior):
                plano[clave] = par
    return plano


def _buscar_par(
    plano: Dict[str, Tuple[Optional[float], Optional[float]]], claves: Iterable[str]
) -> Optional[Tuple[Optional[float], Optional[float]]]:
    for clave in claves:
        if clave in plano:
            return plano[clave]
    return None


def _telemetria_de_detalle(
    detalle: Optional[Dict[str, Any]],
    home_slug: str,
    away_slug: str,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Traduce `matchDetails` a dos filas de `match_telemetry` o declara el motivo."""
    if not isinstance(detalle, dict):
        return [], "sin payload matchDetails"
    plano = _plano_stats(detalle)
    if not plano:
        return [], "sin bloque content.stats.Periods.All"

    posesion = _buscar_par(plano, CLAVES_POSESION)
    sot = _buscar_par(plano, CLAVES_SOT)
    if posesion is None:
        return [], "sin BallPossesion"
    if sot is None:
        return [], "sin ShotsOnTarget"

    pos_h, pos_a = posesion
    sot_h, sot_a = sot
    if None in (pos_h, pos_a, sot_h, sot_a):
        return [], "posesión/SoT no numéricos"
    if not (0.0 <= pos_h <= 100.0 and 0.0 <= pos_a <= 100.0):
        return [], f"posesión fuera de [0,100]: {pos_h}/{pos_a}"
    if abs((pos_h + pos_a) - 100.0) > 0.01:
        return [], f"posesión no bipartita: {pos_h}+{pos_a}={pos_h + pos_a}"
    if min(sot_h, sot_a) < 0:
        return [], f"SoT negativos: {sot_h}/{sot_a}"

    xg = _buscar_par(plano, CLAVES_XG) or (None, None)
    xg_h, xg_a = xg
    if xg_h is not None and xg_h < 0:
        xg_h = None
    if xg_a is not None and xg_a < 0:
        xg_a = None
    # La reciprocidad defensiva es una identidad de conjunto: xGA_local ≡ xG_visita.
    return (
        [
            {
                "team_slug": home_slug,
                "possession_pct": float(pos_h),
                "sot": float(sot_h),
                "sota": float(sot_a),
                "xg": xg_h,
                "xga": xg_a,
            },
            {
                "team_slug": away_slug,
                "possession_pct": float(pos_a),
                "sot": float(sot_a),
                "sota": float(sot_h),
                "xg": xg_a,
                "xga": xg_h,
            },
        ],
        None,
    )


def _parsear_fixture(
    entrada: Dict[str, Any],
    temporada: str,
    detalles: Optional[Dict[str, Dict[str, Any]]],
) -> Optional[Dict[str, Any]]:
    """Traduce un fixture terminado a un registro canónico (incluye `UNMAPPED`)."""
    if not isinstance(entrada, dict):
        return None
    estado = entrada.get("status") or {}
    if not bool(estado.get("finished")):
        return None

    fotmob_id = str(entrada.get("id") or "").strip()
    if not fotmob_id:
        return None
    home_nombre = str((entrada.get("home") or {}).get("name") or "").strip()
    away_nombre = str((entrada.get("away") or {}).get("name") or "").strip()
    goles_local, goles_visita = _marcador(entrada)

    season_id, season_year, season_name = _temporada_canonica(temporada)
    home_canonico, home_slug, home_error = resolver_equipo(home_nombre)
    away_canonico, away_slug, away_error = resolver_equipo(away_nombre)
    unmapped = [nombre for nombre, error in ((home_nombre, home_error), (away_nombre, away_error)) if error]
    estado_identidad = "OK" if not unmapped else "UNMAPPED"

    telemetria: List[Dict[str, Any]] = []
    motivo_telemetria: Optional[str] = "sin identidad canónica" if unmapped else "sin matchDetails"
    if estado_identidad == "OK" and detalles is not None:
        telemetria, motivo_telemetria = _telemetria_de_detalle(
            detalles.get(fotmob_id), str(home_slug), str(away_slug)
        )

    return {
        "match_id": f"FOTMOB-{fotmob_id}",
        "fotmob_match_id": fotmob_id,
        "temporada": temporada,
        "season_id": season_id,
        "season_year": season_year,
        "season_name": season_name,
        "jornada": _a_entero(entrada.get("round") or entrada.get("roundName")),
        "kickoff_utc": _fecha_utc(estado.get("utcTime")),
        "home_nombre": home_nombre,
        "away_nombre": away_nombre,
        "home_canonico": home_canonico,
        "away_canonico": away_canonico,
        "home_team_slug": home_slug,
        "away_team_slug": away_slug,
        "score_home": goles_local,
        "score_away": goles_visita,
        "status": "FINISHED",
        "estado_identidad": estado_identidad,
        "unmapped": unmapped,
        "telemetria": telemetria,
        "motivo_telemetria": motivo_telemetria,
    }


def parsear_next_data(
    payload: Any,
    detalles: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Parser puro del `__NEXT_DATA__`: devuelve fixtures terminados canónicos.

    Args:
        payload: JSON del `__NEXT_DATA__` (dict) o el HTML completo de la página.
        detalles: `{fotmob_match_id: matchDetails}`; si falta, el partido queda sin telemetría.

    Raises:
        ValueError: si no existe `props.pageProps.fixtures.allMatches` o la temporada no
            es reconocible. Es un fallo estructural, no una ausencia de datos.
    """
    if isinstance(payload, str):
        payload = extraer_next_data(payload)
    if not isinstance(payload, dict):
        raise ValueError("`__NEXT_DATA__` no es un objeto JSON.")

    page_props = (payload.get("props") or {}).get("pageProps") or {}
    fixtures = (page_props.get("fixtures") or {}).get("allMatches")
    if not isinstance(fixtures, list):
        raise ValueError("`props.pageProps.fixtures.allMatches` ausente; Alto al Fuego estructural.")

    details = page_props.get("details") or {}
    temporada = str(details.get("selectedSeason") or (page_props.get("overview") or {}).get("selectedSeason") or "")
    if not temporada:
        raise ValueError("`props.pageProps.details.selectedSeason` ausente.")
    _temporada_canonica(temporada)  # valida la etiqueta antes de iterar

    partidos: List[Dict[str, Any]] = []
    for entrada in fixtures:
        registro = _parsear_fixture(entrada, temporada, detalles)
        if registro is not None:
            partidos.append(registro)
    return partidos


# ═════════════════════════════════════════════════════════════════════════════════════════════
# PERSISTENCIA 3NF (sin commit: el commit lo pone `write_transaction`)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def persistir_partidos(sesion: Session, partidos: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    """Upsert de `seasons`, `matches` y `match_telemetry`; el llamador hace commit.

    Es idempotente por `match_id` y por `(match_id, team_slug)`. Los registros `UNMAPPED`
    se omiten antes de tocar la 3NF para no romper las FK.
    """
    contadores = {
        "temporadas_insertadas": 0,
        "matches_insertados": 0,
        "matches_actualizados": 0,
        "telemetria_insertadas": 0,
        "telemetria_actualizadas": 0,
        "omitidos": 0,
        "unmapped": 0,
    }

    for registro in partidos:
        estado_identidad = str(registro.get("estado_identidad") or "")
        if estado_identidad != "OK":
            contadores["omitidos"] += 1
            if estado_identidad == "UNMAPPED":
                contadores["unmapped"] += 1
            continue

        season_id = str(registro["season_id"])
        temporada = sesion.get(Season, season_id)
        if temporada is None:
            temporada = Season(
                id=season_id,
                competition_id=COMPETITION_ID,
                year=int(registro["season_year"]),
                name=str(registro["season_name"]),
            )
            sesion.add(temporada)
            # La FK `matches.season_id` exige que la temporada exista antes del partido;
            # el flush explícito fija el orden sin depender del grafo implícito del ORM.
            sesion.flush()
            contadores["temporadas_insertadas"] += 1

        match_id = str(registro["match_id"])
        partido = sesion.get(Match, match_id)
        if partido is None:
            partido = Match(id=match_id, competition_id=COMPETITION_ID)
            sesion.add(partido)
            contadores["matches_insertados"] += 1
        else:
            contadores["matches_actualizados"] += 1

        partido.season_id = season_id
        partido.matchday_num = registro.get("jornada")
        partido.kickoff_utc = registro.get("kickoff_utc")
        partido.home_team_slug = str(registro["home_team_slug"])
        partido.away_team_slug = str(registro["away_team_slug"])
        partido.status = "FINISHED"
        partido.score_home = registro.get("score_home")
        partido.score_away = registro.get("score_away")

        vistos: set = set()
        for fila in registro.get("telemetria") or []:
            team_slug = str(fila.get("team_slug") or "").strip()
            if not team_slug or team_slug in vistos:
                continue
            vistos.add(team_slug)
            telemetria = sesion.get(MatchTelemetry, (match_id, team_slug))
            if telemetria is None:
                telemetria = MatchTelemetry(match_id=match_id, team_slug=team_slug)
                sesion.add(telemetria)
                contadores["telemetria_insertadas"] += 1
            else:
                contadores["telemetria_actualizadas"] += 1
            telemetria.possession_pct = fila.get("possession_pct")
            telemetria.sot = fila.get("sot")
            telemetria.sota = fila.get("sota")
            telemetria.xg = fila.get("xg")
            telemetria.xga = fila.get("xga")
            telemetria.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    sesion.flush()
    return contadores


# ═════════════════════════════════════════════════════════════════════════════════════════════
# ORQUESTACIÓN
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _expandir_temporada(etiqueta: str) -> List[str]:
    """Acepta `2015-2016`, `2015/2016` o la etiqueta completa con fase."""
    limpia = str(etiqueta or "").strip()
    if not limpia:
        return []
    if re.fullmatch(r"\d{4}[-/]\d{4}", limpia):
        inicio, fin = re.split(r"[-/]", limpia)
        return [f"{inicio}/{fin} - Apertura", f"{inicio}/{fin} - Clausura"]
    return [limpia]


def descubrir_temporadas() -> List[str]:
    """Lista `allAvailableSeasons` desde el `__NEXT_DATA__` de la página de liga."""
    html = _descargar_texto(URL_OVERVIEW)
    payload = extraer_next_data(html)
    page_props = (payload.get("props") or {}).get("pageProps") or {}
    temporadas = page_props.get("allAvailableSeasons")
    if not isinstance(temporadas, list) or not temporadas:
        raise RuntimeError("FotMob no publicó `allAvailableSeasons`; Alto al Fuego estructural.")
    return [str(t) for t in temporadas]


def _filtrar_temporadas(
    temporadas: Sequence[str], desde: Optional[int], hasta: Optional[int]
) -> List[str]:
    filtradas: List[Tuple[int, int, str]] = []
    for etiqueta in temporadas:
        coincidencia = re.search(r"(\d{4})\s*/\s*(\d{4})\s*-\s*(Apertura|Clausura)", etiqueta, re.I)
        if not coincidencia:
            continue
        inicio = int(coincidencia.group(1))
        if desde is not None and inicio < desde:
            continue
        if hasta is not None and inicio > hasta:
            continue
        fase_orden = 0 if coincidencia.group(3).lower() == "apertura" else 1
        filtradas.append((inicio, fase_orden, etiqueta))
    filtradas.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in filtradas]


def configurar_bd_historica(ruta: str) -> PersistenceGateway:
    """Apunta el Gateway a la 3NF histórica aislada y garantiza el esquema.

    La bóveda viva (`data/qbe_database.db`) NO se toca por omisión: el corpus 2010-2025
    no debe contaminar los agregados del modelo de la temporada activa. `--db` permite
    apuntar otra 3NF de forma explícita.
    """
    import src.config as cfg
    from src.storage.models import Base

    absoluta = os.path.abspath(ruta)
    url = f"sqlite:///{absoluta.replace(os.sep, '/')}"
    cfg.settings.DATABASE_URL = url
    os.environ["DATABASE_URL"] = url
    PersistenceGateway._instance = None
    gateway = PersistenceGateway()
    Base.metadata.create_all(bind=gateway.engine)
    return gateway


def _detalles_de_temporada(
    fixtures: Sequence[Dict[str, Any]],
    modo_telemetria: str,
    anio: int,
    espera: float,
    limite: int,
) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, str]], str]:
    """Descarga `matchDetails` según la política y devuelve `(detalles, errores, motivo_omision)`."""
    if modo_telemetria == "no":
        return {}, [], "telemetría desactivada por CLI"
    if modo_telemetria == "auto" and anio < UMBRAL_TELEMETRIA:
        return {}, [], f"FotMob no publica stats antes de {UMBRAL_TELEMETRIA}"

    candidatos = fixtures[: int(limite)] if int(limite) > 0 else fixtures
    detalles: Dict[str, Dict[str, Any]] = {}
    errores: List[Dict[str, str]] = []
    for posicion, entrada in enumerate(candidatos, 1):
        if not isinstance(entrada, dict) or not bool((entrada.get("status") or {}).get("finished")):
            continue
        match_id = str(entrada.get("id") or "").strip()
        if not match_id:
            continue
        try:
            detalles[match_id] = _descargar_json(URL_PARTIDO.format(match_id=match_id))
        except RuntimeError as error:
            errores.append({"match_id": match_id, "motivo": str(error)})
        if espera > 0 and posicion < len(candidatos):
            time.sleep(espera)
    return detalles, errores, ""


def ingerir_temporada(
    etiqueta: str,
    *,
    gateway: Optional[PersistenceGateway] = None,
    modo_telemetria: str = "auto",
    espera: float = 0.25,
    limite: int = 0,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Ingiere una temporada completa: `__NEXT_DATA__` → detalles → upsert 3NF."""
    html = _descargar_texto(URL_TEMPORADA.format(temporada=quote(etiqueta, safe="")))
    payload = extraer_next_data(html)
    page_props = (payload.get("props") or {}).get("pageProps") or {}
    fixtures = (page_props.get("fixtures") or {}).get("allMatches")
    if not isinstance(fixtures, list):
        raise ValueError(f"[{etiqueta}] `fixtures.allMatches` ausente; Alto al Fuego estructural.")

    temporada = str((page_props.get("details") or {}).get("selectedSeason") or etiqueta)
    season_id, anio, _ = _temporada_canonica(temporada)
    detalles, errores, motivo_omision = _detalles_de_temporada(
        fixtures, modo_telemetria, anio, espera, limite
    )

    fixtures_efectivos = fixtures[: int(limite)] if int(limite) > 0 else fixtures
    partidos = parsear_next_data(
        {"props": {"pageProps": {
            "details": page_props.get("details") or {"selectedSeason": temporada},
            "fixtures": {"allMatches": fixtures_efectivos},
        }}},
        detalles,
    )

    if dry_run:
        contadores = {
            "temporadas_insertadas": 0,
            "matches_insertados": 0,
            "matches_actualizados": 0,
            "telemetria_insertadas": 0,
            "telemetria_actualizadas": 0,
            "omitidos": 0,
            "unmapped": 0,
        }
    else:
        gateway = gateway or PersistenceGateway()
        with gateway.write_transaction() as sesion:
            contadores = persistir_partidos(sesion, partidos)

    con_telemetria = sum(1 for partido in partidos if partido.get("telemetria"))
    return {
        "temporada": temporada,
        "season_id": season_id,
        "fixtures": len(fixtures),
        "terminados": sum(
            1 for entrada in fixtures if bool((entrada.get("status") or {}).get("finished"))
        ),
        "partidos": len(partidos),
        "con_telemetria": con_telemetria,
        "sin_telemetria": len(partidos) - con_telemetria,
        "unmapped": sum(1 for partido in partidos if partido.get("estado_identidad") == "UNMAPPED"),
        "motivo_omision_telemetria": motivo_omision,
        "errores_detalle": errores,
        "persistencia": contadores,
        "dry_run": bool(dry_run),
    }


def ingerir_historico(
    temporadas: Optional[Sequence[str]] = None,
    *,
    gateway: Optional[PersistenceGateway] = None,
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    modo_telemetria: str = "auto",
    espera: float = 0.25,
    limite: int = 0,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Orquesta la corrida histórica y devuelve el manifiesto estructurado."""
    if temporadas:
        etiquetas: List[str] = []
        for etiqueta in temporadas:
            etiquetas.extend(_expandir_temporada(etiqueta))
    else:
        etiquetas = _filtrar_temporadas(descubrir_temporadas(), desde, hasta)

    if not etiquetas:
        raise RuntimeError("No hay temporadas que ingerir con los filtros solicitados.")

    reportes: List[Dict[str, Any]] = []
    for posicion, etiqueta in enumerate(etiquetas, 1):
        logger.info("📡 [%d/%d] %s", posicion, len(etiquetas), etiqueta)
        reporte = ingerir_temporada(
            etiqueta,
            gateway=gateway,
            modo_telemetria=modo_telemetria,
            espera=espera,
            limite=limite,
            dry_run=dry_run,
        )
        reportes.append(reporte)
        logger.info(
            "   ✓ partidos=%d · con_telemetria=%d · unmapped=%d · insertados=%d · actualizados=%d",
            reporte["partidos"], reporte["con_telemetria"], reporte["unmapped"],
            reporte["persistencia"]["matches_insertados"],
            reporte["persistencia"]["matches_actualizados"],
        )

    return {
        "sonda": "ARCH-1.4.73 · LN-QBE-133 · INGESTA-HISTORICA-FOTMOB",
        "temporadas": reportes,
        "resumen": {
            "temporadas": len(reportes),
            "partidos": sum(r["partidos"] for r in reportes),
            "con_telemetria": sum(r["con_telemetria"] for r in reportes),
            "unmapped": sum(r["unmapped"] for r in reportes),
            "matches_insertados": sum(r["persistencia"]["matches_insertados"] for r in reportes),
            "matches_actualizados": sum(r["persistencia"]["matches_actualizados"] for r in reportes),
            "telemetria_insertadas": sum(r["persistencia"]["telemetria_insertadas"] for r in reportes),
            "telemetria_actualizadas": sum(r["persistencia"]["telemetria_actualizadas"] for r in reportes),
            "errores_detalle": sum(len(r["errores_detalle"]) for r in reportes),
            "dry_run": bool(dry_run),
        },
    }


# ═════════════════════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _imprimir_resumen(reporte: Dict[str, Any]) -> None:
    resumen = reporte.get("resumen") or {}
    print("\n" + "=" * 88)
    print("📚 [ARCH-1.4.73 / LN-QBE-133] INGESTA HISTÓRICA MASIVA DE FOTMOB")
    print("=" * 88)
    print(f"  Temporadas: {resumen.get('temporadas')} · partidos: {resumen.get('partidos')}")
    print(
        f"  Cobertura: con telemetría={resumen.get('con_telemetria')} · "
        f"unmapped={resumen.get('unmapped')} · errores_detalle={resumen.get('errores_detalle')}"
    )
    print(
        f"  3NF: matches insertados={resumen.get('matches_insertados')} · "
        f"actualizados={resumen.get('matches_actualizados')} · "
        f"telemetría insertadas={resumen.get('telemetria_insertadas')} · "
        f"actualizadas={resumen.get('telemetria_actualizadas')}"
    )
    if resumen.get("dry_run"):
        print("  🧪 DRY-RUN: no se escribió ninguna fila.")
    print("-" * 88)
    for temporada in reporte.get("temporadas") or []:
        print(
            f"  {temporada['temporada']:<28} partidos={temporada['partidos']:>3} "
            f"telemetría={temporada['con_telemetria']:>3} unmapped={temporada['unmapped']:>2} "
            f"ins={temporada['persistencia']['matches_insertados']:>3} "
            f"act={temporada['persistencia']['matches_actualizados']:>3}"
        )
    print("=" * 88)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ingesta histórica masiva de FotMob (2010/11 → actualidad) en la 3NF."
    )
    parser.add_argument("--temporada", action="append", default=None,
                        help="Temporada(s): 2015-2016, 2015/2016 o la etiqueta completa.")
    parser.add_argument("--desde", type=int, default=2010)
    parser.add_argument("--hasta", type=int, default=None)
    parser.add_argument("--db", default=RUTA_HISTORICO_DEFAULT,
                        help=("SQLite 3NF histórica aislada (default: "
                              f"{RUTA_HISTORICO_DEFAULT}); use data/qbe_database.db solo "
                              "con orden expresa del Director."))
    parser.add_argument("--telemetria", choices=("auto", "si", "no"), default="auto",
                        help="auto: stats solo desde 2018; si: siempre; no: solo resultados.")
    parser.add_argument("--espera", type=float, default=0.25)
    parser.add_argument("--limite", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        gateway = None
        if args.db and not args.dry_run:
            gateway = configurar_bd_historica(str(args.db))
        reporte = ingerir_historico(
            args.temporada,
            gateway=gateway,
            desde=args.desde,
            hasta=args.hasta,
            modo_telemetria=args.telemetria,
            espera=float(args.espera),
            limite=int(args.limite),
            dry_run=bool(args.dry_run),
        )
    except (RuntimeError, ValueError) as error:
        logger.error("❌ ALTO AL FUEGO: %s", error)
        return 2

    if args.json:
        print(json.dumps(reporte, ensure_ascii=False, indent=2, default=str))
    else:
        _imprimir_resumen(reporte)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
