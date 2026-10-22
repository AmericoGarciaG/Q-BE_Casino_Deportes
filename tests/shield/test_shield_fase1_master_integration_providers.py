# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: FASE 1 · INTEGRACIÓN MAESTRA DE LOS PROVEEDORES SOBERANOS
Gobierno: `docs/LOGIC.md` [LN-QBE-117] [LN-QBE-108] [LN-QBE-109] [LN-QBE-110] [LN-QBE-111]
          `docs/ARCH.md` [ARCH-1.4.55] · Respaldo atómico de la bóveda

Régimen declarado (Dual-Track honesto):
* `[DIRGEN-STRICT]` — `src/core/sovereign_pipeline.derivar_factores_estructurales` (motor sellado
  [VAULT-CORE-005]) y `src/core/sovereign/attack_defense_core.calcular_colision_fuerzas_cruzadas`
  ([LN-QBE-108]). El Juez NO reimplementa la matemática: la invoca VERBATIM y exige paridad exacta,
  además de certificar que `xga` permanece fuera del `raw_match_data` del motor
  (Decreto `VAR-2026-J7-HOMOLOGACION §E1`).
* `[DBBD-FUNGIBLE]` — orquestación del paquete `insumos_factivados` en `factor_attribution`
  (`empaquetar_insumos_factivados`, `_MAPA_NIDOS_A_PLANO`) y el respaldo atómico del Gateway.

Alcance certificado (Fase 1 de la Integración Maestra):
1. Los cinco sub-bloques legislados (`h2h`, `contexto`, `trayectoria`, `volumen_porteria`,
   `ataque_defensa`) se ANIDAN y sus claves planas heredadas se derivan sin pérdida.
2. Las claves planas encienden EXACTAMENTE las celdas del catálogo de 44 variables [LN-QBE-101]
   que la ruta heredada iluminaba (`EVALUADO` sólo si el insumo real fue consumido).
3. La colisión cruzada publicada es la del plano sellado y el `xGA` sólo se exhibe como V10.
4. Degradación honesta: sin fixture ni evidencia, cero cifras y cero invocación fabricada.
5. `PersistenceGateway.crear_backup_boveda_sqlite` materializa una copia consistente y verificada.

Aislamiento hermético: cero red, cero navegador, cero tokens. El gateway se materializa en memoria
(`sqlite://`) con el metamodelo real de producción y el corpus Opta congelado se inyecta desde
`tmp_path`; jamás se toca `data/` ni la bóveda real (el respaldo se prueba sobre un archivo temporal).
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.core.sovereign.attack_defense_core import (
    calcular_colision_fuerzas_cruzadas,
    obtener_metricas_ataque_defensa,
)
from src.core.sovereign.context_provider import obtener_metricas_contexto
from src.core.sovereign.factor_attribution import (
    SUB_BLOQUES_INSUMOS_FACTIVADOS,
    construir_atribucion_factorial,
    empaquetar_insumos_factivados,
    estructurar_catalogo_44_variables,
)
from src.core.sovereign.telemetry_provider import obtener_metricas_volumen_porteria
from src.core.sovereign.trajectory_provider import obtener_metricas_trayectoria
from src.core.sovereign_pipeline import derivar_factores_estructurales
from src.storage.gateway import PersistenceGateway
from src.storage.models import (
    Base,
    Competition,
    League,
    Match,
    MatchTelemetry,
    StandingSnapshot,
)

RAIZ = Path(__file__).resolve().parents[2]

MATCH_ID = "LIGAMX-J17-01"
LOCAL = "puebla"
VISITA = "tigres"
TEMPORADA = "2026"
JORNADA = 17
MU_LIGA = 2.65
KICKOFF_EVALUADO = datetime(2026, 4, 20, 19, 0)

# 6 jornadas previas por club (3 como local / 3 como visitante ⇒ gate GSL-3D de sede satisfecho).
_JORNADAS_HISTORICAS = (11, 12, 13, 14, 15, 16)
_RIVALES = ("america", "monterrey", "toluca", "cruz-azul", "pumas", "chivas-guadalajara")
# Marcadores REALES declarados (goles a favor / goles en contra del club rastreado).
_RESULTADOS_LOCAL = ((2, 1), (1, 1), (0, 2), (3, 0), (1, 0), (2, 2))
_RESULTADOS_VISITA = ((3, 1), (1, 2), (2, 0), (0, 0), (1, 3), (2, 1))

# ═════════════════════════════════════════════════════════════════════════════════════════════
# BÓVEDA HERMÉTICA: metamodelo REAL sobre `sqlite://` (cero dobles en rutas de código)
# ═════════════════════════════════════════════════════════════════════════════════════════════
class _GatewayMemoria:
    """Gateway de prueba sobre `sqlite://` con `Base.metadata` de producción."""

    def __init__(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self._sesiones = sessionmaker(bind=self.engine)

    @contextmanager
    def read_session(self):
        sesion = self._sesiones()
        try:
            yield sesion
        finally:
            sesion.close()

    @contextmanager
    def write_transaction(self):
        sesion = self._sesiones()
        try:
            yield sesion
            sesion.commit()
        except Exception:
            sesion.rollback()
            raise
        finally:
            sesion.close()


def _xg_de(goles_favor: int, goles_contra: int, indice: int) -> tuple:
    """Serie Opta congelada declarada (xG ≠ GF y xGA ≠ GC: evita el respaldo por identidad)."""
    xg = round(0.85 * float(goles_favor) + 0.55 + 0.05 * float(indice), 2)
    xga = round(0.85 * float(goles_contra) + 0.70 + 0.03 * float(indice), 2)
    return xg, xga


def _partido_historico(
    club: str,
    rival: str,
    jornada: int,
    es_local: bool,
    goles_favor: int,
    goles_contra: int,
    kickoff: datetime,
) -> Match:
    """Fixture TERMINAL del corte N−1 con marcador real (futuro-ciego por `matchday_num`)."""
    local, visita = (club, rival) if es_local else (rival, club)
    return Match(
        id=f"HIST-{club.upper()}-J{jornada:02d}",
        competition_id="MEX_LIGAMX",
        matchday_num=jornada,
        kickoff_utc=kickoff,
        home_team_slug=local,
        away_team_slug=visita,
        status="FINALIZADO",
        score_home=goles_favor if es_local else goles_contra,
        score_away=goles_contra if es_local else goles_favor,
    )



def _sembrar_boveda(gw: _GatewayMemoria, ruta_corpus: Path) -> None:
    """Siembra la cartelera factual mínima: fixture evaluado, 12 partidos terminales, corpus y
    telemetría 3NF con cobertura ÍNTEGRA (una sola fila faltante apagaría la tasa completa)."""
    with gw.write_transaction() as tx:
        tx.add(
            Competition(
                id="MEX_LIGAMX",
                name="Liga MX",
                country="México",
                macro_mu_liga=MU_LIGA,
                macro_gamma_home=0.15,
            )
        )
        tx.add(League(id=1, name="Liga MX", country="México", flag="MX", fotmob_id=262))
        tx.add(
            Match(
                id=MATCH_ID,
                competition_id="MEX_LIGAMX",
                matchday_num=JORNADA,
                kickoff_utc=KICKOFF_EVALUADO,
                home_team_slug=LOCAL,
                away_team_slug=VISITA,
                status="PROGRAMADO",
            )
        )

    corpus = {}
    with gw.write_transaction() as tx:
        for club, resultados, base in (
            (LOCAL, _RESULTADOS_LOCAL, datetime(2026, 4, 9, 19, 0)),
            (VISITA, _RESULTADOS_VISITA, datetime(2026, 4, 5, 19, 0)),
        ):
            for indice, (jornada, marcador) in enumerate(zip(_JORNADAS_HISTORICAS, resultados)):
                es_local = indice % 2 == 0
                rival = _RIVALES[indice]
                goles_favor, goles_contra = marcador
                partido = _partido_historico(
                    club,
                    rival,
                    jornada,
                    es_local,
                    goles_favor,
                    goles_contra,
                    base + timedelta(days=indice),
                )
                tx.add(partido)
                xg, xga = _xg_de(goles_favor, goles_contra, indice)
                xg_rival, xga_rival = _xg_de(goles_contra, goles_favor, indice)
                propio = {"xg": xg, "xga": xga}
                ajeno = {"xg": xg_rival, "xga": xga_rival}
                corpus[partido.id] = (
                    {"home": propio, "away": ajeno}
                    if es_local
                    else {"home": ajeno, "away": propio}
                )
                tx.add(
                    MatchTelemetry(
                        match_id=partido.id,
                        team_slug=club,
                        sot=float(4 + indice % 3),
                        sota=float(5 - indice % 2),
                        possession_pct=(
                            (58.0 if es_local else 48.0)
                            if club == LOCAL
                            else (54.0 if es_local else 44.0)
                        ),
                    )
                )
        tx.add(
            StandingSnapshot(
                league_id=1,
                season=TEMPORADA,
                matchday=16,
                positions_json=[
                    {"equipo": "Puebla", "pj": 6, "puntos": 11, "xpts": 9.2},
                    {"equipo": "Tigres UANL", "pj": 6, "puntos": 10, "xpts": 11.4},
                ],
            )
        )

    ruta_corpus.write_text(
        json.dumps(
            {
                "generado_at": "2026-04-16T00:00:00+00:00",
                "fuente": "corpus_congelado_certificacion_fase1",
                "partidos": corpus,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


@pytest.fixture()
def boveda(tmp_path: Path):
    """Bóveda hermética sembrada + ruta del corpus congelado (aislada por prueba)."""
    gw = _GatewayMemoria()
    ruta_corpus = tmp_path / f"cache_optaxg_liga_mx_{TEMPORADA}.json"
    _sembrar_boveda(gw, ruta_corpus)
    return gw, ruta_corpus


def _bloques(boveda) -> dict:
    """Los sub-bloques tal como los publican los proveedores canónicos (sólo lectura)."""
    gw, ruta_corpus = boveda
    with gw.read_session() as sesion:
        contexto = obtener_metricas_contexto(sesion, MATCH_ID, temporada=TEMPORADA)
        trayectoria = obtener_metricas_trayectoria(
            sesion, MATCH_ID, temporada=TEMPORADA, ruta_corpus=str(ruta_corpus)
        )
        volumen = obtener_metricas_volumen_porteria(sesion, MATCH_ID, temporada=TEMPORADA)
        ataque = obtener_metricas_ataque_defensa(
            sesion,
            MATCH_ID,
            temporada=TEMPORADA,
            ruta_corpus=str(ruta_corpus),
            mu_liga=MU_LIGA,
        )
    return {
        "contexto": contexto,
        "trayectoria": trayectoria,
        "volumen_porteria": volumen,
        "ataque_defensa": ataque,
    }


def _bloque_h2h() -> dict:
    """Sub-bloque `h2h` factual (3 duelos verificables dentro de la ventana τ = 540 d)."""
    return {
        "bloque": "h2h",
        "match_id": MATCH_ID,
        "status": "EXITO",
        "insumos": {
            "h2h_conteo": 3,
            "h2h_stats": {
                "record_general": "2-1-0",
                "dif_goles": "+2",
                "record_sede": "1-0-0",
            },
        },
        "variables": {"V26": {"id": "V26", "estado": "EVALUADO"}},
    }


def _paquete(boveda) -> dict:
    """Paquete `insumos_factivados` ANIDADO + claves planas (orquestación unificada)."""
    return empaquetar_insumos_factivados(h2h=_bloque_h2h(), **_bloques(boveda))


def _crudo_del_motor(bloque: dict, incluir_xga: bool) -> dict:
    """Reconstruye el `raw_match_data` de la ruta sellada desde los cortes PUBLICADOS.

    `incluir_xga=True` documenta el contra-fáctico: el motor sellado SÍ consumiría `xga` si se le
    entregara, de ahí la prohibición del Decreto `VAR-2026-J7-HOMOLOGACION §E1`.
    """
    cortes = bloque["cortes"]

    def _stats(corte: dict) -> dict:
        datos = {
            "pj": corte["pj"],
            "gf": corte["gf"],
            "gc": corte["gc"],
            "pts": corte["pts"],
        }
        if corte["xg_total"] is not None:
            datos["xg"] = corte["xg_total"]
        if incluir_xga and corte["xga_total"] is not None:
            datos["xga"] = corte["xga_total"]
        return datos

    return {
        "home_team_stats": _stats(cortes["local"]),
        "away_team_stats": _stats(cortes["visita"]),
        "home_split_stats": dict(cortes["local"]["splits_sede"]["como_local"]),
        "away_split_stats": dict(cortes["visita"]["splits_sede"]["como_visitante"]),
        "xg_es_real_opta": True,
    }



# ═════════════════════════════════════════════════════════════════════════════════════════════
# LEY 1 · Los cinco sub-bloques legislados publican el contrato [LN-QBE-117]
# ═════════════════════════════════════════════════════════════════════════════════════════════
def test_bloques_proveedores_publican_contrato_legislado(boveda):
    """Cada proveedor declara su identidad, su `status` y sus `insumos` planos (cero fabricación)."""
    assert SUB_BLOQUES_INSUMOS_FACTIVADOS == (
        "h2h",
        "contexto",
        "trayectoria",
        "volumen_porteria",
        "ataque_defensa",
    ), "El orden de anidado es parte del contrato [ARCH-1.4.55]."
    bloques = _bloques(boveda)
    for nombre, bloque in bloques.items():
        assert isinstance(bloque, dict), f"El proveedor `{nombre}` no publicó bloque."
        assert bloque.get("status") in ("EXITO", "PARCIAL", "SIN EVIDENCIA"), nombre
        assert isinstance(bloque.get("insumos"), dict) and bloque["insumos"], nombre
        assert bloque.get("escritura_bd", False) is False, nombre

    # Shape homogéneo de los proveedores de métricas + contrato propio de trayectoria.
    for nombre in ("contexto", "volumen_porteria", "ataque_defensa"):
        assert bloques[nombre]["bloque"] == nombre
        assert bloques[nombre]["match_id"] == MATCH_ID
        assert isinstance(bloques[nombre]["variables"], dict) and bloques[nombre]["variables"]
    trayectoria = bloques["trayectoria"]
    assert trayectoria["proveedor"] == "TRAJECTORY_PROVIDER"
    assert set(trayectoria["dimension_8_trayectoria"]) == {"V31", "AUX_M_XG", "AUX_M_XGA", "V32"}

    ataque = bloques["ataque_defensa"]
    assert ataque["status"] == "EXITO", ataque.get("motivo")
    assert ataque["insumos"]["cobertura_opta_local"]["cubiertos"] == 6
    assert ataque["insumos"]["cobertura_opta_visita"]["cubiertos"] == 6
    assert ataque["insumos"]["cobertura_telemetria_local"]["cubiertos"] == 6
    assert ataque["insumos"]["xg_es_real_opta"] is True
    # Las 4 celdas de la fase con feed íntegro en AMBOS cortes quedan EVALUADAS.
    for identificador in ("V06", "V07", "V12", "V13"):
        assert ataque["variables"][identificador]["estado"] == "EVALUADO"
        assert ataque["variables"][identificador]["local"] is not None
        assert ataque["variables"][identificador]["visita"] is not None
    # Fase 6: sin feed en la bóveda ⇒ apagadas, con la nota honesta (los AUX_* sin celda incluidos).
    for identificador in ("V08", "V09", "AUX_XGOT_90", "AUX_PPDA", "V15", "V16"):
        celda = ataque["variables"][identificador]
        assert celda["estado"] == "SIN EVIDENCIA", identificador
        assert celda["local"] is None and celda["visita"] is None


def test_cobertura_integra_declara_cero_faltantes(boveda):
    """6/6 por club y por métrica: la tasa completa se sostiene (sin muestras perdidas)."""
    ataque = _bloques(boveda)["ataque_defensa"]
    for lado in ("local", "visita"):
        corte = ataque["cortes"][lado]
        assert corte["pj"] == 6
        assert corte["cobertura_xg"]["faltantes"] == []
        assert corte["cobertura_sot"]["faltantes"] == []
        assert corte["cobertura_xg"]["cubiertos"] == corte["cobertura_xg"]["total"] == 6
        assert corte["cobertura_sot"]["cubiertos"] == corte["cobertura_sot"]["total"] == 6
        # Split de sede futuro-ciego: 3 PJ por plaza (gate GSL-3D satisfecho).
        assert corte["splits_sede"]["como_local"]["pj"] == 3
        assert corte["splits_sede"]["como_visitante"]["pj"] == 3


def test_trayectoria_y_contexto_publican_sus_celdas(boveda):
    """`V31`/`V32` + `AUX_*` (trayectoria) y `V29`/`V30` + `AUX_*` (contexto) viven en sus proveedores."""
    bloques = _bloques(boveda)
    trayectoria = bloques["trayectoria"]
    assert trayectoria["proveedor"] == "TRAJECTORY_PROVIDER"
    assert trayectoria["escritura_bd"] is False and trayectoria["llamadas_red"] is False
    propias = trayectoria["dimension_8_trayectoria"]
    assert set(propias) == {"V31", "AUX_M_XG", "AUX_M_XGA", "V32"}
    for identificador, celda in propias.items():
        assert celda["id"] == identificador
        assert celda["estado"] in ("EVALUADO", "SIN EVIDENCIA")
    assert propias["V32"]["puntos_local"] is not None
    assert propias["V32"]["diagnostico_local"] is not None
    assert trayectoria["insumos"]["pts_last5_local"] is not None
    assert trayectoria["insumos"]["xg_trend_local"] is not None
    assert trayectoria["corte_n_1"]["muestra_local"] >= 3

    contexto = bloques["contexto"]
    assert contexto["bloque"] == "contexto"
    assert set(contexto["variables"]) == {"AUX_XG_BAJAS", "AUX_XGA_BAJAS", "V30", "V29"}
    for clave in (
        "delta_descanso_dias",
        "delta_alt_metros",
        "q_mod_h",
        "q_mod_a",
        "lambda_contextual_home",
        "lambda_contextual_away",
        "gamma_contextual",
    ):
        assert contexto["insumos"][clave] is not None, clave


# ═════════════════════════════════════════════════════════════════════════════════════════════
# LEY 2 · El paquete ANIDADO deriva las claves PLANAS heredadas sin pérdida [ARCH-1.4.55]
# ═════════════════════════════════════════════════════════════════════════════════════════════
_PLANAS_DEL_CONTRATO = (
    ("ataque_defensa", "xg_local_rate"),
    ("ataque_defensa", "xg_visita_rate"),
    ("ataque_defensa", "xga_local_rate"),
    ("ataque_defensa", "xga_visita_rate"),
    ("ataque_defensa", "gc_local_rate"),
    ("ataque_defensa", "gc_visita_rate"),
    ("ataque_defensa", "sot_local"),
    ("ataque_defensa", "sot_visita"),
    ("ataque_defensa", "sota_local"),
    ("ataque_defensa", "sota_visita"),
    ("ataque_defensa", "pj_sede_local"),
    ("ataque_defensa", "pj_sede_visita"),
    ("volumen_porteria", "poss_local"),
    ("volumen_porteria", "poss_visita"),
    ("h2h", "h2h_conteo"),
    ("h2h", "h2h_stats"),
)

# Celdas del catálogo de 32 variables [LN-QBE-120] que la Fase 1 enciende con evidencia REAL:
# posesión (V01), xG (V06), SoT (V07), xGA (V12), SoT recibidos (V13), Δdescanso (V30),
# Δaltitud (V29) y el conteo H2H (V26). El remapeo [LN-QBE-120] no altera magnitud alguna.
# transcriben al paquete plano (su proveedor las publica en `dimension_8_trayectoria`).
_EVALUADAS_FASE_1 = frozenset(
    {"V01", "V06", "V07", "V12", "V13", "V26", "V27", "V28", "V29", "V30"}
)


def test_paquete_anida_los_cinco_bloques_y_deriva_planas(boveda):
    """Cada sub-bloque viaja ÍNTEGRO y su magnitud real reaparece en la raíz plana."""
    paquete = _paquete(boveda)
    for nombre in SUB_BLOQUES_INSUMOS_FACTIVADOS:
        assert isinstance(paquete[nombre], dict), f"El sub-bloque `{nombre}` no viajó íntegro."
    for nombre in ("h2h", "contexto", "volumen_porteria", "ataque_defensa"):
        assert paquete[nombre]["bloque"] == nombre
    assert paquete["trayectoria"]["proveedor"] == "TRAJECTORY_PROVIDER"
    for sub_bloque, clave in _PLANAS_DEL_CONTRATO:
        anidado = paquete[sub_bloque]["insumos"][clave]
        assert paquete[clave] == anidado, f"{clave} no se derivó del sub-bloque `{sub_bloque}`."
        assert paquete[clave] is not None, f"{clave} derivó en None (cero fabricación)."
    # Ω: la colisión cruzada viaja SÓLO en su sub-bloque (el mapa legislado no la aplana).
    insumos_ataque = paquete["ataque_defensa"]["insumos"]
    for clave in ("A_home", "D_away", "empuje_ofensivo_local", "diferencial_neto_partido"):
        assert clave not in paquete, f"`{clave}` no pertenece al contrato plano [ARCH-1.4.55]."
        assert insumos_ataque[clave] is not None


def test_claves_heredadas_mandan_y_none_raiz_no_borra_evidencia(boveda):
    """`claves_heredadas` manda; un `None` raíz no puede borrar la evidencia anidada real."""
    bloques = _bloques(boveda)
    real_xga = bloques["ataque_defensa"]["insumos"]["xga_local_rate"]
    paquete = empaquetar_insumos_factivados(
        h2h=_bloque_h2h(),
        **bloques,
        claves_heredadas={"xg_local_rate": 1.2345, "xga_local_rate": None},
    )
    assert paquete["xg_local_rate"] == 1.2345      # la ruta heredada gana
    assert paquete["xga_local_rate"] == real_xga   # el `None` no destruye el xGA publicado


def test_paquete_sin_bloques_degrada_sin_fabricar():
    """Sin proveedores el paquete sigue siendo honesto: cinco nidos vacíos y cero claves."""
    paquete = empaquetar_insumos_factivados(h2h=None, contexto={}, trayectoria=None)
    for nombre in SUB_BLOQUES_INSUMOS_FACTIVADOS:
        assert nombre in paquete
    assert "xg_local_rate" not in paquete
    assert "poss_local" not in paquete
    assert paquete["ataque_defensa"] is None


def test_catalogo_44_enciende_exactamente_las_celdas_consumidas(boveda):
    """V01/V06/V07/V12/V13/V26/V27/V28/V29/V30 ([LN-QBE-120]) y NINGUNA otra celda se enciende."""
    catalogo = estructurar_catalogo_44_variables({"insumos_factivados": _paquete(boveda)})
    assert catalogo["total_variables"] == 32
    evaluadas = {
        fila["id"]
        for dimension in catalogo["dimensiones"]
        for fila in dimension["variables"]
        if fila["estado"] == "EVALUADO"
    }
    assert evaluadas == set(_EVALUADAS_FASE_1)
    assert catalogo["total_evaluadas"] == len(evaluadas)
    # Fase 6: el xGOT y demás métricas sin feed permanecen apagadas tras la integración
    # ([LN-QBE-120] V08/V09/V10 relevan a V07/V08/V09; V14/V15/V16 relevan a V12/V13/V14).
    for identificador in ("V08", "V09", "V10", "V14", "V15", "V16"):
        assert identificador not in evaluadas


def test_catalogo_identico_con_paquete_solo_anidado(boveda):
    """El consumidor aplana el paquete sólo anidado: mismas celdas, cero ruptura [ARCH-1.4.55]."""
    completo = _paquete(boveda)
    solo_anidado = {nombre: completo[nombre] for nombre in SUB_BLOQUES_INSUMOS_FACTIVADOS}
    assert "xg_local_rate" not in solo_anidado

    def _evaluadas(datos):
        catalogo = estructurar_catalogo_44_variables({"insumos_factivados": datos})
        return {
            (fila["id"], fila["local"], fila["visita"])
            for dimension in catalogo["dimensiones"]
            for fila in dimension["variables"]
            if fila["estado"] == "EVALUADO"
        }

    assert _evaluadas(solo_anidado) == _evaluadas(completo)


def test_volumen_porteria_hereda_claves_planas(boveda):
    """V01/V06/V07 se encienden con las claves heredadas del bloque de telemetría."""
    volumen = _bloques(boveda)["volumen_porteria"]
    insumos = volumen["insumos"]
    assert insumos["poss_local"] == pytest.approx(53.0, abs=1e-6)
    assert insumos["poss_visita"] == pytest.approx(49.0, abs=1e-6)
    assert insumos["poss_diff"] == pytest.approx(4.0, abs=1e-6)
    assert insumos["sot_local"] is not None and insumos["sota_visita"] is not None
    assert volumen["semaforo"]["cubiertos_local"] == volumen["semaforo"]["total_local"] == 6
    assert volumen["semaforo"]["glifo"] == "🟢"



# ═════════════════════════════════════════════════════════════════════════════════════════════
# LEY 3 · [DIRGEN-STRICT] Paridad VERBATIM con el plano sellado y decreto §E1
# ═════════════════════════════════════════════════════════════════════════════════════════════
def test_motor_sellado_paridad_verbatim_y_xga_fuera_del_crudo(boveda):
    """Los factores publicados son los del motor sellado invocado con el crudo SIN `xga`.

    [VAULT-CORE-005] + Decreto `VAR-2026-J7-HOMOLOGACION §E1`: `xga` permanece fuera del
    `raw_match_data`; si se inyectara, el diagnóstico defensivo certificado cambiaría.
    """
    ataque = _bloques(boveda)["ataque_defensa"]
    sin_xga = _crudo_del_motor(ataque, incluir_xga=False)
    con_xga = _crudo_del_motor(ataque, incluir_xga=True)
    assert "xga" not in sin_xga["home_team_stats"]
    assert sin_xga["xg_es_real_opta"] is True

    esperado = derivar_factores_estructurales(sin_xga, mu_liga=MU_LIGA)
    publicado = (
        ataque["factores"]["A_home"],
        ataque["factores"]["D_away"],
        ataque["factores"]["A_away"],
        ataque["factores"]["D_home"],
    )
    assert math.isclose(publicado[0], float(esperado[0]), rel_tol=0.0, abs_tol=1e-9)
    assert math.isclose(publicado[1], float(esperado[1]), rel_tol=0.0, abs_tol=1e-9)
    assert math.isclose(publicado[2], float(esperado[2]), rel_tol=0.0, abs_tol=1e-9)
    assert math.isclose(publicado[3], float(esperado[3]), rel_tol=0.0, abs_tol=1e-9)

    contaminado = derivar_factores_estructurales(con_xga, mu_liga=MU_LIGA)
    assert not all(
        math.isclose(float(contaminado[i]), float(esperado[i]), rel_tol=0.0, abs_tol=1e-9)
        for i in range(4)
    ), "El decreto §E1 exige que `xga` altere el resultado: si no altera, la prueba es vacua."

    # El xGA SÍ se publica como evidencia V12 (no entra al motor, pero no se oculta).
    pj_local = ataque["cortes"]["local"]["pj"]
    assert ataque["variables"]["V12"]["estado"] == "EVALUADO"
    assert ataque["variables"]["V12"]["local"] == pytest.approx(
        round(ataque["cortes"]["local"]["xga_total"] / pj_local, 6), abs=1e-4
    )
    assert "xga" not in ataque["factores"]["mezcla_sellada"]


def test_colision_cruzada_invariantes_del_plano_sellado(boveda):
    """A_H − D_A, A_A − D_H y su diferencia: signo, magnitud y bando dominante consistentes."""
    ataque = _bloques(boveda)["ataque_defensa"]
    factores = ataque["factores"]
    colision = ataque["colision"]
    A_h, D_a = factores["A_home"], factores["D_away"]
    A_a, D_h = factores["A_away"], factores["D_home"]

    esperado_local = round(A_h - D_a, 6)
    esperado_visita = round(A_a - D_h, 6)
    assert colision["empuje_ofensivo_local"] == pytest.approx(esperado_local, abs=1e-6)
    assert colision["empuje_ofensivo_visita"] == pytest.approx(esperado_visita, abs=1e-6)
    assert colision["diferencial_neto_partido"] == pytest.approx(
        esperado_local - esperado_visita, abs=1e-6
    )
    assert colision["magnitud_colision"] == pytest.approx(
        abs(esperado_local) + abs(esperado_visita), abs=1e-6
    )
    if abs(colision["diferencial_neto_partido"]) <= 1e-12:
        assert colision["bando_dominante"] == "NEUTRO"
    elif colision["diferencial_neto_partido"] > 0:
        assert colision["bando_dominante"] == "LOCAL"
    else:
        assert colision["bando_dominante"] == "VISITANTE"
    # La colisión publicada es función EXACTA de sus propios factores.
    recomputada = calcular_colision_fuerzas_cruzadas(A_h, D_a, A_a, D_h)
    assert recomputada["diferencial_neto_partido"] == colision["diferencial_neto_partido"]
    assert recomputada["bando_dominante"] == colision["bando_dominante"]


def test_atribucion_factorial_unificada_sobre_el_paquete(boveda):
    """La consola forense consume el paquete anidado: conservación aditiva y semáforos reales."""
    bloques = _bloques(boveda)
    ataque = bloques["ataque_defensa"]
    contexto = bloques["contexto"]["insumos"]
    datos = {
        "insumos_factivados": _paquete(boveda),
        "factores": dict(ataque["factores"]),
        "intensidades": {
            "lambda_home": contexto["lambda_contextual_home"],
            "lambda_away": contexto["lambda_contextual_away"],
        },
        "gamma_home": contexto["gamma_contextual"],
    }
    atribucion = construir_atribucion_factorial(datos)

    assert atribucion["disponible"] is True
    assert atribucion["origen_factores"] == "analitico_base"
    descomposicion = atribucion["descomposicion_log"]
    assert descomposicion["delta_neto_total"] == pytest.approx(
        descomposicion["delta_ofensiva"]
        + descomposicion["delta_defensiva"]
        + descomposicion["delta_contexto"],
        abs=1e-6,
    )
    assert atribucion["driver_principal"]["dimension"] in ("OFENSIVA", "DEFENSIVA", "CONTEXTO")
    assert atribucion["semaforos"] == {
        "opta": "VERDE",
        "sede": "VERDE",
        "h2h": "AMARILLO",
        "epist": "VERDE",
        "ctx": "VERDE",
    }
    catalogo = atribucion["variables_44"]
    assert catalogo["total_variables"] == 32
    evaluadas = {
        fila["id"]
        for dimension in catalogo["dimensiones"]
        for fila in dimension["variables"]
        if fila["estado"] == "EVALUADO"
    }
    assert evaluadas == set(_EVALUADAS_FASE_1)
    # El paquete anidado alimenta la consola forense sin recortes: la evidencia es idéntica.
    catalogo_directo = estructurar_catalogo_44_variables({"insumos_factivados": _paquete(boveda)})
    assert catalogo_directo["total_evaluadas"] == len(evaluadas)



# ═════════════════════════════════════════════════════════════════════════════════════════════
# LEY 4 · Degradación honesta: cobertura rota ⇒ tasa completa apagada (cero promedio parcial)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def test_una_fila_faltante_apaga_la_tasa_completa(boveda):
    """Una sola fila del corpus sin `xg`/`xga` deja V06 y V12 SIN EVIDENCIA (sin promedio parcial)."""
    gw, ruta_corpus = boveda
    corpus = json.loads(ruta_corpus.read_text(encoding="utf-8"))
    victima = "HIST-PUEBLA-J13"
    assert victima in corpus["partidos"]
    del corpus["partidos"][victima]
    ruta_corpus.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")

    with gw.read_session() as sesion:
        ataque = obtener_metricas_ataque_defensa(
            sesion,
            MATCH_ID,
            temporada=TEMPORADA,
            ruta_corpus=str(ruta_corpus),
            mu_liga=MU_LIGA,
        )

    corte_local = ataque["cortes"]["local"]
    assert corte_local["cobertura_xg"]["faltantes"] == [victima]
    assert corte_local["cobertura_xg"]["cubiertos"] == 5
    assert corte_local["xg_total"] is None and corte_local["xga_total"] is None
    assert ataque["insumos"]["xg_local_rate"] is None
    assert ataque["insumos"]["xga_local_rate"] is None
    assert ataque["variables"]["V06"]["estado"] == "SIN EVIDENCIA"
    assert ataque["variables"]["V06"]["local"] is None
    assert ataque["variables"]["V12"]["estado"] == "SIN EVIDENCIA"
    # La telemetría 3NF sigue íntegra: V07/V13 NO se apagan por un hueco de otra fuente.
    assert ataque["variables"]["V07"]["estado"] == "EVALUADO"
    assert ataque["variables"]["V13"]["estado"] == "EVALUADO"
    assert ataque["status"] == "PARCIAL"
    # Cero fabricación: el motor sellado sólo recibe `xg` presente o nada.
    assert "xg" not in _crudo_del_motor(ataque, incluir_xga=False)["home_team_stats"]


def test_bloque_vacio_sin_fixture_no_invoca_al_motor(boveda, monkeypatch):
    """Sin fixture: `SIN EVIDENCIA`, factores en None y el motor sellado JAMÁS se invoca."""
    gw, ruta_corpus = boveda
    from src.core.sovereign import attack_defense_core as modulo

    def _prohibido(*_args, **_kwargs):
        raise AssertionError("El motor sellado no puede invocarse sobre un corte vacío.")

    monkeypatch.setattr(modulo, "derivar_factores_estructurales", _prohibido)
    with gw.read_session() as sesion:
        vacio = modulo.obtener_metricas_ataque_defensa(
            sesion, "NO-EXISTE-J99", temporada=TEMPORADA, ruta_corpus=str(ruta_corpus)
        )

    assert vacio["bloque"] == "ataque_defensa"
    assert vacio["status"] == "SIN EVIDENCIA"
    assert vacio["fixture"] is None
    assert vacio["colision"] is None
    assert all(
        vacio["factores"][clave] is None for clave in ("A_home", "D_away", "A_away", "D_home")
    )
    assert vacio["cortes"] == {"local": None, "visita": None}
    assert vacio["insumos"]["xg_local_rate"] is None
    assert all(celda["estado"] == "SIN EVIDENCIA" for celda in vacio["variables"].values())

    paquete = empaquetar_insumos_factivados(ataque_defensa=vacio)
    assert paquete.get("xg_local_rate") is None
    assert paquete["ataque_defensa"]["status"] == "SIN EVIDENCIA"
    catalogo = estructurar_catalogo_44_variables({"insumos_factivados": paquete})
    assert catalogo["total_evaluadas"] == 0


# ═════════════════════════════════════════════════════════════════════════════════════════════
# LEY 5 · [ARCH-1.4.55] Respaldo atómico y VERIFICADO de la bóveda SQLite
# ═════════════════════════════════════════════════════════════════════════════════════════════
def _gateway_huerfano(url: str) -> PersistenceGateway:
    """Instancia NO singleton con un motor arbitrario (jamás toca `settings` ni la bóveda viva)."""
    gateway = object.__new__(PersistenceGateway)
    gateway.engine = create_engine(url, connect_args={"check_same_thread": False})
    return gateway


def test_backup_boveda_sqlite_materializa_copia_verificada(boveda_gateway_aislada, tmp_path):
    """La copia existe, pasa `PRAGMA quick_check`, replica el esquema y NO muta el original."""
    gw = boveda_gateway_aislada
    origen = Path(str(gw.engine.url.database)).resolve()
    assert origen.is_file(), "El arnés debe operar sobre la bóveda clonada en disco."

    destino = gw.crear_backup_boveda_sqlite(str(tmp_path / "backups"))
    archivo = Path(destino)
    assert archivo.is_file()
    assert archivo.parent.name == "backups"
    assert re.match(
        r"^qbe_database_backup_\d{8}_\d{6}\.db$", archivo.name
    ), f"Nombre de respaldo fuera de norma: {archivo.name}"

    def _resumen(ruta: Path) -> tuple:
        with sqlite3.connect(str(ruta)) as con:
            assert con.execute("PRAGMA quick_check;").fetchone()[0] == "ok"
            tablas = tuple(
                sorted(
                    fila[0]
                    for fila in con.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
                    )
                )
            )
            partidos = con.execute("SELECT COUNT(*) FROM matches;").fetchone()[0]
        return tablas, partidos

    copia = _resumen(archivo)
    assert copia[0] == _resumen(origen)[0] and copia[0], "La copia debe declarar el esquema 3NF."
    assert copia[1] == _resumen(origen)[1], "La copia debe replicar íntegra la cartelera."



def test_backup_rechaza_bovedas_sin_archivo_fisico(tmp_path):
    """`sqlite://` en memoria no tiene nada que respaldar: `RuntimeError`, cero copias vacías."""
    gateway = _gateway_huerfano("sqlite://")
    try:
        with pytest.raises(RuntimeError, match="memoria"):
            gateway.crear_backup_boveda_sqlite(str(tmp_path / "backups"))
    finally:
        gateway.engine.dispose()
    assert not list((tmp_path / "backups").glob("*.db"))


def test_backup_rechaza_motores_no_sqlite(tmp_path):
    """Un motor no SQLite declara su rechazo en vez de fabricar un respaldo ficticio."""
    gateway = _gateway_huerfano("postgresql+psycopg2://usuario:clave@localhost:5432/qbe")
    try:
        with pytest.raises(RuntimeError, match="SQLite"):
            gateway.crear_backup_boveda_sqlite(str(tmp_path / "backups"))
    finally:
        gateway.engine.dispose()
    assert not list((tmp_path / "backups").glob("*.db"))

