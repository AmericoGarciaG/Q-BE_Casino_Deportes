# 🏛️ Q-BE CASINO DEPORTES (`Q_BE_CD_WEB`)
**Quantitative Betting Engine — Web Platform Edition**
**Kybern Framework v8.0 / v12.0**

## 📌 Descripción General
`Q_BE_CD_WEB` es el motor cuantitativo de apuestas deportivas de nivel industrial diseñado para procesar la Liga MX y ligas internacionales, aplicando modelos estocásticos (Poisson Bivariado 6x6 calibrado con xG), triaje determinista de cuotas 1X2, aduana de sanidad y anclaje, y distribución óptima de capital mediante Dutching y el Criterio de Kelly.

## 🚀 Guía de Arranque Rápido

### 1. Requisitos Previos
- Python 3.11+
- Virtual Environment (`.venv`)

### 2. Instalación
```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Bash / Mac / Linux:
source .venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Instalar navegador Playwright para reportes PDF
playwright install chromium
```

### 3. Ejecución Autónomas (Bootstrap)
```bash
python run_app.py
```
Al ejecutar `run_app.py`, el servidor levantará FastAPI en `http://127.0.0.1:8000/`, creará la base de datos SQLite en `data/qbe_database.db`, ejecutará el seeder con la Liga MX (ID 262), sincronizará la tabla de posiciones y cartelera de FotMob y abrirá la plataforma en tu navegador.

## 🏛️ Gobernanza e Información
Consulte la carpeta `docs/` para revisar la arquitectura del sistema:
- `docs/ARCH.md`: Topología de componentes y arquitectura Nexus.
- `docs/DESIGN.md`: Sistema de diseño Dark Mode Fintech.
- `docs/GOVERNANCE.md`: Marco de gobierno Kybern y The Shield.
- `docs/LOGIC.md`: Documentación de motores cuantitativos.
