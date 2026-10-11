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

Alcance declarado (honesto): aísla el canal transaccional `PersistenceGateway`. El motor paralelo
`src/storage/database.py` (`engine` / `SessionLocal` / `get_db`) permanece ligado a `data/qbe_database.db`
por excepción declarada y se registra como deuda técnica abierta en `[ARCH-1.5.0-B-Δ1]`.
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

    # ── Nivel 4: Centinela fail-loud (imposibilita degradar en silencio a la bóveda viva) ────────
    url_resuelta = str(gateway.engine.url)
    if BOVEDA_VIVA in url_resuelta or sandbox.as_posix() not in url_resuelta:
        gateway.engine.dispose()
        PersistenceGateway._instance = None
        shutil.rmtree(sandbox, ignore_errors=True)
        raise RuntimeError(
            "🚨 FATAL [ARCH-1.5.0-B]: falló el aislamiento de persistencia de The Shield. El motor "
            f"del Gateway resuelve a '{url_resuelta}' en lugar del sandbox efímero "
            f"'{sandbox.as_posix()}'. Ejecución abortada para impedir mutaciones sobre la bóveda viva."
        )

    yield gateway

    # ── Teardown: liberar el motor y descartar el sandbox efímero ────────────────────────────────
    gateway.engine.dispose()
    PersistenceGateway._instance = None
    shutil.rmtree(sandbox, ignore_errors=True)
