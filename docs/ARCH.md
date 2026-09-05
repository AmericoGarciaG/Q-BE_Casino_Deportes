```markdown
# Q-BE Casino Deportes — Architecture Book (ARCH.md)
**Versión:** 9.0 (Kybern Industrial - Local Full-Stack Web Platform Edition)  
**Estado:** [ALGO-PROTECTED] - Base de Gobierno Sellada (2026-09)  
**Proyecto:** `Q_BE_CD_WEB` (Quantitative Betting Engine — Web Platform)  
**Fuente de Verdad:** Kybern Framework v8.0 / v12.0 + Protocolo Nexus

Este documento define la **Arquitectura Técnica, Topología de Servicios, Capa Web FastAPI, Persistencia SQLite y Contratos Canónicos de Datos (Pydantic V2)** del sistema `Q_BE_CD_WEB`. Cada sección incluye sus etiquetas de justificación vinculante (`[Binding Rationale]`).

---

## 1. TOPOLOGÍA DEL SISTEMA (LOCAL FULL-STACK MONOLITH)

El sistema `Q_BE_CD_WEB` se estructura como un **Monolito Full-Stack Local Gobernado**, operando mediante un servidor asíncrono local que orquesta la ingesta de datos, la persistencia en base de datos, los motores matemáticos y la interfaz reactiva SPA:

```text
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                              ARQUITECTURA DE DOMINIOS Q-BE WEB                         │
 └────────────────────────────────────────────────────────────────────────────────────────┘

    [ SU NAVEGADOR WEB (Cliente SPA Reactivo) — http://localhost:8000 ]
     • Vista 1: Hub de Ligas (Premier, Liga MX ⭐, Champions, LaLiga...)
     • Vista 2: Split-View (Tabla 18 clubes FotMob a la izquierda | Cartelera Checkboxes a la derecha)
     • Vista 3: Dashboard Ejecutivo (KPIs Macro y Boletos Split calculados)
     • Vista 4: Centro de Mando Táctico & Auditoría de Descartes
     • Vistas 5+: Radiografías Forenses Individuales (Opta xG & Tesis Q-BE)
                       │                              ▲
                       │ (Peticiones REST en JSON)    │ (Respuestas en Tiempo Real)
                       ▼                              │
    [ SERVIDOR BACKEND LOCAL (FastAPI + Uvicorn) — src/web/ ]
     ├── Router de Ligas y Cartelera (`/api/leagues`, `/api/fixtures`)
     ├── Router de Portafolio y Despacho (`/api/portfolio/generate`)
     └── Router de Exportación de Documentos (`/api/portfolio/export-pdf`)
                       │                              ▲
                       │                              │
                       ▼                              │
    [ CAPA DE SERVICIOS E INGESTA (src/ingestion/) ]  │
     • FotMob Provider API (Tabla 18 clubes, xG Opta, Forma, Fixtures)
     • Caliente Scraper / OCR Engine (Momios 1X2 + PA)
     • Gemini 3.6 Flash (Sensor Auditor y Redactor Dinámico de Tesis)
                       │                              │
                       ▼                              │
    [ MOTOR MATEMÁTICO PURO (src/core/) — 100% DETERMINISTA ]
     • Triage ➔ Sanitizer ➔ κ-Decay ➔ FCF/E_att ➔ Poisson 6x6 ➔ θ* ➔ Triple Candado ➔ Kelly
                       │                              │
                       ▼                              │
    [ BASE DE DATOS LOCAL (SQLite: data/qbe_database.db) & AUDITOR (The Shield) ]
```

### 1.1 Reglas de Frontera Modular (Protocolo Nexus)
1. **Aislamiento de I/O en `src/core/`:** Los submódulos matemáticos tienen terminantemente prohibido realizar llamadas de red, accesos a base de datos, lectura de disco o depender de variables mutables. Son **funciones puras** (`Input` $\rightarrow$ `Output`).
2. **Soberanía del Contrato Pydantic:** Ningún dato se transfiere entre módulos en forma de diccionarios (`dict`) no tipados. Toda transferencia de estado se realiza mediante instancias de modelos Pydantic V2 validadas.
3. **Inversión Neuro-Simbólica de Carga:** La recolección de hechos numéricos masivos se delega a APIs REST estructuradas (FotMob Opta) con cero costo y cero alucinaciones. Los modelos generativos (Gemini 3.6 Flash) se reservan exclusivamente para auditoría cualitativa de noticias y redacción fluida de la Tesis Q-BE.
4. **Arquitectura Híbrida de Presentación con Fallback Seguro:** El generador narrativo en `src/reporting/narrative.py` invoca primariamente a Gemini API para redactar la tesis en 4 viñetas ricas; ante fallos de conectividad o límites de cuota, degrada automáticamente al generador paramétrico determinista (Mad-Libs) sin interrumpir el pipeline.

---

### [ARCH-1.3.1] Rueda de Inferencia Gemini y Rotador de Llaves Multi-Proyecto [ARCH-PILLAR]

* **Propósito:** Garantizar alta disponibilidad en la auditoría fáctica y redacción narrativa mediante un pool circular de API Keys de Google AI Studio, mitigando límites de frecuencia (15 RPM / 1,500 RPD por proyecto) sin interrupciones.
* **Convención Canónica en `.env`:**
  - `Gemini_API_4_QBE_001`, `Gemini_API_4_QBE_002`, `Gemini_API_4_QBE_003` ... `Gemini_API_4_QBE_NNN`.
  - El sistema auto-descubre dinámicamente todas las llaves que coincidan con este patrón indexado.
* **Máquina de Estados de Llaves (In-Memory Key States):**
  - `KEY_STATUS_OK = "OK"`: Llave activa y lista para operar.
  - `KEY_STATUS_COOLDOWN = "COOLDOWN"`: Llave saturada temporalmente (HTTP 429 / `RESOURCE_EXHAUSTED` / `quota`). Se pone en pausa por el tiempo indicado en `retry_delay` (mínimo 60s) y se rehabilita al expirar.
  - `KEY_STATUS_BANNED = "BANNED"`: Llave inválida o revocada (HTTP 400 / 401 / 403 / `API_KEY_INVALID`). Se inhabilita por 24 horas.
* **Algoritmo de Rotación y Reintento:**
  - Mantiene un puntero circular `_CURRENT_KEY_INDEX`.
  - Ante un error 429, marca la llave en `COOLDOWN`, emite alerta en consola (`[ROTATION-ALERT]`), avanza a la siguiente llave disponible con estado `OK` y reintenta de forma transparente.

---

### [ARCH-1.3.2] Modelo Gemini Canónico Inmutable (`gemini-3.6-flash`) [ARCH-PILLAR] [ANTI-BUG]

* **Fijación Canónica:** Se sella formalmente que `gemini-3.6-flash` es el modelo único canónico de producción para inferencia fáctica y redacción de tesis. Queda estrictamente prohibido usar nombres de modelos como cadenas de texto sueltas en el código.
* **Fuente Única de Verdad:**
  ```python
  DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
  ```
  Exportada desde `src/ingestion/providers/gemini_sensor.py` y consumida obligatoriamente por cualquier módulo cliente.

---

### [ARCH-1.3.3] Gestor Contable Local de Cuotas y Circuit Breaker [ARCH-PILLAR]

* **Mecanismo:** Cada invocación a Gemini pasa por un filtro de pre-vuelo en `src/ingestion/quota_manager.py`.
* **Estados del Circuit Breaker:**
  - `CLOSED` (Verde): Peticiones normales permitidas.
  - `OPEN` (Rojo): Llave congelada. Lee el campo `retry_delay.seconds` enviado por Google o asigna pausa preventiva. El despachador salta la llave en 0 ms sin invocar la red.
  - `HALF-OPEN` (Amarillo): Sonda de reactivación tras expirar el temporizador.
* **Persistencia:** Estado preservado en `data/.api_quotas_state.json`.

---

### [ARCH-1.4.0] Inversión de Carga Neuro-Simbólica (FotMob Primary Sensor) [ARCH-PILLAR]

* **Sensor Primario Estructurado (FotMob / Opta Data):** FotMob API (`https://www.fotmob.com/api/leagues?id=262`) es el sensor primario oficial de hechos deportivos (xG real, xGA, tabla general completa de 18 clubes, forma de 5 partidos y fixtures de la jornada activa).
* **Cero Consumo de Tokens:** La ingestión de estadísticas y marcadores opera con costo $0.00 USD y latencia $< 200\text{ ms}$.
* **Gemini como Auditor Especializado:** La IA se reserva para contrastar noticias de última hora y redactar la Tesis Q-BE en 4 viñetas enriquecidas con los datos de FotMob.

---

### [ARCH-1.5.0] Persistencia Local en Base de Datos SQLite [ARCH-PILLAR]

* **Motor:** SQLAlchemy 2.0 conectado a `sqlite:///data/qbe_database.db` con `check_same_thread=False`.
* **Ciclo Lifespan de Inicio (FastAPI):**
  1. Ejecutar `Base.metadata.create_all()`.
  2. Ejecutar Seeder (`src/storage/seeder.py`): inicializar Liga MX (ID: 262) si no existe.
  3. Ejecutar Sincronización de Arranque (`src/storage/sync_service.py`): consultar FotMob, validar y persistir la tabla general completa de 18 clubes y la cartelera activa.

### [ARCH-1.5.1] Catálogo de Equipos y Escudos en Base de Datos Local (`teams`) [ARCH-PILLAR]

* **Prohibición de Diccionarios de IDs Estáticos:** Queda estrictamente prohibido mantener listas manuales o adivinadas de `fotmob_id` en el código. La persistencia en SQLite de la tabla `teams` y de los snapshots de tabla debe alimentarse dinámicamente del campo `id` devuelto por el payload oficial de FotMob.
* **CDN de Escudos Oficiales:** Todo escudo se obtiene de:
  `https://images.fotmob.com/image_resources/logo/teamlogo/{fotmob_id}.png`.

---

### [ARCH-1.6.0] Arquitectura del Live Board Reactivo y Sincronización SQLite [ARCH-PILLAR]

* **Propósito:** Desacoplar la ingesta deportiva viva de la compilación de reportes, permitiendo que la interfaz SPA explore ligas, consulte tablas completas de 18 clubes en FotMob y seleccione partidos de forma interactiva persistiendo el estado en SQLite local.
* **Flujo de Servicios y Endpoints:**
  1. `GET /api/leagues`: Consulta la tabla `leagues` en SQLite y retorna las competencias activas registradas por el seeder.
  2. `GET /api/leagues/{id}/live-board`:
     - Consulta FotMob API (League ID: 262 para Liga MX) para obtener la tabla oficial de 18 clubes y métricas Opta ($xG, xGA, xPTS$).
     - Consulta FotMob / Scraper para obtener la cartelera activa con momios decimales 1X2 y Pago Anticipado.
     - Persiste snapshots inmutables en SQLite (`standings_snapshots` y `fixtures_snapshots`).
     - Retorna el contrato canónico `LiveBoardOut`.

---

### [ARCH-1.6.1] Política de Presentación Centrada en el Inversionista (Zero Technical Leakage) [ARCH-PILLAR] [UX-MANDATE]

* **Axioma de Pulcritud Institucional:** Queda estrictamente prohibido exponer nombres de motores de base de datos (`SQLite`), métricas de consumo de modelos (`0 Tokens LLM`, `Prompt 01`) o terminología interna de ingeniería (`P.I.R. Sensor`) en las vistas visuales destinadas al usuario final.
* **Voz de Socio Financiero:** Todo encabezado, badge o tarjeta debe comunicar valor operativo, liquidez y certidumbre deportiva en lenguaje didáctico accesible.
* **Estructura Canónica de Cartelera (`LiveBoardOut.fixtures`):** Los partidos de la jornada activa deben estructurarse agrupados cronológicamente por fecha de evento (`"Hoy / Viernes"`, `"Sábado"`, `"Domingo"`, `"Pospuestos"`), con cuotas 1X2 normalizadas y un único identificador de selección por tarjeta.

### [ARCH-1.6.2] Ventana Operativa de Cartelera y Ciclo de Vida de Cuotas [ARCH-PILLAR] [BIZ-LOGIC]

* **Ventana Centrada en la Jornada (Jornada-Centric Window):** Queda prohibido el filtrado estricto por mes calendario. La cartelera extrae todos los partidos asignados a la jornada en disputa (`round_num == current_round`), resolviendo automáticamente fechas que cruzan fin de mes.
* **Segmentación de Fixtures:**
  1. `VENTANA_ACTIVA` (Próximos $\le 7$ días): Partidos habilitados con checkbox de selección para cálculo de cartera.
  2. `VENTANA_POSPUESTA` (Fechas $> 14$ días): Partidos reprogramados agrupados bajo la sección `📅 PARTIDOS REPROGRAMADOS`, con checkbox deshabilitado (`disabled`) y badge `⏳ Fecha Lejana`.
* **Ciclo de Vida de Cuotas (Disponibilidad de Momios):**
  - Si el partido tiene cuotas publicadas en Caliente.mx $\implies$ se registran momios decimales 1X2 reales y `pago_anticipado = True/False`.
  - Si Caliente.mx aún no publica cuotas $\implies$ `momios = null`, `disponible = False`. La interfaz muestra `L — | E — | V —  ⏳ Cuotas Pendientes` y deshabilita el checkbox de selección con un tooltip explicativo.


---

## 2. ESTRUCTURA LIMPIA DE MÓDULOS Y MAPEO DE CÓDIGO

```text
Q_BE_CD_WEB/
├── run_app.py                      # Entrypoint: Uvicorn + Auto-Browser Launch
├── requirements.txt                # Dependencias oficiales selladas
├── .env                            # Configuración local y llaves
│
├── docs/                           # BASE DE GOBIERNO (Única Fuente de Verdad)
│   ├── ARCH.md                     # Arquitectura Técnica y Contratos REST
│   ├── DESIGN.md                   # Tokens Visuales y Geometría DOM
│   ├── GOVERNANCE.md               # Metodología Kybern, Axioma Cero Mocks y Tríada
│   └── LOGIC.md                    # Grafo IPO Matemático [LN-QBE-001 a 090]
│
├── src/                            # CÓDIGO FUENTE MODULAR
│   ├── web/                        # Capa Web FastAPI
│   │   ├── app.py                  # Instancia FastAPI con Lifespan
│   │   ├── routes/
│   │   │   ├── leagues.py          # GET /api/leagues, /api/leagues/{id}/live-board
│   │   │   ├── portfolio.py        # POST /api/portfolio/generate
│   │   │   └── export.py           # GET /api/portfolio/{id}/pdf
│   │   ├── static/                 # Assets de la SPA Reactiva
│   │   │   ├── css/theme.css       # Estilos Dark Mode Fintech
│   │   │   └── js/app.js           # Lógica SPA con Fetch API
│   │   └── templates/
│   │       └── index.html          # Shell SPA reactivo multipantalla
│   │
│   ├── storage/                    # Persistencia y Base de Datos Local
│   │   ├── database.py             # Conexión SQLAlchemy SQLite
│   │   ├── models.py               # Tablas: League, StandingSnapshot, FixtureSnapshot, PortfolioRecord
│   │   ├── repository.py           # Operaciones CRUD tipadas
│   │   ├── seeder.py               # Precarga de Ligas Oficiales (Liga MX)
│   │   └── sync_service.py         # Sincronización en arranque FotMob -> DB
│   │
│   ├── ingestion/                  # Capa de Ingesta y Sensores de Mercado
│   │   ├── normalizer.py           # Normalizador difuso de clubes (18 Liga MX + Internacionales)
│   │   ├── caliente_scraper.py     # Extracción headless de cuotas Caliente.mx
│   │   ├── ocr_parser.py           # Extracción OCR desde capturas
│   │   ├── quota_manager.py        # Gestor de Cuotas y Circuit Breaker de Gemini
│   │   └── providers/
│   │       ├── base_provider.py    # Interfaz canónica abstracta
│   │       ├── fotmob_provider.py  # Sensor primario Opta (Tabla 18 clubes, xG, fixtures)
│   │       └── gemini_sensor.py    # Sensor auditor y redactor de Tesis (Gemini 3.6 Flash)
│   │
│   ├── core/                       # Motores Matemáticos Deterministas [ALGO-PROTECTED]
│   │   ├── catalog.py              # [LN-QBE-060] Catálogo canónico inmutable de estrategias
│   │   ├── triage.py               # [LN-QBE-005] Triaje determinista de cuotas 1X2
│   │   ├── sanitizer.py            # [LN-QBE-010] Aduana de sanidad y anclaje
│   │   ├── temporal.py             # [LN-QBE-020] κ-Decay H2H (180d)
│   │   ├── metrics.py              # [LN-QBE-030] FCF y Eficiencia Atacante E_att
│   │   ├── poisson.py              # [LN-QBE-040] Poisson Bivariado 6x6 calibrado con xG Opta
│   │   ├── breakeven.py            # [LN-QBE-050] Breakeven Dinámico Continuo (θ*)
│   │   ├── evaluator.py            # [LN-QBE-060] Evaluador Booleano y Triple Candado Fáctico
│   │   ├── portfolio.py            # [LN-QBE-070] Router de Utilidad Pura, Kelly y Dutching
│   │   └── auditor.py              # [LN-QBE-090] Release Gate (The Shield — 8 Invarianzas)
│   │
│   ├── models/                     # Contratos Pydantic V2
│   │   ├── web_schemas.py          # Esquemas REST para la Web App
│   │   ├── raw_input.py            # Ingesta cruda y tabla maestra
│   │   ├── analytics.py            # Métricas estocásticas y probabilidades
│   │   ├── decision.py             # Órdenes de ejecución y cartera
│   │   └── consolidated.py         # Payload consolidado maestro
│   │
│   └── reporting/                  # Generación de Reportes
│       ├── narrative.py            # Tesis Dual (Gemini Dinámico + Fallback Mad-Libs)
│       ├── compiler.py             # [LN-QBE-080] Playwright Chromium PDF Engine
│       └── templates/
│           └── master_report.html  # Plantilla A4 oficial con Screen Switcher
│
├── tests/                          # THE SHIELD (Escudo de Calidad)
│   ├── conftest.py                 # Fixtures oficiales globales
│   └── shield/                     # Twin-Tests inmutables (abstractos y concretos)
│
└── data/                           # ALMACENAMIENTO PERSISTENTE
    ├── input/                      # Archivos de entrada cruda (.gitkeep)
    ├── output/                     # PDFs generados y datos consolidados (.gitkeep)
    └── qbe_database.db             # Base de datos SQLite local
```

---

## 3. CONTRATOS CANÓNICOS DE DATOS (PYDANTIC V2)

### 3.1 Contratos de la API Web (`src/models/web_schemas.py`)

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class LeagueOut(BaseModel):
    id: int
    name: str
    country: str
    flag: str
    fotmob_id: int
    is_active: bool

class StandingRowOut(BaseModel):
    pos: int
    equipo: str
    escudo_url: Optional[str] = None
    pj: int
    pg: int
    pe: int
    pp: int
    gf: int
    gc: int
    dif: int
    puntos: int
    forma: List[str] # ["G", "E", "P", ...]
    xg: Optional[float] = None
    xga: Optional[float] = None
    proximo_rival: Optional[str] = None

class Odds1X2(BaseModel):
    L: float = Field(gt=1.0)
    E: float = Field(gt=1.0)
    V: float = Field(gt=1.0)
    pago_anticipado: bool = True

class MatchFixtureOut(BaseModel):
    id_partido: str
    local: str
    visitante: str
    horario: str
    momios: Odds1X2
    es_viable_triaje: bool = True
    motivo_triaje: Optional[str] = None

class LiveBoardOut(BaseModel):
    league_id: int
    league_name: str
    jornada: str
    fechas: str
    standings: List[StandingRowOut]
    fixtures: List[MatchFixtureOut]

class GeneratePortfolioRequest(BaseModel):
    league_id: int
    selected_match_ids: List[str]
    bankroll: float = Field(default=200.0, ge=10.0)
    mode: str = Field(default="BANKROLL", pattern="^(BANKROLL|VAQUITA)$")
```

---

### 3.2 Contratos de Entrada Cruda y Tabla Maestra (`src/models/raw_input.py`)

```python
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class MasterTablePosition(BaseModel):
    model_config = ConfigDict(extra="ignore")
    pos: int = Field(ge=1, le=18)
    equipo: str
    puntos: int = Field(ge=0)
    pj: int = Field(ge=0)
    gf: int = Field(ge=0)
    gc: int = Field(ge=0)
    dif: int
    pts_por_partido: float = Field(ge=0.0)

class MasterTableSnapshot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    jornada_concluida: Optional[int] = None
    posiciones: List[MasterTablePosition] = Field(default_factory=list)

class OddsSet(BaseModel):
    L: float = Field(gt=1.0)
    E: float = Field(gt=1.0)
    V: float = Field(gt=1.0)
    disponible: bool = True

class H2HMatchRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")
    num: Optional[int] = None
    fecha: str
    dias_transcurridos: float = Field(ge=0.0)
    local_real: str
    visitante_real: str
    marcador: str
    resultado_qbe: Optional[str] = None

class Form10PRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")
    gf: int = Field(ge=0)
    gc: int = Field(ge=0)
    sot: float = Field(ge=0.0)
    sota: float = Field(ge=0.0)
    poss_pct: float = Field(ge=0.0, le=100.0)
    promedio_gf: float = Field(ge=0.0)
    promedio_gc: float = Field(ge=0.0)
    promedio_sot: float = Field(ge=0.0)
    promedio_sota: float = Field(ge=0.0)
    promedio_poss: float = Field(ge=0.0, le=100.0)
```

---

### 3.3 Contratos de Órdenes y Portafolio (`src/models/decision.py`)

```python
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class StrategySelection(BaseModel):
    model_config = ConfigDict(frozen=True)
    codigo: str
    nombre_oficial: str
    descripcion_ejecutiva: str
    linea_promocional: str

class TicketOrder(BaseModel):
    model_config = ConfigDict(frozen=True)
    seleccion: str
    momio: float = Field(ge=0.0)
    monto_mxn: float = Field(ge=0.0)

class MatchTickets(BaseModel):
    model_config = ConfigDict(frozen=True)
    inversion_partido_A_i: float = Field(ge=0.0)
    boleto_1_seguro: TicketOrder
    boleto_2_ganancia: TicketOrder

class Projections(BaseModel):
    model_config = ConfigDict(frozen=True)
    ganancia_neta_principal_mxn: float
    roi_principal_porcentaje: float
    freeroll_doble_ganancia_mxn: float = 0.0
    freeroll_roi_porcentaje: float = 0.0
    resultado_tablas_mxn: float
    perdida_maxima_posible_mxn: float

class MatchExecutionOrder(BaseModel):
    model_config = ConfigDict(frozen=True)
    id_partido: str
    partido: str
    horario_evento: str
    estrategia_seleccionada: StrategySelection
    boletos: MatchTickets
    proyecciones: Projections
    cashout_targets: Dict[str, Any]

class PortfolioControl(BaseModel):
    model_config = ConfigDict(frozen=True)
    modalidad: Literal["BANKROLL", "VAQUITA"]
    total_partidos_core_aprobados: int
    capital_total_core_mxn: float
    probabilidad_ruina_total_porcentaje: float
    blindaje_global_preservacion_porcentaje: float
    desglose_vaquita: Dict[str, Any]
    desglose_bankroll: Dict[str, Any]

class PortfolioBalance(BaseModel):
    model_config = ConfigDict(frozen=True)
    capital_total_comprometido_mxn: float
    ganancia_neta_esperada_jornada_mxn: float
    roi_global_esperado_porcentaje: float

class PortfolioExecutionPlan(BaseModel):
    model_config = ConfigDict(frozen=True)
    control_portafolio: PortfolioControl
    ordenes_ejecucion_partidos: List[MatchExecutionOrder]
    modulo_satelite_asimetrico: Dict[str, Any]
    balance_global_portafolio: PortfolioBalance
```

---

## 4. ENDPOINTS REST DE LA APLICACIÓN WEB

```text
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                         CONTRATOS DE ENDPOINTS REST (FASTAPI)                          │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ 1. `GET /api/leagues`                                                                  │
 │    ➔ Retorna catálogo de ligas activas (Liga MX, Premier, Champions, LaLiga...).       │
 │                                                                                        │
 │ 2. `GET /api/leagues/{id}/live-board`                                                  │
 │    ➔ Consulta FotMob y DB; retorna la tabla oficial de 18 clubes (con puntos, GF/GC,    │
 │      forma reciente W/D/L y xG acumulado) y la cartelera con momios 1X2 de Caliente.  │
 │                                                                                        │
 │ 3. `POST /api/portfolio/generate`                                                      │
 │    ➔ Recibe { league_id, selected_match_ids, bankroll, mode }.                         │
 │    ➔ Filtra por triaje, ejecuta Poisson 6x6 con xG Opta, calcula Kelly y Dutching,    │
 │      invoca Gemini 3.6 para la Tesis Q-BE en 4 bullets y audita con The Shield.       │
 │    ➔ Retorna: `ConsolidatedPayload` con las órdenes listas para colocar en casino.     │
 │                                                                                        │
 │ 4. `GET /api/portfolio/{portfolio_id}/pdf`                                            │
 │    ➔ Compila y descarga el PDF institucional A4 oficial generado por Playwright.      │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. REGLAS DE RESILIENCIA Y MANEJO DE EXCEPCIONES

1. **Safe Zero Divisors (`[ANTI-BUG]`):** Toda división (ej. $1.0 / O$, ratios $SoT / (SoT + SoTA)$) incorpora offset $\epsilon > 0$ o verificación previa (`if denom <= 0: return fallback`).
2. **Invarianza de Clamps (`[ALGO-PROTECTED]`):** Todo multiplicador o factor sintético ($FCF, E_{\text{att}}, \Omega_{\text{perf}}, \theta^*$) debe pasar por funciones `np.clip` o `min/max` antes de ingresar a los modelos de Poisson o Kelly.
3. **Audit Hard-Stop (`[GOVERNANCE]`):** Si `auditor.py` detecta una violación a las 8 Pruebas del Shield, el pipeline lanza `ShieldInvariantException`, abortando la emisión de boletos y la compilación del PDF de forma atómica.
4. **Zero-Mock Policy en Runtime (`[GOVERNANCE-01]`):** Queda prohibida la fabricación de partidos o fechas H2H falsas ante caídas de red. Si una fuente falla, el partido se declara en `CUARENTENA` y se preserva el capital en $0.00 MXN.

---
**BASE DE GOBIERNO SELLADA BAJO EL KYBERN FRAMEWORK v8.0 / v12.0 — ARQUITECTURA TÉCNICA INMUTABLE.**
```