```markdown
# Q-BE Casino Deportes — Architecture Book (ARCH.md)
**Versión:** 10.0 (Multi-Bookmaker & Focus Mode Edition)  
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

### [ARCH-1.4.5-C] Unificación del Controlador Financiero REST en markets.py [ARCH-PILLAR]
* El endpoint oficial para generación de cartera Sportsbook es exclusivamente:
  `POST /api/markets/sportsbook/portfolio/generate`
* Consume directamente la base de datos 3NF SQLite (`PersistenceGateway`) y delega el cálculo a `portfolio_math.py`.
* **Materialización (Fase 4):** la ruta canónica `POST /api/markets/sportsbook/portfolio/generate` cierra la cartera con la **ley financiera canónica** de `portfolio_math.py`: `aplicar_hard_caps_constitucionales` (techo individual 8.0% y prorrateo global de jornada 25.0%) y piso de ventanilla `PISO_MINIMO_BOLETO` (`[LN-QBE-071]`). Queda **pendiente de migración** la capa de *orquestación* (hidratación 3NF + pipeline Poisson), aún servida por el router legado; mientras subsista, `src/web/routes/portfolio.py` conserva el estatus de **deprecada** y no debe exponerse como endpoint público.
* **Frontera de selección:** la selección manual se gobierna por el Live Board (`[ARCH-1.6.2-B]`); el despacho automático de jornada opera sobre el pool multiversal de snapshots. Ver `[ARCH-1.6.2-B]`.
* La ruta `src/web/routes/portfolio.py` queda oficialmente **deprecada** para eliminar duplicidades y acoplamiento con adaptadores legacy.
* **[DEROGADO: Se prohíbe terminantemente invocar QBEPipelineEngine o importar src/web/routes/portfolio.py desde la Estación de Mercados. El pipeline monolítico queda restringido a tareas batch de sincronización de tablas; el despacho financiero de apuestas opera de forma desacoplada y directa sobre la base de datos 3NF].**

---

### [ARCH-1.4.6] Topología de Ingesta Multi-Operador y Persistencia Relacional [ARCH-PILLAR]
* **Fuente de Datos Betway.mx:**  
  URL oficial de mercado: `https://betway.mx/mx/es-mx/sports/grp/soccer/mexico/liga-mx?tab=matches`
* **Arquitectura de Extracción:**
  - Se materializa `src/ingestion/betway_scraper.py` encapsulado en la clase `BetwayMarketScraper`.
  - Emplea Playwright headless con perfiles de evasión stealth, timeout de 30.0s y búsqueda focalizada restringida exclusivamente a los pares del slate oficial de la jornada.
* **Axioma de Retrocompatibilidad en `FixtureSnapshot.matches_json`:**
  Cada partido dentro del snapshot almacenará el mapa extendido de operadores:
  ```json
  {
    "id_partido": "LIGAMX-J10-01",
    "local": "Toluca",
    "visitante": "Atlas",
    "momios_operadores": {
      "caliente": { "L": 1.70, "E": 3.80, "V": 4.50, "pago_anticipado": true, "updated_at": "..." },
      "betway": { "L": 1.72, "E": 3.75, "V": 4.60, "pago_anticipado": false, "updated_at": "..." }
    },
    "momios": { "L": 1.70, "E": 3.80, "V": 4.50, "pago_anticipado": true } // Operador principal por defecto
  }
  ```
* **Orquestación en `centinela_mercado.py`:**
  Acepta el parámetro `--operador [caliente|betway|todos]` (por defecto: `todos`), sincronizando secuencialmente ambos frentes y emitiendo un tablero comparativo en consola.

### [ARCH-1.4.6-C] Control de Errores y Telemetría de Extracción [ARCH-PILLAR]
Todo sensor de mercado (`caliente_scraper.py`, `betway_scraper.py`) debe emitir obligatoriamente en consola y en logger:
1. **Nivel Red:** Código HTTP del servidor (`HTTP 200 OK`, `403 Forbidden`, etc.) y tiempo de respuesta.
2. **Nivel DOM:** Cantidad total de contenedores de evento localizados y líneas de texto extraídas.
3. **Nivel Parsing:** Lista de eventos crudos parseados exitosamente (`local_raw vs visitante_raw @ L/E/V`).
4. **Nivel Matching:** Resultado del cotejo contra el Slate oficial:
   - `[MATCH OK] "Atlante" vs "Monterrey" -> Vinculado`
   - `[MATCH DESCARTADO] "Mañana" vs "Local" -> Ignorado por lista negra / no coincide con Slate`
5. **Fail-Loud:** Si el código HTTP no es 200 o los partidos extraídos son 0, emitir advertencia explícita en consola con el motivo exacto.

### [ARCH-1.4.6-D] Expansión Universal de Acordeones de Fecha y Virtual Scroll en Betway [ARCH-PILLAR]
* **Problema:** Betway Next.js agrupa encuentros bajo acordeones dinámicos basados en horario UTC (ej. partidos de sábado en México aparecen bajo "Domingo"). Los días subsecuentes se cargan cerrados (`display: none`).
* **Mecanismo Obligatorio:** Antes de la extracción de texto, Playwright debe:
  1. Ejecutar un barrido DOM interactivo haciendo clic en todos los elementos que contengan texto de días (`hoy`, `mañana`, `sábado`, `domingo`, `lunes`).
  2. Ejecutar desplazamiento vertical progresivo (`page.mouse.wheel(0, 1200)`) para forzar la hidratación de los componentes virtualizados.
  3. Re-posicionar el scroll en la cabecera antes de parsear.

### [ARCH-1.4.6-E] Filtro de Descontaminación de Filas de Evento en Caliente [ARCH-PILLAR]
* **Mecanismo:** Documentar el descarte de filas cruzadas que mencionen a clubes populares ajenos al par objetivo del slate oficial durante el scraping en Caliente.mx para prevenir la contaminación de mercados.

### [ARCH-1.4.6-F] Sensor de Ingesta Novibet.mx por Intercepción de Feed JSON [ARCH-PILLAR]
* **Fuente de Datos:** `https://www.novibet.mx/apuestas-deportivas/futbol/mexico/liga-mx`
* **Arquitectura de Extracción:**
  - Se materializa `src/ingestion/novibet_scraper.py` encapsulado en la clase `NovibetMarketScraper`.
  - Emplea Playwright headless con pre-siembra de cookie de consentimiento (`CookieConsent`) para saltar Cookiebot en 0ms.
  - Intercepta directamente las respuestas de red dirigidas a `/spt/feed/marketviews/location/v2/`.
  - Extrae el mercado canónico `betTypeSysname == "SOCCER_MATCH_RESULT"` (1X2), leyendo `price` decimal nativo.
  - Verifica la presencia del tag `SOCCER_2_GOALS_AHEAD_EARLY_PAYOUT` para activar `pago_anticipado = True`.
  - **Ruta de Transporte Auditada (VARIANCE-01 §V-3-bis):** la hidratación del componente Angular de mercados y la emisión del feed se obtienen navegando la ruta de carrusel `https://www.novibet.mx/apuestas-deportivas/populares/4561745/competitions?ids=6791922,4596556,6589925&t=6792246` (el parámetro `t` transporta el `locationId` 6792246 del feed), esperando la señal DOM `sb-market-bet-item`. La ruta `/apuestas-deportivas/futbol/mexico/liga-mx` responde HTTP 200 pero no monta el componente de mercados y emite 0 respuestas del namespace.
* **Persistencia en 3NF:**
  - Almacena en `FixtureSnapshot.matches_json` bajo `momios_operadores["novibet"]`.

> **Trazabilidad de registro (VARIANCE-01) — Volumen III (Novibet):** el nodo
> `[ARCH-1.4.6-F]` se incorpora como **enmienda correctiva** anclada a su nodo matriz sellado
> `[ARCH-1.4.6]` inmediatamente después de `[ARCH-1.4.6-E]`, sin colisión con los
> identificadores previamente legislados (`[ARCH-1.4.6]`, `-C`, `-D`, `-E`). El contrato de
> telemetría `[ARCH-1.4.6-C]` rige íntegramente sobre el nuevo sensor. Juez Inmutable:
> `tests/shield/test_shield_novibet_ingestion.py`.

---

### [ARCH-1.4.7] Contrato de Telemetría Extendida en FixtureSnapshot.matches_json [ARCH-PILLAR]
Cada partido almacenarás en `matches_json`:
```json
{
  "id_partido": "LIGAMX-J10-01",
  "local": "Atlante",
  "visitante": "Monterrey",
  "momios_operadores": {
    "caliente": { "L": 3.45, "E": 3.75, "V": 1.98, "pa": true },
    "betway": { "L": 3.30, "E": 3.75, "V": 2.00, "pa": false }
  },
  "probabilidades_sin_comision": {
    "caliente": { "p_L": 0.273, "p_E": 0.251, "p_V": 0.476 },
    "betway": { "p_L": 0.284, "p_E": 0.250, "p_V": 0.466 }
  },
  "arbitraje": {
    "existe": false,
    "indice": 1.0032,
    "roi_pct": 0.0,
    "mejor_L": { "momio": 3.45, "operador": "caliente" },
    "mejor_E": { "momio": 3.75, "operador": "caliente" },
    "mejor_V": { "momio": 2.00, "operador": "betway" }
  },
  "consenso_mercado": {
    "p_L_mercado": 0.279,
    "p_E_mercado": 0.251,
    "p_V_mercado": 0.471,
    "delta_L": -0.069,
    "delta_E": -0.011,
    "delta_V": +0.089
  },
  "momios": { "L": 3.45, "E": 3.75, "V": 1.98, "pago_anticipado": true }
}
```

### [ARCH-1.4.7-B] Jerarquía y Retrocompatibilidad de Cuotas por Defecto [ARCH-PILLAR]
* **Mecanismo:** Documentar la prioridad de Caliente.mx como operador primario en `fx["momios"]` y Betway.mx como fallback secundario para garantizar retrocompatibilidad.

---

### [ARCH-1.4.8] Despacho Global de Mesa de Apuestas y Descarte Temprano [ARCH-PILLAR]

### [ARCH-1.4.8-B] Exposición del Objeto `consenso_mercado` en LiveBoardOut [ARCH-PILLAR]
* El endpoint `GET /api/leagues/{id}/live-board` debe asegurar el paso del diccionario `consenso_mercado` y `momios_operadores` dentro de cada objeto de partido en `fixtures`, permitiendo al frontend renderizar los niveles 2 y 3 sin peticiones HTTP adicionales.


* **Axioma de Despacho Integral:** El endpoint `POST /api/markets/sportsbook/portfolio/generate` no requiere una lista manual de partidos (`selected_match_ids`). Si la lista no se proporciona o está vacía, el sistema recupera automáticamente la totalidad de los partidos abiertos en ventanilla para la jornada activa (Jornada 10) desde SQLite.
* **Compuerta de Descarte Temprano de Rentabilidad:** Antes de asignar capital o ejecutar Dutching:
  1. Cruza las cuotas de Caliente.mx ($O_L, O_E, O_V$) contra las probabilidades soberanas de `sovereign_distributions` ($\hat{P}_i$).
  2. Calcula los GAPs matemáticos: $\text{GAP}_k = P_k - (1.0 / O_k)$.
  3. Ejecuta el filtro de rentabilidad: si ningún desenlace ofrece Esperanza Matemática Positiva ($+EV \le 0$) o si el encuentro es un volado simétrico sin asimetría explotable, el partido se deriva de inmediato a `QBE-00` (Descarte Preventivo / Veto) con asignación de $\$0.00\text{ MXN}$.
* **Hidratación Soberana Obligatoria:** Las órdenes de los partidos rentables se construyen consumiendo exclusivamente las intensidades acotadas ($\lambda_H, \lambda_A$), el Símplex $\Delta^2$ y el Pago Anticipado de André ($\Phi_{\text{Lead2}}$) calculados por el Tratado Volumen I.

### [ARCH-1.4.9] Módulo de Contratos Matemáticos Inmutables (portfolio_math.py) [ARCH-PILLAR]
* **Ubicación:** `src/core/contracts/portfolio_math.py`
* **Régimen:** `[DIRGEN-STRICT]` (Plano canónico en `docs/DIRGEN_VAULT.md`).
* **Responsabilidad:** Biblioteca matemática funcional pura, sin I/O, sin Pydantic y sin dependencias de base de datos.
* **Funciones requeridas:**
  - `calcular_alpha_edge(p, O) -> float`
  - `calcular_umbral_theta_estrella(o_fav) -> float`
  - `calcular_dutching_v0(b_total, o_fav, o_emp) -> Tuple[float, float, float, float]`
  - `escalar_a_piso_ventanilla(b_seg, o_emp, piso=2.0) -> Tuple[float, float, float]`
  - `triaje_determinista_9_estrategias(payload_soberano, cuotas) -> dict`
  - `calcular_ranking_friccion(partidos) -> list`
  - `calcular_kelly_atenuado(p, O, delta_epist, gamma=0.25) -> float`
  - `aplicar_hard_caps_constitucionales(inversiones, bankroll) -> list`

### [ARCH-1.4.10] Despacho Financiero 3NF en markets.py [ARCH-PILLAR]
* **Endpoint:** `POST /api/markets/sportsbook/portfolio/generate`
* **Arquitectura de Ejecución:**
  1. Consulta en modo lectura atómica `PersistenceGateway.read_session()` sobre `FixtureSnapshot` y `SovereignDistribution` de la jornada activa (Jornada 10).
  2. Extrae las cuotas comerciales desde `matches_json` (`momios_operadores`).
  3. Ejecuta el triaje determinista de 9 estrategias y el ranking de fricción directamente en memoria.
  4. Invoca `PortfolioEngine.build_plan()` alimentado por el `CandidateMatchPayload` extendido.
  5. Retorna la respuesta con latencia $< 20\text{ms}$, eliminando recálculos pesados o llamadas redundantes a disco.

### [ARCH-1.4.12] Servicio del Centro de Control y Despacho de Tareas Administrativas [ARCH-PILLAR]

* **Endpoint:** `POST /api/admin/tasks/run`
* **Contrato de Entrada:** `AdminTaskRequest(task_id: str)`
* **Whitelist Estricta de Seguridad:** Se prohíbe la ejecución de comandos arbitrarios. Solo se autorizan los identificadores certificados:
  - `centinela_deportivo` (FotMob J1-J17)
  - `centinela_mercado` (Caliente + Betway dinámico)
  - `centinela_progol` (Progol #2352 miloteria.mx)
  - `sincronizar_activos` (Escudos y logos locales)
  - `cadena_ingesta_total` (Secuencia encadenada: Deportivo ➔ Mercado ➔ Progol)
  - `auditar_pureza_vol1` (7/7 tests Tratado I)
  - `auditar_cartera_shield` (Invarianzas en DB)
  - `consultar_uso_llm` (Salud de llaves y tokens)
  - `purgar_base_datos` (Reset selectivo de snapshots)
* **Contrato de Salida:** `AdminTaskResponse(task_id: str, exit_code: int, output: str, duration_s: float)`

### [ARCH-1.4.13] Guarda de Resiliencia ante Base de Datos Vacía en Live Board [ARCH-PILLAR]
* Si `sync_league_live_board` o `leagues.py` se consultan tras una purga (cuando no existen snapshots en SQLite), el backend tiene prohibido arrojar HTTP 500 ("Error al obtener Live Board").
* Debe retornar HTTP 200 con payload neutro estructurado (`{"standings": [], "fixtures": [], "db_vacia": true}`), permitiendo que la UI muestre una guía didáctica en lugar de un fallo roto.

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

#### Tablas: `slates` y `slate_items` — [ARCH-1.5.1-C]
**Diccionario de datos sellado del subsistema de quinielas (Progol Regular + Revancha).**
El vínculo con la bóveda estocástica es **opcional por diseño**: `slate_items.match_id` es `NULLABLE` porque la legislación `[LN-QBE-075]` ordena que una casilla sin vínculo soberano degrade al **Prior de Ignorancia Fiduciario** sin bloquear la ingesta. La clave primaria de `slate_items` es **sustituta** (`id` autoincremental) y la unicidad de casilla se garantiza por `UNIQUE (slate_id, position)` (`uq_slate_item_position`).

**`slates`** — Concurso principal (Progol, quiniela multitorneo):
| Columna | Tipo | Restricción | Descripción |
|---|---|---|---|
| `id` | `VARCHAR(50)` | `PK` | ID único del concurso (ej. `PROGOL-2352`, `PRONOSPORTS-754`) |
| `name` | `VARCHAR(120)` | `NOT NULL` | Nombre del concurso |
| `competition_id` | `VARCHAR(50)` | `FK → competitions.id` | Liga principal del concurso |
| `matchday_num` | `INTEGER` | | Jornada asociada |
| `bolsa_estimada` | `FLOAT` | | Bolsa fáctica ofrecida por el concurso (MXN) |
| `fecha_cierre` | `DATETIME` | | Cierre del concurso; `NULL` si la fuente no publica el año |
| `status` | `VARCHAR(20)` | `NOT NULL` | Estado del concurso: `OPEN`, `CLOSED`, `SETTLED` |
| `created_at` | `DATETIME` | `NOT NULL` | Timestamp de creación |

**`slate_items`** — Casilla de quiniela (21 por concurso: `1..14` Regular, `15..21` Revancha):
| Columna | Tipo | Restricción | Descripción |
|---|---|---|---|
| `id` | `INTEGER` | `PK` | ID autoincremental (surrogate key) |
| `slate_id` | `VARCHAR(50)` | `FK → slates.id`, `NOT NULL` | Concurso al que pertenece |
| `tipo_concurso` | `VARCHAR(20)` | `NOT NULL` | Torneo de origen: `REGULAR` \| `REVANCHA` |
| `position` | `INTEGER` | `NOT NULL` | Posición en la quiniela (`1..14` Regular, `15..21` Revancha) |
| `local_raw` | `VARCHAR(100)` | | Cadena fáctica del DOM (local), sin interpretar |
| `visitante_raw` | `VARCHAR(100)` | | Cadena fáctica del DOM (visitante), sin interpretar |
| `local_canonico` | `VARCHAR(100)` | | Identidad canónica normalizada (local) |
| `visitante_canonico` | `VARCHAR(100)` | | Identidad canónica normalizada (visitante) |
| `match_id` | `VARCHAR(100)` | `FK → matches.id`, `NULLABLE` | Vínculo soberano; `NULL` ⇒ Prior Fiduciario |
| `p_local` | `FLOAT` | | $P(\text{local})$ soberana, u $0.3333$ bajo Prior |
| `p_empate` | `FLOAT` | | $P(\text{empate})$ soberana, u $0.3333$ bajo Prior |
| `p_visitante` | `FLOAT` | | $P(\text{visitante})$ soberana, u $0.3334$ bajo Prior |
| `es_prior_ignorancia` | `BOOLEAN` | `NOT NULL` | `True` ⇔ distribución fiduciaria $(1/3, 1/3, 1/3)$ de `[LN-QBE-075]` |

* **Migración física:** SQLite no permite `ALTER` sobre una clave primaria compuesta, por lo que la recreación se ejecuta mediante `scripts/utilidades/migrar_schema_slates.py`, utilitario con **guarda fiduciaria** que aborta (`exit 2`) si alguna de las dos tablas contiene filas.

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

### [ARCH-1.5.3-B] Política de Servido de Activos Visuales y Mitigación Anti-Hotlinking [ARCH-PILLAR] [ANTI-BUG]

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

### [ARCH-1.6.2-B] Ancla Temporal Canónica, Cuarentena por Staleness y Orden Topológico Materializado [ARCH-PILLAR] [GOVERNANCE-01]

* **Reloj Soberano Único:** Toda evaluación de vigencia temporal de la cartelera se computa contra `datetime.now()` del proceso servidor **en el instante de materialización del payload**. Queda prohibido usar la marca `updated_at` del snapshot como sustituto del reloj: la antigüedad del snapshot no exime a un partido ya disputado de ser materializado como tal.
* **Cuarentena por Staleness:** Si $(\text{ahora} - \text{fecha\_dt}) > 150$ minutos, el fixture es **incompatible** con el estado `PROGRAMADO`. `sync_league_live_board` lo materializa como `FINALIZADO` con `marcador_actual = "MARCADOR_PENDIENTE"` (token formal de resultado no capturado) y `disponible_para_seleccion = False`. **Queda prohibido fabricar marcadores**; el token declara la ausencia fáctica de resultado ([GOVERNANCE-01]).
* **Armonización del Umbral:** el umbral operativo queda **unificado en 150 min (2.5 h)**, en paridad exacta con la Invariante #5 del Juez `[LN-QBE-025]`, sustituyendo la mención genérica de 120 min del axioma anti-degradación.
* **Operabilidad Total de Cuotas:** Un fixture no finalizado sin cuotas válidas ($L, E, V > 1.0$) se materializa con `disponible_para_seleccion = False` (paridad con la Invariante #4 del Juez `[LN-QBE-025]`).
* **Orden Topológico Materializado en Backend:** `LiveBoardOut.fixtures` se ordena en `sync_league_live_board` (no en el cliente) bajo la jerarquía inmutable de `[ARCH-1.6.3]`, mediante ordenamiento **estable** que preserva la cronología dentro de cada capa semántica. El mapa `_ORDEN_TOPOLOGICO` de `src/web/routes/leagues.py` es la única fuente semántica de la jerarquía.
* **Frontera de Despacho (reconciliación con [ARCH-1.4.5-C]):** la selección **manual** de partidos está gobernada por el Live Board (veto de `FINALIZADO` y de la cuarentena por staleness). El **despacho automático de jornada** (`selected_match_ids = []`) opera sobre el pool multiversal de snapshots capturados, por tratarse de un lote de refresco total sobre cuotas ya publicadas; no puede ser vetado por staleness sin declarar la jornada completa inoperable. Cualquier endurecimiento de esta frontera requiere VAR previa del Director.

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

### [ARCH-1.6.10-B] Purga Atómica y Limpieza Relacional 3NF [ARCH-PILLAR]
* Al invocar la purga de la base de datos, el script debe vaciar en una sola transacción todas las tablas dependientes y volátiles:
  - `portfolio_records`
  - `slate_items` y `slates`
  - `sovereign_distributions`
  - `matches`
  - `standing_snapshots` y `fixture_snapshots`
  - `current_team_standings` y `matchday_states`
* **Inmutabilidad de Catálogo:** Las tablas maestras `leagues` y `teams` quedan estrictamente preservadas e intactas.
* Se erradica cualquier estado zombi (tener partidos pero no tablas, o tener cuotas sin distribución).

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

### [ARCH-1.6.8] Topología Multi-Jornada y Caché Particionado por Slate [ARCH-PILLAR] [PERF-MANDATE]

* **Propósito:** Permitir la exploración, ingesta y selección fluida de partidos pertenecientes a múltiples jornadas consecutivas (ej. Jornada $N$ en disputa y Jornada $N+1$ con mercado abierto), garantizando aislamiento de estados y cero colisiones en base de datos.
* **Partición de Estado en SQLite:**
  - Las tablas `matchday_states`, `fixture_snapshots` y `fixture_records` se particionan explícitamente por la tupla `(league_id, matchday_num)`.
  - La ingesta o consulta de una jornada futura ($N+1$) **tiene strictly prohibido sobreescribir, alterar o purgar los registros de la jornada activa ($N$)**.
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

### [ARCH-1.6.13] Motor de Ingesta Total de Temporada y Reconstrucción Histórica [DIRGEN-SEALED] [GOVERNANCE-01]

* **Axioma de Cobertura Temporal Integral:** El Centinela Deportivo debe extraer la totalidad del calendario oficial de la competición (153 partidos en torneos de 18 clubes, divididos en 17 jornadas).
* **Reconstrucción Determinista de Tablas Históricas:**
  - A partir de los marcadores oficiales consumados de las fechas concluidas, el motor calcula algebraicamente la tabla de posiciones acumulada al corte de cada jornada ($Pts = 3 \cdot PG + PE$, $DIF = GF - GC$).
  - Persiste un `StandingSnapshot` y un `FixtureSnapshot` para cada jornada de la temporada en SQLite.
* **Soberanía Dinámica:** Cero constantes o tuplas de partidos quemadas en código Python (`[GOVERNANCE-01]`). Todo emana dinámicamente de la red vía FotMob Opta (League 230).

### [ARCH-1.6.13-B] Unicidad Estricta de Encuentros Reprogramados [ARCH-PILLAR]
* **Regla de No Duplicación:** Queda estrictamente prohibido inyectar partidos reprogramados en jornadas arbitrarias mediante condiciones fijas (`if r == 8: ...`).
* Un partido reprogramado pertenece exclusivamente a su jornada de origen o se consolida en una sola bandeja de pendientes; jamás debe coexistir duplicado en los snapshots de dos jornadas distintas (ej. aparecer en J7 y J8 simultáneamente).

### [ARCH-1.6.15] Resolución Dinámica de Jornada Activa en Sensores de Mercado [ARCH-PILLAR]
* **Problema:** Un valor quemado por defecto (`--jornada 10`) provoca que al concluir los partidos de una fecha, el sensor escanee una jornada finalizada cuyas cuotas han sido retiradas por los casinos (0/9 encontrados).
* **Mecanismo Obligatorio:** Si `centinela_mercado.py` se invoca sin el argumento `--jornada` (o en modo automático):
  1. Consulta en SQLite los `FixtureSnapshot` de la competición activa.
  2. Resuelve la **primera jornada que contenga al menos un partido en estado `PROGRAMADO`**.
  3. Si la Jornada 10 ya finalizó en su totalidad, conmuta automáticamente a la **Jornada 11**.
  4. Si todas las jornadas están concluidas, selecciona la última disponible.

### [ARCH-1.6.15-B] Desacoplamiento Cronológico en Sensores de Mercado [ARCH-PILLAR]
* **Principio de Asincronía Fáctica:**
  - En la federación (LigaMX.net / FotMob), una jornada permanece administrativamente "activa" en sus calendarios incluso después de que los 9 partidos han finalizado el domingo, hasta que ellos cambian el ciclo a mitad de semana.
  - En las casas de apuestas (Caliente.mx / Betway.mx), las cuotas se retiran en el minuto en que los partidos concluyen. Los casinos ofrecen exclusivamente los partidos por jugarse y abren de inmediato la **siguiente jornada cronológica**.
* **Mecanismo de Resolución del Slate de Mercado:**
  Para determinar qué jornada debe escanear `centinela_mercado.py`:
  1. No debe depender de la etiqueta administrativa "activa" de la liga.
  2. Debe identificar la jornada con la **fecha de juego más próxima hacia el futuro** ($t_{\text{kickoff}} \ge t_{\text{ahora}}$), descartando jornadas cuyos 9 partidos ya finalizaron.
  3. Los partidos reprogramados a fechas lejanas ($> 14$ días, ej. juegos de noviembre) no deben desviar el sensor hacia jornadas pasadas vacías. El sensor debe apuntar a la jornada ordinaria con cartelera regular abierta (ej. Jornada 11).

### [ARCH-1.6.16] Política de Depuración y Archivado de Sondas Temporales [ARCH-PILLAR]
* Las herramientas de diagnóstico de un solo uso o superadas (`sonda_diagnostico_progol.py`, `sonda_diagnostico_betway.py`, `aislar_fuga_probabilidades.py`, `comprobar_payload_http.py`, `simulador_pantalla_soberana.py`, `migrar_schema_slates.py`, `exportar_volumen1_word.py`) se mueven a `scripts/archive/` para preservar la higiene del repositorio.

> **Trazabilidad de registro (VARIANCE-01) — Fase 7:** los nodos `[ARCH-1.6.15]`,
> `[ARCH-1.4.12]` y `[ARCH-1.6.16]` se incorporan en su familia numérica canónica
> (`1.6.x` tras `[ARCH-1.6.13]`; `1.4.x` tras `[ARCH-1.4.10]`) sin alterar ningún nodo
> sellado. Los identificadores `[ARCH-1.4.11]` y `[ARCH-1.6.14]` permanecen **no
> asignados** (cero reutilización). Juez Inmutable asociado:
> `tests/shield/test_shield_admin_tasks_and_dynamic_matchday.py`.

> **Trazabilidad de registro (VARIANCE-01) — Fase 7.5:** los nodos `[ARCH-1.6.15-B]`,
> `[ARCH-1.6.13-B]`, `[ARCH-1.6.10-B]` y `[ARCH-1.4.13]` se incorporan como enmiendas
> correctivas ancladas a sus nodos matrices sellados (`[ARCH-1.6.15]`, `[ARCH-1.6.13]`,
> `[ARCH-1.6.10]`, `[ARCH-1.4.12]`) sin alterar una sola coma de los planos vigentes.
> Los identificadores `[ARCH-1.4.11]` y `[ARCH-1.6.14]` permanecen **no asignados**
> (cero reutilización). Juez Inmutable asociado:
> `tests/shield/test_shield_market_resolution_and_purge.py` (Twin-Test en Estado RED
> certificado; la materialización en `src/` y `scripts/` queda supeditada a la
> autorización de la Tríada).

### [ARCH-1.4.14] Denominador Fáctico de Cartelera en Macro KPIs [ARCH-PILLAR]
* En el payload emitido por el generador de cartera, el campo `total_partidos_escaneados` debe transportar estrictamente la cantidad total de partidos que componen la fecha en `FixtureSnapshot.matches_json` (ej. 9 partidos en Liga MX), garantizando que el frontend exhiba con veracidad $K / 9$ y no $K / K$.

### [ARCH-1.4.15] Contrato de Disponibilidad Dinámica de Operadores en Ventanilla [ARCH-PILLAR]
* El endpoint que alimenta el selector de casinos no debe fallar silenciosamente usando datos de otro casino. Si un operador carece de cuotas en la jornada activa, el backend debe marcarlo con `disponible: false`, y el frontend debe deshabilitarlo o rotularlo como `(Sin cuotas disponibles)`.

### [ARCH-1.5.10] Bóveda de Activos de Operadores de Casino [ARCH-PILLAR]
* El script `sincronizar_boveda_activos.py` debe descargar y anclar en disco local los logotipos oficiales de las casas de apuestas en `/static/img/bookmakers/{slug}.png` (caliente, betway).
* Queda prohibido el hotlinking a servidores de terceros para logos de casinos.

> **Trazabilidad de registro (VARIANCE-01) — Fase 7.6:** la Directiva Maestra solicitó el
> identificador `[ARCH-1.5.4]` para la Bóveda de Activos de Operadores de Casino; dicho
> identificador ya se encuentra **sellado** desde la Fase 6 en `docs/ARCH.md` (línea 472,
> *Espejeo Físico de Aliases y Axioma Anti-Archivos Fantasma*, referenciado también por
> `src/storage/curation_service.py`). Por axioma de **cero reutilización** de identificadores
> canónicos, el nodo se registra como `[ARCH-1.5.10]` (primer identificador libre tras
> `[ARCH-1.5.9]`), y la referencia `[ARCH-1.5.4]` contenida en el docstring del Juez
> Inmutable `tests/shield/test_shield_cross_market_best_execution.py` queda **mapeada por
> trazabilidad** a `[ARCH-1.5.10]`, sin que ello altere el contenido normativo del nodo.
> Los nodos `[ARCH-1.4.14]` y `[ARCH-1.4.15]` se incorporan en su familia numérica canónica
> (`1.4.x` tras `[ARCH-1.4.13]`) sin colisión. Los identificadores `[ARCH-1.4.11]` y
> `[ARCH-1.6.14]` permanecen **no asignados** (cero reutilización). Juez Inmutable asociado:
> `tests/shield/test_shield_cross_market_best_execution.py` (Twin-Test en Estado RED
> certificado; la materialización en `src/` y `scripts/` queda supeditada a la autorización
> de la Tríada).

### [ARCH-1.5.10-B] Bóveda de Emblemas de Operadores Oficiales y Anti-Hotlinking [ARCH-PILLAR]
* **Ubicación Local Obligatoria:**  
  - Caliente.mx: `/static/img/bookmakers/caliente.png` (descargado desde `https://sports.caliente.mx/es_MX/desktop_header_logo.png`).
  - Betway.mx: `/static/img/bookmakers/betway.svg` (vectorizado oficial del portal).
* El script `sincronizar_boveda_activos.py` debe gestionar la existencia y descarga autónoma de estos recursos locales sin hotlinking externo.

### [ARCH-1.6.17] Resiliencia de Sensores ante Acordeones de Fechas Calendario (Betway) [ARCH-PILLAR]
* En partidos programados a más de 5 días de distancia, las plataformas de apuestas deportivas reemplazan los nombres de días relativos (*"Hoy"*, *"Mañana"*) por cadenas de fecha calendario (ej. *"Viernes 9 Oct"*, *"10/10"*).
* El script `betway_scraper.py` debe expandir acordeones evaluando contención semántica (`el.textContent.includes('oct')`, `el.textContent.includes('vie')`, o elementos con atributos `aria-expanded="false"`), impidiendo que las jornadas futuras queden colapsadas en 0 eventos.

### [ARCH-1.6.15-C] Apertura Dinámica de Jornada en Live Board (sync_service.py) [ARCH-PILLAR]
* En `src/storage/sync_service.py:140`, la variable `jornada_actual` no debe estar quemada en 10.
* Debe resolverse dinámicamente mediante `resolver_jornada_activa_dinamica()`, garantizando que la pantalla «Equipos y Partidos» abra automáticamente en la fecha con partidos `PROGRAMADO` (Jornada 11).

> **Trazabilidad de registro (VARIANCE-01) — Volumen II:** los nodos `[ARCH-1.5.10-B]`,
> `[ARCH-1.6.17]` y `[ARCH-1.6.15-C]` se incorporan como **enmiendas correctivas** ancladas a
> sus nodos matrices sellados (`[ARCH-1.5.10]`, `[ARCH-1.4.6-D]`, `[ARCH-1.6.15]`) sin alterar
> una sola coma de los planos vigentes, y sin colisión con los identificadores previamente
> legislados (`1.5.1`–`1.5.10`, `1.6.0`–`1.6.16`). Los identificadores `[ARCH-1.4.11]` y
> `[ARCH-1.6.14]` permanecen **no asignados** (cero reutilización). Juez Inmutable asociado:
> `tests/shield/test_shield_volume2_consolidation.py` (Twin-Test volumétrico; el estado fáctico
> de sus cuatro sensores se certifica por salida cruda de `pytest` y queda supeditado a la
> autorización de la Tríada para el Paso 3).

### [ARCH-1.5.12] Aprovisionador JIT de Ligas y Bóveda Soberana de Activos de Clubes (`src/normalization/`) [ARCH-PILLAR]
* **Paquete sellado:** `src/normalization/` — `__init__.py`, `gender_guards.py` (implementa `[LN-QBE-095]`), `temporal_disambiguator.py` (implementa `[LN-QBE-094]`), `entity_resolver.py` (jerga oficial → identidad), `asset_vault_service.py` y `league_provisioner.py`.
* **Aprovisionador JIT:** `provisionar_competicion_y_clubes_jit(fotmob_league_id, league_name, country, clubes, session=None, mu_liga=None, season_id=None, season_year=None, season_name=None)` compone EXCLUSIVAMENTE APIs selladas: `registrar_liga_descubierta_si_no_existe()` (`[ARCH-1.4.21]`, *cero ligas zombis*), la convención 3NF `Competition.id = f"FOTMOB_{fotmob_league_id}"` y `macro_gamma_home = 0.15` (`[ARCH-1.5.1]` / `[ARCH-1.6.19-B]`), μ macro desde la propiedad gobernada `League.mu_liga` (`[LN-QBE-089]`) y la identidad categorizada de cada club (`[LN-QBE-095]`). El registro es **idempotente** (clave `fotmob_league_id` / `fotmob_team_id`) y **transaccional** (`write_transaction()` del Gateway, o la sesión del llamador si se provee).
* **Cero invención de identificadores:** el `Season.id` de 3NF **nunca se fabrica**: sólo se registra cuando el llamador aporta el identificador oficial (`season_id`, derivado de metadatos fácticos).
* **Bóveda soberana:** `resolver_uri_activo_local(slug, tipo)` entrega **exclusivamente** URIs locales (`/static/img/crests/…`, `/static/img/leagues/…`) y **levanta excepción ante cualquier URI remota** (prohibición de hotlinking). `auditar_activo_fisico(slug, tipo)` certifica existencia, tamaño ≥ 2,500 bytes y cabecera física real (PNG/SVG/JPEG), erradicando archivos fantasma (`[LN-QBE-019]`).
* **Escalera de escudos:** cuando el activo no está ancorado en la bóveda, el club se persiste con `resolver_escudo_canonico()` (`[LN-QBE-019]`), **jamás** con una URL de terceros.
* **[SHIELD]:** `tests/shield/test_shield_temporal_disambiguation_and_provisioner.py`

> **Trazabilidad de registro (VAR-2026-ARCH-1.5.11 — Colisión resuelta por Decreto de Saneamiento):**
> la Directiva de SPRINT 2 Capa 2 solicitó el identificador `[ARCH-1.5.11]` para este nodo; dicho
> identificador ya se encuentra **sellado** en `docs/ARCH.md` (línea 1204, *Catálogo de Jerga y
> Aliases Globales de Progol (PROGOL_GLOBAL_ALIASES)*, materializado en
> `src/ingestion/progol_resolver.py:25` y `scripts/daemons/centinela_progol.py:31`). Por axioma de
> **cero reutilización**, el nodo se registra como `[ARCH-1.5.12]` (primer identificador libre de la
> familia `1.5.x`, verificado por el pre-vuelo de unicidad del Paso 0) y las referencias textuales
> del nodo `[LN-QBE-095]` y del Juez Inmutable quedan **mapeadas por trazabilidad**, sin alterar una
> coma del contenido normativo. Expediente formal:
> `docs/DIRGEN_VARIANCE_REQUEST_ARCH-1.5.11_COLLISION.md`. Registro maestro: `docs/ID_REGISTRY.md`.
> Juez Inmutable asociado: `tests/shield/test_shield_temporal_disambiguation_and_provisioner.py`.

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
│   │   ├── models.py               # Tablas: League, StandingSnapshot, FixtureSnapshot, PortfolioRecord, Slate, SlateItem
│   │   ├── repository.py           # Operaciones CRUD tipadas
│   │   ├── seeder.py               # Precarga de Ligas Oficiales (Liga MX)
│   │   └── sync_service.py         # Sincronización en arranque FotMob -> DB
│   │
│   ├── ingestion/                  # Capa de Ingesta y Sensores de Mercado
│   │   ├── normalizer.py           # Normalizador difuso de clubes (18 Liga MX + Internacionales)
│   │   ├── schemas.py              # [ARCH-1.4.24] DTOs Pydantic V2 de la Capa 1 (Ingesta Pura)
│   │   ├── caliente_scraper.py     # Extracción headless de cuotas Caliente.mx
│   │   ├── progol_scraper.py       # [LN-QBE-075] Ingesta fáctica Progol (14 Regular + 7 Revancha)
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

> **Nota de trazabilidad (`[ARCH-1.4.24]` / `[LN-QBE-093]`):** los DTOs de la Capa 1 (Ingesta Pura, Data Nexus) residen en `src/ingestion/schemas.py` y se rigen por el contrato hexagonal `[ARCH-1.4.24]`.

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
| `/api/admin/tasks/run` | `POST` | `AdminTaskRequest` | `AdminTaskResponse` | Despacho gobernado de tareas administrativas bajo whitelist estricta ([ARCH-1.4.12]). |
| `/health` | `GET` | — | `{"status": "HEALTHY"}` | Sonda de salud de servidor para auto-lanzador. |

---

## 5. REGLAS DE RESILIENCIA Y MANEJO DE EXCEPCIONES

1. **Safe Zero Divisors (`[ANTI-BUG]`):** Toda división (ej. $1.0 / O$, ratios $SoT / (SoT + SoTA)$) incorpora offset $\epsilon > 0$ o verificación previa (`if denom <= 0: return fallback`).
2. **Invarianza de Clamps (`[ALGO-PROTECTED]`):** Todo multiplicador o factor sintético ($FCF, E_{\text{att}}, \Omega_{\text{perf}}, \theta^*$) debe pasar por funciones `np.clip` o `min/max` antes de ingresar a los modelos de Poisson o Kelly.
3. **Audit Hard-Stop (`[GOVERNANCE]`):** Si `auditor.py` detecta una violación a las 8 Pruebas del Shield, el pipeline lanza `ShieldInvariantException`, abortando la emisión de boletos y la compilación del PDF de forma atómica.
4. **Zero-Mock Policy en Runtime (`[GOVERNANCE-01]`):** Queda prohibida la fabricación de partidos o fechas H2H falsas ante caídas de red. Si una fuente falla, el partido se declara en `CUARENTENA` y se preserva el capital en $0.00 MXN.

---

### [ARCH-1.4.16] Contrato de Atribución Unívoca de Operador en Boletos [ARCH-PILLAR]
* En el payload emitido por el generador de cartera, **todo boleto individual (`boleto_1_seguro` y `boleto_2_ganancia`) debe portar obligatoriamente la propiedad `operador: str` con el slug de la casa correspondiente**, incluso en modalidad mono-operador (`operador: "caliente"` o `"novibet"`).
* Queda terminantemente prohibido que `operador` sea `None` o vacío, impidiendo la degradación al texto plano "VENTANILLA".

### [ARCH-1.3.5] Retiro y Deprecación Definitiva de Rutas Legacy en routes/portfolio.py [ARCH-PILLAR]
* El endpoint `POST /api/portfolio/generate` en `src/web/routes/portfolio.py` queda oficialmente **deprecado y desconectado**. El archivo conserva exclusivamente el servicio de tesis `/api/portfolio/match-thesis`. Toda generación de cartera es gobernada por `src/web/routes/markets.py`.

> **Trazabilidad de registro (VAR-2026-ARCH-1.3.4 — Colisión histórica resuelta por Decreto de Saneamiento):**
> el identificador `[ARCH-1.3.4]` ya se encuentra **sellado** desde la Fase 8 en `docs/ARCH.md`
> (línea 95, *GeminiCognitiveGateway y Ledger Contable de Inferencia*, referenciado por
> `src/services/gemini_gateway.py`, `src/core/sovereign_pipeline.py`, `src/reporting/narrative.py`
> y `tests/shield/test_shield_gemini_gateway.py`). Por axioma de **cero reutilización**, este nodo
> (Retiro de Rutas Legacy) se remapea a `[ARCH-1.3.5]` (primer identificador libre de la familia
> `1.3.x`, verificado por auditoría de unicidad del Paso 0). La referencia `[ARCH-1.3.4]` contenida
> en el docstring y en el mensaje de aserción del Juez Inmutable
> `tests/shield/test_shield_technical_debt_liquidation.py` queda **mapeada por trazabilidad** a
> `[ARCH-1.3.5]`, sin alterar el contenido normativo del nodo.

### [ARCH-1.6.18] Resiliencia de Navegación de Torneo en Sensores de Mercado [ARCH-PILLAR]
* En `betway_scraper.py`, el sensor debe realizar un clic preventivo en el selector de competición de Liga MX antes de leer el DOM, forzando la apertura de la cartelera completa de jornadas futuras (Jornada 11).
* En `novibet_scraper.py`, el `locationId` debe resolverse a través de la API de navegación del operador, tolerando cambios estacionales de identificador sin requerir parches de código.

---

### [ARCH-1.4.17] Contrato de la Distribución Fiduciaria Contraída en el Pipeline de Cartera [ARCH-PILLAR]
* La función `build_plan()` en `src/core/portfolio.py` debe consumir `p_fav` y `p_emp` del contrato extendido, calcular la probabilidad efectiva de éxito $P_{\text{éxito}}'$ y ordenar la cartera antes de dimensionar stakes.
* Se erradica formalmente la clave de ordenamiento muerta `(-(1.0 - x["psi_downside"]), -x["ev_neto_roi"])`.
* **Frontera de mutación:** $\hat{P}_i$ (Poisson 6x6 + 3NF) es INMUTABLE. $\hat{P}_i'$ es variable derivada downstream que vive exclusivamente dentro del motor de cartera (`portfolio_math.py` y `portfolio.py`); queda prohibido sobreescribir la distribución soberana persistida. El resultado viaja como el campo derivado `prob_exito_efectiva` en el payload de partidos aprobados.
* **Alcance de materialización:** el ordenamiento se resuelve con `ordenar_cartera_por_certeza_lexicografica` (`[VAULT-CORE-079-SHRINKAGE]`) sobre `prob_exito_efectiva`, con desempate por `ganancia_neta` descendente.

### [ARCH-1.4.18] Algoritmo de Sizing Monótono Proporcional a la Certeza [ARCH-PILLAR]
* La inversión de cada partido se calcula de forma proporcional a su probabilidad efectiva de éxito:
  $$w_i = \frac{P_{\text{éxito}, i}'}{\sum_{j=1}^K P_{\text{éxito}, j}'}$$
  forzando la condición $B_{(1)} \ge B_{(2)} \ge \dots \ge B_{(K)}$ y aplicando los hard-caps del 8% individual y 25% de cartera total.
* **Erradicación formal:** el piso `max(0.02, f_kelly)` y la bolsa heurística `bolsa_core = bankroll · min(0.25, 0.06·K)` quedan extintos como generadores de tamaño (deuda técnica). El piso operativo subsistente es el de ventanilla `PISO_MINIMO_BOLETO = 2.00` (`[LN-QBE-071]`).
* **Conciliación con `[LN-QBE-070-B]`:** `calcular_kelly_atenuado` subsiste en `build_plan()` exclusivamente como **cota analítica de auditoría NO vinculante** (control TD-COR-01, exigido por el AST de `tests/shield/test_shield_technical_debt_liquidation.py`) y se reporta en `control_portafolio.desglose_bankroll.auditoria_kelly_atenuado`. Ningún peso de cartera se deriva de Kelly.
* **Orden de aplicación:** (1) contracción `[LN-QBE-079]` → (2) orden lexicográfico `[LN-QBE-081]` → (3) sizing monótono `[LN-QBE-082]` → (4) hard-caps constitucionales `[LN-QBE-070-B]` + piso de ventanilla `[LN-QBE-071]`.
* **[SHIELD]:** `tests/shield/test_shield_fiduciary_shrinkage_and_monotonic_ordering.py` y `tests/shield/test_shield_technical_debt_liquidation.py`.

### [ARCH-1.4.19] Monotonía Estricta Post-Dutching en PortfolioEngine.build_plan() [ARCH-PILLAR]
* **Problema:** El escalamiento a piso de ventanilla ($\$2.00\text{ MXN}$) y el recálculo $B_{\text{seg}} \times O_{\text{emp}}$ para garantizar $V=0$ pueden re-inflar el monto de un partido inferior, rompiendo la jerarquía monetaria de certeza.
* **Mecanismo Obligatorio:** Tras resolver las piernas split de cada orden, el motor debe aplicar un **segundo pase de monotonía no creciente**:
  $$B_{(1)} \ge B_{(2)} \ge \dots \ge B_{(K)}$$
  Si $B_{(i)} > B_{(i-1)}$, se trunca $B_{(i)} = B_{(i-1)}$ y se recalculan proporcionalmente $B_{\text{seg}}$ y $B_{\text{prio}}$ preservando el piso de $\$2.00$ y la indemnidad $V=0$.

### [ARCH-1.4.20] Contrato de Datos del Optimizador de Masa P' en progol_math.py [ARCH-PILLAR]
* **Módulo Canónico:** `src/core/contracts/progol_math.py`
* **Régimen:** `[DIRGEN-STRICT]` (Plano sellado en `docs/DIRGEN_VAULT.md`).
* **Responsabilidad:** Biblioteca matemática pura libre de dependencias I/O o heurísticas de "vibe coding".
* **Firmas Canónicas Obligatorias** *(dictamen VARIANZA V-1 / ALT-1 — paridad 1:1 absoluta con `[VAULT-CORE-084-PROGOL-P-PRIME]` y el Juez Inmutable)*:
  - `seleccionar_cobertura_binaria_optima(partidos_14: List[dict]) -> List[dict]`
  - `generar_universo_restringido_y_ordenar_p_prime(partidos_14: List[dict]) -> List[Tuple[tuple, float]]`
  - `seleccionar_primeras_m_combinaciones(p_prime_ordenado: List[Tuple[tuple, float]], m_cupo: int) -> Tuple[List[dict], float]`
  - `reducir_a_garantia_hamming_l(p_prime_ordenado: List[Tuple[tuple, float]], l_aciertos_objetivo: int = 13, max_boletas: int = 16) -> List[Dict[str, Any]]`
  - `optimizar_quiniela_progol_soberana(partidos_14: List[dict], presupuesto_mxn: float = 360.0, l_objetivo: int = 14) -> dict`
* **Frontera de inmutabilidad:** el nodo sellado `[LN-QBE-074]` (`optimizar_quiniela_por_presupuesto`, `progol_math.py:48-162`) y `[LN-QBE-037]` (`calcular_sesgo_quiniela`) permanecen INTACTOS; la inyección es estrictamente aditiva (5 símbolos nuevos).
* **Nota de trazabilidad (VARIANZA V-1 / ALT-1):** el resumen inicial de este nodo declaraba `reducir_a_garantia_hamming_l(combinaciones_m: List[dict], l_objetivo: int) -> List[dict]` y `optimizar_quiniela_progol_soberana(partidos_14, presupuesto_mxn)`; el dictamen ratifica el contrato de facto del plano sellado y del Juez (defaults `l_aciertos_objetivo=13`, `max_boletas=16`, `l_objetivo=14`), evitando el falso fallo por `TypeError`.
* **[SHIELD]:** `tests/shield/test_shield_progol_p_prime_mass_optimizer.py`

### [ARCH-1.4.21] Arquitectura de Ingesta Just-In-Time (JIT) Multi-Torneo [ARCH-PILLAR]
* **Principio de Cero Ligas Zombis:** El sistema no almacena ni raspa ligas que no estén en juego. La ingesta se dispara exclusivamente por demanda guiada por el concurso oficial activo de Progol (`slates`).
* **Módulo:** `src/ingestion/progol_resolver.py`
  - Expone `resolver_casillas_concurso_jit(casillas_raw: List[dict]) -> Dict[str, Any]`.
  - Agrupa las ligas descubiertas y registra transaccionalmente en la tabla `leagues` aquellas que no existan previamente en SQLite.

### [ARCH-1.6.19] Desacoplamiento Multi-Liga del Centinela Deportivo [ARCH-PILLAR]
* Se deroga la constante rígida `LEAGUE_ID = 262` en `centinela_deportivo.py`.
* El Centinela Deportivo incorpora el modo `--todas-las-ligas`:
  1. Consulta `League.all()` en `PersistenceGateway.read_session()`.
  2. Descarga secuencialmente el JSON de temporada de FotMob para cada liga registrada.
  3. Reconstruye tablas acumuladas (`StandingSnapshot`), partidos (`Match`) y calcula las distribuciones soberanas (`SovereignDistribution`) para todos los encuentros de las ligas activas.

### [ARCH-1.6.19-B] Ingesta y Parser Genérico de Temporadas FotMob [ARCH-PILLAR]
* **Endpoint de Ingesta:** `https://www.fotmob.com/api/leagues?id={fotmob_id}`
* **Estandarización Universal:** Toda competición registrada en SQLite (LaLiga **87**, Premier League **47**, LaLiga2 **140**, Argentina **112**, Série A Brasil **268**, Nations League, etc.) debe poder procesarse mediante un parser genérico que extraiga:
  1. Tabla de posiciones actual (`table` / `standings`).
  2. Fixtures completos de la temporada (`matches`).
  3. Metadatos de goles esperados ($xG$) cuando estén disponibles en Opta.
* **Cero Degradación Silenciosa:** Se deroga la degradación vacía para `fotmob_id != 262`. Toda liga activa debe intentar la descarga fáctica antes de emitir log de estado.
* **Materialización Canónica (`[DIRGEN-STRICT]` — `scripts/daemons/centinela_deportivo.py`):**
  - `parsear_json_liga_fotmob_generico(payload: Dict[str, Any], fotmob_id: int) -> Dict[str, Any]` — transcrita VERBATIM del dictamen (Fase 8.2).
  - `descargar_json_liga_fotmob(fotmob_id: int) -> Dict[str, Any]` — transporte httpx (timeout 15 s, headers de navegador).
  - `persistir_temporada_generica(...)` — persiste `Competition` (`FOTMOB_{fotmob_id}`), `Match`, `StandingSnapshot`, `FixtureSnapshot` y las `SovereignDistribution` de los partidos activos mediante el puente gobernado `sincronizar_distribuciones_soberanas_partidos` (canon Vol. I; μ dinámica `[LN-QBE-089]`).
  - `sincronizar_temporada_completa(league_id != 262)` enruta a la ingesta genérica (derogada la degradación vacía previa `[ARCH-1.6.19-A]`).
* **Nota de trazabilidad (SONDEO-01 — hallazgo fáctico 2026-10-01, **DICTAMINADO Y APLICADO — ALT-1**, expediente `docs/DIRGEN_VARIANCE_REQUEST_ARCH-1.6.19-B_ENDPOINT.md`):** el endpoint legislado `https://www.fotmob.com/api/leagues?id={id}` responde **HTTP 404** (`text/html`) ante headers de navegador, `Referer` y `x-mas`, **incluido el control `id=262` (Liga MX)**. La página canónica de liga (`https://www.fotmob.com/es-419/leagues/{id}/overview/{slug}`) responde **HTTP 200** y embebe el JSON de Next.js (`__NEXT_DATA__`) que contiene `table[0].data.table.all`, `fixtures.allMatches` (380 partidos) y `scoresStr` **en la forma exacta que consume el parser sellado**. Artefacto formal: `docs/DIRGEN_VARIANCE_REQUEST_ARCH-1.6.19-B_ENDPOINT.md` (ALT-1: extracción `__NEXT_DATA__`, técnica ya gobernada por `[VAULT-DAEMON-001-B]`; ALT-2: credencial `x-mas` administrada por el Director). Adicionalmente, el identificador `47` corresponde fácticamente a **Premier League** (LaLiga = **87** en FotMob), no a LaLiga. Sondeo 2026-10-01: **112 = Liga Profesional Argentina**, **140 = LaLiga2**, **268 = Série A (Brasil)** (el ejemplo "Argentina 268" de `[ARCH-1.6.19-B]` era incorrecto). Validación en vivo post-dictamen: 4 competiciones ingeridas por `__NEXT_DATA__` ⇒ bóveda en `leagues` 5, `matches` 1789, `sovereign_distributions` 808; casillas del concurso 2353 `GIRONA vs MALLORCA` (match 5868476) y `CORDOBA vs TENERIFE` (match 5868474) vinculadas a distribución física real (LaLiga2, J8).
* **Nota de trazabilidad (SONDEO-02):** el contrato sellado del parser no emite `pg`/`pe`/`pp`, `forma`, marcadores por fixture ni $xG$; en consecuencia `current_team_standings` y las tablas históricas por jornada NO se pueblan para competiciones descubiertas (cero invención `[GOVERNANCE-01]`), y las `SovereignDistribution` se alimentan con `{pj, gf, gc}` dejando que el canon Vol. I (§4.5) aplique su propio respaldo de $xG$ cuando Opta no lo suministra.
* **[SHIELD]:** `tests/shield/test_shield_jit_competition_discovery.py`

### [ARCH-1.4.22] Disparo JIT de Descubrimiento en centinela_progol.py [ARCH-PILLAR]
* Al procesar cada una de las 21 casillas de Progol:
  1. El centinela consulta el resolver semántico (`progol_resolver.py`).
  2. Si el partido pertenece a una competición que aún no existe en SQLite, la inscribe atómicamente en la tabla `leagues` mediante `registrar_liga_descubierta_si_no_existe()`.
  3. Esto deja la base de datos lista para que el Centinela Deportivo descargue los datos de esas ligas en la siguiente fase de la cadena.
* **Materialización Canónica (`scripts/daemons/centinela_progol.py`):** `disparar_descubrimiento_jit(tx, analisis, cache)` se invoca al cierre de cada casilla que degradó al Prior (Caso B), con caché de corrida por club y degradación explícita ante fallo de red: la ingesta del concurso JAMÁS se interrumpe (`[LN-QBE-075]`).
* **Nota de trazabilidad (SONDEO-03 — ABIERTO: mitigación operativa aplicada, **ALT-3 pendiente de autorización**):** el endpoint legislado `https://www.fotmob.com/api/search/searchapi?term={club}` responde **HTTP 404** (`text/html`) en el entorno de materialización (misma causa raíz que SONDEO-01). El disparo JIT queda operativo y no bloqueante, con degradación explícita a log (medición viva 2026-10-01: las 21 casillas del concurso 2353 cerraron en Prior, `leagues` sin altas automáticas). Mitigación operativa aplicada sin tocar código: registro de las competiciones **en juego** por el API sellado `registrar_liga_descubierta_si_no_existe()` (`[ARCH-1.4.21]`, *cero ligas zombis*) con ids verificados fácticamente; ver `docs/DIRGEN_VARIANCE_REQUEST_ARCH-1.6.19-B_ENDPOINT.md` (SONDEO-04 registra la dependencia dura de `persistir_temporada_generica` respecto de `leagues`).


### [ARCH-1.4.23] Sensor de Ingesta Oficial de Liga Premier FMF (ligapremier.mx) [ARCH-PILLAR]
* **Fuente Oficial:** `https://ligapremier.mx/estadisticas` y `https://ligapremier.mx/resultados/`
* **Módulo:** `src/ingestion/ligapremier_scraper.py` (`LigaPremierScraper`)
* **Responsabilidad:**
  1. Extraer la tabla de posiciones oficial de Serie A / Serie B (`JJ, G, E, P, GF, GC, PTS`).
  2. Extraer los marcadores de las jornadas disputadas (J1 a J5).
  3. Registrar la competición `MEX_LIGAPREMIER` en SQLite 3NF con $\mu_{\text{premier}} = 2.45$ y $\bar{\gamma}_{\text{home}} = 0.16$.
* **[SHIELD]:** `tests/shield/test_shield_ligapremier_and_global_aliases.py`

### [ARCH-1.4.24] Contrato Hexagonal de Proveedores de Ingesta Pura y DTOs (Capa 1) [ARCH-PILLAR]
La extracción de datos crudos se encapsula en proveedores sin estado y sus respuestas se tipifican rigurosamente mediante Data Transfer Objects (DTOs).

* **Directiva de Directorios (Capa 1):**
    * `src/ingestion/providers/`: Aloja exclusivamente sensores de red/API. Prohibido el acceso a la capa de persistencia.
    * `src/ingestion/schemas.py`: Contiene exclusivamente las declaraciones DTO (Pydantic V2) para transporte de datos.
* **Inyección de Dependencias:** Cualquier requerimiento de datos históricos o de persistencia debe ser satisfecho mediante inyección de dependencias desde el llamador (ej. `fallback_loader`), nunca mediante acoplamiento estático interno.
* **Invariante de Pureza (`[LN-QBE-093]`):** Ningún archivo dentro de `src/ingestion/providers/` puede importar `src.storage`, `sqlalchemy` ni realizar I/O de escritura a disco.
* **Nota de trazabilidad (VAR-2026-ARCH-1.4.24 — Resolución de colisión, **ALT-A ratificada**):** el identificador `[ARCH-1.4.23]` está sellado por el Sensor de Ingesta Oficial de Liga Premier FMF (`ligapremier.mx`); conforme al principio *"sin reutilización de identificadores"*, la Capa 1 Data Nexus se promulga como **`[ARCH-1.4.24]`** (nodo `[LN-QBE-093]`). La tensión legislativa entre el axioma de aislamiento y el fallback offline certificado de `[LN-QBE-017]` se resuelve por **Inversión de Dependencias**: el puerto `fallback_loader` se inyecta desde el llamador y su adaptador de lectura reside en `src/storage/repository.py` (`cargar_snapshot_certificado_posiciones`). La capacidad offline **NO se deroga**.
* **[SHIELD]:** `tests/shield/test_shield_data_nexus_providers.py`

### [ARCH-1.4.25] Módulo de Normalización, Jerga y Desambiguación (`src/normalization/`) [ARCH-PILLAR]
La Capa 2 encapsula la inteligencia de resolución de entidades en un paquete autónomo:
* `src/normalization/gender_guards.py`: Implementa `[LN-QBE-095]`.
* `src/normalization/temporal_disambiguator.py`: Implementa `[LN-QBE-094]`.
* `src/normalization/entity_resolver.py`: Mapea jerga de quinielas (`PROGOL_GLOBAL_ALIASES`) a identidades oficiales.

### [ARCH-1.6.20] Actualización de Endpoint de Búsqueda FotMob (/searchapi/suggest) [ARCH-PILLAR]
* En `src/ingestion/progol_resolver.py`, se actualiza la URL del resolver semántico:
  `https://www.fotmob.com/api/searchapi/suggest?term={club_sanitizado}`
  sustituyendo el endpoint deprecado `/api/search/searchapi` para erradicar los errores 404.
* **[SHIELD]:** `tests/shield/test_shield_ligapremier_and_global_aliases.py`

### [ARCH-1.5.11] Catálogo de Jerga y Aliases Globales de Progol (PROGOL_GLOBAL_ALIASES) [ARCH-PILLAR]
* Se formaliza el diccionario de traducción determinista para las 21 casillas en `progol_resolver.py`:
  - `"VERACRUZ"` $\to$ `"Racing de Veracruz"`
  - `"OAXACA"` $\to$ `"Chapulineros de Oaxaca"`
  - `"DURANGO"` $\to$ `"Alacranes de Durango"`
  - `"ZACATECAS"` $\to$ `"Zacatepec"` (o `"Mineros de Zacatecas"`)
  - `"CANCUN"` $\to$ `"Cancún FC"` | `"TAPATIO"` $\to$ `"Tapatío"`
  - `"AGUILAS F"` $\to$ `"Club América Femenil"` | `"RAYADOS DE MONTERREY"` (en Femenil) $\to$ `"CF Monterrey Femenil"`
  - `"MILAN F"` $\to$ `"AC Milan Femenil"` | `"JUVENTUS F"` $\to$ `"Juventus Femenil"`
  - `"R SOCIED. B"` $\to$ `"Real Sociedad B"` | `"E.U.A."` $\to$ `"USA"`
* **[SHIELD]:** `tests/shield/test_shield_ligapremier_and_global_aliases.py`

---

**BASE DE GOBIERNO SELLADA BAJO EL KYBERN FRAMEWORK v8.0 / v12.0 — ARQUITECTURA TÉCNICA INMUTABLE.**

```