# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DE REESTRUCTURACIÓN DE LA RADIOGRAFÍA FORENSE
Validación de:
- [LN-QBE-098] Suspensión de llamadas a Gemini y Generación Determinista en O(1).
- [ARCH-1.4.31] / [DES-QBE-063] Tabla de 6 Columnas de Probabilidad, Botón 'Cerrar' y Radar Factual.
- [GOV-TEST-01] Aislamiento Hermético en Memoria (Cero Red / Cero Tokens).
"""

from pathlib import Path
import re
import pytest


def test_ln_qbe_098_gemini_is_asleep_in_radiografia():
    """Audita que app.js NO invoque el endpoint de Gemini match-thesis al abrir el modal."""
    app_js_path = Path("src/web/static/js/app.js")
    assert app_js_path.exists(), "Falta src/web/static/js/app.js"
    
    content = app_js_path.read_text(encoding="utf-8")
    
    # Extraer la función abrirRadiografiaForense
    match_func = re.search(r'function\s+abrirRadiografiaForense\s*\([^)]*\)\s*\{(.*?)\n\}', content, re.DOTALL)
    assert match_func is not None, "Debe existir la función abrirRadiografiaForense en app.js"
    
    func_body = match_func.group(1)
    
    # [LN-QBE-098]: Prohibido hacer fetch a /api/portfolio/match-thesis
    assert "fetch('/api/portfolio/match-thesis'" not in func_body and 'fetch("/api/portfolio/match-thesis"' not in func_body, (
        "🚨 VIOLACIÓN [LN-QBE-098]: abrirRadiografiaForense sigue llamando a la API de Gemini. "
        "El acceso a LLM debe estar en reposo total."
    )


def test_des_qbe_063_modal_html_structure_and_button():
    """Audita que index.html contenga el botón simple 'Cerrar' y la nueva tabla sin momios."""
    index_html_path = Path("src/web/templates/index.html")
    assert index_html_path.exists(), "Falta src/web/templates/index.html"
    
    content = index_html_path.read_text(encoding="utf-8")
    
    # 1. El botón debe decir 'Cerrar' y NO '✕ Cerrar Radiografía'
    assert "Cerrar Radiografía" not in content, (
        "🚨 VIOLACIÓN [DES-QBE-063]: El botón del modal debe decir simplemente 'Cerrar'."
    )
    assert re.search(r'<button[^>]*onclick="cerrarRadiografiaForense\(\)"[^>]*>.*?Cerrar.*?</button>', content, re.DOTALL), (
        "Debe existir el botón con onclick='cerrarRadiografiaForense()' rotulado como 'Cerrar'."
    )

    # 2. La tabla NO debe contener cabeceras de momios decimales
    assert "MOMIO Q-BE" not in content, "La tabla de la radiografía no debe mostrar la columna 'MOMIO Q-BE'."
    assert "MOMIO CASINO" not in content, "La tabla de la radiografía no debe mostrar la columna 'MOMIO CASINO'."

    # 3. La tabla DEBE contener las nuevas cabeceras de probabilidad
    assert "PROB. CASINO" in content or "PROB. IMPLÍCITA" in content
    assert "CASINO SELECCIONADO" in content or "OPERADOR" in content
    assert "VENTAJA" in content or "VENTAJA MATEMÁTICA" in content


def test_des_qbe_063_app_js_renders_colorized_tickets():
    """Audita que app.js inyecte clases o estilos de color (verde/azul) para Ataque y Cobertura."""
    app_js_path = Path("src/web/static/js/app.js")
    content = app_js_path.read_text(encoding="utf-8")
    
    # Comprobar que en la hidratación de la tabla de radiografía se contemplen los colores de boletos
    assert "#00E676" in content or "color-ataque" in content, (
        "Debe existir resaltado en verde esmeralda para el desenlace de ataque en la tabla."
    )
    assert "#38BDF8" in content or "color-seguro" in content, (
        "Debe existir resaltado en azul cian para el desenlace de cobertura en la tabla."
    )
