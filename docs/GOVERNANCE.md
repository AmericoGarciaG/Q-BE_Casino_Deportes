```markdown
# Q-BE Casino Deportes — Governance Book (GOVERNANCE.md)
**Versión:** 12.0 (Kybern Industrial - Production Multi-Engine Edition)  
**Estado:** [ALGO-PROTECTED] - Base de Gobierno Sellada (2026-09)  
**Proyecto:** `Q_BE_CD_WEB` (Quantitative Betting Engine — Web Platform)  
**Autoridad Suprema:** Américo García Guerrero (Director Humano)  
**Fuente de Verdad:** Kybern Framework v8.0 / v12.0 + Protocolo Nexus

Este documento define **CÓMO TRABAJAMOS**. Es la constitución operativa, metodológica y técnica absoluta para el desarrollo, auditoría y evolución del sistema `Q_BE_CD_WEB` bajo el estándar **Kybern Framework v8.0 / v12.0**.

---

## 1. PRINCIPIO RECTOR Y FILOSOFÍA DE INGENIERÍA

### 1.1 Axioma Central de Soberanía Intelectual
> **"El código fuente es un subproducto fungible, transitorio y reemplazable; la Intención Legislada (Lógica de Negocio y Restricciones Matemáticas) en la Base de Gobierno es el único activo institucional permanente, inmutable y soberano."**

En la era de la Inteligencia Artificial Generativa, el desarrollo no gobernado ("Vibe Coding") introduce entropía y riesgo sistémico. `Q_BE_CD_WEB` opera bajo una separación estricta entre la **Inteligencia** (el modelo generativo como extractor semántico y redactor didáctico) y la **Gobernanza** (el servidor y motor determinista como ejecutores matemáticos inquebrantables).

### 1.2 Principio del Sándwich Neuro-Simbólico Invertido
1. **Sensor Fáctico Estructurado Primario:** Extracción determinista de datos duros (tablas, xG Opta, forma reciente y cuotas) mediante APIs REST estructuradas (FotMob) y scrapers especializados con 0% de consumo de tokens y cero alucinaciones.
2. **Enforcer Matemático Determinista (Motor Central):** Código Python puro (`src/core/`) que ejecuta cálculos de Poisson bivariado 6x6, derivadas de Breakeven ($\theta^*$), filtros booleanos del Catálogo, dimensionamiento de Kelly y verificación de invarianzas numéricas.
3. **Inferencia Asistida y Auditoría (Capa Superior):** Modelos de lenguaje (Gemini 3.6 Flash con Google Search Grounding) operando exclusivamente como auditores de noticias de última hora y redactores pedagógicos de la Tesis Q-BE en 4 viñetas.

### 1.3 Axioma de Cero Datos Sintéticos en Producción [GOVERNANCE-01] [ANTI-BUG]
> **"Queda terminantemente prohibido que una rutina de contingencia, sensor de ingesta o script de fallback fabrique, simule o invente datos deportivos sintéticos (marcadores ficticios, fechas arbitrarias o estadísticas simuladas) en tiempo de ejecución."**

Si un conector de API externa, scraper o sensor de búsqueda falla en recuperar la información fáctica real (10P, H2H o bajas), el sistema DEBE:
1. Activar el estado formal de `CUARENTENA_DATOS_INSUFICIENTES` y registrar la anomalía.
2. Lanzar `DataQuarantineException(QBE-00)` por falta de evidencia fáctica, vetando el partido de la cartera.
3. Preservar el capital en riesgo en $0.00 MXN.

La inyección de datos mockeados o simulados en producción se clasifica como **Violación Crítica de Integridad Institucional**, sujeta a reversión inmediata de código.

### 1.5 Axioma de Abstracción Universal y No-Sobreajuste [GOVERNANCE-02] [ANTI-BUG]
> **"Queda terminantemente prohibido codificar reglas condicionales particulares sobreajustadas a partidos, equipos o resultados específicos de una fecha en disputa."**

Toda rutina de scraping, parsing o procesamiento estocástico debe ser una **función general abstracta** capaz de gobernar $N$ elementos dinámicos ($N \ge 0$). Los partidos, marcadores o fechas particulares de una jornada activa actúan exclusivamente como **instancias de prueba fácticas para verificar la ley general**, jamás como constantes o condicionales rígidos en el código fuente de producción.

### 1.4 Mandato de Fallo Ruidoso (Fail-Loud Mandate) [GOVERNANCE] [ARCH-PILLAR]
En sistemas financieros y cuantitativos de asignación de capital, **la degradación silenciosa es inaceptable**. Quedan estrictamente prohibidas las capturas genéricas de error (`except Exception: return fallback_data()`) que oculten fallos de conexión inventando estados ficticios. Es preferible que un proceso falle de forma explícita y visible a que opere con datos corruptos.

### 1.6 Umbral de Integridad Fail-Loud para Ingestas Externas [GOVERNANCE-03] [ARCH-PILLAR]

* **Axioma de Integridad de Catálogo:** Si una rutina de extracción de datos vivos (FotMob o Liga MX) retorna un conjunto de clubes inferior a 15 entidades (`len(datos) < 15`), el sistema tiene estrictamente prohibido parchar los registros faltantes con datos sintéticos.
* **Acción Inmediata:** La rutina debe lanzar `RuntimeError("FAIL-LOUD: Ingesta incompleta detectada")`, preservando el estado previo certificado en SQLite y manteniendo el capital en riesgo en $0.00 MXN.

---

## 2. ESTRUCTURA DE AUTORIDAD FUNCIONAL (LA TRÍADA)

Para garantizar la sostenibilidad operativa y eliminar la dilución de responsabilidades en flujos asistidos por IA, se legisla la siguiente jerarquía de autoridad:

```text
  ┌────────────────────────────────────────────────────────┐
  │         1. LA FUENTE DE LA INTENCIÓN (Director)        │ ➔ Visión, Presupuesto, Veto Absoluto
  └───────────────────────────┬────────────────────────────┘
                              │ (Intención de Negocio)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │       2. EL TRADUCTOR DE INTENCIÓN (Arquitecto)        │ ➔ Leyes (BG), Nodos IPO, Jueces Inmutables
  └───────────────────────────┬────────────────────────────┘
                              │ (Contratos y Twin-Tests)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │        3. EL EJECUTOR GOBERNADO (Constructor IA)       │ ➔ Materialización de Código (src/)
  └───────────────────────────┬────────────────────────────┘
                              │ (Inspección Automática)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │        4. EL ESCUDO FORENSE (The Shield - AST/DOM)     │ ➔ Detección de Mocks y Hardcodes
  └────────────────────────────────────────────────────────┘
```

1. **La Fuente de la Intención (Director Humano — Américo García Guerrero):**
   * Define los objetivos financieros, los límites de riesgo, las reglas de asignación, los presupuestos y las prioridades de plataforma.
   * Asume la responsabilidad fiduciaria última y posee **poder de veto absoluto** sobre cualquier cambio en el sistema.
2. **El Traductor de Intención (Arquitecto de Sistema — Instancia IA):**
   * Traduce la visión del Director en **Nodos Lógicos IPO (`[LN-QBE-XXX]`)**, contratos de API y formalismos matemáticos.
   * Diseña los **Jueces Inmutables (Twin-Tests)**, custodia los 4 libros de la Base de Gobierno (`docs/`) y audita la observabilidad del sistema.
3. **El Ejecutor Gobernado (Agente Constructor — Instancia IA):**
   * Entidad algorítmica responsable de la materialización táctica del código en `src/`.
   * Carece de autoridad para alterar la lógica, crear constantes rígidas o modificar contratos. Su éxito se mide exclusivamente por la satisfacción del Juez Inmutable (`Exit Code 0`).
4. **El Escudo Forense (The Shield):**
   * Capa de validación automatizada que intercepta y bloquea cualquier intento de hardcodeo o manipulación de pruebas antes del despliegue.

---

## 3. EL ESTÁNDAR "PROTOCOLO NEXUS" (TOPOLOGÍA FULL-STACK WEB)

El proyecto `Q_BE_CD_WEB` adopta la topología de **Monolito Full-Stack Local Gobernado**:

```text
Q_BE_CD_WEB/
├── run_app.py                  # Entrypoint: Uvicorn + Auto-Browser Launch
├── requirements.txt            # Dependencias oficiales inmutables
├── .env                        # Credenciales locales seguras
│
├── docs/                       # BASE DE GOBIERNO (Única Fuente de Verdad)
│   ├── GOVERNANCE.md           # Constitución Operativa y Tríada
│   ├── ARCH.md                 # Arquitectura Técnica y Contratos REST
│   ├── LOGIC.md                # Grafo Lógico IPO Matemático
│   └── DESIGN.md               # Tokens Visuales y Geometría DOM
│
├── src/                        # CÓDIGO FUENTE MODULAR
│   ├── web/                    # Capa de Aplicación Web Local (FastAPI + SPA)
│   ├── storage/                # Persistencia Local (SQLite + SQLAlchemy)
│   ├── ingestion/              # Sensores de Mercado (FotMob, Caliente, Gemini)
│   ├── core/                   # Motores Matemáticos Puros [ALGO-PROTECTED]
│   ├── models/                 # Contratos Pydantic V2 Fuertemente Tipados
│   └── reporting/              # Motor de Reportes y Compilación Playwright A4
│
├── tests/                      # THE SHIELD (Escudo de Calidad Inmutable)
│   ├── conftest.py             # Fixtures oficiales
│   └── shield/                 # Jueces Abstractos y Concretos
│
└── data/                       # ALMACENAMIENTO PERSISTENTE LOCAL
    ├── input/                  # Capturas y slates de entrada
    ├── output/                 # Reportes y PDFs generados
    └── qbe_database.db         # Base de datos SQLite local
```

### 3.1 Regla de Oro de Comunicación Modular
> **Un submódulo de `src/core/` jamás realiza I/O (llamadas de red, lecturas de base de datos o acceso a disco) ni importa lógica de capas superiores (`web/` o `reporting/`); es una librería matemática pura y sin estado (`Input` $\rightarrow$ `Output`).**

---

## 4. FLUJO DE TRABAJO OPERATIVO (EL MOTOR DE 3 PASOS)

Todo cambio estructural en `Q_BE_CD_WEB` DEBE ejecutarse mediante el **Motor de 3 Pasos**:

```text
  [PASO 1: LEGISLACIÓN]        [PASO 2: JUEZ INMUTABLE]        [PASO 3: MATERIALIZACIÓN]
    Edición en docs/       ➔    Creación de Twin-Test     ➔     Código en src/ hasta
  (CERO código en src/)         Abstracto en tests/shield/        alcanzar EXIT CODE 0
```

### Entregable 1: La Legislación (Dominio Teórico)
* **Regla:** CERO líneas de código de producción (`src/`) pueden ser modificadas en esta fase.
* **Acción:** El Arquitecto redacta o modifica los Nodos Lógicos en `docs/LOGIC.md`, `ARCH.md` o `DESIGN.md`, documentando la regla formal, el contrato IPO y la etiqueta `[Binding Rationale]`.
* **Mandato:** El Agente Constructor asimila el contexto antes de programar (`[KYBERN-OP-01]`).

### Entregable 2: El Juez Inmutable (Dominio Contractual)
* **Regla:** CERO líneas de código de producción (`src/`) pueden ser modificadas en esta fase.
* **Acción:** Se diseña una clase abstracta de prueba (`abstract_test_*.py` en `tests/shield/`) que encapsula métodos, datos mockeados inmutables y aserciones matemáticas y geométricas.
* **Comportamiento:** El test DEBE fallar (`RED`), demostrando la inexistencia de la funcionalidad o la presencia del bug antes de la intervención.

### Entregable 3: La Materialización (Dominio Táctico)
* **Regla:** Se autoriza la modificación de `src/`.
* **Acción:** El Agente Constructor implementa el código en `src/` y la clase concreta que hereda del Juez Abstracto.
* **Cierre de Bucle Ético:** El ciclo concluye ÚNICAMENTE cuando la suite completa de pruebas retorna `Green State (Exit Code 0)`, se ejecuta la auditoría perimetral contra regresiones y se valida que no existan hardcodes.

### 4.1 El Motor de 3 Pasos Extendido (Régimen Dual-Track)
Para equilibrar la agilidad en la capa de presentación con el rigor extremo en la capa financiera, todo ciclo de desarrollo se bifurca según su Régimen de Gobernanza:

1. **Vía A: Régimen [DBBD-FUNGIBLE] (UI, CSS, Templates, Utilidades):**
   * *Paso 1 (Legislación):* Definición de contratos IPO y reglas visuales en `docs/`.
   * *Paso 2 (Juez Inmutable):* Clase abstracta `abc.ABC` con validaciones funcionales y Sad Paths.
   * *Paso 3 (Materialización):* Autonomía táctica iterativa del Constructor en `src/` hasta `Exit Code 0`.
2. **Vía B: Régimen [DIRGEN-STRICT] (Matemática Pura, Poisson, André, Kelly, Persistencia):**
   * *Paso 1 (Legislación + Bóveda):* Contrato IPO + Transcripción Canónica exacta en `docs/DIRGEN_VAULT.md`.
   * *Paso 2 (Juez + Guardián AST):* Test funcional numérico + Verificador criptográfico de integridad (SHA-256 / AST).
   * *Paso 3 (Materialización Fiel):* Transcripción determinista al código de producción. Cero tolerancia a modificaciones arbitrarias.

### 4.2 Protocolo Anti-Bandazos (Single-Strike Constraint)
En componentes bajo `[DIRGEN-STRICT]`, queda estrictamente prohibido el ensayo y error iterativo autónomo. Ante el primer fallo de compilación o ejecución, el Constructor debe detenerse de inmediato y emitir el artefacto `DIRGEN_VARIANCE_REQUEST.md` detallando coordenadas, traceback, diagnóstico causal, abanico de 2 alternativas evaluadas y diff propuesto, esperando resolución de la Dirección.

### 4.3 Protocolo de Gestión Cognitiva y Ventana Limpia [GOV-LLM-01]
En flujos asistidos por `gemini-3.6-flash`, toda característica mayor debe iniciarse en una ventana de contexto limpia. Si una implementación desvía su esfuerzo en $\ge 50\%$ o entra en bucles de parches, se descarta la ventana y se inicia una nueva sesión limpia ejecutando la directiva de arranque de `AGENTS.md`.

---

## 5. TAXONOMÍA DE INCIDENTES Y RUTAS DE RESOLUCIÓN

### 5.1 Fallo de Implementación (Error de Dedo)
* **Definición:** Desviaciones sintácticas, `ImportError`, errores de tipado Pydantic, nombres de variables mal escritos o rutas de archivos incorrectas.
* **Vía de Resolución:** **Corrección Directa (Fast-Track).** El Agente Constructor repara la línea específica de forma atómica e inmediata sin necesidad de legislar en la BG.

### 5.2 Fallo de Lógica de Negocio o Regresión Estructural
* **Definición:** Violación de invariantes matemáticas (ej. sumatoria de probabilidades $\ne 1.0$, alteración de fórmulas de Poisson, hardcodeo de ganancias esperadas, o desalineación geométrica de tablas).
* **Vía de Resolución:** **Asedio Metodológico (Motor de 3 Pasos Obligatorio).** Prohibida la corrección directa sin antes legislar y crear el test abstracto.

### 5.3 Matriz de Fases y Roadmap Operativo (v12.0)

```text
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                              MATRIZ DE FASES Q_BE_CD_WEB (v12.0)                       │
 ├──────────┬──────────────────────────────────────────┬───────────┬──────────────────────┤
 │ FASE     │ ALCANCE PRINCIPAL                        │ ESTADO    │ IMPACTO EN PRODUCTO  │
 ├──────────┼──────────────────────────────────────────┼───────────┼──────────────────────┤
 │ FASE 0   │ Cimientos Web y Purga Crisol             │ ✅ SELLADA│ Monolito FastAPI+DB  │
 │ FASE 1   │ Curación Agéntica y Bóveda Soberana      │ ✅ SELLADA│ 18 escudos FMF disco │
 │ FASE 2   │ Ingesta Real ligamx/Caliente & Cache-1st │ ✅ SELLADA│ Cero mocks, <20ms BD │
 │ FASE 3   │ Despacho Cuantitativo, Poisson y Dutching│ ✅ SELLADA│ Portafolio activo,   │
 │          │ (Stress-Testing, Piso $2.00 y HUD)       │           │ Boletos V=0, 3 Vistas│
 ├──────────┼──────────────────────────────────────────┼───────────┼──────────────────────┤
 │ FASE 4   │ Selector Multi-Jornada (J8 vs J9) y      │ 🚀 SIGUIE-│ Conmutación de fecha │
 │          │ Orquestación StateGraph / LangGraph      │ NTE FRENTE│ y agentes paralelos. │
 │ FASE 5   │ Consola Bankroll, Slippage y Vaquita     │ 📋 Planeado│ WhatsApp & Sindicato │
 │ FASE 6   │ Expansión Multi-Torneo Internacional     │ 📋 Planeado│ Premier / Champions  │
 │ FASE 7   │ PM-FACE: Calibración y Brier Score       │ 📋 Bases  │ MatchdayState activo │
 │ FASE 8   │ Ejecución Desatendida In-Play            │ 🔭 Visión │ Apuestas automáticas │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. ETIQUETAS DE PRESERVACIÓN DE INTENCIÓN (BINDING RATIONALE)

Toda definición técnica crítica en la documentación y en el código fuente DEBE portar una etiqueta de justificación:

* `[BIZ-LOGIC]`: Regla matemática o financiera central del modelo Q-BE (Poisson, Dutching, Kelly, $\theta^*$). Prohíbe refactorizaciones que alteren el resultado económico.
* `[ANTI-BUG]`: Medida preventiva institucionalizada tras un error histórico (ej. división por cero en cuotas, safe nulls, prohibición de mocks en producción).
* `[ARCH-PILLAR]`: Pilar estructural no negociable (ej. inmutabilidad de esquemas Pydantic, pureza stateless de `src/core/`).
* `[ALGO-PROTECTED]`: Fórmulas matemáticas, derivadas de equilibrio y Clamps explícitamente sellados contra modificación no autorizada por el Director.
* `[GOVERNANCE]`: Reglas operativas del equipo, de la Tríada y de los protocolos de auditoría.
* `[UX-MANDATE]`: Requisitos estrictos de presentación visual, geometría de tablas y experiencia de usuario.

---

## 7. EL ESCUDO DE CALIDAD (THE SHIELD — LAS 8 PRUEBAS DE INVARIANZA)

> **"Un código sin test es un código que no existe."**

Ninguna orden de inversión ni reporte interactivo puede ser despachado sin superar las **8 Pruebas de Invarianza Numérica y Estructural**:

```text
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                    LAS 8 PRUEBAS DE INVARIANZA NUMÉRICA Y GEOMETRÍA (SHIELD)           │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ 1. Test de Simplex de Probabilidad  ➔ |(P_Fav + P_Emp + P_Und) - 1.0000| <= 0.001       │
 │ 2. Invarianza en Tablas (Dutching)  ➔ |Retorno_Seguro - Inversion_Total| <= $0.05 MXN  │
 │ 3. Hard-Cap Individual por Activo   ➔ Inversion_Partido <= Bankroll * 0.0801 (<= 8.0%) │
 │ 4. Hard-Cap Global de la Cartera    ➔ Sum(Inversiones) <= Bankroll * 0.2501 (<= 25.0%) │
 │ 5. Colchón Financiero Satélite      ➔ Sum(Ganancias_Core) >= 3.0 * Monto_Satelite      │
 │ 6. Linaje y Anclaje a Tabla Maestra ➔ Paridad 100% de Puntos y Posición Oficial        │
 │ 7. Techo Aritmético de Cartera      ➔ Sum(EV_Core) <= Sum(Ganancia_Maxima_Posible)     │
 │ 8. Linaje Cronológico Real H2H      ➔ Fechas reales decrecientes, >= 60d y alternancia │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7.1 DOCTRINA CANÓNICA DE PRUEBAS: THE SHIELD TESTING DOCTRINE

> **"Una suite de pruebas lenta, frágil o acoplada a la red no es un escudo de calidad; es un freno a la innovación y una fuente constante de falsa seguridad."**

Toda suite de pruebas construida bajo el Kybern Framework debe regirse obligatoriamente por los siguientes siete mandatos universales, aplicables a cualquier dominio o tecnología:

### [GOV-TEST-01] Axioma de Desacoplamiento Absoluto de Red e I/O en Pruebas Unitarias [ARCH-PILLAR]
* **Principio:** Los Jueces Abstractos (`abstract_test_*.py`) y las pruebas unitarias concretas de `tests/shield/` tienen **terminantemente prohibido realizar llamadas de red externas en tiempo de ejecución**.
* **Mecanismo:** Deben ejecutarse exclusivamente contra bases de datos efímeras en memoria (`sqlite:///:memory:`), transacciones con rollback automático, o snapshots estáticos fácticos congelados en disco.
* **Binding Rationale:** Una prueba unitaria que depende de que un servidor de terceros responda a través de internet es intrínsecamente no determinista, lenta y propensa a fallos falsos positivos por problemas de conectividad ajenos al software.

### [GOV-TEST-02] Presupuesto de Rendimiento y Segregación de Niveles (Performance SLA) [PERF-MANDATE]
Toda suite de pruebas debe segmentarse en dos niveles operativos estrictamente separados por su tiempo de ejecución:
1. **Nivel 1: The Shield Core (`tests/shield/`):**  
   - **SLA de Velocidad:** La suite completa debe ejecutarse en **menos de 5.0 segundos acumulados** (promedio $< 100\text{ ms}$ por prueba; las pruebas de matemática pura deben responder en $< 5\text{ ms}$).
   - **Frecuencia:** Se ejecuta de forma obligatoria en cada commit local, antes de cada push y en el pre-vuelo de cada refactorización.
2. **Nivel 2: Integración y Verificación E2E (`tests/e2e/`):**  
   - **Alcance:** Pruebas que validan navegadores headless (Playwright/Selenium), scrapers vivos, servicios externos o compilación pesada de documentos (PDFs).
   - **Frecuencia:** Se ejecutan **únicamente bajo demanda explícita o en compuertas de liberación final (Release Gates)**, jamás dentro del bucle rápido de desarrollo.

### [GOV-TEST-03] Principio de Unicidad del Juez (1 Nodo Lógico = 1 Juez Abstracto) [ARCH-PILLAR]
* **Prohibición de Fragmentación:** Queda prohibida la proliferación de múltiples clases abstractas o scripts duplicados para auditar un mismo Nodo Lógico IPO.
* **Consolidación:** Todas las aserciones de un nodo (`[LN-XXX]`) deben concentrarse en una única clase abstracta canónica (`AbstractTestLN_XXX`). Si se requiere evaluar aspectos complementarios (ej. contratos vs. presentación), se estructuran como métodos distintos dentro del mismo archivo maestro, erradicando archivos espejo redundantes.

### [GOV-TEST-04] Invarianza Semántica vs. Sobreajuste de Pruebas (Anti-Vibe Testing) [ANTI-BUG]
* **Aserciones Robustas:** Las pruebas deben evaluar **invariantes matemáticas, leyes de conservación y transiciones de estado**, no cadenas de texto efímeras ni detalles de implementación volátiles.
* **Prohibición de Sobreajuste:** Queda prohibido que un test verifique constantes sobreajustadas a un caso particular (ej. esperar un partido específico de un mes calendario). Las aserciones deben evaluar propiedades abstractas válidas para $N$ elementos (ej. sumas simplex $= 1.0000$, límites numéricos acotados en $[0, 1]$, o consistencia contable $\text{Activos} == \text{Pasivos} + \text{Capital}$).

### [GOV-TEST-05] Diseño Obligatorio de la Frustración (Sad Paths First) [ANTI-BUG]
* **Cobertura de la Adversidad:** Ningún Juez Abstracto es válido si únicamente prueba el camino feliz (*Happy Path*).
* **Casos Límite Exigidos:** Todo test debe incorporar aserciones para entradas vacías (`None`, `[]`), división por cero, valores fuera de rango, fechas expiradas y datos incompletos, certificando que el sistema se degrada de forma predecible, controlada y bajo el **Mandato de Fallo Ruidoso (`Fail-Loud`)**.

### [GOV-TEST-06] Idempotencia, Aislamiento y Cero Efectos Secundarios [ARCH-PILLAR]
* **Reversibilidad Absoluta:** La ejecución de un test no debe alterar el estado persistente del entorno de desarrollo ni de producción.
* **Aislamiento:** Ningún test debe depender de que otro se haya ejecutado previamente. El orden de ejecución debe ser intercambiable y aleatorizable sin alterar el veredicto.
* **Limpieza de Residuos:** Queda prohibido que una prueba genere archivos temporales que no sean eliminados automáticamente al concluir (`teardown` / fixtures efímeros).

### [GOV-TEST-07] Centinelas Forenses AST (Linters Sintácticos de Integridad) [GOVERNANCE]
Toda suite de The Shield debe incluir pruebas de inspección estática del Árbol de Sintaxis Abstracta (AST Linters, ej. `test_shield_anti_patterns_ast.py`) para verificar algorítmicamente en el código de producción:
1. Ausencia de datos mockeados o simulados en producción (`[GOVERNANCE-01]`).
2. Ausencia de números mágicos hardcodeados sin constante descriptiva.
3. Ausencia de capturas de error genéricas y silenciosas (`except Exception: pass`).

---

## 8. NOMENCLATURA MAESTRA INMUTABLE DE ESTRATEGIAS Q-BE

Queda **terminantemente prohibido** inventar, abreviar o alterar los nombres oficiales de las estrategias:

1. `QBE-D1` ➔ **Favorito Directo Puro**
2. `QBE-D1+` ➔ **Favorito Directo Potenciado**
3. `QBE-H1` ➔ **Favorito con Seguro en Empate**
4. `QBE-H1+` ➔ **Favorito Potenciado con Seguro**
5. `QBE-H2` ➔ **Empate de Valor con Seguro Fav**
6. `QBE-H2+` ➔ **Freeroll Doble Impacto (Joya)**
7. `QBE-R1` ➔ **Valor en No-Favorito con Seguro**
8. `QBE-R2` ➔ **Doble Oportunidad Sintética X2**
9. `QBE-00` ➔ **Veto Preventivo de Capital**
10. `QBE-MOONSHOT` ➔ **Tiro Satélite Asimétrico**

---

## 9. PROTOCOLOS OPERATIVOS DE CONTINUIDAD Y AUDITORÍA

### 9.1 Protocolo Sherlock (Diagnóstico Forense)
Ante una discrepancia o comportamiento inesperado:
1. **Aislamiento:** Prohibido modificar código a ciegas.
2. **Evidencia:** Extraer paquete de datos reproducibles (logs, payloads, respuestas de API).
3. **Simulación:** Construir script de reproducción forense en `scripts/` antes de proponer solución.

### 9.2 Protocolo Crisol (Purga y Reforja)
Si el código acumula deuda técnica crítica, parches o datos sintéticos:
1. **Extracción de Esencia:** Respaldar los algoritmos matemáticos dorados.
2. **Purga:** Eliminar código corrupto, mocks y archivos basura.
3. **Reforja:** Reconstruir sobre base limpia satisfaciendo los Twin-Tests.

### 9.3 Protocolo de Entrega con Manifiesto Git Diff (Proof of Work)
El Agente Constructor tiene prohibido declarar una tarea como "lista" basándose en afirmaciones verbales. Para dar por cerrado un ticket de desarrollo, debe emitir el **Manifiesto de Cierre**:
1. Salida de `git status` y `git diff --stat`.
2. Certificación explícita de **CERO números mágicos** y **CERO datos mockeados en producción**.
3. Telemetría de consola con tiempo de ejecución y resultado de `pytest tests/shield/ -v` en `EXIT CODE 0`.

---
**BASE DE GOBIERNO SELLADA BAJO EL KYBERN FRAMEWORK v8.0 / v12.0 — PROHIBIDA SU MUTACIÓN SIN CONSENSO LEGISLATIVO.**
```