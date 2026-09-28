# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: CENTRO DE CONTROL, WHITELIST DE TAREAS Y JORNADA DINÁMICA
[ARCH-1.6.15, ARCH-1.4.12] & [DES-QBE-048, DES-QBE-049]
Régimen: [DIRGEN-STRICT]
Axioma: Whitelist estricta anti-inyección y erradicación de límites rígidos de celda.
"""

import ast
import os
import re
import pytest
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.storage.database import Base
from src.storage.models import FixtureSnapshot, League, MatchdayState, StandingSnapshot
from src.storage.sync_service import resolver_jornada_actual_dinamica, sync_league_live_board


def _boveda_efimera():
    """Sesión SQLite efímera en memoria: cero red y cero contaminación de la bóveda real [GOV-TEST-01]."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _fixture(id_partido: str, estado: str, momio_local=None, horas_desde_ahora: int = 48):
    """Fixture canónico mínimo para la bóveda efímera (fechas relativas al reloj soberano)."""
    momios = {"L": momio_local, "E": 3.2, "V": 3.6} if momio_local is not None else {}
    return {
        "id_partido": id_partido,
        "local": "Club América",
        "visitante": "Club Tijuana",
        "estado": estado,
        "fecha_dt": (datetime.now() + timedelta(hours=horas_desde_ahora)).isoformat(),
        "fecha_bloque": "Bloque de prueba",
        "horario": "19:00",
        "marcador_actual": "1 - 0" if estado == "FINALIZADO" else None,
        "minuto_juego": None,
        "disponible_para_seleccion": False,
        "momios": momios,
    }


class AbstractTestAdminTasksAndDynamicMatchday(ABC):
    """Juez Abstracto que audita la resolución dinámica de jornada y el centro de control."""

    def test_resolucion_dinamica_jornada_activa(self):
        """Verifica que el resolver dinámico avance a la jornada con partidos programados."""
        from scripts.daemons.centinela_mercado import resolver_jornada_activa_dinamica

        # Simular fixture donde J10 está 100% FINALIZADA y J11 está PROGRAMADA
        mock_fixtures_db = {
            10: [{"estado": "FINALIZADO"} for _ in range(9)],
            11: [{"estado": "PROGRAMADO"} for _ in range(9)],
            12: [{"estado": "PROGRAMADO"} for _ in range(9)]
        }
        jornada_resuelta = resolver_jornada_activa_dinamica(mock_fixtures_db)
        assert jornada_resuelta == 11, f"Fallo: Esperaba J11 por estar J10 finalizada, obtuvo J{jornada_resuelta}"

    # ══════════════════════════════════════════════════════════════════════════════════
    # [ARCH-1.6.15 / ARCH-1.4.10] JORNADA ACTUAL DINÁMICA EN EL LECTOR DEL BUS (sync_service)
    # Cero celdas de jornada rígidas: la jornada administrativa emana de la bóveda 3NF.
    # ══════════════════════════════════════════════════════════════════════════════════

    def test_sync_service_cero_celdas_de_jornada_quemadas(self):
        """
        [ARCH-1.6.15 / GOVERNANCE-01] Guardián AST: el lector del bus tiene prohibido asignar
        un literal entero a `jornada_actual` o a `MatchdayState.matchday_num`. La jornada debe
        resolverse algebraicamente del estado fáctico (nunca transcribir una fecha).
        """
        ruta = Path("src", "storage", "sync_service.py")
        assert ruta.exists(), "No existe src/storage/sync_service.py"

        tree = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        violaciones = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            valor = node.value
            if not (
                isinstance(valor, ast.Constant)
                and isinstance(valor.value, int)
                and not isinstance(valor.value, bool)
            ):
                continue
            for objetivo in node.targets:
                if isinstance(objetivo, ast.Name) and objetivo.id == "jornada_actual":
                    violaciones.append(node.lineno)
                if isinstance(objetivo, ast.Attribute) and objetivo.attr == "matchday_num":
                    violaciones.append(node.lineno)

        assert not violaciones, (
            "Violación [ARCH-1.6.15 / GOVERNANCE-01]: celda de jornada rígida detectada en "
            f"src/storage/sync_service.py líneas {violaciones}."
        )

    def test_jornada_actual_sigue_a_la_ventanilla_con_mercado_abierto(self):
        """
        [ARCH-1.6.15] Con mercado publicado en J9 (jornada no concluida con cuotas) y jornadas
        posteriores sin cuotas, la jornada activa es J9 y el ledger `MatchdayState` la refleja.
        """
        sesion = _boveda_efimera()
        try:
            ahora = datetime.now()
            sesion.add(League(id=1, name="Liga MX", country="México", flag="mx", fotmob_id=262))
            sesion.flush()

            # J11 futura SIN cuotas (no puede hijackear la ventanilla)
            sesion.add(FixtureSnapshot(
                league_id=1, matchday=11, updated_at=ahora,
                matches_json=[_fixture("LIGAMX-J11-01", "PROGRAMADO")],
            ))
            # J10 concluida con el snapshot más fresco
            sesion.add(FixtureSnapshot(
                league_id=1, matchday=10, updated_at=ahora,
                matches_json=[_fixture("LIGAMX-J10-01", "FINALIZADO", horas_desde_ahora=-24)],
            ))
            # J9 con mercado abierto (cuotas 1X2 publicadas) capturada antes
            sesion.add(FixtureSnapshot(
                league_id=1, matchday=9, updated_at=ahora - timedelta(days=3),
                matches_json=[_fixture("LIGAMX-J9-01", "PROGRAMADO", momio_local=2.5)],
            ))
            # Efecto Dual: tabla por jornada (J9) y respaldo (J10)
            for jornada in (9, 10):
                sesion.add(StandingSnapshot(
                    league_id=1, season="2026", matchday=jornada, captured_at=ahora,
                    positions_json=[{"equipo": "Club América", "proximo_rival": "Club Tijuana"}],
                ))
            sesion.add(MatchdayState(league_id=1, matchday_num=10, status="ACTIVA"))
            sesion.commit()

            board = sync_league_live_board(262, sesion)

            assert board["jornada_actual"] == 9, (
                f"Violación [ARCH-1.6.15]: la jornada activa debe ser la ventanilla con mercado "
                f"abierto (J9), se obtuvo J{board['jornada_actual']}."
            )
            assert board["jornada_mostrada"] == 9, "La jornada desplegada debe ser la jornada activa."
            assert board["jornadas_disponibles"] == [9, 10, 11], "El carrusel no debe truncar jornadas."

            sesion.expire_all()
            ledger = sesion.query(MatchdayState).filter(MatchdayState.league_id == 1).first()
            assert ledger.matchday_num == 9, (
                f"Violación [LN-QBE-026]: el ledger PM-FACE debe registrar la jornada activa "
                f"dinámica (9), registró {ledger.matchday_num}."
            )
        finally:
            sesion.close()

    def test_jornada_actual_sin_mercado_conmuta_a_la_ultima_registrada(self):
        """
        [ARCH-1.6.15] §4 — Si ninguna jornada porta cuotas publicadas (mercado retirado), la
        jornada activa es la última registrada en la bóveda, sin constantes quemadas.
        """
        sesion = _boveda_efimera()
        try:
            ahora = datetime.now()
            sesion.add(League(id=1, name="Liga MX", country="México", flag="mx", fotmob_id=262))
            sesion.flush()

            for jornada, desfase in ((11, 0), (10, 2)):
                sesion.add(FixtureSnapshot(
                    league_id=1, matchday=jornada, updated_at=ahora - timedelta(hours=desfase),
                    matches_json=[_fixture(f"LIGAMX-J{jornada}-01", "PROGRAMADO")],
                ))
            sesion.add(StandingSnapshot(
                league_id=1, season="2026", matchday=11, captured_at=ahora,
                positions_json=[{"equipo": "Club América", "proximo_rival": "Club Tijuana"}],
            ))
            sesion.commit()

            board = sync_league_live_board(262, sesion)
            assert board["jornada_actual"] == 11, (
                f"Violación [ARCH-1.6.15] §4: sin mercado publicado la jornada activa debe ser la "
                f"última registrada (J11), se obtuvo J{board['jornada_actual']}."
            )
        finally:
            sesion.close()

    def test_resolver_jornada_actual_boveda_vacia_devuelve_none(self):
        """[GOVERNANCE-01] Bóveda sin snapshots ⇒ `None`: cero invención de jornadas."""
        sesion = _boveda_efimera()
        try:
            assert resolver_jornada_actual_dinamica(sesion, 262) is None, (
                "Violación [GOVERNANCE-01]: el resolver inventó una jornada sin datos en bóveda."
            )
        finally:
            sesion.close()

    def test_whitelist_seguridad_admin_tasks(self):
        """Verifica que el router administrativo rechace tareas fuera de la whitelist."""
        from src.web.routes.admin_tasks import TAREAS_PERMITIDAS, validar_tarea_solicitada

        # Tareas legítimas deben pasar
        assert "centinela_deportivo" in TAREAS_PERMITIDAS
        assert "centinela_mercado" in TAREAS_PERMITIDAS
        assert "centinela_progol" in TAREAS_PERMITIDAS
        assert "cadena_ingesta_total" in TAREAS_PERMITIDAS

        # Comando malicioso o arbitrario debe arrojar ValueError
        with pytest.raises(ValueError):
            validar_tarea_solicitada("rm -rf /")

        with pytest.raises(ValueError):
            validar_tarea_solicitada("tarea_inventada_no_autorizada")

    def test_erradicacion_max_width_145px_en_theme_css(self):
        """Verifica que theme.css NO contenga la regla rígida max-width: 145px que corta nombres."""
        css_path = os.path.join("src", "web", "static", "css", "theme.css")
        assert os.path.exists(css_path), "theme.css no encontrado"

        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()

        # Prohibido el límite rígido de 145px en las celdas de equipos
        assert "max-width: 145px" not in css, \
            "Violación DES-QBE-049: max-width: 145px persiste en theme.css y corta nombres de equipos"

    def test_cockpit_cuarta_pestana_centro_control(self):
        """Verifica que index.html contenga la navegación al Centro de Control y la consola."""
        html_path = os.path.join("src", "web", "templates", "index.html")
        assert os.path.exists(html_path), "index.html no encontrado"

        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        assert 'view-control-center' in html or 'btn-tab-control' in html, \
            "Violación DES-QBE-048: Falta pestaña de Centro de Control en el header de index.html"
        assert 'terminal-stream-output' in html or 'consola-control' in html, \
            "Violación DES-QBE-048: Falta consola de streaming en la vista de Centro de Control"


class TestAdminTasksAndDynamicMatchday(AbstractTestAdminTasksAndDynamicMatchday):
    """Implementación concreta en The Shield."""
    pass
