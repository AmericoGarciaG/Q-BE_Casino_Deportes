# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DE AISLAMIENTO DE PERSISTENCIA (H-1)
[ARCH-1.5.0-B] & [GOVERNANCE-01] & [GOV-TEST-01]
Régimen: [DIRGEN-STRICT]

Axioma: Ningún juez de The Shield puede alcanzar la bóveda viva `data/qbe_database.db` a través
del canal transaccional `PersistenceGateway`. Este Juez certifica la existencia y vigencia del
Cuádruple Cerrojo materializado por la fixture de sesión en `tests/shield/conftest.py`.

Alcance: certifica el canal Gateway y, desde la Enmienda de Aislamiento Hermético Total (P0-1),
también el motor paralelo `src/storage/database.py` (`engine` / `SessionLocal` / `get_db`), que el
cerrojo de `tests/shield/conftest.py` intercepta y redirige hacia el SQLite efímero de la sesión.
"""

import os

from src.config import settings
from src.storage.gateway import PersistenceGateway

BOVEDA_VIVA = "data/qbe_database.db"


def test_invarianza_1_motor_del_gateway_no_resuelve_a_la_boveda_viva():
    """Invarianza #1: el motor del Gateway debe resolver a un artefacto efímero, jamás a la bóveda viva."""
    gateway = PersistenceGateway()
    url_motor = str(gateway.engine.url)
    assert BOVEDA_VIVA not in url_motor, (
        "🚨 VIOLACIÓN CRÍTICA [GOV-TEST-01]: el motor del `PersistenceGateway` está apuntando a la "
        f"bóveda viva ({url_motor}). El cerrojo Nivel 2 (reseteo del singleton) no se materializó."
    )
    assert gateway.engine.url.database not in (None, "", ":memory:"), (
        "🚨 VIOLACIÓN CRÍTICA [GOV-TEST-01]: el motor del Gateway no resuelve a un archivo físico "
        "efímero; la evidencia fáctica del clonado (Nivel 3) es inverificable."
    )


def test_invarianza_2_variable_de_entorno_secuestrada():
    """Invarianza #2: `DATABASE_URL` debe estar secuestrada hacia el artefacto descartable de la sesión."""
    url_entorno = os.environ.get("DATABASE_URL")
    assert url_entorno, (
        "🚨 VIOLACIÓN CRÍTICA [GOV-TEST-01]: `DATABASE_URL` no fue fijada por la fixture de sesión; "
        "el cerrojo Nivel 1 (configuración temprana) no está activo."
    )
    assert BOVEDA_VIVA not in url_entorno, (
        f"🚨 VIOLACIÓN CRÍTICA [GOV-TEST-01]: `DATABASE_URL` apunta a la bóveda viva ({url_entorno})."
    )


def test_invarianza_3_singleton_pydantic_reapuntado_y_ruta_efimera():
    """Invarianza #3: el singleton Pydantic `settings` debe estar re-apuntado a una ruta efímera de pytest.

    `src/config.py` congela `settings` en el import; fijar únicamente `os.environ` produce un falso
    verde. La coexistencia de ambos apuntadores es la única prueba válida del Nivel 1.
    """
    url_entorno = os.environ.get("DATABASE_URL", "")
    assert settings.DATABASE_URL == url_entorno, (
        "🚨 VIOLACIÓN CRÍTICA [GOV-TEST-01]: el singleton `settings` no fue re-apuntado "
        f"(settings={settings.DATABASE_URL} vs entorno={url_entorno}); el cerrojo es nominal."
    )
    assert "pytest" in url_entorno and BOVEDA_VIVA not in url_entorno, (
        "🚨 VIOLACIÓN CRÍTICA [GOV-TEST-01]: la URL efectiva no reside en el sandbox efímero de pytest "
        f"({url_entorno})."
    )


class TestAislamientoHermeticoDatabasePy:
    """[P0-1] Extensión del Juez Inmutable al motor paralelo `src.storage.database`."""

    def test_aislamiento_hermetico_database_py(self):
        """Certifica que `engine` / `SessionLocal` fueron interceptados por el cerrojo P0-1."""
        import sqlite3
        import uuid
        from pathlib import Path

        import src.storage.database as db_module
        from src.storage.models import League

        gateway = PersistenceGateway()
        url_motor = str(db_module.engine.url)
        assert BOVEDA_VIVA not in url_motor, (
            "🚨 VIOLACIÓN CRÍTICA [ARCH-1.5.0-B / P0-1]: `src.storage.database.engine` sigue "
            f"apuntando a la bóveda viva ({url_motor}). El cerrojo de aislamiento hermético "
            "total no se materializó en `tests/shield/conftest.py`."
        )
        assert db_module.engine.url == gateway.engine.url, (
            "🚨 VIOLACIÓN CRÍTICA [ARCH-1.5.0-B / P0-1]: el motor paralelo "
            f"({db_module.engine.url}) no coincide con el motor efímero del Gateway "
            f"({gateway.engine.url}); el split-brain de persistencia persiste."
        )

        marca = f"P0-1-{uuid.uuid4().hex}"
        fotmob_id = 900_000_000 + (uuid.uuid4().int % 90_000_000)
        sesion = db_module.SessionLocal()
        try:
            sesion.add(
                League(
                    name=marca,
                    country="Sandbox P0-1",
                    flag="🏳️",
                    fotmob_id=fotmob_id,
                )
            )
            sesion.commit()
        finally:
            sesion.close()

        verificacion = db_module.SessionLocal()
        try:
            assert verificacion.query(League).filter(League.name == marca).count() == 1, (
                "🚨 VIOLACIÓN CRÍTICA [ARCH-1.5.0-B / P0-1]: la escritura dummy no quedó "
                "registrada en el entorno efímero."
            )
        finally:
            verificacion.close()

        # La bóveda viva se inspecciona en modo lectura puro: la ausencia del registro dummy
        # certifica que la escritura de `SessionLocal()` jamás atravesó el motor paralelo.
        boveda_viva = Path(BOVEDA_VIVA)
        if boveda_viva.exists():
            uri_ro = f"file:{boveda_viva.resolve().as_posix()}?mode=ro"
            conexion = sqlite3.connect(uri_ro, uri=True)
            try:
                fila = conexion.execute(
                    "SELECT COUNT(*) FROM leagues WHERE name = ?", (marca,)
                ).fetchone()
            finally:
                conexion.close()
            assert not fila or fila[0] == 0, (
                "🚨 VIOLACIÓN CRÍTICA [ARCH-1.5.0-B / P0-1]: la escritura dummy alcanzó la "
                f"bóveda viva ({boveda_viva}). El aislamiento es nominal, no hermético."
            )

        limpieza = db_module.SessionLocal()
        try:
            limpieza.query(League).filter(League.name == marca).delete()
            limpieza.commit()
        finally:
            limpieza.close()
