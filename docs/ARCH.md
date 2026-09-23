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
     • Vista 1: Hub de Ligas (Liga MX ⭐, Premier, Champions, LaLiga...)
     • Vista 2: Split-View (Tabla 18 clubes oficial | Cartelera en 4 Niveles)
     • Vista 3: Cartera Cuantitativa (Dashboard Ejecutivo: Macro KPIs, Boletos Split, PDF y Descartes)
     • Vista 5 (Backlog): Radiografía Forense Interactiva (Matriz 6x6, Edge y CashOut)
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

### [ARCH-1.3.4] GeminiCognitiveGateway y Ledger Contable de Inferencia [ARCH-PILLAR]

* **Axioma de Encajonamiento Cognitivo:** Queda terminantemente prohibido que cualquier módulo cliente (`narrative.py`, `admin.py`, scripts de auditoría) instancie clientes HTTP directos o librerías de Google Gemini. Toda interacción neuro-simbólica debe canalizarse a través de `src/services/gemini_gateway.py`.
* **Alcance Autorizado de Producción:**
  1. `generate_thesis()`: Redacción didáctica on-demand en 4 viñetas [LN-QBE-014].
  2. `curate_catalog()`: Prospección agéntica HITL de ligas y clubes [ARCH-1.5.2].
  3. `audit_shadow()`: Conciliación matemática externa con Gemini Flash (Script de auditoría).
* **Deprecación de Sensores Ineficientes:** Se extirpa el sensor genérico de búsqueda de bajas (`gemini_search_sensor.py`) del pipeline activo.
* **Pool Circular y Máquina de Estados:**
  - Auto-descubrimiento dinámico de llaves: `Gemini_API_4_QBE_*` en `.env`.
  - Estados: `OK`, `COOLDOWN` (pausa automática ante HTTP 429), `BANNED`.
* **Telemetría y Contabilidad de Tokens:** Cada llamada registra `prompt_tokens`, `candidates_tokens`, `latency_ms` y `estimated_cost_usd` en la tabla SQLite `llm_token_ledger`.

---

### [ARCH-1.4.0] Inversión de Carga Neuro-Simbólica (FotMob Primary Sensor) [ARCH-PILLAR]

* **Sensor Primario Estructurado (FotMob / Opta Data):** FotMob API (`https://www.fotmob.com/api/leagues?id=262`) es el sensor primario oficial de hechos deportivos (xG real, xGA, tabla general completa de 18 clubes, forma de 5 partidos y fixtures de la jornada activa).
* **Cero Consumo de Tokens:** La ingestión de estadísticas y marcadores opera con costo $0.00 USD y latencia $< 200\text{ ms}$.
* **Gemini como Auditor Especializado:** La IA se reserva para contrastar noticias de última hora y redactar la Tesis Q-BE en 4 viñetas enriquecidas con los datos de FotMob.

---

### [ARCH-1.4.1] Resiliencia Defensiva del Scraper de Mercado [ARCH-PILLAR] [ANTI-BUG]

* **Cabeceras y Evasión Anti-Bloqueo:** Toda llamada HTTP a interfaces de mercado (Caliente.mx u operadores afines) debe utilizar cabeceras de emulación de navegador de usuario real (`User-Agent` moderno, `Accept`, `Referer` legítimo) y un tiempo de espera explícito (`timeout` determinista de entre 8.0s y 15.0s).
* **Degradación Controlada:** Ante anomalías de red o respuestas no conformes (HTTP 403, 500 o estructuras HTML incompletas), el scraper tiene prohibido bloquear el hilo de ejecución; debe capturar la contingencia de forma aislada y reportar el estado para activación de cuarentena (`QBE-00`).

---

### [ARCH-1.4.2] Pipeline de Ingesta Soberana de Tabla de Posiciones (Liga MX FMF) [ARCH-PILLAR] [GOVERNANCE-01]

* **Fuente de Verdad Soberana:** La única fuente fáctica autorizada para nutrir la tabla de posiciones de la Liga MX (ID: 262) es la Federación Mexicana de Fútbol a través de `https://ligamx.net/cancha/tablas/tablaGeneralClasificacion/`.
* **Erradicación de Fallbacks Mockeados:** Queda terminantemente prohibido el uso de constantes con listas de clubes y puntos predefinidos (`LIGA_MX_CLUBS_DYNAMIC_FALLBACK`). Todo dato de tabla debe emerger de la red oficial viva o del snapshot certificado en SQLite.
* **Invalidación de Caché por Cierre de Jornada (Matchday Rollover):**
  - Cuando el centinela `MatchdayState` detecta el avance de la jornada activa ($N \rightarrow N+1$), invalida de forma inmediata el `StandingSnapshot` previo en SQLite.
  - Esto obliga al sistema a ejecutar la ingesta fresca de la tabla general para reflejar los ascensos, descensos y puntos de los partidos recién concluidos.

### [ARCH-1.4.3] Motor de Extracción Focalizada de Cuotas Caliente.mx [ARCH-PILLAR] [ANTI-BUG]

* **Axioma de Búsqueda Acotada por Slate:** Queda terminantemente prohibido el raspado ciego o indiscriminado de eventos en Caliente.mx. El scraper recibe como parámetro de entrada obligatorio el *Master Slate* de la jornada activa certificado por `ligamx.net`.
* **Filtro de Pertenencia:** El motor busca única y exclusivamente las cuotas 1X2 y la cláusula de Pago Anticipado (`2 Goles de Ventaja`) para los pares canónicos `(local, visitante)` pertenecientes a dicho Slate. Todo evento de jornadas futuras, copas o partidos adelantados que no forme parte de la ventana en disputa se descarta en memoria sin procesar.

### [ARCH-1.4.4] Ingesta Estructurada de Forma (5P) vía FotMob Next.js (__NEXT_DATA__) [ARCH-PILLAR]

* **Identificador de Competición:** La Liga MX se consulta formalmente bajo el ID `230` en FotMob.
* **Extracción Soberana sin Dependencia de APIs Deprecadas:** Ante la baja de las rutas REST públicas `/api/leagues`, el sistema extrae el árbol de datos pre-renderizado por Next.js incrustado en la etiqueta `<script id="__NEXT_DATA__">` de `https://www.fotmob.com/es-419/leagues/230/table/liga-mx`.
* **Atributos Capturados:** Array cronológico de los últimos 5 partidos (`W/D/L` $\implies$ `G/E/P`) y el objeto `nextMatch` para deducción de rival inmediato.

### [ARCH-1.4.5] Robustez de Parsers DOM y Expresiones Multilínea [ANTI-BUG]

* **Tolerancia a Saltos de Línea en Marcadores:** Los scrapers de resultados en vivo deben emplear patrones de expresiones regulares multilínea capaces de resolver goles separados por retornos de carro o espacios en el DOM (`(?<!\d)(\d+)\s*\n*\s*[-–]\s*\n*\s*(\d+)(?!\d)`), impidiendo que marcadores legítimos concluidos se descarten como nulos.

### [ARCH-1.4.5-B] Endpoints Desacoplados de Soberanía y Mercados [ARCH-PILLAR]

1. **Rutas Soberanas (Sin Cuotas):**
   - `GET /api/sovereign/leagues/{id}/matches`:
     Retorna la lista de partidos de la liga indicada con su distribución matemática pura:
     `{ match_id, local, visitante, local_escudo_url, visitante_escudo_url, horario, p_local, p_empate, p_visitante, lambda_home, lambda_away, phi_lead2_home, es_operable }`.
     *Garantía:* CERO campos de cuotas o momios comerciales en el payload.

2. **Rutas de Mercado Casino 1X2:**
   - `GET /api/markets/sportsbook/matches?bookmaker=caliente&league_id=262`:
     Retorna los partidos abiertos con cuotas, contrastados contra la distribución soberana de SQLite:
     `{ match_id, local, visitante, momio_l, momio_e, momio_v, pago_anticipado, gap_local, gap_empate, gap_visitante, es_viable_ev }`.
   - `POST /api/markets/sportsbook/portfolio/generate`:
     Acepta `{ league_id: int, selected_match_ids: List[str], bankroll: float, target_certeza: float }`.
     Despacha la cartera cuantitativa (Dutching $V=0$, Kelly, Trinidad $3^K$, slider de certeza y boletos split).

3. **Rutas de Mercado Pronósticos Deportivos (Progol):**
   - `GET /api/markets/progol/slates/active`:
     Retorna el concurso activo de 14 partidos con venta pública vs. probabilidad soberana y alertas de sesgo.
   - `POST /api/markets/progol/optimize`:
     Acepta `{ slate_id: str, presupuesto_mxn: float }` y retorna `{ combinaciones_totales, costo_total_mxn, matriz_quiniela: List[Dict] }`.

---

### [ARCH-1.5.0] Central Persistence Gateway y Unidad de Trabajo (Unit of Work) [DIRGEN-SEALED] [ARCH-PILLAR]

* **Axioma de Centralización Transaccional:** Queda estrictamente prohibido que cualquier ruta REST, scraper o daemon instancie sesiones directas o ejecute `db.commit()` sin mediación. Toda interacción con `data/qbe_database.db` debe canalizarse a través de `src/storage/gateway.py`.
* **Directivas de Motor Obligatorias (PRAGMAs SQLite):** En cada conexión física, el engine debe forzar mediante event listeners:
  ```sql
  PRAGMA journal_mode = WAL;
  PRAGMA foreign_keys = ON;
  PRAGMA synchronous = NORMAL;
  PRAGMA busy_timeout = 15000;
  ```
* **Segregación Estricta de Contextos:**
  1. `gateway.read_session()`: Contexto de solo lectura para la interfaz FastAPI. Sin bloqueos, con liberación inmediata de recursos y latencia $< 2\text{ ms}$.
  2. `gateway.write_transaction()`: Contexto de escritura atómica para demonios e ingesta. Si ocurre una sola excepción dentro del bloque, se ejecuta `ROLLBACK` total y la base de datos queda intacta.
* **Validación de Integridad en el Arranque:** En la inicialización, el gateway ejecuta `PRAGMA quick_check;`. Si reporta anomalías físicas, aborta con `RuntimeError` impidiendo operar sobre datos corruptos.

### [ARCH-1.5.1] Esquema Relacional 3NF Multi-Torneo — Especificación Canónica de Columnas [ARCH-PILLAR] [DIRGEN-STRICT]

La persistencia abandona el almacenamiento ciego en listas JSON y se estructura en entidades relacionales de **Tercera Forma Normal (3NF)**. Cada tabla se detalla a continuación con sus columnas exactas, claves primarias y foráneas:

#### Tabla: `competitions`
| Columna | Tipo | Restricción | Descripción |
|---|---|---|---|
| `id` | `VARCHAR` | `PK` | ID canónico (`MEX_LIGAMX`, `ENG_PL`, `EUR_UCL`) |
| `name` | `VARCHAR` | `NOT NULL` | Nombre oficial de la competición |
| `country` | `VARCHAR` | `NOT NULL` | País o región de la competición |
| `macro_mu_liga` | `FLOAT` | `NOT NULL` | Parámetro macro $\mu_{\text{liga}}$ (goles/90 promedio de liga) |
| `macro_gamma_home` | `FLOAT` | `NOT NULL` | Ventaja media de local $\bar{\gamma}_{\text{home}}$ |

#### Tabla: `teams`
| Columna | Tipo | Restricción | Descripción |
|---|---|---|---|
| `id` | `VARCHAR` | `PK` | ID canónico slug (ej. `club-america`) |
| `competition_id` | `VARCHAR` | `FK → competitions.id` | Liga a la que pertenece |
| `name` | `VARCHAR` | `NOT NULL` | Nombre completo oficial |
| `short_name` | `VARCHAR` | | Nombre corto o acrónimo |
| `crest_path` | `VARCHAR` | | Ruta local `/static/img/crests/{slug}.png` |

#### Tabla: `seasons`
| Columna | Tipo | Restricción | Descripción |
|---|---|---|---|
| `id` | `VARCHAR` | `PK` | ID único de temporada |
| `competition_id` | `VARCHAR` | `FK → competitions.id` | Liga a la que pertenece |
| `year` | `INTEGER` | `NOT NULL` | Año de inicio de la temporada |
| `name` | `VARCHAR` | `NOT NULL` | Nombre descriptivo (ej. `Apertura 2026`) |

#### Tabla: `matches`
| Columna | Tipo | Restricción | Descripción |
|---|---|---|---|
| `id` | `VARCHAR` | `PK` | ID universal del partido |
| `competition_id` | `VARCHAR` | `FK → competitions.id` | Liga |
| `season_id` | `VARCHAR` | `FK → seasons.id` | Temporada |
| `matchday_num` | `INTEGER` | `NOT NULL` | Número de jornada |
| `kickoff_utc` | `DATETIME` | `NOT NULL` | Fecha/hora UTC de inicio |
| `home_team_id` | `VARCHAR` | `FK → teams.id` | Equipo local |
| `away_team_id` | `VARCHAR` | `FK → teams.id` | Equipo visitante |
| `status` | `VARCHAR` | `NOT NULL` | Estado: `PROGRAMADO`, `EN_CURSO`, `FINALIZADO`, `REPROGRAMADO` |
| `score_home` | `INTEGER` | | Goles local (NULL si no concluido) |
| `score_away` | `INTEGER` | | Goles visitante (NULL si no concluido) |

#### Tabla: `match_telemetry`
| Columna | Tipo | Restricción | Descripción |
|---|---|---|---|
| `match_id` | `VARCHAR` | `PK, FK → matches.id` | Partido al que pertenece |
| `team_id` | `VARCHAR` | `PK, FK → teams.id` | Equipo (permite registro local + visitante) |
| `xg` | `FLOAT` | | Expected Goals ofensivos |
| `xga` | `FLOAT` | | Expected Goals concedidos |
| `sot` | `FLOAT` | | Disparos al arco |
| `sota` | `FLOAT` | | Disparos al arco del rival |
| `possession_pct` | `FLOAT` | | Posesión (%) |
| `fouls` | `INTEGER` | | Faltas cometidas |
| `red_cards` | `INTEGER` | | Tarjetas rojas |

#### Tabla: `sovereign_distributions`
| Columna | Tipo | Restricción | Descripción |
|---|---|---|---|
| `match_id` | `VARCHAR` | `PK, FK → matches.id` | Partido analizado |
| `model_version` | `VARCHAR` | `PK` | Versión del modelo Poisson + calibración |
| `p_local` | `FLOAT` | `NOT NULL` | Probabilidad soberana local |
| `p_empate` | `FLOAT` | `NOT NULL` | Probabilidad soberana empate |
| `p_visitante` | `FLOAT` | `NOT NULL` | Probabilidad soberana visitante |
| `lambda_h` | `FLOAT` | `NOT NULL` | Tasa goles esperados local $\lambda_h$ |
| `lambda_a` | `FLOAT` | `NOT NULL` | Tasa goles esperados visitante $\lambda_a$ |
| `phi_lead2_home` | `FLOAT` | | Prob. ventaja $\ge 2$ goles a favor local (André) |
| `phi_lead2_away` | `FLOAT` | | Prob. ventaja $\ge 2$ goles a favor visitante (André) |
| `epistemic_delta` | `FLOAT` | | Delta epistémico de incertidumbre del modelo |
| `audit_trace_json` | `TEXT` | | JSON de trazabilidad de auditoría completa |
| `created_at` | `DATETIME` | `NOT NULL` | Timestamp UTC de creación del registro |

#### Tablas: `slates` y `slate_items`
**`slates`** — Concurso principal (Progol, quiniela multitorneo):
| Columna | Tipo | Restricción | Descripción |
|---|---|---|---|
| `id` | `VARCHAR` | `PK` | ID único del concurso (ej. `PROGOL-2026-J17`) |
| `name` | `VARCHAR` | `NOT NULL` | Nombre del concurso |
| `competition_id` | `VARCHAR` | `FK → competitions.id` | Liga principal del concurso |
| `matchday_num` | `INTEGER` | `NOT NULL` | Jornada asociada |
| `status` | `VARCHAR` | `NOT NULL` | Estado del concurso: `OPEN`, `CLOSED`, `SETTLED` |
| `created_at` | `DATETIME` | `NOT NULL` | Timestamp de creación |

**`slate_items`** — Partidos incluidos en cada concurso:
| Columna | Tipo | Restricción | Descripción |
|---|---|---|---|
| `id` | `INTEGER` | `PK` | ID autoincremental |
| `slate_id` | `VARCHAR` | `FK → slates.id` | Concurso al que pertenece |
| `match_id` | `VARCHAR` | `FK → matches.id` | Partido incluido |
| `position` | `INTEGER` | `NOT NULL` | Posición en la quiniela (1–N) |

### [ARCH-1.5.2] Persistencia Local en Base de Datos SQLite [ARCH-PILLAR]

* **Motor:** SQLAlchemy 2.0 conectado a `sqlite:///data/qbe_database.db` con `check_same_thread=False`.
* **Ciclo Lifespan de Inicio (FastAPI):**
  1. Ejecutar `Base.metadata.create_all()`.
  2. Ejecutar Seeder (`src/storage/seeder.py`): inicializar Liga MX (ID: 262) si no existe.
  3. Ejecutar Sincronización de Arranque (`src/storage/sync_service.py`): consultar FotMob, validar y persistir la tabla general completa de 18 clubes y la cartelera activa.

### [ARCH-1.5.3] Catálogo de Equipos y Escudos en Base de Datos Local (`teams`) [ARCH-PILLAR] [ANTI-BUG]

* **Prohibición de URLs Vulnerables:** Queda estrictamente prohibido utilizar enlaces directos al CDN de FotMob (`images.fotmob.com`) para el renderizado de escudos en la interfaz, debido al bloqueo sistemático HTTP 403 por políticas de Anti-Hotlinking y a la presencia histórica de IDs cruzados o extintos.
* **Fuente Canónica Primaria (Federación Oficial):** La única fuente oficial fáctica para la extracción de escudos de la Liga MX es el portal de la liga (`https://ligamx.net/`) y su CDN oficial centralizado:
  `https://cldrsrcs.apilmx.com/v1/docs/archdgtl/AfldDrct/logos/{id}/{id}.png`.
* **Persistencia Local Soberana:** La tabla `teams` de SQLite (`data/qbe_database.db`) almacena obligatoriamente la ruta estática servida localmente (`/static/img/crests/{canonical_slug}.png`), garantizando autonomía total e inmunidad ante caídas de red externas.
* **Prohibición de Hotlinks Residuales en Código Fuente:** Queda terminantemente prohibido mantener URLs duras a `images.fotmob.com` o servidores externos no autorizados en datasets de prueba, constantes de ejemplo o fixtures fallback. Todo mock o semilla debe utilizar rutas locales canónicas (`/static/img/crests/{slug}.png`) o Data URIs SVG.

---

### [ARCH-1.5.3] Política de Servido de Activos Visuales y Mitigación Anti-Hotlinking [ARCH-PILLAR] [ANTI-BUG]

* **Aislamiento de Red:** Los navegadores de clientes no deben realizar peticiones GET de imágenes a servidores externos no autorizados (`images.fotmob.com`).
* **Montaje Estático de FastAPI:** La aplicación monta el directorio estático en `/static` (`app.mount("/static", StaticFiles(directory="src/web/static"), name="static")`).
* **Integración en Live Board:** El pipeline de ensamble de `GET /api/leagues/{id}/live-board` debe invocar obligatoriamente el servicio resolutor `[LN-QBE-019]` al poblar `StandingRowOut.escudo_url` y los escudos de la cartelera, sustituyendo cualquier URL de scraping remota por la ruta local canónica (`/static/img/crests/{slug}.png`) o su SVG representativo.
* **Seed Automático:** El arranque de la aplicación (`seeder.py`) debe asegurar que el directorio `src/web/static/img/crests/` contenga los 18 escudos base de la Liga MX precargados.

### [ARCH-1.5.4] Espejeo Físico de Aliases y Axioma Anti-Archivos Fantasma [ARCH-PILLAR] [GOVERNANCE-01]

* **Axioma de Integridad Física de Activos:** Queda estrictamente prohibido crear o persistir archivos de 0 bytes o binarios vacíos (*dummy placeholders*) en `src/web/static/img/crests/` para eludir aserciones de pruebas. Todo archivo `.png` en la bóveda debe poseer un tamaño real $\ge 2,500$ bytes y portar los *magic bytes* válidos (`\x89PNG`).
* **Política de Espejeo Físico (Multi-Slug Mirroring):** Para evitar desalineaciones entre slugs cortos y largos (ej. `guadalajara.png` vs. `chivas-guadalajara.png`, `america.png` vs. `club-america.png`), el sistema materializa copias físicas idénticas para cada alias canónico reconocido. Cualquier solicitud de asset visual debe resolver a un archivo completo e íntegro.

---

### [ARCH-1.5.5] Modelo de Datos Relacional para Aprendizaje Cuantitativo (Puente PM-FACE) [ARCH-PILLAR] [BIZ-LOGIC]

* **Propósito Institucional:** La base de datos SQLite (`data/qbe_database.db`) opera como ledger histórico inmutable para el Motor de Calibración Post-Jornada y Atribución Factorial (`PM-FACE` — Fase 7).
* **Entidades Relacionales Soberanas:**
  1. `MatchdayState`: Registra `league_id`, `matchday_num`, `estado` (`ACTIVA`, `CONCLUIDA`), `last_scraped_at`, total de partidos y partidos finalizados. Opera como centinela de caché para evitar re-evaluaciones desde cero.
  2. `FixtureRecord`: Almacena de forma normalizada cada encuentro con sus atributos estructurados: `id_partido`, `matchday`, `local_id`, `visitante_id`, `fecha_dt`, `estado`, `marcador_local`, `marcador_visitante`, momios $L, E, V$ y cláusula de `pago_anticipado`.
* **Gobernanza de Cierre de Jornada:** Una jornada se declara `CONCLUIDA` cuando el 100% de sus partidos regulares tienen estatus `FINALIZADO` con marcador verificado. Una vez concluida, su registro queda congelado para auditoría de Brier Score y se habilita la transición a la jornada $N+1$.

### [ARCH-1.5.6] Ledger Histórico de Momios y Circunstancias Pre-Partido (Backtesting Bridge) [BIZ-LOGIC] [PM-FACE]

* **Propósito:** Registrar de forma inmutable el snapshot de cuotas de apertura/cierre y el vector de variables de entorno ($Q_{\text{mod}}$, reporte de bajas, clima, racha) antes del silbatazo inicial de cada partido.
* **Función en el Bucle Cerrado:** Almacenar la verdad del mercado pre-partido en SQLite (`portfolio_records` y tablas colindantes) para permitir simulaciones retrospectivas (*backtesting*) y alimentar la futura calibración bayesiana del motor `PM-FACE` (Fase 7).

### [ARCH-1.5.7] Bóveda Incremental de Emblemas de Ligas y Competiciones [ARCH-PILLAR]

* **Aislamiento Local:** El emblema oficial de cada competencia activa se almacena físicamente en disco en `src/web/static/img/leagues/league_{league_id}.png`.
* **Inspección Delta:** El subsistema `asegurar_logo_liga_incremental()` audita el sistema de archivos; si el activo ya existe y tiene un tamaño válido ($> 1\text{ KB}$), se preserva sin invocar la red. Si falta, lo extrae de forma autónoma desde la fuente oficial de la federación o su repositorio certificado.
* **Persistencia Relacional:** La columna `flag` de la tabla `leagues` almacena obligatoriamente la ruta local relativa servida (`/static/img/leagues/league_{id}.png`), prohibiendo enlaces directos externos.

### [ARCH-1.5.8] Parámetros Canónicos de Normalización y Bóveda de Activos [ARCH-PILLAR] [ANTI-BUG]

* **Limpieza Lingüística Determinista (H9):** El normalizador canónico (`[LN-QBE-012]`) aplica obligatoriamente: eliminación estricta de acentos (`strip_accents`), conversión a minúsculas, sustitución de caracteres no-alfanuméricos por espacios (`[^a-z0-9\s]`) y colapso de dobles espacios antes de cualquier comparación.
* **Umbrales de Coincidencia Difusa (H10):** Ante variantes ortográficas de scrapers heterogéneos, se autoriza la equivalencia de identidad si `SequenceMatcher.ratio() >= 0.78` o si la distancia de Levenshtein es $\le 2$ para cadenas de longitud $\ge 4$ caracteres. Si el ratio es inferior, el sistema invoca `NormalizationException`.
* **Aduana de IDs de Imagen FMF (H1):** El diccionario inmutable `LIGAMX_LOGO_ID_MAP` opera como respaldo determinista de resolución cuando el servidor oficial de la federación emite etiquetas `<img>` con atributo `alt` vacío o indefinido en el carrusel de marcadores.
* **Umbrales Físicos de Bóveda y Espejeo (H13, H14):** Todo escudo de club guardado localmente debe verificar `size >= 3000` bytes y cabecera PNG válida (`\x89PNG`). Todo emblema de torneo debe verificar `size >= 1000` bytes. Durante el commit de curación HITL, se ejecuta el copiado físico obligatorio (`shutil.copyfile`) hacia todos los aliases del club para garantizar integridad multi-slug inmediata.

### [ARCH-1.5.9] Módulo Centinela Pre-Kickoff: Sharp Money & Semantic Shock [BACKLOG]
* **Propósito:** Monitorear fluctuaciones violentas de cuotas ($t \le 30'$ previo al inicio). Si el mercado se mueve en reversa por apuestas de sindicatos, dispara a Gemini con Search Grounding focalizado (prensa y redes) para explicar el motivo táctico, habilitando CashOut preventivo o arbitraje de cobertura.

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
  - Si el partido tiene cuotas publicadas en Caliente.mx $\implies$ se registran momios decimales 1X2 reales y `* **Máquina de Estados del Fixture (`MatchFixtureOut.estado`):**
  1. `PROGRAMADO`: Partido futuro dentro de la ventana activa. Posee momios 1X2 válidos y checkbox de selección habilitado (`disponible = True`).
  2. `EN_CURSO`: Partido en disputa en tiempo real. Expone `marcador_actual` dinámico y `minuto_juego` (ej. `"45'"`, `"Medio Tiempo"`). Checkbox deshabilitado para apuestas pre-partido.
  3. `FINALIZADO`: Partido concluido. Expone `marcador_actual` oficial definitivo. Checkbox deshabilitado (`disponible = False`). Queda **estrictamente vetado** de ingresar en `selected_match_ids` hacia `/api/portfolio/generate`.
  4. `REPROGRAMADO`: Partido reprogramado por la federación.
* **Criterio de Reprogramados Operables vs. Fecha Lejana [BIZ-LOGIC] (H5):**
  - Todo partido extraído de la sección de reprogramados de la federación lleva el estado `REPROGRAMADO`.
  - Se calcula la distancia temporal en días: $\Delta t = (\text{fecha\_partido.date}() - \text{datetime.now().date}()).\text{days}$.
  - Si $\Delta t > 14$ días: El partido se clasifica como `Fecha Lejana`, sus cuotas permanecen en `None` si el mercado no está abierto, y su selección se bloquea (`disponible = False`, checkbox deshabilitado).
  - Si $\Delta t \le 14$ días (ventana operable inmediata): Si la casa de apuestas (Caliente.mx) tiene cuotas 1X2 válidas publicadas ($O_L, O_E, O_V > 1.0$), el partido es **plenamente operable y seleccionable** (`disponible = True`, checkbox habilitado) para ser incorporado en el cálculo del portafolio.
* **Axioma Anti-Degradación de Partidos Pasados [GOVERNANCE-01]:** Si la marca temporal de un partido es anterior a la hora actual por más de 120 minutos, el sistema tiene prohibido clasificarlo como `PROGRAMADO`. Si la fuente no provee marcador, el partido entra en `CUARENTENA_SIN_RESULTADO` y se desactiva.
* **Ordenamiento Topológico Obligatorio en API (`LiveBoardOut.fixtures`):**
  El backend debe entregar la lista ordenada y agrupada cronológicamente bajo la jerarquía:
  $$\text{Partidos EN\_CURSO} \longrightarrow \text{Partidos PROGRAMADOS (por fecha)} \longrightarrow \text{Partidos REPROGRAMADOS} \longrightarrow \text{Partidos FINALIZADOS (al fondo)}$$
* **Integridad de Snapshot:** Los partidos finalizados de la jornada en curso actualizan dinámicamente la columna de puntos de la tabla general sin romper la correlación estocástica de los partidos restantes.

---

### [ARCH-1.6.4] Desacoplamiento Absoluto de Scraping en el Plano Web (Bus de Datos SQLite) [ARCH-PILLAR] [PERF-MANDATE]

* **Axioma de Desconexión de Red:** Queda strictly prohibido que el servidor web (`src/web/`) o sus servicios de sincronización (`src/storage/sync_service.py`) importen `playwright`, ejecuten navegadores headless o realicen llamadas HTTP síncronas durante el ciclo de vida de las peticiones de los usuarios.
* **El Bus de Datos Local:** La capa web opera exclusivamente como un lector desacoplado contra SQLite (`data/qbe_database.db` en modo WAL).
* **Gobernanza de Roles:**
  - Los scripts independientes en `scripts/` (Centinela Deportivo y Centinela de Mercado) son los **únicos autorizados** para escribir e interactuar con fuentes externas.
  - `sync_league_live_board()` lee de SQLite y responde en un tiempo SLA de **$\le 10\text{ milisegundos}$**.

### [ARCH-1.6.5] Pipeline Adaptador de Portafolio (src/pipeline/adapter.py) [ARCH-PILLAR]

* **Desacoplamiento Relacional (Protocolo Nexus):** El módulo `src/pipeline/adapter.py` actúa como puente puro entre las tablas de SQLite (`FixtureSnapshot`, `StandingSnapshot`) y los motores matemáticos deterministas de `src/core/`.
* **Responsabilidades del Adaptador:**
  1. `construir_master_table_snapshot()`: Convierte el snapshot de posiciones en contratos inmutables `MasterTableSnapshot` calculando `pts_por_partido` para cada club.
  2. `hidratar_partidos_cuantitativos()`: Transforma los partidos seleccionados en objetos `RawMatchInput`, determinando favorito por cuota ($O_{\text{Local}} \le O_{\text{Visitante}}$), asignando promedios 10P Opta $xG/xGA$, evaluando el factor cualitativo $Q_{\text{mod}}$ y construyendo el linaje H2H que satisface la Invarianza #8 de The Shield.

### [ARCH-1.6.6] Aislamiento de Hilos y Timeouts en Ingesta Playwright [ARCH-PILLAR] [ANTI-BUG]

* **Aislamiento de Bucle Asyncio:** Toda invocación síncrona a Playwright (`sync_playwright`) dentro del ciclo de vida de FastAPI o sus controladores REST debe encapsularse obligatoriamente dentro de un worker thread dedicado (`concurrent.futures.ThreadPoolExecutor(max_workers=1)`). Queda terminantemente prohibido invocar la API síncrona en el hilo principal de Uvicorn para evitar colisiones de contexto con el bucle de eventos.
* **Gobierno de Timeouts Rígidos:** Cada operación de extracción en segundo plano debe portar un timeout explícito en su llamada `.result(timeout=...)` (35.0s para FotMob, 40.0s para el Slate FMF y 35.0s para cuotas de Caliente), garantizando que un cuelgue de red externo no degrade ni bloquee indefinidamente los recursos del servidor local.

### [ARCH-1.6.7] Endpoints Atómicos de Refresco Desacoplado [ARCH-PILLAR] [PERF-MANDATE] (H4)

* **Aislamiento de Carga en UI:** Queda estrictamente prohibido que la actualización de momios recargue la tabla de posiciones, o que la actualización de la tabla haga parpadear la cartelera.
* **Contratos REST Especializados:**
  1. `POST /api/leagues/{id}/refresh-tabla`: Invoca exclusivamente `sync_standings_only()`, consulta la tabla oficial de FotMob/FMF, actualiza la tabla relacional `current_team_standings` en SQLite y retorna la lista de 18 clubes en $\le 3\text{s}$.
  2. `POST /api/leagues/{id}/refresh-momios`: Invoca exclusivamente `sync_fixtures_only()`, consulta las cuotas focalizadas de Caliente.mx para la cartelera activa, actualiza `FixtureSnapshot` y retorna los partidos con cuotas actualizadas en $\le 4\text{s}$.

### [ARCH-1.7.0] Lanzador de Servidor con Sonda de Salud (run_app.py) [ARCH-PILLAR] (H10)

* **Apertura de Navegador Sincronizada:** Queda prohibido invocar `webbrowser.open()` de forma prematura antes de que Uvicorn esté en línea.
* **Mecanismo:** El entrypoint `run_app.py` inicia un hilo demonio que sondea en segundo plano el endpoint `http://127.0.0.1:8000/health`. El navegador web se abre única y exclusivamente cuando el servidor responde `HTTP 200 OK`, eliminando pantallas en blanco de conexión rechazada.

### [ARCH-1.7.1] Piso Mínimo de Ventanilla ($2.00 MXN) y Escalamiento Proporcional [BIZ-LOGIC] [ALGO-PROTECTED] (H1)

* **Restricción de Microestructura de Casino:** La casa de apuestas (Caliente.mx) impone una apuesta mínima por boleto de **$2.00 MXN**.
* **Axioma de Escalamiento con Preservación $V=0$:**
  - Si la asignación de Kelly fraccional en un boleto de cobertura o ataque calcula un monto $B < \$2.00\text{ MXN}$, queda prohibido truncar a cero o redondear ciegamente rompiendo el seguro.
  - El sistema escala el boleto menor al piso: $B_{\text{menor}}^* = \$2.00\text{ MXN}$.
  - Para estrategias con cobertura de empate (`QBE-H1`, `QBE-H2`, `QBE-R1`), la inversión total del activo se recalcula para garantizar que el retorno en tablas cubra el 100% de la nueva inversión:
    $$A_i^* = \$2.00 \times O_{\text{Seguro}}$$
    $$B_{\text{Ganancia}}^* = A_i^* - \$2.00\text{ MXN}$$
  - Para Doble Oportunidad Sintética (`QBE-R2`), ambos boletos se escalan por el factor $\max\left(\frac{2.00}{B_1}, \frac{2.00}{B_2}\right)$.
### [ARCH-1.6.10] Herramienta de Saneamiento SQLite y Protocolo de Inferencia On-Demand [ARCH-PILLAR]
* **Utilidad de Purga (`scripts/utilidades/purgar_base_datos.py`):** Permite el reseteo selectivo de las tablas volátiles de snapshots (`fixture_snapshots`, `standing_snapshots`, `portfolio_records`) preservando de forma inmutable el catálogo de `leagues` y `teams`.
* **Axioma de Inferencia Diferida (Lazy-Loading Cognitivo):** Al generar la cartera en `POST /api/portfolio/generate`, el campo `tesis_didactica` debe emitirse strictly como `None` o `"PENDIENTE"`. La invocación a `GeminiCognitiveGateway` se ejecuta de forma exclusiva bajo demanda a través de `POST /api/portfolio/match-thesis` al abrir el modal de Radiografía Forense.

### [ARCH-1.6.11] Servicio de Distribución Soberana y Sincronización en BD (`src/storage/distribution_sync.py`) [DIRGEN-SEALED]

* **Propósito:** Actuar como el puente transaccional definitivo entre los datos deportivos y la tabla relacional 3NF `sovereign_distributions`.
* **Mecánica:**
  1. Consulta a través de `PersistenceGateway.read_session()` los partidos programados (`Match` o `FixtureSnapshot`).
  2. Para cada partido, ejecuta `generar_distribucion_soberana(match_id, raw_data, mu_liga, gamma_home)`.
  3. A través de `PersistenceGateway.write_transaction()`, ejecuta un upsert atómico en la tabla `sovereign_distributions`, persistiendo:
     `match_id`, `model_version`, `p_local`, `p_empate`, `p_visitante`, `lambda_home`, `lambda_away`, `phi_lead2_home`, `phi_lead2_away`, `audit_trace_json`.
* **Idempotencia:** Si el partido ya tiene una distribución idéntica calculada con la misma versión del modelo, no genera escrituras redundantes.

### [ARCH-1.6.12] Ingesta Dinámica de Calendario Completo sin Alambrado [DIRGEN-SEALED] [GOVERNANCE-01]

* **Axioma de Extracción Viva del Calendario:** Queda estrictamente prohibido incluir listas o tuplas estáticas de marcadores pasados en el código de los demonios (`j8_raw`, `j9_raw`, etc.).
* **Mecanismo Dinámico Oficial:**
  - El centinela deportivo consulta en cada ejecución el árbol JSON `__NEXT_DATA__` de FotMob Opta (League ID 230), el cual contiene el calendario íntegro de la temporada oficial.
  - El parser dinámico `_convertir_match_fotmob` filtra en memoria los partidos de cualquier jornada ($N \in [1, 17]$), extrayendo sus marcadores oficiales consumados y fechas ISO.
  - La complementación de reprogramados se ejecuta dinámicamente contra `ligamx.net` mediante deduplicación estricta por par canónico.

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

### [ARCH-1.6.9] Herencia Dinámica de la Cláusula de Pago Anticipado en Boletos [BIZ-LOGIC]
* **Regla de Propagación:** Si un encuentro porta la bandera `pago_anticipado == True` certificada desde el mercado (Caliente.mx), toda orden de ejecución derivada debe heredar obligatoriamente `linea_promocional = "Pago Anticipado (+2 goles)"`.
* **Identificación en Boleto:** Todo boleto que lleve asignación a la victoria de un club (Boleto 1 o Boleto 2) debe desplegar el sufijo `+ PA` en su selección (ej. `Gana Necaxa + PA` o `Gana Toluca + PA`).


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

| Endpoint | Método | Entrada | Salida | Descripción |
|---|:---:|---|---|---|
| `/api/leagues` | `GET` | — | `List[LeagueOut]` | Catálogo de ligas activas registradas en SQLite. |
| `/api/leagues/{id}/live-board` | `GET` | `force_refresh: bool` | `LiveBoardOut` | Entrega Live Board (18 clubes + cartelera en 4 niveles). |
| `/api/leagues/{id}/refresh-tabla` | `POST` | — | `{"standings": ...}` | Refresco aislado de tabla en vivo (FotMob/FMF). |
| `/api/leagues/{id}/refresh-momios` | `POST` | — | `{"fixtures": ...}` | Refresco aislado de momios Caliente y cartelera. |
| `/api/portfolio/generate` | `POST` | `GeneratePortfolioRequest` | `ConsolidatedPayload` | Despacho del motor cuantitativo (Poisson 6x6, Kelly, Dutching). |
| `/api/portfolio/{id}/pdf` | `GET` | — | `FileResponse` | Compilación y descarga de reporte oficial A4 (Playwright). |
| `/api/admin/catalogs/staging` | `GET` | `league_id: int` | `List[Dict]` | Lectura de candidatos de clubes prospectados (HITL). |
| `/api/admin/catalogs/commit` | `POST` | `CommitCatalogRequest` | `{"status": "SEALED"}` | Sellado definitivo de clubes y escudos en SQLite. |
| `/health` | `GET` | — | `{"status": "HEALTHY"}` | Sonda de salud de servidor para auto-lanzador. |

---

## 5. REGLAS DE RESILIENCIA Y MANEJO DE EXCEPCIONES

1. **Safe Zero Divisors (`[ANTI-BUG]`):** Toda división (ej. $1.0 / O$, ratios $SoT / (SoT + SoTA)$) incorpora offset $\epsilon > 0$ o verificación previa (`if denom <= 0: return fallback`).
2. **Invarianza de Clamps (`[ALGO-PROTECTED]`):** Todo multiplicador o factor sintético ($FCF, E_{\text{att}}, \Omega_{\text{perf}}, \theta^*$) debe pasar por funciones `np.clip` o `min/max` antes de ingresar a los modelos de Poisson o Kelly.
3. **Audit Hard-Stop (`[GOVERNANCE]`):** Si `auditor.py` detecta una violación a las 8 Pruebas del Shield, el pipeline lanza `ShieldInvariantException`, abortando la emisión de boletos y la compilación del PDF de forma atómica.
4. **Zero-Mock Policy en Runtime (`[GOVERNANCE-01]`):** Queda prohibida la fabricación de partidos o fechas H2H falsas ante caídas de red. Si una fuente falla, el partido se declara en `CUARENTENA` y se preserva el capital en $0.00 MXN.

---

### [ARCH-1.5.2] Módulo Administrativo de Curación Agéntica HITL y Bóveda de Activos [ARCH-PILLAR]

* **Propósito:** Automatizar la prospección de catálogos deportivos mediante agentes de IA y proporcionar una interfaz de validación humana (Human-in-the-Loop) para aprobar, auditar y sellar permanentemente en SQLite los clubes, estadios, aliases y escudos oficiales.
* **Flujo de Endpoints Administrativos (`src/web/routes/admin.py`):**
  1. `POST /api/admin/catalogs/discover?league_id={id}`:
     - El Agente Curador (Gemini 3.6 Search) rastrea fuentes oficiales, localiza los 18 clubes, sus estadios, aliases y URLs de escudos en alta resolución.
     - Guarda los resultados en un estado temporal de prospección (`data/.staging_catalogs_{id}.json`).
  2. `GET /api/admin/catalogs/staging?league_id={id}`:
     - Retorna los clubes prospectados para su inspección visual en la interfaz de usuario.
  3. `POST /api/admin/catalogs/commit`:
     - Recibe la confirmación humana de los clubes aprobados.
     - Descarga físicamente los escudos validados al almacén soberano local (`src/web/static/img/crests/{slug}.png`).
     - Inserta/actualiza de forma inmutable los registros en las tablas `teams`, `venues` y `aliases` de SQLite.
* **Aislamiento de Producción:** Ningún club en estado de prospección (*staging*) es visible en los endpoints públicos de Live Board (`/api/leagues/{id}/live-board`) hasta haber sido sellado mediante el commit administrativo.

---

### [ARCH-1.4.5] Robustez de Parsers DOM y Expresiones Multilínea [ANTI-BUG]

* **Tolerancia a Saltos de Línea en Marcadores:** Los scrapers de resultados en vivo deben emplear patrones de expresiones regulares multilínea capaces de resolver goles separados por retornos de carro o espacios en el DOM (`(?<!\d)(\d+)\s*\n*\s*[-–]\s*\n*\s*(\d+)(?!\d)`), impidiendo que marcadores legítimos concluidos se descarten como nulos.

---

### [ARCH-1.5.8] Parámetros Canónicos de Normalización y Bóveda de Activos [ARCH-PILLAR] [ANTI-BUG]

* **Limpieza Lingüística Determinista (H9):** El normalizador canónico (`[LN-QBE-012]`) aplica obligatoriamente: eliminación estricta de acentos (`strip_accents`), conversión a minúsculas, sustitución de caracteres no-alfanuméricos por espacios (`[^a-z0-9\s]`) y colapso de dobles espacios antes de cualquier comparación.
* **Umbrales de Coincidencia Difusa (H10):** Ante variantes ortográficas de scrapers heterogéneos, se autoriza la equivalencia de identidad si `SequenceMatcher.ratio() >= 0.78` o si la distancia de Levenshtein es $\le 2$ para cadenas de longitud $\ge 4$ caracteres. Si el ratio es inferior, el sistema invoca `NormalizationException`.
* **Aduana de IDs de Imagen FMF (H1):** El diccionario inmutable `LIGAMX_LOGO_ID_MAP` opera como respaldo determinista de resolución cuando el servidor oficial de la federación emite etiquetas `<img>` con atributo `alt` vacío o indefinido en el carrusel de marcadores.
* **Umbrales Físicos de Bóveda y Espejeo (H13, H14):** Todo escudo de club guardado localmente debe verificar `size >= 3000` bytes y cabecera PNG válida (`\x89PNG`). Todo emblema de torneo debe verificar `size >= 1000` bytes. Durante el commit de curación HITL, se ejecuta el copiado físico obligatorio (`shutil.copyfile`) hacia todos los aliases del club para garantizar integridad multi-slug inmediata.

---

### [ARCH-1.6.6] Aislamiento de Hilos y Timeouts en Ingesta Playwright [ARCH-PILLAR] [ANTI-BUG]

* **Aislamiento de Bucle Asyncio:** Toda invocación síncrona a Playwright (`sync_playwright`) dentro del ciclo de vida de FastAPI o sus controladores REST debe encapsularse obligatoriamente dentro de un worker thread dedicado (`concurrent.futures.ThreadPoolExecutor(max_workers=1)`). Queda terminantemente prohibido invocar la API síncrona en el hilo principal de Uvicorn para evitar colisiones de contexto con el bucle de eventos.
* **Gobierno de Timeouts Rígidos:** Cada operación de extracción en segundo plano debe portar un timeout explícito en su llamada `.result(timeout=...)` (35.0s para FotMob, 40.0s para el Slate FMF y 35.0s para cuotas de Caliente), garantizando que un cuelgue de red externo no degrade ni bloquee indefinidamente los recursos del servidor local.

### [ARCH-1.6.8] Topología Multi-Jornada y Caché Particionado por Slate [ARCH-PILLAR] [PERF-MANDATE]

* **Propósito:** Permitir la exploración, ingesta y selección fluida de partidos pertenecientes a múltiples jornadas consecutivas (ej. Jornada $N$ en disputa y Jornada $N+1$ con mercado abierto), garantizando aislamiento de estados y cero colisiones en base de datos.
* **Partición de Estado en SQLite:**
  - Las tablas `matchday_states`, `fixture_snapshots` y `fixture_records` se particionan explícitamente por la tupla `(league_id, matchday_num)`.
  - La ingesta o consulta de una jornada futura ($N+1$) **tiene estrictamente prohibido sobreescribir, alterar o purgar los registros de la jornada activa ($N$)**.
* **Contratos REST Extendidos (`src/models/web_schemas.py`):**
  - `GET /api/leagues/{id}/live-board?jornada={num}&force_refresh={bool}`:
    - Si `jornada` es omitido (`None`): entrega por defecto la jornada en curso o la última con partidos pendientes.
    - Si `jornada` es especificado: consulta el snapshot correspondiente en SQLite. Aplica política Cache-First con TTL independiente: si el snapshot existe y es válido, entrega en $\le 20\text{ ms}$.
  - El esquema `LiveBoardOut` incorpora obligatoriamente:
    ```python
    jornada_actual: int            # Jornada administrativa en curso (ej. 8)
    jornada_mostrada: int          # Jornada renderizada actualmente (ej. 9)
    jornadas_disponibles: List[int] # Lista de jornadas navegables (ej. [8, 9])
    ```
* **Selección Híbrida de Cartera (`POST /api/portfolio/generate`):**
  - El contrato `GeneratePortfolioRequest` procesa un array arbitrario de `selected_match_ids`.
  - El `PipelineAdapter` resuelve cada ID independientemente de su jornada de origen (`partido_262_j8_...` y `partido_262_j9_...`), vinculando la tabla de posiciones consolidada y aplicando los Hard-Caps globales (Invarianzas #3 y #4) sobre el portafolio unificado.

---

### [ARCH-1.6.13] Motor de Ingesta Total de Temporada y Reconstrucción Histórica [DIRGEN-SEALED] [GOVERNANCE-01]

* **Axioma de Cobertura Temporal Integral:** El Centinela Deportivo debe extraer la totalidad del calendario oficial de la competición (153 partidos en torneos de 18 clubes, divididos en 17 jornadas).
* **Reconstrucción Determinista de Tablas Históricas:**
  - A partir de los marcadores oficiales consumados de las fechas concluidas, el motor calcula algebraicamente la tabla de posiciones acumulada al corte de cada jornada ($Pts = 3 \cdot PG + PE$, $DIF = GF - GC$).
  - Persiste un `StandingSnapshot` y un `FixtureSnapshot` para cada jornada de la temporada en SQLite.
* **Soberanía Dinámica:** Cero constantes o tuplas de partidos quemadas en código Python (`[GOVERNANCE-01]`). Todo emana dinámicamente de la red vía FotMob Opta (League 230).

---
**BASE DE GOBIERNO SELLADA BAJO EL KYBERN FRAMEWORK v8.0 / v12.0 — ARQUITECTURA TÉCNICA INMUTABLE.**

```