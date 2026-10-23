# -*- coding: utf-8 -*-
"""
Kybern Industrial — Sprint 1 (v13.5): Sincronización de la Fuente Única y Matriz Canónica de
Investigación.

[LN-QBE-127] UNIVERSO AUDITABLE SIN DESCARTE SILENCIOSO
    `matches` es la fuente única de verdad de la calibración: un partido CONCLUIDO con marcador
    consumado que no porta P′ sellada (ni en el snapshot de captura ni en la tabla soberana) deja
    de ser descartado con un `continue` mudo y se resuelve AL VUELO por el motor soberano
    (`generar_distribucion_soberana`) — cuyo prior de ignorancia R-1 es (0.3333, 0.3333, 0.3334).
    La resolución se DECLARA (`origen_p_prima = "AL_VUELO"`, `suficiencia_S_I = 0`) y se cuenta
    (`partidos_resueltos_al_vuelo`): cero invención, cero descarte invisible [GOVERNANCE-01].

[ARCH-1.4.67] MATRIZ CANÓNICA DE INVESTIGACIÓN (`research_feature_matrix.csv`)
    Instrumento CLI-FIRST de lectura pura sobre cuatro zonas disjuntas:
      · A — identidad y contexto del partido;
      · B — 64 celdas fácticas PRE-KICKOFF (catálogo de 32 variables × {local, visita});
      · C — distribución soberana PRE-KICKOFF (P′, vértices Δ², ΔAlt, S(I));
      · D — etiquetas CONSUMADAS en la cancha (marcador, triada, Brier).
    La frontera A∪B∪C (features) ∩ D (etiquetas) = ∅ es la garantía anti-fuga del dataset.

Régimen: [HÍBRIDO DUAL-TRACK] — el vector P′ y el Brier se DELEGAN en sus planos canónicos
(`sovereign_pipeline`, `portfolio_math`); la composición de la matriz y la CLI son [DBBD-FUNGIBLE].

[GOV-TEST-01] Hermetismo: cero red, cero navegador, cero tokens. La prueba conductual del
descarte silencioso usa una bóveda SQLite EFÍMERA en memoria; el espejo contra el Visor lee la
bóveda viva en modo `read_session()` (cero DML).
"""

import inspect
import os

import pytest

RUTA_MARKETS = os.path.join("src", "web", "routes", "markets.py")
RUTA_SCRIPT = os.path.join("scripts", "investigacion", "generar_matriz_investigacion.py")

# Prior de ignorancia fiduciario R-1 ([LN-QBE-075]): el único vector que el motor puede emitir
# sin una sola celda de evidencia. Se cita como CONSTANTE LEGISLADA, jamás como cálculo local.
PRIOR_IGNORANCIA_R1 = (0.3333, 0.3333, 0.3334)

# Tokens que delatan una etiqueta consumada dentro de la frontera de features (anti-fuga).
TOKENS_DE_ETIQUETA = (
    "score",
    "goles",
    "resultado_real",
    "brier",
    "clasificacion",
    "tipo_resultado",
    "acierto",
)


def _fuente(ruta: str) -> str:
    """Lectura textual de un artefacto del repositorio (Guardián de código)."""
    assert os.path.exists(ruta), f"🚨 Artefacto ausente: {ruta}"
    with open(ruta, encoding="utf-8") as archivo:
        return archivo.read()


def _fuente_funcion(nombre: str) -> str:
    """Código fuente de una función viva de `markets.py` (el Juez audita lo EJECUTADO)."""
    from src.web.routes import markets

    return inspect.getsource(getattr(markets, nombre))


def _boveda_efimera():
    """Sesión ORM sobre una bóveda SQLite EFÍMERA en memoria (hermetismo [GOV-TEST-01])."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from src.storage import models  # noqa: F401  (registro del universo ORM en el metadata)
    from src.storage.database import Base

    motor = create_engine("sqlite://", future=True)
    Base.metadata.create_all(bind=motor)
    return sessionmaker(bind=motor, autocommit=False, autoflush=False)()

# ── [LN-QBE-127] UNIVERSO AUDITABLE SIN DESCARTE SILENCIOSO ───────────────────


def test_ln_qbe_127_resolucion_al_vuelo_delega_en_el_motor_soberano():
    """[LN-QBE-127] El P′ al vuelo NO se inventa: es el que publica `generar_distribucion_soberana`.

    Guardián de código (la cláusula derogada no sobrevive como rama muerta) + prueba conductual
    de delegación: sin fixture ni traza, el resolvedor devuelve EXACTAMENTE el prior R-1.
    """
    from src.storage.models import Match
    from src.web.routes.markets import _p_prima_al_vuelo

    fuente = _fuente_funcion("_construir_reporte_calibracion")
    assert "_p_prima_al_vuelo(" in fuente, (
        "🚨 [LN-QBE-127] El reporte de calibración debe resolver P′ al vuelo antes de descartar "
        "un partido concluido."
    )
    assert "partidos_resueltos_al_vuelo" in _fuente_funcion("_agregar_resumen_calibracion"), (
        "🚨 [LN-QBE-127] La resolución al vuelo debe CONTARSE en el agregado macro."
    )
    assert "Sin captura sellada de P' el partido no es auditable" not in fuente, (
        "🚨 [LN-QBE-127] Cláusula derogada: el descarte silencioso no puede sobrevivir como "
        "rama muerta ni como comentario de contrato."
    )
    assert "generar_distribucion_soberana" in _fuente(RUTA_MARKETS), (
        "🚨 [DIRGEN-STRICT] El resolvedor debe DELEGAR en el motor soberano sellado."
    )

    partido = Match(
        id="MATCH_JUEZ_AL_VUELO",
        competition_id="MEX_LIGAMX",
        matchday_num=11,
        home_team_slug="club-puebla",
        away_team_slug="club-toluca",
        status="FINALIZADO",
    )
    obtenido = _p_prima_al_vuelo(partido, None, None)

    assert obtenido is not None, (
        "🚨 [LN-QBE-127] Sin traza ni fixture el motor soberano SIEMPRE puede emitir el prior "
        "R-1: devolver `None` reintroduce el descarte silencioso."
    )
    assert tuple(round(float(valor), 4) for valor in obtenido) == PRIOR_IGNORANCIA_R1
    assert pytest.approx(sum(obtenido), abs=1e-9) == 1.0, (
        "🚨 El vector resuelto debe habitar el símplex Δ² (suma 1.0)."
    )


def test_ln_qbe_127_partido_concluido_sin_distribucion_no_se_descarta():
    """[LN-QBE-127] Conductual: el universo auditable cubre TODO partido concluido con marcador.

    Bóveda efímera con dos partidos concluidos —uno con distribución soberana sellada y otro sin
    NINGUNA evidencia P′—: ambos entran al Visor, el segundo declarado `AL_VUELO` con S(I)=0 y el
    primero intacto (la resolución al vuelo JAMÁS degrada la evidencia capturada).
    """
    from src.storage.models import Competition, Match, SovereignDistribution
    from src.web.routes.markets import _construir_reporte_calibracion

    sesion = _boveda_efimera()
    try:
        # Padre relacional: la bóveda efímera hereda el PRAGMA de FK del Gateway (fail-loud).
        sesion.add(Competition(id="MEX_LIGAMX", name="Liga MX", country="México"))
        sesion.add(Match(
            id="MATCH_JUEZ_CAPTURADO",
            competition_id="MEX_LIGAMX",
            matchday_num=4,
            home_team_slug="club-puebla",
            away_team_slug="club-toluca",
            status="FINALIZADO",
            score_home=2,
            score_away=0,
        ))
        sesion.add(Match(
            id="MATCH_JUEZ_SIN_DISTRIBUCION",
            competition_id="MEX_LIGAMX",
            matchday_num=11,
            home_team_slug="club-pachuca",
            away_team_slug="club-tigres",
            status="FINALIZADO",
            score_home=1,
            score_away=1,
        ))
        sesion.add(SovereignDistribution(
            match_id="MATCH_JUEZ_CAPTURADO",
            p_local=0.5,
            p_empate=0.3,
            p_visitante=0.2,
            lambda_home=1.4,
            lambda_away=1.0,
            epistemic_delta=0.02,
        ))
        sesion.commit()

        informe = _construir_reporte_calibracion(sesion)
        resumen = informe["resumen_global"]

        assert resumen["total_partidos"] == 2, (
            "🚨 [LN-QBE-127] `matches` es la fuente única: ningún partido concluido con marcador "
            "puede quedar fuera del universo auditable."
        )
        assert resumen["partidos_pendientes_captura"] == 0, (
            "🚨 [LN-QBE-127] Un partido resuelto al vuelo NO es una captura pendiente."
        )
        assert resumen["partidos_resueltos_al_vuelo"] == 1, (
            "🚨 [LN-QBE-127] La resolución dinámica debe declararse y contarse."
        )

        micro = {
            partido["id_partido"]: partido
            for jornada in informe["jornadas"]
            for partido in jornada["partidos"]
        }

        volatil = micro["MATCH_JUEZ_SIN_DISTRIBUCION"]
        assert volatil["origen_p_prima"] == "AL_VUELO"
        assert volatil["suficiencia_S_I"] == 0, (
            "🚨 [GOVERNANCE-01] Un P′ resuelto al vuelo ES el prior de ignorancia: declararlo "
            "informado (S=1) fabricaría una calibración inexistente."
        )
        assert (
            volatil["p_local"], volatil["p_empate"], volatil["p_visitante"]
        ) == PRIOR_IGNORANCIA_R1

        capturado = micro["MATCH_JUEZ_CAPTURADO"]
        assert capturado["origen_p_prima"] == "SOBERANA"
        assert capturado["suficiencia_S_I"] == 1
        assert capturado["p_local"] == 0.5

        assert informe["resumen_calibrado"]["total_partidos"] == 1, (
            "🚨 [LN-QBE-125] El segmento informado sólo admite evidencia real (S=1)."
        )
    finally:
        sesion.close()


# ── [ARCH-1.4.67] MATRIZ CANÓNICA DE INVESTIGACIÓN ────────────────────────────


def test_arch_1_4_67_matriz_cuatro_zonas_sin_fuga_de_etiquetas():
    """[ARCH-1.4.67] Contrato estructural: cuatro zonas disjuntas y features ∩ etiquetas = ∅."""
    from scripts.investigacion import generar_matriz_investigacion as matriz

    assert matriz.ZONAS == ("A", "B", "C", "D"), (
        "🚨 [ARCH-1.4.67] La matriz canónica declara exactamente cuatro zonas."
    )

    zona_a, zona_b = matriz.COLUMNAS_ZONA_A, matriz.COLUMNAS_ZONA_B
    zona_c, zona_d = matriz.COLUMNAS_ZONA_C, matriz.COLUMNAS_ZONA_D
    assert len(zona_b) == 64, (
        "🚨 [ARCH-1.4.67] Zona B = catálogo de 32 variables × 2 lados = 64 celdas "
        f"(hoy {len(zona_b)})."
    )
    assert len(set(matriz.COLUMNAS_MATRIZ)) == len(matriz.COLUMNAS_MATRIZ), (
        "🚨 [ARCH-1.4.67] Encabezado duplicado: dos zonas publican la misma columna."
    )
    assert list(matriz.COLUMNAS_MATRIZ) == list(zona_a + zona_b + zona_c + zona_d), (
        "🚨 [ARCH-1.4.67] El encabezado se DERIVA de las zonas, no se transcribe a mano."
    )

    features = set(zona_a) | set(zona_b) | set(zona_c)
    etiquetas = set(zona_d)
    assert not (features & etiquetas), (
        f"🚨 FUGA DE ETIQUETAS: columnas en ambas fronteras: {sorted(features & etiquetas)}"
    )
    for columna in sorted(features):
        delator = [token for token in TOKENS_DE_ETIQUETA if token in columna]
        assert not delator, (
            f"🚨 FUGA DE ETIQUETAS: la columna de features '{columna}' delata {delator}."
        )


def test_arch_1_4_67_matriz_es_lectura_pura_y_tarea_certificada():
    """[ARCH-1.4.67] Cero DML, cero red, cero navegador; la tarea vive en la whitelist sellada."""
    from src.web.routes.admin_tasks import COMANDOS_TAREAS, TAREAS_PERMITIDAS

    fuente = _fuente(RUTA_SCRIPT)
    for prohibido in ("write_transaction", "session.commit(", "requests", "playwright", "urllib"):
        assert prohibido not in fuente, (
            f"🚨 [ARCH-1.4.67] La matriz de investigación es LECTURA PURA: prohibido `{prohibido}`."
        )
    assert "read_session" in fuente, (
        "🚨 [ARCH-1.4.67] El acceso a la bóveda pasa por `PersistenceGateway.read_session()`."
    )

    assert "generar_matriz_investigacion" in TAREAS_PERMITIDAS
    assert COMANDOS_TAREAS["generar_matriz_investigacion"] == [
        ["scripts", "investigacion", "generar_matriz_investigacion.py"]
    ], "🚨 [ARCH-1.4.67] La tarea despacha un único ejecutor atómico del repositorio."
    assert os.path.exists(os.path.join("scripts", "investigacion", "__init__.py")), (
        "🚨 [ARCH-1.4.67] El paquete `scripts/investigacion/` debe ser importable."
    )

    plantilla = _fuente(os.path.join("src", "web", "templates", "index.html"))
    assert "ejecutarTareaAdmin('generar_matriz_investigacion')" in plantilla, (
        "🚨 [ARCH-1.4.67] La tarea certificada debe ser invocable desde el Centro de Control."
    )


def test_arch_1_4_67_matriz_espeja_al_visor_sobre_la_boveda_viva():
    """[ARCH-1.4.67] Espejo de una sola verdad: la matriz reproduce el Visor fila por fila.

    Lee la bóveda viva en modo `read_session()` y exige: (i) el piso certificado de 97 partidos
    concluidos, (ii) cardinalidad idéntica al `resumen_global`, (iii) paridad exacta de la zona C
    con el micro-DTO del Visor y (iv) las 64 celdas de la zona B presentes en toda fila.
    """
    from scripts.investigacion.generar_matriz_investigacion import construir_matriz_investigacion
    from src.storage.gateway import PersistenceGateway
    from src.web.routes.markets import _construir_reporte_calibracion

    with PersistenceGateway().read_session() as sesion:
        filas = construir_matriz_investigacion(sesion)
        informe = _construir_reporte_calibracion(sesion)

    assert len(filas) >= 97, (
        "🚨 [ARCH-1.4.67] Piso certificado de la temporada: 97 partidos concluidos "
        f"(hoy {len(filas)})."
    )
    assert len(filas) == informe["resumen_global"]["total_partidos"], (
        "🚨 [ARCH-1.4.67] Segunda verdad: la matriz y el Visor deben auditar el MISMO universo."
    )

    micro = {
        partido["id_partido"]: partido
        for jornada in informe["jornadas"]
        for partido in jornada["partidos"]
    }
    assert set(micro.keys()) == {fila["match_id"] for fila in filas}, (
        "🚨 [ARCH-1.4.67] Universo divergente entre la matriz y el micro-DTO del Visor."
    )

    for fila in filas:
        referencia = micro[fila["match_id"]]
        assert fila["jornada"] == referencia["jornada"]
        assert fila["p_local"] == referencia["p_local"]
        assert fila["p_empate"] == referencia["p_empate"]
        assert fila["p_visitante"] == referencia["p_visitante"]
        assert fila["r_max"] == referencia["r_max"]
        assert fila["r_mid"] == referencia["r_mid"]
        assert fila["r_low"] == referencia["r_low"]
        assert fila["suficiencia_s_i"] == referencia["suficiencia_S_I"]
        assert fila["origen_p_prima"] == referencia["origen_p_prima"]
        assert fila["resultado_real"] == referencia["resultado_real"]
        assert fila["clasificacion_triada"] == referencia["clasificacion_triada"]
        assert fila["brier_qbe"] == referencia["brier_qbe"]
        faltantes = [columna for columna in fila["_zonas"]["B"] if columna not in fila]
        assert not faltantes, f"🚨 [ARCH-1.4.67] Celdas de la zona B ausentes: {faltantes[:5]}"

    celdas_informadas = sum(
        1
        for fila in filas
        for columna in fila["_zonas"]["B"]
        if fila.get(columna) not in (None, "")
    )
    assert celdas_informadas > 0, (
        "🚨 [ARCH-1.4.67] La zona B debe materializar evidencia fáctica real, no una matriz vacía."
    )

