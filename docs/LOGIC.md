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
  3. **Aduana de Identidad Estricta (Saneamiento O-09):** Queda estrictamente prohibida la validación por contención de subcadenas (`texto in alias` o `alias in texto`). La coincidencia se validará exclusivamente por igualdad exacta, ratio de `SequenceMatcher` $\ge 0.78$ o distancia de Levenshtein $\le 2$.
  4. **Fail-Loud Mandatorio:** Si un equipo no puede resolverse con certeza con los umbrales anteriores, se lanzará obligatoriamente `NormalizationException`. Prohibido el retorno silencioso del texto crudo.
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
* **Aduana de Sanidad Comercial de Overround en Ventanilla:**
  Toda tupla de cuotas 1X2 $(O_L, O_E, O_V)$ debe satisfacer obligatoriamente que la suma de probabilidades implícitas brutas (margen comercial) pertenezca al intervalo admisible:
  $$S = \frac{1}{O_L} + \frac{1}{O_E} + \frac{1}{O_V} \in [0.8500, 1.3000]$$
  Si $S < 0.8500$ (margen negativo / cuotas corruptas o duplicadas) o $S > 1.3000$ (overround usurario o cuota rota), el partido entra de forma atómica en **Cuarentena Fiduciaria Total (`QBE-00`)**, prohibiendo cualquier cálculo de $+EV$ o colocación de capital.

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
### ID: [LN-QBE-020-C] Kernel H2H Empírico en Eje Localía (Generador C)

* **Ω (Resumen):** Proyectar la evidencia de enfrentamientos directos sobre el símplex $\Delta^2$ en el **eje localía** (LOCAL / EMPATE / VISITA) del fixture evaluado, como Generador C empírico que alimenta la discrepancia epistémica $\Delta_{\text{epist}}$. **No sustituye a `[LN-QBE-020]`**: aquel opera sobre el eje FAVORITO / EMPATE / UNDERDOG y exige exactamente 5 partidos.
* **I (Input):** `h2h_matches` (secuencia de enfrentamientos en perspectiva del fixture evaluado: `goles_local`, `goles_visita`, `dias_antiguedad`) y vida media $\tau = 180$ días.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Reutilización de la constante sellada (cero duplicación):** $\kappa = \ln(2)/\tau$ tomado de `[LN-QBE-020]` (`src/core/temporal.py: TemporalDecayEngine.KAPPA` cuando $\tau = 180$).
  2. Ponderación exponencial continua: $w_k = \exp(-\kappa \cdot \Delta t_k)$ con $\Delta t_k = \max(0, \text{dias\_antiguedad}_k)$.
  3. Acumulación de masa efectiva por desenlace y normalización sobre el símplex:
     $$w_{\text{LOC}} = \sum_{k: GL_k > GV_k} w_k, \quad w_{\text{EMP}} = \sum_{k: GL_k = GV_k} w_k, \quad w_{\text{VIS}} = \sum_{k: GL_k < GV_k} w_k$$
     $$p_{\text{local}} = \frac{w_{\text{LOC}}}{W}, \quad p_{\text{empate}} = \frac{w_{\text{EMP}}}{W}, \quad p_{\text{visita}} = \frac{w_{\text{VIS}}}{W}, \quad W = \sum_k w_k > 0$$
  4. **Fail-Loud (Cero Mocks Sintéticos):** secuencia vacía o $W \le 0$ $\implies$ `ValueError`. La ausencia de antecedentes se gobierna por la Ley Zero-H2H `[LN-QBE-020-B]`; queda terminantemente prohibido fabricar partidos históricos.
* **O (Output):** `H2HKernelResult` (`p_local`, `p_empate`, `p_visita`, `suma_probabilidades`, `peso_total_efectivo`) declarado en `src/models/analytics.py`.
* **Φ (Transición):** Hacia la calibración de $\Delta_{\text{epist}}$ y la fusión híbrida de `[LN-QBE-040]`.
* **[SHIELD]:** `tests/shield/test_shield_bayesian_form_and_h2h.py`
* **Trazabilidad de registro:** identificador promulgado por Decreto del Sprint 3 (enmienda D-2): el kernel decretado no podía sellarse bajo `[LN-QBE-020]` (ya materializado en `src/core/temporal.py` con Juez `abstract_test_LN_QBE_020_temporal.py`), evitando así una doble fuente de verdad sobre un nodo `[ALGO-PROTECTED]`.

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
* **Constantes Formalizadas (CONSTANTS.md §8):** `BASELINE_LIGA`, `SATURACION_MADUREZ_J`, `OMEGA_MIN`, `OMEGA_MAX`, `BLEND_XG`, `BLEND_GF`, `CLAMP_GOLES_MIN`, `CLAMP_GOLES_MAX`.
* **O (Output):** `PoissonAnalyticsResult`.
* **Φ (Transición):** Hacia **[LN-QBE-050]**.

---

### ID: [LN-QBE-040-B] Techo Conjunto de Intensidad Ofensiva en Espacio Logarítmico (Anti-Resonancia)

* **Ω (Resumen):** Mecanismo de compresión hiperbólica conjunta sobre el diferencial neto atacante-defensor $(A_H^* - D_A^*)$ para erradicar la sobre-amplificación exponencial en duelos entre plantillas de alta jerarquía.
* **I (Input):** Factores individuales amortiguados $A_H^*, D_A^*$ y constante de compresión $\kappa_{\text{net}} = 0.2500$.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  $$\Delta_{\text{net}} = \kappa_{\text{net}} \cdot \tanh\left(\frac{A_H^* - D_A^*}{\kappa_{\text{net}}}\right) \quad \text{con } \kappa_{\text{net}} = 0.2500$$
  $$\eta_H = \alpha + \gamma_{\text{contextual}} + \Delta_{\text{net}} + C_H$$
  Garantiza analíticamente que $\lambda_H \le 1.8600\text{ xG}$ en partidos equilibrados de liga, preservando la ligadura $\alpha$ y la conservación de masa global de goles.
* **O (Output):** Intensidades físicas acotadas $\lambda_H, \lambda_A$.
* **Φ (Transición):** Hacia `[LN-QBE-040]` (Matriz Dixon-Coles 2D) y `[VAULT-CORE-001]`.
* **[SHIELD]:** `tests/shield/test_shield_portfolio_integrity_and_floor.py`

---

### ID: [LN-QBE-040-C] Parámetro de Correlación Táctica Bivariada ($\rho$) en Partidos de Baja Anotación

* **Ω (Resumen):** Conmutar dinámicamente la correlación de Dixon-Coles del nodo `[LN-QBE-040]` según el régimen de anotación proyectado, concentrando masa fiduciaria en los vértices de empate de baja anotación $(0,0)$ y $(1,1)$ para erradicar el déficit estructural del vértice $X$ frente a la migración de empates de baja anotación hacia $P_{\text{mid}}$ en partidos cerrados.
* **I (Input):** Intensidades físicas certificadas $\lambda_H, \lambda_A$ (post-techo anti-resonancia `[LN-QBE-040-B]`); constantes selladas $\rho_{\text{base}} = -0.0500$, $\rho_{\text{táctica}} = -0.1200$ y frontera $\Sigma_{\text{corte}} = 2.6500$ xG (CONSTANTS.md §2).
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  $$\rho_{\text{efectivo}}(\lambda_H, \lambda_A) = \begin{cases} -0.1200 & \text{si } \lambda_H + \lambda_A \le 2.6500 \\ -0.0500 & \text{si } \lambda_H + \lambda_A > 2.6500 \end{cases}$$
  1. **Cláusula de invocación obligatoria:** todo cómputo de la matriz bivariada que NO reciba un $\rho$ explícito distinto del default sellado ($\rho_{\text{base}} = -0.0500$) DEBE resolver su correlación con `resolver_rho_dixon_coles(lambda_h, lambda_a)`. El parámetro deja de ser constante de diseño y pasa a ser función del régimen proyectado.
  2. **Preservación verbatim del plano sellado:** con $\rho = 0.0000$ (escape hatch "sin corrección Dixon-Coles") y con cualquier $\rho$ explícito distinto del default, la transcripción del factor $\tau(x, y)$ y de las cotas de admisibilidad de la Sección 5.16.1 permanecen intactas, garantizando el Teorema de No-Negatividad Estricta (Invariante I13).
  3. **Sentido físico del signo:** con la convención $\tau$ sellada, $\rho < 0$ eleva $\tau(0,0)$ y $\tau(1,1)$ y deprime $\tau(0,1)$/$\tau(1,0)$; en partidos cerrados la matriz de Poisson pura subestima el empate por el truncamiento del retículo $[0,5]$.
* **O (Output):** $\rho_{\text{efectivo}}$ (adimensional) y matriz bivariada renormalizada sobre el retículo $[0, 5]$.
* **Φ (Transición):** Hacia `[LN-QBE-050]` (Breakeven), `[VAULT-CORE-004]` (generador Dixon-Coles) y `[VAULT-CORE-005]` (orquestador soberano).
* **[SHIELD]:** `tests/shield/test_shield_rho_tactico_calibration.py`
* **[RÉGIMEN]:** `[DIRGEN-STRICT]` para la ley de resolución, las constantes y el factor $\tau$; el re-etiquetado del `motivo` del Radar de Descartes es `[DBBD-FUNGIBLE]`.

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

### ID: [LN-QBE-059] Partición Canónica del 2-Símplex Δ² sobre P' y Concentración Dinámica Γ [ARCH-PILLAR]
* **Ω (Resumen):** Segmenta exhaustiva y deterministamente el espacio fiduciario Δ² en ocho familias morfológicas disjuntas a partir de variedades de cobertura bivariada, gobernadas por el parámetro interactivo de concentración de masa Γ ∈ {0.67, 0.70, 0.75}.
* **I (Input):** `distribucion_contraida: Tuple[float, float, float]` ($P'$) y `gamma_threshold: float` ($\Gamma \in \{0.67, 0.70, 0.75\}$, default 0.67).
* **P (Process) [ALGO-PROTECTED]:**
  1. **Aduana de Dominancia Univariada:**
     - Si $p_1' \ge \Gamma \implies$ Familia `HEGEMONIA_LOCAL` ($\mathcal{M}_{\text{DOM-L}}$).
     - Si $p_2' \ge \Gamma \implies$ Familia `HEGEMONIA_VISITANTE` ($\mathcal{M}_{\text{DOM-V}}$).
  2. **Aduana de Variedad de Cobertura Bivariada:**
     - Si $p_1' + p_X' \ge \Gamma$ (implica $p_2' \le 1 - \Gamma$):
       * Si $p_1' \ge p_X' \implies$ Familia `ASIMETRIA_LOCAL` ($\mathcal{M}_{\text{ASIM-L}}$).
       * Si $p_X' > p_1' \implies$ Familia `ASIMETRIA_EMPATE_LOCAL` ($\mathcal{M}_{\text{ASIM-X(L)}}$).
     - Si $p_2' + p_X' \ge \Gamma$ (implica $p_1' \le 1 - \Gamma$):
       * Si $p_2' \ge p_X' \implies$ Familia `ASIMETRIA_VISITANTE` ($\mathcal{M}_{\text{ASIM-V}}$).
       * Si $p_X' > p_2' \implies$ Familia `ASIMETRIA_EMPATE_VISITANTE` ($\mathcal{M}_{\text{ASIM-X(V)}}$).
     - Si $p_1' + p_2' \ge \Gamma$ (implica $p_X' \le 1 - \Gamma$) $\implies$ Familia `BIPOLARIDAD_TERRITORIAL` ($\mathcal{M}_{\text{BIPOLAR}}$).
     - **Regla de Prioridad de Banda Máxima [VAULT-CORE-059]:** En caso de solapamiento donde múltiples bandas bivariadas alcancen $\Gamma$, prevalece estrictamente aquella de **mayor masa combinada** (*max-band*); ante empate exacto de masas, el orden canónico de precedencia es $(1X) > (2X) > (12)$. Maximizar la masa del par cubierto es idéntico a **minimizar el riesgo residual desprotegido** ($1 - \max(s)$). (Enmienda legislativa por resolución vinculante `VAR-11` / ALT-1, Director Humano, 2026-10-07.)
  3. **Aduana de Entropía:**
     - Si $\max(p_1' + p_X', \; p_2' + p_X', \; p_1' + p_2') < \Gamma \implies$ Familia `PARIDAD_CIEGA` ($\mathcal{M}_{\text{PARIDAD-0}}$).
     - **Teorema de Frontera de Entropía [VAULT-CORE-059]:** Puesto que $s_{1X} + s_{2X} + s_{12} = 2(p_1' + p_X' + p_2') = 2.0$, se cumple siempre $\max(s_{1X}, s_{2X}, s_{12}) \ge 2/3 \approx 0.6667$. Puesto que la terna canónica $\Gamma \in \{0.67, 0.70, 0.75\}$ satisface $\Gamma > 2/3$ en los tres modos del selector, la familia `PARIDAD_CIEGA` es alcanzable de forma canónica en $\Gamma = 0.67$, $\Gamma = 0.70$ y $\Gamma = 0.75$; el umbral quemado $0.65$ queda erradicado. (Enmienda legislativa `VAR-11` + Directiva de Integración Capa 0→Capa 1, 2026-10-07.)
* **O (Output):** `MorphologyClassification(familia: str, desenlace_ataque: str, desenlace_seguro: Optional[str], riesgo_residual: float)`.
* **Φ (Transición):** Hacia `[LN-QBE-060-B]` (Triaje Determinista).
* **[SHIELD]:** `tests/shield/test_shield_simplex_morphology_and_gamma_slider.py`

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
  **Cláusula de Pureza de Mercado (Saneamiento O-05):** El triaje y el evaluador exigen la presencia fáctica de las cuotas comerciales. Queda estrictamente prohibido el uso de valores por defecto (fallbacks), interpolaciones o proxis sintéticos para `O_L`, `O_E` u `O_V`. Si alguno de los precios no está disponible o es menor a 1.0, la tupla se considera inválida y el partido colapsa inmediatamente a `QBE-00` por Veto Fiduciario.
  Árbol de decisión determinista en cascada de 7 pasos:
  1. Si $S(\mathcal{I}_i) = 0 \lor \Delta_{\text{epist}} > 0.12 \implies$ **`QBE-00`** (Cuarentena / Capital = $\$0.00$).
  2. Si la morfología de Capa 0 resuelve `HEGEMONIA_LOCAL` o `HEGEMONIA_VISITANTE` bajo el umbral $\Gamma$ recibido $\land \Delta_{\text{epist}} \le 0.04 \land \alpha_{\text{fav}} > 0.05 \implies$ **`QBE-D1`** (Local) o **`QBE-D2`** (Visita). Si $p_{\text{fav}}' < \Gamma$, el partido no puede ser Directa y es transferido a Asimetría Híbrida (ver Paso 4).
  3. Si cumple las Cuatro Leyes del Underdog ($\alpha_{\text{dog}} \ge +0.20 \land O_{\text{dog}} \ge 3.50 \land \Delta_{\text{epist}} \le 0.05 \land Q_{\text{mod}} \ge 0.98) \implies$ **`QBE-R1`** (Dog Local) o **`QBE-R2`** (Dog Visita).
  4. Si la morfología de Capa 0 resuelve `ASIMETRIA_LOCAL` o `ASIMETRIA_VISITANTE` bajo el umbral $\Gamma$ recibido $\land O_{\text{Empate}} > \theta^* \land \alpha_H > 0 \implies$ **`QBE-H1`** (Local) o **`QBE-H2`** (Visita) con seguro $V=0$.
     - **Invariante VIII-11 — Simetría Canónica de Cobertura H1/H2** *(Resolución Definitiva de `VARIANZA-H2`, Director Humano, 2026-10; ficha de cierre `VAR-H2-SIMETRIA-CANONICA`)*: la cobertura de tablas es **ÚNICA** para toda la Familia H. `QBE-H2` NO monetiza la cuota del Empate: monetiza la superioridad del **favorito visitante** ($\alpha_V > 0$) y se cubre en tablas. Queda derogado el Diseño B del commit génesis `0f4b340`.
       - **Ataque: Gana Favorito Visitante** ($O_V$) — boleto 2 (`boleto_2_ganancia`), pierna que transporta el $+EV$.
       - **Seguro: Empate** ($O_X$) — boleto 1 (`boleto_1_seguro`), reintegro del $100\%$ del capital ($V=0$) conforme a `[VAULT-CORE-070-DUTCHING]` ($b_{seg} = A_i / O_X$).
       - **Condición de admisión:** morfología de Capa 0 `ASIMETRIA_VISITANTE` (umbral $\Gamma$) $\land \Delta_{\text{epist}} \le 0.08 \land O_X > \theta_2^* \land \alpha_2 > 0$, con $\theta_2^* = O_V / (O_V - 1.0)$ y $\alpha_2 = p_2 O_V - 1.0$.
       - **Asignación de importes:** `calcular_dutching_v0(b_total, o_fav, o_emp)` (`portfolio_math.py`), idéntica para `H1` y `H2` (ley del Vault conectada; fin de la ley huérfana V-1).
       - **Anclaje endógeno del Doble Cobro:** `[LN-QBE-083]` — *Ganancia Principal = Victoria ordinaria del favorito* y *Retorno Bruto* $= B_{\text{prio}} O_{\text{fav}} + B_i$ — ya legislaba el Diseño A para `H1` **y** `H2`; la inversión histórica de piernas fue una violación de este nodo, no una doctrina alternativa.
       - **Nota de vigencia (umbral):** el mandato de admisión $\Delta_{\text{epist}} \le 0.08$ pertenece a la Resolución `VARIANZA-H2`; la frontera de cuarentena hoy vigente en la cascada sellada `[VAULT-CORE-070-TRIAJE]` es global ($\Delta_{\text{epist}} \le 0.12$). La armonización del umbral queda registrada como varianza **ABIERTA** (`VAR-H2-UMBRAL`) y no se alteró sin dictamen expreso.
       - **[SHIELD]:** `tests/shield/test_shield_invariante_viii_11_simetria_h1_h2.py`
  5. Si $O_{\text{Empate}} \le \theta^*$ (empate caro) $\land \alpha_{\text{DNB}} > 0.05 \implies$ **`QBE-C1`** (Draw No Bet / AH 0.0).
  6. Si $\max(\alpha_{1X2}) \le 0 \land \alpha_{\text{Totales}} > 0.06 \implies$ **`QBE-C2`** (Derivado Totales en $M_{xy}^*$).
  7. Por defecto ante ausencia de valor $\implies$ **`QBE-00`** (Abstención).
* **O (Output):** `strategy_code: str`, `pago_anticipado: bool`, `alpha_neto: float`.
* **Φ (Transición):** Hacia [LN-QBE-070-B] (Asignación de Capital).
* **Axioma de Subordinación Morfológica de la Familia R (Anti-Secuestro de Triaje):**
  1. La Capa 0 precede estrictamente a la búsqueda de Underdogs. Si la morfología de masa $\Delta^2$ clasifica el partido como `ASIMETRIA_LOCAL` ($p_1' + p_X' \ge \Gamma$), queda **TERMINANTEMENTE PROHIBIDO** emitir la estrategia reversa visitante `QBE-R2`, sin importar cuán alta sea la cuota foránea o el $+EV$ aparente.
  2. Recíprocamente, si la morfología es `ASIMETRIA_VISITANTE` ($p_2' + p_X' \ge \Gamma$), queda prohibido emitir `QBE-R1`.
  3. Las estrategias de la Familia R (`QBE-R1` y `QBE-R2`) solo son legalmente admisibles en el estado morfológico de `PARIDAD_CIEGA` ($\mathcal{M}_{\text{PARIDAD-0}}$) donde ningún bando supere $1 - \Gamma$. Queda terminantemente prohibida su emisión en `BIPOLARIDAD_TERRITORIAL` ($\mathcal{M}_{\text{BIPOLAR}}$) por violar la cota de riesgo residual desprotegido de la Invariante VIII-37 ($p_{\text{riesgo}} \le 33\%$).

---

### ID: [LN-QBE-060-C] Filtro de Veto Fiduciario Inteligente Anti-Ruptura (QBE-00)

* **Ω (Resumen):** Filtro de abstención fiduciaria temprana que intercepta partidos con huella digital demostrada de ruptura estocástica hacia $P_{\text{low}}$. Aplica el principio de que "no apostar es una decisión válida e inteligente", preservando el capital en escenarios de alta entropía o volatilidad de fuego ingobernable en 1X2.
* **I (Input):** Probabilidades ordenadas $P_{\max}, P_{\text{mid}}, P_{\text{low}}$, delta de dispersión $\Delta P = P_{\max} - P_{\text{low}}$, intensidades de gol $\lambda_H, \mu_A$, probabilidad de empate $p_X'$.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Aduana de Falsa Paridad (Arquetipo 4 - Alta Entropía):**
     Si la diferencia entre el primer y tercer desenlace es estrecha y no hay convicción direccional:
     $$\Delta P \le \text{DELTA\_P\_PARIDAD\_VETO} \; (0.1200) \quad \land \quad P_{\max} \le \text{PMAX\_MIN\_OPERABLE} \; (0.3800)$$
     El partido colapsa obligatoriamente a `QBE-00` con motivo:  
     `"Veto Fiduciario: Falsa Paridad / Alta Entropía (Delta P <= 12%)"`.
  2. **Aduana de Bipolar de Fuego (Arquetipo 3 - Volatilidad Extrema de Goles en 1X2):**
     Si el partido proyecta un intercambio desmedido de goles y el empate en 1X2 está asfixiado:
     $$(\lambda_H + \mu_A) \ge \text{LAMBDA\_SUMA\_FUEGO\_VETO} \; (3.0000\text{ xG}) \quad \land \quad p_X' \le \text{P\_EMPATE\_FUEGO\_TECHO} \; (0.2200) \quad \land \quad P_{\max} < 0.5000$$
     El partido colapsa a `QBE-00` en el mercado 1X2 con motivo:  
     `"Veto Fiduciario: Bipolar de Fuego (Desvío a Mercado Derivado de Altas C2)"`.
* **O (Output):** Veredicto de Triaje con emisión de `QBE-00` e informe del arquetipo interceptado en la traza, publicado en el campo `arquetipo_veto` del veredicto (`'FALSA_PARIDAD'` | `'BIPOLAR_FUEGO'`), ausente cuando la abstención proviene de la morfología sellada y no de la aduana. Resolución de varianza: `VAR-ANTI-RUPTURA-ORDEN-01` (dictamen del Director, 2026-10-15).
* **Φ (Transición):** Hacia `[LN-QBE-070-D]` y `src/core/contracts/portfolio_math.py`.
* **[SHIELD]:** `tests/shield/test_shield_anti_ruptura_veto.py`

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
       **Nota de materialización (Fase 4):** la sustitución directa en `PortfolioEngine.build_plan` exige que el contrato de `approved_matches` exponga $p_i$, $O_i$ y $\Delta_{\text{epist}}$. Mientras ese contrato no se extienda, el techo de cartera se aplica con `aplicar_hard_caps_constitucionales` (8% individual / 25% global) y el piso con `[LN-QBE-071]`. Nodo de seguimiento declarado en `VAR-2026-LN-QBE-070-073`.
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
  - El valor por defecto legislado de `delta_epist` es `DELTA_EPIST_DEFAULT` (CONSTANTS.md §8).
  - **Enmienda Nudo 1 (Fase 2 · Bloque 1 — Erradicación de Masa Fabricada):** Los contratos Pydantic asociados al portafolio y a la tesis narrativa (`ConsolidatedPayload`, `MatchThesisRequest`) tienen prohibido inyectar distribuciones (ej. 55/25/20 o 70/20/10) o proyecciones (xG=1.8) por defecto si el payload real no las porta. La ausencia de dato debe reflejarse como `None`, no como una cifra fabricada.
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
### ID: [LN-QBE-036] Operador de Contracción Bayesiana de Forma Reciente (10 Partidos)

* **Ω (Resumen):** Modelar el potencial ofensivo y defensivo combinando la evidencia reciente de alta frecuencia (últimos 10 juegos) con el ancla estructural de la temporada mediante actualización Bayesiana Normal-Normal, evitando sobrerreacciones a rachas cortas de ruido.
* **I (Input):** Métricas 10P ($xG_{10P}, GF_{10P}, xGA_{10P}, GC_{10P}$), acumulados de temporada ($xG_{\text{macro}}, GF_{\text{macro}}$) y factor contextual de shock $Q_{\text{mod}} \in [0.90, 1.05]$.
* **P (Process) [ARCH-PILLAR] [ALGO-PROTECTED]:**
  0. **Guarda de Suficiencia (Fail-Loud):** si la evidencia ofensiva del par evaluado es no positiva o $\mu_{\text{liga}} \le 0$, el operador levanta `ValueError`. La suficiencia fáctica $S(\mathcal{I}_i)$ se gobierna exclusivamente en `[LN-QBE-035-B]`: el operador JAMÁS fabrica factores.
  1. Derivación de tasas log-diferenciales recientes y macro:
     $$A_{\text{reciente}} = \ln\left(\frac{0.65 \cdot xG_{10P} + 0.35 \cdot GF_{10P}}{\mu_{\text{liga}} / 2}\right), \quad A_{\text{macro}} = \ln\left(\frac{0.65 \cdot xG_{\text{macro}} + 0.35 \cdot GF_{\text{macro}}}{\mu_{\text{liga}} / 2}\right)$$
     *(El mismo operador se aplica por simetría al par defensivo $xGA/GC$; el signo del factor defensivo lo legisla `[LN-QBE-035-B]` en el llamador.)*
  2. Ponderación adaptativa por ruptura estructural:
     $$\rho = \begin{cases}
     0.30 & \text{si } Q_{\text{mod}} \ne 1.00 \text{ (shock verificado: prima la evidencia reciente)} \\
     0.55 & \text{si } Q_{\text{mod}} == 1.00 \text{ (estabilidad: prima el ancla de temporada)}
     \end{cases}$$
  3. Contracción convexa del factor ofensivo y defensivo:
     $$A_i^* = (1.0 - \rho) \cdot A_{\text{reciente}} + \rho \cdot A_{\text{macro}}$$
     $$D_i^* = (1.0 - \rho) \cdot D_{\text{reciente}} + \rho \cdot D_{\text{macro}}$$
  4. **Inyección obligatoria al Damping Hiperbólico Simétrico — `[VAULT-CORE-001]`** *(enmienda ratificada D-3: el damping NO pertenece a `[LN-QBE-040]`, que legisla la matriz Poisson 6x6)*: la compresión se delega en el canon sellado `aplicar_damping_hiperbolico(A_i^*, \kappa_{\text{net}})` con $\kappa_{\text{net}} = 0.2500$ ABSOLUTO (constante `KAPPA_NET`; Sección 4.12 del Tratado, materializado en `src/core/intensity_canonical_loglink.py`). La escalera $\kappa = 2.5 \cdot \sigma_{\text{liga}}$ queda **DEROGADA** por `VAR-2026-LIVE-AUDIT-J11`/V-2: $\sigma_{\text{liga}}$ permanece en la firma como vestigio de compatibilidad de llamadas selladas y NO interviene en el cómputo. **Prohibición expresa:** el símbolo $\kappa = \ln(2)/180$ de `[LN-QBE-020]` (decaimiento H2H) JAMÁS se usa como escala de damping; usar $A_{\text{amortiguado}} = \kappa_{\text{net}} \tanh(A_i^* / \kappa_{\text{net}})$ con $\kappa = \ln(2)/180$ colapsa todo factor a la constante $\kappa$ (corrupción silenciosa).
* **O (Output):** `BayesianFormResult` (`a_reciente`, `a_macro`, `a_contraido`, `rho_aplicado`, `a_amortiguado`) declarado en `src/models/analytics.py`; el llamador deriva $D$ por la invocación simétrica del mismo operador.
* **Φ (Transición):** Hacia la ecuación log-lineal de intensidades $(\lambda_H, \lambda_A)$ — `[VAULT-CORE-001]` / `[LN-QBE-040]`.
* **[SHIELD]:** `tests/shield/test_shield_bayesian_form_and_h2h.py`
* **Declaración de Limitación Fáctica del Payload (ALT-5-A — Dictamen VARIANZA-10 §1.3):** La fuente de liga verificada (FotMob) publica **agregados estacionales por club** (tabla de temporada con `xg` / `xgConceded`) y **no** publica series de $xG$ por partido. En consecuencia: (i) queda prohibido etiquetar como $10P$ cualquier agregado de temporada completa (`[GOVERNANCE-01]`); (ii) las derivaciones $xG/xGA$ del sensor (`scripts/daemons/centinela_deportivo.py`, transcripción canónica de `docs/DIRGEN_VAULT.md:1091-1093` e insumo obligatorio de $att\_h\_rate = 0.65 \cdot xG + 0.35 \cdot GF$) permanecen **congeladas**: sustituirlas por la tabla xG real exige Enmienda al Vault y re-certificación numérica; (iii) el streaming de forma 10P de alta frecuencia y las consultas granulares de H2H —kernel `src/core/sovereign/h2h_kernel.py` sin fuente de datos cableada— quedan formalmente catalogados como **capacidades de Fase 6**.

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

### ID: [LN-QBE-071-B] Piso Estructural Bivariado ($4.00 MXN) y Cobertura Universal de la Familia R

* **Ω (Resumen):** Extensión constitucional del piso mínimo de ventanilla a todas las estrategias con dos boletos simultáneos, imponiendo una inversión mínima por partido de $\$4.00\text{ MXN}$ y financiando los ajustes de seguro con el superávit del libro.
* **I (Input):** Cartera de órdenes de ejecución, bankroll total, cuotas de empate $O_{\text{emp}}$, piso legal $\$2.00\text{ MXN}$.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Guarda Universal de Cobertura:** Aplica obligatoriamente a `("QBE-H1", "QBE-H2", "QBE-R1", "QBE-R2", "QBE-C1")`.
  2. **Piso Bivariado Inviolable:** Si una posición porta seguro y ataque, $B_i \ge \$4.00\text{ MXN}$ ($2.00 + 2.00$).
  3. **Preservación del Techo del 25%:** Todo reescalado del seguro a $\$2.00\text{ MXN}$ se financia con el superávit de asignación sin desbordar el límite patrimonial de cartera.
* **O (Output):** Órdenes de cartera certificadas con $B_{\text{seg}} \ge \$2.00\text{ MXN}$ y $B_{\text{prio}} \ge \$2.00\text{ MXN}$.
* **Φ (Transición):** Hacia `[VAULT-CORE-070-PRORRATEO]` y `src/pipeline/adapter.py`.
* **[SHIELD]:** `tests/shield/test_shield_portfolio_integrity_and_floor.py`

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

### ID: [LN-QBE-025-B] Conmutador de Slates, Cartera Vacía y Liquidación Real (Backtesting Fiduciario)

* **Ω (Resumen):** Habilita la simulación retrospectiva de carteras sobre jornadas históricas congeladas en SQLite 3NF y formaliza que una cartelera con cero oportunidades +EV no constituye un error de sistema (HTTP 400), sino una decisión fiduciaria de preservación del 100% del capital en efectivo (HTTP 200 con riesgo $0.00). Contrasta las órdenes simuladas contra los marcadores finales reales para calcular el PnL y ROI histórico.
* **I (Input):** `matchday_target: int`, `modo_simulacion: bool`, `bankroll: float`, `standings_snapshots` (al corte de $N-1$), `fixtures_snapshots` (pre-kickoff) y marcadores reales de `matches`.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Axioma de la Cartera Vacía (Preservación Absoluta en Efectivo):**  
     Si tras evaluar el catálogo de 9 estrategias ningún partido supera el umbral $+EV$ ($\alpha > 0$) o todos los partidos están concluidos/vetados, el sistema emite obligatoriamente una cartera con `capital_en_riesgo_mxn = 0.00`, `total_partidos_core_aprobados = 0` y `ordenes = []`. Queda terminantemente prohibido abortar con excepciones de error de cliente (`HTTP 400`).
  2. **Regla Anti-Fuga de Datos (Cero Data Leakage):**  
     Para simular la jornada $N$, el motor debe consumir estrictamente la tabla general y los factores estructurales calculados con datos acumulados **al corte de la jornada $N-1$**. Queda proscrito utilizar la tabla de posiciones posterior a los partidos simulados.
  3. **Algoritmo de Liquidación Post-Evento (Real vs. Predicho):**  
     Para cada orden histórica $i$ generada en el plan:
     - Si gana el Favorito respaldado: $\text{PnL}_i = B_{i,\text{prio}} \cdot O_{i,\text{fav}} - B_i$.
     - Si ocurre Empate en cobertura $V=0$: $\text{PnL}_i = B_{i,\text{seg}} \cdot O_{i,\text{emp}} - B_i \equiv \$0.00\text{ MXN}$.
     - Si gana el Underdog no cubierto: $\text{PnL}_i = -B_i$.
     $$\text{PnL\_Real\_Jornada} = \sum_{i=1}^K \text{PnL}_i, \quad \text{ROI\_Real} = \frac{\text{PnL\_Real}}{\sum B_i} \times 100$$
  4. **El Doble Seguro de Interfaz:**  
     La consulta de jornadas pasadas exige que el usuario active explícitamente el interruptor `modo_simulacion = True`. Por defecto, el sistema permanece bloqueado en la jornada activa de producción.
* **O (Output):** `PortfolioExecutionPlan` enriquecido con el objeto opcional `liquidacion_post_evento: LiquidacionJornadaReal`.
* **Φ (Transición):** Hacia `src/web/routes/markets.py` y `src/pipeline/adapter.py`.
* **[SHIELD]:** `tests/shield/test_shield_backtesting_and_empty_portfolio.py`

---

### ID: [LN-QBE-037] Algoritmo de Detección de Sesgo Popular en Quinielas Progol

* **Ω (Resumen):** Explotar la sobre-representación de apuestas populares en quinielas colectivas contrastando la venta pública nacional contra la distribución soberana de Q-BE.
* **I (Input):** $P_{\text{Público}} = (v_1, v_X, v_2)$ y $\hat{P}_{\text{Q-BE}} = (p_1, p_X, p_2)$.
* **P (Process) [BIZ-LOGIC]:**
  $$\text{Sesgo}_k = v_k - p_k$$
  $$\text{Si } \text{Sesgo}_{\text{Local}} \ge +0.20 \implies \text{Alerta de Sesgo: El público sobrevaloró al local; el valor (+EV) radica en X2.}$$
* **O (Output):** Clasificación de casillas: `BASE_SIMPLE`, `DOBLE_COBERTURA_SESGO`, `TRIPLE_ESTRATÉGICO`.

---

### ID: [LN-QBE-038] Modelo de Desempeño Específico de Sede (Home/Away Splits) y Fortaleza de Plaza

* **Ω (Resumen):** Desacoplar el rendimiento de local y de visitante del promedio general de temporada. Combina de forma balanceada la producción ofensiva y defensiva específica de sede con el récord general e incorpora el factor aditivo de intimidación de plaza $\Delta\gamma_{\text{plaza}}$ a la ventaja base de localía $\bar{\gamma}_{\text{base}} = 0.15$.
* **I (Input):** `home_team_stats` (general), `away_team_stats` (general), `home_split_stats` (sede local), `away_split_stats` (sede visita), `home_team_slug: str`, `mu_liga: float = 2.65`.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Fusión Ponderada de Sede ($w_{\text{sede}} = 0.50$):**
     $$\text{att\_h\_rate} = (1.0 - w_{\text{sede}}) \cdot \left(\frac{GF_{H,\text{gen}}}{PJ_{H,\text{gen}}}\right) + w_{\text{sede}} \cdot \left(\frac{GF_{H,\text{local}}}{PJ_{H,\text{local}}}\right)$$
     $$\text{def\_h\_rate} = (1.0 - w_{\text{sede}}) \cdot \left(\frac{GC_{H,\text{gen}}}{PJ_{H,\text{gen}}}\right) + w_{\text{sede}} \cdot \left(\frac{GC_{H,\text{local}}}{PJ_{H,\text{local}}}\right)$$
     $$\text{att\_a\_rate} = (1.0 - w_{\text{sede}}) \cdot \left(\frac{GF_{A,\text{gen}}}{PJ_{A,\text{gen}}}\right) + w_{\text{sede}} \cdot \left(\frac{GF_{A,\text{visita}}}{PJ_{A,\text{visita}}}\right)$$
     $$\text{def\_a\_rate} = (1.0 - w_{\text{sede}}) \cdot \left(\frac{GC_{A,\text{gen}}}{PJ_{A,\text{gen}}}\right) + w_{\text{sede}} \cdot \left(\frac{GC_{A,\text{visita}}}{PJ_{A,\text{visita}}}\right)$$
     *(Si no existen datos específicos de sede, degrada suavemente a $w_{\text{sede}} = 0.0$ sin inventar registros).*
  2. **Catálogo Canónico de Intimidación de Plaza ($\Delta\gamma_{\text{plaza}}$):**
     $$\gamma_{\text{home}} = \bar{\gamma}_{\text{base}} + \Delta\gamma_{\text{plaza}}(\text{home\_slug})$$
     donde $\Delta\gamma_{\text{plaza}} \in [0.00, 0.10]$ según el catálogo sellado en `docs/CONSTANTS.md` (ej. `tigres-uanl` / El Volcán $\implies +0.07$).
  3. **Recalibración de la Ligadura Estructural ($\alpha$):**
     $$\alpha = \ln(\mu_{\text{liga}}) - \ln(1.0 + e^{\gamma_{\text{home}}})$$
     garantizando analíticamente la conservación de masa global de goles.
* **O (Output):** `FactoresSedeResult(A_home, D_away, A_away, D_home, gamma_home, alpha)`.
* **Φ (Transición):** Hacia `[VAULT-CORE-001]` (`estimar_intensidades_loglineal`) y `[LN-QBE-040]`.
* **[SHIELD]:** `tests/shield/test_shield_venue_splits_and_h2h_deep.py`

---
### ID: [LN-QBE-039] Motor de Ortogonalización Residual y Factores Latentes Tridimensionales (GSL-3D)

* **Ω (Resumen):** Marco matemático de contención y gobernanza universal para las 44 variables del catálogo. Descompone la evidencia en tres espacios de Hilbert cerrados e independientes ($\mathbb{H}_{\text{att}}, \mathbb{H}_{\text{def}}, \mathbb{H}_{\text{ctx}}$), aplica la proyección de Gram-Schmidt para aislar únicamente el residuo ortogonal $v_k^\perp$ de las señales secundarias frente a la señal directora, e impone un presupuesto de norma/varianza cerrado ($\|\mathcal{A}^*\| \le 1.0, \|\mathcal{D}^*\| \le 1.0, \|\mathcal{C}^*\| \le 0.25$), erradicando la doble contabilización y la resonancia exponencial destructiva.
* **I (Input):** Conjunto de señales observables $\mathcal{X}$, clasificadas por dimensión funcional:
  - $\mathbb{H}_{\text{att}}$ (Ofensiva): Señal directora primaria $u_1$ ($xG$ Opta por 90') y secundarias (GF en sede, tiros, goles acumulados).
  - $\mathbb{H}_{\text{def}}$ (Defensiva): Señal directora primaria $u_1$ ($xGA$ Opta por 90') y secundarias (GC en sede, tiros concedidos, goles recibidos).
  - $\mathbb{H}_{\text{ctx}}$ (Contextual): Ventaja macro incondicional $\bar{\gamma}_{\text{base}} = 0.15$, bono de plaza $\Delta\gamma_{\text{plaza}}$, altitud y descanso.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Aislamiento Dimensional Estricto:** Toda variable pertenece a exactamente uno de los tres espacios de Hilbert. Queda prohibida la contaminación cruzada (cero señales defensivas en el vector de ataque).
  2. **Extracción Residual de Gram-Schmidt por Dimensión:**  
     Para cada variable secundaria $X_k$ en el espacio $\mathbb{H}$, su entrada está condicionada a su residuo ortogonal respecto al subespacio ya cubierto $U_{k-1} = \text{span}(u_1, \dots, u_{k-1})$:
     $$v_k^\perp = X_k - \sum_{j=1}^{k-1} \frac{\langle X_k, u_j \rangle}{\langle u_j, u_j \rangle} u_j = X_k - \text{Proj}_{U_{k-1}}(X_k)$$
     $$u_k = \frac{v_k^\perp}{\|v_k^\perp\|} \quad \text{si } \|v_k^\perp\| > \varepsilon_{\text{ort}}, \quad \text{de lo contrario } 0$$
     *Teorema de No-Redundancia:* Por construcción, $\langle u_j, v_k^\perp \rangle = 0 \quad \forall j < k$.
  3. **Absorción Fiduciaria del Desempeño de Sede (El Des-Solapamiento):**  
     La producción en sede $X_{\text{sede}}$ (ej. goles en casa) solo inyecta su residuo $v_{\text{sede}}^\perp$ no explicado por la calidad general de plantilla ($u_1 = xG$):
     - Si un club modesto tiene un récord extraordinario en casa (caso Tigres), su calidad general $u_1$ es media, por lo que $v_{\text{sede}}^\perp$ es alto y positivo, otorgando la fuerza legítima de la plaza.
     - Si un superlíder ya tiene una calidad general superlativa (caso América), su rendimiento en casa ya está prácticamente al 100% explicado por $u_1$ ($X_{\text{sede}} \approx u_1$), por lo que $v_{\text{sede}}^\perp \approx 0$, anulando el doble cobro y evitando que el factor se dispare.
  4. **Presupuesto Cerrado de Escala y Varianza Unitaria:**  
     El factor latente final de cada dimensión se sintetiza mediante:
     $$\mathcal{A}^* = \tanh\left( \sum_{j=1}^{m_{\text{att}}} w_j u_j \right), \quad \mathcal{D}^* = \tanh\left( \sum_{j=1}^{m_{\text{def}}} w_j u_j \right)$$
     sujeto a $\sum |w_j| \le 1.0000$.  
     La norma está acotada estrictamente en $\|\mathcal{A}^*\| \le 1.0$ y $\|\mathcal{D}^*\| \le 1.0$, garantizando que la adición de nuevas variables jamás expanda la escala de goles de la liga.
* **O (Output):** `FactoresGSL3D(A_star, D_star, C_star, residuos_auditables)`.
* **Φ (Transición):** Hacia `[VAULT-CORE-001]` (`estimar_intensidades_loglineal`) y `[LN-QBE-040]`.
* **[SHIELD]:** `tests/shield/test_shield_gsl3d_orthogonal_engine.py`

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

### ID: [LN-QBE-077-B] Teorema de Aceleración Asintótica y Partición de Capital con Cobertura Activa (V = δ > 0)

* **Ω (Resumen):** Generalización de la cobertura sintética en tablas para transformar el retorno de indemnidad pasiva ($0.00 MXN) en un retorno neto estrictamente positivo ($G_{\text{emp}} = \delta \cdot B_i > 0$). Erradica la fricción por estancamiento de capital (Growth Drag) en jornadas dominadas por empates, inyectando energía positiva a la tasa de crecimiento compuesto de Kelly ($g$).
* **I (Input):** Presupuesto asignado $B_i > 0$, cuota comercial del favorito $O_{\text{fav}} > 1.0$, cuota del empate $O_{\text{emp}} > 1.0$, parámetro de retorno exigido $\delta \ge 0.0$, piso legal de ventanilla $B_{\min} = \$2.00\text{ MXN}$.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Partición Generalizada de Capital:**
     $$B_{\text{seg}}(\delta) = \frac{(1.0 + \delta) \cdot B_i}{O_{\text{emp}}}$$
     $$B_{\text{prio}}(\delta) = B_i - B_{\text{seg}}(\delta) = B_i \left[ 1.0 - \frac{1.0 + \delta}{O_{\text{emp}}} \right]$$
  2. **Retornos Proyectados por Desenlace:**
     - En Victoria del Favorito: $G_{\text{fav}}(\delta) = B_i \left( \left[ 1.0 - \frac{1.0 + \delta}{O_{\text{emp}}} \right] O_{\text{fav}} - 1.0 \right)$
     - En Empate (Cobertura Activa): $G_{\text{emp}}(\delta) = \delta \cdot B_i$
     - En Victoria del Underdog: $\text{PnL} = -B_i$
  3. **Piso de Ventanilla en Ambas Piernas:** $B_{\text{seg}} \ge \$2.00$ y $B_{\text{prio}} \ge \$2.00$ ($B_i \ge \$4.00$).
* **O (Output):** `ParticionDutchingResult(B_prio, B_seg, G_fav, G_emp, roi_fav, roi_emp, delta_efectivo)`.
* **Φ (Transición):** Hacia `[LN-QBE-070-D]` (`PortfolioEngine.build_plan`), `[VAULT-CORE-070-DUTCHING]` y `[ARCH-1.4.37]`.
* **[SHIELD]:** `tests/shield/test_shield_dynamic_dutching_delta.py`

### ID: [LN-QBE-077-C] Techo de Viabilidad Analítica δ_max y Umbral de Breakeven θ*

* **Ω (Resumen):** Cota analítica superior que limita el desvío de capital hacia el boleto de seguro, garantizando que la victoria del favorito mantenga una ganancia neta estrictamente positiva ($G_{\text{fav}}(\delta) > 0$).
* **I (Input):** Cuotas comerciales $O_{\text{fav}}, O_{\text{emp}}$, umbral de breakeven $\theta^* = O_{\text{fav}} / (O_{\text{fav}} - 1.0)$.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  $$\delta_{\max} = \frac{O_{\text{emp}}}{\theta^*} - 1.0000 = O_{\text{emp}} \left( 1.0 - \frac{1.0}{O_{\text{fav}}} \right) - 1.0000$$
  Todo parámetro solicitado debe satisfacer $\delta < \delta_{\max}$. Si una solicitud excede la cota, el motor aplica clamping fiduciario seguro:
  $$\delta_{\text{clamped}} = \min(\delta, \; 0.95 \cdot \delta_{\max})$$
* **O (Output):** Cota máxima admisible $\delta_{\max}$ y delta acotado fiduciario.
* **Φ (Transición):** Hacia `[LN-QBE-077-B]`.
* **[SHIELD]:** `tests/shield/test_shield_dynamic_dutching_delta.py`

### ID: [LN-QBE-077-D] Dutching Isorrendimiento de Doble Cosecha (δ*)

* **Ω (Resumen):** Determinación del punto óptimo de simetría donde la posición rinde exactamente el mismo porcentaje de retorno neto tanto en victoria del favorito como en empate: $\text{ROI}_{\text{fav}} \equiv \text{ROI}_{\text{emp}} = \delta^*$.
* **I (Input):** Cuotas comerciales $O_{\text{fav}}, O_{\text{emp}}$ que satisfagan la condición de sub-símplex $(1/O_{\text{fav}}) + (1/O_{\text{emp}}) < 1.0000$.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  $$\delta^* = \frac{O_{\text{fav}} \cdot O_{\text{emp}}}{O_{\text{fav}} + O_{\text{emp}}} - 1.0000 = \frac{1.0}{\frac{1.0}{O_{\text{fav}}} + \frac{1.0}{O_{\text{emp}}}} - 1.0000$$
  Tríptico Operativo de Modalidades:
  - `DEF` (Defensivo): $\delta = 0.0000$ (Indemnidad pura $V=0$).
  - `BAL` (Balanceado): $\delta = 0.50 \cdot \delta^*$ (Crecimiento compuesto balanceado).
  - `AGR` (Isorrendimiento): $\delta = \delta^*$ (Doble cosecha simétrica).
* **O (Output):** Parámetro de isorrendimiento $\delta^*$ y modalidad resuelta.
* **Φ (Transición):** Hacia `[LN-QBE-077-B]`.
* **[SHIELD]:** `tests/shield/test_shield_dynamic_dutching_delta.py`

---

### ID: [LN-QBE-070-E] Prorrateo Resiliente de Hard-Caps con Respeto al Piso de Ventanilla
* **Ω (Resumen):** Resuelve la colisión entre el Hard-Cap global de cartera ($\sum B_i \le 25\% \cdot \text{Bankroll}$) y el piso mínimo de ventanilla ($B_{\text{seg}} \ge \$2.00\text{ MXN}$).
* **P (Process) [ARCH-PILLAR] [ALGO-PROTECTED]:**
  1. Si la suma total de inversiones supera el $25\%$ del bankroll, se calcula el factor de escala: $\text{escala} = \frac{0.25 \cdot B_{\text{total}}}{\sum B_i}$.
  2. En toda orden híbrida ($H1, H2$), si tras aplicar la escala el seguro comprimido resulta $B_{\text{seg}} < \$2.00\text{ MXN}$, se impone la **Regla de Clamping Fiduciario**:
     $$B_{\text{seg}}^* = \$2.00\text{ MXN}$$
     El ajuste residual necesario para no rebasar el tope de cartera se absorbe reduciendo el boleto de ataque ($B_{\text{prio}}$) o prorrateando sobre las demás posiciones con holgura.
     **Guarda O-06:** El parámetro `o_emp` (cuota de empate) es obligatorio para el reescalado. Queda estrictamente prohibido asumir un valor por defecto (como 3.30). Si la orden no porta `o_emp`, se debe levantar `ValueError` o descartar la orden del prorrateo.
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
  **Guarda O-07:** Si el denominador $(p_{fav}' + p_{dog}')$ es igual a cero, la probabilidad efectiva es estrictamente `0.0`. Queda derogado el fallback neutral de `0.50` por no estar promulgado en el sistema.
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

### ID: [LN-QBE-083-B] Unificación Honesta del Rótulo de Ausencia de Cobertura en Estrategias Directas
* **Ω (Resumen):** Extiende la semántica de liquidación de `[LN-QBE-083]` a la capa de presentación: toda posición cuya familia estratégica carezca de pierna de cobertura en tablas (`QBE-D1` y `QBE-D2`) debe declarar el **riesgo directo real** de su exposición, quedando prohibido exhibir cualquier mensaje de recuperación de capital.
* **I (Input):** `codigo` de la familia estratégica (`estrategia_seleccionada.codigo`) e `inversion_partido_A_i` (exposición bruta de la orden) del payload de cartera.
* **P (Process) [UX-MANDATE]:** Para `codigo ∈ {QBE-D1, QBE-D2}` el rótulo canónico es exactamente `"Sin cobertura (Riesgo Directo: -$" + B_i.toFixed(2) + ")"`, con severidad visual de alerta (`#f87171`). **Prohibición expresa:** el literal genérico `Recuperas $X MXN ($0.00 pérdida)` —que describe recuperación íntegra vía pierna de cobertura en tablas— queda **erradicado** para toda familia directa, por ser fiduciariamente falso en ausencia de dicha pierna.
* **O (Output):** Celda de cobertura del `cuerpo-resumen-asignacion` (`src/web/static/js/app.js`).
* **Φ (Transición):** Hacia `[ARCH-1.4.16-B]` (horario fáctico en el Resumen de Asignación) y `[DES-QBE-060]` (anatomía de boletos).
* **[SHIELD]:** `tests/shield/test_shield_portfolio_p_prime_and_ui_contracts.py`


---

### ID: [LN-QBE-084] El Operador Canónico de Selección por Masa Acumulada P' en Progol
* **Ω (Resumen):** Transforma la distribución sobre combinaciones en un problema de optimización determinista: ordena el universo restringido de boletas por probabilidad conjunta descendente y selecciona las primeras $M$ posiciones para maximizar la masa probabilística capturada bajo presupuesto cerrado.
* **P (Process) [ARCH-PILLAR] [ALGO-PROTECTED]:**
  1. Para $K=14$ partidos, se construye el vector ordenado $P'$ tal que:
     $$P(B_{(1)}) \ge P(B_{(2)}) \ge \dots \ge P(B_{(N)})$$
     **Cláusula de Ignorancia Explícita (Saneamiento O-08):** Queda prohibido el uso de literales `0.3333` huérfanos en el cálculo de la probabilidad conjunta. Si un partido no provee distribución fiduciaria, se debe inyectar la terna canónica del Prior Fiduciario `(0.3333, 0.3333, 0.3334)` importando o referenciando las constantes legisladas del sistema, garantizando la conservación de la masa probabilística.
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
* **Enmienda Nudo 1 (Fase 2 · Bloque 1 — Erradicación de Masa Fabricada):** Queda estrictamente prohibido el uso de sensores que generen datos de contingencia (Mocks). El módulo `gemini_search_sensor.py` ha sido formalmente extirpado. Cualquier DTO de ingesta (`raw_input.py`) que declare confiabilidad 100% por defecto, o mercados sintéticos por defecto, viola el Axioma de Cero Mocks.

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
* **Φ (Transición):** Hacia `[LN-QBE-012]` (Normalizador) y `[ARCH-1.5.12]` (Aprovisionador).
* **[SHIELD]:** `tests/shield/test_shield_temporal_disambiguation_and_provisioner.py`

---

### ID: [LN-QBE-096] Coordinador Orquestador Atómico del Ciclo de Vida de Datos (Data Nexus Bus)
* **Ω (Resumen):** Autoridad única de composición del sistema. Encadena las cuatro capas selladas (Sensor de Ingesta $\to$ Identity Brain $\to$ Motor Soberano $\to$ Persistencia 3NF) dentro de **una sola Unit of Work**, garantizando el principio *todo o nada* sobre el snapshot certificado: jamás se publica una cabecera de concurso sin sus casillas, ni una casilla con probabilidades fabricadas. El Coordinador es un **Compositor**, nunca un motor: tiene estrictamente prohibido reimplementar matemática protegida o publicar una sola constante propia.
* **I (Input):** `operacion` y puertos inyectados — `concurso_num: Optional[int]`, `concurso_dto_inyectado: Optional[ProgolContestDTO]`, `candidatos_partidos: Optional[Sequence[ScheduledMatchDTO]]`, `datos_facticos_por_match: Optional[Mapping[str, Mapping[str, Any]]]`, `session: Optional[Session]`.
* **P (Process) [ARCH-PILLAR] [ANTI-BUG]:**
  1. **Adquisición de evidencia:** resolver el `ProgolContestDTO` por el puerto inyectado; en ausencia de éste, invocar el `concurso_loader` provisto. Sin evidencia fáctica $\implies$ `FAIL-LOUD` (`[GOVERNANCE-01]`): queda **terminantemente prohibido** sintetizar un concurso o rellenarlo con datos de fantasía.
  2. **Aduana de integridad (fail-fast):** `contest_id` no vacío y `items` no vacío; casilla que no publique ambos literales (`local_raw`, `visitante_raw`) $\implies$ aborto inmediato de la operación **antes** de abrir la Unit of Work.
  3. **Apertura de la Unit of Work:** una única `PersistenceGateway.write_transaction()` (o la `session` cedida por el llamador) que engloba la cabecera y las $N$ casillas.
  4. **Upsert de cabecera:** `slates.id = contest_id`; `name` derivado del dato sellado (`"Progol Concurso #"` + `contest_id`, cero invención de identidad); `bolsa_estimada` y `fecha_cierre = cierre_utc` transcritos verbatim del DTO; `status = "OPEN"`; `competition_id = NULL` (el DTO sellado no publica liga: no se fabrica un identificador de competición).
  5. **Composición por casilla** (bucle sobre las $N$ posiciones, sin atajos ni ramas muertas):
     - Identidad categorizada: `resolver_entidad_oficial()` (`[ARCH-1.4.25]`).
     - Vínculo temporal: `desambiguar_partido_por_ventana()` (`[LN-QBE-094]`) sobre los candidatos inyectados.
     - Símplex: `generar_distribucion_soberana()` (`[VAULT-CORE-005]`) — **siempre invocada**, incluso con evidencia vacía.
     - $S(I) = 0$ o ventana crítica vacía $\implies$ `match_id = NULL` y `es_prior_ignorancia = True`, con el Prior Fiduciario emitido por el **motor sellado** ($[LN-QBE-075]$): el Coordinador jamás publica una probabilidad propia.
     - `p_local`, `p_empate`, `p_visitante` se transcriben **verbatim** de la salida del motor: cero redondeos, cero mezclas, cero rescalados.
     - Idempotencia: la casilla se upsertea por la clave única `(slate_id, position)`; una re-sincronización actualiza in situ y jamás duplica ni destruye evidencia previa.
  6. **Cierre atómico:** un solo `commit`. Toda excepción dentro de la Unit of Work $\implies$ **ROLLBACK TOTAL**: cero cabecera, cero casillas. El sistema escribe $0$ filas o el conjunto completo; una operación fallida se reporta con `exitosos = 0` y la causa publicada en `errores` (jamás silenciada).
* **O (Output):** `CoordinatorExecutionReport(operacion, status, procesados, exitosos, errores, duracion_s)`. En fallo, `status = "FAILED"` y mutación nula del snapshot certificado (capital en riesgo 0.00 MXN).
* **Φ (Transición):** Consume `[LN-QBE-093]` / `[ARCH-1.4.24]`, `[ARCH-1.4.25]`, `[VAULT-CORE-005]` y `[VAULT-DATA-001]`; publica la Capa 5 (Data Nexus Bus) y alimenta los daemons de captura y la UI.
* **[SHIELD]:** `tests/shield/test_shield_ingestion_coordinator.py`

---

### ID: [LN-QBE-097] Puente de Despacho Unificado entre Rutas Web y el Data Nexus Bus
* **Ω (Resumen):** Conecta las peticiones REST de la capa web (`/api/markets/...` y `/api/admin/tasks/...`) con el `IngestionCoordinator` (Capa 5) y los repositorios 3NF, asegurando que las decisiones de inversión y optimización combinatoria consuman la memoria histórica completa (10P, H2H y desambiguación JIT) con latencia $< 20\text{ ms}$ en consultas cacheadas.
* **I (Input):** Peticiones JSON tipadas (`GeneratePortfolioRequest`, `AdminTaskRequest`, solicitudes de optimización Progol).
* **P (Process) [ARCH-PILLAR] [ALGO-PROTECTED]:**
  1. **Enrutamiento Financiero Sportsbook:**
     - `POST /api/markets/sportsbook/portfolio/generate` extrae los partidos de la jornada activa de `FixtureSnapshot.matches_json` y sus `SovereignDistribution` asociadas.
     - Aplica el triaje determinista de 9 estrategias (`[LN-QBE-060-B]`), el ranking lexicográfico por $P_{\text{éxito}}'$ (`[LN-QBE-081]`) y el dimensionamiento monótono con Hard-Caps (`[LN-QBE-082]`).
  2. **Enrutamiento Combinatorio Progol:**
     - `POST /api/markets/progol/optimize` consume el concurso activo de `slates` y sus 21 `slate_items` generados por el coordinador.
     - Extrae las primeras $M$ combinaciones que maximizan la masa $C(M)$ (`[LN-QBE-084]`) o desciende por distancia de Hamming (`[LN-QBE-086]`).
  3. **Despacho del Centro de Control con Streaming:**
     - `POST /api/admin/tasks/run` ejecuta las tareas de la whitelist gobernada. La tarea maestra `cadena_ingesta_total` delega en `IngestionCoordinator` y canaliza la salida estándar hacia el frontend en tiempo real.
* **O (Output):** Payloads tipados `PortfolioExecutionPlan`, `ProgolPlanResponse` y `AdminTaskResponse`.
* **Φ (Transición y Grafo Consumidor):**  
  - Nodos Lógicos Sucesores: Presentación en SPA (`[DES-QBE-032]`, `[DES-QBE-048]`).  
  - **Consumidores Activos en Producción:** Cliente reactivo `src/web/static/js/app.js` y routers FastAPI en `src/web/routes/`.
* **[SHIELD]:** `tests/shield/test_shield_sprint5_domain_reconnection.py`

---

### ID: [LN-QBE-098] Radiografía Forense Determinista y Comparador de Probabilidades sin LLM [ARCH-PILLAR]
* **Ω (Resumen):** Transforma la ventana de inspección de partido en un tablero visual instantáneo en $O(1)$, poniendo en reposo total las llamadas generativas a Gemini. Sustituye la prosa estocástica por el Radar Factual de 3 Factores (Ofensiva xG, Solidez Defensiva y Localía), el Top-4 de marcadores Poisson ($M_{xy}^*$) y la comparación de probabilidades puras contra el casino seleccionado.
* **I (Input):** `id_partido: str`, distribución soberana $\hat{P}_i$, fiduciaria $P'_i$, consenso sin vig $\vec{q}_{\text{mkt}}$, cuota comercial de ventanilla $O_k$ y operador asignado.
* **P (Process) [ALGO-PROTECTED]:**
  1. **Reposo de Inferencia LLM:** Queda formalmente prohibido disparar peticiones a `/api/portfolio/match-thesis` o instanciar `GeminiCognitiveGateway` al abrir el modal. La narrativa de IA se reemplaza por el Radar Factual de 3 Factores.
  2. **Micro-Matriz Top-4 de Marcadores Poisson:** Extrae de $M_{xy}^*$ los 4 estados con mayor densidad de masa probabilística, ordenados descendentemente.
  3. **Comparador de Probabilidades de 6 Columnas (Cero Momios):**
     - Columna 1 (`RESULTADO`): Destaca en **Verde (`#00E676`)** el desenlace de Ataque (Boleto 1) y en **Azul (`#38BDF8`)** el de Cobertura (Boleto 2).
     - Columna 2 (`P' FIDUCIARIA`): Probabilidad fiduciaria contraída con colorimetría de boleto.
     - Columna 3 (`P̂ DEPORTIVA`): Probabilidad soberana pura de física de goles.
     - Columna 4 (`CONSENSO MERCADO`): Probabilidad promedio des-marginada (Vig-Free).
     - Columna 5 (`PROB. CASINO`): Probabilidad implícita comercial con comisión ($1/O_k$) del operador asignado.
     - Columna 6 (`CASINO SELECCIONADO`): Nombre/logo y distintivo de la casa óptima.
     - Columna 7 (`VENTAJA (+EV)`): Ventaja matemática neta sobre la casa ($\alpha = p \cdot O - 1.0$).
* **O (Output):** Estructura visual renderizada en el DOM del modal `#modal-radiografia-forense`.
* **Φ (Transición):** Hacia `[DES-QBE-063]`.
* **[SHIELD]:** `tests/shield/test_shield_radiografia_forense_reborn.py`

---

### ID: [LN-QBE-099] Registro Fiduciario de Congelamiento de Boletos (Paper Trading & Audit Ledger) [ARCH-PILLAR]
* **Ω (Resumen):** Persiste el boleto aprobado por el usuario como un hecho fiduciario inmutable, capturando las cuotas comerciales del momento exacto de la compra y alimentando el badge de control de gasto. Cero recálculo retroactivo.
* **I (Input):** `id_partido: str`, `desenlace: str`, `mercado: str`, `cuota_congelada: float`, `monto: float`, `operador: str`, `timestamp: datetime`.
* **P (Process) [ALGO-PROTECTED]:**
  1. **Aduana de Idempotencia:** Si el boleto ya existe para (`id_partido`, `desenlace`, `mercado`), se rechaza el duplicado sin mutar el ledger.
  2. **Congelamiento de Cuota:** La cuota persistida es la de ventanilla ofertada al usuario en el instante de la compra; prohibido recomputarla contra el consenso del mercado posterior.
  3. **Sellado de Trazabilidad:** El registro se escribe con su marca temporal y estado `✔ Boleto Registrado`, quedando auditable contra el histórico de la orden.
* **O (Output):** Fila del ledger fiduciario + agregado de cartera para el badge `#badge-boletos-comprados` (`🎟️ Comprados: N ($XX.XX MXN)`).
* **Φ (Transición):** Hacia `[ARCH-1.4.32]` (contenedor de acciones de tarjeta y congelamiento) y `[LN-QBE-083-B]` (rótulo de cobertura).
* **[SHIELD]:** `tests/shield/test_shield_portfolio_p_prime_and_ui_contracts.py`

---

### ID: [LN-QBE-100] Motor de Calibración Factual de Temporada y Evaluación Multicategórica de Brier

* **Ω (Resumen):** Motor analítico de solo lectura que evalúa la concordancia empírica entre las Distribuciones Soberanas/Fiduciarias (P', P̂) y los resultados reales consumados a lo largo de la temporada. Compara la calibración de Q-BE contra el mercado mediante Brier Score Multicategórico y desglosa el desempeño por jornada.
* **I (Input):** Histórico de partidos concluidos en `matches` y cuotas de cierre en `fixtures_snapshots.matches_json` (donde residen P' y los momios 1X2).
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Tasa de Coincidencia Fiduciaria Global (H_fid):**
     $$H_{\text{fid}} = \frac{N_{\text{favorito}} + N_{\text{empate}}}{N_{\text{total}}} \times 100$$
  2. **Brier Score Multicategórico:**
     $$BS_{\text{QBE}} = \frac{1}{3N} \sum_{i=1}^N \sum_{k \in \{1, X, 2\}} (\hat{p}_{i,k} - y_{i,k})^2$$
     $$BS_{\text{MKT}} = \frac{1}{3N} \sum_{i=1}^N \sum_{k \in \{1, X, 2\}} (q_{i,k}^{\text{mkt}} - y_{i,k})^2$$
     $$\text{Alpha de Calibración} = \left( 1.0 - \frac{BS_{\text{QBE}}}{BS_{\text{MKT}}} \right) \times 100$$
  3. **Jerarquía Estocástica de Vértices en Δ²:**
     Para cada encuentro, los desenlaces se ordenan estrictamente por probabilidad fiduciaria descendente:
     $$P_{\max} \ge P_{\text{mid}} \ge P_{\text{low}} \quad \text{con } R_{(1)}, R_{(2)}, R_{(3)} \in \{\text{LOCAL}, \text{EMPATE}, \text{VISITANTE}\}$$
     - $P_{\max}$ (Vértice Primario de Masa): Máxima convicción soberana de Q-BE (Golpe de ataque).
     - $P_{\text{mid}}$ (Vértice Secundario de Apoyo): Cobertura probabilística del segundo desenlace más probable. Queda desvinculado de ser exclusivamente el empate: en morfologías bipolares, $P_{\text{mid}}$ es el equipo rival.
     - $P_{\text{low}}$ (Vértice Residual de Riesgo): Cola de menor masa y fuente de la pérdida/ruptura.
  4. **Métricas de Cobertura y Desglose Factual:**
     - **Masa de Cobertura ($H_{\text{masa}}$):** $\% P_{\max} + \% P_{\text{mid}} = 100\% - \% P_{\text{low}}$.
     - **Tasa de Acierto Primario ($\% P_{\max}$):** Porcentaje de partidos donde ganó $R_{(1)}$.
     - **Tasa de Rescate Secundario ($\% P_{\text{mid}}$):** Porcentaje de partidos donde ocurrió $R_{(2)}$, desglosado en:
       * $\% P_{\text{mid}}^{(\text{emp})}$: Casos donde $R_{(2)}$ era Empate y ocurrió Empate.
       * $\% P_{\text{mid}}^{(\text{riv})}$: Casos donde $R_{(2)}$ era el Rival y ocurrió el Rival.
     - **Tasa de Ruptura Residual ($\% P_{\text{low}}$):** Porcentaje de partidos donde ganó $R_{(3)}$ (error máximo / eventos no controlados).
* **O (Output):** `CalibrationReportResponse` (resumen macro, tabla meso por jornada y parrilla micro estilo BetExplorer).
* **Φ (Transición):** Hacia `[ARCH-1.4.38]` e interfaz `index.html`.
* **[SHIELD]:** `tests/shield/test_shield_visor_backtesting.py` · `tests/shield/test_shield_visor_backtesting_cold_start.py`
* **Axioma del Prior de Mercado (Cold Start Resolution):** Para evitar que el Brier Score global y la clasificación de aciertos (la tríada de vértices $P_{\max}$ / $P_{\text{mid}}$ / $P_{\text{low}}$, extirpada la sigla derogada FAS/FES/FUS) se degraden artificialmente con "basura estadística" durante las primeras jornadas, todo partido que declare ignorancia fáctica ($S(\mathcal{I}) = 0$) sustituirá retrospectivamente su vector de probabilidad por el vector des-marginado del mercado ($q^{\text{mkt}}$) antes de ejecutar el clasificador factual. Esto garantiza un $\text{Alpha} = 0.00\%$ en dichos eventos. Para honrar el principio de Degradación Honesta (`[GOVERNANCE-01]`), la interfaz visual rotulará obligatoriamente estos partidos como `COLD START`.

---

### ID: [LN-QBE-101] Motor de Atribución Factorial y Telemetría de Integridad de Insumos

* **Ω (Resumen):** Descompone analíticamente el diferencial log-lineal de intensidades $\Delta \eta = \ln(\lambda_H / \lambda_A)$ en sus tres vectores de fuerza componentes (Ofensiva, Defensiva, Sede/Contexto), identifica el Driver Principal que movió la masa hacia $P_{\max}$, audita la completitud fáctica de insumos mediante 5 semáforos fiduciarios, y estructura la taxonomía de 44 variables fácticas (Nivel 1) agrupadas en 12 dimensiones para inspección forense.
* **I (Input):** Factores estructurales del partido: $A_H, D_A, A_A, D_H, C_H, C_A$, $\bar{\gamma}_{\text{home}}$, $\lambda_H, \lambda_A$, $\Delta_{\text{epist}}$, métricas fácticas de entrada y corte $N-1$.
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Descomposición Aditiva Exacta en Espacio Logarítmico:**
     $$\Delta \eta = \ln\left(\frac{\lambda_H}{\lambda_A}\right) = \underbrace{(A_H - D_A)}_{\Delta \text{Ofensiva}} + \underbrace{(D_H - A_A)}_{\Delta \text{Defensiva}} + \underbrace{(\bar{\gamma}_{\text{home}} + C_H - C_A)}_{\Delta \text{Contexto/Sede}}$$
     Garantiza la conservación de energía: $\Delta \text{Ofensiva} + \Delta \text{Defensiva} + \Delta \text{Contexto} \equiv \ln(\lambda_H) - \ln(\lambda_A)$.
     * **Cláusula de Amortiguamiento Canónico (`[VAULT-CORE-001]`):** los factores $A_H, D_A, A_A, D_H$ se reciben **crudos** (pre-damping) y la descomposición se ejecuta sobre su imagen canónica $\kappa_{net} \cdot \tanh(\cdot / \kappa_{net})$ con $\kappa_{net} = 0.2500$ absoluto, exactamente como los consume `estimar_intensidades_loglineal`. Sin esta cláusula, la suma factorial no reproduciría $\ln(\lambda_H/\lambda_A)$ y se violaría la conservación aditiva. Cero margen creativo: se delega en la función sellada del Libro de Constantes.
     * **Cláusula de Contexto:** $C_H = \ln(\max(0.90, \min(1.05, Q_{\text{mod},H})))$ y $C_A$ análogo, espejo de la formulación canónica Sección 4.9. El término $\bar{\gamma}_{\text{home}}$ absorbe la localía efectiva (base + bono de plaza + altitud + descanso), que es la única familia de términos no atribuible a los equipos.
  2. **Resolución del Driver Principal (Core Force Driver):**
     Determina $\text{Driver}^* = \arg\max_{k \in \{\text{Ofensiva, Defensiva, Contexto}\}} |\Delta_k|$.
     - Si $\Delta_{\text{Driver}} > 0 \implies$ Impulsa a Local ($P_{\text{local}}$).
     - Si $\Delta_{\text{Driver}} < 0 \implies$ Impulsa a Visitante ($P_{\text{visita}}$).
     - Desempate determinista: orden fijo `OFENSIVA → DEFENSIVA → CONTEXTO` (reproducibilidad estricta del Juez).
  3. **Lógica de los 5 Semáforos de Salud Fáctica (Data Health):**
     - `OPTA`: 🟢 $xG_{\text{Opta}} > 0$ real | 🟡 Calibrado $1.05 \cdot GF$ | 🔴 $S(\mathcal{I}) = 0$.
     - `SEDE`: 🟢 $PJ_{\text{sede}} \ge 3$ (Gate GSL-3D abierto) | 🟡 $1 \le PJ < 3$ | 🔴 $PJ = 0$.
     - `H2H`: 🟢 5 partidos ($\tau = 540\text{d}$) | 🟡 1 a 4 partidos | ⚪ Zero-H2H ($w_{\text{H2H}} = 0$).
     - `EPIST`: 🟢 $\Delta_{\text{epist}} \le 0.03$ (Consenso) | 🟡 $0.03 < \Delta \le 0.12$ (Fricción) | 🔴 $\Delta > 0.12$ (Ruptura).
     - `CTX`: 🟢 $Q_{\text{mod}} = 1.00$ | 🟡 Shock leve / fatiga | 🔴 Shock severo ($Q_{\text{mod}} \le 0.93$).
     * **Cláusula de Degradación Honesta:** la ausencia de evidencia jamás se maquilla. `SEDE` evalúa el mínimo bilateral de $PJ$ (gate GSL-3D exige solidez de ambas plazas); `H2H` sin enfrentamientos emite ⚪ NEUTRO conforme a la Ley Zero-H2H `[LN-QBE-020-B]`; `CTX` sin modulador publicado se lee $Q_{\text{mod}} = 1.00$ (ningún shock registrado).
  4. **Taxonomía de 44 Variables:** Estructura un diccionario inmutable de 12 dimensiones ($\mathcal{T}_{\text{Vol}}$ a $\mathcal{T}_{\text{Cls}}$) conteniendo el valor fáctico local/visita, procedencia y estado. La partición canónica es la del dossier normativo (`docs/QBE_RESEARCH_DOSSIER.md` §3): Volumen Territorial (4), Calidad de Remate (5), Defensa (5), Portería (3), Balón Parado y Penales (4), Disciplina (3), Shocks de Plantilla/Contexto (4), Trayectoria (4), Cronometría (4), Banca/Profundidad (2), Memoria Longitudinal/H2H (4) y Cierre de Partido (2) $= 44$.
* **O (Output):** `FactorAttributionResult(descomposicion, driver_principal, semaforos, variables_44_dict)`.
* **Φ (Transición):** Hacia `[ARCH-1.4.42]` y endpoint `/api/markets/backtesting/calibration-report`.
* **[SHIELD]:** `tests/shield/test_shield_factor_attribution_and_telemetry.py`

---

### ID: [LN-QBE-102] Axioma de Protección de la Evidencia en Vivo, Sello de Procedencia y Telemetría de Insumos Fácticos

**Régimen:** `[DIRGEN-STRICT]` en el candado transaccional y en el empaquetado forense del núcleo · `[DBBD-FUNGIBLE]` en la exhibición del sello.
**Base de Gobierno:** `[LN-QBE-101]` (atribución factorial) · `[ARCH-1.4.43]` (persistencia y DTOs) · `[DES-QBE-065]` (badge de procedencia).

* **I (Input):** `raw_match_data` (registro fáctico del partido) + el sello de procedencia $\omega = \texttt{origen\_captura} \in \{\text{EN\_VIVO}, \text{HISTORICO\_RECONSTRUIDO}\}$ declarado por la ruta invocante (no inferido del payload).
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Axioma 1 — Inmutabilidad de la Evidencia en Vivo (`LIVE_PROTECTION_LOCK`):** una distribución capturada en ventanilla es evidencia primaria y **no puede ser sobreescrita** por una reconstrucción histórica posterior:
     $$\text{lock}(r,\omega)=\begin{cases}\textbf{VETADO} & r.\omega=\text{EN\_VIVO}\ \wedge\ \omega=\text{HISTORICO\_RECONSTRUIDO}\\ \textbf{PERMITIDO} & \text{en cualquier otro caso}\end{cases}$$
     La relación es **estrictamente asimétrica**: `EN_VIVO → EN_VIVO` (re-captura de la misma evidencia) y `HISTORICO_RECONSTRUIDO → EN_VIVO` (ascenso de calidad de evidencia) **sí** escriben; sólo la **degradación de procedencia** queda vetada. El candado se evalúa **dentro de la misma transacción** (`gw.write_transaction`) leyendo la fila antes de asignar atributos, y se contabiliza en la clave aditiva `protegidos` del retorno.
  2. **Axioma 1-bis — Excepción del Hecho Consumado:** bajo blindaje se permite **una única** escritura, la de los marcadores oficiales en la tabla `matches` (`score_home`, `score_away`, `status = "FINISHED"`), porque el resultado oficial no altera la probabilidad calculada ni la evidencia capturada. Ningún otro campo de `sovereign_distributions` se toca.
  3. **Axioma 2 — Sello de Procedencia Único:** `origen_captura` viaja dentro de `audit_trace_json` y es la **única** fuente de verdad de la procedencia. El default canónico del puente de persistencia es `HISTORICO_RECONSTRUIDO` (**Regla de Menor Privilegio**: sólo un demonio de captura viva declara `EN_VIVO` explícitamente). Un registro sin la clave se lee `HISTORICO_RECONSTRUIDO`; **prohibido el backfill** de sellos en vivo sobre datos pasados.
  4. **Axioma 3 — Telemetría de Insumos Fácticos (`insumos_factivados`):** el generador empaqueta en la traza forense las magnitudes **efectivamente consumidas** por la matemática: tasas canónicas `xg_local_rate`/`xg_visita_rate`/`xga_*`/`gc_*` (acumulado ÷ PJ, `[ARCH-1.4.41]`), `sot_*`/`sota_*`/`poss_*`, `pj_sede_*` (`[LN-QBE-038]`), `h2h_conteo` (ventana $\tau = 540\text{d}$), `q_mod_h`/`q_mod_a`, `delta_alt_metros`, `delta_descanso_dias` y `xg_es_real_opta`. **Cero invención:** un insumo no publicado se declara `None`; el paquete se emite también en la rama de ignorancia $S(\mathcal{I}) = 0$.
  5. **Axioma 4 — Activación de las Ocho Variables Vivas:** cuando `insumos_factivados` está presente, el catálogo de 44 variables enciende `V01` (posesión), `V05` (xG/PJ), `V06` (SoT), `V10` (xGA/PJ con respaldo GC/PJ), `V11` (SoTA), `V27` (ΔDías), `V28` (ΔAltitud) y `V39` (ventana H2H) con el **valor fáctico** y estado `EVALUADO`; los semáforos `OPTA`/`SEDE`/`H2H`/`CTX` se pronuncian sobre el insumo publicado en lugar de degradar por omisión. Sin el paquete, la ruta heredada (`SIN EVIDENCIA` / `NEUTRO`) permanece **byte-idéntica**.
* **O (Output):** `StochasticAuditTrace(origen_captura, timestamp_captura, insumos_factivados, …)` · bloque `atribucion_factorial` con `origen_captura` y las 8 variables en `EVALUADO` · retorno del sincronizador `{procesados, exitosos, protegidos, errores}`.
* **Φ (Transición):** Hacia `[ARCH-1.4.43]`, `[DES-QBE-065]` y el endpoint `/api/markets/backtesting/calibration-report`.
* **[SHIELD]:** `tests/shield/test_shield_live_lock_and_input_telemetry.py`

---

### ID: [LN-QBE-103] Proveedor Soberano de Memoria H2H con Corpus Congelado, Certificación Tri-Estado de la Procedencia Opta y Telemetría Dimensional

**Régimen:** `[DIRGEN-STRICT]` en la extracción determinista, la futuro-ceguera y la certificación de procedencia · `[DBBD-FUNGIBLE]` en la exhibición bicolor del acordeón forense.
**Base de Gobierno:** `[LN-QBE-020]` (κ-Decay) · `[LN-QBE-020-B]` (Ley Zero-H2H) · `[LN-QBE-020-C]` (kernel H2H empírico) · `[LN-QBE-101]` (atribución factorial) · `[LN-QBE-102]` (Axiomas 3 y 4) · `[ARCH-1.4.44]` (proveedor unificado) · `[DES-QBE-066]` (acordeón bicolor).

* **I (Input):** la identidad del fixture $(s_L, s_V, f_{\text{ref}}, \ell)$ con $s_L, s_V$ slugs canónicos y $f_{\text{ref}}$ el kickoff; el **corpus congelado** `data/cache_h2h_liga_mx_2026.json` (esquema `h2h_corpus_v1`, sellado OFFLINE por `scripts/ingesta/congelar_cache_h2h_liga_mx.py` bajo `[ARCH-1.4.44]`); la bóveda 3NF (`fixtures_snapshots.matches_json` + catálogo `teams`); y el paquete `insumos_factivados` de la traza forense. **Cero red:** el proveedor no abre sockets, no dispara scraping y no consulta ningún origen externo.
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Unificación de vestimenta de identidad (puente slug ↔ nombre).** Los marcadores de la bóveda viajan en **nombres de exhibición** (`Team.name`) mientras el contrato del kernel exige **slugs canónicos**; el proveedor canonicaliza ambos lados con el catálogo `teams` (`name`/`short_name` $\to$ `canonical_slug`) antes de comparar parejas. Sin este puente la comparación es vacía por construcción (defecto erradicado: 0 duelos reportados con evidencia presente).
  2. **Futuro-ceguera estricta.** Sólo entra evidencia con $f_k < f_{\text{ref}}$ (anti-fuga en backfill histórico). Un duelo que empata o excede el kickoff queda excluido.
  3. **Deduplicación determinista.** Clave $(\text{fecha}, s_H, s_V)$ con **precedencia de la bóveda** sobre el corpus: una misma fuente duplicada jamás infla el conteo ni la masa efectiva.
  4. **Proyección al eje del fixture evaluado.** Los goles se leen en la perspectiva del club local evaluado: si el club fue visitante en el duelo histórico, los marcadores se intercambian.
  5. **Selección de los cinco más recientes.** Se ordena por `dias_antiguedad` ascendente y se retienen $\le 5$; $\text{dias\_antiguedad} = \max(0, (f_{\text{ref}} - f_k).\text{días})$.
  6. **Ponderación delegada (cero duplicación de plano).** La matriz se calcula con el kernel sellado `calcular_matriz_h2h_empirica` ($\tau_{\text{deep}} = 540\text{d}$, `[LN-QBE-020-C]`); el proveedor **no reimplementa** decaimiento ni normalización. Sin duelos $\Rightarrow$ lista vacía (Ley Zero-H2H `[LN-QBE-020-B]`): prohibido fabricar enfrentamientos.
  7. **Certificación tri-estado de la procedencia Opta.** Con $\mathcal{P}_{real} = \{\texttt{cache\_local}, \texttt{telemetria\_3nf}, \texttt{sensor\_fotmob}, \texttt{factual\_mixto}\}$ (fuentes fácticas FotMob/Opta) se certifica
     $$\texttt{xg\_es\_real\_opta} = \mathbb{1}\big[\pi_H \in \mathcal{P}_{real}\big] \cdot \mathbb{1}\big[\pi_V \in \mathcal{P}_{real}\big],$$
     y el semáforo `OPTA` se pronuncia en tres estados honestos sobre el insumo publicado:
     $$\text{opta} = \begin{cases} 🟢 & \texttt{flag} = 1 \\ 🟡 & \texttt{flag} = 0 \ \wedge\ (\texttt{xg\_local\_rate} \neq \varnothing \ \vee\ \texttt{xg\_visita\_rate} \neq \varnothing) \\ 🔴 & \text{en cualquier otro caso} \end{cases}$$
     El estado 🟡 declara la verdad incómoda: hay métrica xG publicada, pero **no está certificada como Opta real bilateral** (al menos un club-corte degradó a calibrado). El rojo queda reservado a la ausencia de métrica.
  8. **Telemetría dimensional del catálogo.** Cada una de las 12 dimensiones publica `total_variables`, `variables_evaluadas` (renglones con evidencia en local **o** visita) y `tiene_datos = 1[\text{variables\_evaluadas} > 0]`. Axioma 4 `[LN-QBE-102]`: `V10` enciende con `xga_*_rate` y, en su ausencia, con el **respaldo `gc_*_rate`** (ancla GC/PJ), declarándolo en la `nota` forense.
* **O (Output):** `List[H2HDueloVivo]` con `{goles_local, goles_visita, dias_antiguedad, fecha, fuente}` en la perspectiva del local evaluado · sello `xg_es_real_opta: bool` en el `raw_match_data` y en la traza del homologador · `semaforos.opta` tri-estado · por dimensión `{total_variables, variables_evaluadas, tiene_datos}`.
* **Φ (Transición):** Hacia `[ARCH-1.4.44]`, el homologador `scripts/ingesta/homologar_temporada_optah2h.py`, el daemon `scripts/daemons/centinela_deportivo.py`, `sovereign_pipeline.insumos_factivados` y el modal forense `[DES-QBE-066]`.
* **[SHIELD]:** `tests/shield/test_shield_opta_flag_and_accordion_telemetry.py`

### ID: [LN-QBE-104] Fusión Convexa del Símplex Soberano (Poisson ∪ Kernel H2H) y Persistencia de la Δ_epist Real

**Régimen:** `[DIRGEN-STRICT]` en la ley de mezcla, en la métrica de discrepancia y en el puente de persistencia · `[DBBD-FUNGIBLE]` en la cartelera de calibración (badge + filtro anti-cuarentena).
**Base de Gobierno:** `[LN-QBE-020-B]` (Ley Zero-H2H) · `[LN-QBE-020-C]` (kernel H2H empírico y TVD) · `[LN-QBE-102]` (evidencia 3NF sellada) · `[VAULT-CORE-005]` (ley de mezcla) · `[ARCH-1.6.22]` · `[DES-QBE-067]`.

* **I (Input):** el símplex paramétrico del Generador A $P_A = (p_1, p_X, p_2)$ ya publicado por el orquestador · la instancia ÚNICA del Generador C $P_C = (q_1, q_X, q_2)$ (`calcular_matriz_h2h_empirica`, $\tau_{\text{deep}} = 540\text{d}$) · el número de duelos verificables $N$ de la ventana sellada.
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Ley de mezcla convexa (`[VAULT-CORE-005]`):** con $w_{H2H} = \min(0.25, N \cdot 0.05)$ y $w_{Liga} = 1 - w_{H2H}$,
     $$P_{hib}(k) = w_{Liga} \cdot P_A(k) + w_{H2H} \cdot P_C(k), \quad k \in \{1, X, 2\}.$$
     Al ser una combinación convexa de dos distribuciones de probabilidad, $P_{hib}$ habita el mismo símplex $\Delta^2$ ($\sum_k P_{hib}(k) = 1$) y cada componente queda acotada entre los dos generadores: $\min(P_A(k), P_C(k)) \le P_{hib}(k) \le \max(P_A(k), P_C(k))$. El SÍMPLEX PUBLICADO —el que sostiene la Cláusula de André, el despacho de mesas y la calibración— es $P_{hib}$; el Poisson puro deja de ser la vitrina.
  2. **Una sola fuente del Generador C:** la misma instancia del kernel alimenta la discrepancia y la fusión (una invocación por partido). Cero doble fuente de verdad.
  3. **Métrica de discrepancia:** $\Delta_{epist}(\infty) = \max_k |P_A(k) - P_C(k)| \in [0, 1]$ (norma infinito sobre $\Delta^2$, cota de Kolmogorov), que acota por arriba la TVD sellada: $\text{TVD} \le \Delta(\infty)$. La TVD $\Delta_{epist}$ de `[LN-QBE-020-C]` **no se deroga**: sigue publicada en la traza como `discrepancia_epist`.
  4. **Ley Zero-H2H:** $N = 0$ (o `kernel=None`) $\Rightarrow w_{H2H} = 0$, la fusión es la **identidad** y $\Delta_{epist}(\infty)$ se declara en el piso de ignorancia del Contrato R-1 (`DELTA_EPISTEMICO_SIN_EVIDENCIA = 0.02`), jamás $0.0$: ausencia de evidencia no es coincidencia.
  5. **Persistencia honesta (`[VAULT-DATA-002]`):** `sovereign_distributions.epistemic_delta` deja de espejar el `ratio` $\lambda_{\max}/\lambda_{\min}$ —magnitud de tasas, sin relación con la evidencia— y persiste $\Delta_{epist}(\infty)$ con lectura `contrato de salida → traza forense → piso R-1` y acotamiento a $[0, 1]$. Un `None` heredado o un tipo no numérico NO se maquilla con $0.0$. El `ratio` permanece intacto en `intensidades` (`[LN-QBE-102]`: la evidencia 3NF no se reescribe). **Prohibido el backfill** sobre filas históricas.
  6. **Cartelera anti-cuarentena (`[DES-QBE-067]`):** los partidos vetados ($\text{EPIST} = 🔴$, $\Delta_{epist} > 0.12$, `[LN-QBE-070-B]`) pueden excluirse de la vitrina de calibración mediante `#chk-excluir-vetados`. El filtro es de **PRESENTACIÓN**: re-deriva los agregados desde los **conteos enteros** del subconjunto, declara el universo efectivo en `#bt-estado` y **jamás** muta `backtestingReportCache`. Con $0$ vetados el filtro es inerte (idempotencia estricta: manda el agregado servido).
  7. **Badge honesto (`[DES-QBE-067]`):** una dimensión del catálogo forense sin una sola variable evaluada NO exhibe `0/0 evaluadas` —que finge medición—, declara `SIN EVALUAR` (`[GOVERNANCE-01]`: cero maquillaje).
* **O (Output):** `SovereignDistributionOutput` con el símplex HÍBRIDO (`p_local`, `p_empate`, `p_visitante`) y `epistemic_delta = Δ_epist(∞)` · `StochasticAuditTrace` con `simplex_poisson` (Generador A puro), `epistemic_delta` y `kernel_h2h_empirico` enriquecido con `peso_h2h`/`peso_liga` · fila 3NF con `epistemic_delta` real · cartelera con filtro anti-cuarentena y badge `SIN EVALUAR`.
* **Φ (Transición):** Hacia `[ARCH-1.6.22]`, `[DES-QBE-067]`, el visor de backtesting (`/api/markets/backtesting/*`), la Cláusula de André y el despacho de mesas (ambos consumen el símplex publicado).
* **[SHIELD]:** `tests/shield/test_shield_ensemble_fusion_and_ui_sync.py` · `tests/shield/test_shield_bayesian_form_and_h2h.py` (enmienda E-2: invariantes de mezcla) · `tests/shield/test_shield_venue_splits_and_h2h_deep.py` · `tests/shield/test_shield_gsl3d_orthogonal_engine.py`.

---

### ID: [LN-QBE-105] Consolidación Fáctica de la Dimensión Memoria Longitudinal (H2H)

* **Ω (Resumen):** Expande la ingesta del Kernel H2H para nutrir las variables V39, V40 y V41 del Catálogo Forense. Extrae el récord de victorias, el diferencial neto de goles históricos y aísla la resistencia específica del visitante en la sede evaluada, proveyendo al analista evidencia cuantitativa del peso del enfrentamiento directo sin alucinaciones.
* **I (Input):** Lista de enfrentamientos históricos provista por `h2h_provider.py`, extendida con la bandera `es_local_sede: bool`.
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Aprovisionamiento Extendido:** El motor H2H marca cada duelo histórico con `es_local_sede = True` si el `local_slug` evaluado fue el equipo local en dicho encuentro pasado.
  2. **Agregación de V39 (Récord H2H):**
     Calcula $W$ (victorias locales), $D$ (empates), $L$ (victorias visitantes) desde la perspectiva del equipo local evaluado. Se formatea como `"{W}V - {D}E - {L}D"`.
  3. **Agregación de V40 (Diferencial $\Delta G$):**
     $$\Delta G_{\text{H2H}} = \sum (GF_{\text{local\_evaluado}} - GC_{\text{local\_evaluado}})$$
     Se formatea con signo `+` o `-` (ej. `"+2"` o `"-1"`).
  4. **Agregación de V41 (Resistencia en Sede):**
     Filtra los duelos donde `es_local_sede == True`. Calcula el récord del visitante ($W_{\text{vis}}, D_{\text{vis}}, L_{\text{vis}}$) y lo formatea como `"{W}V - {D}E - {L}D"`. Si no hay duelos en esa sede, emite `"Sin antecedentes locales"`.
  5. **Variable V42 (xG Histórico):** Permanece explícitamente como `SIN EVIDENCIA` en espera de la Fase 6 (Deep Opta Cache).
* **O (Output):** Bloque `h2h_stats` inyectado en `insumos_factivados`.
* **Φ (Transición):** Hacia `factor_attribution.py` (V39, V40, V41).
* **[SHIELD]:** `tests/shield/test_shield_h2h_dimension_population.py`

**Enmiendas ratificadas por el Director (Dictamen 2026-10-17, Opción A):**
1. **Punto de inyección:** `h2h_stats` se calcula en el paso 0 de `generar_distribucion_soberana` (antes del gate $S(\mathcal{I})$), de modo que el paquete `insumos_factivados` lo porta también en la rama de ignorancia (`[LN-QBE-102]`, Axioma 3).
2. **Precedencia V39:** `h2h_stats` manda **cuando está presente**; en su ausencia la ruta heredada `_FORMATO_INSUMO["V39"] = ("h2h_conteo", None, "partidos")` permanece **byte-idéntica** (`"N partidos"`).
3. **Columna de V41:** el récord del visitante en la sede se transcribe en la columna `local` de la celda forense con el sufijo declarativo `" (Visita)"` y `visita = None`; la celda mantiene `estado = EVALUADO`.
4. **Alias de dimensión:** cada dimensión del catálogo publica de forma **aditiva** `nombre` (= `titulo`), conservando `dimension` y `titulo` (cero ruptura del DTO `[LN-QBE-101]`).
5. **Cero de $\Delta G$:** cuando $\Delta G_{\text{H2H}} = 0$ se emite `"0"` (neutro, sin signo); en cualquier otro caso se emite con signo explícito `+`/`-`.
6. **Bandera ausente:** un duelo sin `es_local_sede` (fila histórica previa a la re-sincronización) no acredita sede alguna; el filtro de V41 no lo cuenta y, sin duelos acreditados, V41 emite `"Sin antecedentes locales"`. Cero fabricación de sede.
7. **Acordeón UI:** la reparación se materializa sobre la geometría sellada `[DES-QBE-064/066]` (`<details>` + hidratación dinámica `_badgeDimension44`), sin Bootstrap y sin rótulo literal en la plantilla del `summary`; `SIN EVALUAR` subsiste únicamente como fallback honesto de una dimensión con cero variables evaluadas (`[DES-QBE-067]`).

### ID: [LN-QBE-106] Pipeline Sandbox Autónomo y Modelado Relacional de Memoria H2H

* **Ω (Resumen):** Establece el protocolo de experimentación y validación desacoplada de la interfaz gráfica mediante pipelines autónomos en consola (CLI-First). Modela las variables de la Dimensión 11 bajo la taxonomía relacional: V39 como multiconjunto de resultados, V40 como magnitud diferencial con atribución explícita al bando beneficiario, y V41 como rendimiento condicionado a la sede, eliminando la asimetría artificial de columnas locales vacías.
* **I (Input):** `match_id: str` o `jornada: int`, persistencia SQLite en modo lectura, caché histórica congelada `data/cache_h2h_liga_mx_2026.json`.
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Aislamiento de Entorno:** El pipeline opera de punta a punta como función pura de solo lectura (`Read-Only`). Prohibido mutar `data/qbe_database.db`.
  2. **Modelado Relacional Antisimétrico de V40 ($\Delta G$):**
     $$\Delta G_{\text{local}} = \sum (GF_L - GC_L) \quad \Longleftrightarrow \quad \Delta G_{\text{visita}} = -\Delta G_{\text{local}}$$
     - Si $\Delta G_{\text{local}} > 0 \implies$ Beneficiario: `LOCAL` con ventaja de $+\Delta G$ goles.
     - Si $\Delta G_{\text{local}} < 0 \implies$ Beneficiario: `VISITANTE` con ventaja de $+|\Delta G|$ goles.
     - Si $\Delta G_{\text{local}} = 0 \implies$ `EQUILIBRADO` (0 goles de diferencia).
  3. **Ejecución y Contraste Estocástico Completo:**
     - Resuelve la distribución Poisson Pura $\hat{P}_{\text{poisson}}$ y el Kernel H2H $\hat{P}_{\text{H2H}}$.
     - Calcula la Discrepancia Epistémica Real $\Delta_{\text{epist}} = \max_k |P_{\text{poisson}}(k) - P_{\text{H2H}}(k)|$.
     - Computa la Distribución Híbrida Soberana $\hat{P}_{\text{híbrida}}$ mediante la combinación convexa con $w_{\text{H2H}} = \min(0.25, N_{\text{H2H}} \cdot 0.05)$.
     - Evalúa el cambio de convicción: $\Delta P = \hat{P}_{\text{híbrida}} - \hat{P}_{\text{poisson}}$.
* **O (Output):** Reporte forense en consola con tablero ASCII de alta densidad y diccionario estructurado para pruebas (`--json`).
* **Φ (Transición):** Hacia `scripts/laboratorio/sandbox_h2h_pipeline.py`.
* **[SHIELD]:** `tests/shield/test_shield_sandbox_h2h_pipeline.py`

### ID: [LN-QBE-107] Simulación Retrospectiva de Rentabilidad, Liquidación Factual y Métricas de Riesgo del Fondo

**Régimen:** `[DIRGEN-STRICT]` en la liquidación factual, la delegación matemática y las cotas de capital · `[DBBD-FUNGIBLE]` en la composición del pipeline, el CLI y el tablero.
**Base de Gobierno:** `[LN-QBE-082]` (sizing monótono) · `[LN-QBE-070]`/`[LN-QBE-071]` (dutching y piso de ventanilla) · `[LN-QBE-079]` (contracción fiduciaria) · `[ARCH-1.4.14]` (denominador de cartelera) · `[GOVERNANCE-01]` (cero cifras sintéticas).

* **Ω (Resumen):** Cierra el circuito fiduciario del fondo: convierte decisiones YA congeladas en la 3NF (estrategia, partición y stake) más los marcadores oficiales consumados en un **estado de resultados de cartera** (PnL, ROI, máximo drawdown, tasa de preservación $V=0$ y proyección anualizada a 40 jornadas). Es un instrumento de **medición**, jamás de optimización: no recalibra parámetros, no reentrena modelos y no escribe una sola fila.
* **I (Input):** `bankroll_inicial > 0` · `rango_jornadas` (p. ej. `1-11`) · `modo ∈ {compuesto, plano}` · bóveda 3NF en **sólo lectura** (`fixtures_snapshots.matches_json` para $P'$, cuotas y `pago_anticipado`; `matches.score_home` / `score_away` como único oráculo; `sovereign_distributions` como respaldo declarado de $P'$).
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Aislamiento y delegación:** `PersistenceGateway.read_session()` sin transacción de escritura. La aritmética NO se reimplementa: se invocan VERBATIM `triaje_determinista_9_estrategias` (`[LN-QBE-060-B]`), `contraer_distribucion_fiduciaria` (`[LN-QBE-079]`), `calcular_probabilidad_exito_estrategia` y `ordenar_cartera_por_certeza_lexicografica` (`[LN-QBE-081]`), `asignar_capital_monotono_cartera` (`[LN-QBE-082]`) y `calcular_dutching_v0` (`[LN-QBE-070]`). Prohibido duplicar una constante o una fórmula del plano canónico.
  2. **Ventanilla retrospectiva declarada:** el triaje se alimenta con `es_operable = True` (idéntico al carril de Backtesting de `[ARCH-1.4.35]`: el veto de partido concluido `[ARCH-1.6.2]` se suspende porque la liquidación real EXIGE el resultado consumado) y con `delta_epist = 0.02`, estrato legislado por `[LN-QBE-070-C]` (la columna 3NF `epistemic_delta` no se transcribe: su unidad no está certificada). Un fixture sin cuotas 1X2 fácticas muere en la compuerta hacia `QBE-00`.
  3. **Sizing dinámico con base rodante:** la jornada $j$ dimensiona sobre $B_{j-1}$ en `modo=compuesto` (patrimonio real) y sobre $B_0$ en `modo=plano` (stake nominal fijo). Se preservan las cotas constitucionales $\text{tope}^{\text{indiv}} = 8\%\cdot B$ y $\text{tope}^{\text{cartera}} = 25\%\cdot B$. El piso de ventanilla de $\$2.00$ MXN **no infla** la orden: cuando el piso bivariado ($\$4.00$ MXN) es inalcanzable bajo el tope, la posición se descarta y el capital permanece líquido (`capital_no_desplegado`), conforme al precedente del tope que prevalece.
  4. **Partición de boletos:** para la Familia con cobertura $(\text{H1},\text{H2},\text{R1},\text{R2})$ la partición la dicta `calcular_dutching_v0`: $B_{seg} = B_i / O_{emp}$, $B_{prio} = B_i - B_{seg}$, con pierna de ataque = favorito en H1/H2 y = underdog en R1/R2. Las familias sin cobertura $(\text{D1},\text{D2},\text{C1},\text{C2})$ viajan con $B_{seg} = \$0.00$. Nota de paridad declarada: la rama `R2` del motor vivo usa ponderación inversa de probabilidad; el sandbox aplica la ley $V=0$ uniforme por mandato de `[LN-QBE-070]`, de modo que toda cobertura de tablas preserva el capital íntegro.
  5. **Liquidación factual en cinco desenlaces:** con $B_i$ la inversión, $O_{ata}$ la cuota de la pierna de ataque y $O_{emp}$ la del empate:
     - `VICTORIA_FAVORITO` — la pierna de ataque gana: $\text{Cobro} = B_{prio}\cdot O_{ata}$.
     - `COBERTURA_EMPATE_V0` — tablas en familia con cobertura: $\text{Cobro} = B_{seg}\cdot O_{emp} \approx B_i$ (indemnidad, tolerancia de redondeo $\le \$0.08$).
     - `DOBLE_COBRO_PA` — tablas con Pago Anticipado **acreditado**: $\text{Cobro} = B_{prio}\cdot O_{ata} + B_{seg}\cdot O_{emp}$.
     - `RUPTURA_P_LOW` — gana el bando no cubierto (o tablas sin cobertura): $\text{Cobro} = \$0.00$.
     - `NO_LIQUIDABLE` — sin marcador oficial: capital devuelto, $\text{PnL} = \$0.00$; **jamás se fabrica un $0\text{-}0$**.
     El Pago Anticipado se acredita con testigo fáctico: margen final $\ge 2$ goles del bando de ataque (necesariamente lideró por $+2$ en algún instante). En tablas el único testigo válido es la traza in-play opcional `ventaja_maxima_favorito`; sin ella, la acreditación se declara negativa con motivo explícito y se liquida $V=0$ puro.
  6. **Métricas de riesgo del fondo:** con la curva $\{B_0, B_1, \dots, B_N\}$ completa,
     $$\text{DD}_j = \frac{\max_{k \le j} B_k - B_j}{\max_{k \le j} B_k}\times 100\% \qquad \text{DD}_{\max} = \max_j \text{DD}_j$$
     y la tasa de preservación se computa sobre el denominador honesto de desenlaces defensivos: $\text{Tasa}_{V=0} = \frac{\#\text{COBERTURA\_EMPATE\_V0}}{\#\text{COBERTURA\_EMPATE\_V0} + \#\text{RUPTURA\_P\_LOW}}$. Los `NO_LIQUIDABLE` quedan fuera y se reportan aparte.
  7. **Proyección anualizada (40 jornadas):** $\text{Lineal} = B_0 + \left(\text{PnL}_{\text{total}} / N_{\text{operadas}}\right)\cdot 40$; $\text{Compuesta} = B_0(1 + \overline{\text{ROI}})^{40}$ con $\overline{\text{ROI}} = \frac{1}{N}\sum_j \text{PnL}_j / B_{j-1}$; $\text{CAGR} = \left[(B_N/B_0)^{40/N} - 1\right]\times 100\%$. Guarda fiduciaria: si $(1+\overline{\text{ROI}}) \le 0$ la proyección compuesta se declara colapso analítico ($0.0$), nunca un valor imaginario o `NaN`.
* **O (Output):** Reporte estructurado con siete llaves maestras (`bankroll_final`, `pnl_acumulado`, `roi_acumulado_pct`, `drawdown_maximo_pct`, `resumen_coberturas`, `jornadas_detalle`, `curva_bankroll`) más `proyeccion_anual` (`lineal_mxn`, `compuesta_mxn`, `roi_anual_compuesto_pct`) y el tablero ASCII de alta densidad (`--json` suprime el tablero).
* **Φ (Transición):** Hacia `scripts/laboratorio/sandbox_rentabilidad_pipeline.py` y `[ARCH-1.4.46]`.
* **[SHIELD]:** `tests/shield/test_shield_sandbox_rentabilidad_pipeline.py`
* **Enmienda Nudo 3:** El motor matemático de simulación (`ejecutar_simulacion_rentabilidad`) debe residir en `src/core/` para ser consumido por la API REST, no en `scripts/laboratorio/`.

### ID: [LN-QBE-108] Colisión Cruzada de Fuerzas y Modelado Bipartito de Ataque (𝒯_Fin) y Defensa (𝒯_Def)

* **Ω (Resumen):** Sella el protocolo de aislamiento en consola del núcleo de mayor peso de la distribución soberana (>70 % de λ): la Calidad de Remate (Dimensión 2, `𝒯_Fin`, V05-V09) y la Contención Defensiva (Dimensión 3, `𝒯_Def`, V10-V14). Define la **colisión cruzada de fuerzas complementarias** —ataque de un bando contra la defensa del otro— y prohíbe expresamente la resta directa de ataques, preservando la estructura bipartita simétrica de las catorce variables.

* **I (Input):** `match_id: str` | `jornada: int`; corte N−1 de la 3NF (`matchday_num < N` ∧ estado terminal); caché congelada `data/cache_optaxg_liga_mx_2026.json` (xG/xGA por club y partido); `match_telemetry` (SoT/SoTA) únicamente cuando cubra el corte completo.

* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Futuro-ceguera N−1:** el corte de cada club son los partidos con `matchday_num < N` en estado terminal. El fixture evaluado JAMÁS alimenta su propia acumulación.
  2. **Cobertura íntegra:** si a un solo partido del corte le falta la métrica Opta, ese club-corte **no** publica la tasa (se degrada completo a la ruta sellada con GF/GC reales). Prohibido mezclar fuentes o imputar cifras (`[GOVERNANCE-01]`).
  3. **Colisión cruzada de fuerzas:**
     $$\Delta_{\text{of,H}} = A_H - D_A \qquad \Delta_{\text{of,A}} = A_A - D_H \qquad \Delta_{\text{neto}} = \Delta_{\text{of,H}} - \Delta_{\text{of,A}}$$
     El signo de $\Delta_{\text{neto}}$ identifica al bando dominante (`LOCAL` / `VISITANTE` / `EQUILIBRADO`). Los ataques **no** se restan entre sí: sólo se cruzan fuerzas complementarias.
  4. **Delegación matemática obligatoria:** el sandbox consume VERBATIM `derivar_factores_estructurales` (`[VAULT-CORE-005]`) y `estimar_intensidades_loglineal` (`[VAULT-CORE-001]`); no reimplementa factores ni intensidades, de modo que la consola y el servidor central emiten la MISMA $\lambda_H$ y la MISMA $\lambda_A$ para el mismo insumo.
  5. **Contrato homologado (Decreto `VAR-2026-J7-HOMOLOGACION` §E1):** el `raw_match_data` publica `xg` y **nunca** `xga`; el xGA se exhibe como V10 sin inyectarse al motor (publicarlo invertía el diagnóstico defensivo medido).
  6. **Bipartita simétrica:** cada celda V0x publica `local` y `visita` independientes con su unidad canónica; una variable se declara `EVALUADO` sólo si AMBOS clubes publican magnitud real, y `SIN EVIDENCIA` en caso contrario — jamás un cero ficticio.
  7. **Presupuesto físico:** las intensidades resultantes se acotan al Invariante I6 $[\lambda_{\min}, \lambda_{\max}] = [0.15, 4.50]$ dentro del plano sellado, incluido el techo conjunto anti-resonancia `[LN-QBE-040-B]`.

* **O (Output):** Reporte estructurado con las llaves `dimension_2_ataque`, `dimension_3_defensa`, `colision`, `factores_estructurales`, `intensidades_proyectadas` y `semaforos`; tablero ASCII de alta densidad en consola (`--json` suprime el tablero).

* **Φ (Transición):** Hacia `scripts/laboratorio/sandbox_ataque_defensa_pipeline.py` y `[ARCH-1.4.47]`.

* **[SHIELD]:** `tests/shield/test_shield_sandbox_ataque_defensa_pipeline.py`

### ID: [LN-QBE-109] Modelado Físico de Shocks de Contexto, Altitud Fisiológica y Fatiga de Calendario

* **Ω (Resumen):** Modela formalmente las 4 variables de la Dimensión 7 ($\mathcal{T}_{\text{Shk}}$: Shocks de Contexto y Entorno, V25 a V28) que modulan el vector contextual $(C_H, C_A)$ y la ventaja territorial expandida $\gamma_{\text{home}}(H, A)$ en la ecuación log-lineal canónica. Aísla el impacto fisiológico de la altitud ($\Delta\text{Alt}^+$), la asimetría de recuperación en días ($\Delta\text{Descanso}$) y las perturbaciones por bajas críticas ($Q_{\text{mod}}$) bajo cotas estrictas de contención.
* **I (Input):** `match_id: str`, altitud de los estadios en msnm, fechas de inicio ($t_{\text{kickoff}}$) de los encuentros previos inmediatos de ambos clubes en `matches`, factores $Q_{\text{mod}, H}, Q_{\text{mod}, A} \in [0.90, 1.05]$.
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Altitud Fisiológica Unidireccional (V28):**
     $$\Delta\text{Altitud}^+ = \max\left(0, \;\text{Altitud}_{\text{Local}} - \text{Altitud}_{\text{Visita}}\right)$$
     $$\text{Bono}_{\text{alt}} = 0.0300 \cdot \left(\frac{\Delta\text{Altitud}^+}{1000.0}\right)$$
     *(Solo opera si el local juega a mayor altura que la visita; jugar a nivel del mar no penaliza al local frente a un rival de altura).*
  2. **Diferencial de Descanso y Fatiga (V27):**
     $$\text{Días}_T = \min\left(14.0, \; (t_{\text{kickoff}} - t_{\text{anterior}, T}).\text{days}\right) \quad \text{para } T \in \{H, A\}$$
     $$\Delta\text{Descanso}_{H, A} = \text{Días}_H - \text{Días}_A$$
     $$\text{Bono}_{\text{rec}} = 0.0200 \cdot \text{Clamp}(\Delta\text{Descanso}_{H, A}, \; [-3.0, \; +3.0])$$
  3. **Fortaleza de Plaza Aditiva:**
     $$\Delta\gamma_{\text{plaza}} \in [0.00, 0.10] \quad \text{según catálogo sellado en CONSTANTS.md (Tigres +0.07, Toluca +0.06, etc.)}$$
  4. **Vector Contextual Compuesto:**
     $$\gamma_{\text{contextual}} = \bar{\gamma}_{\text{base}} + \Delta\gamma_{\text{plaza}} + \text{Bono}_{\text{alt}} + \text{Bono}_{\text{rec}} \quad (\text{con } \bar{\gamma}_{\text{base}} = 0.1500)$$
     $$C_H = (\gamma_{\text{contextual}} - \bar{\gamma}_{\text{base}}) + \ln(Q_{\text{mod}, H})$$
     $$C_A = \ln(Q_{\text{mod}, A})$$
     $$\Delta\text{Contexto} = \bar{\gamma}_{\text{base}} + C_H - C_A$$
  5. **Variables de Bajas (V25 y V26):**
     - $V25$ (Bajas ofensivas): $Q_{\text{mod}, H}$ expresado en porcentaje de merma ($1.00 \to 0\%$, $0.92 \to -8\%$).
     - $V26$ (Bajas defensivas): $Q_{\text{mod}, A}$ expresado en porcentaje de merma. Si no hay reporte médico auditado, se fijan en `1.00` (`SIN SHOCK / EVALUADO`).
* **O (Output):** Estructura `ContextoShocksResult` con V25 a V28 evaluadas, desglose de bonos físicos, $\gamma_{\text{contextual}}$, $C_H, C_A$, y el reporte ASCII en consola.
* **Φ (Transición):** Hacia `scripts/laboratorio/sandbox_contexto_shocks_pipeline.py`.
* **[SHIELD]:** `tests/shield/test_shield_sandbox_contexto_shocks_pipeline.py`

### ID: [LN-QBE-110] Modelado Fáctico de Trayectoria, Tendencias de Goles Esperados y Varianza xPTS

* **Ω (Resumen):** Modela formalmente las 4 variables de la Dimensión 8 ($\mathcal{T}_{\text{Traj}}$: Trayectoria y Dinámica Temporal, V29 a V32) que capturan la aceleración o desaceleración competitiva de los clubes en una ventana móvil de 5 partidos ($5P$). Cuantifica la pendiente de peligro ofensivo ($m_{xG}$), la pendiente de vulnerabilidad defensiva ($m_{xGA}$), el momento de puntos (Forma 5P) y el diferencial de puntos esperados ($\Delta xPTS$), aislando el sobre-rendimiento espurio por suerte de la calidad futbolística estructural para alimentar la contracción bayesiana (`[LN-QBE-036]`).
* **I (Input):** `match_id: str` o `jornada: int`, series cronológicas de $xG$ y $xGA$ de los últimos 5 partidos jugados por cada club hasta el corte $N-1$, puntos reales y puntos esperados ($xPTS$) acumulados.
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Momento y Puntos Recientes (V29):**
     $$\text{Pts5P}_T = \sum_{k=1}^5 (3 \cdot \mathbb{I}_{\{G_k\}} + 1 \cdot \mathbb{I}_{\{E_k\}}) \in [0, 15] \quad \text{para } T \in \{H, A\}$$
     $$\Delta\text{Pts5P} = \text{Pts5P}_H - \text{Pts5P}_A \in [-15, +15]$$
  2. **Pendientes de Evolución de Peligro (V30 y V31):**
     Para la serie cronológica de 5 partidos $t \in \{1, 2, 3, 4, 5\}$ con valores $y_t \in \{xG_t, xGA_t\}$:
     $$m = \frac{\sum_{t=1}^5 (t - \bar{t})(y_t - \bar{y})}{\sum_{t=1}^5 (t - \bar{t})^2} = \frac{\sum_{t=1}^5 (t - 3)(y_t - \bar{y})}{10}$$
     - $V30$ (Pendiente $xG$): $m_{xG} > 0 \implies$ Aceleración ofensiva; $m_{xG} < 0 \implies$ Desaceleración.
     - $V31$ (Pendiente $xGA$): $m_{xGA} < 0 \implies$ Consolidación defensiva (mejora); $m_{xGA} > 0 \implies$ Resquebrajamiento defensivo.
  3. **Diagnóstico de Varianza y Regresión a la Media (V32):**
     $$\Delta xPTS_T = \text{PTS}_T - xPTS_T \quad \text{para } T \in \{H, A\}$$
     - $\Delta xPTS \ge +3.0 \implies$ **Sobrerrendimiento Crítico (Alerta de Regresión):** El equipo ha sumado puntos por azar/suerte; su nivel de juego no respalda la cosecha.
     - $\Delta xPTS \le -3.0 \implies$ **Subrrendimiento Fiduciario (Rebote Inminente):** El equipo juega bien pero ha perdido puntos por varianza desfavorable.
     - Diferencial de Partido: $\Delta xPTS_{\text{neto}} = \Delta xPTS_H - \Delta xPTS_A$.
* **O (Output):** Estructura `TrayectoriaMomentoResult` con V29 a V32 evaluadas, pendientes de tendencia con dirección, saldo de suerte y el reporte ASCII en consola. Toda celda degrada a `SIN EVIDENCIA` si la ventana de 5 partidos está incompleta o la serie $xG/xGA$ presenta faltantes (cero imputación); el tablero publica entonces el guion fiduciario.
* **Φ (Transición):** Hacia `scripts/laboratorio/sandbox_trayectoria_momento_pipeline.py`.
* **[SHIELD]:** `tests/shield/test_shield_sandbox_trayectoria_momento_pipeline.py`

### ID: [LN-QBE-111] Modelado Fáctico de Volumen Territorial y Rendimiento de Guardametas (Volumen & Portería)

* **Ω (Resumen):** Modela formalmente las 4 variables de la Dimensión 1 ($\mathcal{T}_{\text{Vol}}$: Volumen y Dominio Territorial, V01 a V04) y las 3 variables de la Dimensión 4 ($\mathcal{T}_{\text{Gk}}$: Rendimiento de Guardametas, V15 a V17), aislándolas del núcleo de proyección $\lambda$ para que **jamás dupliquen** la señal de peligro ya contabilizada por el $xG$. Define el **residuo de volumen ortogonal** $v_{\text{Vol}}^{\perp}$ —el dominio territorial que NO se tradujo en remate— mediante la reducción cerrada del Factor de Control de Cancha (`[LN-QBE-030]`) montada sobre la base ortogonalizada de Gram-Schmidt (`[LN-QBE-039]`), y el **Porcentaje de Atajadas** ($Save\%$) como métrica individual del guardameta, independiente de la calidad de la zaga. Prohíbe la suma lineal de posesión y $xG$ (doble contabilización) y toda imputación de cifras (`[GOVERNANCE-01]`).
* **I (Input):** `match_id: str` o `jornada: int`; corte N−1 de la 3NF (`matchday_num < N` ∧ estado terminal); caché congelada `data/cache_optaxg_liga_mx_2026.json` ($xG$/$xGA$ por club y partido); `match_telemetry` ($poss\_pct$, $SoT$, $SoTA$) únicamente cuando cubra el corte **completo** de cada club.
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Futuro-ceguera N−1:** el corte de cada club son los partidos con `matchday_num < N` en estado terminal. El fixture evaluado JAMÁS alimenta su propia acumulación.
  2. **Cobertura íntegra:** si a un solo partido del corte le falta la posesión, el $SoT$ o el $SoTA$, ese club-corte **no** publica la variable (se degrada completo a `SIN EVIDENCIA`). Prohibido mezclar fuentes o imputar cifras (`[GOVERNANCE-01]`); una fila creada con los defaults del esquema (`0.0` / `50.0`) NO es evidencia.
  3. **Residuo de Volumen Ortogonal (V01-V04 · GSL-3D):** con $\mathbb{H}_{\text{att}} = \operatorname{span}(u_{xG}, u_{SoT}, u_{\text{Vol}})$ y ortogonalización de Gram-Schmidt (`[LN-QBE-039]`), la señal de volumen se reduce al factor cerrado sellado:
     $$\text{Raw\_FCF}_T = \left(\frac{\text{Poss}_T}{50.0}\right)\cdot\left(\frac{2.0\,(SoT_T+1.0)}{SoT_T+SoTA_T+2.0}\right) \qquad FCF_T = \operatorname{Clamp}(\text{Raw\_FCF}_T,\,[0.65,\,1.35])$$
     $$v_{\text{Vol},T}^{\perp} = FCF_T - 1.0000 \in [-0.35,\,+0.35]$$
     - $v_{\text{Vol}}^{\perp} < 0 \implies$ **presión estéril:** dominio territorial sin remate (posesión inflada).
     - $v_{\text{Vol}}^{\perp} > 0 \implies$ **dominio convertido:** la posesión sí produjo peligro.
     - $v_{\text{Vol}}^{\perp} = 0 \implies$ neutralidad territorial.
     El residuo es **diagnóstico**: no se reinyecta a $\lambda$ (el motor sellado ya consume la señal directora $xG$).
  4. **Porcentaje de Atajadas (V16) [ALGO-PROTECTED]:** sobre el corte N−1 con cobertura íntegra de $SoTA$ y goles en contra reales:
     $$Save\%_T = \operatorname{Clamp}\left(100\cdot\frac{SoTA_T - GC_T}{SoTA_T},\,[0,\,100]\right)$$
     Guardas: $SoTA_T = 0 \implies Save\%_T = 100.0$ (no hubo remate a puerta que atajar); $GC_T > SoTA_T \implies Save\%_T = 0.0$ (imposible por física del marcador: se satura, nunca se publica un negativo).
  5. **Delegación matemática obligatoria:** el sandbox NO reimplementa el FCF ni sus clamps; invoca VERBATIM `SyntheticMetricsEngine._compute_fcf` (`[LN-QBE-030]`, `src/core/metrics.py`) y resta la unidad. La consola y el servidor central emiten por construcción el MISMO $FCF$ para el mismo insumo.
  6. **Bipartita simétrica:** cada celda V01-V04 y V15-V17 publica `local` y `visita` independientes con su unidad canónica; una variable se declara `EVALUADO` sólo si AMBOS clubes publican magnitud real, y `SIN EVIDENCIA` en caso contrario — jamás un cero ficticio.
  7. **Degradación fiduciaria:** V02 (toques en área), V03 (pases progresivos), V04 (entradas al último tercio), V15 ($xGOT$) y V17 (salidas por alto) se declaran `SIN EVIDENCIA (FASE 6)` mientras el sensor congelado no los publique. V01 y V16 degradan igual si el corte N−1 no cubre la posesión o el $SoTA$; el tablero publica entonces la cobertura `cubiertos/total` de ambos clubes.
* **Trazabilidad de varianza (`VAR-2026-LAB5-EVIDENCIA`, ratificada por el Director/Arquitecto):** el Juez `[SHIELD]` certifica el **contrato tri-estado** de V01/V16 —`EVALUADO` con magnitud real, o `SIN EVIDENCIA (FASE 6)` con valores `None` y nota de cobertura— en lugar de exigir una posesión y un $SoTA$ que el corpus 2026 no publica. La aserción de suma $100\%$ queda **condicionada** a que V01 esté `EVALUADO`. Se prohíbe todo mock o cifra inventada para alcanzar el verde (`[GOVERNANCE-01]`). Acta: `docs/DIRGEN_VARIANCE_REQUEST_LAB5_EVIDENCIA.md`.
* **Trazabilidad de varianza (`VAR-2026-LAB5-FCF-COTAS`, resuelta por alto al fuego):** el primer vector del Juez para $v_{\text{Vol}}^{\perp}$ afirmaba un clamp que aritméticamente no ocurre —$\text{Raw\_FCF}=0.78$ con $(\text{Poss}=65, SoT=2, SoTA=6)$ vive DENTRO de la banda $[0.65,1.35]$—. Se enmendó **sólo el vector de prueba**: la saturación inferior se certifica con $(\text{Poss}=30, SoT=2, SoTA=6)\Rightarrow \text{Raw\_FCF}=0.36 \Rightarrow \text{clamp } 0.65 \Rightarrow -0.35$, y el caso interior se conserva como aserción de **no-clamp** ($-0.22$) que prueba la delegación verbatim a `SyntheticMetricsEngine._compute_fcf`. Cero mutación en `src/core/metrics.py`, en `FCF_MIN`/`FCF_MAX` o en la delegación; la consola y el servidor central siguen emitiendo el MISMO $FCF$. Acta: `docs/DIRGEN_VARIANCE_REQUEST_LAB5_FCF_COTAS.md`.
* **Ω (Algoritmo — Procedencia fáctica de la telemetría óptica, `VAR-2026-LAB5-EVIDENCIA` Opción A ejecutada):** el sensor `matchDetails` de FotMob (claves duras `BallPossesion` y `ShotsOnTarget`) se congela en `data/cache_telemetria_liga_mx_2026.json` (SHA-256 auto-excluyente, rehidratable con `--desde-cache`) y se materializa en la tabla 3NF `match_telemetry` (`possession_pct`, `sot`, `sota`; `xg`/`xga` = `NULL`) mediante `scripts/ingesta/congelar_telemetria_fotmob.py`. Reglas invariables: (1) **reciprocidad defensiva** `sota_home ≡ sot_away` y `sota_away ≡ sot_home`; (2) **bipartita por partido** `poss_home + poss_away ≡ 100.0`; (3) **no complementariedad entre cortes independientes** — la media de posesión del corte N−1 de un club y la de su rival son muestras separadas y NO suman 100 (San Luis 52.9 % + Santos Laguna 50.8 % = 103.7 %); la identidad legítima es `V01.local_num == mean(poss del corte)` y el diferencial es `Δ = local_num − visita_num` ($+2.1$ pp en `LIGAMX-J11-07`); (4) **cero imputación** — `0.0` de posesión se trata como ausencia (centinela) y degrada la celda a `SIN EVIDENCIA (FASE 6)` sin promediar un cero falso; (5) un partido sin `BallPossesion` o `ShotsOnTarget` queda fuera de la ingesta y se declara en `faltantes`. El $FCF$ y $v_{\text{Vol}}^{\perp}$ siguen siendo propiedad exclusiva de `[LN-QBE-030]` (delegación verbatim; aquí no se recalcula).
* **O (Output):** Estructura `VolumenPorteriaResult` con `dimension_1_volumen` (V01-V04), `dimension_4_porteria` (V15-V17), `delta_posesion`, `residuo_volumen` (clave real del bloque $v_{\text{Vol}}^{\perp}$ por club; la referencia histórica `residuo_volumen_ortogonal` se corrige aquí sin tocar el sandbox), `cobertura` de telemetría y de `opta_xg` por club, `corte_n_1`, `semaforos` y el reporte ASCII de tres secciones en consola (`--json` suprime el tablero).
* **Φ (Transición):** Hacia `scripts/laboratorio/sandbox_volumen_porteria_pipeline.py` y `[ARCH-1.4.50]`.
* **[SHIELD]:** `tests/shield/test_shield_sandbox_volumen_porteria_pipeline.py`

### ID: [LN-QBE-112] Modelado de Micro-Dinámicas, Balón Parado, Fricción Disciplinaria y Cierre Táctico

* **Ω (Resumen):** Modela formalmente las 15 variables de micro-dinámicas que completan la taxonomía de 44 variables del Tratado Vol. I: Dimensión 5 ($\mathcal{T}_{\text{Spc}}$: Balón Parado y Penales, V18-V21), Dimensión 6 ($\mathcal{T}_{\text{Dsc}}$: Fricción Disciplinaria, V22-V24), Dimensión 9 ($\mathcal{T}_{\text{Time}}$: Cronometría de Gol, V33-V36), Dimensión 10 ($\mathcal{T}_{\text{Sub}}$: Gestión de Banca y Profundidad, V37-V38) y Dimensión 12 ($\mathcal{T}_{\text{Cls}}$: Comportamiento de Cierre, V43-V44). Evalúa asimetrías de táctica fija, riesgo de inferioridad numérica (rojas), fatiga en segundas partes (1T vs 2T) y fragilidad tardía en los minutos finales (80'-90'+) para auditar la robustez del Pago Anticipado (+PA).
* **I (Input):** `match_id: str` o `jornada: int`, corte histórico $N-1$ en SQLite 3NF y telemetría Opta congelada.
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Balón Parado y Penales (V18 a V21):**
     - $V18 / V19$: Producción y concesión de $xG$ a balón parado por 90'.
     - $V20$: Córners a favor por 90' ($\Delta\text{Córners} = \text{Córners}_H - \text{Córners}_A$).
     - $V21$: Penales a favor históricos por partido.
  2. **Fricción Disciplinaria y Riesgo de Roja (V22 a V24):**
     - $V22$: Faltas en tercio defensivo por 90' (propensión a regalar tiros libres de peligro).
     - $V23$: Tarjetas amarillas promedio por 90'.
     - $V24$: Índice de expulsión ($\text{Rojas por partido} = \text{Rojas} / PJ$). Si supera $0.25 \implies$ Alerta de asimetría numérica.
  3. **Cronometría y Ratios de Desgaste (V33 a V36):**
     - $V33$: $\text{Ratio } xG_{1T/2T} = xG_{1T} / xG_{2T}$ ($> 1.0 \implies$ arranque explosivo; $< 1.0 \implies$ diesel / mejor en 2T).
     - $V34$: $\text{Ratio } xGA_{1T/2T} = xGA_{1T} / xGA_{2T}$ ($> 1.0 \implies$ fragilidad inicial; $< 1.0 \implies$ desajuste tardío).
     - $V35 / V36$: Goles anotados y concedidos en el intervalo inicial $0\text{-}15'$.
  4. **Banca y Rotación (V37 y V38):**
     - $V37$: $xG$ aportado por suplentes por 90'.
     - $V38$: Rotación del XI titular (variación de alineación entre jornadas consecutivas).
  5. **Comportamiento de Cierre Tardío (V43 y V44 — Salpicadura a Pago Anticipado):**
     - $V43$ (Clutch Offense): $xG$ producido entre los minutos $80'$ y $90'+$.
     - $V44$ (Fragilidad de Cierre): $xGA$ permitido entre los minutos $80'$ y $90'+$.  
       *Regla fiduciaria:* Un $V44_{\text{fav}} \ge 0.35\text{ xGA}$ alerta sobre alta probabilidad de perder ventajas de 2 goles en el tramo final, encendiendo el indicador de cobertura de Doble Cobro en Pago Anticipado (`[LN-QBE-083]`).
  6. **Axioma de Degradación Fiduciaria (`[GOVERNANCE-01]`):** Aquellas métricas cuyos feeds por tramo temporal o suplentes no estén presentes en el corpus disponible se marcan limpiamente como `SIN EVIDENCIA / FASE 6` con valores `None`. Prohibida la invención de cifras.
* **O (Output):** Estructura `MicroDinamicasResult` con las 15 variables evaluadas o degradadas, ratios cronométricos, índice de riesgo de roja y reporte ASCII en consola.
* **Φ (Transición):** Hacia `scripts/laboratorio/sandbox_micro_dinamicas_pipeline.py`.
* **[SHIELD]:** `tests/shield/test_shield_sandbox_micro_dinamicas_pipeline.py`

### ID: [LN-QBE-113] Veto Fiduciario Selectivo por Familia Estratégica en Simulador de Rentabilidad

* **Ω (Resumen):** Habilita la exclusión dinámica de familias estratégicas específicas (ej. Familia R: `QBE-R1`, `QBE-R2`) durante la orquestación retrospectiva de la cartera, permitiendo evaluar el impacto aislado de estrategias de alto riesgo sobre el Drawdown y el ROI del fondo. Las posiciones vetadas no absorben capital de la jornada y se declaran en abstención fiduciaria.
* **I (Input):** Lista de códigos a excluir (ej. `["QBE-R1", "QBE-R2"]`), resultado del triaje determinista base `[LN-QBE-060-B]`.
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. Para cada partido evaluado en la jornada, se ejecuta el triaje canónico y se obtiene su `codigo` original.
  2. **Intercepción Pre-Dimensionamiento:**
     Si el `codigo` pertenece a la lista de exclusión $\implies$ se sobreescribe el estado de la posición a:
     - `codigo` = `"QBE-00"`
     - `nombre` = `"Veto Fiduciario Selectivo"`
     - `alpha` = $0.00$
  3. Al colapsar a `QBE-00`, el partido es automáticamente descartado por los filtros de la cartera antes de ingresar al ordenamiento lexicográfico (`[LN-QBE-081]`) y la asignación monótona (`[LN-QBE-082]`).
  4. El capital que habría sido consumido por estas estrategias se reasigna a las estrategias de alta convicción (`H1`, `H2`) o se preserva en efectivo si no hay más oportunidades viables en la fecha.
* **O (Output):** Cartera depurada de las estrategias excluidas y nuevo PnL acumulado.
* **Φ (Transición):** Hacia `scripts/laboratorio/sandbox_rentabilidad_pipeline.py`.
* **[SHIELD]:** `tests/shield/test_shield_sandbox_rentabilidad_pipeline.py`

### ID: [LN-QBE-114] Orquestación REST para Simulación Financiera Retrospectiva

* **Ω (Resumen):** Expone las capacidades del motor de liquidación factual (`[LN-QBE-107]`) mediante una API REST para la parametrización dinámica desde la interfaz cliente. Permite inyectar vectores de configuración (bankroll base, umbrales de certeza, modo de cobertura y listas de exclusión fiduciaria) para recalcular la trayectoria de capital en tiempo real.
* **I (Input):** Payload `SimulatePortfolioRequest`: `bankroll_inicial` (float), `rango_jornadas` (str), `modo_interes` (plano/compuesto), `excluir_estrategias` (List[str]).
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. El endpoint recibe el payload y delega la ejecución íntegramente a `ejecutar_simulacion_rentabilidad` del `sandbox_rentabilidad_pipeline.py`.
  2. Queda estrictamente prohibido que la capa web reimplemente cálculos de PnL, Drawdown o sumatorias de capital. El controlador opera exclusivamente como un pasarela (Pass-through) hacia el motor matemático.
* **O (Output):** Estructura JSON con la curva de capital, métricas de riesgo y detalle meso por jornada.
* **Φ (Transición):** Hacia `src/web/routes/markets.py` y el renderizador frontend en `app.js`.
* **[SHIELD]:** `tests/shield/test_shield_backtesting_simulation_rest.py`

### ID: [LN-QBE-115] Saneamiento Vol. II: Cota Underdog Ley 3, Escudo de Altitud y Trinidad de Certeza

* **Ω (Resumen):** Sanea el sangrado estructural del fondo certificado en la auditoría retrospectiva de la línea base (`[LN-QBE-107]`: ROI −16.84% sobre 30 posiciones; `QBE-R2` −$6,755.30 y `QBE-H2` −$3,255.38). Introduce tres blindajes: (i) **Cota Underdog Ley 3** — toda orden de la Familia R (`QBE-R1`/`QBE-R2`) queda acotada al **1.5% del capital de la jornada**; (ii) **Escudo de Altitud** — un diferencial de altitud fisiológica $\Delta\text{Alt}^+ \ge 1000$ m veta la Híbrida Visitante (`QBE-H2`); (iii) **Trinidad de Certeza §5.10** — el Slider de Certeza opera como filtro ACTIVO de admisión de cartera.
* **I (Input):** `payload` del triaje (`p_local`, `p_empate`, `p_visitante`, `es_operable`, `delta_epist`, `delta_alt_metros`), `cuotas` (`L`, `E`, `V`, `pa`, `DNB`, `Under_25`), `gamma` ($\Gamma$ de Capa 0), `target_certeza_pct` y `modo_cobertura` ($\delta \in \{\text{DEF}, \text{BAL}, \text{AGR}\}$).
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Cota Underdog Ley 3 (`portfolio_math.asignar_capital_monotono_cartera`):** tras la asignación monótona y ANTES del prorrateo global, el tamaño de toda orden cuya familia pertenezca a `FAMILIAS_UNDERDOG_LEY3 = ("QBE-R1", "QBE-R2")` se acota a $\text{Cap}_{\text{underdog}} = 0.0150 \cdot B_j$ (`CAP_UNDERDOG_LEY3_PCT`). La cota es **techo, jamás piso**: no rescata una orden sub-dimensionada ni infla la bolsa del 25%.
  2. **Escudo de Altitud (`triaje_determinista_9_estrategias`, rama `ASIMETRIA_VISITANTE`):** por **precedencia estructural**, ANTES de exigir $\alpha_V > 0$, si $\Delta\text{Alt}^+ \ge 1000.0$ m (`UMBRAL_VETO_ALTITUD_METROS`) y $O_X > \theta_2^*$ $\implies$ veto fiduciario inmediato hacia `QBE-00` con `motivo = "Veto Fiduciario: Trampa de Altitud Visitante (Delta Alt >= 1000m)"` y `arquetipo_veto = "TRAMPA_ALTITUD"`. El diferencial es unidireccional ($\Delta\text{Alt}^+ = \max(0, \text{alt}_{\text{local}} - \text{alt}_{\text{visita}})$, `[LN-QBE-109]`) y se deriva del catálogo inmutable `CATALOGO_ALTITUDES_LIGAMX`. Sin evidencia de altitud (club fuera de catálogo) el diferencial vale `0.0`: el escudo NO se evalúa y jamás se fabrica un veto.
  3. **Trinidad de Certeza (§5.10) — filtro de admisión:** antes del dimensionamiento, `target_certeza_pct` restringe las familias admitidas: $\ge 90.0$ (Modo Conservador) veta `QBE-D1`, `QBE-D2`, `QBE-R1` y `QBE-R2` (cartera 100% Híbridas con cobertura); $80.0 \le c < 90.0$ (Modo Balanceado) veta `QBE-R1`, `QBE-R2` y `QBE-D2`; $c < 80.0$ (Modo Crecimiento) admite la cartera plena con el nuevo tope del $1.5\%$. El modo resuelto y las familias vetadas se declaran en el reporte.
  4. **Cobertura dinámica $\delta$:** el simulador particiona con `calcular_particion_dutching_dinamico` (`[LN-QBE-077-B/C/D]`); `DEF` reproduce exactamente la ley V=0 (`[LN-QBE-070]`), `BAL` aplica $\delta = 0.50\,\delta^*$ y `AGR` $\delta = \delta^*$, siempre bajo el clamping fiduciario $\min(\delta, 0.95\,\delta_{\max})$.
  5. **$\Delta_{\text{epist}}$ fáctico con guarda de dominio:** el simulador lee `sovereign_distributions.epistemic_delta`; si $0.0 \le \Delta \le 1.0$ usa el valor fáctico real y en cualquier otro caso (legado no normalizado o ausente) aplica el fallback legislado `0.02` de `[LN-QBE-070-C]`. La fuente efectiva se declara en `nota_paridad`.
  6. **Instrumento de medición, no de optimización:** el simulador NO recalibra $\Gamma$, la certeza ni $\delta$; sólo los transporta y los aplica. Cero mutación de la bóveda 3NF.
* **O (Output):** triaje calificado (`QBE-00` + `arquetipo_veto`), cartera con `inversion_total` acotada, y reporte con `resumen_estrategias` (posiciones, inversión, PnL y ROI por código estratégico) y `parametros_simulacion` ($\Gamma$, banda de certeza, modo $\delta$, fuente de $\Delta$).
* **Φ (Transición):** Hacia `src/core/contracts/portfolio_math.py` (y su espejo `docs/DIRGEN_VAULT.md`), `scripts/laboratorio/sandbox_rentabilidad_pipeline.py`, `src/models/web_schemas.py` y `src/web/routes/markets.py`.
* **[SHIELD]:** `tests/shield/test_shield_saneamiento_estrategias_vol2.py`

---

### ID: [LN-QBE-116] Cota de Dominancia P′ ≥ 50% en la Híbrida Visitante (Blindaje H2)

* **Ω (Resumen):** La Híbrida Visitante (`QBE-H2`) promete dominancia foránea con el empate asegurado en tablas. Si el propio vector $P'$ del modelo **no concede mayoría al visitante** ($p_2 < 50.0\%$), la promesa es fiduciariamente falsa: la masa dominante de la asimetría es el empate y el boleto atacante descansa sobre un favorito inexistente. La auditoría retrospectiva de la línea base certificó el sangrado de esta clase de posición (`QBE-H2` −$867.29 en `LIGAMX-J10-01`, Atlante vs Rayados, $p_2 = 0.4975$). El sprint sella una **cota de dominancia**: por debajo del $50.0\%$ de $p_2$, la ruta `QBE-H2` colapsa a `QBE-00` con arquetipo declarado.
* **I (Input):** `payload` del triaje (`p_local`, `p_empate`, `p_visitante`, `es_operable`, `delta_epist`, `delta_alt_metros`), `cuotas` (`L`, `E`, `V`, `pa`, `DNB`, `Under_25`) y `gamma` ($\Gamma$ de Capa 0).
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Punto de intercepción exacto:** la cota opera **dentro** del predicado de emisión de la Híbrida Visitante (`familia == "ASIMETRIA_VISITANTE" and O_X > θ_2^* and α_V > 0`), es decir, **únicamente sobre la ruta `QBE-H2`**. No toca la Familia R, ni `QBE-C1`, ni `QBE-C2`, ni las Directas: una fila que no iba a emitir `QBE-H2` conserva su cascada íntegra (alcance quirúrgico, Opción A del dictamen `SPRINT-H2-DOMINANCE-ATLANTE-MESO-UI-17`).
  2. **Regla:** si $p_2 < 0.5000$ (`UMBRAL_DOMINANCIA_VISITANTE_PCT`) $\implies$ `QBE-00` con `nombre = "Veto Fiduciario: Ruptura de Dominancia Visitante"`, `motivo = "Veto Fiduciario: Dominancia Visitante (P_visitante < 50%)"`, `arquetipo_veto = "RUPTURA_DOMINANCIA"`, $\alpha = 0.0$ y $pa = \text{False}$.
  3. **Borde exacto:** la comparación es **estricta** ($<$). Con $p_2 = 0.5000$ la Híbrida Visitante **subsiste**: la cota es un piso de dominancia, no una exclusión del $50\%$.
  4. **Precedencia estructural de la altitud:** el Escudo de Altitud `[LN-QBE-115]` se evalúa **antes**. Si $\Delta\text{Alt}^+ \ge 1000$ m y $O_X > θ_2^*$, el veredicto conserva `motivo` y `arquetipo_veto = "TRAMPA_ALTITUD"` (la trampa fisiológica certificada es el hecho dominante). La cota de dominancia sólo califica las filas que superaron el escudo.
  5. **Hecho de altitud catalogado (Atlante):** se incorpora `"atlante": 2240.0` (y su forma compuesta `"club-atlante"`) al catálogo inmutable `CATALOGO_ALTITUDES_LIGAMX` de `[LN-QBE-109]`. Es un **hecho declarado**, no una estimación: el Estadio Azulgrana / Neutro de la Ciudad de México opera a 2,240 msnm. Con ello $\Delta\text{Alt}^+(\text{atlante}, \text{rayados-de-monterrey}) = 1700$ m y el escudo neutraliza `LIGAMX-J10-01`.
  6. **Instrumento de medición, no de optimización:** cero recalibración de $\Gamma$, de la certeza o de $\delta$; cero mutación de la bóveda 3NF.
* **O (Output):** triaje calificado (`QBE-00` + `arquetipo_veto = "RUPTURA_DOMINANCIA"`) y, sobre el corpus real J1–J11 (`modo="compuesto"`, bankroll $10,000.00$): ROI AGR $+8.41\%$, PnL $+$841.11 MXN, 18 posiciones operables, drawdown máximo $0.04\%$ (dictamen del Bucle Reflexivo).
* **O (Output) — Enmienda `[VAR-2026-SPRINT3-ROI-AGR]` (RESUELTO, 2026-10-23):** el baseline anterior ($+8.41\%$ / $+$841.11 MXN / 18 posiciones / drawdown $0.04\%$) queda **archivado como evidencia del corpus con cold start artificial**, no como umbral. El criterio de aceptación **vigente** se re-cimenta sobre la física informada de Apertura 2025 (`[LN-QBE-128]` / `[ARCH-1.4.69]`): **ROI AGR $\ge +5.0\%$, PnL $\ge +$500.00 MXN, drawdown máximo $\le 2.0\%$ y $\ge 11$ jornadas liquidadas sobre J1–J11** (medición viva: $+5.85\%$, $+$584.59 MXN, $1.50\%$, 11 jornadas; 4 posiciones operables informativas). El piso de dominancia $0.5000$ (`UMBRAL_DOMINANCIA_VISITANTE_PCT`) y el Escudo de Altitud **no se tocaron**. Dictamen en `docs/DIRGEN_VARIANCE_REQUEST_SPRINT3_ROI_AGR.md` §7.
* **Φ (Transición):** Hacia `src/core/contracts/portfolio_math.py` (y su espejo atómico `docs/DIRGEN_VAULT.md` → `[VAULT-CORE-070-TRIAJE]`), `scripts/laboratorio/sandbox_contexto_shocks_pipeline.py` (catálogo `[LN-QBE-109]`) y la capa de presentación `src/web/static/js/app.js` + `src/web/static/css/theme.css` (conforme `[ARCH-1.4.54]`).
* **[SHIELD]:** `tests/shield/test_shield_h2_dominance_and_atlante_altitude.py`

---

### ID: [LN-QBE-117] Proveedores Canónicos de Insumos Factuales (Fase 1 · Integración Maestra)

* **Ω (Resumen):** La matemática validada en los cuatro sandboxes de laboratorio (`[LN-QBE-108]` Ataque/Defensa, `[LN-QBE-109]` Contexto & Shocks, `[LN-QBE-110]` Trayectoria & Momento, `[LN-QBE-111]` Volumen & Portería) deja de vivir en scripts de consola y se materializa como **proveedores modulares puros** bajo `src/core/sovereign/`. Cada proveedor publica su bloque dentro de un paquete **anidado** `insumos_factivados` (`h2h`, `contexto`, `trayectoria`, `volumen_porteria`, `ataque_defensa`) que `[LN-QBE-101]` consume de forma **aditiva**: las claves planas heredadas conservan su nombre y significado byte a byte (cero ruptura del DTO ni del catálogo de 44 variables).
* **I (Input):** `sesion` de sólo lectura sobre la bóveda 3NF (`matches`, `match_telemetry`, `standings_snapshots`) leída por la **aduana canónica** `src/core/sovereign_reads.py`, que entrega **diccionarios planos** (`[ARCH-1.4.55-B]`): la capa pura jamás importa `sqlalchemy` ni `src.storage` (`[ARCH-1.4.26]`). Además `match_id`, `temporada` y los shocks declarados `q_mod_h` / `q_mod_a`.
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Herencia matemática VERBATIM:** los cuatro proveedores **transcriben sin una sola coma de diferencia** las fórmulas selladas de sus sandboxes de origen —`ΔAlt⁺ = max(0, Alt_local − Alt_visita)`, `γ_contextual = γ̄_base + Δγ_plaza + 0.0300·ΔAlt⁺/1000 + 0.0200·clamp(ΔDías, ±3)`, `m = Σ(t−t̄)(y_t−ȳ)/Σ(t−t̄)²` con denominador exacto `10.0` para n = 5, `Save% = 100·(SoTA − GC)/SoTA` saturado en `[0, 100]`, `v_Vol⊥ = FCF − 1.0` y la colisión cruzada `A_H − D_A` / `A_A − D_H`. Cero reimplementación de λ: se invocan `estimar_intensidades_loglineal`, `calcular_alpha_ligadura` y `obtener_bono_fortaleza_plaza` de `[VAULT-CORE-001]` / `[LN-QBE-038]`, y `derivar_factores_estructurales` de `[VAULT-CORE-005]`.
  2. **Corte futuro-ciego N−1:** todo proveedor lee exclusivamente `matchday_num < N ∧ estado ∈ {FINALIZADO, FINISHED}`. El fixture evaluado jamás alimenta su propio corte.
  3. **Cobertura íntegra obligatoria:** una tasa bilateral sólo se publica si TODOS los partidos del corte traen la métrica. Una sola ausencia ⇒ `None` + estado `SIN EVIDENCIA` (cero imputación, cero defaults de esquema).
  4. **Degradación honesta J1–J4:** con menos de `VENTANA_TRAYECTORIA = 5` partidos terminales en el corte, V29/V30/V31 se declaran `SIN EVIDENCIA`; jamás se rellena la ventana con datos sintéticos ni se extrapola una pendiente.
  5. **Altitud catalogada:** `CATALOGO_ALTITUDES_LIGAMX` es un hecho declarado, no una estimación; incluye `"atlante": 2240.0` (Estadio Azulgrana / Neutro de la Ciudad de México, `[LN-QBE-116]`). Slug no catalogado ⇒ `None` (jamás "nivel del mar").
  6. **Empaquetado aditivo:** `empaquetar_insumos_factivados` publica el paquete **anidado** y **propaga** además las claves planas heredadas en la raíz, de modo que `_insumos_factivados` de `[LN-QBE-101]` sigue iluminando el catálogo sin cambios de contrato. Un paquete **sólo anidado** (sin claves planas) se aplana por la tabla declarativa `_MAPA_NIDOS_A_PLANO`.
  7. **Backup atómico previo al lote:** `PersistenceGateway.crear_backup_boveda_sqlite()` materializa una copia consistente de la bóveda vía `sqlite3.Connection.backup` (API online de SQLite, segura en WAL) en `data/backups/qbe_database_backup_{YYYYMMDD_HHMMSS}.db`, verificada con `PRAGMA quick_check`. Se invoca explícitamente al inicio del lote, jamás por escritura.
* **O (Output):** cuatro bloques con `status` (`EXITO` / `PARCIAL` / `SIN_EVIDENCIA`), sus celdas V-coded (`V01, V05, V06, V10, V11, V16, V27, V28, V29-V32`), sus `insumos` planos y el paquete anidado consumible por la consola forense.
* **Φ (Transición):** Hacia `src/core/sovereign_reads.py` (aduana de lectura ORM → dicts), `src/core/sovereign/context_provider.py`, `src/core/sovereign/trajectory_provider.py`, `src/core/sovereign/telemetry_provider.py`, `src/core/sovereign/attack_defense_core.py`, `src/core/sovereign/factor_attribution.py` y `src/storage/gateway.py`.
* **[SHIELD]:** `tests/shield/test_shield_fase1_master_integration_providers.py`

---

### ID: [LN-QBE-118] Materialización Anidada de los Cinco Pilares y Resguardo WORM Previo a la DML (Fase 2 · Re-homologación)

* **Ω (Resumen):** El contrato anidado `insumos_factivados` fue legislado en `[LN-QBE-117]` y su aplanador (`_MAPA_NIDOS_A_PLANO`) quedó sellado en `[ARCH-1.4.55]`, pero **nadie lo materializaba**: la sonda fáctica sobre `sovereign_distributions` (J1–J11, 99 filas) certificó **0 bloques anidados** en las 99 trazas — el generador sellado seguía publicando sólo las 21 claves planas. La Fase 2 cierra la brecha por la vía **no invasiva**: el generador anida los cinco pilares como **proyección pura** de las magnitudes que ya consumió (cero matemática nueva) y la homologación de temporada le entrega la **evidencia contextual y de volumen REAL** (altitud catalogada, descanso reconstruido, SoT/SoTA y posesión) en lugar de los ceros por ausencia. El lote se blinda además con el **Resguardo WORM** obligatorio ANTES de la primera DML.
* **I (Input):** `raw_match_data` (el vector homólogo de 7 campos más los hechos contextuales publicados por `[LN-QBE-117]`), el paquete plano de 21 claves de `[LN-QBE-102]` y los parámetros contextuales efectivos `delta_alt_metros`, `delta_descanso_dias`, `q_mod_h`, `q_mod_a` que λ ya consumía.
* **P (Process) [ALGO-PROTECTED] [DIRGEN-STRICT]:**
  1. **Cero matemática nueva (proyección, no cálculo):** los cinco sub-bloques se derivan **exclusivamente** de las magnitudes planas ya consumidas y de los hechos contextuales del registro. `derivar_factores_con_procedencia`, `estimar_intensidades_loglineal`, Dixon-Coles, el operador de André y la fusión `[LN-QBE-104]` permanecen **bit-idénticos**: con los mismos argumentos se reproducen exactamente los mismos $\lambda_h, \lambda_a$ (verificado por el Juez 1 del `[SHIELD]`).
  2. **Shape `[LN-QBE-117]`:** cada sub-bloque se publica como `{"bloque": <nombre>, "status": <estado>, "insumos": {...}}` bajo las cinco claves legisladas `h2h`, `contexto`, `trayectoria`, `volumen_porteria`, `ataque_defensa`.
  3. **Regla de cobertura del `status` (`EXITO` / `PARCIAL` / `SIN_EVIDENCIA`):** `EXITO` exige **todas** las magnitudes del bloque publicadas; `PARCIAL` al menos una; `SIN_EVIDENCIA` ninguna. Un `None` **jamás** se sustituye por un default: el estado declara la evidencia, no la fabrica.
  4. **Paridad plana ↔ nido:** toda clave del nido con espejo en `_MAPA_NIDOS_A_PLANO` transporta **el mismo valor** que la clave plana heredada (misma fuente, misma unidad); el aplanador de `[ARCH-1.4.55]` re-deriva el mismo número. El anidamiento es **aditivo**: las 21 claves planas conservan nombre, unidad y valor (cero ruptura del DTO `StochasticAuditTrace` ni del catálogo de 44 variables de `[LN-QBE-101]`).
  5. **Ley Zero-H2H declarada:** con `h2h_conteo = 0` el bloque `h2h` se publica `SIN_EVIDENCIA` con su `motivo` explícito; jamás un récord 0-0-0 inventado (`[LN-QBE-020-B]`).
  6. **Trayectoria honesta:** la captura de homologación no publica la serie de 5 partidos, de modo que los cuatro insumos del pilar (`pts_5p_local`, `pts_5p_visita`, `pendiente_local`, `pendiente_visita`) quedan en `None` con `SIN_EVIDENCIA`; el bloque **existe** (la ausencia es información veraz) y su ventana sintética queda prohibida.
  7. **Altitud y descanso REALES en el motor:** el vector homólogo publica $\Delta\text{Alt}^+ = \max(0, \text{Alt}_{local} - \text{Alt}_{visita})$ desde el catálogo inmutable `CATALOGO_ALTITUDES_LIGAMX` y el $\Delta\text{Días}$ del último partido terminal con `matchday_num < N` (futuro-ciego), calculados por el proveedor canónico `obtener_metricas_contexto` de `[LN-QBE-117]` — **cero fórmula duplicada**. El generador los adopta por su ruta legislada de contexto efectivo (`_contexto_efectivo`, `[LN-QBE-102]`): la matemática no cambia, cambia la evidencia que recibe. Esto **recertifica P′ de los 99 partidos** (autorizado por el Director): la altitud no es telemetría pasiva ($\Delta\text{Alt} = 1700$ m $\Rightarrow \approx +5.1\%$ en $\lambda_h$ según `intensity_canonical_loglink.py`, líneas 115–116).
  8. **Volumen & Portería con cobertura íntegra y fuente única:** `sot`/`sota` se acumulan (conteos) y `possession` se promedia sobre el corte **sólo si TODOS** los partidos cualificados traen la métrica y **un solo nivel de procedencia** la suministra; una sola ausencia $\Rightarrow$ las claves no se publican (cero mezcla de fuentes, cero imputación). Fuente: `match_telemetry` (`sot`, `sota`, `possession_pct`) — la caché congelada y el sensor sólo emiten xG/xGA, de modo que el orquestador construye el mapa `cache_volumen` y jamás completa un corte con otro nivel. **`[LN-QBE-119]` supersede la UNIDAD de `sot`/`sota`:** la acumulación de conteos se conserva como paso intermedio, pero lo PUBLICADO es la **tasa por partido** (`Σ/|corte|`), porque la casilla `V06`/`V11` rotula «por partido».
  9. **Resguardo WORM previo a la DML:** `PersistenceGateway.crear_backup_boveda_sqlite()` se invoca **una sola vez por lote y ANTES** de `sincronizar_distribuciones_soberanas_partidos` y del `write_transaction` del sellado de captura; la ruta verificada (`PRAGMA quick_check`) se publica en `parte["resguardo_worm"]` y se anuncia con el marcador `🛡️ [RESGUARDO WORM]`. `--dry-run` no respalda (no muta).
* **O (Output):** 99/99 trazas con los cinco bloques anidados, paridad plana/nido exacta, `contexto.delta_alt_metros` igual a la altitud catalogada del duelo y P′ recertificada sobre J1–J11 (`procesados=99 exitosos=99 errores=0`) con respaldo previo materializado en `data/backups/`.
* **Φ (Transición):** Hacia `src/core/sovereign_pipeline.py` (generador sellado) y su espejo atómico `docs/DIRGEN_VAULT.md` → `[VAULT-CORE-005]` (adenda `[LN-QBE-118]`), `scripts/ingesta/homologar_temporada_optah2h.py` (Pilares 1–4 de suministro fáctico) y los consumidores de sólo lectura `src/web/routes/admin_status.py` + `src/web/routes/markets.py`.
* **[SHIELD]:** `tests/shield/test_shield_fase2_rehomologacion_and_audit_trace.py`

### ID: [LN-QBE-119] Ley de Unidad de Volumen & Portería (Tasa Por Partido) y Sonda de Completitud Fáctica del Visor 44V (Fase 3 · Sincronía J13)

* **Ω (Resumen):** La casilla `V06` (`𝒯_Rem`, «Tiros a puerta por partido») exhibía la **sumatoria** del corte: la homologación publicaba `sot`/`sota` acumulados y el Visor los rotulaba «por partido», multiplicando la magnitud por PJ (el SoT medio de J11 se exhibía en **47.722** tiros). En paralelo, el acordeón forense degradaba toda dimensión a `SIN EVALUAR` / `○ 0 de 0` porque el DTO `AtribucionDimensionOut` descartaba en silencio los tres contadores que el productor puro ya publicaba (`extra="ignore"`, causa raíz registrada en `[ARCH-1.4.58]`). Este nodo fija la **ley de unidad** (lo publicado en una casilla «por partido» es una TASA, jamás una sumatoria) y materializa la **sonda forense de sólo lectura** que certifica, jornada por jornada, cero `0 de 0`, cotas físicas y sincronía Visor ↔ bóveda.
* **I (Input):** `cualificados` (corte futuro-ciego N−1 del club con `match_id` y `es_local`) y `cache_volumen` (`sot`, `sota`, `possession`, `procedencia` por `match_telemetry`); y, para la sonda, la salida **ya validada** por `CalibrationReportResponse` del endpoint `GET /api/markets/backtesting/calibration-report` más el universo factual de `matches` (marcador consumado + estado concluido).
* **P (Process) [DBBD-FUNGIBLE] (suministro fáctico, cero matemática nueva):**
  1. **Ley de unidad (`_volumen_porteria_corte`):** `sot = round(Σ sot / |corte|, 3)`, `sota = round(Σ sota / |corte|, 3)`, `possession = round(Σ possession / |corte|, 3)`. La acumulación sigue siendo el paso intermedio; se prohíbe publicar la sumatoria en una casilla rotulada «por partido». `possession` ya era media y conserva su valor exacto (regresión cero).
  2. **Cobertura íntegra intacta (`[LN-QBE-118]`):** una sola ausencia de `sot`/`sota`/`possession` o más de un nivel de `procedencia` $\Rightarrow$ las tres claves no se publican. Este nodo NO relaja la ley de procedencia: sólo corrige la unidad.
  3. **Efecto certificado (re-sellado forzado J1–J13):** el SoT medio por casilla pasa de `[17 … 56]` a `[4.611 … 5.444]`; la sumatoria deja de rebasar la cota física de **15.0** que la propia sonda vigila.
  4. **Sonda de completitud (`scripts/auditoria/auditar_completitud_visor.py`):** sólo lectura (`PersistenceGateway.read_session()`, cero `write_transaction`), barrido J1→J17 sobre el DTO validado. Seis familias de anomalía: `DENOMINADOR_NULO` (`total_variables <= 0`), `EVALUADAS_EXCEDE_TOTAL`, `CONTEO_DIVERGENTE` (alias `conteo` ≠ `total_variables`), `BADGE_INCOHERENTE` (`tiene_datos` ⟺ `variables_evaluadas > 0`), `COTA_SOT` (`V06`/`V11` fuera de `[0, 15.0]`), `COTA_POSS` (`V01` fuera de `[0, 100]`), `CATALOGO_INCOMPLETO` (Σ ≠ 44), `SIN_CATALOGO_44V`, `SINCRONIA_JORNADA` (jornada con partidos consumados que el Visor no publica) y `UNIVERSO_MERMA` (`auditados + pendientes ≠ concluidos_boveda`). Salida: tabla ASCII + parte JSON en `data/output/auditoria_completitud_visor.json`, `EXIT 0/1`.
  5. **Ausencia honesta (Ley Zero-H2H de la jornada sin evidencia):** una jornada del rango sin marcadores consumados se rotula 🟡 `JORNADA_SIN_EVIDENCIA`; jamás se reproyecta una distribución ni se inventa un marcador para completar la cartelera.
  6. **Sincronía de jornadas:** `_construir_reporte_calibracion` no porta techo de jornada (el Visor publica toda jornada concluida con P′ sellada); el literal `"1-11"` que sobrevive en `web_schemas.py` es el **default del simulador financiero** (V-5, ley distinta) y permanece intacto.
* **O (Output):** 97/97 casillas micro de J1–J11 con cotas físicas cumplidas; sonda en `🟡` con **0 anomalías rojas** y `EXIT 0` (6 ámbar declarativas: J12–J17 sin marcadores en la bóveda); `jornadas_faltantes_sync = []` y `auditados(97) + pendientes(0) == concluidos_boveda(97)`.
* **Φ (Transición):** Hacia `scripts/ingesta/homologar_temporada_optah2h.py` (`[DBBD-FUNGIBLE]`), la sonda nueva, el Centro de Control (`[ARCH-1.4.58]`, 19.ª tarea) y el espejo `docs/DIRGEN_VAULT.md` → `[VAULT-CORE-005]` (adenda `[LN-QBE-119]`).
* **[SHIELD]:** `tests/shield/test_shield_completitud_visor_and_sync_j13.py` · `tests/shield/test_shield_fase2_rehomologacion_and_audit_trace.py`

---


### ID: [LN-QBE-120] Catálogo Estructural de 32 Variables PRE-KICKOFF (Reingeniería Macro) y Derogación de la Partición 12×44

* **Ω (Resumen):** La partición de **12 dimensiones × 44 variables** de `[LN-QBE-101]` se **deroga** (decreto `VAR-3`) porque su granularidad de minuto a minuto (1T/2T, 0-15', 80-90'), de banca y de rotación del XI no gobierna la decisión PRE-KICKOFF y diluía la señal directora en ruido de baja frecuencia. El catálogo vigente es **6 dimensiones × 32 variables** estrictamente correlativas (`V01`…`V32`), con los mismos espacios de Hilbert (`H_att` / `H_def` / `H_ctx`) y **la misma semántica por magnitud**: la reingeniería **renumera**, no reinterpreta. Cero matemática nueva: `derivar_factores_con_procedencia`, la loglineal de Poisson, Dixon-Coles, la fusión `[LN-QBE-104]` y el operador de André quedan **bit-idénticos**.
* **I (Input):** El paquete `insumos_factivados` (`[LN-QBE-102]`/`[LN-QBE-117]`), el bloque `h2h_stats` (`[LN-QBE-105]`) y los hechos contextuales `delta_alt_metros` / `delta_descanso_dias` que λ ya consumía.
* **P (Process) [DBBD-FUNGIBLE] (renumeración declarativa, cero matemática nueva):**
  1. **Partición canónica (`DIMENSIONES_CANONICAS`, 6 renglones / 32 variables, cero duplicados):** `𝒯_Vol` Volumen Territorial y Fricción (5: V01-V05), `𝒯_Rem` Calidad de Remate (6: V06-V11), `𝒯_Def` Resistencia Defensiva (5: V12-V16), `𝒯_Por` Rendimiento de Portería (4: V17-V20), `𝒯_Spc` Balón Parado y Disciplina (5: V21-V25) y `𝒯_Ctx` Memoria, Forma y Contexto (7: V26-V32). `CATALOGO_VERSION = "32V-2026"`.
  2. **Mapa de renumeración (`VAR-3`, magnitud → celda, sin cambio de semántica):** xG/PJ `V05→V06`; SoT/PJ `V06→V07`; xGA/PJ `V10→V12`; SoTA/PJ `V11→V13`; ΔDescanso `V27→V30`; ΔAltitud `V28→V29`; memoria longitudinal `V39→V26` (récord), `V40→V27` (ΔG) y `V41→V28` (sede). Las métricas de cronometría, banca, rotación y cierre (`V33-V38`, `V43-V44` de `[LN-QBE-101]`) se **excluyen** del catálogo base y se delegan a un proyecto periférico de inferencia causal.
  3. **Cero ruptura de contrato (alias conservados):** el productor sigue llamándose `estructurar_catalogo_44_variables`, la clave de payload sigue siendo `variables_44` y el DTO sigue siendo `Catalogo44Out`; sólo cambia su **cardinalidad** (`total_variables: 32`, `_CATALOGO_32` como alias semántico de lectura). La UI (`app.js::_cardDimension44` / `_badgeDimension44`) se auto-sana: lee `n/m` del propio DTO, sin una línea de JS editada.
  4. **Tablas de transcripción realineadas:** `_FORMATO_INSUMO` (V01, V06, V07, V12, V13, V26, V29, V30), `_RESPALDO_INSUMO` (respaldo GC/PJ del Axioma 4 ahora en `V12`) y `_CLAVES_H2H_STATS` (V26/V27/V28) apuntan a las nuevas celdas sin cambiar la magnitud ni el formato (`pct`, `num0`, `num2`, `partidos`, `metros`, `dias`).
  5. **Sonda de completitud realineada (`[LN-QBE-119]`):** `TOTAL_VARIABLES_CATALOGO = 32` (el `CATALOGO_INCOMPLETO` compara Σ ≠ 32) y la cota física `COTA_SOT` vigila `V07`/`V13` (SoT/SoTA por partido), ya no `V06`/`V11`.
* **O (Output):** `estructurar_catalogo_44_variables({})` publica `total_variables = 32` y `6` dimensiones con denominador real (5/6/5/4/5/7); con el paquete de Fase 1 enciende exactamente `V01, V06, V07, V12, V13, V26, V27, V28, V29, V30` y ninguna otra celda.
* **Φ (Transición):** Hacia `src/models/web_schemas.py` (`Catalogo44Out`), `scripts/auditoria/auditar_completitud_visor.py`, el extractor macro `[ARCH-1.4.59]` (cuyo `MAPA_LEADERBOARDS` referencia los `V01`…`V32` vigentes) y el espejo `docs/DIRGEN_VAULT.md`.
* **[SHIELD]:** `tests/shield/test_shield_factor_attribution_and_telemetry.py` · `tests/shield/test_shield_fase1_master_integration_providers.py` · `tests/shield/test_shield_h2h_dimension_population.py` · `tests/shield/test_shield_live_lock_and_input_telemetry.py` · `tests/shield/test_shield_opta_flag_and_accordion_telemetry.py` · `tests/shield/test_shield_completitud_visor_and_sync_j13.py` · `tests/shield/test_shield_macro_extraction_phase_a.py`

---

### ID: [LN-QBE-121] Aduana de Exhibición Macro-Torneal: Iluminación Fáctica de las Celdas No Insumidas y Purga Nominal 44V

* **Ω (Resumen):** El artefacto congelado `data/cache_macro_stats_liga_mx_2026.json` (`[ARCH-1.4.59]`) se **conecta** al orquestador soberano como **Aduana de Exhibición**, no como insumo del motor. La ley separa dos regímenes irreconciliables: la **verdad torneal** (agregado de temporada completa, publicada por el proveedor) y el **corte N−1 futuro-ciego** (`[LN-QBE-020-B]`) que λ consume. Mezclarlos inyectaría futuro en el pasado. Por eso el bloque `macro_stats` **enciende** las celdas del catálogo de 32 variables (`[LN-QBE-120]`) que hoy están apagadas y **jamás** sustituye una magnitud que alimente λ: `V01`, `V06`, `V07`, `V12` y `V13` conservan el corte certificado **byte a byte**. Cero alteración de λ, de Δ_epist, de Dixon-Coles, del operador de André ni de la fusión `[LN-QBE-104]`: la distribución histórica $P'$ de los 117 partidos re-homologados queda **bit-idéntica** (Opción A ratificada por la Tríada, `VAR-2026-FASEB-C3`).
* **I (Input):** El artefacto congelado (`esquema: macro_stats_v1`, `catalogo_version: 32V-2026`, 18 clubes, 25 magnitudes publicadas) resuelto **por slug** en el orquestador de ingesta; el paquete `insumos_factivados` (`[LN-QBE-102]`/`[LN-QBE-117]`/`[LN-QBE-118]`) y las tablas de transcripción de `factor_attribution`.
* **P (Process) [DBBD-FUNGIBLE] (transcripción declarativa, cero matemática nueva):**
  1. **Firma aditiva (C4 ratificado):** `generar_distribucion_soberana(..., xg_es_real_opta=None, cache_macro_stats: Optional[Dict[str, Any]] = None)` y `_empaquetar_insumos_factivados(..., cache_macro_stats=None)`. El parámetro se **anexa al final**: toda llamada posicional existente (servicios REST, puente de sincronía, pruebas) permanece válida sin edición.
  2. **Bloque anidado `macro_stats`:** cuando llega el artefacto resuelto, el paquete publica `{"procedencia": "MACRO_TORNEAL", "catalogo_version": "32V-2026", "local": {...}, "visita": {...}, "cotejo": {...}}`. La clave **no** entra en `_MAPA_NIDOS_A_PLANO` ni en `_FORMATO_INSUMO`: el contrato plano heredado queda intacto (`None` ⇒ paquete byte-idéntico al previo, Juez de identidad).
  3. **Tabla de transcripción `_CLAVES_MACRO_STATS`:** traduce 21 claves del artefacto a 19 celdas (`V02`, `V03`, `V04`, `V05`, `V08`, `V09`, `V10`, `V11`, `V14`, `V15`, `V17`, `V18`, `V19`, `V20`, `V21`, `V22`, `V23`, `V24`, `V25`). `V16` (Big Chances Concedidas) **no** se enciende: el proveedor no publica ese leaderboard (hueco declarado, cero imputación). Las cinco celdas insumidas (`V01`, `V06`, `V07`, `V12`, `V13`) se publican en `macro_stats.cotejo` como **control cruzado de exhibición** y siguen mandando el corte.
  4. **Precedencia legislada:** `h2h_stats` (`[LN-QBE-105]`) → `_FORMATO_INSUMO` (insumo consumido) → `_RESPALDO_INSUMO` (Axioma 4) → `_CLAVES_MACRO_STATS` (exhibición torneal). La macro **nunca** pisa una celda ya encendida por evidencia de corte: sólo rellena lo apagado.
  5. **Purga nominal 44V:** las taxonomías locales de los cinco proveedores (`_TAXONOMIA_DIM_1..4`, bloques `V25-V28` y `V29-V32` de contexto y trayectoria) se **derivan** de `_CATALOGO_32` por dimensión (`𝒯_Vol`, `𝒯_Rem`, `𝒯_Def`, `𝒯_Por`) y los identificadores legados `V39/V40/V41/V05/V10/V16/V27/V28` desaparecen del núcleo, de los sandboxes y de The Shield. Las magnitudes sin celda en el catálogo (`m_xG`, `m_xGA`, impacto de bajas) se publican como **auxiliares sin código** (`AUX_*`): visibles, auditables y jamás antinaturales al catálogo (C1/C2 ratificados). Se conserva el nombre `estructurar_catalogo_44_variables`, la clave `variables_44` y el DTO `Catalogo44Out` (alias vivos, `[LN-QBE-120] §3`).
* **O (Output):** Con el artefacto conectado, el catálogo enciende **24 de 32** celdas (19 nuevas + 5 de cotejo) y publica `V16` como único hueco de la dimensión `𝒯_Spc`/`𝒯_Def` por ausencia de fuente; sin artefacto (`cache_macro_stats=None`) el resultado es **byte-idéntico** al de `[LN-QBE-120]`. λ, `p_local/p_empate/p_visitante` y `discrepancia_epist` idénticas con y sin macro (Juez de invariancia).
* **Φ (Transición):** Hacia `scripts/ingesta/homologar_temporada_optah2h.py` (resolución nombre→slug, `_cargar_cache_macro`), `src/core/sovereign_pipeline.py` (firma y bloque), `src/core/sovereign/factor_attribution.py` (tabla de transcripción) y el espejo `docs/DIRGEN_VAULT.md` → `[VAULT-CORE-005]` (adenda `[LN-QBE-121]`).
* **[SHIELD]:** `tests/shield/test_shield_macro_consumption_phase_b.py` · `tests/shield/test_shield_factor_attribution_and_telemetry.py` · `tests/shield/test_shield_fase1_master_integration_providers.py` · `tests/shield/test_shield_live_lock_and_input_telemetry.py` · `tests/shield/test_shield_sandbox_h2h_pipeline.py` · `tests/shield/test_shield_sandbox_ataque_defensa_pipeline.py` · `tests/shield/test_shield_sandbox_contexto_shocks_pipeline.py` · `tests/shield/test_shield_sandbox_trayectoria_momento_pipeline.py` · `tests/shield/test_shield_sandbox_volumen_porteria_pipeline.py`

### ID: [LN-QBE-122] Purga Nominal ALT-B: Derivación Estructural de Taxonomías desde el Catálogo Único y Régimen de Auxiliares `AUX_*`

* **Ω (Resumen):** `[LN-QBE-121]` §P.5 ordenaba derivar las taxonomías locales de `_CATALOGO_32`, pero la derivación **no podía ser posicional** (cardinalidades divergentes) y una derivación ingenua colisionaba en unidad, semántica y saturación. La varianza `VAR-2026-10-21-FASE-B-PURGA-V` certificó el hecho y el Director ratificó la **Opción ALT-B**: la casilla del catálogo se reserva a la evidencia que la sostiene con su MISMA granularidad y toda magnitud sin casilla se publica como **auxiliar sin código** (`AUX_*`). Este nodo materializa el helper `derivar_taxonomia()`, purga los nueve artefactos del alcance y alinea la UI: el nombre y el orden forenses dejan de transcribirse a mano y pasan a **derivarse del catálogo único en import-time**.
* **I (Input):** `_CATALOGO_44` (32 celdas con `nombre`/`familia`/`modo`), las tablas locales `id → (unidad, nota)` de cada proveedor y la captura sellada (λ, P′, `S_epist`).
* **P (Process) [DBBD-FUNGIBLE] (renombre nominal; cero matemática nueva):**
  1. **Helper estructural (`factor_attribution`):** `PREFIJO_AUXILIAR = "AUX_"`, `es_identificador_auxiliar()`, `nombre_de_celda()` y `derivar_taxonomia(dimension, locales)`, que toma **nombre y posición del catálogo**, conserva del proveedor **unidad y nota**, anexa los `AUX_*` al final en el orden declarado y **rechaza en voz alta** (`ValueError`) un `VXX` que no pertenezca a la familia: la taxonomía local no puede inventar celdas ni robarle una a otra dimensión.
  2. **Tabla de remapeo materializada** (la MISMA que `_FORMATO_INSUMO` ya legislaba, `[LN-QBE-120]`): `V05→V06` (xG/PJ), `V06→V07` (SoT/PJ), `V10→V12` (xGA/PJ), `V11→V13` (SoTA/PJ), `V16→V18` (Save %), `V15→V17`/`V17→V19` (𝒯_Por), `V27→V30` (ΔDías), `V28→V29` (ΔAlt⁺), `V29→V31` (Forma 5P), `V39→V26`/`V40→V27`/`V41→V28` (𝒯_Ctx). La magnitud no cambia de valor: cambia de casilla cuando la casilla es suya.
  3. **Auxiliares sin código:** `AUX_XGOT_90`, `AUX_PPDA`, `AUX_PASES_PROG`, `AUX_ENTRADAS_UT`, `AUX_XG_BAJAS`, `AUX_XGA_BAJAS`, `AUX_Q_MOD_H`, `AUX_Q_MOD_A`, `AUX_M_XG`, `AUX_M_XGA`, `AUX_XG_HIST`. Ninguno porta un `VXX`: la usurpación nominal queda estructuralmente prohibida.
  4. **UI alineada (`[DBBD-FUNGIBLE]`):** las tarjetas del Hero Card leen las celdas canónicas (`V06` xG, `V12` xGA, `V18` atajadas, `V26/V27/V28` memoria H2H, `V30` descanso, `V29` altitud) y las rejillas de 𝒯_Vol/𝒯_Rem/𝒯_Def/𝒯_Por sólo citan ids del catálogo.
  5. **Cero cambio de magnitud:** los cortes, las tasas y las claves planas de `insumos_factivados` conservan nombre y valor; el catálogo enciende las MISMAS celdas y la macro sigue iluminando lo que el corte no puede sostener.
* **O (Output):** 9 artefactos purgados (≈130 referencias), **492 passed / 0 failed en 15.74 s** (`467 + 25` jueces nuevos), re-homologación `1-13 --forzar` con **117/117** partidos, `0` errores, paridad 3NF ↔ captura `idénticas=117` y resguardo WORM previo; catálogo con **22–29 celdas encendidas** por partido (la macro conserva su cotejo `V01/V06/V07/V12/V13`) y λ/P′ bit-idénticas. Pre-vuelo de cartelera: **0 discrepancias 🔴**.
* **Φ (Transición):** Hacia `src/core/sovereign/factor_attribution.py` (helper), los cuatro proveedores, los cinco sandboxes de `scripts/laboratorio/`, `src/web/static/js/app.js` y el espejo `docs/DIRGEN_VAULT.md` → `[VAULT-CORE-005]` (adenda `[LN-QBE-122]`).
* **Deuda declarada:** `scripts/laboratorio/sandbox_micro_dinamicas_pipeline.py` conserva las dimensiones 5/6/9/10/12 del régimen 44V **derogado** (`V18-V24`, `V33-V44`): esas dimensiones no existen en el catálogo de 32 y su realineación exige una varianza propia (fuera del alcance ratificado). `docs/DESIGN.md` conserva la nomenclatura histórica como registro forense de la etapa 44V.
* **[SHIELD]:** `tests/shield/test_shield_purga_nominal_alt_b.py` · `test_shield_fase1_master_integration_providers.py` · `test_shield_sandbox_h2h_pipeline.py` · `test_shield_sandbox_ataque_defensa_pipeline.py` · `test_shield_sandbox_contexto_shocks_pipeline.py` · `test_shield_sandbox_trayectoria_momento_pipeline.py` · `test_shield_sandbox_volumen_porteria_pipeline.py` · `test_shield_control_center_and_calibration_unblock.py`

### ID: [LN-QBE-123] Saneamiento de Trayectoria Fáctica, Cuarentena Declarada de V16 y Guardián de Presencia del Descanso (Régimen Opción B)

* **Ω (Resumen):** la varianza `VAR-2026-10-22-TRAYECTORIA-POSESION-V16` certificó tres patologías de la telemetría forense: (a) `V16` (Big Chances Concedidas) se exhibía como celda ACTIVA sin fuente que la sostenga; (b) `V31`/`V32` —forma 5P y varianza ΔxPTS— llegaban publicadas por `trajectory_provider` en `trayectoria.insumos` pero el catálogo no las transcribía, de modo que la trayectoria estaba medida y no exhibida; y (c) `V30` publicaba `+0.0 d` cuando el fixture no reconstruye fechas, convirtiendo la ignorancia en medición. El Director ratificó la **Opción B**: cuarentena declarada de `V16` **sin purgar el catálogo de 32** (el contrato `𝒯_Def` de `derivar_taxonomia` y ~40 Jueces dependen de la integridad del 32V), cableado de `V31`/`V32` y guardián de presencia del descanso.
* **I (Input):** `_CATALOGO_44` (32 celdas), el paquete `insumos_factivados` anidado (`trayectoria`, `contexto`), y las claves planas heredadas del homologador (`delta_descanso_dias`).
* **P (Process) [DIRGEN-STRICT] (transcripción pura; λ y P′ intactas):**
  1. **Cuarentena de V16 (sin purga).** `_CUARENTENA = {"V16": …}` y `ESTADO_FUERA_DE_FUENTE = "FUERA DE FUENTE"`. La fila del catálogo pasa a `modo="cuarentena"` con cero claves de extracción y el bucle de `estructurar_catalogo_44_variables` **corta antes** de la telemetría y de la ruta heredada: `local = visita = None`, `origen = FUERA DE FUENTE`, `estado = SIN EVIDENCIA`. La cuarentena es ESTRUCTURAL: ninguna clave heredada (`big_chances_conceded`) ni la macro torneal pueden encenderla por la espalda.
  2. **Cableado de la trayectoria (`_celda_trayectoria`).** `_CLAVES_TRAYECTORIA` mapea `V31 ← pts_last5_local/visita` (`num0`) y `V32 ← xpts_diff_local/visita` (`delta2`, formato CON signo). Se evalúa en `_celda_telemetria` **después** de `h2h_stats` y **antes** de la ruta heredada: una clave ausente o `None` apaga la celda (`None` ⇒ cae a la ruta byte-idéntica de `_FORMATO_INSUMO`, cero ruptura). Sólo la magnitud REALMENTE publicada se transcribe; la trayectoria es DIAGNÓSTICO y no entra en λ.
  3. **Guardián de presencia del descanso (`_presencia_refutada`).** `_PRESENCIA_CONTEXTO = {"V30": ("descanso_evaluado", "descanso_local", "descanso_visita")}`. Si el bloque `contexto` declara `descanso_evaluado = False` —o publica AMBAS fechas en `None`— la celda se apaga con nota honesta, **aunque** la clave plana traiga `0.0`: ese cero es el centinela de ausencia de `homologar_temporada_optah2h` (`or 0.0`), no una magnitud. `context_provider.py` publica ambas banderas (`descanso_evaluado`, `altitud_evaluada`) en `insumos`; el `0.0` que recibe el motor sellado sigue siendo ausencia de BONO, jamás telemetría.
  4. **Aritmética intocable:** cero edición de λ, P′, `estimar_intensidades_loglineal`, `calcular_alpha_ligadura`, Kelly o Poisson. El sprint es de TRANSCRIPCIÓN y PRESENCIA.
* **O (Output):** catálogo de **32 celdas** intacto; `V16` exhibida `FUERA DE FUENTE`/`SIN EVIDENCIA`; `V31`/`V32` encendidas `EVALUADO` cuando la trayectoria real existe y apagadas cuando no; `V30` sin `+0.0 d` fabricado. `499 passed / 0 failed` en **21.62 s** en frío y **19.75 s** en caliente.
* **Φ (Transición):** hacia `src/core/sovereign/factor_attribution.py` (`_celda_trayectoria`, `_presencia_refutada`, `_CUARENTENA`), `src/core/sovereign/context_provider.py` (banderas de presencia), la vitrina `src/web/static/js/app.js` + `theme.css` (`[ARCH-1.4.63]`) y el espejo `docs/DIRGEN_VAULT.md` → `[VAULT-CORE-005]` (adenda `[LN-QBE-123]`).
* **Deuda declarada:** la cuarentena de `V16` caduca si algún día se ingesta un corpus con leaderboard de big chances concedidas; hasta entonces la celda permanece declarada y vacía. El centinela `0.0` del homologador sigue existiendo en el artefacto persistido: neutralizarlo en origen exige varianza propia sobre `scripts/ingesta/homologar_temporada_optah2h.py` (fuera del alcance ratificado).
* **[SHIELD]:** `tests/shield/test_shield_saneamiento_trayectoria_ui_purga_v16.py` (nuevo, 4 jueces) · `test_shield_fase1_master_integration_providers.py` (realineado: `_EVALUADAS_FASE_1` incorpora `V31`/`V32`) · `test_shield_factor_attribution_and_telemetry.py` · `test_shield_fase3_polymorphic_cards_ui.py` · `test_shield_h2h_dimension_population.py` · `test_shield_fasec_visual_and_micro_dynamics.py`

### ID: [LN-QBE-124] Banda de Indiferencia Fiduciaria en la Cobertura Ordinal y Desempate por Altitud del Anfitrión

* **Ω (Resumen):** la varianza `VAR-2026-10-22-INDIFERENCIA-ALTITUD` certificó que la jerarquía de vértices `P_max ≥ P_mid ≥ P_low` trataba como separación epistémica lo que es ruido de régimen: en Atlante vs Rayados (J10, `LIGAMX-J10-01`) el trío soberano fue $P' = (0.2554,\,0.2601,\,0.4845)$ — una diferencia de **0.0047** entre el 2.º y el 3.er vértice, indistinguible de la discontinuidad Dixon-Coles en $\Sigma\lambda = 2.65$ — y sin embargo el orden aritmético sentenciaba `EMPATE` como cobertura secundaria, dejando fuera al anfitrión que jugaba con **1700 msnm** de desnivel. El Director ratificó la **Banda de Indiferencia Fiduciaria**: cuando la frontera $\{P_{siguiente}, P_{ultimo}\}$ es estadísticamente plana, la ventaja territorial extrema del LOCAL es el criterio fideicomisario que decide el orden — **sin tocar jamás $P_{max}$**.
* **I (Input):** el trío soberano $P' = (p_1, p_X, p_2)$ ya fusionado por `[LN-QBE-104]` y el desnivel unidireccional $\Delta Alt^{+} = \max(0,\; \text{altitud\_local} - \text{altitud\_visita})$ en metros, resuelto por la traza V29 realmente consumida por $\lambda$ (`insumos_factivados.contexto.insumos.delta_alt_metros`) y, en su defecto, por el catálogo inmutable de plazas (`altitud_estadio`).
* **P (Process) [DIRGEN-STRICT] (función pura; $\lambda$, $P'$ y la masa de cobertura intactas):**
  1. **Manifiesto declarado:** `BANDA_INDIFERENCIA_EPSILON = 0.0100` ($\varepsilon_{indif} = 1.00\%$) y `UMBRAL_ALTITUD_RESCATE_METROS = 1000.0`. Se declaran como constantes PROPIAS: **prohibido mutar** `UMBRAL_VETO_ALTITUD_METROS` de `[LN-QBE-115]`, que rige otro predicado (el Escudo de Altitud del triaje) y conserva su valor y su semántica byte-idénticos.
  2. **Orden aritmético base:** `sorted` descendente y **estable** sobre `[(LOCAL, p_1), (EMPATE, p_X), (VISITANTE, p_2)]` ⇒ la igualdad exacta se resuelve por el orden canónico $1 \cdot X \cdot 2$; cero desempate inventado.
  3. **Rescate territorial (las tres condiciones son conjuntivas):** (a) $|P_{mid} - P_{low}| \le \varepsilon_{indif}$; (b) el par en disputa es **exactamente** $\{LOCAL, EMPATE\}$; (c) $\Delta Alt^{+} \ge 1000.0$ msnm. Verificadas las tres, el LOCAL se promueve a $P_{mid}$ y el EMPATE desciende a $P_{low}$. **La promoción es una PERMUTACIÓN de posición, no una reescritura de magnitud**: los valores servidos siguen siendo los del símplex sellado.
  4. **Invarianzas duras:** $P_{max}$ y su etiqueta **nunca** cambian; la masa de cobertura $P_{max} + P_{mid}$ es **invariante** bajo la permutación ($\equiv 1 - P_{low}$); un par $\{LOCAL, VISITANTE\}$ o $\{EMPATE, VISITANTE\}$ en banda **no se toca** (el rescate es exclusivo del eje localía); sin desnivel $\ge 1000$ msnm no hay rescate.
  5. **Aritmética intocable:** cero edición de $\lambda$, `estimar_intensidades_loglineal`, `calcular_alpha_ligadura`, Kelly, Poisson o `triaje_determinista_9_estrategias` (cuya cascada sellada `SHA256-VAULT-CORE-STRATEGIES-9-CASCADE` **no se toca**: la función se publica como adenda pura, invocable, no como sustituto del triaje).
* **O (Output):** `resolver_orden_fiduciario_con_indiferencia(p1, pX, p2, delta_alt)` ⇒ `{r_max, r_mid, r_low, p_max_val, p_mid_val, p_low_val, masa_cobertura_pct, separacion_mid_low, rescate_indiferencia, delta_alt_metros}`. En Atlante J10: `r_max = VISITANTE`, `r_mid = LOCAL`, `r_low = EMPATE`, `masa_cobertura_pct = 73.99`, `rescate_indiferencia = True`; el vértice consumado (`LOCAL`) pasa de `P_LOW` a **`P_MID`** (rescate cian) sin mover una sola décima de $P_{max}$.
* **Φ (Transición):** hacia `src/core/contracts/portfolio_math.py` (función pura + 2 constantes), `src/web/routes/markets.py` (invocación única en el Visor de calibración) y el espejo `docs/DIRGEN_VAULT.md` → `[VAULT-CORE-070-TRIAJE]` (adenda `[LN-QBE-124]`).
* **Deuda declarada:** la banda calibra la frontera de los vértices **bajos**; no jerarquiza la frontera $P_{max}/P_{mid}$ (donde una permutación sí alteraría la cobertura primaria y exigiría decreto propio). El sandbox de rentabilidad (`[LN-QBE-113]`) no consume aún esta jerarquía: sus Jueces sellados operan sobre la cascada de 9 estrategias, fuera del alcance ratificado.
* **[SHIELD]:** `tests/shield/test_shield_cold_start_and_indifference_band.py` (nuevo, 4 jueces) · `test_shield_visor_backtesting.py` · `test_shield_visor_backtesting_cold_start.py` (reconvertido, `[LN-QBE-125]`).

---

### ID: [LN-QBE-125] Cold Start Sincero: Derogación de la Sustitución por Prior de Mercado y Segmentación Declarada de la Muestra Calibrada

* **Ω (Resumen):** la varianza `VAR-2026-10-22-COLDSTART-SINCERO` certificó que la resolución de Cold Start sustituía $P'$ por el consenso desmarcado $q_{mkt}$ en todo partido con $S(\mathcal{I}) = 0$, de modo que `BS_QBE ≡ BS_MKT` **por identidad de vectores** y el Alpha resultante ($\equiv 0.00\%$) no era una medición sino un artefacto algebraico: la ignorancia se maquillaba de paridad con el mercado. Con **27 partidos ciegos** (J1–J3) sobre 97 concluidos, el Alpha de temporada quedaba contaminado. El Director ratificó el **Cold Start Sincero**: el modelo se evalúa con su **vector soberano real**, la ceguera se **declara** en la vitrina (`❄️ Cold Start (S=0)`) y la calibración honesta se lee en la **muestra calibrada** ($S(\mathcal{I}) = 1$, J4–J13).
* **I (Input):** el reporte macro/meso/micro de `_construir_reporte_calibracion` (`GET /api/markets/backtesting/calibration-report`), el sello `suficiencia_S_I` del fixture y los registros de Brier por partido.
* **P (Process) [DIRGEN-STRICT] (transcripción pura; $\lambda$ y $P'$ intactas):**
  1. **Cláusula derogatoria expresa.** Queda **DEROGADA** la regla de sustitución del *Axioma del Prior de Mercado* de `[LN-QBE-100]`: `if suficiencia_S_I == 0: p_local, p_empate, p_visitante = q_local, q_empate, q_visitante`. El bloque desaparece de `markets.py`; **no** se reubica, no se parametriza y no se conserva como rama muerta. Subsiste de `[LN-QBE-100]` todo lo demás: fórmula del Brier multicategórico, Alpha de calibración, taxonomía `P_MAX/P_MID/P_LOW`, desmarque proporcional de vig y contrato macro/meso/micro.
  2. **Evaluación con el vector soberano real.** Un partido con $S(\mathcal{I}) = 0$ se puntúa con su $P'$ publicado (prior puro del modelo), de manera que $BS_QBE$ y $BS_MKT$ divergen cuando el prior difiere del consenso: la degradación **se mide**, no se oculta [GOVERNANCE-01].
  3. **Declaración de ceguera.** La jornada expone `es_cold_start` (derivado del DATO: **todos** sus partidos con $S(\mathcal{I}) = 0$) y `alpha_etiqueta = "COLD_START"` (vs `"MEDIDO"`). El partido conserva `suficiencia_S_I` y la micro-tarjeta lo rotula `❄️ Cold Start (S=0)`; **derogado** el rótulo `🧊 COLD START: PRIOR DE MERCADO`, que afirmaba una sustitución ya inexistente.
  4. **Doble agregado declarado.** Se sirven tres bloques con la MISMA aritmética (una sola función de agregación, cero segunda verdad): `resumen_calibrado` (universo $S(\mathcal{I}) = 1$ — el criterio es el DATO, no el número de jornada), `resumen_global` (universo completo) y `resumen_temporada` (**alias byte-idéntico** de `resumen_global`, conservado porque tres consumidores sellados lo leen).
  5. **Aritmética intocable:** cero edición de la fórmula del Brier, del Alpha, del Brier individual por partido ni del desmarque de vig.
* **O (Output):** J1–J3 con `es_cold_start = True` y `alpha_etiqueta = "COLD_START"`; `resumen_calibrado` con las jornadas efectivamente informadas (J4–J13) y `resumen_global` con la temporada completa; `resumen_temporada` intacto como alias; micro-tarjeta honesta (`❄️ Cold Start (S=0)`) y macro-cards conmutables.
* **Φ (Transición):** hacia `src/web/routes/markets.py` (`_agregar_resumen_calibracion`, `es_cold_start`, `alpha_etiqueta`), `src/models/web_schemas.py` (`resumen_calibrado`, `resumen_global`, `es_cold_start`, `alpha_etiqueta`, `delta_alt_metros`, `rescate_indiferencia` — aditivos con default), `src/web/static/js/app.js` (`conmutarMuestraVisor`) y `src/web/templates/index.html` (selector de muestra) bajo `[ARCH-1.4.65]`.
* **Deuda declarada:** la muestra calibrada arranca en J4 porque la bóveda viva no posee historia previa informada; con más jornadas el $N$ crecerá y el Alpha será progresivamente más estable. Si una jornada futura publicara mezcla, se declarará `MEDIDO` y su bloque calibrado sólo contará los partidos informados.
* **[SHIELD]:** `tests/shield/test_shield_cold_start_and_indifference_band.py` (nuevo, 4 jueces) · `test_shield_visor_backtesting_cold_start.py` (RECONVERTIDO por BR-1 opción b: vigila la nueva ley) · `test_shield_visor_backtesting.py`.

---

### ID: [LN-QBE-126] Sandbox de Arquetipos y Vectores: Extracción Inducida de Firmas por Clase en el Espacio Z-Score

* **Ω (Resumen):** la doctrina vigente nombra TRES desenlaces ($P_{max}$, $P_{mid}$, $P_{low}$) pero nunca había publicado su **firma empírica**: qué combinación de magnitudes distingue de verdad un acierto primario de una ruptura. Este nodo legisla un instrumento **descriptivo y de sólo lectura** que, sobre los **97 partidos concluidos** (J1–J11), induce las firmas $\mathbf{V}_{P_{max}}$, $\mathbf{V}_{P_{mid}}$ y $\mathbf{V}_{P_{low}}$ en un espacio **Z-Score global** anclado al favorito, mide el poder separador de cada variable con el **F-ratio univariado de Fisher** y publica el **Vector de Contraste** $\Delta\mathbf{V}_{Ruptura} = \mathbf{V}_{P_{low}} - \mathbf{V}_{P_{max}}$. No recalibra $\lambda$, no reentrena, no escribe en la bóveda y no sustituye al triaje: es una sonda de lectura para el Director.
* **I (Input):** `matches` (97 finalizados) y `sovereign_distributions` (`p_local`/`p_empate`/`p_visitante` + `audit_trace_json.insumos_factivados`), leídos **exclusivamente** con `PersistenceGateway.read_session()` (3NF, cero DML).
* **P (Process):**
  1. **Anclaje al favorito (cero data snooping sobre el marcador).** El marco de referencia es el vértice $r_{max}$ del orden fiduciario canónico: toda magnitud **bilateral** se publica como diferencial firmado $\Delta V_j = V_{j,fav} - V_{j,rival}$; toda magnitud **contextual** se orienta al mismo bando (V29 $\Delta$Alt y V30 $\Delta$Descanso se invierten si el favorito es el visitante). El marcador sólo se lee DESPUÉS, para clasificar.
  2. **Matriz $\mathbf{X}$ (97 × D) con $D = 34$:** las **27 variables del catálogo de 32 con evidencia fáctica celda a celda** (V16 en cuarentena `[LN-QBE-123]`; V28 sin magnitud firmada —sólo cadena `1V - 0E - 2D`—; V31/V32 en `SIN EVIDENCIA` sobre 97/97; **V27 $\Delta$G H2H fuera de matriz porque el snapshot vigente no publica `h2h_stats`** —0 de 153 entradas de `matches_json`, verificado—) más **7 metadatos estocásticos** ($P_1'$, $P_X'$, $P_2'$, $P_{max}'$, $P_{mid}'$, $\Delta\eta$, $\Delta_{epist}$). Cada columna declara su **cobertura** $N_j$; la celda ausente **no participa** y **jamás se imputa** (`[GOVERNANCE-01]`). Una dimensión sin una sola celda en la muestra se declara en `derivaciones.fuera_de_matriz` con su causa y **se reintegra sola** en cuanto la fuente publique la celda (ningún literal congela $D$).
  3. **Normalización Z-Score global** por columna sobre las filas presentes, con guarda $\sigma_j = 0 \Rightarrow z = 0$ (constante ⇒ señal nula, nunca división por cero).
  4. **Partición ternaria delegada.** $\mathcal{S}_c$ se decide con `resolver_orden_fiduciario_con_indiferencia` (`portfolio_math`, `[LN-QBE-124]`) —la MISMA función que gobierna el Visor de calibración—: el sandbox **no ordena por su cuenta** (cero segunda verdad).
  5. **Centroides y contraste.** $\mathbf{V}_c$ = media por columna de $\mathbf{z}$ sobre $\mathcal{S}_c$; $\Delta\mathbf{V}_{Ruptura} = \mathbf{V}_{P_{low}} - \mathbf{V}_{P_{max}}$.
  6. **Poder separador.** $F_j$ = razón univariada de Fisher entre las tres clases (denominador $=0 \Rightarrow F_j = 0.0$, etiqueta `NULO`), rotulada `DECISIVA` / `MODERADA` / `RUIDO` con umbrales declarados; el ranking se ordena descendente y **separa el bloque estructural del metaestocástico**, que separa por construcción y no constituye hallazgo.
  7. **Reglas de veto sugeridas.** Sólo las variables con $F_j$ en el cuartil superior **y** $|\Delta V_{Ruptura,j}| \ge 0.25\sigma$ generan una regla rotulada `SUGERIDA · NO EJECUTA TRIAJE`: el sandbox no altera la cobertura ni la cascada de estrategias.
* **O (Output):** reporte estructurado (`status`, `particion`, `vector_pmax`/`vector_pmid`/`vector_plow`, `vector_contraste_ruptura`, `ranking_fisher`, `cobertura`, `derivaciones`), tablero ASCII de 6 bloques y export opcional a `data/output/arquetipos_vectores_reporte.json`.
* **Φ (Transición):** hacia `scripts/laboratorio/sandbox_arquetipos_vectores.py` (nuevo, CLI-FIRST: `--json`, `--top N`) bajo `[ARCH-1.4.66]`; el patrón de tablero se hereda de `sandbox_h2h_pipeline` (`[LN-QBE-106]`).
* **Deuda declarada:** (i) el F-ratio es **univariado**: no detecta interacción ni redundancia (dos columnas colineales se reparten el crédito) y una prueba conjunta exigiría varianza propia; (ii) $N = 97$ con 34 columnas es muestra pequeña: el ranking es una **hipótesis**, no una certificación de significancia; (iii) V28 (récord del visitante en sede) queda **fuera de la matriz** por no existir como magnitud firmada; (iv) la matriz crece con cada jornada concluida: la partición es una **instantánea** y el Juez congela la de hoy (**38 / 35 / 24, suma 97**), no un literal eterno; (v) V27 ($\Delta$G H2H) está fuera **por ausencia de fuente**, no por decisión doctrinal: los 17 snapshots vigentes publican 153 entradas de `matches_json` y **ninguna** porta `h2h_stats`; la celda entra sola cuando el colector la publique, sin tocar la ley.
* **[SHIELD]:** `tests/shield/test_shield_sandbox_arquetipos_vectores.py` (nuevo, 4 jueces: partición factual, centroides/contraste, monotonía de Fisher, pureza read-only y exportación).

### ID: [LN-QBE-127] Fuente Única de Verdad en la Calibración: Resolución al Vuelo de $P'$ y Derogación del Descarte Silencioso

* **Ω (Resumen):** el Visor de calibración fue declarado espejo de `matches` (fuente única de verdad), pero en la práctica **no lo era**: un partido CONCLUIDO con marcador consumado que no portaba $P'$ sellada —ni en el snapshot de captura ni en `sovereign_distributions`— se descartaba con un `continue` mudo, de modo que la vitrina y el dataset de investigación publicaban un universo **menor** que la temporada real sin declararlo. La ceguera de captura se convertía en ceguera de auditoría: el partido desaparecía de la muestra, del Brier y de la matriz sin dejar rastro. La ley establece que **ningún partido concluido se descarta en silencio**: si falta la distribución sellada, $P'$ se resuelve **AL VUELO** con el motor soberano y la resolución se **declara** y se **cuenta**.
* **I (Input):** `matches` (estado concluido + marcador factual), `fixtures_snapshots.matches_json` (captura sellada), `sovereign_distributions` (3NF) y los insumos PRE-KICKOFF ya presentes en la bóveda (`home_team_stats`, `away_team_stats`, splits, `form_10p`, ventana H2H, V29 de altitud).
* **P (Process) [DIRGEN-STRICT] en la matemática · [DBBD-FUNGIBLE] en el cableado:**
  1. **Cláusula derogatoria expresa.** Queda **DEROGADA** la rama `if p_prima is None: partidos_pendientes += 1; continue` de `_construir_reporte_calibracion` como mecanismo de descarte. No se reubica, no se parametriza ni se conserva como rama muerta.
  2. **Resolución al vuelo (delegada, cero invención).** El helper `_p_prima_al_vuelo(fila, fixture, traza)` delega en `generar_distribucion_soberana` (plano canónico sellado) con los insumos PRE-KICKOFF de la lista CERRADA `_CLAVES_RESOLUCION_AL_VUELO`. La resolución es **EFÍMERA**: se publica y jamás se persiste (persistirla crearía una segunda fuente de verdad y falsearía la captura). Sin una sola celda de evidencia el motor emite el **Prior de Ignorancia R-1** legislado $(0.3333, 0.3333, 0.3334)$: el vector es del motor, no de la capa web.
  3. **Sello de procedencia `origen_p_prima`.** Toda casilla declara de dónde sale el vector: `CAPTURA` (snapshot congelado, autoridad primaria) · `SOBERANA` (tabla 3NF) · `AL_VUELO` (resuelto dinámicamente). El sello sustituye a la inferencia implícita y es la columna que distingue evidencia sellada de reconstrucción.
  4. **Suficiencia declarada, no fabricada.** Una resolución al vuelo publica $S(\mathcal{I}) = 0$: el vector emitido sin distribución sellada **es** el prior de ignorancia, y rotularlo informado fabricaría una calibración inexistente (`[GOVERNANCE-01]`). `resumen_calibrado` sigue admitiendo **sólo** $S(\mathcal{I}) = 1$ (`[LN-QBE-125]` intacta); la resolución sí engrosa `resumen_global.total_partidos`, que es donde se mide la temporada real.
  5. **Contabilidad declarada.** El agregado macro publica `partidos_resueltos_al_vuelo`, derivado del propio micro-DTO (`origen_p_prima == "AL_VUELO"`): una sola contabilidad, cero parámetro extra. `partidos_pendientes_captura` subsiste con un único significado admisible: el motor **no pudo** emitir vector (fallo registrado en `logger.warning`).
  6. **Aritmética intocable:** cero edición de la fórmula del Brier, del Alpha, del orden fiduciario $P_{max}/P_{mid}/P_{low}$ ni del desmarque de vig.
* **O (Output):** micro-DTO con `origen_p_prima` y `suficiencia_S_I` por partido; `resumen_global` con `partidos_resueltos_al_vuelo`; `resumen_calibrado` inalterado en su criterio; y la matriz canónica de investigación (`[ARCH-1.4.67]`) heredando el universo completo.
* **Φ (Transición):** hacia `src/web/routes/markets.py` (constantes `ORIGEN_P_PRIMA_*`, lista `_CLAVES_RESOLUCION_AL_VUELO`, helper `_p_prima_al_vuelo`, cableado en `_construir_reporte_calibracion` y contabilidad en `_agregar_resumen_calibracion`), `src/models/web_schemas.py` (`CalibrationMatchOut.origen_p_prima`, `CalibrationSummaryOut.partidos_resueltos_al_vuelo` — aditivos con default) y `scripts/investigacion/generar_matriz_investigacion.py` bajo `[ARCH-1.4.67]`.
* **Deuda declarada:** (i) la resolución al vuelo es una **reconstrucción**, no una medición: por eso se declara $S(\mathcal{I}) = 0$ y nunca engorda el segmento calibrado; (ii) sólo se resuelven los insumos que la bóveda **ya** contiene; si un partido histórico no porta ninguna celda PRE-KICKOFF, el motor devuelve R-1 y el dataset lo exhibe como ignorancia declarada, no como pronóstico; (iii) el vector resuelto **no se persiste**: dos lecturas del mismo partido deben coincidir por determinismo del motor, y una divergencia futura sería un defecto del plano canónico, no de esta ley.
* **[SHIELD]:** `tests/shield/test_shield_sprint1_sincronizacion_matriz_investigacion.py` (2 jueces `[LN-QBE-127]`: guardián de código + conducta sobre bóveda SQLite efímera con dos partidos concluidos, uno sellado y uno sin distribución).

---

> **Trazabilidad de registro (VARIANCE-01) — Fase 8 (Colisión `LN-QBE-080`):** el nodo
> solicitado como `[LN-QBE-080]` por la Directiva P.I.R. **colisiona** con el nodo YA sellado
> `[LN-QBE-080] Compilador de Reportes Oficiales y PDF A4` (línea 555 de este libro,
> `src/reporting/compiler.py`). Conforme al precedente de trazabilidad `[LN-QBE-076]`/`[LN-QBE-077]`
> (*"sin reutilización de identificadores"*), el bloque se remapea a **`081`** y **`082`**
> conservando el orden ascendente, el contenido matemático VERBATIM y la frontera
> `[DIRGEN-STRICT]`. Solicitud formal registrada en
> `VAR-HIST-080-COLLISION`.

### ID: [LN-QBE-128] Prior Congelado de Apertura 2025 y Ley de Mezcla Monótona del Corte (Erradicación del Cold Start Estructural)

* **Ω (Resumen):** el motor sellado declara ignorancia (`S(I)=0`, Prior Fiduciario R-1 `(0.3333, 0.3333, 0.3334)`) cuando el corte N-1 de cualquiera de los dos clubes no alcanza el umbral de suficiencia (`pj < 3`), de modo que las jornadas J1-J3 de toda temporada nacen estructuralmente ciegas: **27 de 97 partidos** quedaban fuera del segmento calibrado no por una razón fáctica, sino por la mera ausencia de muestra DENTRO del torneo. La ley establece que la ignorancia se combate con **EVIDENCIA PREVIA CONGELADA**, jamás con el consenso del mercado (la sustitución por `q_mkt` está DEROGRADA por `[LN-QBE-125]`): se siembra el agregado físico REAL del torneo anterior (Apertura 2025) y se mezcla con el corte observado mediante un peso monótono `w = min(1, pj_obs / 3)`. Con `pj_obs = 0` el corte es 100% prior; con `pj_obs = 3` (umbral de suficiencia) el peso del prior es EXACTAMENTE 0 y el bloque es byte-idéntico al de la ruta previa. La ley JAMÁS altera λ, Dixon-Coles, André ni la fusión `[LN-QBE-104]`: sólo cambia la EVIDENCIA de entrada, y la suficiencia se sella por su propia función indicadora.
* **I (Input):** `data/cache_prior_apertura2025_liga_mx.json` (artefacto congelado de `[ARCH-1.4.69]`, generado del corpus H2H `betexplorer.com`), el corte N-1 reconstruido por el Pilar 1 (`_bloque_general`) y `torneo_actual_pj`.
* **P (Process) [DIRGEN-STRICT] en la matemática · [DBBD-FUNGIBLE] en el cableado:**
  1. **Umbral espejo.** `PJ_SUFICIENCIA_CANONICA = 3` es un ESPEJO declarado de la función indicadora sellada `evaluar_suficiencia_informativa` (Sección 2.13.1). El espejo se certifica en runtime (`verificar_espejo_umbral_suficiencia`): `pj=2 ⇒ 0` y `pj=3 ⇒ 1`. Si el plano canónico cambiara su umbral, el espejo lo delata antes de escribir una sola fila.
  2. **Ley de mezcla.** `w = min(1.0, pj_obs / 3)`; `pj_mezcla = pj_obs + round((1 - w) · pj_prior)`; para cada tasa `t` en `{gf, gc, pts, xg}`: `t_mezcla = w · (t_obs / pj_obs) + (1 - w) · (t_prior / pj_prior)` y `T_mezcla = round(t_mezcla · pj_mezcla)`.
  3. **Identidad en el umbral.** `pj_obs >= 3 ⇒ w = 1 ⇒` se devuelve el bloque observado SIN una sola clave añadida: J4-J17 (y toda jornada con muestra suficiente) permanecen byte-idénticas. Cero regresión.
  4. **Ceguera residual honesta.** Un club AUSENTE del prior (Atlante no disputó Apertura 2025) no recibe mezcla: su bloque queda como estaba y `S(I)=0` subsiste. La degradación se DECLARA, no se maquilla.
  5. **Frontera anti-fabricación.** `xGA` y `posesión` del prior NO viajan al bloque del motor: `[VAR-2026-J7-HOMOLOGACION §6.1·E1]` prohíbe publicar xGA en el vector homólogo (invertía el diagnóstico defensivo) y la posesión de Apertura 2025 NO EXISTE como medición en el corpus. El resolvedor los publica como TELEMETRÍA de auditoría; el ensamblador del vector sólo propaga `pj/gf/gc/pts/xg`.
  6. **Peso cero en el prior desactivado.** `--sin-prior` ⇒ `w` idéntico a 1 ⇒ reconstrucción byte-idéntica a la ruta anterior (auditoría A/B sin ramas muertas).
* **O (Output):** bloque de club con `suficiencia_S_I ∈ {0,1}` y sello `prior_apertura2025 = {fuente, temporada, fase, peso_prior, peso_observado, pj_observado, pj_prior, pj_mezcla, procedencia_xg}`; traza por fixture en el parte de homologación; re-sellado de `fixtures_snapshots` (7 campos) y de `sovereign_distributions`.
* **Φ (Transición):** `scripts/ingesta/sembrar_prior_apertura2025.py` (nuevo) y el resolvedor `_resolver_insumos_con_prior` de `scripts/ingesta/homologar_temporada_optah2h.py`, cableado en el bucle del corte N-1 con las banderas `--prior` / `--sin-prior`.
* **Deuda declarada:** (i) el prior es de FASE REGULAR 2025 (136 partidos, 17 clubes, `pj=16` cada uno): liguilla y Play-In quedan fuera por no ser muestra comparable; (ii) `xg_per_match` del prior es la ESTIMACIÓN calibrada `[ARCH-1.4.39]` (`max(0.5, GF · 1.05)`) porque el corpus NO porta xG Opta de 2025, y `xga_per_match` es GC factual (E1); (iii) la posesión 2025 no existe: se publica baseline neutro `50.0` declarado `NO MEDIDO`, que jamás se propaga al motor ni al catálogo 44V; (iv) la mezcla promedia TASAS con redondeo entero de conteos, de modo que en `pj_obs` de 1 o 2 el bloque no es un entero del torneo previo sino una interpolación DECLARADA (el sello `peso_prior` la publica); (v) 3 partidos de J1-J3 (los de Atlante) permanecen ciegos por diseño: la ceguera estructural desaparece, la ceguera fáctica residual se conserva y se mide; (vi) **DEUDA CERRADA POR DECRETO** `[VAR-2026-SPRINT3-ROI-AGR]` (RESUELTO, 2026-10-23): la erradicación del Cold Start retiró la masa ciega sobre la que se certificó el criterio `+8.0% / 18 posiciones / PnL 841.11` de `[LN-QBE-116]`, y el Director ratificó la **Alternativa B** re-cimentando el criterio sobre la física informada: **ROI $\ge +5.0\%$, PnL $\ge +$500.00 MXN, drawdown $\le 2.0\%$, $\ge 11$ jornadas** (medición viva: `+5.85%`, `+$584.59`, `1.50%`, 11 jornadas). El Juez 6 de `test_shield_h2_dominance_and_atlante_altitude.py` vuelve a VERDE; la evidencia fáctica y el dictamen constan en `docs/DIRGEN_VARIANCE_REQUEST_SPRINT3_ROI_AGR.md`.
* **[SHIELD]:** `tests/shield/test_shield_sprint3_prior_seeding_and_shannon_mining.py` (INVARIANZAS 1 y 2) + reconversión de los Jueces de `[LN-QBE-125]` (`test_shield_visor_backtesting_cold_start.py` y `test_shield_cold_start_and_indifference_band.py`) al FRENTE RESIDUAL (ciudadanía honesta de los 3 ciegos de Atlante).


### ID: [LN-QBE-129] Minería de Información Mutua de Shannon y Árbol Esparso de Veto (Descubrimiento de Rupturas P_LOW)

* **Ω (Resumen):** el sandbox de arquetipos `[LN-QBE-126]` mide separación con la razón de Fisher, que es **univariada y lineal**: no cuantifica la INCERTIDUMBRE REMANENTE ni detecta interacción. La ley incorpora la medida de información canónica de Shannon para ordenar las 64 celdas fácticas PRE-KICKOFF por su contenido informativo sobre la etiqueta consumada, y un árbol CART **esparso** que induce reglas de veto legibles sobre la ruptura residual (`clasificacion_triada == "P_LOW"`). El instrumento es de SÓLO LECTURA sobre `research_feature_matrix.csv` y sus salidas son **HIPÓTESIS ROTULADAS**: ninguna regla altera la cobertura, el triaje ni la cascada de estrategias.
* **I (Input):** `data/output/research_feature_matrix.csv` (`[ARCH-1.4.67]`): 64 celdas de Zona B como candidatas y `clasificacion_triada` (Zona D) como etiqueta. PROHIBIDO usar cualquier columna de Zona C como candidata: porta la P′ servida y `p_low_ruptura_pct`, que es una función determinista de la etiqueta (fuga circular).
* **P (Process) [DBBD-FUNGIBLE] (estadística descriptiva, cero DML, cero red):**
  1. **Discretización declarada.** Cada candidata numérica se bina en `k = 4` cuantiles por rangos; `SIN_DATO` es una categoría propia, jamás un cero. Columnas con menos de `5` valores observados quedan `SIN_EVIDENCIA`.
  2. **Información mutua.** `I(X;Y) = Σ_x Σ_y p(x,y) · log2( p(x,y) / (p(x)·p(y)) )` en BITS sobre la etiqueta ternaria `Y = P_MAX | P_MID | P_LOW`; el ranking se publica descendente y con desempate alfabético (determinismo bit-a-bit).
  3. **Árbol esparso de ruptura.** CART binario sobre `y = 1[P_LOW]`, impureza de Gini, umbrales candidatos = todos los puntos medios observados de cada variable (búsqueda exacta con sumas acumuladas), profundidad canónica `3` y hoja mínima canónica `5`. Si la configuración canónica no induce el umbral de veto, se ejecuta un **barrido gobernado** de hoja mínima en `{6, 7, 8, 4}` y —sólo después— de profundidad en `{4, 5}`; se publica la configuración elegida (`configuracion_arbol.calidad = CANONICA | BARRIDO_GOBERNADO`) junto con la canónica. El dato ausente (`SIN_DATO`) NO supera el umbral y cae en la rama `<=` (semántica declarada, jamás un cero).
  4. **Regla de veto.** Una hoja es regla si `pureza >= 60%` **y** `soporte >= 5` **y** `lift = pureza / tasa_base >= 2.0` (Decreto D4). Cada regla publica `condicion_booleana` interpretable, `tasa_ruptura_pct`, `soporte`, `lift` y la ruta de nodos.
  5. **Rótulo de hipótesis.** Toda regla se emite como `SUGERIDA · NO EJECUTA TRIAJE`: con `N = 97` y 64 candidatas la significancia NO queda certificada; el reporte declara el tamaño de muestra y la tasa base.
* **O (Output):** diccionario con `status`, `particion`, `tasa_base_ruptura_pct`, `ranking_informacion_mutua` (mínimo 15 filas), `arbol_esparso`, `reglas_veto_inducidas`, `cobertura`, `degradacion_declarada` y tablero ASCII de 5 bloques; export JSON opcional (`data/output/mineria_shannon_reporte.json`).
* **Φ (Transición):** `scripts/investigacion/mineria_factores_shannon.py` (nuevo, CLI-FIRST: `--json`, `--top N`, `--profundidad`, `--min-hoja`, `--ruta-dataset`, `--ruta-reporte`) bajo `[ARCH-1.4.70]`.
* **Deuda declarada:** (i) la información mutua es **sesgada al alza** en muestras pequeñas: la corrección por permutación queda fuera del Sprint; (ii) `k = 4` es una decisión de discretización declarada, no una optimalidad; (iii) las reglas describen la MUESTRA y no constituyen certificación out-of-sample; (iv) el árbol no reemplaza la cobertura de la tríada: es un mapa de riesgo para el analista.
* **[SHIELD]:** `tests/shield/test_shield_sprint3_prior_seeding_and_shannon_mining.py` (INVARIANZAS 3 y 4).

### ID: [LN-QBE-130] Reglas de Curación HITL y Seeding de Competiciones
* **Ω (Resumen):** Gobernar la inicialización de competiciones y la lógica de curación de escudos, absorbiendo las decisiones operativas previamente documentadas como comentarios en el código (VARIANZA-09, ALT-9).
* **I (Input):** Identificadores de liga, catálogos de clubes.
* **P (Process) [BIZ-LOGIC]:**
  1. El Seeder inicializa las competiciones base garantizando la idempotencia.
  2. La Curación HITL aplica las reglas de hash SHA-256 para validar los escudos descargados.
  3. Los fallbacks de imágenes aplican la jerarquía SVG en caso de ausencia del binario.
* **O (Output):** Transacciones 3NF de catálogos y activos.
* **Φ (Transición):** Consumidor activo: `src/storage/curation_service.py` y `src/storage/seeder.py`.
* **[SHIELD]:** `tests/shield/test_shield_orphan_rules_saneamiento.py`
* **Enmienda Nudo 2:** Queda terminantemente prohibido el seeding de tablas de posiciones estáticas (`TABLA_OFICIAL_J7_CONCLUIDA`) o de cuotas comerciales inventadas (`fixtures_iniciales_j8`). El Seeder solo puede inicializar la estructura base (competiciones), el resto debe venir de la ingesta fáctica.

---

**BASE DE GOBIERNO SELLADA BAJO EL KYBERN FRAMEWORK v8.0 / v12.0 — GRAFO LÓGICO INMUTABLE.**


```