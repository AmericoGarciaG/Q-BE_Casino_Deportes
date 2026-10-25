# -*- coding: utf-8 -*-
"""
🛡️ JUEZ INMUTABLE: UNIVERSO COMPLETO DE LA TABLA MESO Y SEMÁNTICA DEL FILTRO DE ALTITUD

Gobierno: `docs/ARCH.md` `[ARCH-1.4.38 · Enmienda de Saneamiento]` ·
          `docs/DESIGN.md` `[DES-QBE-072 · Enmienda — Capa 2 · Toggles Fiduciarios]`

Régimen: `[DIRGEN-STRICT]` sobre la ley de universo (cero truncamiento no declarado) y sobre la
aritmética del desnivel (`resolver_orden_fiduciario_con_indiferencia`, INMUTABLE);
`[DBBD-FUNGIBLE]` sobre la capa de presentación (`app.js` / `index.html`).

Invariantes auditadas:
  1. **MESO COMPLETA:** toda jornada con resultado consumado aparece en la tabla meso. Un partido
     con marcador publicado por la captura congelada (`estado`/`is_finished` ⇒ FINALIZADO y
     `marcador_actual` legible) cuya fila 3NF quedó rezagada NO puede desaparecer del Visor.
     Corolario: un partido SIN resultado consumado JAMÁS se inventa (J15 no entra).
  2. **ALTITUD = INCLUSIÓN:** el toggle `#chk-filtro-altitud` no penaliza a los partidos con
     Asedio Territorial Neto (ΔAlt ≥ 1,000 m): los AÍSLA. Queda prohibida la semántica derogada
     que excluía precisamente a los partidos con ventaja física del local y restaba Masa
     Probabilística sin justificación estadística.

Doctrina de la Triple Aserción:
  (1) contrato positivo; (2) Sad Path / control negativo; (3) auto-verificación del juez (el
  detector demuestra que SÍ distingue la conducta prohibida, para no certificar por vacuidad).

Estado esperado en Fase 2: ROJO (la meso se detiene en J11 y el filtro resta masa).
"""

import json
import shutil
import subprocess
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

RAIZ = Path(__file__).resolve().parents[2]
APP_JS = RAIZ / "src" / "web" / "static" / "js" / "app.js"
INDEX_HTML = RAIZ / "src" / "web" / "templates" / "index.html"
NODE = shutil.which("node")

P_L11 = {"p_local": 0.52, "p_empate": 0.27, "p_visitante": 0.21}
P_L13 = {"p_local": 0.49, "p_empate": 0.25, "p_visitante": 0.26}


# ---------------------------------------------------------------------------
# Bóveda efímera (SQLite en memoria) — cero contacto con la bóveda viva.
# ---------------------------------------------------------------------------
def _boveda_efimera():
    """Reproduce el caso real: J11 sellada en 3NF y J13 con resultado sólo en la captura."""
    from src.storage.models import Base, Competition, FixtureSnapshot, League, Match

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(League(id=1, name="Liga MX", country="México", flag="MX", fotmob_id=1))
    session.add(Competition(id="MEX_LIGAMX", name="Liga MX", country="México"))
    session.flush()  # el orden de inserción se declara explícitamente (FK leagues/competitions)

    # J11 — hecho sellado en la bóveda 3NF (estado normalizado FINALIZADO + marcador).
    session.add(
        Match(
            id="TEST-J11-01", competition_id="MEX_LIGAMX", matchday_num=11,
            home_team_slug="chivas-guadalajara", away_team_slug="necaxa",
            status="FINALIZADO", score_home=2, score_away=1,
        )
    )
    # J13 — la fila 3NF quedó rezagada (PROGRAMADO, sin marcador) pero la captura congelada
    # declara el partido FINALIZADO con marcador "1 - 0". Es el defecto que se legisla.
    session.add(
        Match(
            id="TEST-J13-01", competition_id="MEX_LIGAMX", matchday_num=13,
            home_team_slug="chivas-guadalajara", away_team_slug="necaxa",
            status="PROGRAMADO", score_home=None, score_away=None,
        )
    )
    # J15 — por jugar: su captura NO publica resultado. Jamás puede inventarse.
    session.add(
        Match(
            id="TEST-J15-01", competition_id="MEX_LIGAMX", matchday_num=15,
            home_team_slug="chivas-guadalajara", away_team_slug="necaxa",
            status="SCHEDULED", score_home=None, score_away=None,
        )
    )

    session.flush()  # los `matches` deben existir antes de las capturas (orden declarado)

    session.add(
        FixtureSnapshot(
            league_id=1, matchday=11,
            matches_json=[{
                "id_partido": "TEST-J11-01", "local": "Chivas", "visitante": "Necaxa",
                "estado": "FINALIZADO", "is_finished": True, "marcador_actual": "2 - 1",
                "momios": {"L": 1.80, "E": 3.50, "V": 4.20}, "suficiencia_S_I": 1, **P_L11,
            }],
        )
    )
    session.add(
        FixtureSnapshot(
            league_id=1, matchday=13,
            matches_json=[{
                "id_partido": "TEST-J13-01", "local": "Chivas", "visitante": "Necaxa",
                "estado": "FINALIZADO", "is_finished": True, "marcador_actual": "1 - 0",
                "momios": {"L": 1.70, "E": 3.70, "V": 4.60}, "suficiencia_S_I": 1, **P_L13,
            }],
        )
    )
    session.add(
        FixtureSnapshot(
            league_id=1, matchday=15,
            matches_json=[{
                "id_partido": "TEST-J15-01", "local": "Chivas", "visitante": "Necaxa",
                "estado": "PROGRAMADO", "is_finished": False, "marcador_actual": None,
                "suficiencia_S_I": 1, **P_L13,
            }],
        )
    )
    session.commit()
    return session


# ---------------------------------------------------------------------------
# 1. LA TABLA MESO NO TRUNCA JORNADAS CONCLUIDAS
# ---------------------------------------------------------------------------
def test_meso_incluye_todas_las_jornadas_concluidas():
    """[ARCH-1.4.38 · Enmienda] J11 y J13 aparecen; J15 (sin resultado) no se fabrica."""
    from src.web.routes.markets import _construir_reporte_calibracion

    session = _boveda_efimera()
    try:
        reporte = _construir_reporte_calibracion(session)
    finally:
        session.close()

    jornadas = {int(jornada["jornada"]): jornada for jornada in reporte["jornadas"]}

    # -- Aserción 1 (contrato positivo): TODA jornada concluida tiene entrada en la meso --
    faltantes = [jornada for jornada in (11, 13) if jornada not in jornadas]
    assert not faltantes, (
        "🚨 TRUNCAMIENTO NO DECLARADO [ARCH-1.4.38 · Enmienda]: la tabla meso omitió las "
        f"jornadas {faltantes}. J13 tiene marcador consumado en la captura congelada; su "
        "ausencia es una ceguera de universo, no una salvaguarda."
    )
    assert reporte["resumen_temporada"]["total_partidos"] == 2, (
        "El universo auditable no contabilizó exactamente los dos partidos concluidos: "
        f"{reporte['resumen_temporada']['total_partidos']}."
    )

    # El marcador de J13 proviene de la EVIDENCIA congelada, no de una cifra fabricada.
    j13 = jornadas[13]["partidos"]
    assert [(p["id_partido"], p["marcador"]) for p in j13] == [("TEST-J13-01", "1 - 0")], (
        "J13 no recuperó el marcador publicado por la captura (`marcador_actual` = '1 - 0'): "
        f"se sirvió {[(p['id_partido'], p['marcador']) for p in j13]}."
    )
    assert j13[0]["resultado_real"] == "LOCAL", (
        "El desenlace consumado de J13 (1 - 0) debe resolverse LOCAL."
    )

    # -- Aserción 2 (Sad Path): el partido sin resultado consumado NO se inventa --
    assert 15 not in jornadas, (
        "🚨 FABRICACIÓN DE RESULTADO [GOVERNANCE-01]: J15 no tiene marcador consumado y, aun así, "
        "apareció en la tabla meso."
    )
    assert not [p for p in reporte["jornadas"] if p["partidos"] and p["jornada"] == 15], (
        "J15 publicó partidos pese a no tener resultado consumado."
    )

    # -- Aserción 3 (no truncamiento declarado): el conjunto servido es EXACTAMENTE el concluido --
    assert sorted(jornadas) == [11, 13], (
        "El conjunto de jornadas servidas no coincide con el de jornadas con resultado consumado: "
        f"{sorted(jornadas)}."
    )


# ---------------------------------------------------------------------------
# 2. EL FILTRO DE ALTITUD ES DE INCLUSIÓN (no una penalización)
# ---------------------------------------------------------------------------
def _bloque_js(fuente: str, marca: str) -> str:
    """Bloque balanceado `{ … }` que comienza en `marca` (función o literal de objeto)."""
    inicio = fuente.index(marca)
    apertura = fuente.index("{", inicio)
    profundidad = 0
    for posicion in range(apertura, len(fuente)):
        if fuente[posicion] == "{":
            profundidad += 1
        elif fuente[posicion] == "}":
            profundidad -= 1
            if profundidad == 0:
                return fuente[inicio:posicion + 1]
    raise AssertionError(f"Bloque JS no balanceado para `{marca}`.")


def _evaluar_filtro_en_node(tmp_path: Path, logica: str, casos) -> list:
    """Ejecuta la lógica REAL del filtro (extraída de `app.js`) sobre una tabla de casos."""
    assert NODE, "Node.js no está disponible para evaluar la lógica del frontend."
    harness = tmp_path / "harness_filtro_altitud.js"
    harness.write_text(
        'const fs = require("fs");\n'
        f"{logica}\n"
        "function _filtrosVisorActivos() { return { epist: false, altitud: true, fragil: false }; }\n"
        "function _partidoVetadoBacktesting() { return false; }\n"
        "const casos = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));\n"
        "process.stdout.write(JSON.stringify(casos.map("
        "c => _motivoFiltroFiduciarioVisor(c.partido, c.filtros))));\n",
        encoding="utf-8",
    )
    entrada = tmp_path / "casos_filtro_altitud.json"
    entrada.write_text(json.dumps(casos), encoding="utf-8")
    proceso = subprocess.run(
        [NODE, str(harness), str(entrada)],
        capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    assert proceso.returncode == 0, f"El harness JS falló: {proceso.stderr}"
    return json.loads(proceso.stdout)


def _logica_filtro_real() -> str:
    fuente = APP_JS.read_text(encoding="utf-8")
    motivos = _bloque_js(fuente, "const MOTIVOS_EXCLUSION_VISOR = {")
    funcion = _bloque_js(fuente, "function _motivoFiltroFiduciarioVisor(")
    return f"{motivos};\n{funcion};\n"


def _casos_filtro():
    activo = {"epist": False, "altitud": True, "fragil": False}
    inactivo = {"epist": False, "altitud": False, "fragil": False}
    return [
        {"partido": {"delta_alt_metros": 1500, "p_local": 0.55}, "filtros": activo},
        {"partido": {"delta_alt_metros": 1000, "p_local": 0.55}, "filtros": activo},
        {"partido": {"delta_alt_metros": 500, "p_local": 0.55}, "filtros": activo},
        {"partido": {"delta_alt_metros": -150, "p_local": 0.55}, "filtros": activo},
        {"partido": {"delta_alt_metros": 0, "p_local": 0.30}, "filtros": inactivo},
        {"partido": {"delta_alt_metros": 2000, "p_local": 0.30}, "filtros": activo},
    ]


def test_logica_filtro_altitud(tmp_path):
    """[DES-QBE-072 · Enmienda] El Asedio Territorial Neto AÍSLA (incluye), no penaliza."""
    fuente = APP_JS.read_text(encoding="utf-8")
    html = INDEX_HTML.read_text(encoding="utf-8")

    # -- Aserción 1 (contrato positivo): la semántica derogada no sobrevive en el código --
    assert "if (activos.altitud && partido.delta_alt_metros >= 1000) {" not in fuente, (
        "🚨 PENALIZACIÓN DE ALTITUD [DES-QBE-072 · Enmienda]: el toggle sigue EXCLUYENDO a los "
        "partidos con Asedio Territorial Neto (ΔAlt ≥ 1,000 m), que son precisamente los que "
        "gozan de la ventaja física del local."
    )
    assert "activos.altitud && !(partido.delta_alt_metros >= 1000)" in fuente, (
        "El toggle de altitud no declara la guarda de INCLUSIÓN "
        "(`!(delta_alt_metros >= 1000)` ⇒ excluye únicamente a quien NO tiene asedio)."
    )

    # La etiqueta visible declara la inclusión (no un 'Excluir' encubierto).
    assert "sólo ΔAlt ≥ 1,000 m" in html, (
        "🚨 ETIQUETA IMPRECISA: el toggle debe declarar que muestra SÓLO los partidos con "
        "ΔAlt ≥ 1,000 m (filtro de inclusión) o rotularse 'Excluir Asedio'."
    )
    assert "INCLUSIÓN" in html, (
        "La vitrina no declara en su etiqueta/tooltip que el filtro de altitud es de INCLUSIÓN."
    )

    # -- Aserción 2 (conducta real del frontend, ejecutada en Node) --
    motivos = _evaluar_filtro_en_node(tmp_path, _logica_filtro_real(), _casos_filtro())
    con_asedio, frontera, sin_asedio, visitante_favorito, toggle_apagado, fragil = motivos

    assert con_asedio is None, (
        "🚨 ΔAlt = 1,500 m fue EXCLUIDO con el toggle activo: el filtro resta Masa Probabilística "
        "exactamente a los partidos con ventaja física del local."
    )
    assert frontera is None, "La frontera ΔAlt = 1,000 m debe quedar INCLUIDA (≥)."
    assert sin_asedio, "ΔAlt = 500 m debe quedar fuera del aislamiento (motivo publicado)."
    assert "Sin Asedio" in sin_asedio, (
        f"El motivo de exclusión no declara la ausencia de asedio: {sin_asedio!r}"
    )
    assert visitante_favorito, (
        "Un desnivel negativo (ΔAlt = -150 m) no puede contarse como asedio del local."
    )
    assert toggle_apagado is None, (
        "Con el toggle apagado el filtro no debe intervenir (cero penalización latente)."
    )
    assert fragil is None, (
        "Un partido con asedio y favorito frágil debe seguir INCLUIDO si el toggle de fragilidad "
        "está apagado (los filtros son independientes)."
    )

    # -- Aserción 3 (auto-verificación): el detector SÍ reconoce la semántica prohibida --
    logica_derogada = """
const MOTIVOS_EXCLUSION_VISOR = { ALTITUD: "Asedio Territorial Neto (ΔAlt ≥ 1,000 m)" };
function _motivoFiltroFiduciarioVisor(partido, filtros) {
    const activos = filtros || _filtrosVisorActivos();
    if (activos.altitud && partido.delta_alt_metros >= 1000) {
        return MOTIVOS_EXCLUSION_VISOR.ALTITUD;
    }
    return null;
}
"""
    veredicto_derogado = _evaluar_filtro_en_node(tmp_path, logica_derogada, [_casos_filtro()[0]])
    assert veredicto_derogado[0] is not None, (
        "El juez no distingue la semántica derogada: certificaría por vacuidad."
    )


# ---------------------------------------------------------------------------
# 3. AUDITORÍA MATEMÁTICA DEL DESNIVEL (plano sellado, INMUTABLE)
# ---------------------------------------------------------------------------
def test_desnivel_positivo_favorece_al_local():
    """[LN-QBE-124] ΔAlt⁺ = max(0, alt_local − alt_visita) y promueve al LOCAL a P_mid."""
    from src.core.contracts.portfolio_math import (
        BANDA_INDIFERENCIA_EPSILON,
        UMBRAL_ALTITUD_RESCATE_METROS,
        resolver_orden_fiduciario_con_indiferencia,
    )

    # -- Aserción 1: el desnivel se acota a cero y el LOCAL asciende a P_mid en la banda --
    assert UMBRAL_ALTITUD_RESCATE_METROS == 1000.0
    assert BANDA_INDIFERENCIA_EPSILON == 0.0100
    # P′ = (LOCAL 0.31 · EMPATE 0.315 · VISITANTE 0.375): el par en disputa es {EMPATE, LOCAL}.
    con_asedio = resolver_orden_fiduciario_con_indiferencia(0.31, 0.315, 0.375, delta_alt=1500.0)
    assert con_asedio["r_mid"] == "LOCAL" and con_asedio["rescate_indiferencia"] is True
    assert con_asedio["delta_alt_metros"] == 1500.0
    assert con_asedio["p_mid_val"] == 0.31, (
        "La banda debe prometer el vértice LOCAL con SU PROPIA magnitud: cero magnitud inventada."
    )

    # -- Aserción 2 (Sad Path): el desnivel negativo JAMÁS premia al visitante --
    negativo = resolver_orden_fiduciario_con_indiferencia(0.31, 0.315, 0.375, delta_alt=-1500.0)
    assert negativo["delta_alt_metros"] == 0.0
    assert negativo["rescate_indiferencia"] is False
    assert negativo["r_mid"] == "EMPATE"

    # -- Aserción 3: con masas empatadas la permutación es PURA (P_max y Masa invariantes) --
    sin_asedio = resolver_orden_fiduciario_con_indiferencia(0.32, 0.32, 0.36, delta_alt=0.0)
    con_asedio_par = resolver_orden_fiduciario_con_indiferencia(0.32, 0.32, 0.36, delta_alt=2000.0)
    assert con_asedio_par["rescate_indiferencia"] is True
    assert con_asedio_par["p_max_val"] == sin_asedio["p_max_val"] == 0.36
    assert con_asedio_par["masa_cobertura_pct"] == sin_asedio["masa_cobertura_pct"] == 68.0
