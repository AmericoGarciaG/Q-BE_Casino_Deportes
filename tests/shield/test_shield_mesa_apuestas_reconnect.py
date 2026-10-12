# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [FASE 6 SPRINT 6.9] Verificación de Reconexión de Mesa de Apuestas
Doctrina: Kybern Framework v12.0 [ARCH-1.4.6 / LN-QBE-065]
Régimen: [HÍBRIDO DUAL-TRACK]

[VAR-2026-MESA-RECONNECT-PREMISE] — ALT-1 RATIFICADA POR EL DIRECTOR (Dictamen de Varianza).
La premisa de DATOS de `test_despacho_automatico_jornada_completa_sin_seleccion_manual` quedó
obsoleta: fue concebida cuando la ventanilla activa portaba candidatos +EV abiertos pre-kickoff.
En la cartelera viva vigente (J11) los partidos ya concluidos y las compuertas de sanidad dejan
CERO activos +EV, de modo que `ordenes >= 1` era inalcanzable CON DATOS ELEGIBLES. Se restituye
la premisa SIN tocar una sola aserción: se siembra una ventanilla hermética (SQLite efímero en
memoria inyectado en el singleton `PersistenceGateway`, [GOV-TEST-01]) con un candidato +EV
elegible, con el MISMO patrón soberano ratificado en `test_shield_market_dispatch_sovereign_source`.
Cero fabricación de órdenes en el motor, cero relajación del triaje y cero mutación de la bóveda.
"""

from datetime import datetime, timedelta

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

client = TestClient(app)

# ── Semilla soberana del candidato elegible (idéntica a la ratificada en el juez hermano) ─────
# p_local 0.72 con momio de ataque 1.60 ⇒ triaje QBE-D1 con α = +15.2%: activo ELEGIBLE con +EV.
ID_PARTIDO_ELEGIBLE = "LIGAMX-J11-01"
ID_PARTIDO_NO_RENTABLE = "LIGAMX-J11-02"
P_ELEGIBLE = {"p_local": 0.72, "p_empate": 0.18, "p_visitante": 0.10}
PHI_ELEGIBLE = 0.61
MOMIOS_ELEGIBLE = {"L": 1.60, "E": 3.80, "V": 6.00}
MOMIOS_NO_RENTABLE = {"L": 2.10, "E": 3.50, "V": 3.60}


def _boveda_efimera(monkeypatch):
    """SQLite efímero en memoria inyectado en el singleton del Gateway (cero red).

    `StaticPool` es obligatorio: la bóveda `sqlite://` vive por conexión, de modo que el endpoint
    (que abre su propia sesión desde la fábrica del Gateway) debe compartir la MISMA conexión que
    sembró las tablas; en otro caso el despacho leería un esquema vacío. `monkeypatch` deshace la
    inyección al cierre del test: la bóveda viva jamás se toca ([ARCH-1.5.0-B] / [GOV-TEST-01]).
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


def _fixture_elegible():
    """Candidato +EV con estrato fáctico propio (p_local 0.72 / momio 1.60 ⇒ QBE-D1)."""
    return {
        "id_partido": ID_PARTIDO_ELEGIBLE,
        "local": "Club Puebla",
        "visitante": "Club León",
        "estado": "PROGRAMADO",
        "horario": "17:00",
        "fecha_dt": (datetime.now() + timedelta(hours=48)).isoformat(),
        "p_local": P_ELEGIBLE["p_local"],
        "p_empate": P_ELEGIBLE["p_empate"],
        "p_visitante": P_ELEGIBLE["p_visitante"],
        "phi_lead2_home": PHI_ELEGIBLE,
        "momios": dict(MOMIOS_ELEGIBLE),
    }


def _fixture_no_rentable():
    """Contraparte sin distribución en ningún estrato: debe quedar en cuarentena QBE-00."""
    return {
        "id_partido": ID_PARTIDO_NO_RENTABLE,
        "local": "Tigres UANL",
        "visitante": "Deportivo Toluca",
        "estado": "PROGRAMADO",
        "horario": "19:00",
        "fecha_dt": (datetime.now() + timedelta(hours=50)).isoformat(),
        "momios": dict(MOMIOS_NO_RENTABLE),
    }


def _sembrar_ventanilla_con_elegible(sesion):
    """Liga + partido 3NF + snapshot J11 (elegible + no rentable) + distribución 3NF discordante.

    `src/storage/gateway.py` activa `PRAGMA foreign_keys = ON`, por lo que el motor efímero aplica
    integridad referencial estricta: se fuerza el orden padre→hijo con `flush()` explícito.
    """
    sesion.add(Competition(id="MEX_LIGAMX", name="Liga MX", country="México"))
    sesion.add(Match(
        id=ID_PARTIDO_ELEGIBLE,
        competition_id="MEX_LIGAMX",
        matchday_num=11,
        home_team_slug="puebla",
        away_team_slug="leon",
    ))
    sesion.add(League(id=262, name="Liga MX", country="México", flag="mx", fotmob_id=262))
    sesion.flush()
    sesion.add(FixtureSnapshot(
        league_id=262, matchday=11, updated_at=datetime.now(),
        matches_json=[_fixture_elegible(), _fixture_no_rentable()],
    ))
    sesion.flush()
    sesion.add(SovereignDistribution(
        match_id=ID_PARTIDO_ELEGIBLE,
        model_version="VAR-MESA-RECONNECT",
        p_local=0.30, p_empate=0.30, p_visitante=0.40,
        lambda_home=1.00, lambda_away=1.20,
        phi_lead2_home=0.1262, phi_lead2_away=0.1262,
        epistemic_delta=3.75,
    ))
    sesion.commit()
    return sesion


def test_despacho_automatico_jornada_completa_sin_seleccion_manual(monkeypatch):
    """
    [ARCH-1.4.6] Valida que al no enviar selected_match_ids, el endpoint tome
    automáticamente los partidos de la ventanilla ACTIVA y procese la cartera.

    [VAR-2026-MESA-RECONNECT-PREMISE / ALT-1] La ventanilla viva vigente (J11) no porta activos
    +EV (partidos concluidos + compuertas de sanidad): se siembra herméticamente el candidato
    elegible para restituir la premisa del juez conservando sus aserciones INTACTAS.
    """
    payload = {
        "league_id": 262,
        "selected_match_ids": [],  # Lista vacía: despacho automático
        "bankroll": 200.0,
        "target_certeza": 0.80,
        "operador": "caliente"
    }
    # [VAR-2026-MESA-RECONNECT-PREMISE / ALT-1] Ventanilla hermética con candidato +EV elegible:
    # el despacho corre contra el padrón sembrado, no contra la cartelera viva sin activos +EV.
    sesion = _sembrar_ventanilla_con_elegible(_boveda_efimera(monkeypatch))
    try:
        response = client.post("/api/markets/sportsbook/portfolio/generate", json=payload)
        assert response.status_code == 200, f"Error en endpoint: {response.text}"
        data = response.json()
    finally:
        sesion.close()
    assert "balance_global_portafolio" in data
    assert "control_portafolio" in data
    assert "ordenes_ejecucion_partidos" in data

    # Validar que se generaron órdenes reales
    ordenes = data["ordenes_ejecucion_partidos"]
    assert len(ordenes) >= 1, "Debió generarse al menos una orden aprobada con +EV"

    # Validar que las órdenes lleven la herencia de Pago Anticipado
    for o in ordenes:
        assert o["boletos"]["inversion_partido_A_i"] >= 2.0, "Violación de piso mínimo $2.00 MXN"


def test_descarte_temprano_activos_no_rentables():
    """
    [LN-QBE-065] Valida que los partidos sin ventaja (+EV <= 0)
    sean vetados como QBE-00 y reciban $0.00 MXN de inversión.
    """
    payload = {
        "league_id": 262,
        "bankroll": 200.0,
        "target_certeza": 0.80,
        "operador": "caliente"
    }
    response = client.post("/api/markets/sportsbook/portfolio/generate", json=payload)
    assert response.status_code == 200

    data = response.json()
    descartes = data.get("descartes", [])
    
    # Debe existir al menos un partido vetado (ej. volados simétricos como Cruz Azul vs Toluca)
    assert len(descartes) >= 1, "El filtro de descarte temprano debió vetar partidos no rentables"
    for d in descartes:
        assert d.get("codigo_estrategia") == "QBE-00" or "VETO" in d.get("motivo", "").upper()


def test_fuga_probabilidades_leagues_corregida():
    """
    Valida que el endpoint principal de ligas entregue p_local numérico (NO null).
    """
    response = client.get("/api/leagues/262/live-board?jornada=10")
    assert response.status_code == 200
    data = response.json()
    p1 = data["fixtures"][0]
    assert p1.get("p_local") is not None, "Fuga persistente: p_local sigue saliendo null en leagues.py"
    assert 0.0 <= p1.get("p_local") <= 1.0
