"""
Kybern Industrial Governance — The Shield
Prueba Concreta: [DES-QBE-005 / DES-QBE-010 / DES-QBE-016]
Paleta Cromática Disciplinada, Identidad Discreta y Checkbox Único
ID: SHIELD-TEST-LN-QBE-018-BRANDING-CLEAN

El Prisionero: hereda del Juez Abstracto v1.1 y provee el contenido real
de 3 capas de presentación usando TestClient(app):
  1. HTML estático servido por FastAPI (GET /)
  2. theme.css  (GET /static/css/theme.css)
  3. app.js     (GET /static/js/app.js)

Comportamiento esperado en Fase 2 (Twin-Test Protocol):
  → Estado ROJO (RED): Los tests deben FALLAR porque:
    - theme.css contiene '--accent-amber: #f59e0b' aplicado a selectores
      de marca/navegación.
    - app.js contiene el template '✅ Seleccionado' inyectado en .fixture-card.
"""
from fastapi.testclient import TestClient

from tests.shield.abstract_test_LN_QBE_018_color_palette_and_branding import (
    AbstractTestColorPaletteAndBranding,
)
from src.web.app import app
from src.storage.seeder import seed_initial_leagues


class TestLN_QBE_018_ColorPaletteAndBranding_Concrete(
    AbstractTestColorPaletteAndBranding
):
    """
    Prisionero Concreto — Hereda del Juez Inmutable v1.1.
    Expone las tres capas de presentación al Juez Abstracto para
    auditoría de paleta disciplinada e identidad discreta.
    """

    def setup_method(self):
        """Siembra las ligas iniciales para que el DOM esté poblado."""
        seed_initial_leagues()
        self._client = TestClient(app)

    def get_rendered_web_html(self) -> str:
        """HTML raíz del servidor FastAPI (sin ejecución de JS)."""
        resp = self._client.get("/")
        assert resp.status_code == 200, (
            f"[QBE-018] Error al obtener HTML raíz '/': "
            f"HTTP {resp.status_code} — {resp.text[:300]}"
        )
        return resp.text

    def get_theme_css_content(self) -> str:
        """
        Contenido de /static/css/theme.css — donde viven las
        variables CSS y reglas de paleta de la aplicación.
        """
        resp = self._client.get("/static/css/theme.css")
        assert resp.status_code == 200, (
            f"[QBE-018] Error al obtener theme.css: "
            f"HTTP {resp.status_code}"
        )
        return resp.text

    def get_app_js_content(self) -> str:
        """
        Contenido de /static/js/app.js — donde viven los templates
        HTML inyectados dinámicamente en el DOM del cliente.
        """
        resp = self._client.get("/static/js/app.js")
        assert resp.status_code == 200, (
            f"[QBE-018] Error al obtener app.js: "
            f"HTTP {resp.status_code}"
        )
        return resp.text
