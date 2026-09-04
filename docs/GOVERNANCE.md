```markdown
# Q-BE Casino Deportes — Governance Book (GOVERNANCE.md)
**Versión:** 9.0 (Kybern Industrial - Local Full-Stack Web Platform Edition)  
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

### 1.4 Mandato de Fallo Ruidoso (Fail-Loud Mandate) [GOVERNANCE] [ARCH-PILLAR]
En sistemas financieros y cuantitativos de asignación de capital, **la degradación silenciosa es inaceptable**. Quedan estrictamente prohibidas las capturas genéricas de error (`except Exception: return fallback_data()`) que oculten fallos de conexión inventando estados ficticios. Es preferible que un proceso falle de forma explícita y visible a que opere con datos corruptos.

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

---

## 5. TAXONOMÍA DE INCIDENTES Y RUTAS DE RESOLUCIÓN

### 5.1 Fallo de Implementación (Error de Dedo)
* **Definición:** Desviaciones sintácticas, `ImportError`, errores de tipado Pydantic, nombres de variables mal escritos o rutas de archivos incorrectas.
* **Vía de Resolución:** **Corrección Directa (Fast-Track).** El Agente Constructor repara la línea específica de forma atómica e inmediata sin necesidad de legislar en la BG.

### 5.2 Fallo de Lógica de Negocio o Regresión Estructural
* **Definición:** Violación de invariantes matemáticas (ej. sumatoria de probabilidades $\ne 1.0$, alteración de fórmulas de Poisson, hardcodeo de ganancias esperadas, o desalineación geométrica de tablas).
* **Vía de Resolución:** **Asedio Metodológico (Motor de 3 Pasos Obligatorio).** Prohibida la corrección directa sin antes legislar y crear el test abstracto.

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