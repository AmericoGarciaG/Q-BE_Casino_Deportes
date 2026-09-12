import os
import sys
import io

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import webbrowser
import threading
import time
import uvicorn
from pathlib import Path


# Añadir raíz a sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

def abrir_navegador(url: str):
    time.sleep(1.5)
    print(f"[Q-BE] Abriendo navegador en: {url}")
    webbrowser.open(url)


def main():
    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SERVER_PORT", "8000"))
    url = f"http://{host}:{port}"
    
    # Lanzar hilo para abrir navegador
    threading.Thread(target=abrir_navegador, args=(url,), daemon=True).start()
    
    # Arrancar Uvicorn
    uvicorn.run("src.web.app:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
