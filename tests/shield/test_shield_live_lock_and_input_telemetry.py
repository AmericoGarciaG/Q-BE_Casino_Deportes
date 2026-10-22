# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: CANDADO EN VIVO (`LIVE_PROTECTION_LOCK`) Y TELEMETRÍA DE INSUMOS FÁCTICOS
Gobierno: `docs/LOGIC.md` [LN-QBE-102] / `docs/ARCH.md` [ARCH-1.4.43] / `docs/DESIGN.md` [DES-QBE-065]

Régimen declarado (Dual-Track honesto):
* `[DIRGEN-STRICT]` — `src/core/sovereign_pipeline.py` (empaquetado de insumos) y
  `src/storage/distribution_sync.py` (candado transaccional). Sólo se validan claves ADITIVAS:
  ninguna fórmula sellada ([VAULT-CORE-001], [VAULT-CORE-003], [VAULT-CORE-004]) se re-calcula aquí.
* `[DBBD-FUNGIBLE]` — exhibición del sello de procedencia y colorimetría del estado `EVALUADO`.

Aislamiento hermético: cero red, cero navegador, cero tokens. El gateway se materializa en memoria
(`sqlite://`) con el metamodelo real de producción, jamás con dobles de prueba en rutas de código.
"""

from contextlib import contextmanager
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.storage.models import Base, Competition, Match, SovereignDistribution
from src.storage.distribution_sync import sincronizar_distribuciones_soberanas_partidos

RAIZ = Path(__file__).resolve().parents[2]
APP_JS = RAIZ / "src" / "web" / "static" / "js" / "app.js"
INDEX_HTML = RAIZ / "src" / "web" / "templates" / "index.html"
THEME_CSS = RAIZ / "src" / "web" / "static" / "css" / "theme.css"


class _GatewayMemoria:
    """Gateway hermético sobre `sqlite://` con el metamodelo REAL (`Base.metadata`)."""

    def __init__(self) -> None:
        self._engine = create_engine("sqlite://")
        Base.metadata.create_all(self._engine)
        self._sesiones = sessionmaker(bind=self._engine)

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


def _payload(match_id: str, gf_local: int = 14, gc_local: int = 6,
             gf_visita: int = 9, gc_visita: int = 12, **extra) -> dict:
    """Registro fáctico de prueba (Puebla vs Atlante): sólo insumos publicados, cero invención."""
    datos = {
        "match_id": match_id,
        "competition_id": "MEX_LIGAMX",
        "home_team_slug": "puebla",
        "away_team_slug": "atlante",
        "home_team_stats": {
            "pj": 8, "gf": gf_local, "gc": gc_local,
            "xg": 12.8, "xga": 8.0, "sot": 40, "sota": 32, "possession": 53.5,
        },
        "away_team_stats": {
            "pj": 8, "gf": gf_visita, "gc": gc_visita,
            "xg": 8.8, "xga": 12.0, "sot": 24, "sota": 32, "possession": 46.5,
        },
        "home_split_stats": {"pj": 4},
        "away_split_stats": {"pj": 4},
        "h2h_matches": [
            {"dias_antiguedad": 120, "goles_local": 2, "goles_visita": 1},
            {"dias_antiguedad": 260, "goles_local": 1, "goles_visita": 1},
            {"dias_antiguedad": 400, "goles_local": 0, "goles_visita": 2},
        ],
    }
    datos.update(extra)
    return datos


def _insumos_vivos(h2h_conteo: int = 4, delta_alt: float = 2240.0, delta_descanso: float = 0.0) -> dict:
    """Paquete de telemetría tal como lo emite `_empaquetar_insumos_factivados`."""
    return {
        "xg_local_rate": 1.6, "xg_visita_rate": 1.1,
        "xga_local_rate": 1.0, "xga_visita_rate": 1.5,
        "gc_local_rate": 0.75, "gc_visita_rate": 1.5,
        "sot_local": 5.0, "sot_visita": 3.0,
        "sota_local": 4.0, "sota_visita": 4.0,
        "poss_local": 53.5, "poss_visita": 46.5,
        "pj_sede_local": 4, "pj_sede_visita": 4,
        "h2h_conteo": h2h_conteo,
        "q_mod_h": 1.0, "q_mod_a": 1.0,
        "delta_alt_metros": delta_alt, "delta_descanso_dias": delta_descanso,
        "xg_es_real_opta": True,
    }


def _crear_competicion(gw: _GatewayMemoria) -> None:
    with gw.write_transaction() as tx:
        tx.add(Competition(
            id="MEX_LIGAMX", name="Liga MX", country="México",
            macro_mu_liga=2.65, macro_gamma_home=0.15,
        ))


# ── Inversión 1: el candado veta la degradación de procedencia (asimetría estricta) ────────────
def test_candado_en_vivo_no_sobreescribe_evidencia_capturada_en_ventanilla():
    gw = _GatewayMemoria()
    _crear_competicion(gw)
    with gw.write_transaction() as tx:
        tx.add(Match(
            id="M_LIVE_01", competition_id="MEX_LIGAMX", matchday_num=9,
            home_team_slug="puebla", away_team_slug="atlante", status="SCHEDULED",
        ))

    vivo = sincronizar_distribuciones_soberanas_partidos(
        [_payload("M_LIVE_01")], gateway=gw, origen_captura="EN_VIVO"
    )
    assert vivo["exitosos"] == 1
    assert vivo["protegidos"] == 0

    with gw.read_session() as sesion:
        capturada = sesion.query(SovereignDistribution).filter_by(match_id="M_LIVE_01").one()
        p_local_en_vivo = capturada.p_local
        lambda_h_en_vivo = capturada.lambda_home
        assert capturada.audit_trace_json["origen_captura"] == "EN_VIVO"
        assert capturada.audit_trace_json["insumos_factivados"]["h2h_conteo"] == 3

    # Reconstrucción histórica con un vector fáctico DISTINTO y marcador oficial.
    historico = _payload(
        "M_LIVE_01", gf_local=60, gc_local=1, gf_visita=2, gc_visita=40,
        score_home=2, score_away=1,
    )
    veto = sincronizar_distribuciones_soberanas_partidos(
        [historico], gateway=gw, origen_captura="HISTORICO_RECONSTRUIDO"
    )
    assert veto["protegidos"] == 1, "El candado debe vetar la sobreescritura histórica de evidencia EN_VIVO."
    assert veto["exitosos"] == 0

    with gw.read_session() as sesion:
        preservada = sesion.query(SovereignDistribution).filter_by(match_id="M_LIVE_01").one()
        assert preservada.p_local == p_local_en_vivo
        assert preservada.lambda_home == lambda_h_en_vivo
        assert preservada.audit_trace_json["origen_captura"] == "EN_VIVO"
        # Excepción del Hecho Consumado: sólo el marcador oficial de `matches`.
        partido = sesion.query(Match).filter_by(id="M_LIVE_01").one()
        assert (partido.score_home, partido.score_away, partido.status) == (2, 1, "FINISHED")

    # Asimetría: la re-captura EN_VIVO sí actualiza (no es un candado de sólo lectura).
    recaptura = sincronizar_distribuciones_soberanas_partidos(
        [_payload("M_LIVE_01", gf_local=20)], gateway=gw, origen_captura="EN_VIVO"
    )
    assert recaptura["exitosos"] == 1
    assert recaptura["protegidos"] == 0


# ── Inversión 2: telemetría de insumos veraz (el número declarado es el consumido) ────────────
def test_insumos_factivados_declaran_la_magnitud_realmente_consumida():
    from src.core.sovereign_pipeline import generar_distribucion_soberana

    publicado = _payload("M_TEL_01", delta_alt_metros=2240.0, xg_es_real_opta=True)
    salida = generar_distribucion_soberana(
        match_id="M_TEL_01", raw_match_data=publicado, origen_captura="EN_VIVO"
    )
    traza = salida.audit_trace.model_dump()

    assert traza["origen_captura"] == "EN_VIVO"
    insumos = traza["insumos_factivados"]
    assert isinstance(insumos, dict), "El generador debe empaquetar `insumos_factivados` [LN-QBE-102]."
    assert insumos["delta_alt_metros"] == 2240.0
    assert insumos["delta_descanso_dias"] == 0.0
    assert insumos["pj_sede_local"] == 4
    assert insumos["pj_sede_visita"] == 4
    assert insumos["h2h_conteo"] == 3
    assert insumos["xg_es_real_opta"] is True
    assert insumos["xg_local_rate"] == pytest.approx(12.8 / 8, abs=1e-9)
    assert insumos["xga_local_rate"] == pytest.approx(8.0 / 8, abs=1e-9)

    # La telemetría declara EXACTAMENTE el número que consumió la matemática (cero maquillaje):
    # parámetro explícito == magnitud publicada por el registro ⇒ traza idéntica.
    explicito = generar_distribucion_soberana(
        match_id="M_TEL_01", raw_match_data=_payload("M_TEL_01", xg_es_real_opta=True),
        delta_alt_metros=2240.0,
    )
    assert explicito.audit_trace.insumos_factivados["delta_alt_metros"] == 2240.0
    assert explicito.lambda_home == salida.lambda_home
    assert explicito.audit_trace.insumos_factivados["xg_es_real_opta"] is True

    # Rama de ignorancia S(I)=0: la telemetría también se emite y NADA se inventa.
    ignorancia = generar_distribucion_soberana(
        match_id="M_TEL_02",
        raw_match_data={"home_team_stats": {"pj": 1}, "away_team_stats": {"pj": 1}},
        origen_captura="EN_VIVO",
    )
    assert ignorancia.audit_trace.suficiencia_S_I == 0
    assert ignorancia.audit_trace.origen_captura == "EN_VIVO"
    assert ignorancia.audit_trace.insumos_factivados["xg_local_rate"] is None
    assert ignorancia.audit_trace.insumos_factivados["h2h_conteo"] == 0


# ── Inversión 3: los cinco semáforos se pronuncian sobre el insumo publicado ──────────────────
def test_semaforos_se_pronuncian_con_la_telemetria_publicada():
    from src.core.sovereign.factor_attribution import construir_atribucion_factorial

    traza = {
        "factores_entrada": {"A_home": 0.35, "D_away": -0.12, "A_away": 0.05, "D_home": 0.18},
        "intensidades": {"lambda_home": 1.65, "lambda_away": 1.10, "ratio": 1.5},
        "discrepancia_epist": 0.018,
        "suficiencia_S_I": 1,
        "origen_captura": "EN_VIVO",
        "insumos_factivados": _insumos_vivos(h2h_conteo=4),
    }
    atribucion = construir_atribucion_factorial({"audit_trace": traza, "delta_epist": 0.018})
    semaforos = atribucion["semaforos"]

    assert semaforos["opta"] == "VERDE", "xG real de Opta publicado ⇒ verde."
    assert semaforos["sede"] == "VERDE", "PJ de sede bilateral ≥ 3 (gate GSL-3D) ⇒ verde."
    assert semaforos["h2h"] == "AMARILLO", "4 duelos < ventana normativa de 5 ⇒ ámbar."
    assert semaforos["epist"] == "VERDE"
    assert semaforos["ctx"] == "VERDE", "Q_mod = 1.00 publicado ⇒ verde."
    assert atribucion["origen_captura"] == "EN_VIVO"


# ── Inversión 4: catálogo de 32 variables [LN-QBE-120] con las ocho variables vivas ──────────
def test_catalogo_44_ilumina_las_ocho_variables_vivas_sin_fabricar():
    from src.core.sovereign.factor_attribution import estructurar_catalogo_44_variables

    catalogo = estructurar_catalogo_44_variables({
        "insumos_factivados": _insumos_vivos(h2h_conteo=5, delta_alt=2660.0, delta_descanso=3.0),
    })
    planas = {v["id"]: v for d in catalogo["dimensiones"] for v in d["variables"]}
    assert len(planas) == 32

    esperado = {
        "V01": "53.5%",
        "V06": "1.60",
        "V07": "5",
        "V12": "1.00",
        "V13": "4",
        "V30": "+3.0 d",
        "V29": "2660m",
        "V26": "5 partidos",
    }
    for identificador, valor in esperado.items():
        assert planas[identificador]["local"] == valor, f"{identificador} no exhibe el insumo fáctico."
        assert planas[identificador]["estado"] == "EVALUADO", f"{identificador} debe encenderse en EVALUADO."

    assert planas["V26"]["visita"] is None, "La ventana H2H es contexto de la serie, no bilateral."
    assert planas["V08"]["estado"] == "SIN EVIDENCIA", "Cero fabricación: V08 no publicada."

    # Regresión dura: sin el paquete telemetrizado la ruta heredada permanece intacta.
    heredado = {
        v["id"]: v
        for d in estructurar_catalogo_44_variables({})["dimensiones"]
        for v in d["variables"]
    }
    assert heredado["V01"]["estado"] == "SIN EVIDENCIA"
    assert heredado["V01"]["local"] is None


# ── Inversión 5: badge de procedencia e iluminación en la capa de presentación ───────────────
def test_ui_exhibe_el_sello_de_procedencia_y_la_iluminacion_de_44_variables():
    app_js = APP_JS.read_text(encoding="utf-8")
    html = INDEX_HTML.read_text(encoding="utf-8")
    css = THEME_CSS.read_text(encoding="utf-8")

    assert "_badgeProcedencia" in app_js, "Falta el constructor del badge de procedencia [DES-QBE-065]."
    assert "badge-procedencia-vivo" in app_js and "EN VIVO" in app_js
    assert "badge-procedencia-hist" in app_js and "HISTÓRICO" in app_js
    assert "origen_captura" in app_js, "La UI debe leer el sello publicado por el DTO."
    assert "EVALUADO" in app_js, "El estado EVALUADO debe existir en la colorimetría forense."
    assert 'id="vars44-origen"' in html, "Falta el sub-rayado de procedencia del modal."
    assert "vars44-origen" in app_js, "El modal debe pintar la procedencia de la evidencia."

    for color in ("#10B981", "#F59E0B", "#EF4444", "#94A3B8"):
        assert color in css, f"Colorimetría Dark Fintech ausente: {color}"
    assert ".badge-procedencia-vivo" in css
    assert ".badge-procedencia-hist" in css
