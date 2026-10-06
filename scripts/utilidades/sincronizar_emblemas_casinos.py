# -*- coding: utf-8 -*-
"""
Kybern Industrial — Script Dedicado: Bóveda de Activos de Operadores de Casino
Base de Gobierno: [ARCH-1.5.10] / [ARCH-1.5.10-B]
Responsabilidad: Descargar, generar trazos locales y anclar en disco los emblemas
de las casas de apuestas (Caliente, Betway, Novibet). CERO hotlinks a terceros.
"""
import os
import sys
import httpx

if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BOOKMAKERS_DIR = os.path.join(PROJECT_ROOT, "src", "web", "static", "img", "bookmakers")
os.makedirs(BOOKMAKERS_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.google.com/"
}

BOOKMAKERS_MASTER = [
    {"slug": "caliente", "nombre": "Caliente_Deportes.MX",
     "urls": ["https://sports.caliente.mx/es_MX/desktop_header_logo.png"]},
    {"slug": "betway", "nombre": "Betway.MX", "viewbox": "0 -2 55 20", "urls": []},
    {"slug": "novibet", "nombre": "Novibet.MX", "viewbox": "0 0 164 38", "urls": []},
]

def generar_emblema_local_svg(casino: dict) -> str:
    """[ARCH-1.5.10-B] Emblema vectorial propio, generado localmente."""
    nombre = casino["nombre"]
    viewbox = str(casino.get("viewbox", "0 0 240 60"))
    vb_x, vb_y, vb_w, vb_h = (float(v) for v in viewbox.split())
    pad = vb_h * 0.18
    radio = vb_h * 0.18
    centro_x = vb_x + pad + radio
    texto_x = vb_x + pad + radio * 2 + vb_h * 0.16
    disponible = max(vb_w - (texto_x - vb_x) - pad, vb_h * 0.2)
    fuente = min(vb_h * 0.34, disponible / max(len(nombre) * 0.58, 1.0))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- [ARCH-1.5.10-B] Emblema de respaldo local. Cero hotlinking. -->
<svg xmlns="http://www.w3.org/2000/svg" width="{vb_w:g}" height="{vb_h:g}" viewBox="{viewbox}" role="img" aria-label="{nombre}">
  <rect x="{vb_x:g}" y="{vb_y:g}" width="{vb_w:g}" height="{vb_h:g}" rx="{vb_h * 0.16:g}" fill="#0f172a"/>
  <circle cx="{centro_x:g}" cy="{vb_y + vb_h / 2:g}" r="{radio:g}" fill="none" stroke="#38BDF8" stroke-width="{vb_h * 0.09:g}"/>
  <circle cx="{centro_x:g}" cy="{vb_y + vb_h / 2:g}" r="{vb_h * 0.045:g}" fill="#38BDF8"/>
  <text x="{texto_x:g}" y="{vb_y + vb_h * 0.67:g}" font-family="Segoe UI, Arial, sans-serif" font-size="{fuente:g}" font-weight="700" fill="#ffffff">{nombre}</text>
</svg>
"""

def sincronizar_casinos():
    print("🎰 Sincronizando Bóveda de Operadores de Casino...")
    anclados = 0
    with httpx.Client(timeout=10.0, headers=HEADERS) as client:
        for casino in BOOKMAKERS_MASTER:
            pri_png = os.path.join(BOOKMAKERS_DIR, f"{casino['slug']}.png")
            alt_svg = os.path.join(BOOKMAKERS_DIR, f"{casino['slug']}.svg")

            if os.path.exists(pri_png) and os.path.getsize(pri_png) > 1000:
                print(f"   ℹ️ Preservado PNG oficial: {casino['nombre']}")
                anclados += 1
                continue

            if os.path.exists(alt_svg):
                print(f"   ℹ️ Preservado SVG oficial: {casino['slug']}.svg")
                anclados += 1
                continue

            descargado = False
            for u in casino.get("urls", []):
                try:
                    r = client.get(u)
                    if r.status_code == 200 and len(r.content) > 1000 and r.content.startswith(b"\x89PNG"):
                        with open(pri_png, "wb") as f: f.write(r.content)
                        print(f"   ✅ Descargado PNG: {casino['nombre']}")
                        descargado = True
                        anclados += 1
                        break
                except Exception:
                    pass

            if not descargado:
                with open(alt_svg, "w", encoding="utf-8") as f:
                    f.write(generar_emblema_local_svg(casino))
                print(f"   🛡️ Generado SVG local de respaldo: {casino['slug']}.svg")
                anclados += 1

    print(f"🏁 Verificados: {anclados}/{len(BOOKMAKERS_MASTER)} operadores de casino.\n")

if __name__ == "__main__":
    sincronizar_casinos()