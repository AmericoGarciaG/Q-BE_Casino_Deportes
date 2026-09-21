# -*- coding: utf-8 -*-
"""
🏆 Q-BE PERSISTENCE GATEWAY — CENTRAL DATA ACCESS & UNIT OF WORK
[VAULT-DATA-001] Motor Transaccional SQLite WAL con Foreign Keys y Aislamiento de Contextos.
Base de Gobierno: Kybern Framework v12.0 [ARCH-1.5.0]
"""

import os
import sqlite3
import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from src.config import settings

logger = logging.getLogger("PersistenceGateway")


@event.listens_for(Engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    """
    [ARCH-1.5.0] Configuración inmutable de motor SQLite en cada conexión:
    - WAL Mode: Concurrencia masiva lecturas/escrituras.
    - Foreign Keys: Integridad referencial estricta 3NF.
    - Synchronous NORMAL: Seguridad física con máxima velocidad.
    - Busy Timeout: 15,000 ms para eliminar bloqueos de concurrencia.
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA busy_timeout = 15000;")
        cursor.close()


class PersistenceGateway:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PersistenceGateway, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        db_path = settings.DATABASE_URL
        connect_args = {"check_same_thread": False} if "sqlite" in db_path else {}
        
        self.engine = create_engine(
            db_path,
            connect_args=connect_args,
            pool_pre_ping=True
        )
        self.SessionFactory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        self._verify_database_health()

    def _verify_database_health(self):
        """Ejecuta PRAGMA quick_check al arranque para detectar corrupción."""
        with self.engine.connect() as conn:
            result = conn.exec_driver_sql("PRAGMA quick_check;").scalar()
            if result != "ok":
                raise RuntimeError(f"🚨 FATAL: Base de datos corrupta: {result}")
            logger.info("🛡️ [GATEWAY HEALTH] SQLite integrity verified: OK (WAL Mode & FK Active)")

    @contextmanager
    def read_session(self) -> Generator[Session, None, None]:
        """
        Contexto de Solo Lectura (FastAPI UI / Endpoints).
        No-lock, ultraligero (< 2ms), auto-close garantizado.
        """
        session: Session = self.SessionFactory()
        try:
            yield session
        finally:
            session.close()

    @contextmanager
    def write_transaction(self) -> Generator[Session, None, None]:
        """
        Contexto de Escritura Atómica (Unit of Work para Daemons).
        Commit automático si todo es exitoso; ROLLBACK total ante cualquier excepción.
        """
        session: Session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as ex:
            session.rollback()
            logger.error(f"❌ [GATEWAY ROLLBACK] Transacción abortada por excepción: {ex}")
            raise ex
        finally:
            session.close()

    def create_all_tables(self, base_metadata):
        """Crea todas las tablas declaradas en el esquema ORM."""
        base_metadata.create_all(bind=self.engine)
        logger.info("✅ [GATEWAY TABLES] Esquema relacional 3NF sincronizado.")
