```markdown
# Q-BE Casino Deportes — Logic Book (LOGIC.md)
**Versión:** 9.0 (Kybern Industrial - Formal IPO Graph Edition)  
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
        ▼
 ┌──────────────┐
 │ [LN-QBE-005] │ ➔ Triaje Determinista de Cuotas 1X2 (Paso 0-A)
 └──────┬───────┘
        │ (Partidos pre-aprobados por 6 vías de valor)
        ├──────────────────────────┐
        ▼                          ▼
 ┌──────────────┐           ┌──────────────┐
 │ [LN-QBE-003] │           │ [LN-QBE-002] │
 │ FotMob Opta  │           │ Gemini Search│
 └──────┬───────┘           └──────┬───────┘
        │                          │
        └────────────┬─────────────┘
                     ▼
              ┌──────────────┐
              │ [LN-QBE-010] │ ➔ Aduana de Sanidad y Anclaje (Paso 0-C)
              └──────┬───────┘
                     │
        ┌────────────┴─────────────┐
        ▼                          ▼
 ┌──────────────┐           ┌──────────────┐
 │ [LN-QBE-020] │           │ [LN-QBE-030] │
 │ κ-Decay H2H  │           │ FCF & E_att  │
 └──────┬───────┘           └──────┬───────┘
        │                          │
        └────────────┬─────────────┘
                     ▼
              ┌──────────────┐
              │ [LN-QBE-040] │ ➔ Poisson Bivariado 6x6 calibrado con xG Opta
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │ [LN-QBE-050] │ ➔ Breakeven Dinámico Continuo (θ*)
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │ [LN-QBE-060] │ ➔ Evaluador Booleano, Catálogo y Triple Candado
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │ [LN-QBE-070] │ ➔ Router Θ de Utilidad Pura, Kelly y Hard-Caps
              └──────┬───────┘
                     │
        ┌────────────┴─────────────┐
        ▼                          ▼
 ┌──────────────┐           ┌──────────────┐
 │ [LN-QBE-013] │           │ [LN-QBE-014] │
 │ Cronometría  │           │ Tesis Dual   │
 └──────┬───────┘           └──────┬───────┘
        │                          │
        └────────────┬─────────────┘
                     ├──────────────────────────┐
                     ▼                          ▼
              ┌──────────────┐           ┌──────────────┐
              │ [LN-QBE-080] │           │ [LN-QBE-090] │
              │ Compilador   │           │ Shield Gate  │
              └──────────────┘           └──────────────┘
```

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

### [LN-QBE-060-R] Estado de Sueño Profundo para la Familia R (R1 y R2) [GOVERNANCE] [ALGO-PROTECTED]
* **Estado:** DESCONECTADA / EN REFORMULACIÓN HOLÍSTICA.
* **Mandato:** Queda estrictamente prohibida la emisión de órdenes bajo los códigos `QBE-R1` y `QBE-R2` en el evaluador de estrategias.
* **Comportamiento:** Toda evaluación de R1 y R2 debe retornar `viable = False` con el motivo `"ESTRATEGIA EN SUEÑO PROFUNDO (REFORMULACIÓN HOLÍSTICA EN CURSO)"`. Todo partido con ineficiencia en el no-favorito o empate debe derivar a `QBE-H2` o a `QBE-00` (Veto preventivo).

* **Candado 4 para Familia R (Filtro Anti-Contracorriente Obligatorio) [BIZ-LOGIC] [ALGO-PROTECTED]:**
  - Queda estrictamente prohibido autorizar estrategias de la Familia R (`QBE-R1` o `QBE-R2`) si el favorito del mercado mantiene la probabilidad individual dominante en el modelo Q-BE ($P_{\text{Fav}} > P_{\text{Und}}$) y el no-favorito posee ventaja matemática negativa ($Edge_{\text{Und}} \le 0.0$).
  - *Regla de Decisión:*
    $$\text{Si } (P_{\text{Fav}} > P_{\text{Und}} \land Edge_{\text{Und}} \le 0.0) \implies \text{Viable}_{\text{R1/R2}} = \text{False}$$
  - *Motivo:* Previene apostar capital a la derrota del desenlace más probable cuando el valor real está concentrado exclusivamente en el empate. El partido debe derivar a `QBE-H2` o a `QBE-00` (Veto preventivo).
* **O (Output):** `StrategyComplianceMatrix`.
* **Φ (Transición):** Hacia **[LN-QBE-070]**.

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
  5. **Asignación de Capital:**
     - $S_i = \frac{EV_i}{\Psi_i}$, $w_i = \frac{S_i}{\sum S_j}$.
     - $\text{Bolsa}_{\text{Core}} = B \times \min(0.25, 0.06 \cdot K)$.
     - $\text{Cap}_i = \min(0.08, \max(0.02, \frac{EV_i}{3.0 \cdot \Psi_i}))$.
     - $A_i = \min(\text{Bolsa}_{\text{Core}} \times w_i, B \times \text{Cap}_i)$ con piso operativo de $4.00 MXN.
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

### ID: [LN-QBE-035] Registro Modular de Variables y Suficiencia Fáctica

* **Ω (Resumen):** Gobernar la transformación determinista de datos observados ($\mathcal{I}_i$) en factores estructurales normalizados ($\mathcal{A}_i, \mathcal{D}_i$) bajo la regla de suficiencia $S(\mathcal{I}_i) \in \{0, 1\}$.
* **Suficiencia $S(\mathcal{I}_i)$:** Requiere obligatoriamente que ambos clubes cuenten con partidos jugados $PJ \ge 3$, métricas de goles y tiros $SoT > 0$. Si $S(\mathcal{I}_i) = 0$, la distribución colapsa al prior de ignorancia uniforme $(1/3, 1/3, 1/3)$ y se marca como no operable.
* **Cálculo de Factores Normalizados:**
  $$A_{\text{home}} = \ln\left(\frac{0.65 \cdot xG_{\text{local}} + 0.35 \cdot GF_{\text{local}}}{\mu_{\text{liga}} / 2}\right), \quad D_{\text{away}} = -\ln\left(\frac{0.65 \cdot xGA_{\text{visita}} + 0.35 \cdot GC_{\text{visita}}}{\mu_{\text{liga}} / 2}\right)$$
* **Derivación de $xG/xGA$ en Ausencia de Tiros Profundos (H7):**
  $$\text{Fav } xG_{\text{est}} = \text{round}(\overline{GF}_{\text{Fav}} \times 1.05, 2), \quad xGA_{\text{est}} = \text{round}(\overline{GC}_{\text{Fav}} \times 0.95, 2)$$
  $$\text{Und } xG_{\text{est}} = \text{round}(\overline{GF}_{\text{Und}} \times 0.95, 2), \quad xGA_{\text{est}} = \text{round}(\overline{GC}_{\text{Und}} \times 1.10, 2)$$
* **Token Fail-Loud de Marcador Pendiente (H4):** Si un encuentro concluyó pero la federación aún no publica los números oficiales de goles, el sistema asigna el token canónico `"MARCADOR_PENDIENTE"`, prohibiendo inventar empates `"0 - 0"`.

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
**BASE DE GOBIERNO SELLADA BAJO EL KYBERN FRAMEWORK v8.0 / v12.0 — GRAFO LÓGICO INMUTABLE.**

```