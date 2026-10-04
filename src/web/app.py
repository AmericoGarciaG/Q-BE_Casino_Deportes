import os
import sys
import io

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates

from src.storage.seeder import seed_initial_leagues
from src.storage.sync_service import sync_active_leagues_data
from src.web.routes import leagues, portfolio, export, sovereign, markets, admin_tasks
from src.web.routes.admin import router as admin_router, llm_router

# [ARCH-1.4.28] Directorio de plantillas resuelto UNA sola vez para toda la fábrica.
templates = Jinja2Templates(directory="src/web/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Inicializar BD y sincronizar
    print("\n" + "=" * 70)
    print("[Q-BE] PLATAFORMA WEB INDUSTRIAL")
    print("=" * 70)
    seed_initial_leagues()
    sync_active_leagues_data()
    print("[LIFESPAN]: Servidor listo y base de datos sincronizada.")
    print("=" * 70 + "\n")
    yield
    # SHUTDOWN
    print("[LIFESPAN]: Deteniendo servidor Q-BE.")


async def add_telemetry_middleware(request: Request, call_next):
    t0_req = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - t0_req
    if request.url.path.startswith("/api/"):
        print(f"⏱️ [PERF-API]: {request.method} {request.url.path} procesado en {duration:.3f}s")
    return response


def create_app() -> FastAPI:
    """
    [ARCH-1.4.28] Fábrica canónica de la aplicación FastAPI.

    Materializa una instancia web COMPLETA e independiente (middlewares + estáticos +
    routers + sondas de salud) sin ejecutar el `lifespan`: la topología de despacho puede
    auditarse de forma hermética, sin tocar disco ni red (`[GOV-TEST-01]`).

    El módulo publica además el singleton `app = create_app()` para el lanzador
    (`run_app.py`) y para todos los consumidores históricos (`[ARCH-1.7.0]`).
    """
    api = FastAPI(title="Q-BE Casino Deportes Web Platform", lifespan=lifespan)

    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api.middleware("http")(add_telemetry_middleware)

    # Montar estáticos y plantillas
    api.mount("/static", StaticFiles(directory="src/web/static"), name="static")

    api.include_router(leagues.router)
    api.include_router(portfolio.router)
    api.include_router(export.router)
    api.include_router(admin_router)  # [ARCH-1.5.2] Curación Agéntica HITL
    api.include_router(llm_router)    # [ARCH-1.3.4] Telemetría de LLMTokenLedger
    api.include_router(sovereign.router)  # [ARCH-1.4.5] Endpoint Soberano Deportivo Puro
    api.include_router(markets.router)    # [ARCH-1.4.5] Endpoints de Mercados Financieros (Casino / Progol)
    api.include_router(admin_tasks.router)  # [ARCH-1.4.12] Centro de Control: whitelist de tareas

    @api.get("/health")
    def health_check():
        return {"status": "ONLINE", "version": "3.0.0-web", "database": "CONNECTED"}

    @api.get("/", response_class=HTMLResponse)
    def read_root(request: Request):
        return templates.TemplateResponse(request=request, name="index.html")

    @api.get('/favicon.ico', include_in_schema=False)
    async def favicon():
        favicon_path = os.path.join(os.path.dirname(__file__), "static", "img", "favicon.svg")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path, media_type="image/svg+xml")
        return Response(status_code=404)

    return api


app = create_app()
