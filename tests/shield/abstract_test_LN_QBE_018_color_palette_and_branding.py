"""
Kybern Industrial Governance — Twin-Test Protocol
Juez Inmutable: [DES-QBE-005 / DES-QBE-010 / DES-QBE-016]
Paleta Disciplinada, Identidad Discreta y Checkbox Único
ID de Prueba: SHIELD-TEST-LN-QBE-018-BRANDING-CLEAN
Estado: [ALGO-PROTECTED] — Aserciones INMUTABLES sin autorización del Director Humano

NOTA FORENSE v1.1: Los tokens prohibidos residen en archivos CSS/JS estáticos,
no en el HTML estático del servidor. El Juez inspecciona 3 capas:
  1. HTML renderizado por FastAPI (sin JS ejecutado) — DOM estático.
  2. theme.css — Variables y reglas CSS que definen la paleta real.
  3. app.js — Templates de DOM inyectados dinámicamente en el cliente.
"""
import abc
import re
from bs4 import BeautifulSoup


class AbstractTestColorPaletteAndBranding(abc.ABC):
    """
    Juez Abstracto que audita las tres capas de presentación:
    1. [DES-QBE-005] Erradicación de amarillos/naranjas chillones en la
       marca, botones principales y variables CSS.
    2. [DES-QBE-010] Identidad de marca discreta (no invasiva).
    3. [DES-QBE-016] Eliminación de selectores duplicados y emojis de
       'Seleccionado' en las tarjetas de partidos (incluyendo el DOM
       inyectado dinámicamente por JavaScript).
    """

    @abc.abstractmethod
    def get_rendered_web_html(self) -> str:
        """
        Retorna el HTML completo de la aplicación tal como lo sirve
        el servidor FastAPI local (GET /).
        """
        pass

    @abc.abstractmethod
    def get_theme_css_content(self) -> str:
        """
        Retorna el contenido textual de /static/css/theme.css
        tal como lo sirve el servidor.
        """
        pass

    @abc.abstractmethod
    def get_app_js_content(self) -> str:
        """
        Retorna el contenido textual de /static/js/app.js
        tal como lo sirve el servidor.
        """
        pass

    # ─────────────────────────────────────────────────────────────────
    # LEY [DES-QBE-005]: Paleta Cromática Disciplinada — Capa CSS
    # ─────────────────────────────────────────────────────────────────

    def test_theme_css_no_amber_in_brand_or_nav_variables(self):
        """
        [SHIELD-UX / DES-QBE-005]
        El archivo theme.css NO debe definir variables o reglas que
        asignen colores ámbar/amarillo (#f59e0b, #fbbf24, #ff9800) a
        los selectores de marca, cabeceras, pestañas activas o botones
        primarios.

        NOTA: La presencia de `--accent-amber` como variable CSS de
        paleta global está permitida SOLO si NO se aplica a .brand-*,
        nav .active, header, o .btn-primary. Esta prueba verifica que
        dichos selectores no referencien el token ámbar.
        """
        css = self.get_theme_css_content()

        # Tokens ámbar prohibidos en la hoja de estilos de la marca/nav
        amber_tokens = ["#f59e0b", "#fbbf24", "#ff9800", "#d97706"]

        # Extraer bloques CSS relevantes a marca y navegación
        # Buscamos si algún selector de marca/nav contiene colores ámbar
        forbidden_selectors_pattern = re.compile(
            r'(\.brand[\w-]*|header\s*h1|\.app-header|\.app-title|'
            r'nav\s*\.active|\.tab-active|\.tab\.active|\.nav-tab\.active|'
            r'\.btn-primary|#btn-dispatch-portfolio)'
            r'[^}]*?(' + '|'.join(re.escape(t) for t in amber_tokens) + r')',
            re.IGNORECASE | re.DOTALL
        )
        match = forbidden_selectors_pattern.search(css)
        assert not match, (
            f"[DES-QBE-005] REGRESIÓN CSS: Se detectó color ámbar prohibido "
            f"en un selector de marca/navegación/botón primario en theme.css.\n"
            f"Fragmento: {match.group(0)[:200]}\n"
            f"Los selectores de marca deben usar #94A3B8, #CBD5E1 o #FFFFFF. "
            f"Las pestañas activas deben usar #38BDF8 / #0284C7."
        )

    def test_theme_css_no_amber_color_on_logo_or_title(self):
        """
        [SHIELD-UX / DES-QBE-005 / DES-QBE-010]
        El CSS no debe asignar color ámbar (#f59e0b, #fbbf24) al
        texto del logo/título de la aplicación.
        """
        css = self.get_theme_css_content()
        amber_tokens = ["#f59e0b", "#fbbf24", "#ff9800"]

        # Verificar que la variable --accent-amber no se use como 'color'
        # en selectores de texto de cabecera
        for token in amber_tokens:
            # Patrón: color: <token_ambar> dentro de selector de marca/logo
            pattern = re.compile(
                r'(\.brand|\.logo|\.app-title|header\s*h1|\.top-brand)'
                r'[^}]*?color\s*:\s*' + re.escape(token),
                re.IGNORECASE | re.DOTALL
            )
            assert not pattern.search(css), (
                f"[DES-QBE-010] REGRESIÓN: El selector de logo/título usa "
                f"color: {token} en theme.css. Debe usar #94A3B8 o #FFFFFF."
            )

    # ─────────────────────────────────────────────────────────────────
    # LEY [DES-QBE-005]: Paleta — Capa HTML (estilos inline)
    # ─────────────────────────────────────────────────────────────────

    def test_no_bright_yellow_or_orange_in_primary_buttons_html(self):
        """
        [SHIELD-UX / DES-QBE-005]
        Los botones de acción primaria no deben tener background
        naranja (#ff9800) ni ámbar chillón (#f59e0b) como estilo inline.
        """
        html = self.get_rendered_web_html()
        forbidden_patterns = [
            "background: #ff9800",
            "background-color: #ff9800",
            "background: #f59e0b",
            "background-color: #f59e0b",
            "background: #fbbf24",
            "background-color: #fbbf24",
        ]
        for pat in forbidden_patterns:
            assert pat not in html, (
                f"[DES-QBE-005] REGRESIÓN: '{pat}' detectado como estilo "
                f"inline en el HTML de botones. Debe usar #0284C7 o #38BDF8."
            )

    def test_no_bright_yellow_or_orange_in_brand_header_html(self):
        """
        [SHIELD-UX / DES-QBE-005]
        El contenedor de marca en el HTML estático no debe tener
        colores ámbar/naranja como atributos de estilo inline.
        """
        html = self.get_rendered_web_html()
        soup = BeautifulSoup(html, "html.parser")

        brand_el = soup.select_one(
            ".top-brand-header, .brand-logo, header h1, "
            ".brand-title, .app-header, nav .brand"
        )
        if brand_el:
            style_str = str(brand_el).lower()
            forbidden_tokens = [
                "#ff9800", "#f59e0b", "#fbbf24",
                "color: orange", "color:orange",
                "color: yellow", "color:yellow",
                "color: gold", "color:gold",
            ]
            violations = [t for t in forbidden_tokens if t in style_str]
            assert not violations, (
                f"[DES-QBE-005] REGRESIÓN CROMÁTICA: El encabezado de marca "
                f"usa colores prohibidos inline: {violations}."
            )

    # ─────────────────────────────────────────────────────────────────
    # LEY [DES-QBE-016]: Cartelera — Capa JS (DOM inyectado)
    # ─────────────────────────────────────────────────────────────────

    def test_app_js_no_check_emoji_seleccionado_in_fixture_template(self):
        """
        [SHIELD-UX / DES-QBE-016] — CAPA JAVASCRIPT
        El template de tarjeta de partido en app.js NO debe contener
        la cadena '✅ Seleccionado' ni 'Seleccionado' como texto de
        nodo inyectado junto al checkbox.

        Esta prueba audita el código fuente de app.js ANTES de que
        sea ejecutado por el navegador, detectando la violación en su
        origen.
        """
        js = self.get_app_js_content()

        assert "✅ Seleccionado" not in js, (
            "[DES-QBE-016] REGRESIÓN JS: app.js contiene el template "
            "'✅ Seleccionado' que se inyecta dinámicamente en las "
            ".fixture-card. Debe eliminarse. Solo el checkbox comunica selección."
        )

    def test_app_js_fixture_card_template_has_single_checkbox_control(self):
        """
        [SHIELD-UX / DES-QBE-016] — CAPA JAVASCRIPT
        El template HTML de .fixture-card generado en app.js debe
        contener exactamente UN input[type='checkbox'] y ningún otro
        control de selección redundante (radio, select de estado, etc.)
        """
        js = self.get_app_js_content()

        # Extraer el bloque de template de fixture-card del JS
        # Busca el bloque de HTML string entre backticks o comillas
        # que contenga 'fixture-card'
        card_template_pattern = re.compile(
            r'fixture-card.*?(?=\n\s*\n|\};|return\s+`)',
            re.DOTALL | re.IGNORECASE
        )
        match = card_template_pattern.search(js)
        if match:
            template_fragment = match.group(0)
            # Contar checkboxes en el template
            checkbox_count = len(re.findall(
                r"input\s+[^>]*type\s*=\s*['\"]checkbox['\"]",
                template_fragment,
                re.IGNORECASE
            ))
            # El template debe tener exactamente 1 checkbox
            assert checkbox_count <= 1, (
                f"[DES-QBE-016] REGRESIÓN JS: El template de .fixture-card "
                f"en app.js contiene {checkbox_count} checkboxes. "
                f"Debe contener exactamente 1."
            )

    # ─────────────────────────────────────────────────────────────────
    # LEY [DES-QBE-016]: Cartelera — Capa HTML estático
    # ─────────────────────────────────────────────────────────────────

    def test_no_duplicated_check_emoji_in_fixture_cards_html(self):
        """
        [SHIELD-UX / DES-QBE-016] — CAPA HTML
        Si hay tarjetas en el HTML estático, no deben contener
        '✅ Seleccionado' como texto.
        """
        html = self.get_rendered_web_html()
        soup = BeautifulSoup(html, "html.parser")

        fixture_cards = soup.select(".fixture-card")
        for i, card in enumerate(fixture_cards):
            card_text = card.get_text()
            assert "✅ Seleccionado" not in card_text, (
                f"[DES-QBE-016] REGRESIÓN HTML: Tarjeta #{i} contiene "
                f"'✅ Seleccionado' en el HTML estático."
            )

    def test_fixture_cards_have_exactly_one_checkbox_html(self):
        """
        [SHIELD-UX / DES-QBE-016] — CAPA HTML
        Si hay tarjetas .fixture-card en el HTML estático, cada una
        debe contener exactamente UN checkbox.
        """
        html = self.get_rendered_web_html()
        soup = BeautifulSoup(html, "html.parser")

        fixture_cards = soup.select(".fixture-card")
        for i, card in enumerate(fixture_cards):
            checkboxes = card.select("input[type='checkbox']")
            assert len(checkboxes) == 1, (
                f"[DES-QBE-016] REGRESIÓN HTML: Tarjeta #{i} contiene "
                f"{len(checkboxes)} checkboxes (esperado: exactamente 1)."
            )
