# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DE CAPA 5 (DATA NEXUS BUS)
Validación de:
- [LN-QBE-096] Coordinador Orquestador Atómico del Ciclo de Vida de Datos (Data Nexus Bus).
- [ARCH-1.4.27] Módulo de Servicios de Composición y Orquestación (`src/services/`).

Gobierno: [GOV-TEST-01] hermeticidad absoluta — SQLite `:memory:`, cero red, cero disco y cero
dobles de lógica de negocio (el único doble es el PUERTO de persistencia, invertido por el
llamador conforme a [ARCH-1.4.24]). El motor matemático y las capas 1–4 NO se sustituyen jamás:
se invocan de verdad.
"""

import ast
import inspect
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
MODULO_COORDINADOR = RAIZ / "src" / "services" / "ingestion_coordinator.py"

CIERRE_UTC = datetime(2026, 10, 15, 17, 0, tzinfo=timezone.utc)


def _ingestion_coordinator():
    """Importa el módulo bajo régimen con mensaje de fallo legislado (paso 2 → RED controlado)."""
    try:
        from src.services.ingestion_coordinator import IngestionCoordinator
    except ImportError as ex:
        pytest.fail(
            "❌ [LN-QBE-096] Falta el Coordinador Orquestador Atómico en "
            f"src/services/ingestion_coordinator.py: {ex}"
        )
    return IngestionCoordinator


def _dto_progol(items, contest_id="PROGOL-TEST-001", bolsa_estimada=10_000_000.0):
    from src.ingestion.schemas import ProgolContestDTO

    return ProgolContestDTO(
        contest_id=contest_id,
        bolsa_estimada=bolsa_estimada,
        cierre_utc=CIERRE_UTC,
        items=items,
    )


def _candidato(match_id="FOTMOB-4412345"):
    from src.ingestion.schemas import ScheduledMatchDTO

    return ScheduledMatchDTO(
        match_id=match_id,
        home_team="Club América",
        away_team="Chivas Guadalajara",
        kickoff_utc=datetime(2026, 10, 15, 19, 0, tzinfo=timezone.utc),  # +2 h (DENTRO de W)
        tournament_id=262,
    )


@pytest.fixture
def gateway_memoria():
    """Doble hermético del PUERTO de persistencia: SQLite `:memory:` con integridad referencial ON."""
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker

    from src.storage.models import Base

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _activar_integridad_referencial(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    fabrica = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)

    class GatewayMemoria:
        def __init__(self):
            self.SessionFactory = fabrica

        @contextmanager
        def read_session(self):
            sesion = fabrica()
            try:
                yield sesion
            finally:
                sesion.close()

        @contextmanager
        def write_transaction(self):
            sesion = fabrica()
            try:
                yield sesion
                sesion.commit()
            except Exception as ex:
                sesion.rollback()
                raise ex
            finally:
                sesion.close()

    return GatewayMemoria()


# ---------------------------------------------------------------------------
# 1. PRUEBA DEL PIPELINE ATÓMICO PROGOL_FULL ([LN-QBE-096])
# ---------------------------------------------------------------------------
def test_ln_qbe_096_progol_full_pipeline_atomic(gateway_memoria):
    """Audita el ciclo completo Sensor→Capa 2→Capa 4→3NF dentro de UNA sola Unit of Work."""
    from src.storage.models import Slate, SlateItem

    IngestionCoordinator = _ingestion_coordinator()
    coordinador = IngestionCoordinator(gateway=gateway_memoria)

    dto = _dto_progol([
        {"position": 1, "local_raw": "Club América", "visitante_raw": "Chivas Guadalajara"},
        {"position": 2, "local_raw": "Puebla", "visitante_raw": "Toluca"},
    ])

    reporte = coordinador.sincronizar_progol_pipeline_completo(
        concurso_dto_inyectado=dto,
        candidatos_partidos=[_candidato()],
    )

    assert reporte.operacion == "PROGOL_FULL"
    assert reporte.status == "SUCCESS"
    assert reporte.procesados == 2
    assert reporte.exitosos == 2
    assert reporte.errores == []
    assert reporte.duracion_s >= 0.0

    with gateway_memoria.read_session() as sesion:
        cabecera = sesion.get(Slate, "PROGOL-TEST-001")
        assert cabecera is not None
        assert cabecera.name == "Progol Concurso #PROGOL-TEST-001"
        assert cabecera.bolsa_estimada == pytest.approx(10_000_000.0)
        assert cabecera.fecha_cierre is not None
        assert cabecera.status == "OPEN"
        # Cero invención de identidad: el DTO sellado no publica liga ⇒ competition_id = NULL.
        assert cabecera.competition_id is None

        casillas = (
            sesion.query(SlateItem)
            .filter(SlateItem.slate_id == "PROGOL-TEST-001")
            .order_by(SlateItem.position)
            .all()
        )
        assert [casilla.position for casilla in casillas] == [1, 2]

        for casilla in casillas:
            assert casilla.local_raw and casilla.visitante_raw
            assert casilla.local_canonico and casilla.visitante_canonico
            # S(I) = 0 ⇒ sin vínculo soberano reclamado y Prior Fiduciario [LN-QBE-075]
            assert casilla.es_prior_ignorancia is True
            assert casilla.match_id is None
            # Símplex cerrado: transcripción VERBATIM del motor sellado, cero recálculo propio
            assert (
                casilla.p_local + casilla.p_empate + casilla.p_visitante
                == pytest.approx(1.0, abs=1e-9)
            )

        casilla_2 = casillas[1]
        assert casilla_2.p_local == pytest.approx(0.3333, abs=1e-4)
        assert casilla_2.p_empate == pytest.approx(0.3333, abs=1e-4)
        assert casilla_2.p_visitante == pytest.approx(0.3334, abs=1e-4)

    # Idempotencia del upsert: re-sincronizar actualiza in situ, jamás duplica ni destruye.
    repetido = coordinador.sincronizar_progol_pipeline_completo(
        concurso_dto_inyectado=dto,
        candidatos_partidos=[_candidato()],
    )
    assert repetido.status == "SUCCESS"
    with gateway_memoria.read_session() as sesion:
        assert sesion.query(Slate).count() == 1
        assert sesion.query(SlateItem).count() == 2


# ---------------------------------------------------------------------------
# 2. PRUEBA DE FAIL-LOUD Y ROLLBACK TOTAL ([LN-QBE-096].P.2 / P.6)
# ---------------------------------------------------------------------------
def test_ln_qbe_096_fail_loud_and_total_rollback(gateway_memoria):
    """Audita que el sistema escriba 0 filas o el conjunto completo: nunca un snapshot parcial."""
    from src.storage.models import Slate, SlateItem

    IngestionCoordinator = _ingestion_coordinator()
    coordinador = IngestionCoordinator(gateway=gateway_memoria)

    # (a) Aduana fail-fast: casilla sin literal ⇒ aborto ANTES de abrir la Unit of Work.
    dto_corrupto = _dto_progol([
        {"position": 1, "local_raw": "Club América", "visitante_raw": "Chivas Guadalajara"},
        {"position": 2, "local_raw": "Puebla", "visitante_raw": "   "},
    ])
    reporte = coordinador.sincronizar_progol_pipeline_completo(
        concurso_dto_inyectado=dto_corrupto,
        candidatos_partidos=[_candidato()],
    )
    assert reporte.status == "FAILED"
    assert reporte.procesados == 0
    assert reporte.exitosos == 0
    assert len(reporte.errores) == 1

    # (b) Sin evidencia fáctica ⇒ FAIL-LOUD [GOVERNANCE-01]: prohibido sintetizar el concurso.
    reporte = coordinador.sincronizar_progol_pipeline_completo(concurso_num=2353)
    assert reporte.status == "FAILED"
    assert reporte.exitosos == 0
    assert reporte.errores

    # (c) Rollback TOTAL: el partido resuelto NO está registrado ⇒ violación de FK en el commit
    #     ⇒ la cabecera TAMBIÉN desaparece (invariante todo-o-nada del snapshot certificado).
    dto_valido = _dto_progol([
        {"position": 1, "local_raw": "Club América", "visitante_raw": "Chivas Guadalajara"},
    ])
    reporte = coordinador.sincronizar_progol_pipeline_completo(
        concurso_dto_inyectado=dto_valido,
        candidatos_partidos=[_candidato(match_id="FOTMOB-NO-REGISTRADO")],
        datos_facticos_por_match={
            "FOTMOB-NO-REGISTRADO": {
                "home_team_stats": {"pj": 8, "gf": 13, "gc": 8},
                "away_team_stats": {"pj": 8, "gf": 10, "gc": 8},
            }
        },
    )
    assert reporte.status == "FAILED"
    assert reporte.procesados == 1
    assert reporte.exitosos == 0
    assert any("FOREIGN KEY" in error.upper() for error in reporte.errores), reporte.errores

    with gateway_memoria.read_session() as sesion:
        assert sesion.query(Slate).count() == 0
        assert sesion.query(SlateItem).count() == 0


# ---------------------------------------------------------------------------
# 3. PRUEBA DEL CONTRATO DE INTERFAZ Y PUREZA ([ARCH-1.4.27])
# ---------------------------------------------------------------------------
def test_arch_1_4_27_coordinator_interface_and_purity():
    """Audita la signatura legislada, la resolución perezosa del Gateway y la frontera de régimen."""
    IngestionCoordinator = _ingestion_coordinator()
    from src.services.ingestion_coordinator import CoordinatorExecutionReport

    # 1. Contrato IPO legislado de la puerta de orquestación.
    firma = inspect.signature(IngestionCoordinator.sincronizar_progol_pipeline_completo)
    for puerto in (
        "concurso_num",
        "session",
        "concurso_dto_inyectado",
        "candidatos_partidos",
        "datos_facticos_por_match",
    ):
        assert puerto in firma.parameters, f"Puerto legislado ausente: {puerto}"

    assert list(CoordinatorExecutionReport.model_fields) == [
        "operacion", "status", "procesados", "exitosos", "errores", "duracion_s",
    ]

    # 2. Resolución PEREZOSA: instanciar sin argumentos NO toca disco ni resuelve el singleton.
    coordinador = IngestionCoordinator()
    assert coordinador._gateway is None

    # 3. Frontera de régimen (auditoría AST): cero sensores de red en la Capa 5.
    assert MODULO_COORDINADOR.exists(), f"Falta el módulo de Capa 5: {MODULO_COORDINADOR}"
    arbol = ast.parse(MODULO_COORDINADOR.read_text(encoding="utf-8"))
    prohibidos = ("playwright", "requests", "httpx", "scraper")
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos = [alias.name for alias in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            modulos = [nodo.module or ""]
        else:
            continue
        for modulo in modulos:
            assert not any(p in modulo.lower() for p in prohibidos), (
                f"[ARCH-1.4.27] Impureza detectada en la Capa 5: import de '{modulo}'"
            )

    # 4. Prohibición de duplicar el Prior Fiduciario [LN-QBE-075]: cero constantes propias.
    literales = {
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, float)
    }
    assert not ({0.3333, 0.3334} & literales), (
        f"[LN-QBE-096] El Coordinador duplica el Prior Fiduciario [LN-QBE-075]: {literales}"
    )
