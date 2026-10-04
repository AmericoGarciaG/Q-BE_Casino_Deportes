# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DE LA PURGA TOTAL DE LA BÓVEDA 3NF
[ARCH-1.4.29] & [VAULT-DATA-001] & [GOVERNANCE-01] & [GOV-TEST-01]
Régimen: [HÍBRIDO DUAL-TRACK]
Axioma: Vaciar la bóveda es un acto ATÓMICO, AUDITABLE y con UNA sola exención fiduciaria.
"""

import ast
import os
from abc import ABC

import pytest
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.orm import sessionmaker

from src.storage.database import Base
from src.storage.models import (
    Competition,
    FixtureSnapshot,
    LLMTokenLedger,
    League,
    Match,
    MatchTelemetry,
    MatchdayState,
    PortfolioRecord,
    Slate,
    SlateItem,
    SovereignDistribution,
    StandingSnapshot,
    Team,
)

PURGA_PATH = os.path.join("src", "web", "routes", "admin_tasks.py")
INDEX_PATH = os.path.join("src", "web", "templates", "index.html")


def _boveda_efimera_con_fk():
    """SQLite en memoria con PRAGMA foreign_keys=ON: cero red, cero contaminación [GOV-TEST-01]."""
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def _activar_fk(dbapi_connection, connection_record):  # pragma: no cover - adaptador
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _ast_de_funcion(nombre: str) -> ast.FunctionDef:
    """AST de una función del router administrativo (auditoría estructural, nunca textual)."""
    with open(PURGA_PATH, "r", encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.FunctionDef) and nodo.name == nombre:
            return nodo
    raise AssertionError(f"🚨 El plano '{nombre}' no existe en {PURGA_PATH}")


class AbstractTestPurgaTotalBoveda3NF(ABC):
    """Juez Abstracto: whitelist, canal in-process, atomicidad, exención fiduciaria y cockpit."""

    # ── 1. WHITELIST AMPLIADA A 10 (VAR-A1) ─────────────────────────────────
    def test_whitelist_ampliada_a_diez_tareas_con_canal_in_process(self):
        """[ARCH-1.4.29] La whitelist de [ARCH-1.4.12] pasa de 9 a 10 tareas, y sólo esa."""
        from src.web.routes.admin_tasks import (
            CANAL_IN_PROCESS,
            TAREAS_PERMITIDAS,
            TAREA_PURGA_TOTAL_DB,
        )

        assert TAREA_PURGA_TOTAL_DB == "purga_total_db"
        assert len(TAREAS_PERMITIDAS) == 10, (
            "Violación [ARCH-1.4.29]: la whitelist debe ser de exactamente 10 tareas certificadas."
        )

        especificacion = TAREAS_PERMITIDAS[TAREA_PURGA_TOTAL_DB]
        assert especificacion["canal"] == CANAL_IN_PROCESS
        assert especificacion["comandos"] == [], (
            "Violación [ARCH-1.4.29]: una purga in-process no publica comandos de subproceso."
        )

    def test_purga_es_ejecutor_in_process_registrado_y_ruteado(self):
        """[ARCH-1.4.29] El mapa de ejecutores in-process y el router apuntan al MISMO plano."""
        from src.web.routes import admin_tasks as modulo

        assert modulo.EJECUTORES_IN_PROCESS[modulo.TAREA_PURGA_TOTAL_DB] is (
            modulo.ejecutar_purga_total_boveda_3nf
        )

        router = _ast_de_funcion("ejecutar_tarea_administrativa")
        subscripts = [
            nodo
            for nodo in ast.walk(router)
            if isinstance(nodo, ast.Subscript)
            and isinstance(nodo.value, ast.Name)
            and nodo.value.id == "EJECUTORES_IN_PROCESS"
        ]
        assert subscripts, (
            "Violación [ARCH-1.4.29]: el router administrativo no consulta "
            "`EJECUTORES_IN_PROCESS` (la purga quedaría inalcanzable desde el cockpit)."
        )

    def test_purga_jamas_se_degrada_a_subproceso_fail_loud(self):
        """[GOVERNANCE-01] Despacharla por el canal de subprocesos es FAIL-LOUD, no un no-op."""
        from src.web.routes.admin_tasks import ejecutar_tarea_autorizada

        with pytest.raises(ValueError):
            ejecutar_tarea_autorizada("purga_total_db")

    # ── 2. ATOMICIDAD Y ORDEN TOPOLÓGICO (VAR-A2) ───────────────────────────
    def test_orden_de_purga_emana_del_esquema_y_respeta_las_fk(self):
        """[VAULT-DATA-001] El orden es el inverso topológico del ORM: hijos antes que padres."""
        from src.web.routes.admin_tasks import TABLAS_EXENTAS_PURGA

        orden = [
            tabla.name
            for tabla in reversed(Base.metadata.sorted_tables)
            if tabla.name not in TABLAS_EXENTAS_PURGA
        ]
        assert len(orden) == len(Base.metadata.sorted_tables) - len(TABLAS_EXENTAS_PURGA)

        for tabla in Base.metadata.sorted_tables:
            if tabla.name in TABLAS_EXENTAS_PURGA:
                continue
            for fk in tabla.foreign_keys:
                padre = fk.column.table.name
                if padre in TABLAS_EXENTAS_PURGA:
                    continue
                assert orden.index(tabla.name) < orden.index(padre), (
                    f"Violación [VAULT-DATA-001]: '{tabla.name}' se borra DESPUÉS de su padre "
                    f"'{padre}'; las claves foráneas se violarían."
                )

    def test_ejecutor_no_commitea_y_el_orden_no_se_transcribe_a_mano(self):
        """[ARCH-1.4.29] Auditoría AST: orden del esquema, exención por constante, cero commit."""
        nodo = _ast_de_funcion("purgar_boveda_3nf")

        atributos = {sub.attr for sub in ast.walk(nodo) if isinstance(sub, ast.Attribute)}
        assert "sorted_tables" in atributos, (
            "Violación [ARCH-1.4.29]: el orden de purga debe emanar de `Base.metadata.sorted_tables`, "
            "jamás de una lista de tablas transcrita a mano."
        )

        llamadas = [
            getattr(call.func, "attr", "") for call in ast.walk(nodo) if isinstance(call, ast.Call)
        ]
        assert "commit" not in llamadas and "rollback" not in llamadas, (
            "Violación [VAULT-DATA-001]: la Unit of Work es propiedad del Gateway; el ejecutor de "
            "purga NO puede commitear ni hacer rollback por su cuenta."
        )

        constantes = {name.id for name in ast.walk(nodo) if isinstance(name, ast.Name)}
        assert "TABLAS_EXENTAS_PURGA" in constantes, (
            "Violación [ARCH-1.4.29]: la exención debe referenciar la constante gobernada."
        )

        literales = {
            constante.value
            for constante in ast.walk(nodo)
            if isinstance(constante, ast.Constant) and isinstance(constante.value, str)
        }
        assert "llm_token_ledger" not in literales, (
            "Violación [GOVERNANCE-01]: el nombre de la tabla exenta quedó incrustado como literal "
            "en el ejecutor; debe emanar de `TABLAS_EXENTAS_PURGA`."
        )

        ejecutor = _ast_de_funcion("ejecutar_purga_total_boveda_3nf")
        llamadas_ejecutor = [
            getattr(call.func, "attr", "")
            for call in ast.walk(ejecutor)
            if isinstance(call, ast.Call)
        ]
        assert "write_transaction" in llamadas_ejecutor, (
            "Violación [VAULT-DATA-001]: la purga debe correr dentro de "
            "`PersistenceGateway.write_transaction()` (Unit of Work única)."
        )

    # ── 3. EXENCIÓN FIDUCIARIA Y VACIADO EMPÍRICO (VAR-A2) ──────────────────
    def test_purga_total_vacia_la_boveda_y_preserva_el_libro_mayor(self):
        """[ARCH-1.4.29] Vaciado empírico con FK activas: 14 tablas a cero y el ledger intacto."""
        from src.web.routes.admin_tasks import TABLAS_EXENTAS_PURGA, purgar_boveda_3nf

        sesion = _boveda_efimera_con_fk()
        try:
            assert sesion.execute(text("PRAGMA foreign_keys")).scalar() == 1, (
                "El banco de pruebas exige PRAGMA foreign_keys=ON para probar el orden de borrado."
            )

            # Fase 1: padres. Cero ambigüedad de orden en el fixture.
            sesion.add(Competition(id="MEX_LIGAMX", name="Liga MX", country="México"))
            sesion.add(League(id=262, name="Liga MX", country="México", flag="MX", fotmob_id=262))
            sesion.add(Slate(id="PROGOL-9999", name="Concurso sintético del Juez"))
            sesion.commit()

            # Fase 2: hijos y hojas (una fila por cada tabla no exenta del universo ORM).
            sesion.add(Team(
                league_id=262, fotmob_team_id=999001, name="Club Prueba",
                short_name="PRU", canonical_slug="club-prueba", crest_url="local://prueba",
            ))
            sesion.add(FixtureSnapshot(league_id=262, matchday=11, matches_json=[{"local": "A"}]))
            sesion.add(StandingSnapshot(league_id=262, season="2026", matchday=11, positions_json=[]))
            sesion.add(PortfolioRecord(league_id=262, matchday=11, bankroll=1000.0, portfolio_json=[]))
            sesion.add(MatchdayState(league_id=262, matchday_num=11))
            sesion.add(Match(
                id="MATCH_TEST_01", competition_id="MEX_LIGAMX", matchday_num=11,
                home_team_slug="club-prueba", away_team_slug="club-rival",
            ))
            sesion.add(MatchTelemetry(match_id="MATCH_TEST_01", team_slug="club-prueba"))
            sesion.add(SovereignDistribution(
                match_id="MATCH_TEST_01", p_local=0.4, p_empate=0.3, p_visitante=0.3,
                lambda_home=1.2, lambda_away=1.0,
            ))
            sesion.add(SlateItem(slate_id="PROGOL-9999", tipo_concurso="REGULAR", position=1))
            sesion.add(LLMTokenLedger(key_alias="GEMINI_PRUEBA", task_type="AUDITORIA"))
            sesion.commit()

            conteos = purgar_boveda_3nf(sesion)
            sesion.commit()  # En producción este commit pertenece a la Unit of Work del Gateway.

            universo = {tabla.name for tabla in Base.metadata.sorted_tables}
            assert set(conteos) == universo - set(TABLAS_EXENTAS_PURGA), (
                "Violación [ARCH-1.4.29]: el manifiesto de purga no cubre exactamente el universo "
                "de tablas menos las exentas."
            )
            assert conteos["leagues"] == 1
            assert conteos["matches"] == 1
            assert conteos["slate_items"] == 1
            assert conteos["sovereign_distributions"] == 1

            for tabla in Base.metadata.sorted_tables:
                total = sesion.execute(select(func.count()).select_from(tabla)).scalar()
                if tabla.name in TABLAS_EXENTAS_PURGA:
                    assert total == 1, (
                        f"Violación [ARCH-1.4.29]: la tabla exenta '{tabla.name}' fue purgada."
                    )
                else:
                    assert total == 0, (
                        f"Violación [ARCH-1.4.29]: la tabla '{tabla.name}' conserva {total} filas."
                    )
        finally:
            sesion.close()

    # ── 4. COCKPIT: BOTÓN DIDÁCTICO Y CONCURSO VIGENTE ──────────────────────
    def test_boton_de_purga_total_en_cockpit_con_tooltip_fiduciario(self):
        """[DES-QBE-050] Botón gobernado en Activos y Mantenimiento 3NF, con tooltip didáctico."""
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            html = f.read()

        seccion_cc = html.split('id="view-control-center"')[1].split("</section>")[0]
        assert "ejecutarTareaAdmin('purga_total_db')" in seccion_cc, (
            "Violación [ARCH-1.4.29]: falta el botón de purga total en el Centro de Control."
        )

        lineas_boton = [linea for linea in seccion_cc.splitlines() if "purga_total_db" in linea]
        assert lineas_boton and "title=" in lineas_boton[0], (
            "Violación [DES-QBE-050]: el botón de purga total no publica tooltip fiduciario."
        )

    def test_etiqueta_vigente_del_concurso_progol(self):
        """[ARCH-1.6.19-B] La etiqueta del concurso vivo es 2353, no la obsoleta 2352."""
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            html = f.read()

        seccion_cc = html.split('id="view-control-center"')[1].split("</section>")[0]
        assert "Concurso #2353" in seccion_cc
        assert "Concurso #2352" not in seccion_cc


class TestPurgaTotalBoveda3NF(AbstractTestPurgaTotalBoveda3NF):
    """Implementación concreta en The Shield."""

    pass
