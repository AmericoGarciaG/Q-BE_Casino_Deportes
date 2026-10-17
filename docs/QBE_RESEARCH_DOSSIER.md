# 🔬 Q-BE RESEARCH DOSSIER
## Física Matemática, Constantes, Catálogo de 44 Variables y Autopsia Forense

| Campo | Valor |
|---|---|
| **Proyecto** | `Q_BE_CD_WEB` (Quantitative Betting Engine — Web Platform) |
| **Emisor** | Agente Constructor Kybern v12.0 |
| **Autoridad** | Américo García Guerrero (Director Humano) |
| **Fecha de compilación** | 2026-10-16 |
| **Régimen de la tarea** | `[DBBD-FUNGIBLE]` — Tarea estrictamente documental (cero diffs en `src/`, cero escrituras a base de datos) |
| **Destinatario** | Agente Data Scientist aislado (entorno Linux, dataset histórico provisto externamente) |
| **Artefacto** | `docs/QBE_RESEARCH_DOSSIER.md` |

> **Propósito.** Este documento es el **único punto de contexto** que el Data Scientist necesita para
> iniciar la investigación de Machine Learning sobre Q-BE: la física matemática del motor estocástico,
> las constantes canónicas vigentes, el catálogo íntegro de las 44 variables candidatas y el estado
> fáctico real medido por la autopsia forense de 97 partidos.
>
> **Aviso de gobernanza (frontera de inmutabilidad).** El motor de Q-BE opera bajo régimen
> `[DIRGEN-STRICT]`: las ecuaciones, constantes y umbrales aquí transcritos **no son calibrables por el
> investigador**; son la línea base contra la cual se mide cualquier mejora. Las fuentes de verdad del
> sistema siguen siendo `docs/LOGIC.md`, `docs/CONSTANTS.md`, `docs/DIRGEN_VAULT.md` y
> `docs/ID_REGISTRY.md`; este dossier únicamente las consolida y agrega la evidencia empírica.
> Toda variable nueva del catálogo de 44 ingresa al motor **exclusivamente** a través del contenedor de
> factores latentes GSL-3D (`[ARCH-1.4.33]`): la ecuación log-lineal de intensidades solo interactúa con
> los 3 factores latentes sellados ($\mathcal{A}^*, \mathcal{D}^*, \mathcal{C}^*$).

### Índice
1. **[Sección 1]** Física matemática y motor estocástico
2. **[Sección 2]** Línea base y autopsia factual actual
3. **[Sección 3]** El catálogo de las 44 variables candidatas
4. **[Sección 4]** Mandato para el Data Scientist

---

# SECCIÓN 1 — FÍSICA MATEMÁTICA Y MOTOR ESTOCÁSTICO

## 1.1. Modelo base: Poisson independiente con enlace Log-Lineal

El núcleo proyecta los goles esperados ($\lambda_H$ del local, $\mu_A$ del visitante) mediante una
**ecuación de enlace log-lineal** (arquitectura canónica `[VAULT-CORE-001]`, Sección 4.9 del Tratado
Volumen I, materializada en `src/core/intensity_canonical_loglink.py`):

$$\log \lambda_H = \alpha + \gamma + A_H - D_A + C_H$$

$$\log \mu_A = \alpha + A_A - D_H + C_A$$

**Lectura de los términos:**

| Término | Significado | Dominio |
|---|---|---|
| $\alpha$ | **Ligadura estructural de masa** de la competición | $\alpha = \ln(\mu_{\text{liga}}) - \ln\left(1 + e^{\gamma}\right)$ |
| $\gamma$ | Intercepto de localía contextual | $\gamma = \bar{\gamma}_{\text{base}} + \Delta\gamma_{\text{plaza}} + 0.03\cdot\frac{\Delta\text{Alt}}{1000} + 0.02\cdot\text{clamp}(\Delta\text{Días}, -3, +3)$ |
| $A_H, A_A$ | Potencial **ofensivo** normalizado (log-ratio) | $\ln\!\left(\dfrac{0.65\cdot xG + 0.35\cdot GF}{\mu_{\text{liga}}/2}\right)$ |
| $D_A, D_H$ | Resistencia **defensiva** normalizada (log-ratio) | $-\ln\!\left(\dfrac{0.65\cdot xGA + 0.35\cdot GC}{\mu_{\text{liga}}/2}\right)$ |
| $C_H, C_A$ | Shock contextual de plantilla | $C = \ln(Q_{\text{mod}})$, con $Q_{\text{mod}} \in [0.90, 1.05]$ |

**Amortiguación hiperbólica obligatoria (anti-resonancia).** Antes de entrar en la ecuación, todo factor
log-diferencial se comprime con una tangente hiperbólica pura de escala absoluta:

$$A^{*} = \kappa_{\text{net}} \cdot \tanh\!\left(\frac{A^{\text{crudo}}}{\kappa_{\text{net}}}\right), \qquad \kappa_{\text{net}} = 0.2500$$

Esto preserva $\mathbb{E}[A] = 0$ por imparidad estricta y acota asintóticamente $|A^{*}| < \kappa_{\text{net}}$,
**garantizando que la adición de variables al catálogo jamás expanda la escala de goles de la liga**.
La escalera histórica $\kappa = 2.5\cdot\sigma_{\text{liga}}$ está **DEROGADA** (`VAR-2026-LIVE-AUDIT-J11`/V-2).

**Contracción bayesiana de forma reciente (10 partidos, `[LN-QBE-036]`).** El factor crudo no es la señal
reciente pura ni el ancla macro pura, sino una contracción convexa:

$$A_i^{*} = (1 - \rho)\cdot A_{\text{reciente}} + \rho\cdot A_{\text{macro}}, \qquad
\rho = \begin{cases} 0.30 & \text{si } Q_{\text{mod}} \ne 1.00 \text{ (shock verificado)} \\ 0.55 & \text{si } Q_{\text{mod}} = 1.00 \text{ (estabilidad)} \end{cases}$$

**Modulación H2H con decaimiento temporal (`[LN-QBE-020]`).** La mezcla de enfrentamientos directos
históricos pondera por vida media de 180 días:

$$w_{\text{H2H}} = \max\!\left(w^{\text{piso}},\; w^{\text{amp}} \cdot e^{-\kappa_{\text{decay}}\Delta t}\right), \qquad
\kappa_{\text{decay}} = \frac{\ln 2}{180} \approx 0.00385098\ \text{días}^{-1}$$
$$w^{\text{amp}} = 0.5000, \qquad w^{\text{piso}} = 0.1500$$

**Suficiencia fáctica $S(\mathcal{I}_i)$ (`[LN-QBE-035-B]`).** El motor exige $PJ \ge 3$ en ambos clubes y
$SoT > 0$. Si $S(\mathcal{I}_i) = 0$, la distribución colapsa al prior de ignorancia uniforme
$(1/3, 1/3, 1/3)$ y el partido se rotula **Cold Start** (`[LN-QBE-100]`): jamás se fabrica un factor.

**Cierres numéricos (invariantes).** Positividad estricta acotada
$\lambda \in [0.15, 4.50]$; matriz bivariada evaluada sobre el **retículo truncado $[0,5]$** (matriz $6\times 6$)
y **renormalizada** para conservar la masa unitaria.

## 1.2. Motor GSL-3D — Ortogonalización Residual de Gram-Schmidt (`[LN-QBE-039]`)

Nodo lógico: **`[LN-QBE-039]` Motor de Ortogonalización Residual y Factores Latentes
Tridimensionales (GSL-3D)** · Contenedor arquitectónico: **`[ARCH-1.4.33]`** ·
Implementación: `src/core/sovereign/orthogonal_factor_engine.py` (función pura en $O(m)$, con $m \le 44$).

**Ω (Objetivo).** Marco matemático de contención y gobernanza universal para las **44 variables del
catálogo**. Descompone la evidencia en **tres espacios de Hilbert cerrados e independientes**, aísla
únicamente el **residuo ortogonal** de cada señal secundaria frente a la señal directora, e impone un
presupuesto de norma cerrado. Su propósito físico es **erradicar la doble contabilización** y la
resonancia exponencial destructiva.

$$\mathbb{H}_{\text{att}} \ \text{(Ofensiva)} \qquad \mathbb{H}_{\text{def}} \ \text{(Defensiva)} \qquad \mathbb{H}_{\text{ctx}} \ \text{(Contextual)}$$

**Paso 1 — Aislamiento dimensional estricto.** Toda variable pertenece a **exactamente uno** de los tres
espacios. Queda prohibida la contaminación cruzada (cero señales defensivas en el vector de ataque).

**Paso 2 — Extracción residual de Gram-Schmidt por dimensión.** Para cada variable secundaria $X_k$ del
espacio $\mathbb{H}$, su entrada está condicionada a su residuo ortogonal respecto del subespacio ya
cubierto $U_{k-1} = \text{span}(u_1, \dots, u_{k-1})$:

$$v_k^{\perp} = X_k - \sum_{j=1}^{k-1} \frac{\langle X_k, u_j \rangle}{\langle u_j, u_j \rangle}\, u_j \;=\; X_k - \text{Proj}_{U_{k-1}}(X_k)$$

$$u_k = \frac{v_k^{\perp}}{\|v_k^{\perp}\|} \ \text{ si } \ \|v_k^{\perp}\| > \varepsilon_{\text{ort}}, \quad \text{en caso contrario } u_k = 0$$

*Teorema de No-Redundancia:* por construcción $\langle u_j, v_k^{\perp} \rangle = 0 \ \ \forall j < k$.
Tolerancia de singularidad ortogonal: $\varepsilon_{\text{ort}} = 1\times 10^{-5}$.

**Paso 3 — Absorción fiduciaria del desempeño de sede (el des-solapamiento).** La producción en sede
$X_{\text{sede}}$ (p. ej. goles en casa) solo inyecta su residuo **no explicado** por la calidad general
de plantilla ($u_1 = xG$):

* Un club modesto con récord extraordinario en casa tiene $u_1$ media $\Rightarrow$ $v_{\text{sede}}^{\perp}$ alto y positivo: se acredita la fuerza legítima de la plaza.
* Un superlíder ya tiene su rendimiento en casa prácticamente explicado por $u_1$ ($X_{\text{sede}} \approx u_1$) $\Rightarrow$ $v_{\text{sede}}^{\perp} \approx 0$: se anula el doble cobro y el factor no se dispara.

> **Axioma de Asimetría de Sede** (Decreto `VAR-2026-GSL3D-1D-DEGENERACY`): el residuo ortogonal de sede
> $v_{\text{sede}}^{\perp}$ se extrae y aplica **EXCLUSIVAMENTE al club anfitrión (local)**. El visitante
> conserva su evaluación estructural basal (`[LN-QBE-035-B]`), impidiendo que su fragilidad foránea infle
> artificialmente $\lambda_H$ vía $D_A^{*}$.

**Paso 4 — Presupuesto cerrado de escala y varianza unitaria.** Los factores latentes finales se
sintetizan bajo compresión hiperbólica, con presupuesto normado $\sum |w_j| \le 1.0000$:

$$\mathcal{A}^{*} = \tanh\!\left(\sum_{j=1}^{m_{\text{att}}} w_j u_j\right), \qquad
\mathcal{D}^{*} = \tanh\!\left(\sum_{j=1}^{m_{\text{def}}} w_j u_j\right)$$

$$\|\mathcal{A}^{*}\|_{\max} = 1.0000, \qquad \|\mathcal{D}^{*}\|_{\max} = 1.0000, \qquad \|\mathcal{C}^{*}\|_{\max} = 0.2500$$

**O (Output):** `FactoresGSL3D(A_star, D_star, C_star, residuos_auditables)`.
**Φ (Transición):** hacia `estimar_intensidades_loglineal` (`[VAULT-CORE-001]`) y `[LN-QBE-040]`.
**Juez sellado:** `tests/shield/test_shield_gsl3d_orthogonal_engine.py`.


## 1.3. Corrección de Dixon-Coles ($\tau$) aplicada a los 4 marcadores bajos

La matriz bivariada de Poisson pura **subestima estructuralmente los empates de baja anotación** por el
truncamiento del retículo $[0,5]$. Q-BE aplica la corrección de dependencia de Dixon-Coles sobre
**exactamente 4 vértices** ($\tau \equiv 1.0000$ en el resto del retículo, de modo que la Poisson pura
permanece intacta), con cotas analíticas de admisibilidad (§5.16.1) que garantizan el **Teorema de
No-Negatividad Estricta (Invariante I13, $\tau(x,y) \ge 0$)**:

$$P(X=x, Y=y) = \frac{\lambda_H^{x} e^{-\lambda_H}}{x!}\cdot\frac{\mu_A^{y} e^{-\mu_A}}{y!}\cdot \tau(x,y)$$

$$\tau(x,y) = \begin{cases}
1.0 - \lambda_H \mu_A \rho_{\text{adm}} & (x,y) = (0,0)\\
1.0 + \lambda_H \rho_{\text{adm}} & (x,y) = (0,1)\\
1.0 + \mu_A \rho_{\text{adm}} & (x,y) = (1,0)\\
1.0 - \rho_{\text{adm}} & (x,y) = (1,1)\\
1.0 & \text{en cualquier otro caso}
\end{cases}$$

con la admisibilidad de $\rho$ acotada por:

$$\rho_{\text{adm}} = \max\!\left(\;-\min\!\left(\frac{1}{\lambda_H}, \frac{1}{\mu_A}\right),\;\; \min\!\left(1,\; \frac{1}{\lambda_H \mu_A}\right),\;\; \rho \;\right)$$

**Calibración táctica dinámica vigente (`[LN-QBE-040-C]`).** El parámetro $\rho$ **deja de ser una
constante de diseño y pasa a ser función del régimen de anotación proyectado**:

$$\rho_{\text{efectivo}}(\lambda_H, \lambda_A) = \begin{cases}
\rho_{\text{base}} = -0.0500 & \text{si } \lambda_H + \lambda_A > 2.6500 \text{ xG} \quad \text{(partido abierto)}\\
\rho_{\text{táctica}} = -0.1200 & \text{si } \lambda_H + \lambda_A \le 2.6500 \text{ xG} \quad \text{(partido cerrado)}
\end{cases}$$

* **Frontera de conmutación:** $\Sigma_{\text{corte}} = 2.6500$ xG (coincide con el $\mu_{\text{liga}}$ canónico de Liga MX; la frontera pertenece a la rama táctica por el $\le$).
* **Sentido físico del signo:** con la convención $\tau$ sellada, $\rho < 0$ **eleva** $\tau(0,0)$ y $\tau(1,1)$ y **deprime** $\tau(0,1)$/$\tau(1,0)$: esto concentra masa fiduciaria en los vértices de empate de baja anotación $(0,0)$ y $(1,1)$.
* **Cláusula de invocación obligatoria:** todo cómputo de la matriz bivariada que NO reciba un $\rho$ explícito distinto del default sellado **DEBE** resolver su correlación con `resolver_rho_dixon_coles(lambda_h, lambda_a)`. Un $\rho = 0.0000$ explícito es el *escape hatch* de auditoría (matriz de Poisson pura, sin corrección Dixon-Coles).
* Tras la corrección, la matriz se **renormaliza** sobre el retículo $[0,5]$ y se colapsa geométricamente al símplex $\Delta^2$, produciendo el vector fiduciario $P' = (p_1', p_X', p_2')$ que se persiste (tabla 3NF `sovereign_distributions`) y se compara contra el mercado.

**Juez sellado:** `tests/shield/test_shield_rho_tactico_calibration.py`.


## 1.4. Métrica de evaluación: Brier Score Multicategórico 1X2

Nodo lógico **`[LN-QBE-100]`** (Motor de Calibración Factual de Temporada). Régimen de **solo lectura**:
evalúa la concordancia empírica entre las distribuciones soberanas ($P'$ fiduciaria / $\hat{P}$) y los
resultados reales consumados. **No usa log-loss ni accuracy binaria**: la métrica canónica es el Brier
multicategórico con normalización $1/(3N)$ sobre las tres casillas del símplex 1X2:

$$BS_{\text{QBE}} = \frac{1}{3N} \sum_{i=1}^{N} \sum_{k \in \{1, X, 2\}} \left( \hat{p}_{i,k} - y_{i,k} \right)^{2}$$

$$BS_{\text{MKT}} = \frac{1}{3N} \sum_{i=1}^{N} \sum_{k \in \{1, X, 2\}} \left( q^{\text{mkt}}_{i,k} - y_{i,k} \right)^{2}$$

$$\text{Alpha de Calibración} = \left( 1.0 - \frac{BS_{\text{QBE}}}{BS_{\text{MKT}}} \right) \times 100$$

donde $y_{i,k} \in \{0,1\}$ es el indicador *one-hot* del desenlace real y $q^{\text{mkt}}$ es el
**consenso des-marginado (vig-free)** del mercado de cierre, obtenido por descuento proporcional del
margen comercial sobre el símplex $\Delta^2$:

$$q_k = \frac{1/O_k}{\sum_{j \in \{L,E,V\}} 1/O_j}$$

**Frontera de comparación exigida.** El benchmark del investigador es el **mercado de cierre vig-free**
($BS_{\text{MKT}}$ sobre las cuotas de cierre congeladas en el snapshot). Alpha $> 0$ significa error
cuadrático menor que el mercado (ventaja estocástica); Alpha $< 0$ significa que el mercado gana.

**Axioma del Prior de Mercado (Cold Start Resolution).** Todo partido con ignorancia fáctica
$S(\mathcal{I}) = 0$ sustituye retrospectivamente su vector por $q^{\text{mkt}}$ antes de clasificar, de
modo que aporta exactamente $BS_{\text{QBE}} \equiv BS_{\text{MKT}}$ y $\text{Alpha} \equiv 0.00\%$ por
identidad de vectores (evita que "basura estadística" degrade artificialmente la métrica global).

**Jerarquía estocástica de vértices.** Para cada partido, los desenlaces se ordenan estrictamente por
probabilidad fiduciaria descendente ($P_{\max} \ge P_{\text{mid}} \ge P_{\text{low}}$), definiendo la
tríada de vértices:

* $P_{\max}$ — vértice primario de masa (máxima convicción) $\Rightarrow$ **Tasa de Acierto Primario**.
* $P_{\text{mid}}$ — vértice secundario de apoyo $\Rightarrow$ **Tasa de Rescate Secundario** (desglosada en empate vs rival; jamás es "el empate" por definición).
* $P_{\text{low}}$ — vértice residual de riesgo $\Rightarrow$ **Tasa de Ruptura Residual**.
* **Masa de Cobertura** $= \%P_{\max} + \%P_{\text{mid}} = 100\% - \%P_{\text{low}}$.

**Jueces sellados:** `tests/shield/test_shield_visor_backtesting.py` ·
`tests/shield/test_shield_visor_backtesting_cold_start.py`.

## 1.5. Libro de constantes operativas vigentes

Transcripción de las constantes que gobiernan el motor (fuente canónica: `docs/CONSTANTS.md`; valores
**inmutables**, prohibido alterarlos o reutilizarlos fuera de su dominio legislado):

| Símbolo | Valor exacto | Unidad | Nodo dueño |
|---|:---:|:---:|:---:|
| $\mu_{\text{liga}}$ (Media Goles Liga MX) | `2.6500` | Goles / 90' | `[LN-QBE-089]` |
| $\bar{\gamma}_{\text{home}}$ (Ventaja Media Incondicional) | `0.1500` | Log-Ratio | `[VAULT-CORE-001]` |
| $\kappa_{\text{net}}$ (Techo de Compresión $\tanh$, ABSOLUTO) | `0.2500` | Adimensional | `[VAULT-CORE-001]` |
| Techo del bono de plaza $\Delta\gamma_{\text{plaza}}^{\max}$ | `0.1000` | Log-Ratio | `[LN-QBE-038]` |
| $\text{peso}_{xG}$ / $\text{peso}_{GF}$ | `0.6500` / `0.3500` | Fracción | `[LN-QBE-035-B]` |
| $\rho_{\text{estable}}$ / $\rho_{\text{shock}}$ (ancla macro) | `0.5500` / `0.3000` | Fracción | `[LN-QBE-036]` |
| $N_{\text{forma}}$ (ventana de forma reciente) | `10` | Partidos | `[LN-QBE-036]` |
| $\tau_{\text{H2H}}$ (vida media H2H) / $\kappa_{\text{decay}}$ | `180.0` / `0.00385098` | Días / $\text{días}^{-1}$ | `[LN-QBE-020]` |
| $w_{\text{H2H}}^{\text{amp}}$ / $w_{\text{H2H}}^{\text{piso}}$ | `0.5000` / `0.1500` | Adimensional | `[LN-QBE-040]` |
| $\varepsilon_{\text{ort}}$ (tolerancia de singularidad ortogonal) | `1e-5` | Adimensional | `[LN-QBE-039]` |
| $\|\mathcal{A}^{*}\|_{\max}$ / $\|\mathcal{D}^{*}\|_{\max}$ / $\|\mathcal{C}^{*}\|_{\max}$ | `1.0000` / `1.0000` / `0.2500` | Desv. Estándar | `[LN-QBE-039]` |
| $\rho_{\text{base}}$ (partidos abiertos) | `-0.0500` | Adimensional | `[LN-QBE-040-C]` |
| $\rho_{\text{táctica}}$ (partidos cerrados) | `-0.1200` | Adimensional | `[LN-QBE-040-C]` |
| $\Sigma_{\text{corte}}$ (frontera de conmutación de $\rho$) | `2.6500` | xG | `[LN-QBE-040-C]` |
| $\Delta P_{\text{paridad}}$ (cota de dispersión mínima) | `0.1200` (12%) | Fracción | `[LN-QBE-060-C]` |
| $P_{\max}^{\min}$ (piso de masa del favorito) | `0.3800` (38%) | Fracción | `[LN-QBE-060-C]` |
| $\sum \lambda_{\text{fuego}}$ (techo de goles combinados) | `3.0000` | xG | `[LN-QBE-060-C]` |
| $p_{X,\text{fuego}}^{\max}$ (asfixia de empate) | `0.2200` (22%) | Fracción | `[LN-QBE-060-C]` |
| $\Gamma_{\text{base}}$ (umbral maestro de masa base) | `0.6700` (67%) | Probabilidad | `[LN-QBE-059]` |
| Cotas de positividad de intensidad | $[0.15,\ 4.50]$ | Goles | Invariante I6 |
| Retículo de evaluación bivariada | $[0,5]$ ($6\times 6$, renormalizado) | Goles | `[VAULT-CORE-004]` |


---

# SECCIÓN 2 — LÍNEA BASE Y AUTOPSIA FACTUAL ACTUAL

## 2.0. Alcance y provenance de la evidencia

* **Universo auditado:** **97 partidos consumados** (Liga MX, Jornadas 1–11) con 99 fixtures homologados y persistidos en 3NF. El oráculo del marcador consumado es la tabla `matches`; las capturas de cuotas de cierre y $P'$ viven en `fixtures_snapshots` (con respaldo en `sovereign_distributions`).
* **Instrumentos (tres, todos de solo lectura, régimen `[DBBD-FUNGIBLE]`):**
  * `python -m scripts.auditoria.analizar_autopsia_rupturas_plow` $\Rightarrow$ autopsia forense de las rupturas residuales $P_{\text{low}}$ y de la tríada $P_{\max}/P_{\text{mid}}/P_{\text{low}}$.
  * `python scripts/auditoria/auditar_pipeline_end_to_end_backtesting.py` $\Rightarrow$ paridad 3NF ↔ captura y Alpha global de temporada contra el mercado de cierre vig-free.
  * `python -m scripts.auditoria.auditar_coherencia_cartelera --check` $\Rightarrow$ Pre-Vuelo Diagnóstico de Cartelera (`[ARCH-1.4.34]`) **re-ejecutado en esta pasada** sobre la cartelera activa (Jornada 12): `EXIT CODE 0`, **cero discrepancias estructurales 🔴** (9 partidos en banda de vigilancia 🟡, 0 🔴, 18 sondas ⚪ por evidencia parcial no publicada). El dato vivo de la temporada activa no presenta rupturas axiomáticas.
* **Fecha de medición:** 2026-10-16 (`HEAD` = `e1be553`, cero commits). Las cifras de esta sección fueron **re-ejecutadas y verificadas** sobre el árbol vivo; **cero cifras fabricadas**.
* **Contexto de calibración:** la medición incorpora la rectificación de unidad de $xG$ (`VAR-2026-10-16-ESCALA-XG`), que extirpó un *shim* de doble unidad y re-selló 17 capturas en temporada temprana.

## 2.1. Masa de Cobertura Base: **67.01%**

| Métrica | Valor verificado | Nota |
|---|:---:|---|
| Partidos auditados | `97` | Jornadas 1–11 |
| Partidos cubiertos ($P_{\max}$ o $P_{\text{mid}}$) | `65 de 97` | $65/97 = 67.01\%$ |
| **Masa de Cobertura Base** | **`67.01%`** | $= \%P_{\max} + \%P_{\text{mid}} = 100\% - \%P_{\text{low}}$ |
| Tasa de Acierto Primario ($P_{\max}$) | `38.14%` | 37 partidos |
| Tasa de Rescate Secundario ($P_{\text{mid}}$) | `28.87%` | 28 partidos = 9 con Empate · 19 con Rival |
| Tasa de Ruptura Residual ($P_{\text{low}}$) | `32.99%` | **32 partidos** (fallos) |
| Censo factual de desenlaces | `38 L · 26 E · 33 V` | victorias locales / empates / victorias visitantes |

**Lectura fiduciaria.** De cada 100 partidos, Q-BE "controla" 67 y falla 33. El fallo no es simétrico: el
empate es el enemigo estructural del sistema (ver §2.3), coherente con que $P_{\text{mid}}$ se desvincule
del empate por diseño (`[LN-QBE-100]`) y con la calibración $\rho$ táctica de `[LN-QBE-040-C]`.

## 2.2. Alpha Global: **−2.14%** (el mercado nos gana por un margen estrecho)

| Métrica | Valor verificado |
|---|:---:|
| $BS_{\text{QBE}}$ (Brier multicategórico, $1/(3N)$) | `0.2191` |
| $BS_{\text{MKT}}$ (mercado de cierre vig-free) | `0.2145` |
| Diferencia absoluta | `+0.0046` de error cuadrático medio por casilla frente al mercado |
| **Alpha de Calibración global** | **`−2.14%`** |
| Partidos en Cold Start $S(\mathcal{I}) = 0$ | `27` (J1: 9 · J2: 9 · J3: 9) |
| Partidos pendientes de captura $P'$ | `0` |

**Lectura fiduciaria.** El Alpha global negativo es **estrecho** (≈2.1% de error relativo): el motor no está
destruido, está **empatado con la eficiencia del mercado** en un rango donde la varianza domina la señal.
Los 27 partidos de Cold Start aportan, por axioma, $BS_{\text{QBE}} \equiv BS_{\text{MKT}}$ y
$\text{Alpha} \equiv 0.00\%$; por tanto **el déficit real se concentra en los 70 partidos donde el modelo
operó con evidencia**. Ese es exactamente el universo donde una mejora de *feature engineering* tiene
sentido económico.

> **Provenance de la línea base (para no confundir censos):** el censo del 2026-10-14 (previo a la
> rectificación de escala de $xG$) reportaba $BS_{\text{QBE}} = 0.2169$ / $BS_{\text{MKT}} = 0.2145$
> $\Rightarrow$ Alpha $= −1.12\%$ sobre el mismo universo de 97 partidos. La cifra **vigente y única**
> para esta investigación es la de la tabla anterior: **`0.2191 / 0.2145 ⇒ −2.14%`**.


## 2.3. Los 5 arquetipos de ruptura actuales

La autopsia clasifica **por qué** fallan los 32 partidos que el motor no cubrió. Cinco arquetipos
exploran hoy el espacio de fuga:

| # | Arquetipo | Firma operativa | Estado |
|---|---|---|---|
| 1 | **Falsa Paridad** | $\Delta P = P_{\max} - P_{\text{low}} \le 12\%$ con $P_{\max} \le 38\%$: alta entropía, ausencia total de convicción direccional | **Veto formal** `[LN-QBE-060-C]` $\Rightarrow$ colapso a `QBE-00` con `arquetipo_veto = FALSA_PARIDAD` |
| 2 | **Bipolar de Fuego** | $\Sigma xG = \lambda_H + \mu_A \ge 3.0$ con empate asfixiado ($p_X' \le 22\%$) y $P_{\max} < 50\%$: intercambio desmedido de goles | **Veto formal** `[LN-QBE-060-C]` $\Rightarrow$ colapso a `QBE-00` con `arquetipo_veto = BIPOLAR_FUEGO` |
| 3 | **Golpe al Gigante** | $P_{\max} > 50\%$: el favorito de Q-BE cae pese a portar mayoría absoluta de masa fiduciaria | Arquetipo **diagnóstico** (aún sin veto codificado) |
| 4 | **Empate Táctico no Detectado** | El empate ocurre pero el modelo lo rankeó en $P_{\text{low}}$ (tercer lugar) | Arquetipo **diagnóstico**; **falla dominante del sistema** |
| 5 | **Ruptura Foránea** | La victoria del visitante ocurre donde el modelo no la evaluó como desenlace primario ni secundario | Arquetipo **diagnóstico**; hipótesis estructural asociada: asimetría de sede (ver nota) |

> **Nota de frontera (honestidad de definición, `[GOVERNANCE-01]`).** Los arquetipos 1 y 2 están
> **legislados con umbrales numéricos** en `[LN-QBE-060-C]` y ejecutados en
> `src/core/contracts/portfolio_math.py`. Los arquetipos 3, 4 y 5 son **etiquetas forenses de la
> autopsia**: su firma factual se documenta abajo con datos duros, pero **no existe aún un umbral
> canónico sellado** para ellos. Formalizar (o refutar) esos umbrales es parte natural del trabajo de
> selección de características.

**Anatomía verificada de las 32 rupturas (J1–J11):**

| Corte | Valor verificado |
|---|:---:|
| Rupturas por **Empate** | **17 de 32 (53.1%)** |
| Rupturas por **Victoria visitante** | 10 de 32 (31.3%) |
| Rupturas por **Victoria local** | 5 de 32 (15.6%) |
| **Empates consumados que terminaron en ruptura** | **17 de 26 (≈65.5%)** — es decir, **el 65.5% de nuestros empates son rupturas**; solo 9 empates fueron rescatados por $P_{\text{mid}}$ ($9^{\text{Emp}} \cdot 19^{\text{Riv}}$) |
| Rupturas con $P_{\max} > 50\%$ (Golpe al Gigante) | 10 de 32 (31.3%): 7 vía visitante · 1 vía local · 2 vía empate |
| Rupturas que el **mercado tampoco** capturó | 30 de 32 (**93.8%** son "sorpresas para todos": el casino falló el mismo partido) |
| Rupturas sin captura factual de cuotas (excluidas del cruce) | **0** (cero cuotas inventadas) |

**Conclusión de la anatomía.** $\approx 9$ de cada 10 rupturas son eventos que **el mercado también falló**:
el sistema no está perdiendo contra el mercado en *esos* partidos, sino compartiendo su ceguera. La fuga
de valor real está en (i) el **empate táctico no detectado** (arquetipo dominante) y (ii) la
**distribución de cola** de los partidos de alta entropía.

## 2.4. Impacto verificado del Veto Inteligente Anti-Ruptura (`[LN-QBE-060-C]`)

| Métrica | Valor verificado |
|---|:---:|
| Rupturas interceptadas por **Falsa Paridad** ($\Delta P \le 12\%$) | `3` |
| Rupturas interceptadas por **Bipolar de Fuego** ($\Sigma xG \ge 3.0$) | `2` |
| **Total de rupturas eliminables de la cartera** | **`5 de 32`** |
| Cobertura Base (sin veto) | `67.01%` |
| **Cobertura real con veto activo** | **`70.65%`** (sobre `92` partidos operables) |

*Mecánica del veto:* el partido vetado **no se opera**; colapsa a la estrategia de abstención `QBE-00` con
traza auditable (`arquetipo_veto`). El veto no "acierta" el partido: **lo saca del balance**, de modo que
la cobertura se mide sobre el subconjunto de partidos que el sistema sí decidió jugar. Este es el
precedente metodológico más importante para el Data Scientist: **abstenerse es una acción con valor
medible** y el *feature selection* debe identificar cuándo el modelo no sabe (arquetipos), no solo
empujar la probabilidad.

## 2.5. Limitaciones fácticas declaradas (insumo obligatorio para el investigador)

1. **Series $xG$ por partido no disponibles en la fuente de liga:** la fuente verificada (FotMob/Opta) publica **agregados estacionales por club**, no series partido a partido. Queda prohibido etiquetar agregados de temporada como ventana "10P". Las derivaciones $xG/xGA$ del sensor permanecen **congeladas** hasta Enmienda al Vault.
2. **Kernel H2H sin fuente de datos cableada:** el streaming de forma 10P de alta frecuencia y las consultas granulares H2H quedan catalogados como capacidades de Fase 6.
3. **Cold Start inevitable en temporada temprana:** con $PJ < 3$ el motor publica ignorancia uniforme $(1/3,1/3,1/3)$ y Alpha $\equiv 0$; 27 de los 97 partidos pertenecen a esta clase.
4. **Muestra de 97 partidos:** la varianza del Brier sobre 97 eventos es del orden de la ventaja buscada. Cualquier conclusión de "Alpha significativo" exige el dataset histórico ampliado que aportará el investigador y una prueba de significancia estadística explícita.


---

# SECCIÓN 3 — EL CATÁLOGO DE LAS 44 VARIABLES CANDIDATAS

Este es el **catálogo normativo de 44 variables candidatas** que el Data Scientist debe evaluar mediante
*Feature Selection* (Elastic-Net / SHAP). Reglas de gobernanza del catálogo:

* Toda variable del catálogo entra al motor **exclusivamente** dentro del contenedor GSL-3D (`[ARCH-1.4.33]`, `[LN-QBE-039]`): "toda adición o suspensión de variables en el catálogo de 44 se ejecuta exclusivamente dentro de este contenedor", con presupuesto cerrado $\sum |w_j| \le 1.0000$ y compresión $\tanh$.
* Cada variable debe asignarse a **exactamente uno** de los tres espacios de Hilbert: $\mathbb{H}_{\text{att}}$ (ofensiva), $\mathbb{H}_{\text{def}}$ (defensiva) o $\mathbb{H}_{\text{ctx}}$ (contextual). Prohibida la contaminación cruzada.
* La señal directora de cada espacio es $xG$ por 90' (ataque) y $xGA$ por 90' (defensa); toda variable secundaria entra **solo por su residuo ortogonal** (Gram-Schmidt), para impedir la doble contabilización.
* En producción, el vector homólogo homologado porta hoy los agregados Opta por club ($xG$, $GF$, $GC$) y los *splits* de sede; el resto del catálogo es espacio de investigación declarado.

## Volumen Territorial
1. Posesión efectiva (%)
2. Toques en área rival (opp_box_touches)
3. Pases progresivos completados
4. Entradas al último tercio (final_third_entries)

## Calidad de Remate
5. xG no penal (npxG)
6. Tiros a puerta (SoT)
7. xG a puerta (xGOT)
8. Grandes oportunidades creadas (BC_creat)
9. Grandes oportunidades falladas (BC_missed)

## Defensa
10. xG concedido (xGA)
11. Tiros a puerta concedidos (SoTA)
12. PPDA (Pases permitidos por acción defensiva)
13. Intercepciones y recuperaciones en tercio medio
14. Grandes oportunidades concedidas (BC_conceded)

## Portería
15. Goles prevenidos (xGOT - GC)
16. Porcentaje de atajadas (Save %)
17. Salidas exitosas por alto

## Balón Parado y Penales
18. xG a balón parado (xG_setpiece)
19. xGA a balón parado (xGA_setpiece)
20. Tiros de esquina a favor
21. Tasa histórica de penales a favor

## Disciplina
22. Faltas cometidas en tercio defensivo
23. Tarjetas amarillas promedio
24. Índice de riesgo de expulsión / rojas previas

## Shocks de Plantilla/Contexto
25. Impacto xG de bajas críticas ofensivas
26. Impacto xGA de bajas críticas defensivas
27. Diferencial de descanso (ΔDías)
28. Factor de altitud fisiológica (ΔAltitud+)

## Trayectoria
29. Diferencial de puntos recientes (forma 5 partidos)
30. Pendiente/evolución de xG
31. Pendiente/evolución de xGA
32. Diferencial de puntos esperados (xPTS)

## Cronometría
33. Ratio xG generado 1T vs 2T
34. Ratio xGA concedido 1T vs 2T
35. Tasa de goles tempraneros anotados (min 0–15)
36. Tasa de goles tempraneros concedidos (min 0–15)

## Banca/Profundidad
37. Impacto xG promedio de suplentes
38. Índice de rotación del XI titular

## Memoria Longitudinal/H2H
39. Victorias en los últimos cinco H2H
40. Diferencial de goles en H2H reciente
41. Resistencia del visitante en esa sede
42. xG promedio a favor en H2H

## Cierre de Partido
43. xG generado en minutos 80–90+
44. xGA concedido en minutos 80–90+

---

# SECCIÓN 4 — MANDATO PARA EL DATA SCIENTIST

La misión del investigador es utilizar un dataset histórico (provisto externamente) para aplicar modelos
duales de Poisson (regularizados con Elastic-Net o Gradient Boosting) sobre estas 44 variables. El
objetivo es identificar el subconjunto dorado (*Golden Dataset*) que logre aislar señal pura del ruido,
superar el Brier Score del mercado de cierre (vig-free) y determinar si la distribución Q-BE puede
generar un Alpha matemáticamente significativo.

**Criterio de aceptación del mandato (contraste contra la línea base de este dossier):**

| # | Criterio de éxito del investigador | Línea base a vencer |
|---|---|---|
| 1 | $BS_{\text{QBE}}$ del modelo dual de Poisson sobre el *Golden Dataset* | `< 0.2145` (mercado de cierre vig-free, 97 partidos J1–J11) |
| 2 | Alpha de Calibración multicategórico | `> 0.00%` (línea base vigente: **−2.14%**; $BS_{\text{QBE}} = 0.2191$) |
| 3 | Masa de Cobertura ($\%P_{\max} + \%P_{\text{mid}}$) | `> 67.01%` (línea base sin veto); objetivo declarado: `> 70.65%` (cobertura con veto activo) |
| 4 | Reducción de la ruptura por Empate Táctico no Detectado | `< 17` rupturas y `< 65.5%` de los empates consumados |
| 5 | Significancia estadística del Alpha | prueba explícita de significancia sobre la ventana out-of-sample (la muestra de 97 partidos es insuficiente por sí sola) |
| 6 | Trazabilidad de la fuga | Reportar residuos/coeficientes en el espacio de los 3 factores latentes ($\mathcal{A}^*, \mathcal{D}^*, \mathcal{C}^*$), no solo métricas de caja negra |

**Frontera de gobernanza del hallazgo.** Un *Golden Dataset* aprobado no modifica el motor: la
integración de variables nuevas al pipeline productivo requiere acto formal bajo `[ARCH-1.4.33]`
(contenedor GSL-3D) y re-certificación numérica de su Juez Sellado. El investigador entrega **evidencia**;
el Director y el Arquitecto legislan la **materialización**.

---

> **FIN DEL DOSSIER.** Documento compilado el 2026-10-16 por el Agente Constructor Kybern v12.0 bajo
> régimen `[DBBD-FUNGIBLE]`. Cero diffs en `src/`, cero escrituras a base de datos, cero commits.
> Fuentes consolidadas: `docs/LOGIC.md`, `docs/CONSTANTS.md`, `docs/DIRGEN_VAULT.md`, `docs/ARCH.md`,
> `docs/ID_REGISTRY.md` y la re-ejecución verificada de la autopsia forense sobre los 97 partidos.

