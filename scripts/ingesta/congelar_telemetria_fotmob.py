# -*- coding: utf-8 -*-
"""
Q-BE CD WEB - CONGELADOR DE TELEMETRÍA ÓPTICA LIGA MX (FOTMOB `matchDetails`)
[ARCH-1.4.50] Materializa `data/cache_telemetria_liga_mx_2026.json` y puebla la 3NF `match_telemetry`.
Régimen: [HÍBRIDO DUAL-TRACK] — ingesta y artefacto [DBBD-FUNGIBLE]; la escritura 3NF queda sujeta al
contrato sellado de persistencia (`[VAULT-DATA-001]`, `[GOVERNANCE-01]`, `VAR-2026-LAB5-EVIDENCIA` §7).

Base de Gobierno: Kybern Framework v13.5 / CERO ALAMBRADO

Axiomas operativos:
  1. Cero cifras inventadas: cada magnitud proviene de `content.stats.Periods.All` del `matchDetails`
     real; si `BallPossesion` o `ShotsOnTarget` no están publicadas, el partido se excluye y se
     declara en `faltantes` (jamás se imputa `50.0` ni `0.0`).
  2. Reciprocidad defensiva: `sota_home ≡ sot_away` y `sota_away ≡ sot_home` (identidad de conjunto:
     el remate a puerta de un club ES el remate recibido por el rival).
  3. Bipartita por partido: `possession_home + possession_away ≡ 100.0`. Un partido que no la cumpla
     se rechaza con traza (el contrato `[LN-QBE-111]` la exige exacta).
  4. Identidad canónica: el club se resuelve con `canonicalize_team_name` → `obtener_slug_club` y se
     acopla al fixture por la terna `(jornada, home_slug, away_slug)`; `matches.kickoff_utc` es NULL
     en el corpus, por lo que el reloj JAMÁS se usa como llave. Una sede invertida se rechaza.
  5. Idempotencia: `partidos` se ordena por `match_id`; dos corridas sobre la misma evidencia producen
     un cuerpo bit-idéntico (sólo cambia `generado_at` / `hash_sha256`). El upsert 3NF commuta a
     `actualizadas` sin duplicar filas.
  6. Integridad de la evidencia: `hash_sha256` se calcula sobre el cuerpo canónico auto-excluyente y
     `--desde-cache` la recalcula; una huella rota aborta la rehidratación.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import func, insert, select, update

from src.ingestion.normalizer import canonicalize_team_name
from src.storage.crest_resolver import obtener_slug_club
from src.storage.gateway import PersistenceGateway
from src.storage.models import Match, MatchTelemetry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CongeladorTelemetria")

SONDA_TELEMETRIA = "ARCH-1.4.50 · TELEMETRIA-OPTICA-LIGAMX"
ESQUEMA_TELEMETRIA = "telemetria_optics_v1"
FUENTE_TELEMETRIA = "fotmob.com · matchDetails › content.stats.Periods.All"
ENDPOINT_PARTIDO = "https://www.fotmob.com/api/data/matchDetails?matchId={match_id}"
ENDPOINT_LIGA = "https://www.fotmob.com/api/data/leagues?id={liga_id}&ccode3=MEX"
RUTA_TELEMETRIA_DEFAULT = os.path.join(
    PROJECT_ROOT, "data", "cache_telemetria_liga_mx_2026.json"
)
LIGA_FOTMOB_ID_DEFAULT = 230
TEMPORADA_DEFAULT = "2026"
ESTADOS_TERMINALES = ("FINALIZADO", "FINISHED")
CLAVE_POSESION = "BallPossesion"
CLAVE_SOT = "ShotsOnTarget"
CABECERAS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Referer": "https://www.fotmob.com/",
}


# ═════════════════════════════════════════════════════════════════════════════════════════════════
# TRANSPORTE (red acotada, reintentos con espera creciente, cero caché implícita)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def _descargar_json(
    url: str, *, timeout: float = 30.0, reintentos: int = 3, espera: float = 1.0
) -> Dict[str, Any]:
    """GET JSON con reintentos acotados; agota los intentos ⇒ excepción (fail-loud)."""
    ultimo_error: Optional[Exception] = None
    for intento in range(1, max(1, reintentos) + 1):
        try:
            peticion = Request(url, headers=CABECERAS_HTTP)
            with urlopen(peticion, timeout=timeout) as respuesta:
                return json.loads(respuesta.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            ultimo_error = error
            if intento < reintentos:
                pausa = espera * intento
                logger.warning(
                    "⚠️  [RED] %s (intento %d/%d) · reintento en %.1fs",
                    type(error).__name__, intento, reintentos, pausa,
                )
                time.sleep(pausa)
    raise RuntimeError(f"No se pudo descargar {url}: {ultimo_error}") from ultimo_error


def _a_entero(valor: Any) -> Optional[int]:
    """Conversión estricta a entero (`None` si no es un número legible)."""
    if isinstance(valor, bool) or valor is None:
        return None
    if isinstance(valor, (int, float)):
        return int(round(float(valor)))
    if isinstance(valor, str):
        limpio = valor.strip().replace("%", "").replace(",", ".")
        try:
            return int(round(float(limpio)))
        except ValueError:
            return None
    if isinstance(valor, dict):
        return _a_entero(valor.get("value"))
    return None


def _estadisticas_planas(payload_partido: Dict[str, Any]) -> Dict[str, Tuple[Any, Any]]:
    """Aplana los grupos de `Periods.All` a `{clave: (local, visita)}`.

    El payload publica grupos (`top_stats`, `shots`, …) cuyas entradas son
    `{title, key, stats: [local, visita], rawStats: [{value}, …]}`. Se recorren todos los grupos y
    se indexa por `key`; la primera aparición gana (contrato estable del feed).
    """
    stats = (((payload_partido.get("content") or {}).get("stats") or {}).get("Periods") or {})
    grupos = (stats.get("All") or {}).get("stats")
    if not isinstance(grupos, list):
        return {}
    plano: Dict[str, Tuple[Any, Any]] = {}
    for grupo in grupos:
        if not isinstance(grupo, dict):
            continue
        entradas = grupo.get("stats")
        if not isinstance(entradas, list):
            continue
        for entrada in entradas:
            if not isinstance(entrada, dict):
                continue
            clave = str(entrada.get("key") or "").strip()
            if not clave or clave in plano:
                continue
            valores = entrada.get("stats")
            if not isinstance(valores, list) or len(valores) < 2:
                continue
            crudos = entrada.get("rawStats")
            if isinstance(crudos, list) and len(crudos) >= 2:
                plano[clave] = (
                    _a_entero(crudos[0]) if crudos[0] is not None else _a_entero(valores[0]),
                    _a_entero(crudos[1]) if crudos[1] is not None else _a_entero(valores[1]),
                )
            else:
                plano[clave] = (_a_entero(valores[0]), _a_entero(valores[1]))
    return plano


def _telemetria_de_payload(
    payload_partido: Dict[str, Any]
) -> Tuple[Optional[Dict[str, int]], str]:
    """Extrae `{possession_h, possession_a, sot_h, sot_a}` o el motivo fáctico del rechazo."""
    plano = _estadisticas_planas(payload_partido)
    posesion = plano.get(CLAVE_POSESION)
    remates = plano.get(CLAVE_SOT)
    if posesion is None:
        return None, f"sin `{CLAVE_POSESION}` en `content.stats.Periods.All`"
    if remates is None:
        return None, f"sin `{CLAVE_SOT}` en `content.stats.Periods.All`"
    poss_h, poss_a = posesion
    sot_h, sot_a = remates
    if None in (poss_h, poss_a, sot_h, sot_a):
        return None, "estadísticas no numéricas en el feed"
    if not (0 <= poss_h <= 100 and 0 <= poss_a <= 100):
        return None, f"posesión fuera de [0, 100]: {poss_h}/{poss_a}"
    if poss_h + poss_a != 100:
        return None, f"posesión no bipartita: {poss_h} + {poss_a} = {poss_h + poss_a}"
    if min(sot_h, sot_a) < 0:
        return None, f"remates a puerta negativos: {sot_h}/{sot_a}"
    return (
        {
            "possession_h": int(poss_h),
            "possession_a": int(poss_a),
            "sot_h": int(sot_h),
            "sot_a": int(sot_a),
        },
        "",
    )


# ═════════════════════════════════════════════════════════════════════════════════════════════════
# IDENTIDAD CANÓNICA Y ACOPLAMIENTO CON EL CALENDARIO 3NF
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def _slug_de_club(nombre: Optional[str]) -> str:
    """Slug canónico del club (misma cadena que la 3NF usa en `matches.*_team_slug`)."""
    return obtener_slug_club(canonicalize_team_name(nombre))


def _objetivos_3nf(sesion: Any) -> Tuple[List[Dict[str, Any]], set]:
    """Fixtures con estado terminal + universo de slugs canónicos publicados por el calendario."""
    filas = sesion.execute(select(Match).where(Match.status.in_(ESTADOS_TERMINALES))).scalars().all()
    objetivos: List[Dict[str, Any]] = []
    catalogo: set = set()
    for fila in filas:
        home_slug, away_slug = str(fila.home_team_slug), str(fila.away_team_slug)
        catalogo.update((home_slug, away_slug))
        if fila.matchday_num is None:
            continue
        objetivos.append(
            {
                "match_id": str(fila.id),
                "jornada": int(fila.matchday_num),
                "home_slug": home_slug,
                "away_slug": away_slug,
            }
        )
    objetivos.sort(key=lambda item: (item["jornada"], item["match_id"]))
    return objetivos, catalogo


def _mapa_feed(
    payload_liga: Dict[str, Any], catalogo: set
) -> Tuple[Dict[Tuple[int, str, str], Dict[str, Any]], List[Dict[str, str]]]:
    """Indexa el feed por `(jornada, home_slug, away_slug)` y reporta clubes no homologables.

    La identidad se resuelve SÓLO con el plano sellado (`canonicalize_team_name` →
    `obtener_slug_club`): una etiqueta que no pertenezca al catálogo del calendario se descarta con
    traza, jamás se adivina.
    """
    entradas = ((payload_liga.get("fixtures") or {}).get("allMatches") or [])
    indice: Dict[Tuple[int, str, str], Dict[str, Any]] = {}
    huerfanos: List[Dict[str, str]] = []
    for entrada in entradas:
        if not isinstance(entrada, dict):
            continue
        nombre_home = str(((entrada.get("home") or {}).get("name")) or "")
        nombre_away = str(((entrada.get("away") or {}).get("name")) or "")
        home_slug, away_slug = _slug_de_club(nombre_home), _slug_de_club(nombre_away)
        if home_slug not in catalogo or away_slug not in catalogo:
            huerfanos.append(
                {"local": nombre_home, "visitante": nombre_away, "motivo": "club fuera del catálogo"}
            )
            continue
        jornada = _a_entero(entrada.get("roundName"))
        if jornada is None:
            jornada = _a_entero(str(entrada.get("round") or "").rstrip(". "))
        if not jornada:
            huerfanos.append(
                {"local": nombre_home, "visitante": nombre_away, "motivo": "jornada ilegible"}
            )
            continue
        estado = entrada.get("status") or {}
        indice[(int(jornada), home_slug, away_slug)] = {
            "fotmob_match_id": str(entrada.get("id") or ""),
            "terminado": bool(estado.get("finished")),
            "utc_time": str(estado.get("utcTime") or ""),
            "marcador": str(estado.get("scoreStr") or ""),
        }
    return indice, huerfanos


def _huella_sha256(cuerpo: Dict[str, Any]) -> str:
    """SHA-256 del cuerpo canónico auto-excluyente (misma convención que `audit_exporter`)."""
    canonico = json.dumps(cuerpo, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def _verificar_huella(artefacto: Dict[str, Any]) -> str:
    """Recalcula la huella del artefacto cargado; devuelve el veredicto y aborta si fue alterado."""
    cuerpo = dict(artefacto)
    declarada = str(cuerpo.pop("hash_sha256", ""))
    recalculada = _huella_sha256(cuerpo)
    if declarada != recalculada:
        raise RuntimeError(
            "Evidencia alterada: `hash_sha256` declarado no reproduce el cuerpo canónico "
            f"({declarada[:12]}… ≠ {recalculada[:12]}…)"
        )
    return recalculada


# ═════════════════════════════════════════════════════════════════════════════════════════════════
# MATERIALIZACIÓN DEL ARTEFACTO CONGELADO
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def _registro_partido(
    objetivo: Dict[str, Any], feed: Dict[str, Any], telemetria: Dict[str, int]
) -> Dict[str, Any]:
    """Registro del fixture con reciprocidad defensiva aplicada (`SoTA_H ≡ SoT_A`)."""
    return {
        "fotmob_match_id": feed["fotmob_match_id"],
        "jornada": int(objetivo["jornada"]),
        "utc_time": feed["utc_time"],
        "marcador": feed["marcador"],
        "home": {
            "slug": objetivo["home_slug"],
            "possession": int(telemetria["possession_h"]),
            "sot": int(telemetria["sot_h"]),
            "sota": int(telemetria["sot_a"]),
        },
        "away": {
            "slug": objetivo["away_slug"],
            "possession": int(telemetria["possession_a"]),
            "sot": int(telemetria["sot_a"]),
            "sota": int(telemetria["sot_h"]),
        },
    }


def _escribir_artefacto(destino: str, artefacto: Dict[str, Any]) -> int:
    """Escribe el artefacto canónico (claves ordenadas, cuerpo estable) y devuelve sus bytes."""
    ruta = os.path.abspath(destino)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    texto = json.dumps(artefacto, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    with open(ruta, "w", encoding="utf-8", newline="\n") as manejador:
        manejador.write(texto)
    return os.path.getsize(ruta)


def _cargar_artefacto(destino: str) -> Dict[str, Any]:
    """Carga el artefacto congelado y certifica su huella antes de usarlo."""
    ruta = os.path.abspath(destino)
    if not os.path.exists(ruta):
        raise RuntimeError(f"No existe el artefacto congelado `{ruta}`: ejecute la ingesta con red")
    with open(ruta, "r", encoding="utf-8") as manejador:
        artefacto = json.load(manejador)
    _verificar_huella(artefacto)
    return artefacto


# ═════════════════════════════════════════════════════════════════════════════════════════════════
# ORQUESTADOR (calendario 3NF → feed → artefacto → 3NF)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def congelar_telemetria(
    temporada: str = TEMPORADA_DEFAULT,
    salida: str = RUTA_TELEMETRIA_DEFAULT,
    liga_id: int = LIGA_FOTMOB_ID_DEFAULT,
    espera: float = 0.25,
    limite: int = 0,
    desde_cache: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Congela la telemetría óptica de la temporada y puebla la 3NF en una sola transacción."""
    gateway = PersistenceGateway()
    with gateway.read_session() as sesion:
        objetivos, catalogo = _objetivos_3nf(sesion)
    logger.info(
        "📋 Calendario 3NF: %d fixture(s) terminales · %d slug(s) canónicos",
        len(objetivos), len(catalogo),
    )

    if desde_cache:
        artefacto = _cargar_artefacto(salida)
        partidos = dict(artefacto.get("partidos") or {})
        logger.info(
            "♻️  [DESDE-CACHÉ] huella certificada · %d partido(s) · %d faltante(s)",
            len(partidos), len(artefacto.get("faltantes") or []),
        )
        contadores = _persistir_3nf(partidos, dry_run=dry_run)
        return {
            "artefacto": artefacto,
            "persistencia": contadores,
            "huerfanos": [],
            "desde_cache": True,
        }

    payload_liga = _descargar_json(ENDPOINT_LIGA.format(liga_id=liga_id), espera=espera)
    indice, huerfanos = _mapa_feed(payload_liga, catalogo)
    logger.info(
        "🛰️  Feed: %d fixture(s) indexados · %d club(es)/jornada(s) descartados",
        len(indice), len(huerfanos),
    )

    pendientes = objetivos[: int(limite)] if int(limite) > 0 else objetivos
    partidos: Dict[str, Any] = {}
    faltantes: List[Dict[str, str]] = []
    for posicion, objetivo in enumerate(pendientes, 1):
        match_id = str(objetivo["match_id"])
        llave = (int(objetivo["jornada"]), str(objetivo["home_slug"]), str(objetivo["away_slug"]))
        feed = indice.get(llave)
        if feed is None:
            invertida = indice.get((llave[0], llave[2], llave[1]))
            faltantes.append(
                {
                    "match_id": match_id,
                    "motivo": (
                        "sede invertida en la fuente" if invertida else "fixture ausente del feed"
                    ),
                }
            )
            continue
        if not feed["terminado"]:
            faltantes.append({"match_id": match_id, "motivo": "partido no terminado en la fuente"})
            continue
        try:
            payload_partido = _descargar_json(
                ENDPOINT_PARTIDO.format(match_id=feed["fotmob_match_id"]), espera=espera
            )
        except RuntimeError as error:
            faltantes.append({"match_id": match_id, "motivo": f"red: {error}"})
            continue
        telemetria, motivo = _telemetria_de_payload(payload_partido)
        if telemetria is None:
            faltantes.append({"match_id": match_id, "motivo": motivo})
            continue
        partidos[match_id] = _registro_partido(objetivo, feed, telemetria)
        if posicion % 10 == 0 or posicion == len(pendientes):
            logger.info(
                "… %d/%d fixture(s) auditados · %d congelado(s) · %d faltante(s)",
                posicion, len(pendientes), len(partidos), len(faltantes),
            )
        if espera > 0:
            time.sleep(espera)

    partidos = {clave: partidos[clave] for clave in sorted(partidos)}
    faltantes.sort(key=lambda item: item["match_id"])
    artefacto: Dict[str, Any] = {
        "sonda": SONDA_TELEMETRIA,
        "esquema": ESQUEMA_TELEMETRIA,
        "fuente": FUENTE_TELEMETRIA,
        "endpoint": ENDPOINT_PARTIDO,
        "liga_fotmob_id": int(liga_id),
        "temporada": str(temporada),
        "generado_at": datetime.now(timezone.utc).isoformat(),
        "resumen": {
            "fixtures_calendario": len(objetivos),
            "partidos_congelados": len(partidos),
            "faltantes": len(faltantes),
            "filas_3nf": 2 * len(partidos),
            "clubes_descartados": len(huerfanos),
        },
        "faltantes": faltantes,
        "partidos": partidos,
    }
    artefacto["hash_sha256"] = _huella_sha256(artefacto)

    if dry_run:
        logger.info(
            "🧪 [DRY-RUN] %d partido(s) · %d faltante(s) · artefacto y 3NF NO escritos",
            len(partidos), len(faltantes),
        )
        return {
            "artefacto": artefacto,
            "persistencia": _persistir_3nf(partidos, dry_run=True),
            "huerfanos": huerfanos,
            "desde_cache": False,
        }

    bytes_escritos = _escribir_artefacto(salida, artefacto)
    logger.info(
        "✅ [CONGELADO] %s · %d partido(s) · %d faltante(s) · %d byte(s) · sha256=%s…",
        os.path.abspath(salida), len(partidos), len(faltantes), bytes_escritos,
        artefacto["hash_sha256"][:12],
    )
    contadores = _persistir_3nf(partidos, dry_run=False)
    return {
        "artefacto": artefacto,
        "persistencia": contadores,
        "huerfanos": huerfanos,
        "desde_cache": False,
    }


# ═════════════════════════════════════════════════════════════════════════════════════════════════
# PERSISTENCIA 3NF (transacción única, upsert idempotente por PK compuesta)
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def _persistir_3nf(partidos: Dict[str, Any], dry_run: bool = False) -> Dict[str, int]:
    """Upsert atómico de `match_telemetry` por PK `(match_id, team_slug)`.

    `xg`/`xga` se escriben estrictamente `NULL` (decreto `D3`): el xG/xGA homologado vive en
    `data/cache_optaxg_liga_mx_2026.json` y JAMÁS se fabrica en esta cadena.
    """
    contadores = {
        "filas": 2 * len(partidos),
        "insertadas": 0,
        "actualizadas": 0,
        "xg_previos_descartados": 0,
    }
    if dry_run:
        logger.info("🧪 [DRY-RUN] 3NF intacta · %d fila(s) que se habrían sellado", contadores["filas"])
        return contadores
    if not partidos:
        logger.warning("⚠️  Sin partidos congelados: la tabla `match_telemetry` no se toca")
        return contadores

    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    tabla = MatchTelemetry.__table__
    gateway = PersistenceGateway()
    with gateway.write_transaction() as tx:
        for match_id in sorted(partidos):
            for lado in ("home", "away"):
                bloque = partidos[match_id][lado]
                slug = str(bloque["slug"])
                # DML Core (no ORM): `values(xg=None)` emite `NULL` literal, mientras que el ORM
                # interpreta `None` como "valor no provisto" y aplicaría `Column(default=0.0)`,
                # fabricando un xG falso. Decreto D3: ausencia declarada, nunca `0.0`.
                valores = {
                    "possession_pct": float(bloque["possession"]),
                    "sot": float(bloque["sot"]),
                    "sota": float(bloque["sota"]),
                    "xg": None,
                    "xga": None,
                    "updated_at": ahora,
                }
                existente = tx.get(MatchTelemetry, (match_id, slug))
                if existente is None:
                    tx.execute(
                        insert(tabla).values(match_id=match_id, team_slug=slug, **valores)
                    )
                    contadores["insertadas"] += 1
                else:
                    if existente.xg is not None or existente.xga is not None:
                        contadores["xg_previos_descartados"] += 1
                    tx.execute(
                        update(tabla)
                        .where(tabla.c.match_id == match_id, tabla.c.team_slug == slug)
                        .values(**valores)
                    )
                    contadores["actualizadas"] += 1
        tx.flush()

    logger.info(
        "🗄️  [3NF] %d fila(s) · insertadas=%d · actualizadas=%d · xg/xga=NULL (D3)",
        contadores["filas"], contadores["insertadas"], contadores["actualizadas"],
    )
    return contadores


def _verificar_3nf(match_ids: List[str]) -> Dict[str, int]:
    """Certificación post-escritura: filas del lote y ausencia declarada de xG/xGA."""
    gateway = PersistenceGateway()
    with gateway.read_session() as sesion:
        total = sesion.execute(select(func.count()).select_from(MatchTelemetry)).scalar() or 0
        nulos = sesion.execute(
            select(func.count()).select_from(MatchTelemetry).where(MatchTelemetry.xg.is_(None))
        ).scalar() or 0
        lote = sesion.execute(
            select(func.count())
            .select_from(MatchTelemetry)
            .where(MatchTelemetry.match_id.in_(list(match_ids)))
        ).scalar() or 0
    return {"filas_totales": int(total), "xg_nulos": int(nulos), "filas_lote": int(lote)}


# ═════════════════════════════════════════════════════════════════════════════════════════════════
# CONSOLA Y PUNTO DE ENTRADA
# ═════════════════════════════════════════════════════════════════════════════════════════════════
def _imprimir_resumen(
    resultado: Dict[str, Any], verificacion: Dict[str, int], salida: str
) -> None:
    """Tablero de cierre: cobertura, contadores de escritura y faltantes declarados."""
    artefacto = resultado["artefacto"]
    resumen = artefacto.get("resumen") or {}
    persistencia = resultado.get("persistencia") or {}
    print("\n" + "=" * 84)
    print(f"📡 [{SONDA_TELEMETRIA}] TELEMETRÍA ÓPTICA · {artefacto.get('esquema')}")
    print("=" * 84)
    print(f"   Liga FotMob: {artefacto.get('liga_fotmob_id')} · temporada {artefacto.get('temporada')}")
    print(f"   Fixtures del calendario: {resumen.get('fixtures_calendario')}")
    print(
        f"   Partidos congelados: {resumen.get('partidos_congelados')}"
        f" · faltantes: {resumen.get('faltantes')}"
        f" · clubes descartados: {resumen.get('clubes_descartados')}"
    )
    print(
        f"   Filas 3NF: {persistencia.get('filas')} · insertadas={persistencia.get('insertadas')}"
        f" · actualizadas={persistencia.get('actualizadas')}"
    )
    print(f"   Artefacto: {os.path.abspath(salida)} · sha256={str(artefacto.get('hash_sha256'))[:12]}…")
    if verificacion:
        print(
            f"   3NF verificada: filas={verificacion.get('filas_totales')}"
            f" · xg/xga NULL={verificacion.get('xg_nulos')}"
            f" · filas del lote={verificacion.get('filas_lote')}"
        )
    faltantes = artefacto.get("faltantes") or []
    if faltantes:
        print("   🔴 Faltantes declarados:")
        for item in faltantes:
            print(f"      · {item.get('match_id')}: {item.get('motivo')}")
    print("=" * 84)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Congela la telemetría óptica de Liga MX (FotMob) y puebla `match_telemetry`."
    )
    parser.add_argument("--temporada", default=TEMPORADA_DEFAULT)
    parser.add_argument("--salida", default=RUTA_TELEMETRIA_DEFAULT)
    parser.add_argument("--liga-id", type=int, default=LIGA_FOTMOB_ID_DEFAULT)
    parser.add_argument("--espera", type=float, default=0.25, help="Pausa entre peticiones (segundos).")
    parser.add_argument(
        "--limite", type=int, default=0, help="Sondea sólo los primeros N fixtures (diagnóstico)."
    )
    parser.add_argument(
        "--desde-cache",
        action="store_true",
        help="No descarga: rehidrata la 3NF desde el artefacto congelado (huella certificada).",
    )
    parser.add_argument("--dry-run", action="store_true", help="No escribe artefacto ni 3NF.")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        resultado = congelar_telemetria(
            temporada=str(args.temporada),
            salida=str(args.salida),
            liga_id=int(args.liga_id),
            espera=float(args.espera),
            limite=int(args.limite),
            desde_cache=bool(args.desde_cache),
            dry_run=bool(args.dry_run),
        )
    except RuntimeError as error:
        logger.error("❌ %s", error)
        return 2

    partidos = resultado["artefacto"].get("partidos") or {}
    verificacion: Dict[str, int] = {} if args.dry_run else _verificar_3nf(sorted(partidos))
    _imprimir_resumen(resultado, verificacion, str(args.salida))

    faltantes = resultado["artefacto"].get("faltantes") or []
    if faltantes:
        logger.error(
            "🔴 %d fixture(s) sin telemetría íntegra: SALIDA 1 (fail-loud, cero imputación)",
            len(faltantes),
        )
        return 1
    if verificacion:
        if verificacion.get("xg_nulos") != verificacion.get("filas_totales"):
            logger.error("🔴 Integridad 3NF: existen filas con xg/xga no nulos ⇒ violación del decreto D3")
            return 1
        if verificacion.get("filas_lote") != 2 * len(partidos):
            logger.error(
                "🔴 Integridad 3NF: %s fila(s) del lote ≠ %s esperadas",
                verificacion.get("filas_lote"), 2 * len(partidos),
            )
            return 1
    logger.info("✅ Telemetría congelada y 3NF certificada · EXIT CODE 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
