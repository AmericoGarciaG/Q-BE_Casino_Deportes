# -*- coding: utf-8 -*-
"""
🔬 SONDA FORENSE INDEPENDIENTE: INSPECCIÓN REAL DEL DOM DE BETWAY.MX
Objetivo: Capturar URL final, título, capturas de pantalla, XHR y selectores reales.
"""

import os
import sys

# Forzar encoding UTF-8 para consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

URL_BETWAY = "https://betway.mx/mx/es-mx/sports/grp/soccer/mexico/liga-mx?tab=matches"
OUTPUT_DIR = os.path.join("data", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("\n" + "="*80)
print(f"🚀 INICIANDO SONDA FORENSE CONTRA BETWAY.MX...")
print(f"URL: {URL_BETWAY}")
print("="*80 + "\n")

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-infobars",
            "--ignore-certificate-errors",
        ]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1366, "height": 768},
        locale="es-MX",
        timezone_id="America/Mexico_City"
    )
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # Registrar llamadas de red (XHR/Fetch) para detectar su API interna
    api_calls = []
    page.on("response", lambda resp: api_calls.append(resp.url) if any(k in resp.url.lower() for k in ["api", "event", "match", "feed", "sports"]) else None)

    try:
        response = page.goto(URL_BETWAY, timeout=35000, wait_until="domcontentloaded")
        page.wait_for_timeout(6000) # Espera a que hidrate

        url_final = page.url
        titulo = page.title()
        status_http = response.status if response else "N/A"

        print(f"📍 STATUS HTTP: {status_http}")
        print(f"📍 URL FINAL: {url_final}")
        print(f"📍 TÍTULO DE PÁGINA: {titulo}")

        # Guardar captura visual para que el Director y el Arquitecto auditen
        screenshot_path = os.path.join(OUTPUT_DIR, "evidencia_betway.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 CAPTURA GUARDADA EN: {screenshot_path}")

        # Extraer texto visible del cuerpo (primeros 1,500 caracteres)
        body_text = page.inner_text("body")
        print("\n--- EXTRACTO DE TEXTO VISIBLE EN EL BODY ---")
        print(body_text[:1500])
        print("--------------------------------------------\n")

        # Probar selectores candidatos reales en Betway
        selectores_prueba = [
            ".eventRow",
            "[data-event-id]",
            ".collapsible-item",
            "[data-testid*='event']",
            "[class*='eventCard']",
            "[class*='matchCard']",
            "[class*='coupon']",
            "button[class*='outcome']",
            "[data-testid*='outcome']"
        ]

        print("--- AUDITORÍA DE SELECTORES EN DOM ---")
        for sel in selectores_prueba:
            nodos = page.query_selector_all(sel)
            print(f"Selector '{sel}': {len(nodos)} elementos encontrados")

        print("\n--- LLAMADAS XHR / API DETECTADAS (TOP 10) ---")
        for api in api_calls[:10]:
            print(f"  -> {api}")

    except Exception as ex:
        print(f"❌ ERROR CRÍTICO EN SONDA: {ex}")
    finally:
        browser.close()

print("\n" + "="*80)
print("✅ SONDA CONCLUIDA. ENVÍA EL REPORTE AL ARQUITECTO.")
print("="*80 + "\n")
