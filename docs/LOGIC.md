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

### ID: [LN-QBE-003] Ingesta Fáctica Estructurada FotMob (Opta Metrics Engine)

* **Ω (Resumen):** Extraer y persistir en SQLite la tabla de posiciones completa (18 clubes), métricas Opta ($xG$, $xGA$, $xPTS$, forma reciente de 5 partidos W/D/L) y la cartelera de fixtures de la jornada activa sin consumo de tokens de LLM.
* **I (Input):** `league_id` (e.g. `262` para Liga MX).
* **P (Process) [ARCH-PILLAR] [BIZ-LOGIC]:**
  1. Extraer tabla general de 18 clubes: posición, puntos, PJ, PG, PE, PP, GF, GC, diferencia y vector de forma reciente (5 partidos).
  2. Extraer tabla avanzada Opta: $xG$ acumulado, $xGA$ concedido, $xPTS$ y diferencial $\Delta xG$.
  3. Extraer cartelera de jornada: pares de clubes, fechas, horarios y momios 1X2 con Pago Anticipado.
  4. Guardar snapshot en SQLite (`standings_snapshots` y `fixtures_snapshots`).
  5. Cero simulación: ante caída de red, declarar `CUARENTENA`; prohibido inventar datos sintéticos.
* **O (Output):** `LiveBoardOut` tipado contra Pydantic V2.
* **Φ (Transición):** Hacia **[LN-QBE-016]** y la Vista 2 (Split-View).
* **[SHIELD]:** `tests/shield/abstract_test_LN_QBE_003_live_board_integration.py`

---

### ID: [LN-QBE-002] Sensor Fáctico Grounded (Gemini Search Engine)

* **Ω (Resumen):** Extracción complementaria y auditoría cualitativa mediante Gemini 3.6 Flash con Google Search Grounding asistida por la Rueda de Inferencia y Circuit Breaker de 4 llaves.
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

* **Ω (Resumen):** Convertir la probabilidad híbrida del modelo en un precio decimal puro e identificar el descalce de cuotas (*Market Mispricing*).
* **I (Input):** $P_{\text{híbrida}}(k)$ para $k \in \{\text{Fav}, \text{Emp}, \text{Und}\}$.
* **P (Process) [BIZ-LOGIC]:**
  1. Momio Justo Teórico:
     $$O_{\text{Q-BE}}(k) = \frac{100.0}{P_{\text{híbrida}}(k) \times 100.0} = \frac{1.0}{P_{\text{híbrida}}(k)}$$
  2. Ventaja Matemática Pura:
     $$\text{Edge}(k) = P_{\text{híbrida}}(k) - \frac{1.0}{O_{\text{Casino}}(k)}$$
* **O (Output):** `FairOddsSnapshot`.
* **Φ (Transición):** Hacia **[LN-QBE-050]** y la Vista de Radiografía.

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

### ID: [LN-QBE-030] Métricas Sintéticas de Control y Peligro ($FCF, E_{\text{att}}$)

* **Ω (Resumen):** Aislar la varianza de goles fortuitos mediante volumen de tiros y control de balón de 10 juegos.
* **P (Process) [ALGO-PROTECTED]:**
  $$\text{Raw\_FCF} = \left(\frac{\overline{\text{poss}}}{50.0}\right) \times \left(\frac{2.0 \cdot (\overline{\text{sot}} + 1.0)}{\overline{\text{sot}} + \overline{\text{sota}} + 2.0}\right) \implies FCF = \text{Clamp}(\text{Raw\_FCF}, [0.65, 1.35])$$
  $$\text{Raw\_E}_{\text{att}} = \frac{\overline{\text{gf}} + 0.35 \cdot \overline{\text{sot}}}{1.0 + 0.35 \cdot \overline{\text{sot}}} \implies E_{\text{att}} = \text{Clamp}(\text{Raw\_E}_{\text{att}}, [0.60, 1.40])$$
* **O (Output):** `SyntheticMetrics`.
* **Φ (Transición):** Hacia **[LN-QBE-040]**.

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
* **O (Output):** `StrategyComplianceMatrix`.
* **Φ (Transición):** Hacia **[LN-QBE-070]**.

---

### ID: [LN-QBE-070] Router de Utilidad Pura, Kelly y Techo Aritmético

* **Ω (Resumen):** Seleccionar la estrategia óptima individual mediante comparación analítica de utilidad, calcular la ruina conjunta del portafolio y estructurar los boletos en pesos con respeto estricto al techo de ganancia máxima.
* **P (Process) [ALGO-PROTECTED] [BIZ-LOGIC]:**
  1. **Comparación de Utilidad Directo vs. Cobertura:**
     $$U_{\text{Directo}} = EV_{\text{Directo}} \times P_{\text{Fav}}$$
     $$U_{\text{Cobertura}} = EV_{\text{Cobertura}} \times (1.0 - \Psi_{\text{Ruina}})$$
     - Si $U_{\text{Directo}} > U_{\text{Cobertura}} \land \Psi_{\text{Ruina}} \le 0.08 \implies$ Seleccionar **`QBE-D1+` (o `D1`)**.
  2. **Escalera de Prioridad:** `H2+` $\rightarrow$ Max($U$) entre `D1+/H1+` $\rightarrow$ Max($U$) entre `D1/H1` $\rightarrow$ `H2` $\rightarrow$ `R1/R2` $\rightarrow$ `QBE-00`.
  3. **Asignación de Capital:**
     - $S_i = \frac{EV_i}{\Psi_i}$, $w_i = \frac{S_i}{\sum S_j}$.
     - $\text{Bolsa}_{\text{Core}} = B \times \min(0.25, 0.06 \cdot K)$.
     - $\text{Cap}_i = \min(0.08, \max(0.02, \frac{EV_i}{3.0 \cdot \Psi_i}))$.
     - $A_i = \min(\text{Bolsa}_{\text{Core}} \times w_i, B \times \text{Cap}_i)$ con piso operativo de $4.00 MXN.
  4. **Dutching Exacto:**
     - Familia H2: Boleto 1 (Seguro Fav) $= A_i / O_{\text{Fav}}$, Boleto 2 (Ganancia Emp) $= A_i - \text{Boleto 1}$.
     - Familia H1 / R1: Boleto 1 (Seguro Emp) $= A_i / O_{\text{Emp}}$, Boleto 2 $= A_i - \text{Boleto 1}$.
     - Familia D1: Boleto 1 $= \$0.00$, Boleto 2 $= A_i$.
  5. **Invarianza de Techo Aritmético de Cartera [INVARIANZA #7]:**
     - Prohibido clavar pisos mínimos fijos (ej. `max(0.50)` o `$3.50`).
     - Sumatoria pura: $EV_{\text{Global}} = \sum_{i=1}^K A_i \cdot \left(\frac{EV_{\text{Net\_ROI}, i}}{100.0}\right)$.
     - Techo estricto: $EV_{\text{Global}} \le \sum_{i=1}^K \text{Ganancia\_Máxima\_Partido}_i$.
* **O (Output):** `PortfolioExecutionPlan`.
* **Φ (Transición):** Hacia **[LN-QBE-013]**, **[LN-QBE-014]** y **[LN-QBE-090]**.

---

### ID: [LN-QBE-013] Sintetizador de Metadatos y Cronometría Dinámica

* **Ω (Resumen):** Deducir cronológicamente el torneo, jornada y rango de fechas reales de los partidos eliminando textos hardcodeados.
* **P (Process) [ANTI-BUG]:**
  1. Fechas: Parsear fechas mínimas y máximas de los partidos y formatear en español (`"05 de Septiembre de 2026"` o `"04 al 05 de Septiembre de 2026"`).
  2. Jornada: Si el torneo es Copa/Champions/Leagues Cup $\implies$ rotular `"Fase de Grupos / Eliminatoria"`. Si es liga regular $\implies$ `"Jornada N"`.
  3. Marca temporal de procesamiento: Registrar `datetime.now().strftime("%d-%m-%Y %H:%M hrs")`.
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
**BASE DE GOBIERNO SELLADA BAJO EL KYBERN FRAMEWORK v8.0 / v12.0 — GRAFO LÓGICO INMUTABLE.**
```