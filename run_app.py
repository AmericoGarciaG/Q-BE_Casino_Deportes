import os
import sys
import time
import threading
import webbrowser
import urllib.request
import uvicorn
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Añadir raíz a sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


def abrir_navegador_cuando_este_listo():
    """Espera activamente a que FastAPI responda HTTP 200 en /health antes de lanzar el navegador."""
    url_health = "http://127.0.0.1:8000/health"
    url_app = "http://127.0.0.1:8000"
    
    for _ in range(40):  # Esperar hasta 20 segundos
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(url_health, timeout=1.0) as response:
                if response.status == 200:
                    print("\n🚀 [AUTO-LAUNCH]: Servidor en línea. Abriendo navegador en http://127.0.0.1:8000...", flush=True)
                    webbrowser.open(url_app)
                    break
        except Exception:
            pass


if __name__ == "__main__":
    # Iniciar sonda en segundo plano
    threading.Thread(target=abrir_navegador_cuando_este_listo, daemon=True).start()
    
    # Iniciar servidor Uvicorn en el hilo principal
    uvicorn.run(
        "src.web.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )

