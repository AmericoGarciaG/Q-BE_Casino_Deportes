```markdown
# Q-BE Casino Deportes — Logic Book (LOGIC.md)
**Versión:** 10.0 (Multi-Market & Vig-Free Edition)  
**Estado:** [ALGO-PROTECTED] - Base de Gobierno Sellada (2026-09)  
**Proyecto:** `Q_BE_CD_WEB` (Quantitative Betting Engine — Web Platform)  
**Fuente de Verdad:** Paper Académico Q-BE V2.0 + Kybern Framework v8.0 / v12.0

Este documento define la **Lógica de Negocio Invariante y el Grafo Matemático Determinista** del sistema `Q_BE_CD_WEB`. Cada nodo se modela bajo la tupla canónica:
$$\text{LN}_i = \langle \text{ID}, \Omega, I, P, O, \Phi \rangle$$

---

## 1. FORMALISMO MATEMÁTICO: EL GRAFO DE NODOS IPO

El pipeline de inteligencia cuantitativa se modela como un dígrafo acíclico dirigido $G = (V, E)$, donde los vértices $V$ son los Nodos Lógicos (`[LN-QBE-XXX]`) y las aristas $E$ representan contratos de transición tipados y validados:

```text
 ┌──────────────┐
 │ [LN-QBE-012] │ ➔ Normalizador Canónico de Clubes y Cuotas
 └──────┬───────┘
        │
        ├──────────────────────────┐
        ▼                          ▼
 ┌──────────────┐           ┌──────────────┐
 │ [LN-QBE-005] │           │ [LN-QBE-007] │ ➔ Ingesta Multi-Operador (Caliente & Betway)
 └──────┬───────┘           └──────┬───────┘
        │                          │ ➔ [007-B] Americano a Decimal
        │                          │ ➔ [007-C] Vig-Free al Símplex Δ²
        │                          │ ➔ [007-D] Arbitraje Inter-Casas
        │                          │ ➔ [007-E] Consenso Mkt & Deltas
        ├──────────────────────────┘
        ▼
 ┌──────────────┐
 │ [LN-QBE-010] │ ➔ Aduana de Sanidad y Anclaje
 └──────┬───────┘
        │
        ▼
 ┌──────────────┐
 │ [LN-QBE-040] │ ➔ Poisson Bivariado 6x6 Calibrado
 └──────┬───────┘
        │
        ▼
 ┌──────────────┐
 │ [LN-QBE-065] │ ➔ Filtro de Descarte Temprano (+EV Gate)
 └──────┬───────┘
        │
        ▼
 ┌──────────────┐
 │ [LN-QBE-070] │ ➔ Router Θ de Utilidad, Kelly, Dutching V=0
 └──────┬───────┘
        │
        ▼
 ┌──────────────┐
 │ [LN-QBE-072] │ ➔ Trinidad de Certeza 3^K y Resiliencia
 └──────────────┘
```

### 1.1 Notas de Derogación Normativa (Enmienda P.I.R. — Tratado Volumen II)

* **[DEROGADO: Se prohíbe tratar a D1+, H1+ o H2+ como estrategias independientes. Las estrategias canónicas son exactamente 9 (QBE-D1 a QBE-00); el Pago Anticipado es un atributo contractual ortogonal (pago_anticipado: bool)].**
* **Alcance:** Las entidades históricas `QBE-D1+`, `QBE-H1+` y `QBE-H2+` (referidas en `[LN-QBE-060]` y `[LN-QBE-070]`) pierden estatus de estrategia independiente: son exactamente la misma estrategia canónica portando la bandera ortogonal `pago_anticipado = True`, propagada conforme a `[ARCH-1.6.9]`.
* **Partición Canónica Vigente:** Las estrategias canónicas son exactamente 9 (`QBE-D1`, `QBE-D2`, `QBE-H1`, `QBE-H2`, `QBE-R1`, `QBE-R2`, `QBE-C1`, `QBE-C2` y `QBE-00`), mutuamente excluyentes y colectivamente exhaustivas. La cascada determinista de asignación queda legislada en `[LN-QBE-060-B]` y sellada en `[VAULT-CORE-070-TRIAJE]`.
* **[DEROGADO: Se deroga formalmente el método select_best_strategy basado en comparaciones heurísticas de utilidad arbitraria y generación de sufijos '+' (QBE-D1+, QBE-H1+, QBE-H2+). A partir de la Fase 5, la selección de estrategia se rige de forma unívoca por triaje_determinista_9_estrategias ([LN-QBE-060-B]), y el Pago Anticipado se desacopla como el atributo booleano ortogonal pa_activo: bool].**
* **Alcance (Fase 5 — Derogación de la Escalera Heurística V2.5):** `PortfolioEngine.select_best_strategy` deja de ser fuente de verdad de la selección: la partición canónica se resuelve de forma unívoca mediante `triaje_determinista_9_estrategias(payload, cuotas)` (`[LN-QBE-060-B]` / `[VAULT-CORE-070-TRIAJE]`), y el Pago Anticipado viaja como el atributo booleano ortogonal `pa_activo: bool`, contractualizado en `[LN-QBE-070-C]`. Queda prohibida toda comparación de utilidad arbitraria ($U_{\text{Directo}}$, $U_{\text{Cobertura}}$) y toda generación de sufijos `+` como identidad de estrategia. Sustituto legislado: `[LN-QBE-070-D]`.

---

## 2. CATÁLOGO MAESTRO DE NODOS LÓGICOS IPO

---

### ID: [LN-QBE-012] Normalizador Canónico de Clubes y Cuotas

* **Ω (Resumen):** Unificar nombres de clubes, abreviaturas, variantes ortográficas y aliases de fuentes heterogéneas (FotMob, Caliente, OCR, Gemini) a una identidad canónica inmutable.
* **I (Input):** Cadenas de texto crudas de nombres de equipos (`local`, `visitante`).
* **P (Process) [ARCH-PILLAR]:**
  1. Limpieza de texto: eliminación de caracteres no alfanuméricos, acentos y normalización de espacios.
  2. Mapeo directo contra el diccionario canónico `_CANONICAL_ALIASES` (18 clubes Liga MX + clubes internacionales).
  3. Búsqueda difusa (*Fuzzy Matching*) mediante distancia de Levenshtein ($\text{ratio} \ge 0.78$) ante fallos de OCR o variantes tipográficas.
  4. Si un equipo no puede resolverse con certeza $\implies$ lanzamiento de `NormalizationException`.
* **Heurística de Resolución de Próximo Rival (Safe Rival Lookup):**
  1. Si la fuente estructurada omite el rival o devuelve texto genérico (`"vs Rival"` o vacío), el normalizador deducirá el club rival a partir del fixture cruzado de la jornada activa.
  2. Si no es posible identificar con certeza al rival en la jornada, se resolverá como `"Por Definir"` asociando el placeholder SVG institucional. Prohibido el renderizado de cadenas vacías o términos no procesados.
* **Deducción Dinámica del Rival Sin Prefijo:**
  $$\text{proximo\_rival} = \begin{cases} 
  \text{visitante} & \text{si } \text{equipo} == \text{local} \\ 
  \text{local} & \text{si } \text{equipo} == \text{visitante} 
  \end{cases}$$
  El valor de salida debe ser el nombre canónico puro del rival (sin `"vs "`), asociando de inmediato su URL local de escudo `/static/img/crests/{rival_slug}.png`.
* **O (Output):** `EquipoCanónico` validado y unificado.
* **Φ (Transición):** Hacia **[LN-QBE-005]** y **[LN-QBE-010]**.
* **[SHIELD]:** `tests/shield/test_LN_QBE_012_normalizer.py`
* **[Binding Rationale]:** `[ARCH-PILLAR]` `[GOVERNANCE]` Previene la fragmentación de identidades entre la tabla de posiciones, los momios y el análisis estadístico.

---

### ID: [LN-QBE-007] Ingesta Fáctica y Normalización Multi-Operador (Caliente & Betway)
* **Ω (Resumen):** Extraer, validar y homologar los momios decimales 1X2 procedentes de múltiples casas de apuestas con licencia en México (Caliente.mx y Betway.mx), asociándolos a la identidad canónica de los clubes bajo [LN-QBE-012] para habilitar el arbitraje de valor (+EV).
* **I (Input):** Slate de partidos de la jornada activa `(local_canonico, visitante_canonico)` y lista de operadores objetivo `["caliente", "betway"]`.
* **P (Process) [ARCH-PILLAR] [ALGO-PROTECTED]:**
  1. Para cada operador, extraer las cuotas decimales puras: $O_{\text{Local}}, O_{\text{Empate}}, O_{\text{Visitante}} > 1.00$.
  2. Verificar integridad del mercado: Calcular el margen o sobre-precio comercial (*overround*):
     $$\text{Overround} = \left(\frac{1}{O_L} + \frac{1}{O_E} + \frac{1}{O_V} - 1.0\right) \times 100.0$$
     Si $\text{Overround} \le 0.0$ o $\text{Overround} > 25.0\% \implies$ Cuarentena del mercado del operador (`es_viable = False`).
  3. Mapear cláusulas especiales:
     - Caliente: Cláusula de Pago Anticipado (+2 goles) $\in \{\text{True}, \text{False}\}$.
     - Betway: Identificar disponibilidad de liquidación temprana o registrar `pago_anticipado = False` por defecto.
* **O (Output):** Estructura relacional de cuotas normalizadas por operador.
* **Φ (Transición):** Hacia [LN-QBE-005] (Triaje Determinista) y persistencia en `FixtureSnapshot`.
* **[SHIELD]:** `tests/shield/test_shield_multi_bookmaker_ingestion.py`

---

### ID: [LN-QBE-007-B] Normalización de Momios Americanos a Decimales
* **Ω (Resumen):** Conversión determinista de cotizaciones en formato americano (+/-) a cuotas decimales europeas:
  $$O_{\text{dec}} = \begin{cases} 
  1.0 + \frac{A}{100.0} & \text{si } A > 0 \\ 
  1.0 + \frac{100.0}{|A|} & \text{si } A < 0 
  \end{cases}$$
  *(Ejemplo: $+230 \implies 3.30$, $+100 \implies 2.00$, $-150 \implies 1.67$)*.

### ID: [LN-QBE-007-C] Descuento de Margen Comercial (Vig-Free De-biasing al Símplex Δ²)
* **Ω (Resumen):** Extraer la comisión de la casa para obtener la probabilidad justa implícita del mercado:
  1. Probabilidades brutas implícitas: $\pi_L = 1/O_L, \quad \pi_E = 1/O_E, \quad \pi_V = 1/O_V$.
  2. Suma de mercado (Overround Factor): $S = \pi_L + \pi_E + \pi_V$.
  3. Probabilidades justas sin comisión (Símplex $\Delta^2$):
     $$q_L = \frac{\pi_L}{S}, \quad q_E = \frac{\pi_E}{S}, \quad q_V = \frac{\pi_V}{S} \implies q_L + q_E + q_V = 1.0000$$

### ID: [LN-QBE-007-D] Detector de Arbitraje Inter-Casas (Cross-Market Surebet)
* **Ω (Resumen):** Identificar ineficiencias de mercado cruzando las cuotas máximas entre operadores:
  $$O_L^{\max} = \max_b(O_{L, b}), \quad O_E^{\max} = \max_b(O_{E, b}), \quad O_V^{\max} = \max_b(O_{V, b})$$
  $$\text{Índice Arbitraje} = \frac{1}{O_L^{\max}} + \frac{1}{O_E^{\max}} + \frac{1}{O_V^{\max}}$$
  - Si $\text{Índice Arbitraje} < 1.0000 \implies$ **Existe Arbitraje Puro (+EV)** con ROI libre de riesgo:
    $$\text{ROI}_{\text{Arb}} = \left(\frac{1.0}{\text{Índice Arbitraje}} - 1.0\right) \times 100\%$$

### ID: [LN-QBE-007-E] Consenso de Mercado y Diferenciales vs. Distribución Soberana
* **Ω (Resumen):** Promediar las probabilidades desprovistas de comisión de los casinos y calcular la disparidad contra el modelo soberano Q-BE:
  $$\bar{q}_k = \frac{1}{N} \sum_{b=1}^N q_{k, b} \quad \text{para } k \in \{L, E, V\}$$
  $$\Delta_L = p_{\text{Q-BE}, L} - \bar{q}_L, \quad \Delta_E = p_{\text{Q-BE}, E} - \bar{q}_E, \quad \Delta_V = p_{\text{Q-BE}, V} - \bar{q}_V$$

### ID: [LN-QBE-007-F] Lista Negra de Tokens de Navegación e Interfaz en Scraping (UI_BLACKLIST)
* **Ω (Resumen):** Especificar el descarte de los 27 tokens estáticos (`inicio`, `en vivo`, `1-x-2`, `mañana`, etc.) durante el parsing de sitios de casas de apuestas para prevenir contaminación de nombres de equipos.

### ID: [LN-QBE-007-G] Normalización y Limpieza de Nombres de Clubes de Betway
* **Ω (Resumen):** Describir la remoción previa de sub-cadenas ortográficas (`de guadalajara`, `xolos`, `fc`, `club`) sobre las cadenas extraídas de Betway para matching difuso exacto con el slate canónico.

### ID: [LN-QBE-007-H] Cotas de Admisibilidad de Cuotas y Overround en Betway
* **Ω (Resumen):** Filtrado de cuotas en $1.05 < O < 50.0$ y overround comercial admisible en $0.0\% < S \le 30.0\%$ para validar mercados operables de Betway.

### ID: [LN-QBE-007-I] Validación de Suma de Inversas en Caliente
* **Ω (Resumen):** Exigencia estricta de sanidad matemática sobre las cuotas 1X2 de Caliente, requiriendo que la suma de inversas $1/L + 1/E + 1/V$ se ubique estrictamente en $[1.00, 1.35]$.

### ID: [LN-QBE-007-J] Prior de Ignorancia Fiduciaria ante Ausencia de Distribución Soberana
* **Ω (Resumen):** Documentar la asignación fallback $(0.45, 0.28, 0.27)$ para evitar colapso de deltas si el motor Poisson aún no procesa el partido.

---

### ID: [LN-QBE-005] Triaje Determinista de Cuotas 1X2

* **Ω (Resumen):** Filtro económico previo (Paso 0-A) que evalúa las 6 vías de viabilidad sobre cuotas decimales 1X2 antes de consultar estadísticas profundas.
* **I (Input):** Lista de partidos con momios decimales ($O_{\text{Local}}, O_{\text{Emp}}, O_{\text{Vis}}$) y bandera de Pago Anticipado.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Evaluación de las 6 Vías de Valor Teórico:**
     - **Vía H1 (Favorito con Seguro en Empate):** $ROI_{\text{H1\_Teórico}} = (1.0 - 1.0/O_{\text{Emp}}) \cdot O_{\text{Fav}} - 1.0 \ge 0.05 \land (1.0/O_{\text{Und}}) < 0.35$.
     - **Vía H2 (Empate de Valor con Seguro Fav):** $ROI_{\text{H2\_Teórico}} = (1.0 - 1.0/O_{\text{Fav}}) \cdot O_{\text{Emp}} - 1.0 \ge 0.15 \land (1.0/O_{\text{Und}}) < 0.35$.
     - **Vía D1 (Super-Favorito Directo):** $O_{\text{Fav}} \le 1.45 \land (1.0/O_{\text{Und}}) \le 0.20$.
     - **Vía R1 (Underdog de Valor con Seguro):** $O_{\text{Und}} \ge 3.50 \land ROI_{\text{R1\_Teórico}} \ge 1.00$.
     - **Vía R2 (Doble Oportunidad Sintética X2):** $O_{\text{Sintético, X2}} = \frac{1.0}{(1.0/O_{\text{Und}} + 1.0/O_{\text{Emp}})} \ge 1.60$.
     - **Vía Satélite Asimétrico (Moonshot):** $O_{\text{Und}} \ge 4.50 \land \text{Pago Anticipado} == \text{True}$.
  2. **Descarte Preventivo:** Si un partido no califica en ninguna de las 6 vías $\implies$ clasificado como `TRIAGE_COIN_FLIP` y descartado sin llamadas adicionales.
* **O (Output):** `PartidosAprobadosTriaje` tipado.
* **Φ (Transición):** Hacia **[LN-QBE-003]** o **[LN-QBE-002]**.
* **[SHIELD]:** `tests/shield/abstract_test_LN_QBE_005_triage_and_narrative.py`
* **[Binding Rationale]:** `[BIZ-LOGIC]` `[ARCH-PILLAR]` Ahorra más del 70% del tiempo de procesamiento al descartar partidos cerrados sin asimetría matemática.

---

### ID: [LN-QBE-006] Asignación Relacional de Favorito por Momio 1X2

* **Ω (Resumen):** Determinar de forma puramente objetiva el rol de Favorito y Underdog en un encuentro a partir de las cuotas decimales del mercado.
* **I (Input):** Cuota local ($O_L$), Cuota visitante ($O_V$).
* **P (Process) [BIZ-LOGIC] [ALGO-PROTECTED]:**
  $$\text{Si } O_L \le O_V \implies \text{Favorito} = \text{Local}, \text{Underdog} = \text{Visitante}$$
  $$\text{Si } O_L > O_V \implies \text{Favorito} = \text{Visitante}, \text{Underdog} = \text{Local}$$
* **O (Output):** Roles canónicos `fav_name`, `und_name` y bandera `is_fav_local: bool`.
* **Φ (Transición):** Hacia `[LN-QBE-040]` (Poisson) y `[LN-QBE-070]` (Dutching).

---

### ID: [LN-QBE-003] Ingesta Fáctica Estructurada FotMob (Opta Metrics Engine)

* **P (Process) — Extracción Pura de FotMob sin Filtros Locales:**
  1. El conector debe consumir en vivo `https://www.fotmob.com/api/leagues?id=262` y procesar la tabla oficial en tiempo real, reflejando partidos adelantados o jugados al momento de la consulta (Pachuca PJ: 7, PTS: 8 en puesto #11).
  2. Prohibido el uso de diccionarios o tablas estáticas con datos preconcebidos. La tabla se extrae íntegra y dinámicamente con sus `id` oficiales de equipo.

---

### ID: [LN-QBE-017] Ingesta Fáctica Soberana de la Tabla General (Liga MX / FMF Engine)

* **Ω (Resumen):** Extracción determinista y estructurada de la Tabla General de Clasificación oficial directamente desde el portal de la Federación Mexicana de Fútbol (`https://ligamx.net/cancha/tablas/tablaGeneralClasificacion/`), garantizando paridad matemática absoluta (Posición, JJ, JG, JE, JP, GF, GC, Dif, PTS) con el torneo activo y erradicando cualquier lista de respaldo estática.
* **I (Input):** `league_id: int` (262 para Liga MX), `db_session` (SQLAlchemy Session opcional).
* **P (Process) [ARCH-PILLAR] [GOVERNANCE-01] [ANTI-BUG]:**
  1. **Extracción Soberana Directa:**
     - Consumir el HTML oficial de `https://ligamx.net/cancha/tablas/tablaGeneralClasificacion/`.
     - Parsear la tabla principal extrayendo para cada uno de los 18 clubes:
       `pos`, `club_raw`, `pj`, `pg`, `pe`, `pp`, `gf`, `gc`, `dif`, `puntos`.
  2. **Normalización Canónica (`[LN-QBE-012]`):**
     - Mapear cada nombre de club a su `canonical_slug` y asociar la ruta local soberana `/static/img/crests/{slug}.png` (con verificación física en disco).
  3. **Aduana de Integridad Aritmética de la Liga:**
     - Verificar que el total de clubes sea exactamente 18.
     - Validar coherencia contable: $\text{Puntos} == (\text{PG} \times 3) + \text{PE}$.
     - Validar simetría global: $\sum \text{GF} == \sum \text{GC}$ y $\sum \text{PG} == \sum \text{PP}$.
  4. **Acoplamiento de Métricas Avanzadas ($xG, xGA, xPTS$):**
     - Si la API de FotMob está disponible, se acoplan sus métricas Opta.
     - Si FotMob no responde o está bloqueado, se derivan analíticamente mediante los promedios reales de goles (`[LN-QBE-030]`), prohibiendo estrictamente alterar los puntos o posiciones oficiales de la Federación.
  5. **Axioma de Cero Fallbacks Estáticos [GOVERNANCE-01]:**
     - Queda formalmente prohibido mantener diccionarios de posiciones con datos preconcebidos en código (`LIGA_MX_CLUBS_DYNAMIC_FALLBACK`). Ante fallo total de red, el sistema levanta `DataQuarantineException` y preserva el último snapshot certificado de SQLite.
* **O (Output):** `OfficialStandingsSnapshot` con los 18 clubes oficiales de la federación.
* **Φ (Transición):** Hacia `[LN-QBE-010]` (Aduana de Sanidad), `[LN-QBE-040]` (Poisson Bivariado) y persistencia en `StandingSnapshot`.
* **[SHIELD]:** `tests/shield/test_LN_QBE_017_standings_pipeline.py`

---

### ID: [LN-QBE-018] Extractor Universal de Marcadores y Partidos Reprogramados

* **Ω (Resumen):** Extraer dinámicamente desde el DOM de la federación (`ligamx.net`) los marcadores fácticos de encuentros concluidos y la totalidad de los partidos reprogramados ($N \ge 0$), sin recurrir a marcadores nulos por omisión ni sobreajustes de nombres.
* **I (Input):** Documento HTML / Contexto de página de `https://ligamx.net/`.
* **P (Process) [ARCH-PILLAR] [ANTI-BUG] [GOVERNANCE-01]:**
  1. **Parser Multilínea de Goles:**
     - Para todo encuentro marcado como `FINALIZADO` o `MARCADOR OFICIAL`, extraer los dígitos de goles de los nodos `.goles`, `.marcador` o mediante regex multilínea `(?<!\d)(\d+)\s*\n*\s*[-–]\s*\n*\s*(\d+)(?!\d)`.
     - Mandato Fail-Loud: Prohibido asignar `"0 - 0"` si los goles no se encuentran; el sistema debe registrar `"MARCADOR_PENDIENTE"`.
  2. **Activación de Partidos Reprogramados:**
     - Hacer clic forzado en la píldora interactiva `PARTIDOS REPROGRAMADOS` de la marquesina.
     - Iterar dinámicamente sobre todas las tarjetas de la sección ($N \ge 0$).
     - Extraer clubes, fecha/hora y resolver mediante `LIGAMX_LOGO_ID_MAP` si las imágenes carecen de atributo `alt`.
     - Clasificar automáticamente al Grupo 4: `estado = "REPROGRAMADO"`, `es_pospuesto = True`, `disponible = False`.
* **O (Output):** `MarcadoresConcluidosMap` y `PartidosReprogramadosList`.
* **Φ (Transición):** Hacia `[LN-QBE-010]` y `sync_league_live_board()`.
* **[SHIELD]:** `tests/shield/test_LN_QBE_025_fixture_lifecycle.py`

---

### ID: [LN-QBE-002] Deprecación de Inferencia de Bajas y Anclaje Fáctico Estructurado
* **Ω (Resumen):** El factor de entorno $Q_{\text{mod}}$ se desvincula de búsquedas genéricas de IA y se ancla estrictamente a datos estructurados de fuentes oficiales. La inferencia generativa con Search Grounding se reserva exclusivamente para el futuro módulo `[ARCH-1.5.9]` ante movimientos anómalos de línea.
* **I (Input):** Partidos aprobados, tabla de posiciones congelada y pool `Gemini_API_4_QBE_*`.
* **P (Process) [ARCH-PILLAR] [ANTI-BUG]:**
  1. Verificar pre-vuelo en `GeminiCircuitBreaker`: si la llave está en `COOLDOWN`, rotar en 0 ms sin invocar red.
  2. Ejecutar la llamada a `gemini-3.6-flash` con Google Search Grounding.
  3. Ante error HTTP 429: extraer `retry_delay.seconds` enviado por Google y congelar la llave exactamente por ese lapso.
  4. Extraer reporte médico de bajas y suspensiones confirmadas, derivando el factor $Q_{\text{mod}}$.
* **O (Output):** `RawMatchInput` validado.
* **Φ (Transición):** Hacia **[LN-QBE-010]**.
* **[SHIELD]:** `tests/shield/abstract_test_LN_QBE_002_gemini_rotator.py`
* **[Binding Rationale]:** `[ARCH-PILLAR]` `[GOVERNANCE]` Resiliencia total de cuotas y extracción cualitativa blindada contra límites de frecuencia.

---

### ID: [LN-QBE-010] Aduana de Sanidad, Integridad y Anclaje a Tabla Maestra

* **Ω (Resumen):** Filtro determinista (Paso 0-C) que audita la sanidad de los datos antes de cualquier cálculo estocástico, bloqueando desalineaciones con la Tabla Maestra.
* **I (Input):** `RawMatchInput`, `MasterTableSnapshot`.
* **P (Process) [ALGO-PROTECTED] [ANTI-BUG]:**
  1. Cuarentena: Si `confiabilidad < 80.0%` o estado es `"CUARENTENA"` $\implies$ Veto automático `QBE-00`.
  2. Candado de Anclaje a Tabla Maestra: Validar que para ambos clubes coincidan posición, puntos y $Pts/PJ \pm 0.01$. Discrepancia $\implies$ Veto `QBE-00`.
  3. Checksums de 10P: $\sum GF == 10 \times \overline{GF}$ y $\sum GC == 10 \times \overline{GC}$.
* **O (Output):** `SanitizedMatchData` certificado.
* **Φ (Transición):** Hacia **[LN-QBE-020]** y **[LN-QBE-030]**.
* **[SHIELD]:** `tests/shield/abstract_test_LN_QBE_010_sanitizer.py`

---

### ID: [LN-QBE-011] Cálculo del Momio Justo (Fair Odds Q-BE)

* **Ω (Resumen):** Convertir la probabilidad real del modelo en un precio decimal puro e identificar la ventaja matemática (+EV) frente al casino en la Radiografía Forense.
* **I (Input):** $P_{\text{híbrida}}(k)$ para $k \in \{\text{Fav}, \text{Emp}, \text{Und}\}$.
* **P (Process) [BIZ-LOGIC] [ALGO-PROTECTED]:**
  1. **Momio Justo Teórico Puro Q-BE (H8):**
     $$O_{\text{Q-BE}}(k) = \frac{100.0}{P_{\text{híbrida}}(k) \times 100.0} = \frac{1.0}{P_{\text{híbrida}}(k)}$$
     *(Queda terminantemente prohibido duplicar o copiar el momio del casino en esta columna de la Radiografía).*
  2. **Ventaja Matemática Pura (Edge / +EV):**
     $$\text{Edge}(k) = P_{\text{híbrida}}(k) - \frac{1.0}{O_{\text{Casino}}(k)}$$
* **O (Output):** `FairOddsSnapshot` ($O_{\text{Q-BE}}$, $O_{\text{Casino}}$, $\text{Prob\_Real}$, $\text{Prob\_Casino}$, $\text{Edge}$).
* **Φ (Transición):** Hacia `[LN-QBE-050]` y el modal interactivo de Radiografía Forense.

---

### ID: [LN-QBE-020] Operador de Decaimiento Temporal en H2H ($\kappa$-Decay)

* **Ω (Resumen):** Modelar los últimos 5 enfrentamientos directos de liga mediante decaimiento exponencial continuo con vida media de 180 días ($\kappa = \ln(2)/180 \approx 0.00385\text{ días}^{-1}$).
* **I (Input):** 5 partidos H2H con días transcurridos ($\Delta t_i$) y resultado.
* **P (Process) [ALGO-PROTECTED]:**
  1. $w_i = \exp(-\kappa \cdot \Delta t_i)$, $W_{\text{Total}} = \sum w_i$.
  2. Probabilidades ponderadas: $P_{\text{H2H}}(k) = \frac{\sum w_i \cdot \mathbb{I}_{\{\text{res}_i == k\}}}{W_{\text{Total}}}$.
  3. **Candado de Linaje Cronológico Real [GOVERNANCE-01] [ANTI-BUG]:**
     - Fechas decrecientes verificables ($t_1 > t_2 > t_3 > t_4 > t_5$) con separación mínima de 60 días.
     - Prohibición de fechas duplicadas o sintéticas (ej. `01-01-2024` repetido).
     - Prohibición de localía estática al 100%: debe existir alternancia histórica de cancha.
* **O (Output):** `H2HDecayResults` ($P_{\text{H2H}}$, $\overline{GF}_{\text{H2H}}$).
* **Φ (Transición):** Hacia **[LN-QBE-040]**.
* **[SHIELD]:** `tests/shield/abstract_test_LN_QBE_020_temporal.py`

---

### ID: [LN-QBE-020-B] Ley de Ponderación Zero-H2H (Cero Mocks Sintéticos)

* **Ω (Resumen):** Gobernar el modelado estocástico cuando dos clubes carecen de antecedentes directos registrados en la base de datos, prohibiendo terminantemente inventar partidos históricos falsos.
* **P (Process) [GOVERNANCE-01] [ALGO-PROTECTED]:**
  - Si una pareja de equipos no tiene partidos H2H reales verificables en la base de datos (`len(h2h_matches) == 0`):
    $$w_{\text{H2H}} = 0.0 \implies w_{\text{Liga}} = 1.0$$
  - El modelo bivariado de Poisson 6x6 se ejecuta al **100% sobre las métricas Opta ($xG, xGA, FCF, E_{\text{att}}$)** del torneo activo.
  - Queda formalmente catalogado como violación crítica a la constitución el fabricar partidos H2H sintéticos con fechas o marcadores ficticios para forzar la ejecución de pruebas.
* **O (Output):** Ponderaciones $w_{\text{H2H}} = 0.0$ y $w_{\text{Liga}} = 1.0$.

---

### ID: [LN-QBE-030] Métricas Sintéticas de Control y Peligro ($FCF, E_{\text{att}}$)

* **Ω (Resumen):** Aislar la varianza de goles fortuitos mediante volumen de tiros y control de balón de 10 juegos.
* **P (Process) [ALGO-PROTECTED]:**
  $$\text{Raw\_FCF} = \left(\frac{\overline{\text{poss}}}{50.0}\right) \times \left(\frac{2.0 \cdot (\overline{\text{sot}} + 1.0)}{\overline{\text{sot}} + \overline{\text{sota}} + 2.0}\right) \implies FCF = \text{Clamp}(\text{Raw\_FCF}, [0.65, 1.35])$$
  $$\text{Raw\_E}_{\text{att}} = \frac{\overline{\text{gf}} + 0.35 \cdot \overline{\text{sot}}}{1.0 + 0.35 \cdot \overline{\text{sot}}} \implies E_{\text{att}} = \text{Clamp}(\text{Raw\_E}_{\text{att}}, [0.60, 1.40])$$
* **O (Output):** `SyntheticMetrics`.
* **Φ (Transición):** Hacia **[LN-QBE-040]**.

---

### ID: [LN-QBE-035] Fórmulas de Derivación Opta y Tokens de Marcador

* **Derivación de $xG/xGA$ en Ausencia de Tiros Profundos (H7):**
  $$\text{Fav } xG_{\text{est}} = \text{round}(\overline{GF}_{\text{Fav}} \times 1.05, 2), \quad xGA_{\text{est}} = \text{round}(\overline{GC}_{\text{Fav}} \times 0.95, 2)$$
  $$\text{Und } xG_{\text{est}} = \text{round}(\overline{GF}_{\text{Und}} \times 0.95, 2), \quad xGA_{\text{est}} = \text{round}(\overline{GC}_{\text{Und}} \times 1.10, 2)$$
* **Token Fail-Loud de Marcador Pendiente (H4):** Si un encuentro concluyó pero la federación aún no publica los números oficiales de goles, el sistema asigna el token canónico `"MARCADOR_PENDIENTE"`, prohibiendo inventar empates `"0 - 0"`.

---

### ID: [LN-QBE-040] Matriz Poisson Bivariada (6x6) con Calibración Opta xG

* **Ω (Resumen):** Proyectar goles esperados ($\lambda, \mu$), calcular la matriz Poisson bivariada 6x6 y derivar probabilidades híbridas y variables avanzadas.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Modulación con Opta xG de FotMob:**
     $$\text{Base\_Ataque}_{\text{Local}} = 0.65 \cdot \overline{xG}_{\text{Local}} + 0.35 \cdot \overline{GF}_{\text{Local 10P}}$$
     $$\text{Base\_Defensa}_{\text{Visitante}} = 0.65 \cdot \overline{xGA}_{\text{Vis}} + 0.35 \cdot \overline{GC}_{\text{Vis 10P}}$$
     $$\lambda_{\text{Local, Base}} = \sqrt{\text{Base\_Ataque}_{\text{Local}} \times \text{Base\_Defensa}_{\text{Visitante}}}$$
     $$\lambda_{\text{Local}} = \Big[ W_{\text{H2H}} \cdot \overline{GF}_{\text{H2H, L}} + W_{\text{Liga}} \cdot \lambda_{\text{Local, Base}} \Big] \times \Omega_{\text{perf, Local}}$$
     *(Mismo procedimiento recíproco para $\mu_{\text{Visitante}}$).*
  2. Matriz bivariada: $P(X=x, Y=y) = \frac{\lambda^x e^{-\lambda}}{x!} \cdot \frac{\mu^y e^{-\mu}}{y!} \quad \forall x, y \in [0, 5]$.
  3. Fusión Híbrida: $P_{\text{híbrida}}(k) = W_{\text{H2H}} \cdot P_{\text{H2H}}(k) + W_{\text{Liga}} \cdot P_{\text{Poisson}}(k)$.
  4. Variables de Salida: $\Phi_{\text{Lead2}}$ (Pago Anticipado), $\Psi_{\text{Ruina}} = P_{\text{híbrida}}(\text{Und}) \times 0.98$.
* **O (Output):** `PoissonAnalyticsResult`.
* **Φ (Transición):** Hacia **[LN-QBE-050]**.

---

### ID: [LN-QBE-050] Ecuaciones de Breakeven Dinámico Continuo ($\theta^*$)

* **Ω (Resumen):** Calcular analíticamente los umbrales exactos donde la Esperanza Matemática se anula ($EV = 0$), acotados estrictamente en $[0.00, 1.00]$.
* **P (Process) [ALGO-PROTECTED]:**
  $$\theta^*_{\text{Fav}} = \min\left(1.0, \max\left(0.0, \frac{\Psi_{\text{Ruina}}}{(1.0 - 1.0/O_{\text{Emp}}) \cdot O_{\text{Fav}} - 1.0}\right)\right)$$
  $$\theta^*_{\text{Emp}} = \min\left(1.0, \max\left(0.0, \frac{\Psi_{\text{Ruina}}}{(1.0 - 1.0/O_{\text{Fav}}) \cdot O_{\text{Emp}} - 1.0}\right)\right)$$
  $$\theta^*_{\text{Emp\_PA}} = \min\left(1.0, \max\left(0.0, \frac{\Psi_{\text{Ruina}}}{(1.0 - 1.0/O_{\text{Fav}}) \cdot O_{\text{Emp}} - 1.0 + \Phi_{\text{Lead2}}}\right)\right)$$
  $$\theta^*_{\text{Und}} = \min\left(1.0, \max\left(0.0, \frac{P_{\text{híbrida}}(\text{Fav})}{(1.0 - 1.0/O_{\text{Emp}}) \cdot O_{\text{Und}} - 1.0}\right)\right)$$
* **O (Output):** `BreakevenThresholdsResult`.
* **Φ (Transición):** Hacia **[LN-QBE-060]**.

---

### ID: [LN-QBE-060] Evaluador Determinista del Catálogo y Triple Candado Fáctico

* **Ω (Resumen):** Evaluar el cumplimiento booleano de las 9 estrategias eliminando umbrales fijos y aplicando el Triple Candado Fáctico para la Familia R.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. `QBE-D1` (Favorito Directo Puro):
     - El favorito es el resultado más probable: $P_{\text{Fav}} > P_{\text{Emp}} \land P_{\text{Fav}} > P_{\text{Und}}$.
     - Supera breakeven de casino: $P_{\text{Fav}} \ge 1.0 / O_{\text{Fav}}$ ($\text{Edge}_{\text{Fav}} > 0$).
     - $EV_{\text{D1}} = P_{\text{Fav}} \cdot (O_{\text{Fav}} - 1.0) - (1.0 - P_{\text{Fav}}) > 0 \land O_{\text{Fav}} \ge 1.25$.
     - *Axioma:* El umbral fijo del 70% queda eliminado.
  2. `QBE-D1+` (Favorito Directo Potenciado):
     - `QBE_D1 == True` $\land \Phi_{\text{Lead2}} \ge 0.45 \land \text{Pago Anticipado} == \text{True}$.
  3. `QBE-H1` / `QBE-H1+`:
     - $P_{\text{Fav}} \ge \theta^*_{\text{Fav}} \land \text{Edge}_{\text{Fav}} > 0 \land \Psi_{\text{Ruina}} \le 0.15 \land \text{Denom}_{\text{H1}} > 0$.
  4. `QBE-H2` / `QBE-H2+`:
     - $P_{\text{Emp}} \ge \theta^*_{\text{Emp}} \land \text{Edge}_{\text{Emp}} > 0 \land \Psi_{\text{Ruina}} \le 0.15 \land \text{Denom}_{\text{H2}} > 0$.
     - Para `H2+`: $\Phi_{\text{Lead2}} \ge 0.38 \land \Psi_{\text{Ruina}} \le 0.12 \land \text{PA} == \text{True}$.
  5. `QBE-R1` y `QBE-R2` (Familia R - Triple Candado Fáctico Obligatorio):
     - **Candado 1:** $P_{\text{híbrida}}(\text{Fav}) \le 0.4800$ (Techo estricto de dominancia).
     - **Candado 2:** Vulnerabilidad estructural del favorito ($\ge 2$ de: $Pts/PJ_{\text{Fav}} \le 1.40$, $\overline{GC}_{10P} \ge 1.30$, $Q_{\text{mod}} \le 0.95$).
     - **Candado 3:** Inmunidad histórica: $P_{\text{H2H}}(X2) \ge 0.4000$.
     - Si no supera los 3 candados $\implies \text{viable: False}$ (Veto Inverso).

### [LN-QBE-060-R] NOTA FORMAL DE DEROGACIÓN — Sueño Profundo de la Familia R (R1 y R2) [GOVERNANCE]

* **Estado:** `DEROGADO` — Sustituido por `[LN-QBE-060-R-AWAKEN]`.
* **[DEROGADO por Enmienda LN-QBE-060-R-AWAKEN: Se cancela el sueño profundo; las estrategias R1 y R2 quedan activas bajo las Cuatro Leyes de Hierro del Underdog].**
* **Efecto Normativo:** Queda revocado el mandato de retorno forzado `viable = False` con motivo `"ESTRATEGIA EN SUEÑO PROFUNDO (REFORMULACIÓN HOLÍSTICA EN CURSO)"`. Los códigos `QBE-R1` y `QBE-R2` regresan al catálogo evaluable, sujetos exclusivamente a las Cuatro Leyes de Hierro de `[LN-QBE-060-R-AWAKEN]` y a los Candados Fácticos vigentes de `[LN-QBE-060]`.

* **Candado 4 para Familia R (Filtro Anti-Contracorriente Obligatorio) [BIZ-LOGIC] [ALGO-PROTECTED]:**
  - Queda estrictamente prohibido autorizar estrategias de la Familia R (`QBE-R1` o `QBE-R2`) si el favorito del mercado mantiene la probabilidad individual dominante en el modelo Q-BE ($P_{\text{Fav}} > P_{\text{Und}}$) y el no-favorito posee ventaja matemática negativa ($Edge_{\text{Und}} \le 0.0$).
  - *Regla de Decisión:*
    $$\text{Si } (P_{\text{Fav}} > P_{\text{Und}} \land Edge_{\text{Und}} \le 0.0) \implies \text{Viable}_{\text{R1/R2}} = \text{False}$$
  - *Motivo:* Previene apostar capital a la derrota del desenlace más probable cuando el valor real está concentrado exclusivamente en el empate. El partido debe derivar a `QBE-H2` o a `QBE-00` (Veto preventivo).
* **O (Output):** `StrategyComplianceMatrix`.
* **Φ (Transición):** Hacia **[LN-QBE-070]**.

---

### ID: [LN-QBE-060-B] Partición Exhaustiva de las 9 Estrategias Canónicas y Cascada de Triaje

* **Ω (Resumen):** Partición formal del espacio de inversión en exactamente nueve estrategias mutuamente excluyentes y colectivamente exhaustivas: `QBE-D1`, `QBE-D2`, `QBE-H1`, `QBE-H2`, `QBE-R1`, `QBE-R2`, `QBE-C1`, `QBE-C2` y `QBE-00`.
* **I (Input):** Tupla $\mathcal{T}_i = \langle \vec{p}_i, \Delta_{\text{epist}}, S(\mathcal{I}_i), \vec{O}_i, \vec{\alpha}_i, \theta^*, \Phi_{\text{Lead2}}, Q_{\text{mod}} \rangle$.
* **P (Process) [ARCH-PILLAR] [ALGO-PROTECTED]:**
  Árbol de decisión determinista en cascada de 7 pasos:
  1. Si $S(\mathcal{I}_i) = 0 \lor \Delta_{\text{epist}} > 0.12 \implies$ **`QBE-00`** (Cuarentena / Capital = $\$0.00$).
  2. Si $p_{\text{fav}} \ge 0.65 \land \Delta_{\text{epist}} \le 0.04 \land \alpha_{\text{fav}} > 0.05 \implies$ **`QBE-D1`** (Local) o **`QBE-D2`** (Visita).
  3. Si cumple las Cuatro Leyes del Underdog ($\alpha_{\text{dog}} \ge +0.20 \land O_{\text{dog}} \ge 3.50 \land \Delta_{\text{epist}} \le 0.05 \land Q_{\text{mod}} \ge 0.98) \implies$ **`QBE-R1`** (Dog Local) o **`QBE-R2`** (Dog Visita).
  4. Si $0.40 \le p_{\text{fav}} < 0.65 \land O_{\text{Empate}} > \theta^* \land \alpha_H > 0 \implies$ **`QBE-H1`** (Local) o **`QBE-H2`** (Visita) con seguro $V=0$.
  5. Si $O_{\text{Empate}} \le \theta^*$ (empate caro) $\land \alpha_{\text{DNB}} > 0.05 \implies$ **`QBE-C1`** (Draw No Bet / AH 0.0).
  6. Si $\max(\alpha_{1X2}) \le 0 \land \alpha_{\text{Totales}} > 0.06 \implies$ **`QBE-C2`** (Derivado Totales en $M_{xy}^*$).
  7. Por defecto ante ausencia de valor $\implies$ **`QBE-00`** (Abstención).
* **O (Output):** `strategy_code: str`, `pago_anticipado: bool`, `alpha_neto: float`.
* **Φ (Transición):** Hacia [LN-QBE-070-B] (Asignación de Capital).

---

### ID: [LN-QBE-060-R-AWAKEN] Las Cuatro Leyes de Hierro del Underdog (Familia R)
* **Ω (Resumen):** Condiciones sine qua non para autorizar posiciones en perros de cuota alta ($O \ge 3.50$):
  - **Ley 1:** Retorno neto esperado $\alpha_{\text{dog}} \ge +0.20$ ($+20.0\%$ de EV neto).
  - **Ley 2:** Discrepancia epistémica inter-generadores $\Delta_{\text{epist}} \le 0.05$.
  - **Ley 3:** Exposición máxima acotada por evento: $B_{\text{dog}} \le 0.015 \cdot \text{Bankroll}$ (máximo 1.5% del capital total).
  - **Ley 4:** Factor contextual $Q_{\text{mod}}^{\text{dog}} \ge 0.98$ (sin bajas críticas en el perro).

---

### ID: [LN-QBE-070] Router de Utilidad Pura, Kelly y Techo Aritmético

* **Ω (Resumen):** Seleccionar la estrategia óptima individual mediante comparación analítica de utilidad, calcular la ruina conjunta del portafolio y estructurar los boletos en pesos con respeto estricto al techo de ganancia máxima.
* **P (Process) — Reglas de Ordenamiento y Escala Financiera:**
  1. **Ordenamiento Jerárquico Doble (H3):** Las órdenes del portafolio se ordenan prioritariamente por:
     - 1º Criterio: Mayor probabilidad de preservación $(1.0 - \Psi_{\text{Ruina}})$ descendente.
     - 2º Criterio: Mayor ROI neto esperado descendente.
  2. **Cálculo de Ganancia Esperada (Corrección Decimal Estricta):**
     - Dado que $EV_{\text{Net\_ROI}}$ se deriva como fracción decimal ($0.4464 = 44.64\%$):
       $$EV_{\text{Global}} = \sum_{i=1}^K A_i \times EV_{\text{Net\_ROI}, i}$$
       *(Prohibido dividir entre 100 dos veces; el monto de ganancia esperada se computa en pesos directos).*
     - El ROI global se expresa en porcentaje: $\text{ROI}_{\text{Global}} = \left(\frac{EV_{\text{Global}}}{\sum A_i}\right) \times 100.0$.
  3. **Comparación de Utilidad Directo vs. Cobertura:**
     $$U_{\text{Directo}} = EV_{\text{Directo}} \times P_{\text{Fav}}$$
     $$U_{\text{Cobertura}} = EV_{\text{Cobertura}} \times (1.0 - \Psi_{\text{Ruina}})$$
     - Si $U_{\text{Directo}} > U_{\text{Cobertura}} \land \Psi_{\text{Ruina}} \le 0.08 \implies$ Seleccionar **`QBE-D1+` (o `D1`)**.
  4. **Escalera de Prioridad:** `H2+` $\rightarrow$ Max($U$) entre `D1+/H1+` $\rightarrow$ Max($U$) entre `D1/H1` $\rightarrow$ `H2` $\rightarrow$ `R1/R2` $\rightarrow$ `QBE-00`.
     * **[DEROGADO en Fase 5]:** el método `select_best_strategy` basado en comparaciones heurísticas de utilidad arbitraria ($U_{\text{Directo}}$, $U_{\text{Cobertura}}$) y en la generación de sufijos `+` (`QBE-D1+`, `QBE-H1+`, `QBE-H2+`) queda **prohibido** como identidad de estrategia. La selección se rige de forma unívoca por `triaje_determinista_9_estrategias` (`[LN-QBE-060-B]`) y el Pago Anticipado se desacopla como el atributo booleano ortogonal `pa_activo: bool`. Sustituto legislado: `[LN-QBE-070-D]`.
  5. **Asignación de Capital:**
     - $S_i = \frac{EV_i}{\Psi_i}$, $w_i = \frac{S_i}{\sum S_j}$.
     - $\text{Bolsa}_{\text{Core}} = B \times \min(0.25, 0.06 \cdot K)$.
     - $\text{Cap}_i$ — **[DEROGADO en Fase 4: el divisor heurístico `3.0` y el piso artificial `0.02` quedan erradicados por [LN-QBE-070-B]]**
       La fórmula histórica $\text{Cap}_i = \min(0.08, \max(0.02, \frac{EV_i}{3.0 \cdot \Psi_i}))$ queda **prohibida** por (a) contener el número mágico `3.0` y (b) clavar un piso artificial `0.02` contrario a la [INVARIANZA #7].
       Sustituto canónico — **Kelly Fraccional Atenuado**: $\text{Cap}_i = \texttt{calcular\_kelly\_atenuado}(p_i, O_i, \Delta_{\text{epist}, i}) = \gamma_{\text{Kelly}} \cdot \frac{\alpha_i}{O_i - 1} \cdot \Psi_{\text{epist}}(\Delta_{\text{epist}})$, con $\gamma_{\text{Kelly}} = 0.25$, techo duro $0.0800$ y **cero pisos artificiales**. Fuente única: `[VAULT-CORE-070-KELLY]` / `src/core/contracts/portfolio_math.py`.
       **Nota de materialización (Fase 4):** la sustitución directa en `PortfolioEngine.build_plan` exige que el contrato de `approved_matches` exponga $p_i$, $O_i$ y $\Delta_{\text{epist}}$. Mientras ese contrato no se extienda, el techo de cartera se aplica con `aplicar_hard_caps_constitucionales` (8% individual / 25% global) y el piso con `[LN-QBE-071]`. Nodo de seguimiento declarado en `docs/DIRGEN_VARIANCE_REQUEST_LN-QBE-070-073.md`.
     - $A_i = \min(\text{Bolsa}_{\text{Core}} \times w_i, B \times \text{Cap}_i)$ con **piso de ventanilla canónico de $2.00 MXN** `[LN-QBE-071]` (`PISO_MINIMO_BOLETO`). El literal histórico `4.00` queda derogado por no estar legislado en la bóveda.
  6. **Dutching Exacto:**
     - Familia H2: Boleto 1 (Seguro Fav) $= A_i / O_{\text{Fav}}$, Boleto 2 (Ganancia Emp) $= A_i - \text{Boleto 1}$.
     - Familia H1 / R1: Boleto 1 (Seguro Emp) $= A_i / O_{\text{Emp}}$, Boleto 2 $= A_i - \text{Boleto 1}$.
     - Familia D1: Boleto 1 $= \$0.00$, Boleto 2 $= A_i$.
  7. **Invarianza de Techo Aritmético de Cartera [INVARIANZA #7]:**
     - Prohibido clavar pisos mínimos fijos (ej. `max(0.50)` o `$3.50`).
     - Sumatoria pura: $EV_{\text{Global}} = \sum_{i=1}^K A_i \cdot EV_{\text{Net\_ROI}, i}$.
     - Techo estricto: $EV_{\text{Global}} \le \sum_{i=1}^K \text{Ganancia\_Máxima\_Partido}_i$.
* **O (Output):** `PortfolioExecutionPlan`.
* **Φ (Transición):** Hacia **[LN-QBE-013]**, **[LN-QBE-014]** y **[LN-QBE-090]**.

---

### ID: [LN-QBE-070-B] Asignación con Kelly Fraccional Atenuado y Hard-Caps Constitucionales

* **Ω (Resumen):** Cálculo analítico del tamaño de posición libre de números mágicos:
  $$f_{\text{adj}}^* = \gamma_{\text{Kelly}} \cdot f^* \cdot \Psi_{\text{epist}}(\Delta_{\text{epist}})$$
  donde $\gamma_{\text{Kelly}} = 0.25$ (Cuarto de Kelly) y $\Psi_{\text{epist}} = \max\left(0, 1 - (\Delta_{\text{epist}} / 0.12)^2\right)$.
* **Hard-Caps de Preservación Innegociables:**
  - Partido individual: $B_i \le 0.0800 \cdot B_{\text{total}}$ (máximo 8.0%).
  - Cartera global de jornada: $\sum B_i \le 0.2500 \cdot B_{\text{total}}$ (máximo 25.0%).
  - Techo Aritmético: $EV_{\text{Cartera}} \le \sum \text{Ganancia\_Máxima\_Neta}_i$.

### ID: [LN-QBE-070-C] Contrato Extendido de Partidos Candidatos (CandidateMatchPayload)
* **Ω (Resumen):** Garantiza que cada partido entregado al motor de portafolios transporte íntegros los estratos de probabilidad soberana e incertidumbre epistémica, permitiendo que la asignación de Kelly opere sobre matemáticas analíticas puras sin atajos ni proxies empíricos.
* **I (Input):** Snapshot relacional 3NF de Fixture y SovereignDistribution.
* **P (Process) [ARCH-PILLAR] [ALGO-PROTECTED]:**
  Todo diccionario de partido aprobado en `approved_matches` debe contener obligatoriamente:
  - `id_partido`: str
  - `partido_nombre`: str
  - `p_fav`: float (probabilidad soberana del favorito $\in (0, 1)$)
  - `p_emp`: float (probabilidad soberana del empate)
  - `p_und`: float (probabilidad soberana del underdog)
  - `delta_epist`: float (discrepancia ponderada $\Delta_{\text{epist}} \in [0, 1)$)
  - `psi_epist`: float (factor cuadrático de atenuación $\Psi_{\text{epist}} \in [0, 1]$)
  - `phi_lead2`: float (tasa de Pago Anticipado de Désiré André)
  - `q_mod_fav`, `q_mod_und`: float (factores contextuales de fuerza mayor)
  - `odd_fav`, `odd_emp`, `odd_und`: float (cuotas comerciales efectivas $> 1.0$)
  - `fav_name`, `und_name`: str
  - `pago_anticipado`: bool
* **O (Output):** Payload certificado listo para alimentar `build_plan()`.
* **Φ (Transición):** Hacia [LN-QBE-070-B] (Kelly fraccional y Hard-Caps).

---

### ID: [LN-QBE-070-D] Orquestación Analítica de Cartera en build_plan()
* **Ω (Resumen):** Subordina la construcción de la cartera en `src/core/portfolio.py` a las funciones canónicas inmutables de `portfolio_math.py`:
  1. Ordenamiento previo de los partidos mediante `calcular_ranking_friccion(approved_matches)`.
  2. Dimensionamiento de cada posición mediante `calcular_kelly_atenuado(p_fav, o_fav, delta_epist, gamma_kelly=0.25)`.
  3. Aplicación estricta de topes mediante `aplicar_hard_caps_constitucionales(inversiones, bankroll)`.
  4. Escalamiento al piso de $\$2.00\text{ MXN}$ mediante `escalar_a_piso_ventanilla()` preservando $V=0$.

---

### ID: [LN-QBE-073-B] Algoritmo de Ranking de Fricción de Jornada

* **Ω (Resumen):** Ordenamiento formal de la cartelera por Calidad Distributiva:
  $$\text{Score}_i = \left( \frac{\alpha_i^*}{\Delta_{\text{epist}, i} + 0.01} \right) \cdot \Psi_{\text{epist}, i} \cdot \mathbb{I}_{\{\text{Estrategia}_i \ne \text{QBE-00}\}}$$
* Los partidos se ordenan descendentemente según $\text{Score}_i$, priorizando activos de alta convicción y gran $+EV$.

---

### ID: [LN-QBE-013] Sintetizador de Metadatos, Cronometría Dinámica y Ventanas Reprogramadas

* **Ω (Resumen):** Deducir cronológicamente el rango de fechas real de la jornada y discriminar la operabilidad de encuentros reprogramados sin cadenas quemadas.
* **P (Process) [ANTI-BUG] [BIZ-LOGIC] (H5, H6):**
  1. **Rango Dinámico de Fechas:** Parsear el día y mes de los partidos operables del lote, identificando $d_{\min}$ y $d_{\max}$. Formatear en español institucional:
     $$\text{Rango} = \begin{cases} 
     d_{\min} \text{ al } d_{\max} \text{ de } \text{Mes de } \text{Año} & \text{si } d_{\min} \ne d_{\max} \\ 
     d_{\min} \text{ de } \text{Mes de } \text{Año} & \text{si } d_{\min} == d_{\max} 
     \end{cases}$$
     *(Prohibido el renderizado de cadenas por defecto como "Fechas no especificadas").*
  2. **Discriminación de Reprogramados ($\Delta t \le 14$d):**
     - Calcular distancia en días contra la fecha del sistema: $\Delta t = \text{fecha\_partido} - \text{hoy}$.
     - Si $\Delta t > 14$ días: Sub-etiqueta `Fecha Lejana`, selección bloqueada (`disponible = False`).
     - Si $\Delta t \le 14$ días: Reprogramado en ventana inmediata. Si posee cuotas activas de casino, se declara operable (`disponible = True`).
* **O (Output):** `MetadataDictionary` dinámico y certificado.
* **Φ (Transición):** Hacia **[LN-QBE-080]**.

---

### ID: [LN-QBE-014] Narrativa Híbrida Asistida (Tesis Q-BE en 4 Bullets)

* **Ω (Resumen):** Redactar la Tesis Q-BE estructurada en 4 viñetas expandidas (mínimo 35 palabras por viñeta) con contraste obligatorio de momios (@ Q-BE vs @ Casino) y cobertura de tablas.
* **P (Process) [UX-MANDATE] [ARCH-PILLAR]:**
  1. Invocación primaria a `gemini-3.6-flash` con contexto cuantitativo cerrado (sin alucinaciones numéricas).
  2. Fallback determinista en `narrative.py` (Mad-Libs paramétrico) ante indisponibilidad de red.
  3. Formato inmutable:
     - • <strong>Momento y Tabla:</strong> Disparidad de puestos, puntos y efectividad.
     - • <strong>Dominio de Cancha:</strong> Relación de $SoT$, $SoTA$, posesión y $xG$ Opta.
     - • <strong>Historial y Bajas:</strong> Antecedentes reales H2H y reporte médico.
     - • <strong>Estrategia y Protección:</strong> Asignación de boletos en pesos ($), cobertura de empate ($0.00 pérdida), Pago Anticipado y contraste de momios.
* **O (Output):** `TesisDidacticaHTML`.
* **Φ (Transición):** Hacia **[LN-QBE-080]**.

---

### ID: [LN-QBE-080] Compilador de Reportes Oficiales y PDF A4

* **Ω (Resumen):** Renderizar la aplicación web interactiva (Jinja2) y compilar el documento formal A4 para impresión (Playwright Chromium Headless).
* **P (Process) [UX-MANDATE]:**
  1. Inyección de CSS standalone Dark Mode Fintech inmutable.
  2. Ocultamiento estricto de vistas de selección (Hub y Split-View) en `@media print`.
  3. Numeración automática de folios `@page { @bottom-right { content: "Página " counter(page) " de " counter(pages); } }`.
* **O (Output):** `reporte_ejecutivo.html` y `reporte_ejecutivo.pdf`.

---

### ID: [LN-QBE-090] Escudo Forense de Invarianzas (The Shield Release Gate)

* **Ω (Resumen):** Compuerta de despacho que ejecuta las **8 Pruebas de Invarianza Numérica y Geometría**.
* **P (Process) [ALGO-PROTECTED] [GOVERNANCE]:**
  1. Prueba 1 (Simplex): $| (P_{\text{Fav}} + P_{\text{Emp}} + P_{\text{Und}}) - 1.0 | \le 0.001$.
  2. Prueba 2 (Dutching Exacto): $|\text{Retorno\_Seguro} - \text{Inversión}| \le \$0.08\text{ MXN}$.
  3. Prueba 3 (Hard-Cap Individual): $\text{Inv}_i \le B \times 0.0801$.
  4. Prueba 4 (Hard-Cap Global): $\sum \text{Inv} \le B \times 0.2501$.
  5. Prueba 5 (Colchón Satélite): $\sum \text{Ganancia\_Core} \ge 3.0 \times \text{Satélite}$.
  6. Prueba 6 (Linaje Tabla Maestra): Puntos y puestos coinciden 100% con fuente oficial.
  7. Prueba 7 (Techo Aritmético): $EV_{\text{Global}} \le \sum \text{Ganancia\_Máxima}$.
  8. Prueba 8 (Linaje H2H y Cero Mocks): Fechas reales decrecientes, separación $\ge 60$d y alternancia de localía.
  *Veredicto:* Violación $\implies$ `RuntimeError("Shield Release Gate BLOQUEADO")`.
* **O (Output):** `AuditReleaseVerdict` (`AUTHORIZED` / `BLOCKED`).

---

### ID: [LN-QBE-015] Curador Agéntico de Catálogos y Bóveda de Activos

* **Ω (Resumen):** Prospección multimodal de identidades de clubes, validación de coherencia semántica mediante IA, aprobación humana por tarjeta y sellado inmutable en la base de datos local.
* **I (Input):** Identificador de liga (`league_id`), fuentes de federación oficial.
* **P (Process) [ARCH-PILLAR] [GOVERNANCE]:**
  1. Prospección agéntica: Detección de nombre oficial, nombre corto, slugs, ciudad y escudo oficial en formato PNG transparente.
  2. Staging de revisión: Presentación de tarjetas de pre-visualización al Director Humano.
  3. Bucle HITL: El Director aprueba clubes individualmente (`[✅ Confirmar]`) o solicita reintento agéntico (`[🔄 Re-consultar fuente]`).
  4. Descarga y Hash de Integridad: Al confirmar, Python descarga los archivos de imagen a disco local calculando su hash SHA256 para verificar que el activo no esté vacío ni corrupto.
  5. Commit en SQLite: Inserción en la base de datos `teams` cerrando el catálogo.
* **O (Output):** `SealedCatalogTransaction` y archivos de escudo locales listos para servir.
* **Φ (Transición):** Hacia **[LN-QBE-012]** (Normalizador Canónico).
* **[SHIELD]:** `tests/shield/abstract_test_LN_QBE_022_catalog_curation_hitl.py`

---

### ID: [LN-QBE-019] Resolutor Canónico de Escudos y Activos Visuales

* **Ω (Resumen):** Resolver la URI de imagen para cada club garantizando disponibilidad visual absoluta en el frontend, erradicando el bloqueo por anti-hotlinking HTTP 403 mediante el uso estricto de la Bóveda Soberana Local o placeholders deterministas.
* **I (Input):** `equipo_nombre` (str), `fotmob_id` (int), `db_session` (SQLAlchemy Session opcional).
* **P (Process) [ARCH-PILLAR] [ANTI-BUG]:**
  1. **Resolución de Identidad y Espejeo:** Normalizar `equipo_nombre` mediante `[LN-QBE-012]`, resolviendo el slug canónico primario o sus aliases vinculados.
  2. **Escalera de Precedencia Determinista:**
     - **Nivel 1 (Bóveda Local Certificada):** Verificar existencia física del archivo local `src/web/static/img/crests/{slug}.png`. Exigir obligatoriamente `size >= 2500` bytes (rechazo categórico de archivos de 0 bytes). Si es válido $\implies$ retornar `/static/img/crests/{slug}.png`.
     - **Nivel 2 (Persistencia SQLite):** Consultar tabla `teams` con validación de URL local o CDN de la FMF (`cldrsrcs.apilmx.com`).
     - **Nivel 3 (Fallback SVG Data URI):** Generar SVG determinista con las iniciales del club sobre fondo Slate 800 (`#1C2541`) y borde Cian (`#38BDF8`).
  3. **Mandato Anti-Hotlinking:** Prohibición absoluta de enlaces directos a `images.fotmob.com`.
* **O (Output):** `safe_crest_url: str` (Garantizada accesible localmente o mediante data-uri).
* **Φ (Transición):** Hacia `StandingRowOut.escudo_url` y `MatchFixtureOut`.
* **[SHIELD]:** `tests/shield/test_LN_QBE_019_crest_pipeline.py`
* **[Binding Rationale]:** `[ANTI-BUG]` `[UX-MANDATE]` Elimina los errores visuales por bloqueo de terceros y garantiza autonomía visual en despliegues offline/locales.

---

### ID: [LN-QBE-021] Generador de Traza de Auditoría Cuantitativa Markdown

* **Ω (Resumen):** Exportar de forma determinista un reporte exhaustivo en Markdown (`data/output/auditoria_cuantitativa_jornada_8.md`) con el ciclo estocástico y financiero completo de cada partido operable procesado en la cartera.
* **I (Input):** `ConsolidatedPayload` emitido por `QBEPipelineEngine.run_full()`.
* **P (Process) [ARCH-PILLAR] [BIZ-LOGIC]:**
  1. Registrar metadatos del evento (Torneo, Jornada, Bankroll evaluado, Ganancia neta esperada).
  2. Construir la tabla de Órdenes de Inversión con desglose de boletos split (Boleto 1 Seguro y Boleto 2 Ganancia).
  3. Desglosar para cada partido operable:
     - Entradas Fácticas (Cuotas Caliente L/E/V, Opta xG/xGA, Pts/PJ).
     - Modulación de Poisson ($\lambda, \mu$, Goles Totales, Simplex $=1.0000$, probabilidades Fav/Emp/Und).
     - Variables de Ruina ($\Psi_{\text{Ruina}}, \Phi_{\text{Lead2}}$).
     - Derivadas de Breakeven ($\theta^*_{\text{Fav}}, \theta^*_{\text{Emp}}, \theta^*_{\text{PA}}, \theta^*_{\text{Und}}$).
     - Tesis didáctica en 4 viñetas.
  4. Listar partidos vetados por el filtro del Triple Candado Fáctico o Triaje.
* **O (Output):** Archivo `data/output/auditoria_cuantitativa_jornada_8.md`.
* **Φ (Transición):** Persistencia en disco para verificación forense independiente.

---

### ID: [LN-QBE-022] Auditor Paralelo Independiente CLI (The Shield Parallel Auditor)

* **Ω (Resumen):** Script de ejecución en terminal (`scripts/auditar_calculos_portafolio.py`) que audita de forma aislada e independiente el último portafolio persistido en SQLite, recalculando con NumPy/SciPy puro para certificar las 8 invarianzas numéricas.
* **I (Input):** Registro en tabla `portfolio_records` de `qbe_database.db`.
* **P (Process) [GOVERNANCE] [ALGO-PROTECTED]:**
  1. Invarianza Dutching: $|\text{Monto\_B1} \times \text{Momio\_B1} - \text{Inversión}| \le \$0.08\text{ MXN}$ en coberturas.
  2. Invarianza de Suma: $|\text{Monto\_B1} + \text{Monto\_B2} - \text{Inversión}| \le \$0.02\text{ MXN}$.
  3. Invarianza de Hard-Caps: $\text{Inv}_i \le \text{Bankroll} \times 0.0801$ y $\sum \text{Inv} \le \text{Bankroll} \times 0.2501$.
  4. Invarianza de Techo: $\text{EV}_{\text{Global}} \le \sum \text{Premios\_Máximos}$.
* **O (Output):** Veredicto formal en consola: `EXIT CODE 0 (THE SHIELD PASSED)` o `EXIT CODE 1 (BLOCKED)`.

### ID: [LN-QBE-035-B] Registro Modular de Variables y Suficiencia Fáctica S(I)

* **Ω (Resumen):** Gobernar la transformación determinista de datos observados ($\mathcal{I}_i$) en factores estructurales normalizados ($\mathcal{A}_i, \mathcal{D}_i$) bajo la regla de suficiencia $S(\mathcal{I}_i) \in \{0, 1\}$.
* **Suficiencia $S(\mathcal{I}_i)$:** Requiere obligatoriamente que ambos clubes cuenten con partidos jugados $PJ \ge 3$, métricas de goles y tiros $SoT > 0$. Si $S(\mathcal{I}_i) = 0$, la distribución colapsa al prior de ignorancia uniforme $(1/3, 1/3, 1/3)$ y se marca como no operable.
* **Cálculo de Factores Normalizados:**
  $$A_{\text{home}} = \ln\left(\frac{0.65 \cdot xG_{\text{local}} + 0.35 \cdot GF_{\text{local}}}{\mu_{\text{liga}} / 2}\right), \quad D_{\text{away}} = -\ln\left(\frac{0.65 \cdot xGA_{\text{visita}} + 0.35 \cdot GC_{\text{visita}}}{\mu_{\text{liga}} / 2}\right)$$
* **Derivación de $xG/xGA$ en Ausencia de Tiros Profundos (H7):**
  $$\text{Fav } xG_{\text{est}} = \text{round}(\overline{GF}_{\text{Fav}} \times 1.05, 2), \quad xGA_{\text{est}} = \text{round}(\overline{GC}_{\text{Fav}} \times 0.95, 2)$$
  $$\text{Und } xG_{\text{est}} = \text{round}(\overline{GF}_{\text{Und}} \times 0.95, 2), \quad xGA_{\text{est}} = \text{round}(\overline{GC}_{\text{Und}} \times 1.10, 2)$$
* **Token Fail-Loud de Marcador Pendiente (H4):** Si un encuentro concluyó pero la federación aún no publica los números oficiales de goles, el sistema asigna el token canónico `"MARCADOR_PENDIENTE"`, prohibiendo inventar empates `"0 - 0"`.

---

### ID: [LN-QBE-065] Filtro de Descarte Temprano de Ineficiencia (+EV Gate)

* **Ω (Resumen):** Bloquear el despliegue de capital sobre activos con expectativa nula o negativa antes de ingresar al optimizador de Kelly.
* **I (Input):** Probabilidades soberanas $\hat{P}_i = (p_1, p_X, p_2)$ y cuotas comerciales $(O_L, O_E, O_V)$.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  $$\text{Si } \max_{k \in \{1, X, 2\}} \left( p_k - \frac{1.0}{O_k} \right) \le 0.00 \implies \text{Estado} = \text{QBE-00 (VETO)}$$
  Todo activo vetado recibe inversión $A_i = \$0.00\text{ MXN}$, se excluye del cómputo de ruina de cartera y se traslada a la sección de Descartes con su justificación fiduciaria.
* **O (Output):** Conjunto filtrado de activos estrictamente rentables ($K_{\text{rentables}} \subseteq K_{\text{totales}}$).

---

### ID: [LN-QBE-071] Algoritmo de Escalamiento a Piso de Ventanilla ($2.00 MXN)

* **Ω (Resumen):** Ajustar las asignaciones de boletos split que resulten inferiores al mínimo operativo del casino ($2.00 MXN) mediante escalamiento proporcional que preserva la indemnidad en tablas ($V=0$).
* **I (Input):** Asignación teórica de boletos $B_1$ y $B_2$, Momio de seguro $O_{\text{Seguro}}$, Momio de ataque $O_{\text{Ataque}}$, Código de estrategia.
* **P (Process) [BIZ-LOGIC] [ALGO-PROTECTED] (H1):**
  1. Si $0.0 < B_1 < \$2.00\text{ MXN}$ en estrategias de cobertura (`H1`, `H2`, `R1`):
     - Fijar el boleto de seguro al piso mínimo: $B_1^* = \$2.00\text{ MXN}$.
     - Recalcular la inversión total del partido para igualar el retorno exacto del seguro:
       $$A_i^* = \$2.00 \times O_{\text{Seguro}}$$
     - Derivar el boleto de ataque por diferencia: $B_2^* = A_i^* - \$2.00\text{ MXN}$.
  2. Si $0.0 < B_2 < \$2.00\text{ MXN}$: Fijar $B_2^* = \$2.00$ y $A_i^* = B_1 + \$2.00$.
  3. Para Doble Oportunidad Sintética (`QBE-R2`): Si $\min(B_1, B_2) < \$2.00$, escalar ambos boletos por el factor $k = \frac{2.00}{\min(B_1, B_2)}$.
  4. Para apuestas directas (`QBE-D1`, `D1+`): Si $A_i < \$2.00$, fijar $A_i = \$2.00$, $B_2 = \$2.00$, y asignar al boleto de seguro $B_1$ el momio real del empate con monto $\$0.00\text{ MXN}$.
* **O (Output):** Asignaciones escaladas $A_i^*$, $B_1^*$ y $B_2^*$ cumpliendo $B \ge \$2.00\text{ MXN}$ y $V=0$.

---

### ID: [LN-QBE-072] Modelo Estocástico Combinatorio de Resiliencia 3^K y Trinidad de Certeza

* **Ω (Resumen):** Modelar el espacio muestral discreto exacto de la cartera mediante enumeración combinatoria de los $3^K$ micro-estados posibles, derivando las tres anclas deterministas de certeza financiera y erradicando cualquier ordenamiento lineal arbitrario.
* **I (Input):** $K$ órdenes aprobadas, ganancias netas principales $G_i$, inversiones $A_i$, probabilidades de victoria $P_{\text{Atk}, i}$, probabilidades de empate $P_{\text{Draw}, i}$ y de ruina $\Psi_i$.
* **P (Process) [BIZ-LOGIC] [ALGO-PROTECTED]:**
  1. **Espacio Muestral ($\Omega = 3^K$):** Cada activo $i \in \{1, \dots, K\}$ posee 3 desenlaces discretos:
     - Estado 0 (Victoria Boleto de Ataque): $\text{PnL}_i = +G_i$, $\text{Prob}_i = P_{\text{Atk}, i}$.
     - Estado 1 (Empate / Cobertura): $\text{PnL}_i = \$0.00\text{ MXN}$ (o $+G_{\text{Draw}}$ en R2), $\text{Prob}_i = P_{\text{Draw}, i}$ (en estrategias directas D1: $\text{PnL}_i = -A_i$).
     - Estado 2 (Derrota / Ruina): $\text{PnL}_i = -A_i$, $\text{Prob}_i = \Psi_i$.
  2. **Evaluación Combinatoria Exhaustiva ($s \in \prod_{i=1}^K \{0, 1, 2\}$):**
     $$\text{PnL}(s) = \sum_{i=1}^K \text{PnL}_i(s_i), \quad \text{Prob}(s) = \prod_{i=1}^K \text{Prob}_i(s_i)$$
  3. **Las Tres Anclas de Certeza:**
     - **Ancla 1 (Pleno Éxito):** $\text{PnL} = +\sum G_i$, $\quad P(\text{Pleno}) = \prod_{i=1}^K P_{\text{Atk}, i} \times 100.0$.
     - **Ancla 2 (Tablas o Ganancia — La Métrica Reina):** Suma estricta de las probabilidades de todos los micro-estados donde el balance final es no-negativo:
       $$P(\text{PnL} \ge \$0.00) = \sum_{s \in \Omega: \text{PnL}(s) \ge -0.01} \text{Prob}(s) \times 100.0$$
     - **Ancla 3 (Ruina Total):** $\text{PnL} = -\sum A_i$, $\quad P(\text{Ruina Total}) = \prod_{i=1}^K \Psi_i \times 100.0$.
* **O (Output):** Diccionario `trinidad_resiliencia` con `pleno_exito`, `tablas_o_ganancia` y `ruina_total`.
* **Φ (Transición):** Hacia `[LN-QBE-080]`, `[LN-QBE-090]` y visualización en el Dashboard de Cartera.

### ID: [LN-QBE-025] Conmutador de Slates y Preservación de Estado Inter-Jornadas

* **Ω (Resumen):** Gobernar la transición de estados estocásticos y la ingesta focalizada de cuotas al conmutar entre la fecha en disputa y fechas subsecuentes con mercado abierto, habilitando la selección híbrida de cartera sin ruptura de invariantes.
* **I (Input):** `league_id: int`, `matchday_target: int`, `selected_match_ids: List[str]`, `MasterTableSnapshot`.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Aislamiento de Ingesta:** Al solicitar `matchday_target`, el scraper focalizado interactúa con el selector de la federación (`li.next.ctrlMrcdr`) o consulta la partición de FotMob sin alterar la jornada previa.
  2. **Persistencia No Destructiva:** Cada jornada mantiene su centinela `MatchdayState(league_id, matchday_num)`.
  3. **Selección Híbrida Multiversal:**
     - La cartera acepta un conjunto de partidos $K = K_{N} \cup K_{N+1}$ con $K \ge 1$.
     - Todas las órdenes se someten conjuntamente a los filtros de Triaje (`[LN-QBE-005]`), Poisson 6x6 (`[LN-QBE-040]`), Breakeven Dinámico (`[LN-QBE-050]`) y Dutching $V=0$ (`[LN-QBE-070]`).
  4. **Enforcement de Hard-Caps Globales:**
     $$\sum_{i \in K_N \cup K_{N+1}} \text{Inversión}_i \le \text{Bankroll} \times 0.2501$$
* **O (Output):** `ConsolidatedPortfolioPlan` híbrido y certificado bajo las 8 invarianzas.
* **Φ (Transición):** Hacia `[LN-QBE-070]` y `[LN-QBE-090]`.
* **[SHIELD]:** `tests/shield/test_LN_QBE_025_multi_matchday.py`

---

### ID: [LN-QBE-037] Algoritmo de Detección de Sesgo Popular en Quinielas Progol

* **Ω (Resumen):** Explotar la sobre-representación de apuestas populares en quinielas colectivas contrastando la venta pública nacional contra la distribución soberana de Q-BE.
* **I (Input):** $P_{\text{Público}} = (v_1, v_X, v_2)$ y $\hat{P}_{\text{Q-BE}} = (p_1, p_X, p_2)$.
* **P (Process) [BIZ-LOGIC]:**
  $$\text{Sesgo}_k = v_k - p_k$$
  $$\text{Si } \text{Sesgo}_{\text{Local}} \ge +0.20 \implies \text{Alerta de Sesgo: El público sobrevaloró al local; el valor (+EV) radica en X2.}$$
* **O (Output):** Clasificación de casillas: `BASE_SIMPLE`, `DOBLE_COBERTURA_SESGO`, `TRIPLE_ESTRATÉGICO`.

---

### ID: [LN-QBE-073] Algoritmo del Slider Dinámico de Certeza (Risk Dial)

* **Ω (Resumen):** Modulación estocástica adaptativa del perfil de riesgo de la cartera basada en el parámetro objetivo de certeza del usuario (`target_certeza`).
* **I (Input):** `target_certeza: float` (ej. 0.80), $K$ órdenes seleccionadas, bankroll disponible.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. Asignación inicial de órdenes según utilidades $U_{\text{Directo}}$ vs. $U_{\text{Cobertura}}$.
  2. Evaluación del espacio combinatorio $3^K$ mediante `calcular_trinidad_resiliencia_3k()`.
  3. Mientras $P(\text{PnL} \ge \$0.00) < \text{target\_certeza}$ y existan órdenes en `QBE-D1`:
     - Transmutar la orden directa más frágil a `QBE-H1` (recalcular inversión total $A_i^*$ para absorber boleto de seguro $V=0$).
     - Re-evaluar $3^K$.
  4. Si persiste la deficiencia de certeza:
     - Aplicar atenuación multiplicativa de Kelly ($\times 0.75$) sobre los activos con mayor varianza.
  5. Si la certeza sigue por debajo de $\text{target\_certeza}$:
     - Podar el partido más riesgoso derivándolo a `QBE-00` (Veto preventivo).
* **O (Output):** `ConsolidatedPortfolioPlan` ajustado con métrica de resiliencia satisfaciendo $P(\text{PnL} \ge \$0.00) \ge \text{target\_certeza}$.
* **Φ (Transición):** Hacia `[LN-QBE-070]`, `[LN-QBE-080]`, `[LN-QBE-090]`.
* **[SHIELD]:** `tests/shield/test_shield_risk_dial_modulator.py`

---

### ID: [LN-QBE-074] Optimizador de Quinielas Progol por Presupuesto

* **Ω (Resumen):** Asignación óptima combinatoria de dobles y triples en quinielas de 14 partidos sujeta a restricción presupuestaria comercial ($B$).
* **I (Input):** Presupuesto en pesos ($B$) y vector de sesgos $\text{Sesgo}_k = V_{\text{pub}, k} - P_{\text{qbe}, k}$.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Estructura de Costos Oficial Progol:** Quiniela simple $=\$15.00\text{ MXN}$. Una combinación con $D$ dobles y $T$ triples cuesta:
     $$\text{Costo} = 15.00 \times 2^D \times 3^T \le B$$
  2. **Regla de Asignación:** Ordena los 14 encuentros por magnitud de sesgo popular descendente ($|\text{Sesgo}_k|$). Asigna los Triples a los partidos de máxima incertidumbre/sesgo, los Dobles a los partidos con sesgo $\ge +0.20$, y fija como "Bases Simples" los partidos de alta probabilidad ($P_L \ge 0.65$ o $P_V \ge 0.65$).
* **O (Output):** Diccionario de respuesta `{ combinaciones_totales, costo_total_mxn, matriz_quiniela: List[Dict] }`.
* **Φ (Transición):** Hacia `/api/markets/progol/optimize` y motor de quinielas.

---

### ID: [LN-QBE-075] Ingesta Fáctica de Concursos Progol y Resiliencia Multi-Torneo

* **Ω (Resumen):** Extracción fáctica del concurso Progol vigente (14 encuentros Regular + 7 Revancha = 21 casillas) desde el DOM oficial, resolución del corte canónico local/visitante y degradación fiduciaria ante cualquier ausencia de información. Ninguna casilla congela el sistema.
* **I (Input):** Texto fáctico del DOM oficial del concurso: `concurso_num`, `bolsa` (ej. `$8,800,000.00`), `fecha_cierre` y las 21 casillas en layout de 1 o 3 líneas. Queda prohibido inventar casillas, fechas o bolsas.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Segmentación por torneo:** `Progol` ⇒ `REGULAR` (posiciones $1..14$); `Revancha` ⇒ `REVANCHA` (posiciones $1..7$ del bloque, persistidas como $15..21$ mediante $position = pos + 14$). Total: $14 + 7 = 21$ casillas.
  2. **Corte canónico local/visitante:** sobre el espacio de la línea se puntúan todas las biparticiones de tokens contra el catálogo canónico de clubes y se retiene la de mayor evidencia; nunca se divide por espacio ciego (protege abreviaturas tipo `C. AZUL`, `S. LAGUNA`, `ROSARIO CEN`).
  3. **Caso A — Vínculo Soberano:** club canónico resoluble $\wedge$ partido en `matches` $\wedge$ distribución en `sovereign_distributions` $\implies$ $P_{\text{soberana}} = (p_1, p_X, p_2)$, `match_id` poblado y `es_prior_ignorancia = False`.
  4. **Caso B — Prior de Ignorancia Fiduciaria:** club fuera de catálogo $\vee$ partido ausente $\vee$ bóveda inaccesible $\implies$
     $$P = (0.3333,\ 0.3333,\ 0.3334), \qquad \text{match\_id} = NULL, \qquad \text{es\_prior\_ignorancia} = True$$
     La casilla se persiste igualmente con su cadena fáctica (`local_raw`, `visitante_raw`) intacta.
  5. **Guardas de integridad fáctica [ALTO AL FUEGO]:** la ingesta se aborta con `exit 1` sin escribir en `slates`/`slate_items` si:
     - produce $0$ casillas fácticas (vacuidad), o
     - alguna casilla presenta par local/visitante incompleto ($\text{local\_raw} = \emptyset \vee \text{visitante\_raw} = \emptyset$), síntoma inequívoco de un corte estructural fallido. Una casilla Progol siempre tiene dos clubes: un par incompleto jamás es un dato legítimo, por lo que su persistencia silenciosa está prohibida.
  6. **Fidelidad de monto y de fecha:** `slates.bolsa_estimada` preserva la escala publicada (`$8,800,000.00` $\Rightarrow 8.8 \times 10^{6}$, con la coma como separador de miles) y `slates.fecha_cierre` permanece `NULL` mientras el sitio publique día/mes sin año: la inferencia de año o la recomposición de la escala quedan **prohibidas por no ser dato fáctico**.
* **O (Output):** Un registro `slates` (bolsa, estado `OPEN`) más 21 registros `slate_items` conforme a `[ARCH-1.5.1-C]`, cada uno con su par fáctico (`*_raw`) y su par calibrado (`*_canonico`), la terna de probabilidades y la bandera de origen epistémico.
* **Φ (Transición):** Hacia `[LN-QBE-037]` (sesgo popular), `[LN-QBE-073]` (Risk Dial) y `[LN-QBE-074]` (matriz de quiniela).
* **[SHIELD]:** `tests/shield/test_shield_progol_ingestion.py`

---

### ID: [LN-QBE-076] Arbitraje Sintético de Mejor Combinación Multi-Operador

* **Ω (Resumen):** Optimización desacoplada de cuotas para posiciones con cobertura (H1, H2, R1, R2). En lugar de contratar ambos boletos en la misma casa, se selecciona el operador que maximice el rendimiento de cada pierna por separado:
  $$O_{\text{Ataque}}^* = \max_{b \in \mathcal{B}} O_{\text{fav}, b}, \quad O_{\text{Seguro}}^* = \max_{b \in \mathcal{B}} O_{\text{emp}, b}$$
* **I (Input):** Diccionario de cuotas por operador `{operador: {L, E, V, pa}}` de un mismo partido y la identidad del favorito (`fav ∈ {L, V}`) bajo `[LN-QBE-007]`.
* **P (Process) [ALGO-PROTECTED]:**
  1. Si se selecciona la opción "Mejor Combinación", el seguro en tablas se calcula con la mejor cuota de empate disponible:
     $$B_{\text{seg}} = \frac{B_i}{O_{\text{Seguro}}^*}$$
  2. Reduce el capital absorbido por la cobertura, reduce el umbral de breakeven $\theta^*$ y rescata partidos previamente vetados por cuotas castigadas de un solo casino.
* **O (Output):** Resolución independiente por pierna `{"ataque": {"operador", "momio"}, "seguro": {"operador", "momio"}}`, reteniendo el máximo momio disponible en $\mathcal{B}$ para cada pierna.
* **Φ (Transición):** Hacia `[LN-QBE-070]` (dutching $V=0$) y `[LN-QBE-071]` (piso de ventanilla).
* **[SHIELD]:** `tests/shield/test_shield_cross_market_best_execution.py`

---

### ID: [LN-QBE-077] Ecuación de Decisión: Pago Anticipado (+PA) vs. Cuota Nominal Pura

* **Ω (Resumen):** Resuelve formalmente el dilema comercial: ¿cuándo conviene tomar una cuota nominalmente menor que incluya la cláusula de Pago Anticipado (+PA) frente a una cuota más alta sin la promoción?
* **I (Input):** `o_pa` (cuota del operador con `+PA`), `o_vanilla` (cuota nominal del operador sin `+PA`), `p_fav` (probabilidad soberana del favorito) y `delta_freeroll` (valor esperado de la cláusula `+PA`).
* **P (Process) [ALGO-PROTECTED]:**
  Sean:
  - $O_{\text{PA}}$: Cuota de la casa con Pago Anticipado (+PA) y probabilidad efectiva $p_{\text{PA}} = p_{\text{fav}} + \Delta_{\text{Freeroll}}$.
  - $O_{\text{Vanilla}}$: Cuota de la casa sin Pago Anticipado y probabilidad $p_{\text{fav}}$.
  Se define la **Cuota Umbral de Indiferencia ($O_{\text{indif}}$)**:
  $$O_{\text{indif}} = O_{\text{Vanilla}} \cdot \left( \frac{p_{\text{fav}}}{p_{\text{fav}} + \Delta_{\text{Freeroll}}} \right)$$
  **Regla de Decisión Fiduciaria:**
  - Si $O_{\text{PA}} > O_{\text{indif}} \implies$ **Dominancia de Pago Anticipado:** La protección de cobro ante empate/derrota compensa la cuota menor. Se selecciona la casa con `+PA`.
  - Si $O_{\text{PA}} \le O_{\text{indif}} \implies$ **Dominancia de Cuota Pura:** El sobreprecio del mercado supera el valor del seguro gratuito. Se selecciona la cuota nominal más alta.
* **O (Output):** Diccionario `{"recomendar_pa": bool, "ev_pa": float, "ev_vanilla": float}` con $EV = p \cdot O - 1.0$ para cada alternativa.
* **Φ (Transición):** Hacia `[LN-QBE-076]` (mejor combinación) y `[LN-QBE-070]` (asignación de capital).
* **[SHIELD]:** `tests/shield/test_shield_cross_market_best_execution.py`

---

> **Trazabilidad de registro (VARIANCE-01) — Fase 7.6:** los nodos `[LN-QBE-076]` y
> `[LN-QBE-077]` se incorporan en su familia numérica canónica (`076` y `077` tras
> `[LN-QBE-075]`, sin reutilización de identificadores). Los campos `I (Input)`, `O (Output)`
> y `Φ (Transición)` se transcriben del Contrato IPO ya fijado por el Juez Inmutable
> `tests/shield/test_shield_cross_market_best_execution.py` (`evaluar_tradeoff_pago_anticipado`
> y `resolver_mejor_combinacion_cuotas`), sin margen creativo sobre la matemática sellada.
> Juez Inmutable asociado: `tests/shield/test_shield_cross_market_best_execution.py`
> (Twin-Test en Estado RED certificado; la materialización en `src/` y `scripts/` queda
> supeditada a la autorización de la Tríada).

---

### ID: [LN-QBE-070-E] Prorrateo Resiliente de Hard-Caps con Respeto al Piso de Ventanilla
* **Ω (Resumen):** Resuelve la colisión entre el Hard-Cap global de cartera ($\sum B_i \le 25\% \cdot \text{Bankroll}$) y el piso mínimo de ventanilla ($B_{\text{seg}} \ge \$2.00\text{ MXN}$).
* **P (Process) [ARCH-PILLAR] [ALGO-PROTECTED]:**
  1. Si la suma total de inversiones supera el $25\%$ del bankroll, se calcula el factor de escala: $\text{escala} = \frac{0.25 \cdot B_{\text{total}}}{\sum B_i}$.
  2. En toda orden híbrida ($H1, H2$), si tras aplicar la escala el seguro comprimido resulta $B_{\text{seg}} < \$2.00\text{ MXN}$, se impone la **Regla de Clamping Fiduciario**:
     $$B_{\text{seg}}^* = \$2.00\text{ MXN}$$
     El ajuste residual necesario para no rebasar el tope de cartera se absorbe reduciendo el boleto de ataque ($B_{\text{prio}}$) o prorrateando sobre las demás posiciones con holgura.
  3. Garantiza simultáneamente que ningún boleto sea rechazado por la ventanilla del casino y que la cartera jamás arriesgue más del $25.0\%$.

---

### ID: [LN-QBE-078] Cuantificación Transparente del Veto Fiduciario (Descartes QBE-00)
* **Ω (Resumen):** Erradica los textos descriptivos genéricos en las órdenes descartadas. Todo partido vetado debe exponer en su contrato los parámetros cuantitativos exactos que dictaron su exclusión:
  - Probabilidad Soberana del Favorito ($p_{\text{fav}}$).
  - Cuotas de Mercado disponibles ($O_L, O_X, O_V$).
  - Alpha Edge Máximo ($\alpha_{\max} = \max_k(p_k O_k - 1)$), demostrando que $\alpha \le 0.0$ (-EV).
  - Umbral de Indiferencia de Cobertura ($\theta^* = \frac{O_{\text{fav}}}{O_{\text{fav}} - 1}$) contrastado contra el momio real del empate ($O_X$).

---

### ID: [LN-QBE-079] Operador de Contracción Fiduciaria Baricéntrica (Barycentric Dirichlet Shrinkage)
* **Ω (Resumen):** Genera la variable derivada downstream $\hat{P}_i' \in \Delta^2$ contrayendo la distribución soberana nominal hacia el baricentro de ignorancia $P^{(0)} = (1/3, 1/3, 1/3)$ mediante el factor de consenso $\Psi_{\text{epist}, i} \in [0, 1]$:
  $$\mathbf{p_{i, k}' = \Psi_{\text{epist}, i} \cdot p_{i, k} + (1.0 - \Psi_{\text{epist}, i}) \cdot \frac{1}{3} \quad \forall k \in \{1, X, 2\}}$$
* **Invarianza de Cierre:** $\sum_{k} p_{i, k}' \equiv 1.000000$ por combinación convexa exacta. No reemplaza a $\hat{P}_i$; opera como métrica de ordenamiento y ponderación de capital.
* **Frontera ontológica [DIRGEN-STRICT]:** la distribución soberana base $\hat{P}_i = (p_1, p_X, p_2)$ nace de la física del fútbol (Poisson / Dixon-Coles / Opta xG), reside intacta en `matches_json` y en la 3NF, y gobierna la cartelera y el triaje de las 9 estrategias. **Queda estrictamente prohibido modificar, sobreescribir o mutar $\hat{P}_i$.** El baricentro $P^{(0)}$ y el factor $\Psi_{\text{epist}, i} = \max\left(0.0, 1.0 - (\Delta_{\text{epist}, i}/0.12)^2\right)$ reutilizan literales ya sellados por `[LN-QBE-070-B]` (frontera $\tau_{\text{disp}} = 0.12$); cero números nuevos.
* **Materialización:** `contraer_distribucion_fiduciaria` (`[VAULT-CORE-079-SHRINKAGE]`).
* **Φ (Transición):** Hacia `[LN-QBE-081]` (probabilidad efectiva de éxito) y `[LN-QBE-082]` (asignación monótona de capital).
* **[SHIELD]:** `tests/shield/test_shield_fiduciary_shrinkage_and_monotonic_ordering.py`

---

### ID: [LN-QBE-081] Probabilidad Efectiva de Éxito de la Posición (P_éxito') y Ordenamiento Lexicográfico
* **Ω (Resumen):** Calcula la certeza real de preservar o incrementar el capital según la estructura de cobertura:
  $$P_{\text{éxito}}' = \begin{cases}
  p_{\text{fav}}' + p_{\text{emp}}' & \text{para estrategias híbridas con seguro en tablas } (QBE-H1, QBE-H2) \\
  p_{\text{fav}}' & \text{para apuestas directas sin seguro } (QBE-D1, QBE-D2) \\
  p_{\text{dog}}' & \text{para estrategias reversas } (QBE-R1, QBE-R2) \\
  p_{\text{fav}}' / (p_{\text{fav}}' + p_{\text{dog}}') & \text{para apuestas sin empate } (QBE-C1) \\
  0.3333 & \text{para cuarentena } (QBE-00)
  \end{cases}$$
* **Regla de Ordenamiento Lexicográfico de Cartera:**
  $$\mathbf{\text{Clave Primaria: } P_{\text{éxito}}' \quad \text{Descendente} \quad \longrightarrow \quad \text{Clave Secundaria: } \text{Ganancia Neta} \quad \text{Descendente}}$$
* **Materialización:** `calcular_probabilidad_exito_estrategia` y `ordenar_cartera_por_certeza_lexicografica` (`[VAULT-CORE-079-SHRINKAGE]`). El campo derivado viaja como `prob_exito_efectiva` dentro del payload de partidos aprobados (`[ARCH-1.4.17]`).
* **Φ (Transición):** Hacia `[LN-QBE-082]`.
* **[SHIELD]:** `tests/shield/test_shield_fiduciary_shrinkage_and_monotonic_ordering.py`

---

### ID: [LN-QBE-082] Principio de Asignación Monótona de Capital
* **Ω (Resumen):** El capital asignado debe ser una función monótona no creciente de la certeza:
  $$P_{\text{éxito}, (1)}' \ge P_{\text{éxito}, (2)}' \ge \dots \ge P_{\text{éxito}, (K)}' \implies B_{(1)} \ge B_{(2)} \ge \dots \ge B_{(K)}$$
  El partido con mayor probabilidad de éxito recibe la mayor inversión (hasta el hard-cap del 8.0%), y ningún partido con menor probabilidad de éxito puede recibir un importe superior a uno precedente.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC] (`asignar_capital_monotono_cartera`):**
  1. Bolsa de jornada $= \text{Bankroll} \times 0.25$; tope individual $= \text{Bankroll} \times 0.08$.
  2. Pesos $w_i \propto P_{\text{éxito}, i}'$ con piso analítico de probabilidad $0.01$ (evita división por cero; no altera la jerarquía).
  3. $B_i = \min\left(\text{cap}_{8\%},\ \max(5.00,\ \text{bolsa} \cdot w_i)\right)$ y luego la **guarda de monotonía**: $B_{(i)} := \min\left(B_{(i)},\ B_{(i-1)}\right)$.
  4. Prorrateo uniforme si $\sum B_i > 0.25 \cdot \text{Bankroll}$ (escalado preserva el orden).
* **Conciliación con `[LN-QBE-070-B]` (Kelly Fraccional Atenuado):** queda **erradicado** el piso `max(0.02, f_kelly)` como generador de tamaño. La delegación analítica `calcular_kelly_atenuado` subsiste en `build_plan()` **exclusivamente como cota de auditoría NO vinculante** (control de deuda técnica TD-COR-01), reportada en `control_portafolio.desglose_bankroll.auditoria_kelly_atenuado`; ningún peso de cartera se deriva de ella.
* **Materialización:** `asignar_capital_monotono_cartera` (`[VAULT-CORE-079-SHRINKAGE]`), consumida antes del despacho de órdenes (`[ARCH-1.4.18]`).
* **Φ (Transición):** Hacia `[LN-QBE-070-B]` (hard-caps constitucionales) y `[LN-QBE-071]` (piso de ventanilla).
* **[SHIELD]:** `tests/shield/test_shield_fiduciary_shrinkage_and_monotonic_ordering.py`

### ID: [LN-QBE-083] Formalización de la Tetralogía de Escenarios de Liquidación
* **Ω (Resumen):** En toda posición híbrida con cobertura en tablas ($H1, H2$) dotada de cláusula $+PA$, la tarjeta de ejecución debe cuantificar y desglosar de forma determinista cuatro escenarios de desenlace:
  1. **Ganancia Principal:** Victoria ordinaria del favorito.
  2. **Cobertura en Empate:** Recuperación del $100\%$ del capital ($V=0$).
  3. **Pago Anticipado con Empate (¡Doble Cobro Simultáneo!):** *(rótulo canónico de UI sancionado por la Resolución `VARIANCE-01` de la Fase 7.9: `Pago Anticipado con Empate:`; el rótulo histórico `Pago Anticipado + Empate:` queda derogado. Se exhibe únicamente si `pa_activo = True` y existe boleto seguro.)*
     $$\text{Retorno Bruto} = B_{\text{prio}} \cdot O_{\text{fav}} + B_i$$
     $$\text{Ganancia Neta} = B_{\text{prio}} \cdot O_{\text{fav}} \implies \text{ROI}_{\text{doble}} = \left( 1 - \frac{1}{O_{\text{emp}}} \right) O_{\text{fav}} \times 100\%$$
     Se activa si el favorito alcanza ventaja $+2$ en $t < 90'$ y el encuentro concluye empatado (ej. $2-2$).
  4. **Salida de Emergencia (Rompe-Quinielas):** Regla de CashOut defensivo si el rival anota primero ($0-1$) y el juego se empata en el 2T ($1-1$), asegurando el rescate del $100\%$ de la inversión ($B_i$).
* **Φ (Transición):** Hacia `[ARCH-1.4.19]` (monotonía fiduciaria post-piso de ventanilla), `[DES-QBE-061]` (formato dual de cuotas) y `[DES-QBE-062]` (tetralogía de escenarios), materializados en `src/web/static/js/app.js`.
* **[SHIELD]:** `tests/shield/test_shield_ticket_ux_and_cashout_refinement.py`


---

### ID: [LN-QBE-084] El Operador Canónico de Selección por Masa Acumulada P' en Progol
* **Ω (Resumen):** Transforma la distribución sobre combinaciones en un problema de optimización determinista: ordena el universo restringido de boletas por probabilidad conjunta descendente y selecciona las primeras $M$ posiciones para maximizar la masa probabilística capturada bajo presupuesto cerrado.
* **P (Process) [ARCH-PILLAR] [ALGO-PROTECTED]:**
  1. Para $K=14$ partidos, se construye el vector ordenado $P'$ tal que:
     $$P(B_{(1)}) \ge P(B_{(2)}) \ge \dots \ge P(B_{(N)})$$
  2. Dado un presupuesto $B_{\text{presupuesto}}$, el cupo de boletas sencillas es $M = \lfloor B_{\text{presupuesto}} / 15.0 \rfloor$.
  3. Se selecciona el subconjunto óptimo $\mathcal{A}_M = \{ B_{(1)}, B_{(2)}, \dots, B_{(M)} \}$.
  4. **Teorema de Maximización de Masa:** $\mathcal{A}_M$ maximiza estrictamente la masa acumulada $C(M) = \sum_{j=1}^M P(B_{(j)})$ frente a cualquier otro subconjunto de tamaño $M$. Se descarta toda selección heurística o subjetiva de boletas.
* **Materialización:** `seleccionar_cobertura_binaria_optima`, `generar_universo_restringido_y_ordenar_p_prime` y `seleccionar_primeras_m_combinaciones` (`[VAULT-CORE-084-PROGOL-P-PRIME]`, `src/core/contracts/progol_math.py`).
* **Φ (Transición):** Hacia `[LN-QBE-085]` (espacio restringido) y `[LN-QBE-086]` (descenso por Hamming).
* **[SHIELD]:** `tests/shield/test_shield_progol_p_prime_mass_optimizer.py`

### ID: [LN-QBE-085] Cobertura Binaria Óptima (|S_i| ≤ 2) y Construcción del Espacio Restringido
* **Ω (Resumen):** Traslada la restricción de cobertura de AxR a Progol. En cada partido se seleccionan los dos desenlaces con mayor probabilidad fiduciaria ($c_i = p_{(1)}' + p_{(2)}'$), acotando el espacio combinatorio de búsqueda a $2^d 3^t$ estados (donde $d+t+s=14$) y descartando de raíz el 99.98% del hipercubo sin masa real.
* **Materialización:** `seleccionar_cobertura_binaria_optima` (`[VAULT-CORE-084-PROGOL-P-PRIME]`, `src/core/contracts/progol_math.py`).
* **Φ (Transición):** Hacia `[LN-QBE-084]` (universo $2^{14}$ y secuencia $P'$) y `[LN-QBE-086]` (descenso por distancia de Hamming).
* **[SHIELD]:** `tests/shield/test_shield_progol_p_prime_mass_optimizer.py`

### ID: [LN-QBE-086] Descenso por Distancia de Hamming hacia Premios Menores (L ∈ {13, 12, 11, 10})
* **Ω (Resumen):** Cuando el presupuesto disponible no alcanza para cubrir la masa del primer lugar o existen partidos con prior de ignorancia ($S(\mathcal{I})=0 \implies 1/3, 1/3, 1/3$), el sistema no se arriesga a ciegas buscando el 14: desciende ordenadamente la mira a garantizar premios secundarios en la tabla oficial de Pronósticos mediante bolas de Hamming:
  $$d_H(B, Y) \le 14 - L \quad \text{para } L \in \{13, 12, 11, 10\}$$
* **Materialización:** `reducir_a_garantia_hamming_l` (`[VAULT-CORE-084-PROGOL-P-PRIME]`, `src/core/contracts/progol_math.py`).
* **Φ (Transición):** Hacia `[LN-QBE-074]` (orquestador por presupuesto vigente, no modificado).
* **[SHIELD]:** `tests/shield/test_shield_progol_p_prime_mass_optimizer.py`

### ID: [LN-QBE-087] Algoritmo de Progol Revancha (K=7 Todo o Nada)
* **Ω (Resumen):** La Revancha ($K=7$) es un concurso independiente con bolsa propia y regla estricta de 7 aciertos obligatorios (sin premios secundarios). Queda prohibido el descenso por Hamming; opera mediante cobertura rectangular pura ($2^d 3^t$) maximizando la masa conjunta sobre los 2,187 estados posibles.
* **[SHIELD]:** PENDIENTE DIFERIDO (Fase Revancha K=7 en directiva complementaria).
* **Nota de trazabilidad (VARIANZA V-2 / ALT-1):** el nodo se promulga sin Juez en el Paso 2 de la Directiva Volumen III (el Juez mandatado cubre `[LN-QBE-084/085/086]`); queda fuera del alcance de `[ARCH-1.4.20]`.

### ID: [LN-QBE-088] Resolver Semántico JIT de Competiciones y Clubes Internacionales
* **Ω (Resumen):** Resuelve de forma determinista y bajo demanda la identidad del torneo y de los clubes para cada casilla de Progol, consultando el endpoint de búsqueda estructurada de FotMob (`/api/search/searchapi?term={club}`).
* **I (Input):** Nombre crudo del club en Progol (ej. `"GIRONA"`, `"R SOCIED. B"`, `"CROACIA"`).
* **P (Process) [ARCH-PILLAR] [ALGO-PROTECTED]:**
  1. Sanitizar el término y consultar el endpoint estructurado de FotMob en tiempo $O(1)$.
  2. Parsear el payload JSON extrayendo: `team_id`, `team_name`, `league_id`, `league_name` y `country`.
  3. Si la búsqueda arroja cero coincidencias (ej. divisiones de ascenso sin cobertura óptica o amistosos exóticos):
     - Declarar la casilla como **No Indexada**.
     - Asignar de forma fiduciaria el **Prior de Ignorancia $(1/3, 1/3, 1/3)$** bajo `[LN-QBE-075]`.
     - Prohibir la invención de identificadores ficticios (`[GOVERNANCE-01]`).
* **O (Output):** Diccionario tipado `DiscoveredTeamPayload` con los metadatos oficiales del club y su liga.
* **Φ (Transición):** Hacia [LN-QBE-089] (Auto-registro de ligas) y [LN-QBE-084] (Masa P').

### ID: [LN-QBE-089] Parámetros Macro de Competiciones Descubiertas Dinámicamente
* **Ω (Resumen):** Al registrar una nueva competición en SQLite 3NF descubierta vía JIT, se le asignan parámetros macro de balance de energía (Volumen I, Sección 4.9.1):
  $$\alpha = \ln(\mu_{\text{liga}}) - \ln(1 + e^{\bar{\gamma}_{\text{home}}})$$
  donde por defecto para ligas de primera división $\mu_{\text{liga}} = 2.60$ y $\bar{\gamma}_{\text{home}} = 0.15$, salvo cálculo empírico directo sobre los marcadores históricos descargados.

### ID: [LN-QBE-090-B] Heurística de Vinculación y Emparejamiento Multi-Torneo en Slates
> **Trazabilidad de registro (VAR-2026-LN-QBE-090 — Colisión histórica resuelta por Decreto de Saneamiento):**
> el identificador `[LN-QBE-090]` ya se encuentra **sellado** en este mismo libro (línea 566,
> *Escudo Forense de Invarianzas (Shield Release Gate)*, referenciado por `src/core/auditor.py:4`
> y `src/pipeline/engine.py:482`). Por axioma de **cero reutilización** de identificadores canónicos,
> este nodo se remapea a `[LN-QBE-090-B]`, preservando el sufijo de familia y sin alterar una sola
> coma de su contenido normativo. La primera instancia (L566) conserva la propiedad indisputable de
> `[LN-QBE-090]`. Evidencia fáctica de la colisión: auditoría de unicidad del registro (Paso 0).
* **Ω (Resumen):** Permite vincular casillas de quinielas con partidos de competiciones internacionales mediante coincidencia cruzada de identidades canónicas (`Match.home_team_slug` y `Match.away_team_slug`) independientemente de si la liga es local o foránea.
* **Materialización:** el cotejo elástico ya gobernado en `procesar_casilla_con_resiliencia` (`src`, `scripts/daemons/centinela_progol.py`, `[VARIANCE-05 ratificada]`) opera por contención mutua de slugs normalizados (`club-`, `deportivo-`) sobre TODA la tabla `matches`, sin discriminar competición; la exploración JIT de competiciones foráneas queda legislada en `[ARCH-1.4.22]`.
* **Frontera de inmunidad:** el emparejamiento JAMÁS fabrica probabilidad; sólo localiza el partido. La probabilidad proviene exclusivamente de `sovereign_distributions` o degrada al Prior Fiduciario `[LN-QBE-075]`.

### ID: [LN-QBE-091] Modelo de Intensidades para Divisiones Inferiores sin Opta xG
* **Ω (Resumen):** En ligas sin cobertura óptica de tiros (Liga Premier FMF, divisiones menores), las intensidades $(\lambda_H, \lambda_A)$ se derivan directamente del balance de goles observados ($GF/JJ, GC/JJ$) y la fuerza relativa del rival sobre el grafo de la competición:
  $$\ln(\lambda_H) = \alpha_{\text{div}} + \bar{\gamma}_{\text{home}} + \left( \frac{GF_H}{\mu_{\text{div}} \cdot JJ_H} - 1 \right) - \left( 1 - \frac{GC_A}{\mu_{\text{div}} \cdot JJ_A} \right)$$
* **Gobernanza:** Satisface estrictamente la conservación de masa $\mu_{\text{div}} = 2.45$ y permite emitir distribuciones soberanas legítimas sin inventar datos.

### ID: [LN-QBE-093] Axioma de Pureza de Sensores de Ingesta y Contratos DTO de Capa 1 (Data Nexus)
* **Ω (Resumen):** Los sensores de ingesta (`src/ingestion/providers/`) son entidades puras de red: transforman respuestas HTTP (HTML/JSON) en contratos inmutables (DTOs Pydantic V2, `src/ingestion/schemas.py`) y JAMÁS tocan la capa de persistencia. El acceso al snapshot certificado de SQLite ante fallos de red se ejerce exclusivamente vía inyección de dependencias (un puerto/callable `fallback_loader` pasado como argumento), preservando `[LN-QBE-017]` sin acoplamiento estático interno.
* **I (Input):** Respuesta cruda de red (`httpx` / `BeautifulSoup`) y, opcionalmente, un puerto inyectado por el llamador que resuelve el último snapshot certificado de la bóveda 3NF.
* **P (Process) [ARCH-PILLAR]:**
  1. Extraer y sanear la respuesta cruda del proveedor externo (cero valores inventados, `[GOVERNANCE-01]`).
  2. Tipificar y validar el resultado contra el DTO correspondiente declarado en `src/ingestion/schemas.py`.
  3. Ante contingencia de red, invocar el puerto inyectado `fallback_loader(league_id)`; si no fue inyectado, degradar explícitamente a lista vacía con traza de log (CERO MOCKS).
* **O (Output):** Objetos tipados de `src/ingestion/schemas.py` (ej. `ScheduledMatchDTO`, `SeasonOverviewDTO`, `ProgolContestDTO`, `Odds1X2DTO`).
* **Φ (Transición):** Hacia el `IngestionCoordinator` (Capa 5), responsable de la composición e inyección de los puertos de persistencia.
* **[SHIELD]:** `tests/shield/test_shield_data_nexus_providers.py`

### ID: [LN-QBE-094] Algoritmo de Desambiguación Temporal en Ventana Crítica [t_cierre ± 72h]
* **Ω (Resumen):** Resuelve de forma determinista la asignación de competición y partido cuando un mismo par de clubes se enfrenta en múltiples torneos en fechas cercanas (ej. Cruz Azul vs. América en Liga MX vs. Concachampions).
* **I (Input):** `team_a: str`, `team_b: str`, `t_cierre: datetime`, `candidatos: List[ScheduledMatchDTO]`.
* **P (Process) [ARCH-PILLAR] [ALGO-PROTECTED]:**
  1. Definir la Ventana Crítica de Disputa:
     $$\mathcal{W} = [t_{\text{cierre}} - 24\text{ h}, \; t_{\text{cierre}} + 72\text{ h}]$$
  2. Filtrar el conjunto de candidatos donde ambos clubes participan:
     $$\mathcal{M}_{\text{admisibles}} = \{ m \in \text{candidatos} \mid m.t_{\text{kickoff}} \in \mathcal{W} \}$$
  3. Si $|\mathcal{M}_{\text{admisibles}}| == 1 \implies$ Se vincula unívocamente ese partido y su `competition_id`.
  4. Si $|\mathcal{M}_{\text{admisibles}}| > 1 \implies$ Seleccionar el partido con menor distancia temporal absoluta:
     $$m^* = \arg\min_{m \in \mathcal{M}} |m.t_{\text{kickoff}} - t_{\text{cierre}}|$$
  5. Si $|\mathcal{M}_{\text{admisibles}}| == 0 \implies$ Marcar como no indexado y degradar al Prior Fiduciario `[LN-QBE-075]`.
* **O (Output):** `DisambiguatedMatchDTO(match_id, competition_id, kickoff_utc, is_ambiguous: bool)`.
* **Φ (Transición):** Hacia `[LN-QBE-088]` y persistencia en `slate_items.match_id`.
* **[SHIELD]:** `tests/shield/test_shield_temporal_disambiguation_and_provisioner.py`

---

### ID: [LN-QBE-095] Guardas Léxicas de Identidad de Género y Categoría (Femenil, Filiales, Sub-20)
* **Ω (Resumen):** Erradica colisiones de identidad entre clubes homónimos de diferentes divisiones o ramas deportivas mediante etiquetado canónico y derivación estricta de slugs.
* **I (Input):** `raw_team_name: str`.
* **P (Process) [ARCH-PILLAR] [ANTI-BUG]:**
  1. Detección de patrones regex (case-insensitive):
     - Femenil: `\b(femenil|fem|women|w)\b` $\implies$ `categoria = "FEMENIL"`.
     - Filial / Reserva: `\b(b|ii|filial|promesas)\b` $\implies$ `categoria = "FILIAL"`.
     - Formativas: `\b(sub-?20|sub-?23|u-?20|u-?23)\b` $\implies$ `categoria = "SUB20"`.
     - Por defecto: `categoria = "VARONIL_MAYOR"`.
  2. Generación de Slug Canónico Inmutable:
     - El slug debe conservar el sufijo de categoría: `club-america-femenil`, `real-sociedad-b`, `chivas-sub20`.
     - Queda estrictamente prohibido truncar el sufijo de género para evitar colisiones con el primer equipo varonil (`club-america`).
* **O (Output):** `CategorizedEntityDTO(canonical_name: str, canonical_slug: str, category: str)`.
* **Φ (Transición):** Hacia `[LN-QBE-012]` (Normalizador) y `[ARCH-1.5.11]` (Aprovisionador).
* **[SHIELD]:** `tests/shield/test_shield_temporal_disambiguation_and_provisioner.py`

---

> **Trazabilidad de registro (VARIANCE-01) — Fase 8 (Colisión `LN-QBE-080`):** el nodo
> solicitado como `[LN-QBE-080]` por la Directiva P.I.R. **colisiona** con el nodo YA sellado
> `[LN-QBE-080] Compilador de Reportes Oficiales y PDF A4` (línea 555 de este libro,
> `src/reporting/compiler.py`). Conforme al precedente de trazabilidad `[LN-QBE-076]`/`[LN-QBE-077]`
> (*"sin reutilización de identificadores"*), el bloque se remapea a **`081`** y **`082`**
> conservando el orden ascendente, el contenido matemático VERBATIM y la frontera
> `[DIRGEN-STRICT]`. Solicitud formal registrada en
> `docs/DIRGEN_VARIANCE_REQUEST_LN-QBE-080_COLLISION.md`.

---

**BASE DE GOBIERNO SELLADA BAJO EL KYBERN FRAMEWORK v8.0 / v12.0 — GRAFO LÓGICO INMUTABLE.**

```