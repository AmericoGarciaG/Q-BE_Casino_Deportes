# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — CONFTEST DE AISLAMIENTO DE PERSISTENCIA DEL CANAL GATEWAY
[ARCH-1.5.0-B] & [GOVERNANCE-01] & [GOV-TEST-01]
Régimen: [DIRGEN-STRICT]

Cuádruple Cerrojo (fixture de sesión autouse, exclusiva del arnés `tests/shield/`):
  1. Configuración temprana → `os.environ["DATABASE_URL"]` + re-apuntado del singleton Pydantic `settings`
     (congelado en el import de `src/config.py`; el entorno por sí solo NO basta).
  2. Reseteo del singleton → `engine.dispose()` + `PersistenceGateway._instance = None`.
  3. Clonado online → `sqlite3.Connection.backup` (huésped `mode=ro`, seguro en WAL con el servidor
     encendido): los jueces de inspección conservan su evidencia fáctica sin exponer la bóveda viva.
  4. Centinela fail-loud → `RuntimeError` si el motor resolviera a la bóveda viva.

Extensión P0-1 (Aislamiento Hermético Total): el mismo cerrojo intercepta el motor paralelo
`src/storage/database.py` (`engine` / `SessionLocal` / `get_db`), lo redirige al SQLite efímero y
neutraliza los alias capturados por imports directos (`from ... import SessionLocal, engine`).
La bóveda viva queda fuera del alcance de la totalidad de la superficie de persistencia de pruebas.
"""

import os
import shutil
import sqlite3
from pathlib import Path

import pytest

BOVEDA_VIVA = "data/qbe_database.db"
NOMBRE_SANDBOX = "qbe_shield_db"
NOMBRE_CLON = "test_isolated.db"


@pytest.fixture(scope="session", autouse=True)
def boveda_gateway_aislada(tmp_path_factory):
    """Aísla el canal Gateway en un clon efímero de la bóveda viva."""
    import src.config as cfg
    from src.storage.gateway import PersistenceGateway
    from src.storage.models import Base

    # ── Nivel 1: Configuración temprana (entorno + singleton congelado en el import) ─────────────
    sandbox = tmp_path_factory.mktemp(NOMBRE_SANDBOX)
    archivo_clon = sandbox / NOMBRE_CLON
    url_efimera = f"sqlite:///{archivo_clon.as_posix()}"
    os.environ["DATABASE_URL"] = url_efimera
    cfg.settings.DATABASE_URL = url_efimera

    # ── Nivel 2: Reseteo del singleton (pudo nacer apuntando a la bóveda viva en la colección) ───
    instancia_previa = PersistenceGateway._instance
    if instancia_previa is not None:
        try:
            instancia_previa.engine.dispose()
        except Exception:  # pragma: no cover - defensa ante motor ya inutilizable
            pass
        PersistenceGateway._instance = None

    # ── Nivel 3: Clonado online de la evidencia fáctica (únicamente lectura sobre el huésped) ────
    boveda = Path(BOVEDA_VIVA)
    if boveda.exists():
        uri_ro = f"file:{boveda.resolve().as_posix()}?mode=ro"
        conexion_origen = sqlite3.connect(uri_ro, uri=True)
        conexion_destino = sqlite3.connect(archivo_clon.as_posix())
        try:
            conexion_origen.backup(conexion_destino)
        finally:
            conexion_destino.close()
            conexion_origen.close()

    gateway = PersistenceGateway()
    Base.metadata.create_all(bind=gateway.engine)

    # ── Extensión P0-1: Aislamiento Hermético Total del motor paralelo ──────────────────────────
    import sys

    import src.storage.database as db_module
    from sqlalchemy.orm import sessionmaker

    motor_previo = db_module.engine
    sesion_previa = db_module.SessionLocal

    db_module.engine = gateway.engine
    db_module.SessionLocal = sessionmaker(
        bind=gateway.engine, autocommit=False, autoflush=False
    )
    Base.metadata.create_all(bind=db_module.engine)

    # Los módulos que hicieron `from src.storage.database import SessionLocal/engine` conservan
    # el objeto previo: se reconfigura in situ y se re-apunta cada alias ya cargado en `sys.modules`.
    sesion_previa.configure(bind=gateway.engine)
    for modulo in list(sys.modules.values()):
        if getattr(modulo, "SessionLocal", None) is sesion_previa:
            modulo.SessionLocal = db_module.SessionLocal
        if getattr(modulo, "engine", None) is motor_previo:
            modulo.engine = db_module.engine

    # ── Nivel 4: Centinela fail-loud (Gateway + database.py, sin degradar a la bóveda viva) ─────
    url_resuelta = str(gateway.engine.url)
    url_db = str(db_module.engine.url)
    if (
        BOVEDA_VIVA in url_resuelta
        or sandbox.as_posix() not in url_resuelta
        or BOVEDA_VIVA in url_db
        or url_db != url_resuelta
    ):
        gateway.engine.dispose()
        PersistenceGateway._instance = None
        shutil.rmtree(sandbox, ignore_errors=True)
        raise RuntimeError(
            "🚨 FATAL [ARCH-1.5.0-B / P0-1]: falló el aislamiento de persistencia de The Shield. "
            f"Gateway='{url_resuelta}', database.py='{url_db}', sandbox efímero="
            f"'{sandbox.as_posix()}'. Ejecución abortada para impedir mutaciones sobre la bóveda viva."
        )

    yield gateway

    # ── Teardown: liberar el motor y descartar el sandbox efímero ────────────────────────────────
    gateway.engine.dispose()
    PersistenceGateway._instance = None
    shutil.rmtree(sandbox, ignore_errors=True)
