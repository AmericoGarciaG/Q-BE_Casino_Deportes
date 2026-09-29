# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: DESPACHO DE MERCADO CON FUENTE SOBERANA FÁCTICA
[GOVERNANCE-01] / [ARCH-1.4.10] / DIRECTIVA P.I.R. Fast-Track Ruta 01
Régimen: [HÍBRIDO DUAL-TRACK] — [DIRGEN-STRICT] en la transcripción del triaje;
[DBBD-FUNGIBLE] en la hidratación del despacho desde el snapshot fáctico.

Twin-Test: `AbstractTestMarketDispatchSovereignSource` declara las 4 leyes;
`TestMarketDispatchSovereignSource` las materializa.

Ley 1 [SHIELD-AST] `generate_sportsbook_portfolio_endpoint` tiene PROHIBIDO sembrar
        probabilidades sintéticas: ningún `if/else` del endpoint puede caer a un literal
        flotante en (0,1) — la distribución viaja del `FixtureSnapshot.matches_json`
        (estrato fáctico) o, en su defecto, de la 3NF `sovereign_distributions`.
Ley 2 [GOVERNANCE-01] Sin estrato no hay cartera: el partido va a cuarentena con el
        contrato canónico `_descartar_partido` (QBE-00 / $0.00 MXN / cero cuotas inventadas).
Ley 3 [LN-QBE-070-C] `sovereign_distributions.epistemic_delta` NO es Δ_epist del Contrato
        R-1: almacena el ratio de intensidades λ_max/λ_min (verificado en bóveda:
        0.42 … 3.75, fuera del rango legislado Δ ∈ [0,1)), por lo que NO se transcribe;
        se emiten los defaults legislados Δ = 0.02 / Ψ = 0.9722 (Fase 5 Paso 3).
Ley 4 [Funcional hermética] Con dos estratos DISCORDANTES y presentes, el despacho consume
        SIEMPRE el fixture: el código de estrategia y el diagnóstico André (`phi_lead2_home`
        del snapshot) certifican la fuente — un fallback a la 3NF o a 0.55 cambia el código.

Residuo declarado (fuera, del alcance de la Ruta 01): `get_sportsbook_matches` (Live Board)
conserva sus semillas 0.564 / 0.258 / 0.178 para la ventanilla informativa; el Jurado las
separa por función y el despacho de capital queda protegido por la Ley 1.

Hermeticidad: cero red y cero contaminación de la bóveda real — SQLite efímero en memoria
inyectado en el singleton `PersistenceGateway` [GOV-TEST-01].
"""

import ast
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.storage.database import Base
from src.storage.models import (
    Competition,
    FixtureSnapshot,
    League,
    Match,
    SovereignDistribution,
)
from src.web.app import app

ROOT = Path(__file__).resolve().parent.parent.parent
RUTA_MARKETS = ROOT / "src" / "web" / "routes" / "markets.py"

ENDPOINT_DESPACHO = "generate_sportsbook_portfolio_endpoint"
URL_DESPACHO = "/api/markets/sportsbook/portfolio/generate"

# Semillas sintéticas extirpadas por la Ruta 01 (documentales: la Ley 1 es genérica).
SEMILLAS_EXTIRPADAS = (0.55, 0.25, 0.20, 0.564, 0.258, 0.178)

ID_FIXTURE_FACTICO = "LIGAMX-J11-01"
ID_FIXTURE_SIN_ESTRATO = "LIGAMX-J11-02"

# ── Estrato fáctico (fixture) vs estrato 3NF: DELIBERADAMENTE DISCORDANTES ──────────────
# Fixture: local fuerte (p_local 0.72) ⇒ triaje QBE-D1 con momio 1.60 (α = +15.2%).
# 3NF: local débil (p_local 0.30 / p_visitante 0.40) ⇒ triaje QBE-R2 (α = +140% en momio 6.00).
# Un despacho que ignorara el fixture entregaría QBE-R2 (o QBE-00 con la semilla 0.55).
P_FACTICO = {"p_local": 0.72, "p_empate": 0.18, "p_visitante": 0.10}
PHI_FACTICO = 0.61
P_3NF_DISCORDANTE = (0.30, 0.30, 0.40)
PHI_3NF_DISCORDANTE = 0.1262
EPISTEMIC_DELTA_3NF = 3.75  # ratio λ_max/λ_min: fuera del rango Δ_epist ∈ [0,1)
MOMIOS_FACTICO = {"L": 1.60, "E": 3.80, "V": 6.00}
MOMIOS_SIN_ESTRATO = {"L": 2.10, "E": 3.50, "V": 3.60}


def _boveda_efimera(monkeypatch):
    """SQLite efímero en memoria inyectado en el singleton del Gateway (cero red).

    `StaticPool` es obligatorio: la bóveda efímera `sqlite://` vive por conexión, de modo que el
    endpoint (que abre su propia sesión desde la fábrica) debe compartir la MISMA conexión que
    sembró las tablas; en otro caso el despacho leería un esquema vacío.
    """
    from src.storage import gateway as gw_mod

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(gw_mod.PersistenceGateway(), "SessionFactory", factory)
    return factory()


def _fixture_factico():
    """Fixture con distribución soberana PROPIA (estrato fáctico del snapshot)."""
    return {
        "id_partido": ID_FIXTURE_FACTICO,
        "local": "Club Puebla",
        "visitante": "Club León",
        "estado": "PROGRAMADO",
        "horario": "17:00",
        "fecha_dt": (datetime.now() + timedelta(hours=48)).isoformat(),
        "p_local": P_FACTICO["p_local"],
        "p_empate": P_FACTICO["p_empate"],
        "p_visitante": P_FACTICO["p_visitante"],
        "phi_lead2_home": PHI_FACTICO,
        "momios": dict(MOMIOS_FACTICO),
    }


def _fixture_sin_estrato():
    """Fixture operable en cuotas pero SIN distribución en ningún estrato."""
    return {
        "id_partido": ID_FIXTURE_SIN_ESTRATO,
        "local": "Tigres UANL",
        "visitante": "Deportivo Toluca",
        "estado": "PROGRAMADO",
        "horario": "19:00",
        "fecha_dt": (datetime.now() + timedelta(hours=50)).isoformat(),
        "momios": dict(MOMIOS_SIN_ESTRATO),
    }


def _sembrar_ventanilla_dual(sesion):
    """Liga + partido 3NF + snapshot con los dos fixtures + la distribución 3NF discordante.

    Nota: `src/storage/gateway.py` activa `PRAGMA foreign_keys = ON` globalmente, de modo que el
    motor efímero aplica integridad referencial estricta; se fuerza el orden padre→hijo con
    `flush()` explícito (competición, partido, liga, snapshot, distribución).
    """
    sesion.add(Competition(id="MEX_LIGAMX", name="Liga MX", country="México"))
    sesion.add(Match(
        id=ID_FIXTURE_FACTICO,
        competition_id="MEX_LIGAMX",
        matchday_num=11,
        home_team_slug="puebla",
        away_team_slug="leon",
    ))
    sesion.add(League(id=262, name="Liga MX", country="México", flag="mx", fotmob_id=262))
    sesion.flush()
    sesion.add(FixtureSnapshot(
        league_id=262, matchday=11, updated_at=datetime.now(),
        matches_json=[_fixture_factico(), _fixture_sin_estrato()],
    ))
    sesion.flush()
    sesion.add(SovereignDistribution(
        match_id=ID_FIXTURE_FACTICO,
        model_version="PIR-SHIELD-RUTA01",
        p_local=P_3NF_DISCORDANTE[0],
        p_empate=P_3NF_DISCORDANTE[1],
        p_visitante=P_3NF_DISCORDANTE[2],
        lambda_home=1.00,
        lambda_away=1.20,
        phi_lead2_home=PHI_3NF_DISCORDANTE,
        phi_lead2_away=PHI_3NF_DISCORDANTE,
        epistemic_delta=EPISTEMIC_DELTA_3NF,
    ))
    sesion.commit()
    return sesion

class AbstractTestMarketDispatchSovereignSource:
    """Contrato abstracto e inmutable del despacho con fuente soberana fáctica."""

    def test_ley_1_cero_semillas_de_probabilidad_en_el_despacho(self):
        """
        [SHIELD-AST / GOVERNANCE-01] Guardián sintáctico: ningún `if/else` del endpoint de
        despacho puede caer a un literal flotante de probabilidad en (0,1). Se prohíben además
        las semillas históricas de la Ruta 01 (0.55 / 0.25 / 0.20 y la familia 0.564/0.258/0.178)
        y se exige que la lectura fáctica del fixture esté presente (p_* y André).
        """
        assert RUTA_MARKETS.exists(), "No existe src/web/routes/markets.py"
        arbol = ast.parse(RUTA_MARKETS.read_text(encoding="utf-8"), filename=str(RUTA_MARKETS))
        funcion = next(
            (n for n in ast.walk(arbol)
             if isinstance(n, ast.FunctionDef) and n.name == ENDPOINT_DESPACHO),
            None,
        )
        assert funcion is not None, "Endpoint ausente: %s" % ENDPOINT_DESPACHO

        # (a) Cero semillas: ningún ternario cae a un flotante de probabilidad.
        sospechosos = []
        for nodo in ast.walk(funcion):
            if not isinstance(nodo, ast.IfExp):
                continue
            orelse = nodo.orelse
            if isinstance(orelse, ast.Constant) and isinstance(orelse.value, float) \
                    and 0.0 < orelse.value < 1.0:
                sospechosos.append("L%d: %s" % (nodo.lineno, ast.unparse(nodo)))
        assert not sospechosos, (
            "[GOVERNANCE-01] Semilla sintética de probabilidad reintroducida en "
            "%s => %s" % (ENDPOINT_DESPACHO, " | ".join(sospechosos))
        )

        # (b) Cero constantes de la familia extirpada en TODO el cuerpo del endpoint.
        presentes = sorted({
            n.value for n in ast.walk(funcion)
            if isinstance(n, ast.Constant) and isinstance(n.value, float)
            and n.value in SEMILLAS_EXTIRPADAS
        })
        assert not presentes, (
            "[GOVERNANCE-01] Constantes sintéticas extirpadas (%s) presentes en %s"
            % (presentes, ENDPOINT_DESPACHO)
        )

        # (c) La lectura fáctica del fixture es obligatoria (probabilidades + diagnóstico André).
        dump = ast.dump(funcion)
        for llave in ("p_local", "p_empate", "p_visitante", "phi_lead2_home"):
            assert llave in dump, (
                "[ARCH-1.4.10] %s no lee «%s» del estrato fáctico" % (ENDPOINT_DESPACHO, llave)
            )

    def test_ley_2_sin_estrato_hay_cuarentena_canonica_no_invencion(self):
        """
        [GOVERNANCE-01 / LN-QBE-065] Guardián sintáctico: el endpoint declara explícitamente la
        cuarentena por ausencia de distribución soberana y la registra con el contrato canónico
        `_descartar_partido` (QBE-00 / $0.00 MXN).
        """
        arbol = ast.parse(RUTA_MARKETS.read_text(encoding="utf-8"), filename=str(RUTA_MARKETS))
        funcion = next(
            n for n in ast.walk(arbol)
            if isinstance(n, ast.FunctionDef) and n.name == ENDPOINT_DESPACHO
        )
        dump = ast.dump(funcion)
        assert "Sin distribución soberana fáctica" in dump, (
            "[GOVERNANCE-01] El despacho no declara la cuarentena por ausencia de estrato"
        )
        assert "_descartar_partido" in dump, (
            "[LN-QBE-065] La cuarentena debe registrarse con el contrato canónico "
            "`_descartar_partido`"
        )

    def test_ley_3_epistemic_delta_no_se_transcribe_como_delta_epist(self):
        """
        [LN-QBE-070-C] El endpoint NO puede leer `epistemic_delta` (3NF) como Δ_epist: esa
        columna almacena el ratio de intensidades λ_max/λ_min, no la discrepancia ponderada
        Δ ∈ [0,1) del Contrato R-1. La fuente legítima son los defaults legislados (0.02 / 0.97)
        y la frontera τ_disp = 0.12 del plano canónico.
        """
        arbol = ast.parse(RUTA_MARKETS.read_text(encoding="utf-8"), filename=str(RUTA_MARKETS))
        funcion = next(
            n for n in ast.walk(arbol)
            if isinstance(n, ast.FunctionDef) and n.name == ENDPOINT_DESPACHO
        )
        referencias = [
            "L%d" % n.lineno for n in ast.walk(funcion)
            if isinstance(n, ast.Attribute) and n.attr == "epistemic_delta"
        ]
        assert not referencias, (
            "[LN-QBE-070-C] %s transcribe `epistemic_delta` (ratio de intensidades) como "
            "Δ_epist en %s" % (ENDPOINT_DESPACHO, referencias)
        )
        floats = {
            n.value for n in ast.walk(funcion)
            if isinstance(n, ast.Constant) and isinstance(n.value, float)
        }
        assert 0.12 in floats, (
            "[LN-QBE-070-C] Falta la frontera de incertidumbre τ_disp = 0.12 en %s"
            % ENDPOINT_DESPACHO
        )


    def test_ley_4_despacho_consume_fixture_y_cuarentena_sin_estrato(self, monkeypatch):
        """
        [Funcional hermética] Con dos estratos discordantes, el despacho consume el FIXTURE:
        la orden del partido con p_local 0.72 (fixture) viaja QBE-D1 con el André fáctico 0.61,
        jamás QBE-R2 (3NF) ni QBE-00 (semilla 0.55). El partido sin estrato alguno queda en
        cuarentena QBE-00 con $0.00 MXN — cero cartera inventada.
        """
        sesion = _sembrar_ventanilla_dual(_boveda_efimera(monkeypatch))
        try:
            respuesta = TestClient(app).post(URL_DESPACHO, json={
                "league_id": 262,
                "selected_match_ids": [],
                "bankroll": 200.0,
                "target_certeza": 0.80,
                "operador": "caliente",
            })
            assert respuesta.status_code == 200, respuesta.text
            data = respuesta.json()
        finally:
            sesion.close()

        ordenes = data.get("ordenes_ejecucion_partidos", [])
        assert len(ordenes) == 1, (
            "Sólo el fixture con estrato fáctico puede recibir capital; se obtuvieron %d órdenes"
            % len(ordenes)
        )
        orden = ordenes[0]
        assert orden["id_partido"] == ID_FIXTURE_FACTICO
        assert orden["estrategia_seleccionada"]["codigo"] == "QBE-D1", (
            "El despacho no consumió la probabilidad del fixture (p_local 0.72 ⇒ QBE-D1); "
            "obtuvo %s" % orden["estrategia_seleccionada"]["codigo"]
        )
        assert orden["metricas_clave"]["phi_lead2_prob_ventaja_2_goles"] == pytest.approx(PHI_FACTICO), (
            "El diagnóstico André no proviene del fixture (%s): obtuvo %s"
            % (PHI_FACTICO, orden["metricas_clave"]["phi_lead2_prob_ventaja_2_goles"])
        )
        assert orden["boletos"]["inversion_partido_A_i"] >= 2.0, "Violación del piso $2.00 MXN"

        descartes = {d["id_partido"]: d for d in data.get("descartes", [])}
        assert ID_FIXTURE_SIN_ESTRATO in descartes, (
            "El partido sin distribución en ningún estrato debió ir a cuarentena"
        )
        cuarentena = descartes[ID_FIXTURE_SIN_ESTRATO]
        assert cuarentena["codigo_estrategia"] == "QBE-00"
        assert cuarentena["inversion_mxn"] == 0.0
        assert "Sin distribución soberana fáctica" in cuarentena["motivo"], cuarentena["motivo"]


class TestMarketDispatchSovereignSource(AbstractTestMarketDispatchSovereignSource):
    """Materialización concreta del Juez Inmutable [DIRECTIVA P.I.R. Fast-Track Ruta 01]."""
    pass
