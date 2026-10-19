# -*- coding: utf-8 -*-
"""
[ARCH-1.4.44] Proveedor H2H Unificado — Memoria Longitudinal de Enfrentamientos Directos.
[LN-QBE-103] Contrato de ingesta sellado en `docs/LOGIC.md` (nodo I/P/O/Φ completo).

Función del nodo
----------------
Restituir la evidencia H2H que el diseño monotorneo de la bóveda (`matches` = una sola temporada,
Apertura 17 jornadas) hace estructuralmente inalcanzable, sin abrir red en tiempo de ejecución:

1. **Bóveda 3NF (autoridad de marcador):** reutiliza íntegro el plano sellado `[ARCH-1.6.13-C]`
   (`_precargar_historial_consumado_sqlite` + `_historial_future_blind`), que publica los
   marcadores OFICIALES de `FixtureSnapshot.matches_json`.
2. **Corpus congelado (autoridad longitudinal):** `data/cache_h2h_liga_mx_2026.json`, esquema
   `h2h_corpus_v1`, producido una sola vez por `scripts/ingesta/congelar_cache_h2h_liga_mx.py`.
   Cero sensor en caliente, cero dependencia de disponibilidad del proveedor externo.

Leyes observadas
----------------
* **[LN-QBE-020-B] Ley Zero-H2H:** sin evidencia verificable se devuelve lista vacía. Jamás se
  fabrica un enfrentamiento ni se hereda uno de una pareja distinta.
* **Futuro-ceguera:** todo duelo con `fecha >= fecha_ref` (kickoff evaluado) queda excluido. La
  misma función sirve a la ruta viva y al backfill histórico.
* **Putualidad de perspectiva:** `goles_local` es SIEMPRE el marcador del club local del fixture
  evaluado, sin importar la sede original del duelo.
* **Precedencia de deduplicación:** la bóveda 3NF manda sobre el corpus cuando la misma fecha
  aparece en ambos orígenes (el marcador persistido por el daemon es el oficial).
* **Puente de identidad:** la bóveda indexa por nombre de exhibición y el corpus por slug; este
  módulo canonicaliza AMBOS flujos contra el catálogo `teams` (`name`/`short_name` →
  `canonical_slug`) antes de comparar. Sin el puente, el cruce es vacío por construcción.
* **Cero duplicación algorítmica:** la ponderación exponencial profunda (τ_deep = 540 días) NO se
  reimplementa aquí; se delega en el kernel sellado `[LN-QBE-020-C]`
  (`calcular_matriz_h2h_empirica`).

Régimen: [DIRGEN-STRICT] en la extracción (futuro-ceguera, deduplicación, perspectiva) y pureza de
acceso: este módulo no porta cliente HTTP, no escribe en la bóveda y no muta sus insumos.
"""

import json
import logging
import os
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.core.sovereign.h2h_kernel import TAU_H2H_DEEP, calcular_matriz_h2h_empirica

logger = logging.getLogger("SovereignH2HProvider")

# ─── Constantes legisladas ──────────────────────────────────────────────────────────────────────
ESQUEMA_CORPUS_H2H = "h2h_corpus_v1"
LIMITE_DUELOS_H2H = 5                 # [ARCH-1.6.13-C] ventana de publicación
LIGA_ID_CANONICA = 1                  # MEX_LIGAMX
TAU_H2H_DIAS = TAU_H2H_DEEP           # [ARCH-1.6.13-C] vida media multianual (540 d)
FUENTE_BOVEDA = "boveda_3nf"
FUENTE_CORPUS = "corpus_congelado"
RUTA_CORPUS_H2H = Path(__file__).resolve().parents[3] / "data" / "cache_h2h_liga_mx_2026.json"
CAMPOS_DUELO = (
    "goles_local", "goles_visita", "dias_antiguedad", "fecha", "fuente", "es_local_sede"
)



# ═════════════════════════════════════════════════════════════════════════════════════════════
# PUENTE DE IDENTIDAD — slug canónico ↔ nombre de exhibición (bóveda) ↔ slug (corpus)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _normalizar(valor: Any) -> str:
    """Canoniza un identificador a `kebab-case` sin acentos (`Club América` ⇒ `club-america`).

    Es idempotente sobre los slugs canónicos y colapsa separadores espurios (`_`, `-`, espacios),
    de modo que bóveda y corpus convergen en el MISMO espacio de comparación.
    """
    if valor is None:
        return ""
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    texto = texto.strip().lower()
    for separador in ("_", "/", ".", " "):
        texto = texto.replace(separador, "-")
    while "--" in texto:
        texto = texto.replace("--", "-")
    return texto.strip("-")


def _mapa_identidad(sesion, league_id: int) -> Dict[str, str]:
    """`nombre`/`nombre corto`/`slug` normalizados ⇒ `canonical_slug` desde el catálogo `teams`.

    La bóveda publica nombres de exhibición (`Club América`) mientras el corpus y los fixtures
    publican slugs (`club-america`): sin este puente la intersección es cero por construcción.

    [ARCH-1.4.26] La lectura del plano ORM se delega en `_catalogo_clubes_3nf`
    (`scripts/utilidades/`): este módulo del núcleo puro NO importa `src.storage`, ni aquí ni como
    import diferido. Cualquier fallo de lectura degrada a mapa vacío (comparación por slug literal).
    """
    if sesion is None:
        return {}
    try:
        from scripts.utilidades.poblar_temporada_completa_backtesting import _catalogo_clubes_3nf

        equipos = _catalogo_clubes_3nf(sesion, int(league_id))
    except Exception:  # pragma: no cover — degradación honesta, jamás excepción al explotar
        logger.warning("[ARCH-1.4.44] Catálogo de clubes no legible: se compara por slug literal.")
        return {}
    mapa: Dict[str, str] = {}
    for equipo in equipos:
        slug = _normalizar(equipo.get("canonical_slug"))
        if not slug:
            continue
        for alias in (equipo.get("name"), equipo.get("short_name"), slug):
            clave = _normalizar(alias)
            if clave:
                mapa.setdefault(clave, slug)
    return mapa


def _canonicalizar(valor: Any, mapa: Dict[str, str]) -> str:
    """Traduce un identificador (nombre, nombre corto o slug) a su `canonical_slug`."""
    clave = _normalizar(valor)
    if not clave:
        return ""
    return mapa.get(clave, clave)



# ═════════════════════════════════════════════════════════════════════════════════════════════
# ORIGEN 2 — CORPUS CONGELADO (`h2h_corpus_v1`) · lectura defensiva, cero red
# ═════════════════════════════════════════════════════════════════════════════════════════════
def ruta_corpus_vigente() -> Path:
    """Ruta del corpus congelado (override operativo vía `QBE_H2H_CORPUS`)."""
    override = os.environ.get("QBE_H2H_CORPUS")
    return Path(override) if override else RUTA_CORPUS_H2H


def cargar_corpus_h2h(ruta: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Lee el corpus congelado y devuelve sus partidos; artefacto ilegible ⇒ lista vacía."""
    destino = Path(ruta) if ruta is not None else ruta_corpus_vigente()
    try:
        if not destino.is_file():
            logger.warning("[ARCH-1.4.44] Corpus H2H ausente: %s (memoria degradada).", destino)
            return []
        payload = json.loads(destino.read_text(encoding="utf-8"))
    except (OSError, ValueError) as excepcion:
        logger.warning("[ARCH-1.4.44] Corpus H2H ilegible (%s): %s", destino, excepcion)
        return []
    if not isinstance(payload, dict) or payload.get("esquema") != ESQUEMA_CORPUS_H2H:
        logger.warning("[ARCH-1.4.44] Corpus H2H con esquema ajeno: %s", destino)
        return []
    partidos = payload.get("partidos")
    if not isinstance(partidos, list):
        return []
    return [partido for partido in partidos if isinstance(partido, dict)]


def _como_fecha(valor: Any) -> Optional[datetime]:
    """Interpreta `YYYY-MM-DD` / ISO-8601 / `datetime` sin inventar zona horaria."""
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=None)
    if isinstance(valor, date):
        return datetime(valor.year, valor.month, valor.day)
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).strip().replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _duelo(
    fecha: datetime,
    goles_local: int,
    goles_visita: int,
    fuente: str,
    fecha_ref: datetime,
    es_local_sede: bool = False,
) -> Dict[str, Any]:
    """Empaqueta un enfrentamiento consumado con su antigüedad fáctica (int, nunca negativo).

    `[LN-QBE-105]` `es_local_sede` declara si el club local EVALUADO jugó en su propia sede en
    ese duelo histórico. Es la única fuente de verdad de la localía: la proyección de perspectiva
    de `goles_local`/`goles_visita` la destruye por diseño, de modo que la bandera debe capturarse
    aquí, donde `casa` aún se conoce. `False` = sede no acreditada (cero fabricación).
    """
    return {
        "goles_local": int(goles_local),
        "goles_visita": int(goles_visita),
        "dias_antiguedad": max(0, int((fecha_ref - fecha).days)),
        "fecha": fecha.strftime("%Y-%m-%d"),
        "fuente": fuente,
        "es_local_sede": bool(es_local_sede),
    }


def _desde_corpus(
    partidos: Sequence[Dict[str, Any]],
    local: str,
    visitante: str,
    fecha_ref: datetime,
    mapa: Dict[str, str],
) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
    """Duelos del corpus en la perspectiva del local evaluado, indexados por identidad canónica.

    La clave de deduplicación es `(fecha, local, visitante)` en el espacio canónico: dos capturas
    del mismo partido colapsan en una sola fila (jamás se infla `h2h_conteo`).
    """
    duelos: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for partido in partidos:
        casa = _canonicalizar(partido.get("local_slug") or partido.get("local"), mapa)
        fuera = _canonicalizar(partido.get("visitante_slug") or partido.get("visitante"), mapa)
        if {casa, fuera} != {local, visitante} or not casa or not fuera:
            continue
        fecha = _como_fecha(partido.get("fecha"))
        if fecha is None or fecha >= fecha_ref:
            continue  # futuro-ceguera estricta
        try:
            goles_casa = int(partido.get("goles_local"))
            goles_fuera = int(partido.get("goles_visita"))
        except (TypeError, ValueError):
            continue
        goles_local = goles_casa if casa == local else goles_fuera
        goles_visita = goles_fuera if casa == local else goles_casa
        clave = (fecha.strftime("%Y-%m-%d"), casa, fuera)
        duelos[clave] = _duelo(
            fecha, goles_local, goles_visita, FUENTE_CORPUS, fecha_ref,
            es_local_sede=(casa == local),
        )
    return duelos



# ═════════════════════════════════════════════════════════════════════════════════════════════
# ORIGEN 1 — BÓVEDA 3NF (autoridad de marcador) · reutilización íntegra de [ARCH-1.6.13-C]
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _desde_boveda(
    sesion, league_id: int, local: str, visitante: str, fecha_ref: datetime, mapa: Dict[str, str]
) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
    """Marcadores oficiales persistidos, acotados al conocimiento del kickoff evaluado.

    Las filas de `_precargar_historial_consumado_sqlite` portan nombres de exhibición; aquí se
    traducen al espacio canónico con `_canonicalizar` (puente de identidad, causa raíz del 0).
    """
    if sesion is None:
        return {}
    try:
        from scripts.utilidades.poblar_temporada_completa_backtesting import _historial_future_blind

        historial = _historial_future_blind(sesion, int(league_id), fecha_ref)
    except Exception as excepcion:  # pragma: no cover — bóveda no disponible: sigue el corpus
        logger.warning("[ARCH-1.4.44] Bóveda 3NF no consultable: %s", excepcion)
        return {}

    duelos: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for fila in historial:
        casa = _canonicalizar(fila.get("local"), mapa)
        fuera = _canonicalizar(fila.get("visitante"), mapa)
        if {casa, fuera} != {local, visitante} or not casa or not fuera:
            continue
        fecha = _como_fecha(fila.get("fecha"))
        if fecha is None or fecha >= fecha_ref:
            continue
        try:
            goles_casa = int(fila.get("goles_local"))
            goles_fuera = int(fila.get("goles_visita"))
        except (TypeError, ValueError):
            continue
        goles_local = goles_casa if casa == local else goles_fuera
        goles_visita = goles_fuera if casa == local else goles_casa
        clave = (fecha.strftime("%Y-%m-%d"), casa, fuera)
        duelos[clave] = _duelo(
            fecha, goles_local, goles_visita, FUENTE_BOVEDA, fecha_ref,
            es_local_sede=(casa == local),
        )
    return duelos


# ═════════════════════════════════════════════════════════════════════════════════════════════
# CONTRATO PÚBLICO [ARCH-1.4.44]
# ═════════════════════════════════════════════════════════════════════════════════════════════
def obtener_h2h_unificado(
    sesion,
    local: Any,
    visitante: Any,
    fecha_ref: Any,
    *,
    league_id: int = LIGA_ID_CANONICA,
    limite: int = LIMITE_DUELOS_H2H,
    ruta_corpus: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Los `limite` enfrentamientos directos más recientes entre dos clubes, previos al kickoff.

    Entradas
    --------
    * `sesion`: sesión SQLAlchemy de SÓLO LECTURA (bóveda 3NF). `None` ⇒ se sirve únicamente el
      corpus congelado (ruta hermenéutica de test y de arranque sin base de datos).
    * `local` / `visitante`: slug canónico, nombre de exhibición o nombre corto. Ambos flujos se
      canonicalizan contra `teams`, de modo que el llamador puede pasar cualquiera de las formas.
    * `fecha_ref`: kickoff del fixture evaluado (`datetime`, `date`, ISO-8601). `None` ⇒ `[]`.

    Salidas
    -------
    Lista ordenada del duelo más reciente al más antiguo, cada fila con
    `goles_local`, `goles_visita` (perspectiva del local evaluado), `dias_antiguedad` (int ≥ 0),
    `fecha` (`YYYY-MM-DD`), `fuente` (`boveda_3nf` | `corpus_congelado`) y `es_local_sede`
    (`True` si el local evaluado jugó en su propia sede en ese duelo histórico [`LN-QBE-105`]).
    Sin evidencia verificable ⇒ lista vacía (Ley Zero-H2H `[LN-QBE-020-B]`, cero fabricación).
    """
    fecha_kickoff = _como_fecha(fecha_ref)
    if fecha_kickoff is None:
        return []

    mapa = _mapa_identidad(sesion, league_id)
    club_local = _canonicalizar(local, mapa)
    club_visita = _canonicalizar(visitante, mapa)
    if not club_local or not club_visita or club_local == club_visita:
        return []

    # Precedencia: la bóveda entra primero; el corpus sólo rellena identidades ausentes.
    duelos: Dict[Tuple[str, str, str], Dict[str, Any]] = _desde_boveda(
        sesion, league_id, club_local, club_visita, fecha_kickoff, mapa
    )
    for clave, duelo in _desde_corpus(
        cargar_corpus_h2h(ruta_corpus), club_local, club_visita, fecha_kickoff, mapa
    ).items():
        duelos.setdefault(clave, duelo)

    tope = int(limite) if isinstance(limite, int) and limite > 0 else LIMITE_DUELOS_H2H
    ordenados = sorted(duelos.values(), key=lambda fila: fila["dias_antiguedad"])
    return [{campo: fila[campo] for campo in CAMPOS_DUELO} for fila in ordenados[:tope]]


def sintetizar_h2h(
    duelos: Sequence[Dict[str, Any]], tau_dias: float = TAU_H2H_DIAS
) -> Dict[str, Any]:
    """Resumen de la ventana H2H con la ponderación profunda delegada a `[LN-QBE-020-C]`.

    Devuelve `conteo` (int), `fuentes` (orígenes presentes) y el símplex
    LOCAL/EMPATE/VISITA ponderado con τ_deep = 540 d. Sin duelos: `conteo = 0` y símplex `None`
    (ignorancia declarada, cero relleno sintético).
    """
    ventana: List[Dict[str, Any]] = [dict(fila) for fila in (duelos or [])]
    fuentes = sorted({str(fila.get("fuente")) for fila in ventana if fila.get("fuente")})
    resumen: Dict[str, Any] = {
        "conteo": len(ventana),
        "limite": LIMITE_DUELOS_H2H,
        "tau_dias": float(tau_dias),
        "fuentes": fuentes,
        "p_local": None,
        "p_empate": None,
        "p_visita": None,
        "peso_total_efectivo": None,
    }
    if not ventana:
        return resumen
    matriz = calcular_matriz_h2h_empirica(ventana, tau_dias=tau_dias)
    resumen.update({
        "p_local": float(matriz.p_local),
        "p_empate": float(matriz.p_empate),
        "p_visita": float(matriz.p_visita),
        "peso_total_efectivo": float(matriz.peso_total_efectivo),
    })
    return resumen
