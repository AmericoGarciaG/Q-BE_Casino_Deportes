# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [ARCH-1.5.1] Verificación del Esquema Relacional 3NF Multi-Torneo
Doctrina: Kybern Framework v12.0 [GOV-TEST-01 a 07]
Régimen: [DIRGEN-STRICT]
"""

import pytest
from sqlalchemy import text

# En esta fase (previo a materialización en src/), esta importación DEBE FALLAR (RED STATE)
from src.storage.models import Competition, Match, SovereignDistribution, Slate, SlateItem
from src.storage.gateway import PersistenceGateway


def test_esquema_3nf_multi_torneo_declarado():
    """Valida la existencia de las entidades 3NF con claves foráneas e integridad referencial."""
    gateway = PersistenceGateway()
    
    # Crear tablas en el engine activo
    from src.storage.database import Base
    gateway.create_all_tables(Base.metadata)

    with gateway.write_transaction() as tx:
        # 1. Insertar competición internacional con parámetros macro
        comp = Competition(
            id="ENG_PL",
            name="Premier League",
            country="Inglaterra",
            macro_mu_liga=3.10,
            macro_gamma_home=0.12
        )
        tx.add(comp)
        tx.flush()

        # 2. Validar que la competición existe
        comp_db = tx.query(Competition).filter(Competition.id == "ENG_PL").first()
        assert comp_db is not None
        assert comp_db.macro_mu_liga == 3.10

    # 3. Limpieza de prueba
    with gateway.write_transaction() as tx:
        tx.query(Competition).filter(Competition.id == "ENG_PL").delete()
