# -*- coding: utf-8 -*-
"""
Kybern Industrial — Seeder de Estructura Base [ARCH-1.5.0 · Enmienda Nudo 2]
[LN-QBE-130] · Enmienda Nudo 2

El Seeder SOLO inicializa la estructura base: competición, liga y parámetros macro.
Queda terminantemente prohibido sembrar equipos, posiciones estáticas, partidos o
cuotas comerciales: todo dato fáctico emana de la ingesta viva ([GOVERNANCE-01]).
La bóveda física de escudos se asegura en disco; su sellado en 3NF es competencia
del pipeline HITL de curación.
"""
import logging
import os

from src.storage.gateway import PersistenceGateway
from src.storage.models import Base, Competition, League

logger = logging.getLogger("Seeder")

FOTMOB_LIGAMX_ID = 262
MU_LIGA_LIGAMX = 2.65
GAMMA_HOME_LIGAMX = 0.15

# Escudos primarios que DEBEN existir con bytes reales (> 3 KB) para que la app funcione.
# [ALT-8-C RATIFICADA] Nombres alineados a los slugs canónicos de la identidad fáctica.
_ESCUDOS_CLAVE = [
    "club-america.png", "chivas-guadalajara.png", "cruz-azul.png", "deportivo-toluca.png",
    "club-pachuca.png", "tigres-uanl.png", "rayados-de-monterrey.png", "pumas-unam.png",
    "club-leon.png", "santos-laguna.png", "atlas-fc.png", "atletico-san-luis.png",
    "necaxa.png", "fc-juarez.png", "queretaro-fc.png",
    "club-tijuana.png", "club-puebla.png", "atlante.png"
]


def asegurar_boveda_escudos_base() -> None:
    """[GOVERNANCE-01] Garantiza escudos reales en disco sin sembrar datos fácticos.

    La descarga y el sellado se delegan íntegramente en la curación HITL
    (`sellir_catalogo_en_db` → `sellar_catalogo_en_db`), gobernada por el Gateway.
    """
    from src.storage.crest_resolver import STATIC_CRESTS_DIR

    os.makedirs(STATIC_CRESTS_DIR, exist_ok=True)
    faltantes = [
        escudo
        for escudo in _ESCUDOS_CLAVE
        if not os.path.exists(os.path.join(STATIC_CRESTS_DIR, escudo))
        or os.path.getsize(os.path.join(STATIC_CRESTS_DIR, escudo)) < 3000
    ]
    if not faltantes:
        return

    print(f"[SEEDER] ⚠️ {len(faltantes)} escudos faltantes en bóveda. Ejecutando extracción nativa...")
    from src.storage.curation_service import PROSPECCION_LIGA_MX, sellar_catalogo_en_db

    try:
        with PersistenceGateway().write_transaction() as db:
            sellar_catalogo_en_db(FOTMOB_LIGAMX_ID, PROSPECCION_LIGA_MX, db)
    except Exception as exc:  # best-effort de activos: no bloquea el arranque
        print(f"[SEEDER] ⚠️ Aviso en sellado nativo: {exc}")


def seed_initial_data(gateway=None) -> None:
    """[LN-QBE-130] · Enmienda Nudo 2 Inicializa SOLO la estructura base (idempotente).

    Cero equipos, cero posiciones, cero partidos, cero cuotas. El catálogo fáctico y la
    cartelera los materializa la ingesta viva en la bóveda 3NF.
    """
    gw = gateway or PersistenceGateway()
    with gw.write_transaction() as db:
        if db.query(League).filter(League.fotmob_id == FOTMOB_LIGAMX_ID).first() is None:
            db.add(League(
                name="Liga MX",
                country="México",
                flag=f"/static/img/leagues/league_{FOTMOB_LIGAMX_ID}.png",
                fotmob_id=FOTMOB_LIGAMX_ID,
                is_active=True,
            ))
            db.flush()

        if db.query(Competition).filter(Competition.id == "MEX_LIGAMX").first() is None:
            db.add(Competition(
                id="MEX_LIGAMX",
                name="Liga MX",
                country="México",
                macro_mu_liga=MU_LIGA_LIGAMX,
                macro_gamma_home=GAMMA_HOME_LIGAMX,
            ))


def seed_initial_leagues() -> None:
    """[ARCH-1.5.2] Ciclo de arranque: DDL gobernado + estructura base + activos."""
    gateway = PersistenceGateway()
    gateway.create_all_tables(Base.metadata)
    asegurar_boveda_escudos_base()
    seed_initial_data(gateway)
