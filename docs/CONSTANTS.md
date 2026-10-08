# 📐 LIBRO CANÓNICO DE CONSTANTES, ESCALAS Y COTAS NUMÉRICAS (CONSTANTS.md)
**Versión:** 1.0 (Universal Financial & Stochastic Standards)  
**Marco:** Kybern Industrial Framework v13.5  
**Estado:** `[ALGO-PROTECTED]` — Bóveda de Constantes Inmutables  

Este libro declara formalmente todas las constantes numéricas, escalas y factores del sistema. Queda estrictamente prohibido alterar o reutilizar estos símbolos fuera de su dominio legislado.

---

## 1. DOMINIO TEMPORAL Y DECAIMIENTO HISTÓRICO (H2H)

| Símbolo | Nombre Canónico | Valor Exacto | Unidad | Nodo Dueño | Dominio de Validez | Prohibición de Reúso |
|:---:|---|---|:---:|:---:|---|---|
| $\tau_{\text{H2H}}$ | Vida Media Temporal H2H | `180.0` | Días | `[LN-QBE-020]` | Ventana de enfrentamientos directos | No usar como ventana de forma reciente |
| $\kappa_{\text{decay}}$ | Constante de Decaimiento H2H | $\frac{\ln(2)}{180.0} \approx 0.00385098$ | $\text{días}^{-1}$ | `[LN-QBE-020]` | Exponente del kernel $e^{-\kappa \Delta t}$ | **PROHIBIDO** usar como escala de damping |
| $N_{\text{H2H}}^{\max}$ | Muestra Máxima H2H | `5` | Partidos | `[LN-QBE-020]` | Enfrentamientos directos evaluados | No exceder sin calibración de varianza |

---

## 2. DOMINIO DE FÍSICA ESTOCÁSTICA Y COMPRESIÓN DE GOLES

| Símbolo | Nombre Canónico | Valor Exacto | Unidad | Nodo Dueño | Dominio de Validez | Prohibición de Reúso |
|:---:|---|---|:---:|:---:|---|---|
| $\mu_{\text{liga}}$ | Media Goles Liga MX | `2.65` (Liga MX) / `2.60` (Gral) | Goles / 90' | `[LN-QBE-089]` | Parámetro macro de liga | No usar como expectativa individual |
| $\bar{\gamma}_{\text{home}}$ | Ventaja Media Incondicional | `0.15` | Log-Ratio | `[VAULT-CORE-001]` | Intercepto base en ecuación de ligadura | No alterar sin análisis de 3 temporadas |
| $\kappa_{\text{damp}}$ | Techo de Compresión $\tanh$ | $2.50 \cdot \sigma_{\text{liga}} = 2.50$ | Adimensional | `[VAULT-CORE-001]` | Damping hiperbólico de factores $A, D$ | **PROHIBIDO** confundir con $\kappa_{\text{decay}}$ |
| $\sigma_{\text{liga}}$ | Dispersión Base de Factores | `1.00` | Desv. Estándar | `[VAULT-CORE-001]` | Escala de factores centrados en cero | Inmutable por diseño |
| $\text{peso}_{xG}$ | Ponderación Señal Calidad | `0.65` | Fracción | `[LN-QBE-035-B]` | Mezcla Opta $xG / GF$ | La suma con $\text{peso}_{GF}$ debe ser $1.0$ |
| $\text{peso}_{GF}$ | Ponderación Señal Volumen | `0.35` | Fracción | `[LN-QBE-035-B]` | Mezcla Opta $xG / GF$ | La suma con $\text{peso}_{xG}$ debe ser $1.0$ |

## 3. DOMINIO DE CONTRACCIÓN BAYESIANA DE FORMA (10 PARTIDOS)

| Símbolo | Nombre Canónico | Valor Exacto | Unidad | Nodo Dueño | Dominio de Validez | Prohibición de Reúso |
|:---:|---|---|:---:|:---:|---|---|
| $\rho_{\text{estable}}$ | Peso Ancla Macro (Sin Shock) | `0.55` | Fracción | `[LN-QBE-036]` | Contracción Normal-Normal ($Q_{\text{mod}} = 1.0$) | No alterar sin prueba de calibración |
| $\rho_{\text{shock}}$ | Peso Ancla Macro (Con Shock) | `0.30` | Fracción | `[LN-QBE-036]` | Contracción con shock ($Q_{\text{mod}} \ne 1.0$) | No usar si no hay reporte médico verificado |
| $N_{\text{forma}}$ | Ventana de Forma Reciente | `10` | Partidos | `[LN-QBE-036]` | Partidos de alta frecuencia recientes | No truncar a menos de 5 fechas |

---

## 4. DOMINIO DE INCERTIDUMBRE EPISTÉMICA Y GOBERNANZA

| Símbolo | Nombre Canónico | Valor Exacto | Unidad | Nodo Dueño | Dominio de Validez | Prohibición de Reúso |
|:---:|---|---|:---:|:---:|---|---|
| $\tau_{\text{disp}}$ | Tolerancia Crítica Discrepancia | `0.12` | Probabilidad | `[LN-QBE-070-B]` | Límite de desacuerdo inter-modelos | Discrepancia $> 0.12 \implies$ Cuarentena |
| $\varepsilon_{\text{friccion}}$ | Amortiguador de Singularidad | `0.01` | Adimensional | `[LN-QBE-073-B]` | Denominador en Score de Fricción | Evita división por cero |
| $\gamma_{\text{Kelly}}$ | Fracción Atenuada de Kelly | `0.25` (Cuarto de Kelly) | Escalar | `[LN-QBE-070-B]` | Supresión de colas de varianza | Prohibido usar Kelly Completo ($1.0$) |
| $\Gamma_{\text{base}}$ | Umbral Maestro de Masa Base | `0.6700` ($67.0\%$) | Probabilidad | `[LN-QBE-059]` | Corte canónico que supera $2/3 \approx 0.6667$ | No descender por debajo de 2/3 |
| $\Gamma_{\text{mid}}$ | Umbral Maestro Exigente | `0.7000` ($70.0\%$) | Probabilidad | `[LN-QBE-059]` | Modo estricto de concentración | Exclusivo del selector UI |
| $\Gamma_{\text{high}}$| Umbral Maestro Conservador | `0.7500` ($75.0\%$) | Probabilidad | `[LN-QBE-059]` | Modo ultra-prudente (baja varianza) | Exclusivo del selector UI |


---

## 5. DOMINIO FINANCIERO Y LÍMITES PATRIMONIALES (HARD-CAPS)

| Símbolo | Nombre Canónico | Valor Exacto | Unidad | Nodo Dueño | Dominio de Validez | Prohibición de Reúso |
|:---:|---|---|:---:|:---:|---|---|
| $\text{Cap}_{\text{partido}}$ | Hard-Cap Individual Máximo | `0.0800` ($8.0\%$) | % Bankroll | `[LN-QBE-070-B]` | Exposición máxima por evento | Inviolable (The Shield Invariante #3) |
| $\text{Cap}_{\text{cartera}}$ | Hard-Cap Global de Jornada | `0.2500` ($25.0\%$) | % Bankroll | `[LN-QBE-070-B]` | Exposición total simultánea de jornada | Inviolable (The Shield Invariante #4) |
| $\text{Piso}_{\text{ventanilla}}$ | Apuesta Mínima Legal | `$2.00` | MXN | `[LN-QBE-071]` | Terminal físico de casino | Ningún boleto split puede ser $< 2.00$ |
| $\text{Tol}_{\text{tablas}}$ | Tolerancia Bancaria $V=0$ | `$0.08` | MXN | `[LN-QBE-070]` | Desviación máxima de indemnidad | $\|B_{\text{seg}} \cdot O_{\text{emp}} - B_i\| \le 0.08$ |

---

## 6. DOMINIO COMBINATORIO QUINIELAS (PROGOL / REVANCHA)

| Símbolo | Nombre Canónico | Valor Exacto | Unidad | Nodo Dueño | Dominio de Validez | Prohibición de Reúso |
|:---:|---|---|:---:|:---:|---|---|
| $K_{\text{regular}}$ | Dimensión Progol Regular | `14` | Partidos | `[LN-QBE-084]` | Casillas de concurso principal | Espacio de búsqueda $2^{14} = 16,384$ |
| $K_{\text{revancha}}$ | Dimensión Progol Revancha | `7` | Partidos | `[LN-QBE-087]` | Casillas de concurso anexo | Espacio total $3^7 = 2,187$ (Todo o Nada) |
| $\text{Precio}_{\text{progol}}$ | Costo Quiniela Sencilla | `$15.00` | MXN | `[LN-QBE-074]` | Precio oficial Pronósticos | $M = \lfloor B / 15.0 \rfloor$ |
| $\text{Precio}_{\text{revancha}}$ | Costo Revancha Sencilla | `$5.00` | MXN | `[LN-QBE-087]` | Precio oficial Pronósticos | Prohibido descenso por Hamming |
| $\mathcal{W}_{\text{desamb}}$ | Ventana Crítica de Torneo | $[-24\text{h}, +72\text{h}]$ | Horas | `[LN-QBE-094]` | Disputa respecto a $t_{\text{cierre}}$ | Desambiguación temporal de ligas |

---

## 7. TABLA DE PROHIBICIONES DE REÚSO (CO-LOCACIÓN DE SÍMBOLOS)

| Símbolo A | Símbolo B | Relación Legislada | Nodo Rector |
|---|---|---|:---:|
| $\kappa_{\text{decay}}$ (`ln2/180`, días⁻¹) | $\kappa_{\text{damp}}$ (`2.50·σ`, adimensional) | **Jamás son intercambiables**: uno decae evidencia histórica H2H, el otro comprime factores log-diferenciales | `[LN-QBE-020]` / `[VAULT-CORE-001]` |
| $\rho_{\text{estable}}$ (`0.55`) | $\rho_{\text{shock}}$ (`0.30`) | El ancla macro sólo se relaja con **shock verificado** ($Q_{\text{mod}} \ne 1.0$) | `[LN-QBE-036]` |
| $\text{Cap}_{\text{partido}}$ (`0.08`) | $\text{Cap}_{\text{cartera}}$ (`0.25`) | El cap individual no puede superar el 32% del cap de cartera (relación $0.08/0.25$) | `[LN-QBE-070-B]` |
| $\tau_{\text{disp}}$ (`0.12`) | $\text{Tol}_{\text{tablas}}$ (`0.08` MXN) | Uno mide desacuerdo epistémico en probabilidad; el otro indemnidad bancaria en pesos | `[LN-QBE-070-B]` / `[LN-QBE-070]` |

---

## 📎 NOTA DE TRANSCRIPCIÓN (Provenance)

Transcrito **verbatim** desde el Decreto de Consolidación (Sprint 3 — Capa 4), según la Directiva
Maestra de Consolidación y Materialización. Los valores numéricos, unidades y nodos dueños son
**inmutables**; el catálogo no crea, delega ni re-calibra nada por sí mismo.

* **Errata tipográfica declarada (sólo presentación markdown):** en la fila de
  $\text{Tol}_{\text{tablas}}$ las barras de valor absoluto se escriben `\|` al renderizar (las
  barras crudas `|` cierran la celda de la tabla). El contenido matemático legislado
  ($\text{Tol} = \$0.08$ MXN con $|B_{\text{seg}} \cdot O_{\text{emp}} - B_i| \le 0.08$) queda intacto.
* **Fuentes de verificación en código (anclaje simbólico, cero archivo:línea):**
  $\tau_{\text{H2H}}$ / $\kappa_{\text{decay}}$ → `src/core/temporal.py` (`TemporalDecayEngine`);
  $\kappa_{\text{damp}}$ / $\sigma_{\text{liga}}$ → `src/core/intensity_canonical_loglink.py`
  (`aplicar_damping_hiperbolico`); $\rho_{\text{estable}}$ / $\rho_{\text{shock}}$ /
  $\text{peso}_{xG}$ / $\text{peso}_{GF}$ → `src/core/sovereign/bayesian_form.py`.
* **Cierre de la Capa 4:** los símbolos $\kappa_{\text{decay}}$, $\rho_{\text{estable}}$,
  $\rho_{\text{shock}}$ y $N_{\text{forma}}$ quedan **consumidos** por el motor en producción
  (`src/core/sovereign_pipeline.py`, nodos `[LN-QBE-036]` y `[LN-QBE-020-C]`); ninguna constante
  canónica permanece huérfana ni duplicada.

