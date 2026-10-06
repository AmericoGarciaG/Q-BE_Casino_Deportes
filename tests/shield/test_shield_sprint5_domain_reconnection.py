# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DE SPRINT 5 (RECONEXIÓN DE DOMINIOS Y UI)
Validación de:
- [LN-QBE-097] Puente de Despacho Unificado entre Rutas Web y Capa 5.
- [ARCH-1.4.28] Integración de IngestionCoordinator en Centro de Control y Mercados.
- [GOV-TEST-01] Aislamiento de Red y Verificación Hermética de Endpoints.
"""

import ast
from pathlib import Path
import pytest
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# 1. AUDITORÍA DE CONTRATO: INTEGRACIÓN EN ADMIN_TASKS ([ARCH-1.4.28])
# ---------------------------------------------------------------------------
def test_arch_1_4_28_admin_tasks_whitelist_and_coordinator_wiring():
    """Audita que admin_tasks.py reconozca IngestionCoordinator y mantenga la whitelist."""
    from src.web.routes.admin_tasks import TAREAS_PERMITIDAS

    # Verificar que la whitelist de 10 tareas sigue intacta (9 de [ARCH-1.4.12] + la purga
    # total in-process sellada por [ARCH-1.4.29]).
    assert "cadena_ingesta_total" in TAREAS_PERMITIDAS
    assert "centinela_deportivo" in TAREAS_PERMITIDAS
    assert "centinela_mercado" in TAREAS_PERMITIDAS
    assert "centinela_progol" in TAREAS_PERMITIDAS
    assert "purga_total_db" in TAREAS_PERMITIDAS
    assert len(TAREAS_PERMITIDAS) == 10

    # Auditar AST de admin_tasks.py para confirmar cableado del coordinador
    admin_tasks_path = Path("src/web/routes/admin_tasks.py")
    assert admin_tasks_path.exists(), "Falta src/web/routes/admin_tasks.py"
    
    with open(admin_tasks_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Debe contemplar la delegación a IngestionCoordinator
    assert "IngestionCoordinator" in code or "ingestion_coordinator" in code, \
        "admin_tasks.py debe integrar la referencia a IngestionCoordinator"


# ---------------------------------------------------------------------------
# 2. AUDITORÍA DE ENDPOINTS EN FASTAPI ([LN-QBE-097])
# ---------------------------------------------------------------------------
def test_ln_qbe_097_markets_routes_registration():
    """Audita que la aplicación registre las rutas oficiales de Sportsbook y Progol."""
    from src.web.app import create_app
    app = create_app()

    # [VAR-10-A / Ficha de Varianza aprobada — Dictamen VARIANZA-10 §1.1] Introspección por
    # CONTRATO PÚBLICO (OpenAPI). FastAPI >= 0.141 (Starlette 1.6.0) sustituyó el volcado de
    # APIRoute en `app.routes` por el proxy opaco `fastapi.routing._IncludedRouter` (sin `.path`
    # y sin sub-rutas públicas): el mecanismo previo quedó derogado por deriva de dependencia
    # (requirements.txt:4 `fastapi>=0.111.0`, cota inferior sin pin), no por defecto del contrato.
    # Se audita lo PUBLICADO/DESPACHABLE (`app.openapi()["paths"]`): API estable y version-agnóstica.
    routes = set(app.openapi().get("paths", {}).keys())
    
    # Endpoints obligatorios de mercado y centro de control
    assert "/api/markets/sportsbook/portfolio/generate" in routes
    assert "/api/markets/progol/optimize" in routes
    assert "/api/admin/tasks/run" in routes


# ---------------------------------------------------------------------------
# 3. VERIFICACIÓN DE CONSUMO ACTIVO DE CAPA 5 EN LA APLICACIÓN
# ---------------------------------------------------------------------------
def test_capa_5_coordinator_is_consumed_in_web_or_scripts():
    """
    Audita que IngestionCoordinator no sea código muerto (H-16):
    Debe ser importado y consumido en al menos un punto del sistema (web o daemons).
    """
    consumers = []
    scan_dirs = [Path("src/web"), Path("scripts")]

    for target_dir in scan_dirs:
        for py_file in target_dir.rglob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "IngestionCoordinator" in content and "test_" not in py_file.name:
                    consumers.append(py_file.name)

    assert len(consumers) > 0, (
        "🚨 VIOLACIÓN H-16: IngestionCoordinator es código muerto. "
        "Debe tener al menos un llamador en src/web/ o scripts/."
    )
