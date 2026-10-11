# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DE AISLAMIENTO DE PERSISTENCIA (H-1)
[ARCH-1.5.0-B] & [GOVERNANCE-01] & [GOV-TEST-01]
Régimen: [DIRGEN-STRICT]

Axioma: Ningún juez de The Shield puede alcanzar la bóveda viva `data/qbe_database.db` a través
del canal transaccional `PersistenceGateway`. Este Juez certifica la existencia y vigencia del
Cuádruple Cerrojo materializado por la fixture de sesión en `tests/shield/conftest.py`.

Alcance declarado (honesto): certifica EXCLUSIVAMENTE el canal Gateway. El motor paralelo
`src/storage/database.py` (`engine` / `SessionLocal` / `get_db`) permanece ligado a la bóveda viva
por excepción declarada y se registra como deuda técnica abierta en `[ARCH-1.5.0-B-Δ1]`.
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
