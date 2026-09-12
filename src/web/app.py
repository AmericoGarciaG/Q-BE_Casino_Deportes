import os
import sys
import io

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates

from src.storage.seeder import seed_initial_leagues
from src.storage.sync_service import sync_active_leagues_data
from src.web.routes import leagues, portfolio, export
from src.web.routes.admin import router as admin_router

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


app = FastAPI(title="Q-BE Casino Deportes Web Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar estáticos y plantillas
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
templates = Jinja2Templates(directory="src/web/templates")

app.include_router(leagues.router)
app.include_router(portfolio.router)
app.include_router(export.router)
app.include_router(admin_router)  # [ARCH-1.5.2] Curación Agéntica HITL

@app.get("/health")
def health_check():
    return {"status": "ONLINE", "version": "3.0.0-web", "database": "CONNECTED"}

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(os.path.dirname(__file__), "static", "img", "crests", "america.png")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return Response(status_code=204)
