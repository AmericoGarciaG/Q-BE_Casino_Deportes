# -*- coding: utf-8 -*-
"""
Q-BE CD WEB - SENSOR DE INGESTA HISTÓRICA BETEXPLORER
[ARCH-1.4.36] Cortes acumulados progresivos con future-blindness y persistencia 3NF no destructiva.
Régimen: [HÍBRIDO DUAL-TRACK] — transporte/DOM `[DBBD-FUNGIBLE]`, corte `[DIRGEN-STRICT]`.
Base de Gobierno: Kybern Framework v13.5 / CERO ALAMBRADO [GOVERNANCE-01]

Axiomas operativos:
  1. La matemática del corte acumulado se REUTILIZA del plano canónico (`reconstruir_tabla_acumulada`):
     el sensor importa la función, jamás la reimplementa (`ALGORITMO_CORTE is reconstruir_tabla_acumulada`).
  2. La identidad de un club se resuelve contra el catálogo 3NF (`teams.canonical_slug`), nunca por
     confianza ciega en el normalizador de etiquetas (`canonicalize_team_name` no es idempotente).
  3. Future-blindness: el corte N usa exclusivamente resultados de jornadas <= N.
  4. Persistencia no destructiva: `standings_snapshots` es insert-if-absent; `matches` es fill-if-null
     sobre `score_home`/`score_away` y cero invención de filas de calendario.
  5. [ARCH-1.4.36-ext · Dictamen V-3] Captura de cuotas de cierre 1X2: el sensor sella en
     `fixtures_snapshots.matches_json` el trío publicado por la fuente bajo el contrato de
     gobernanza `{"cuotas": {"L", "E", "V"}, "operador": "betexplorer"}` MÁS la clave `momios` que
     consume el motor de cartera, anclado al `id_partido` canónico de la 3NF (`matches.id`) y jamás
     atribuido a una casa local cuyas cuotas no fueron capturadas. Enriquecimiento de huecos: una
     cuota ya capturada por la ventanilla viva no se sobreescribe jamás.
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bs4 import BeautifulSoup

from src.ingestion.normalizer import NormalizationException, canonicalize_team_name
from src.storage.crest_resolver import obtener_slug_club
from src.storage.gateway import PersistenceGateway
from src.storage.models import (
    CurrentTeamStanding,
    FixtureSnapshot,
    Match,
    StandingSnapshot,
    Team,
    utc_now,
)
from scripts.daemons.centinela_deportivo import reconstruir_tabla_acumulada

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IngestaBetExplorer")

__all__ = [
    "ALGORITMO_CORTE",
    "URL_RESULTADOS_BETEXPLORER",
    "parsear_resultados_betexplorer",
    "resolver_identidad_en_catalogo",
    "canonizar_partidos",
    "construir_corte",
    "persistir_corte_si_ausente",
    "rellenar_marcadores_3nf",
    "persistir_cuotas_en_fixtures_3nf",
    "OPERADOR_FUENTE_CUOTAS",
    "construir_catalogo_3nf",
    "clubes_desde_boveda",
    "descargar_resultados_betexplorer",
]

# ===========================================================================
# CONSTANTES DE CONTRATO (fuente, bóveda y plano canónico)
# ===========================================================================
# [DIRGEN-STRICT] Identidad del algoritmo de corte: el sensor NO reimplementa la matemática.
ALGORITMO_CORTE = reconstruir_tabla_acumulada

URL_RESULTADOS_BETEXPLORER = "https://www.betexplorer.com/football/mexico/liga-mx/results/"
COMPETENCIA_CANONICA = "MEX_LIGAMX"
TEMPORADA_CANONICA = "2026"
LIGA_ID_CANONICA = 1
MAX_JORNADA_TEMPORADA = 17
CLUBES_POR_TEMPORADA = 18

CABECERAS_NAVEGADOR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
}

# Firmas del DOM real certificado en el Paso 0 (evidencia: scratch/betexplorer_results_raw.html)
RE_RONDA = re.compile(r"(\d+)\.\s*Round", re.IGNORECASE)
RE_MARCADOR = re.compile(r"^\d+\s*:\s*\d+$")
RE_SEPARADOR_CLUBES = re.compile(r"\s+-\s+")
# [ARCH-1.4.36-ext · Dictamen V-3] Procedencia de la captura agregada de la fuente: la cuota de
# cierre se sella con su operador declarado y JAMÁS se presta a una casa local ([GOVERNANCE-01]).
OPERADOR_FUENTE_CUOTAS = "betexplorer"
CUOTAS_1X2_REQUERIDAS = 3
CLASES_ETIQUETA = ("h-text-left", "table-main__tt")
CLASE_CELDA_CUOTAS = "table-main__odds"
CLASE_CELDA_GANADORA = "colored"


# ===========================================================================
# FASE 1: PARSER DUAL-DOM DE RESULTADOS (`[DBBD-FUNGIBLE]`)
# ===========================================================================
def _texto_normalizado(etiqueta) -> str:
    """Colapsa el texto de un nodo a una línea canónica (sin tabuladores ni saltos)."""
    return " ".join(etiqueta.get_text().split())


def _contenedor_de_filas(html: str):
    """Localiza la tabla de resultados; tolera fragmentos DOM sueltos sin `<table>`."""
    sopa = BeautifulSoup(html, "html.parser")
    tabla = sopa.find("table", class_="table-main")
    return tabla if tabla is not None else sopa


def _cuota_de_celda(celda) -> Optional[float]:
    """Extrae la cuota decimal de una celda `table-main__odds` (atributo directo o anidado)."""
    valor = celda.get("data-odd")
    if valor is None:
        anidado = celda.find(attrs={"data-odd": True})
        valor = anidado.get("data-odd") if anidado is not None else None
    if valor is None:
        return None
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


def parsear_resultados_betexplorer(html: str) -> Dict[int, List[Dict[str, Any]]]:
    """Parsea la cartelera de resultados de BetExplorer a partidos por jornada.

    Contrato de salida: `{jornada: [partido, ...]}` con `partido` =
    `{jornada, local, visitante, goles_local, goles_visitante, cuotas, odd_ganadora}`.

    Reglas certificadas del DOM real:
      - El bloque de jornada es una fila `tr > th` con etiqueta `N. Round`; una fila suelta sin
        bloque previo se DESCARTA (jamás se inventa una jornada).
      - La clave de identidad es `(jornada, local, visitante)`: el encabezado o la fila repetida
        no inflan la tabla (deduplicación, first-wins).
      - La cuota ganadora es la celda marcada con la clase `colored` (índice 0 = 1, 1 = X, 2 = 2).
    """
    bloques: Dict[int, List[Dict[str, Any]]] = {}
    firmas: set = set()
    jornada: Optional[int] = None

    for fila in _contenedor_de_filas(html).find_all("tr"):
        if fila.find("th") is not None:
            coincidencia = RE_RONDA.search(_texto_normalizado(fila))
            jornada = int(coincidencia.group(1)) if coincidencia else None
            continue
        if jornada is None:
            continue

        etiqueta: Optional[str] = None
        marcador: Optional[str] = None
        celdas_cuotas: List[Tuple[Any, bool]] = []
        for celda in fila.find_all("td"):
            clases = list(celda.get("class") or [])
            texto = _texto_normalizado(celda)
            if CLASE_CELDA_CUOTAS in clases:
                celdas_cuotas.append((celda, CLASE_CELDA_GANADORA in clases))
            elif marcador is None and RE_MARCADOR.match(texto):
                marcador = texto
            elif etiqueta is None and texto and any(c in clases for c in CLASES_ETIQUETA):
                etiqueta = texto

        if etiqueta is None or marcador is None:
            continue
        partes = RE_SEPARADOR_CLUBES.split(etiqueta, maxsplit=1)
        if len(partes) != 2:
            continue
        local, visitante = (parte.strip() for parte in partes)
        goles_local, goles_visitante = (int(x) for x in re.split(r"\s*:\s*", marcador))

        firma = (jornada, local, visitante)
        if firma in firmas:
            continue
        firmas.add(firma)

        bloques.setdefault(jornada, []).append({
            "jornada": jornada,
            "local": local,
            "visitante": visitante,
            "goles_local": goles_local,
            "goles_visitante": goles_visitante,
            "cuotas": [_cuota_de_celda(celda) for celda, _ in celdas_cuotas],
            "odd_ganadora": next((i for i, (_, ganadora) in enumerate(celdas_cuotas) if ganadora), None),
        })

    return bloques


# ===========================================================================
# FASE 2: IDENTIDAD CANÓNICA CONTRA EL CATÁLOGO 3NF (`[DIRGEN-STRICT]`)
# ===========================================================================
def _slugs_candidatos(nombre: str) -> List[str]:
    """Genera los slugs candidatos de una etiqueta cruda de fuente externa.

    `canonicalize_team_name` NO es idempotente ni acíclico (defecto latente certificado en el
    Paso 0: p. ej. `Guadalajara Chivas -> Guadalajara -> Chivas Guadalajara`), por lo que la
    normalización se usa solo como generador de candidatos y la verdad se dirime contra el
    catálogo 3NF (`teams.canonical_slug`).
    """
    candidatos: List[str] = []
    actual = nombre
    for _ in range(2):
        try:
            actual = canonicalize_team_name(actual)
        except NormalizationException:
            # [P1-4] El normalizador es Fail-Loud por diseño; este resolutor de catálogo
            # no inventa identidad y continúa con los candidatos crudos.
            break
        candidatos.append(obtener_slug_club(actual))
    candidatos.append(obtener_slug_club(nombre))
    return [candidato for candidato in candidatos if candidato]


def resolver_identidad_en_catalogo(nombre: str, catalogo: Dict[str, str]) -> Optional[str]:
    """Resuelve la identidad oficial de un club contra el catálogo 3NF (`teams`).

    `catalogo` es el mapa `{canonical_slug: name}` extraído de la tabla `teams` (fuente única de
    verdad). Devuelve el nombre oficial (`teams.name`) si y solo si la resolución es unívoca;
    ante ambigüedad o etiqueta ajena al catálogo devuelve `None` (CERO invención de identidades).
    """
    if not nombre:
        return None
    coincidencias = {slug for slug in _slugs_candidatos(nombre) if slug in catalogo}
    if len(coincidencias) == 1:
        return catalogo[coincidencias.pop()]
    if len(coincidencias) > 1:
        logger.warning(
            "⚠️ [IDENTIDAD AMBIGUA] '%s' colisiona con %s: se descarta (sin invención).",
            nombre, sorted(coincidencias),
        )
    return None


def canonizar_partidos(
    partidos_por_jornada: Dict[int, List[Dict[str, Any]]],
    catalogo: Dict[str, str],
) -> Dict[int, List[Dict[str, Any]]]:
    """Normaliza identidades y materializa el plano de corte canónico por jornada.

    Conserva el orden de la fuente dentro de cada jornada y descarta (con traza en bitácora)
    cualquier partido cuya identidad no resuelva contra el catálogo 3NF.
    """
    por_nombre = {nombre: slug for slug, nombre in catalogo.items()}
    canonico: Dict[int, List[Dict[str, Any]]] = {}
    huerfanos: List[str] = []

    for clave in sorted(partidos_por_jornada, key=lambda c: int(c)):
        jornada = int(clave)
        for partido in partidos_por_jornada[clave]:
            local = resolver_identidad_en_catalogo(str(partido.get("local") or ""), catalogo)
            visitante = resolver_identidad_en_catalogo(str(partido.get("visitante") or ""), catalogo)
            if local is None or visitante is None:
                huerfanos.append(f"J{jornada} {partido.get('local')} - {partido.get('visitante')}")
                continue

            goles_local = int(partido.get("goles_local", 0))
            goles_visitante = int(partido.get("goles_visitante", 0))
            canonico.setdefault(jornada, []).append({
                "jornada": jornada,
                "local": local,
                "visitante": visitante,
                "local_slug": por_nombre[local],
                "visitante_slug": por_nombre[visitante],
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
                "cuotas": list(partido.get("cuotas") or []),
                "odd_ganadora": partido.get("odd_ganadora"),
                "estado": "FINALIZADO",
                "marcador_actual": f"{goles_local} - {goles_visitante}",
                "equipo_local_fuente": partido.get("local"),
                "equipo_visitante_fuente": partido.get("visitante"),
            })

    if huerfanos:
        logger.warning(
            "⚠️ [IDENTIDAD NO RESUELTA] %d partido(s) descartado(s): %s",
            len(huerfanos), huerfanos[:5],
        )
    return canonico


# ===========================================================================
# FASE 3: CORTE ACUMULADO PROGRESIVO Y PERSISTENCIA 3NF NO DESTRUCTIVA
# ===========================================================================
def construir_corte(
    partidos_por_jornada: Dict[int, List[Dict[str, Any]]],
    jornada: int,
    clubes: List[str],
) -> List[Dict[str, Any]]:
    """[DIRGEN-STRICT] Corte acumulado future-blind de la jornada `jornada`.

    Axioma de anti-fuga: solo se aplanan los resultados de jornadas <= `jornada` (orden canónico
    por jornada ascendente y orden de la fuente dentro de cada jornada). La aritmética del corte
    NO se reimplementa: se delega en `ALGORITMO_CORTE` (plano canónico `reconstruir_tabla_acumulada`).
    """
    corte = int(jornada)
    partidos_hasta_fecha: List[Dict[str, Any]] = []
    for clave in sorted(partidos_por_jornada, key=lambda c: int(c)):
        if int(clave) > corte:
            continue
        for partido in partidos_por_jornada[clave]:
            if int(partido.get("jornada", clave)) > corte:
                continue
            partidos_hasta_fecha.append(partido)
    return ALGORITMO_CORTE(partidos_hasta_fecha, list(clubes))


def persistir_corte_si_ausente(
    sesion,
    league_id: int,
    jornada: int,
    tabla: List[Dict[str, Any]],
    season: str = TEMPORADA_CANONICA,
) -> bool:
    """[POLÍTICA INSERT-IF-ABSENT] Sella el corte `jornada` solo si aún no existe.

    No sobreescribe jamás un corte previo (los cortes J1..J9 son referencia canónica certificada y
    J10 es espejo vivo): la ausencia es la única condición de escritura. No comitea: la Unit of Work
    pertenece al `PersistenceGateway` del llamador.
    """
    existente = (
        sesion.query(StandingSnapshot)
        .filter(
            StandingSnapshot.league_id == league_id,
            StandingSnapshot.season == season,
            StandingSnapshot.matchday == int(jornada),
        )
        .first()
    )
    if existente is not None:
        logger.info("🔒 [CORTE CONSERVADO] J%s ya existe en `standings_snapshots`: no se sobreescribe.", jornada)
        return False

    sesion.add(StandingSnapshot(
        league_id=league_id,
        season=season,
        matchday=int(jornada),
        captured_at=utc_now(),
        positions_json=list(tabla),
    ))
    sesion.flush()
    logger.info("✅ [CORTE INSERTADO] J%s (%d clubes) sellado en `standings_snapshots`.", jornada, len(tabla))
    return True


def _buscar_partido_3nf(sesion, jornada: int, slug_local: str, slug_visita: str):
    """Busca la fila de calendario 3NF de un par local/visitante dentro de una jornada."""
    return (
        sesion.query(Match)
        .filter(
            Match.competition_id == COMPETENCIA_CANONICA,
            Match.matchday_num == int(jornada),
            Match.home_team_slug == slug_local,
            Match.away_team_slug == slug_visita,
        )
        .first()
    )


def rellenar_marcadores_3nf(
    sesion,
    league_id: int,
    partidos_por_jornada: Dict[int, List[Dict[str, Any]]],
    simular: bool = False,
) -> Dict[str, Any]:
    """[POLÍTICA FILL-IF-NULL] Rellena marcadores ausentes en `matches` desde resultados publicados.

    Reglas certificadas:
      - Solo se escribe sobre `score_home`/`score_away` cuando AMBOS son `NULL`; un marcador ya
        registrado jamás se sobreescribe (autoridad de la bóveda sobre la fuente externa).
      - El estado transita a `FINALIZADO` únicamente como consecuencia de materializar el marcador
        publicado: sin marcador no hay transición.
      - Cero invención de filas: si el par publicado no existe en el calendario 3NF se reporta en
        `sin_fila_3nf` y NO se crea nada.
      - Inversión de sede: si el calendario contiene el mismo par con los ejes local/visita
        intercambiados, el marcador se normaliza al eje del calendario (mismo partido, misma jornada).
      - `simular=True` proyecta el resultado sin escribir un solo byte (modo `--dry-run`).
      - No comitea: la Unit of Work pertenece al `PersistenceGateway` del llamador.

    `league_id` se conserva en la firma por cohesión con el canal de cortes (`standings_snapshots`);
    el calendario `matches` de la bóveda es mono-competición (`COMPETENCIA_CANONICA`).
    """
    reporte: Dict[str, Any] = {"actualizados": 0, "preservados": 0, "invertidos": 0, "sin_fila_3nf": []}

    for clave in sorted(partidos_por_jornada, key=lambda c: int(c)):
        jornada = int(clave)
        for partido in partidos_por_jornada[clave]:
            slug_local = partido.get("local_slug")
            slug_visita = partido.get("visitante_slug")
            if not slug_local or not slug_visita:
                reporte["sin_fila_3nf"].append(f"J{jornada} (identidad sin slug)")
                continue

            fila = _buscar_partido_3nf(sesion, jornada, slug_local, slug_visita)
            invertido = False
            if fila is None:
                fila = _buscar_partido_3nf(sesion, jornada, slug_visita, slug_local)
                invertido = fila is not None
            if fila is None:
                reporte["sin_fila_3nf"].append({
                    "jornada": jornada,
                    "local": partido.get("local"),
                    "visitante": partido.get("visitante"),
                })
                continue

            if fila.score_home is not None or fila.score_away is not None:
                reporte["preservados"] += 1
                continue

            goles_local = int(partido.get("goles_local", 0))
            goles_visitante = int(partido.get("goles_visitante", 0))
            if invertido:
                goles_local, goles_visitante = goles_visitante, goles_local
                reporte["invertidos"] += 1
            if not simular:
                fila.score_home = goles_local
                fila.score_away = goles_visitante
                if fila.status != "FINALIZADO":
                    fila.status = "FINALIZADO"
            reporte["actualizados"] += 1

    if not simular:
        sesion.flush()
    logger.info(
        "📊 [MARCADORES 3NF] actualizados=%d preservados=%d invertidos=%d sin_fila_3nf=%d",
        reporte["actualizados"], reporte["preservados"], reporte["invertidos"], len(reporte["sin_fila_3nf"]),
    )
    return reporte


# ===========================================================================
# FASE 3-BIS: ESCRITOR DE CUOTAS 1X2 DE CIERRE EN `fixtures_snapshots`
# [ARCH-1.4.36-ext · Dictamen V-3] Vía DATOS: habilita la operabilidad fiduciaria del backtesting
# sobre jornadas concluidas sin inventar un solo número ([GOVERNANCE-01]).
# ===========================================================================
def _cuotas_1x2_de_contrato(partido: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """Traduce el trío publicado por la fuente (`cuotas=[L, E, V]`) al contrato plano 1X2.

    Cero reparaciones, promedios ni rellenos: si la fuente no publica las TRES cuotas del partido
    (o alguna no es decimal > 1.0), no existe captura que sellar y se devuelve `None`.
    """
    cuotas = list(partido.get("cuotas") or [])
    if len(cuotas) != CUOTAS_1X2_REQUERIDAS:
        return None
    try:
        cuota_local, cuota_empate, cuota_visita = (float(valor) for valor in cuotas)
    except (TypeError, ValueError):
        return None
    if min(cuota_local, cuota_empate, cuota_visita) <= 1.0:
        return None
    return {"L": cuota_local, "E": cuota_empate, "V": cuota_visita}


def _porta_captura_factica(fixture: Dict[str, Any]) -> bool:
    """Espejo local del axioma del controlador ([ARCH-1.4.15 / LN-QBE-076]).

    ¿Porta ya el fixture una cuota 1X2 FÁCTICA (L > 1.0)? Se examinan la captura canónica del
    snapshot y las capturas por operador: una cuota ya capturada por la ventanilla viva manda y
    JAMÁS se sobreescribe (autoridad de la bóveda sobre la fuente externa).
    """
    capturas: List[Dict[str, Any]] = [fixture.get("momios") or {}]
    capturas.extend((fixture.get("momios_operadores") or {}).values())
    for captura in capturas:
        try:
            if float((captura or {}).get("L", 0.0) or 0.0) > 1.0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def persistir_cuotas_en_fixtures_3nf(
    sesion,
    league_id: int,
    partidos_por_jornada: Dict[int, List[Dict[str, Any]]],
    simular: bool = False,
) -> Dict[str, Any]:
    """[ARCH-1.4.36-ext · Dictamen V-3] Sella cuotas de cierre 1X2 en `fixtures_snapshots`.

    Leyes certificadas:
      - Procedencia: la cuota viaja con su operador declarado (`OPERADOR_FUENTE_CUOTAS`); cero
        atribución a casas locales cuyas cuotas no fueron capturadas ([GOVERNANCE-01]).
      - Anclaje por identidad canónica 3NF: el `id_partido` sellado es el `matches.id`
        (`LIGAMX-J{n}-{nn}`), dirimido por el par de slugs oficiales del catálogo (con tolerancia de
        inversión de sede, igual que el relleno de marcadores). Cero identificadores inventados.
      - Cero slates sintéticos: si la jornada no tiene snapshot capturado por la ventanilla viva se
        reporta en `sin_snapshot` y NO se crea ninguna fila.
      - Enriquecimiento NO DESTRUCTIVO de huecos: sólo se escribe el fixture que carece de toda
        captura 1X2. Cero borrados, cero mutación de cuotas ya capturadas.
      - Idempotente: la segunda pasada escribe 0 (los huecos ya están sellados).
      - `simular=True` proyecta el resultado sin escribir un solo byte (modo `--dry-run`).
      - No comitea: la Unit of Work pertenece al `PersistenceGateway` del llamador.
    """
    reporte: Dict[str, Any] = {
        "jornadas_enriquecidas": [],
        "cuotas_escritas": 0,
        "preservadas": 0,
        "sin_snapshot": [],
        "sin_fila_3nf": [],
        "cuotas_incompletas": [],
    }

    for clave in sorted(partidos_por_jornada, key=lambda c: int(c)):
        jornada = int(clave)
        snapshot = (
            sesion.query(FixtureSnapshot)
            .filter(
                FixtureSnapshot.league_id == league_id,
                FixtureSnapshot.matchday == jornada,
            )
            .order_by(FixtureSnapshot.updated_at.desc())
            .first()
        )
        if snapshot is None:
            reporte["sin_snapshot"].append(jornada)
            continue

        # Copia de trabajo: la reasignación del atributo JSON es la única forma de que la Unit of
        # Work advierta la mutación (una edición in situ sería invisible para el ORM).
        fixtures: List[Dict[str, Any]] = [
            dict(fx) for fx in (snapshot.matches_json or []) if isinstance(fx, dict)
        ]
        indice: Dict[str, Dict[str, Any]] = {
            str(fx.get("id_partido", "")): fx for fx in fixtures
        }
        escrituras_jornada = 0


        for partido in partidos_por_jornada[clave]:
            slug_local = partido.get("local_slug")
            slug_visita = partido.get("visitante_slug")
            if not slug_local or not slug_visita:
                reporte["sin_fila_3nf"].append(f"J{jornada} (identidad sin slug)")
                continue

            fila = _buscar_partido_3nf(sesion, jornada, slug_local, slug_visita)
            if fila is None:
                fila = _buscar_partido_3nf(sesion, jornada, slug_visita, slug_local)
            if fila is None:
                reporte["sin_fila_3nf"].append({
                    "jornada": jornada,
                    "local": partido.get("local"),
                    "visitante": partido.get("visitante"),
                })
                continue

            fixture = indice.get(str(fila.id))
            if fixture is None:
                reporte["sin_fila_3nf"].append({
                    "jornada": jornada,
                    "id_partido": str(fila.id),
                    "detalle": "el snapshot de la jornada no porta ese fixture",
                })
                continue

            if _porta_captura_factica(fixture):
                reporte["preservadas"] += 1
                continue

            cuotas = _cuotas_1x2_de_contrato(partido)
            if cuotas is None:
                reporte["cuotas_incompletas"].append({
                    "jornada": jornada,
                    "local": partido.get("local"),
                    "visitante": partido.get("visitante"),
                })
                continue

            # Contrato de gobernanza ordenado por el Director: `{"cuotas": {...}, "operador": ...}`
            # —procedencia auditable— MÁS la clave `momios` que SÍ consume el motor de cartera
            # ([ARCH-1.4.15]): ambos planos portan EXACTAMENTE los mismos tres números reales.
            fixture["cuotas"] = dict(cuotas)
            fixture["momios"] = dict(cuotas)
            fixture["operador"] = OPERADOR_FUENTE_CUOTAS
            reporte["cuotas_escritas"] += 1
            escrituras_jornada += 1

        if escrituras_jornada:
            reporte["jornadas_enriquecidas"].append(jornada)
            if not simular:
                snapshot.matches_json = fixtures

    if not simular:
        sesion.flush()

    logger.info(
        "🎯 [CUOTAS 3NF] escritas=%d preservadas=%d jornadas_enriquecidas=%s sin_snapshot=%s "
        "sin_fila_3nf=%d cuotas_incompletas=%d",
        reporte["cuotas_escritas"], reporte["preservadas"], reporte["jornadas_enriquecidas"],
        reporte["sin_snapshot"], len(reporte["sin_fila_3nf"]), len(reporte["cuotas_incompletas"]),
    )
    return reporte


# ===========================================================================
# FASE 4: ORQUESTACIÓN — BÓVEDA, FUENTE Y CLI
# ===========================================================================
def construir_catalogo_3nf(sesion, league_id: int = LIGA_ID_CANONICA) -> Dict[str, str]:
    """Catálogo autoritativo de identidades desde la 3NF: `{teams.canonical_slug: teams.name}`."""
    return {
        equipo.canonical_slug: equipo.name
        for equipo in sesion.query(Team).filter(Team.league_id == league_id).all()
    }


def clubes_desde_boveda(sesion, league_id: int = LIGA_ID_CANONICA) -> List[str]:
    """Orden de clubes del corte: espejo vivo (snapshot más reciente) -> standings -> catálogo."""
    snapshot = (
        sesion.query(StandingSnapshot)
        .filter(StandingSnapshot.league_id == league_id)
        .order_by(StandingSnapshot.matchday.desc())
        .first()
    )
    if snapshot and snapshot.positions_json:
        clubes = [fila.get("equipo") for fila in snapshot.positions_json
                  if isinstance(fila, dict) and fila.get("equipo")]
        if len(clubes) == CLUBES_POR_TEMPORADA:
            return clubes

    filas = (
        sesion.query(CurrentTeamStanding)
        .filter(CurrentTeamStanding.league_id == league_id)
        .order_by(CurrentTeamStanding.pos.asc())
        .all()
    )
    clubes = [fila.team_name for fila in filas if fila.team_name]
    if len(clubes) == CLUBES_POR_TEMPORADA:
        return clubes

    return [
        equipo.name for equipo in
        sesion.query(Team).filter(Team.league_id == league_id).order_by(Team.id.asc()).all()
    ]


def descargar_resultados_betexplorer(url: str = URL_RESULTADOS_BETEXPLORER, timeout: float = 20.0) -> str:
    """Descarga la cartelera de resultados con cabeceras de navegador (import perezoso de httpx)."""
    import httpx

    with httpx.Client(timeout=timeout, follow_redirects=True, headers=CABECERAS_NAVEGADOR) as cliente:
        respuesta = cliente.get(url)
        respuesta.raise_for_status()
        return respuesta.text


def cargar_html_local(ruta: str) -> str:
    """Evidencia offline: lectura de una captura local (solo lectura, cero escritura)."""
    return Path(ruta).read_text(encoding="utf-8", errors="replace")


def _reportar_ingesta(canonico, tabla, jornada_corte: int, clubes: List[str]) -> None:
    """Bitácora legible del corte: jornadas detectadas y tabla acumulada resultante."""
    print("\n" + "=" * 84)
    print(f"📡 [ARCH-1.4.36] INGESTA HISTÓRICA BETEXPLORER — CORTE J{jornada_corte} (future-blind)")
    print("=" * 84)
    for jornada in sorted(canonico, key=lambda clave: int(clave)):
        print(f"   J{int(jornada):>2}: {len(canonico[jornada]):>2} partido(s) publicados por la fuente")
    print(f"   Clubes del corte: {len(clubes)} | Algoritmo de corte: {ALGORITMO_CORTE.__name__}")
    print("-" * 84)
    print(f"   {'#':>2} {'CLUB':<23}{'PJ':>4}{'PG':>4}{'PE':>4}{'PP':>4}"
          f"{'GF':>4}{'GC':>4}{'DIF':>5}{'PTS':>6}  FORMA")
    for fila in tabla:
        print(
            f"   {fila['pos']:>2} {fila['equipo']:<23}{fila['pj']:>4}{fila['pg']:>4}{fila['pe']:>4}{fila['pp']:>4}"
            f"{fila['gf']:>4}{fila['gc']:>4}{fila['dif']:>5}{fila['puntos']:>6}  {''.join(fila['forma'])}"
        )
    print("-" * 84)


def _resumen_sin_fila(reporte: Dict[str, Any]) -> None:
    """Informa (sin actuar) los pares publicados que no tienen fila en el calendario 3NF."""
    pendientes = reporte.get("sin_fila_3nf") or []
    if not pendientes:
        return
    por_jornada: Dict[int, int] = {}
    for pendiente in pendientes:
        jornada = pendiente.get("jornada") if isinstance(pendiente, dict) else 0
        por_jornada[int(jornada)] = por_jornada.get(int(jornada), 0) + 1
    detalle = ", ".join(f"J{j}: {n}" for j, n in sorted(por_jornada.items()))
    print(f"   ⚠️  Pares publicados sin fila en el calendario 3NF (NO se inventan filas): {detalle}")


def ejecutar(argv: Optional[List[str]] = None) -> int:
    """Orquesta la ingesta: fuente -> identidad 3NF -> corte -> persistencia no destructiva."""
    parser = argparse.ArgumentParser(
        prog="ingestar_historico_betexplorer",
        description="[ARCH-1.4.36] Sensor de ingesta histórica BetExplorer (Liga MX) — cortes future-blind.",
    )
    parser.add_argument("--jornada", type=int, default=0,
                        help="Jornada del corte a sellar (0 = la más reciente publicada por la fuente).")
    parser.add_argument("--liga-id", type=int, default=LIGA_ID_CANONICA, help="Identificador de liga en la bóveda.")
    parser.add_argument("--url", default=URL_RESULTADOS_BETEXPLORER, help="URL de la cartelera de resultados.")
    parser.add_argument("--offline-html", default="",
                        help="Captura local (evidencia offline; se abre en solo lectura).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Proyecta la ingesta sin escribir un solo byte en la bóveda.")
    args = parser.parse_args(argv)

    if args.offline_html:
        logger.info("📂 [FUENTE OFFLINE] Captura local en solo lectura: %s", args.offline_html)
        html = cargar_html_local(args.offline_html)
    else:
        logger.info("🌐 [FUENTE VIVA] Descargando cartelera: %s", args.url)
        html = descargar_resultados_betexplorer(args.url)

    bloques = parsear_resultados_betexplorer(html)
    if not bloques:
        logger.error("🚨 [ABORTO] La fuente no expuso ningún bloque de jornada con resultados.")
        return 2

    gateway = PersistenceGateway()
    with gateway.read_session() as lectura:
        catalogo = construir_catalogo_3nf(lectura, args.liga_id)
        clubes = clubes_desde_boveda(lectura, args.liga_id)

    if not catalogo:
        logger.error("🚨 [ABORTO] Catálogo 3NF vacío para la liga %s: sin identidades oficiales no hay ingesta.",
                     args.liga_id)
        return 2

    canonico = canonizar_partidos(bloques, catalogo)
    if not canonico:
        logger.error("🚨 [ABORTO] Ningún partido de la fuente resolvió identidad contra el catálogo 3NF.")
        return 2

    jornada_corte = int(args.jornada) if args.jornada else max(canonico)
    tabla = construir_corte(canonico, jornada_corte, clubes)
    _reportar_ingesta(canonico, tabla, jornada_corte, clubes)

    if args.dry_run:
        with gateway.read_session() as proyeccion:
            reporte = rellenar_marcadores_3nf(proyeccion, args.liga_id, canonico, simular=True)
            cuotas = persistir_cuotas_en_fixtures_3nf(
                proyeccion, args.liga_id, canonico, simular=True)
        _resumen_sin_fila(reporte)
        print(f"\n🧪 [DRY-RUN] Proyección de marcadores: se rellenarían {reporte['actualizados']} "
              f"partido(s) y se preservarían {reporte['preservados']}. Cero escrituras certificadas: "
              f"la bóveda permanece intacta.\n")
        print(f"🧪 [DRY-RUN] Proyección de cuotas 1X2 ({OPERADOR_FUENTE_CUOTAS}): se sellarían "
              f"{cuotas['cuotas_escritas']} partido(s) en jornada(s) {cuotas['jornadas_enriquecidas']}; "
              f"preservadas {cuotas['preservadas']} · sin snapshot {cuotas['sin_snapshot']} · "
              f"cuotas incompletas {len(cuotas['cuotas_incompletas'])}. Cero escrituras.\n")
        return 0

    with gateway.write_transaction() as tx:
        reporte = rellenar_marcadores_3nf(tx, args.liga_id, canonico)
        insertado = persistir_corte_si_ausente(tx, args.liga_id, jornada_corte, tabla)
        cuotas = persistir_cuotas_en_fixtures_3nf(tx, args.liga_id, canonico)

    _resumen_sin_fila(reporte)
    print(f"\n💾 [PERSISTENCIA 3NF] marcadores_actualizados={reporte['actualizados']} "
          f"preservados={reporte['preservados']} invertidos={reporte['invertidos']} "
          f"| corte J{jornada_corte}={'INSERTADO' if insertado else 'YA EXISTÍA (no se sobreescribe)'}\n")
    print(f"💾 [CUOTAS 1X2] operador={OPERADOR_FUENTE_CUOTAS} "
          f"escritas={cuotas['cuotas_escritas']} preservadas={cuotas['preservadas']} "
          f"jornadas_enriquecidas={cuotas['jornadas_enriquecidas']} "
          f"sin_snapshot={cuotas['sin_snapshot']} "
          f"sin_fila_3nf={len(cuotas['sin_fila_3nf'])} "
          f"cuotas_incompletas={len(cuotas['cuotas_incompletas'])}\n")
    return 0


def main() -> int:
    """Punto de entrada CLI del sensor."""
    return ejecutar()


if __name__ == "__main__":
    raise SystemExit(main())
