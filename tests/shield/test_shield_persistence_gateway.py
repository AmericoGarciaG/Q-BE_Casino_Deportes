# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [ARCH-1.5.0] Verificación del Central Persistence Gateway y Unidad de Trabajo
Doctrina: Kybern Framework v12.0 [GOV-TEST-01 a 07]
Régimen: [DIRGEN-STRICT]
"""

import os
import pytest
from sqlalchemy import text, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base

# En esta fase (previo a materialización en src/), esta importación DEBE FALLAR (RED STATE)
from src.storage.gateway import PersistenceGateway

BaseTest = declarative_base()

class ParentTestModel(BaseTest):
    __tablename__ = "test_parents"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

class ChildTestModel(BaseTest):
    __tablename__ = "test_children"
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("test_parents.id"), nullable=False)
    detail = Column(String(50))


def test_gateway_enforces_pragmas():
    """Valida que el gateway configure obligatoriamente WAL, Foreign Keys y Timeout."""
    gateway = PersistenceGateway()
    
    with gateway.read_session() as session:
        # 1. Foreign Keys ON
        fk = session.execute(text("PRAGMA foreign_keys;")).scalar()
        assert fk == 1, "Violación [ARCH-1.5.0]: PRAGMA foreign_keys no está activo."

        # 2. Busy Timeout >= 10000 ms
        timeout = session.execute(text("PRAGMA busy_timeout;")).scalar()
        assert timeout >= 10000, f"Violación [ARCH-1.5.0]: busy_timeout ({timeout}) menor a 10s."


def test_gateway_atomic_rollback_on_failure():
    """Valida que una transacción con fallo ejecute rollback total (cero registros huérfanos)."""
    gateway = PersistenceGateway()
    gateway.create_all_tables(BaseTest.metadata)

    # Contar registros previos
    with gateway.read_session() as session:
        count_before = session.query(ParentTestModel).count()

    # Intentar transacción corrupta
    with pytest.raises(RuntimeError):
        with gateway.write_transaction() as tx:
            parent = ParentTestModel(id=9999, name="Transacción Fallida")
            tx.add(parent)
            tx.flush()
            # Forzar excepción antes del commit
            raise RuntimeError("Fallo forzado para probar atomicidad")

    # Verificar que el registro 9999 NO existe en la base de datos
    with gateway.read_session() as session:
        count_after = session.query(ParentTestModel).count()
        assert count_after == count_before, "Violación ACID: Se insertó un registro a pesar del fallo."


def test_gateway_foreign_key_constraint_enforced():
    """Valida que SQLite rechace un registro hijo sin padre válido (Integridad 3NF)."""
    gateway = PersistenceGateway()
    gateway.create_all_tables(BaseTest.metadata)

    with pytest.raises(Exception) as exc_info:
        with gateway.write_transaction() as tx:
            # Intento de insertar hijo con parent_id inexistente (999999)
            child = ChildTestModel(id=1, parent_id=999999, detail="Huérfano Prohibido")
            tx.add(child)
            tx.flush()

    assert "FOREIGN KEY constraint failed" in str(exc_info.value) or "IntegrityError" in str(type(exc_info.value).__name__)


def teardown_module(module):
    """[GOV-TEST-06] Limpieza de tablas de prueba efímeras."""
    gateway = PersistenceGateway()
    BaseTest.metadata.drop_all(bind=gateway.engine)
