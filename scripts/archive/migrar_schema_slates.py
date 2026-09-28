# -*- coding: utf-8 -*-
"""
🛠️ Q-BE CD WEB — MIGRACIÓN DE ESQUEMA: slates / slate_items
[ARCH-1.5.1-C] Materialización física de las tablas de quiniela (Progol Regular + Revancha).
Régimen: [DIRGEN-STRICT] (esquema 3NF) — Utilitario operativo con guarda anti-pérdida.

Justificación técnica: SQLite no permite ALTER sobre una PRIMARY KEY compuesta ni añadir
columnas NOT NULL sin default, por lo que se recrea el par de tablas desde el ORM.
Guarda fiduciaria: la recreación SOLO se autoriza si ambas tablas están VACÍAS (0 filas).
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.storage.database import Base
from src.storage.gateway import PersistenceGateway
from src.storage.models import Slate, SlateItem  # Efecto de importación: registra [ARCH-1.5.1-C] en Base.metadata


def _registrar_esquema_orm() -> None:
    """
    Guarda anti no-op: verifica que el ORM haya registrado las tablas en `Base.metadata`.
    Sin este import, `create_all` no crea nada y el fallo es silencioso.
    """
    tablas = (Slate.__tablename__, SlateItem.__tablename__)
    faltantes = [t for t in tablas if t not in Base.metadata.tables]
    if faltantes:
        raise RuntimeError(f"🚨 ALTO AL FUEGO: el ORM no registró las tablas {faltantes} en Base.metadata.")


def _contar_filas(conn, tabla: str) -> int:
    """Cuenta filas de forma tolerante (0 si la tabla no existe)."""
    try:
        return int(conn.exec_driver_sql(f"SELECT COUNT(*) FROM {tabla};").scalar() or 0)
    except Exception:
        return 0


def migrar_esquema_slates() -> int:
    """Recrea `slates` y `slate_items` conforme a [ARCH-1.5.1-C]. Retorna código de salida."""
    _registrar_esquema_orm()
    gateway = PersistenceGateway()

    with gateway.engine.begin() as conn:
        n_slates = _contar_filas(conn, "slates")
        n_items = _contar_filas(conn, "slate_items")
        print(f"📊 Estado previo: slates={n_slates} filas | slate_items={n_items} filas")

        if n_slates or n_items:
            print("🚨 ALTO AL FUEGO: las tablas contienen datos fácticos. Recreación ABORTADA para no perder información.")
            return 2

        conn.exec_driver_sql("DROP TABLE IF EXISTS slate_items;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS slates;")
        print("🗑️  Tablas vacías eliminadas: slate_items, slates.")

    gateway.create_all_tables(Base.metadata)
    print("✅ Esquema [ARCH-1.5.1-C] materializado (slates + slate_items).")

    with gateway.engine.connect() as conn:
        for tabla in ("slates", "slate_items"):
            info = conn.exec_driver_sql(f"PRAGMA table_info({tabla});").fetchall()
            columnas = ", ".join(fila[1] for fila in info)
            print(f"   - {tabla} ({len(info)} columnas): {columnas}")

    return 0


if __name__ == "__main__":
    sys.exit(migrar_esquema_slates())
