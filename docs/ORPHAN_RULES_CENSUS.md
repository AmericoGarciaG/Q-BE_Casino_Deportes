# 🕵️ CENSO DE REGLAS HUÉRFANAS (ORPHAN RULES CENSUS)

**Documento:** Auditoría Estática de Gobernanza — Protocolo C.2 (Arqueología de Gobierno / Reconciliación Inversa)
**Régimen:** `[HÍBRIDO DUAL-TRACK]` — `[DIRGEN-STRICT]` (Core / Fórmulas / Vault) · `[DBBD-FUNGIBLE]` (Rutas / UI / Docs)
**Ruta SDLC:** `SDLC-04 Feature Injection`
**Fecha de emisión:** 2026-10-08
**Autoridad Suprema:** Américo García Guerrero (Director Humano)
**Emisor del dictamen de saneamiento:** Agente Arquitecto de Sistema (Custodio de la Base de Gobierno)
**Ejecutor:** Agente Constructor Kybern v12.0
**Estado:** `[SELLADO]` — documento oficial e inmutable de la Base de Gobierno
**Alcance:** auditoría **estática y de solo lectura** de `src/` contra la Base de Gobierno (`docs/LOGIC.md`, `docs/ARCH.md`, `docs/CONSTANTS.md`, `docs/DIRGEN_VAULT.md`, `docs/GOVERNANCE.md`, `docs/ID_REGISTRY.md`).

> **Objeto:** identificar toda lógica, constante o heurística presente en `src/` que **carezca de respaldo formal** (nodo sellado) en la Base de Gobierno, o que contradiga un parámetro promulgado.

---

## 1. Marco metodológico

| Fase | Contenido | Régimen |
|:--|:--|:--|
| Fase 1 | Censo estático (AST mining + verificación documental cruzada). Cero mutaciones del repositorio. | Auditoría |
| Fase 2 | Reconciliación inversa: se eleva cada huérfano a VARIANZA o a saneamiento quirúrgico. | Mixto |
| Fase 3 | Materialización del saneamiento + Bucle Reflexivo (The Shield). | Mixto |

**Regla de un solo intento:** ante rojo en un componente `[DIRGEN-STRICT]`, se emite `DIRGEN_VARIANCE_REQUEST.md` y se detiene la ejecución (sin ensayo-error autónomo).

---

## 2. Manifiesto de estado al iniciar el censo (evidencia de no-mutación)

```
 M docs/ARCH.md                   | 11 ++++-      ← PRE-EXISTENTE (no autoría del auditor)
 M docs/DESIGN.md                 | 25 ++++++++---
 M docs/DIRGEN_VAULT.md           | 123 +++++++++++++++++++++
 M docs/GOVERNANCE.md             |  2 +-
 M docs/ID_REGISTRY.md            | 14 +++---
 M docs/LOGIC.md                  | 13 ++++
   6 files changed, 174 insertions(+), 14 deletions(-)
M  src/core/simplex_morphology.py  | 2 +-         ← PRE-EXISTENTE (Γ 0.65 → 0.67, staged)
?? scratch/                                      ← PRE-EXISTENTE (no versionado)
HEAD = 3f8bc90 (main, origin/main)
```

El censo cita el **working copy** (incluido `docs/DIRGEN_VAULT.md` no commiteado). La Fase 1 introdujo **cero mutaciones**; los únicos artefactos escritos por el auditor fueron temporales fuera del repositorio.

---

## 3. Cerco negativo — literales CON respaldo verificado (NO huérfanos)

| Literal / lógica | Coordenada | Nodo de respaldo verificado |
|:--|:--|:--|
| Γ_base `0.67` | `portfolio_math.py:84`, `simplex_morphology.py:25` | `CONSTANTS.md` L48 `[LN-QBE-059]` |
| Γ_mid `0.70` / Γ_high `0.75` y slider `ge=0.67, le=0.75` | `src/web/routes/markets.py:144` | `CONSTANTS.md` L49-50; `ARCH.md` L1320-1322 `[ARCH-1.4.30]` |
| γ_Kelly `0.25`, Ψ cuadrática, τ_disp `0.12` | `portfolio_math.py:148,155-163` | `CONSTANTS.md` L47 `[LN-QBE-070-B]`; `ARCH.md` L309/L1170-1171 |
| Hard caps `0.0800 / 0.2500` | `portfolio_math.py:170-171,247-248` | `[LN-QBE-070-B]` / `[LN-QBE-070-E]` |
| Piso `$2.00 MXN` | `portfolio_math.py:39,249,279` | `[LN-QBE-071]`; `ARCH.md` L622 |
| Umbral difuso `0.78` + Levenshtein ≤ 2 | `normalizer.py:142-146` | `ARCH.md` L522 `[H10]`; `LOGIC.md` L79 |
| τ_H2H `180.0` / κ `ln2/180 = 0.00385098` | `temporal.py:15-16` | `CONSTANTS.md` L14-15 `[LN-QBE-020]` |
| Baricentro `1/3` (1/3, 1/3, 1/3) | `portfolio_math.py:324`; `progol_math.py:170-172`; `temporal.py:34` | `[LN-QBE-079]` / `[LN-QBE-020-B]` |
| Coberturas V=0, θ* = o/(o−1), Dutching, PA | `portfolio_math.py:14-36,55-81,184-208` | `[LN-QBE-007-C/050/070/070-B/073-B/077]` |
| Clamps FCF `[0.65,1.35]`, E_att `[0.60,1.40]`, GC `[0.05,6.00]`, Ω `[0.40,1.60]` | `models/analytics.py:23-37` | `LOGIC.md` L339-340; `ARCH.md` L1123 (`[ALGO-PROTECTED]`) |
| Guardas Femenil / Filial / Sub-20 | `src/normalization/gender_guards.py` | `[LN-QBE-095]` SELLADO (`ID_REGISTRY.md` L83); `ARCH.md` L1356-1360 |

---

## 4. Tabla de reglas huérfanas (código sin nodo de respaldo)

| ID | Coordenada (Fase 1) | Literal / lógica | Diagnóstico | Riesgo | Estado |
|:--|:--|:--|:--|:--|:--|
| **O-01** | `src/core/contracts/portfolio_math.py:129` (hoy L131) | `o_dnb = cuotas.get("DNB", o_fav * 0.75)` | Precio sintético fabricado para DNB. Ningún nodo promulga un proxy. `[LN-QBE-060-B]` legisla sólo la condición (α > 0.05). **Colisión:** `0.75` está sellado como `Γ_high` (`CONSTANTS.md` L50 `[LN-QBE-059]`) | **ALTO** — EV sobre precio inventado; QBE-C1 promovible sin cotización real | ✅ **SANEADO** (T3 src + Vault) |
| **O-02** | `src/core/poisson.py:57` (hoy L70) | `max(0.15, 0.50 * exp(-días/300.0))` | Mezcla H2H con constante de **300 d**, incompatible con `τ_H2H = 180.0` / `κ = ln2/180` sellados en `CONSTANTS.md` L14-15. La amplitud 0.50 y el piso 0.15 no eran promulgados | **ALTO** — λ/μ ⇒ matriz 6×6, P′, triaje y Kelly | ✅ **SANEADO** (T4 Opción B + promulgación en `CONSTANTS.md` §1) |
| **O-03** | `src/core/poisson.py:52` (hoy L63) | Centinela `>= 9000.0` | Discriminador de la Ley Zero-H2H implementado por convención no legislada; el predicado promulgado es `len(h2h)==0` (`[LN-QBE-020-B]`) | **MEDIO-ALTO** | ✅ **SANEADO** como constante nombrada `SENTINELA_ZERO_H2H_DIAS` con trazabilidad al canal contractual de `temporal.py:36` |
| **O-04** | `src/core/poisson.py:61-63` | `min(1.0, jornada/6.0)`; `(pts_pj/1.35)` | Saturación de madurez en J=6 y baseline de liga 1.35 sin nodo. **Colisión** con el clamp FCF `[0.65,1.35]` | **MEDIO** | ⏳ Abierto (Fase 2) |
| **O-05** | `src/core/evaluator.py:186-203` | ~13 fallbacks: cuotas `o_fav 2.5`, `o_emp 3.0`, `o_und 3.5`; `momio_sintetico_x2 1.60`; θ `0.40/0.30/0.35`; `q_mod 0.90`; `gc 1.5`; `psi_ruina 0.05`; `d_mkt 1.0` | Fabricación de cuotas de operador y umbrales no promulgados. `[LN-QBE-007-J]` legisla el prior de **distribución soberana**, no la invención de precios (viola el espíritu de `[GOVERNANCE-01]`) | **ALTO** | ⏳ Abierto (Fase 2) |
| **O-06** | `src/core/contracts/portfolio_math.py:274` (hoy L276) | `o_emp = float(ord_item.get("odd_emp", 3.30))` | Precio de empate por defecto usado para decidir el reescalado del piso $2.00 dentro de `[LN-QBE-070-E]` | **MEDIO-ALTO** | ⏳ Abierto (Fase 2) |
| **O-07** | `src/core/contracts/portfolio_math.py:323` (hoy L325) | `else 0.50` (QBE-C1 con denominador nulo) | Neutral no legislado; el único neutral promulgado es el baricentro 1/3 (`[LN-QBE-079]`) | **BAJO-MEDIO** | ⏳ Abierto (Fase 2) |
| **O-08** | `src/core/contracts/progol_math.py:200` | `p_conjunta *= probs[idx].get(signo, 0.3333)` | Relleno de masa faltante con 1/3 dentro de un producto de probabilidades conjuntas (trinidad $3^K$) | **MEDIO-ALTO** | ⏳ Abierto (Fase 2) |
| **O-09** | `src/ingestion/normalizer.py:128-130` y `:149` | `texto in alias or alias in texto`; `return str(team_name).strip()` | (a) Contención por subcadena **no** autorizada por `[H10]` (`ARCH.md` L522 / `LOGIC.md` L79: sólo igualdad exacta, `ratio ≥ 0.78` o Levenshtein ≤ 2). (b) Degradación silenciosa en lugar de invocar `NormalizationException` (contradice el texto sellado de H10) | **ALTO** | ⏳ Abierto (Fase 2) |
| **O-10** | `src/ingestion/progol_scraper.py` (bloque `[V-07]`) + `verify=False` | Carril XHR miloteria.mx + TLS sin verificar | Carril de ingesta no promulgado por nodo alguno; `verify=False` sin fundamento documental | **MEDIO-ALTO** | ⏳ Abierto (Fase 2) |
| **O-11** | `src/web/routes/markets.py:257-259` (hoy L259-261) | Prior fallback `(0.564, 0.258, 0.178)` | Segundo prior para la misma condición que el promulgado `(0.45, 0.28, 0.27)` de `[LN-QBE-007-J]` (`LOGIC.md` L154), declarado "residuo fuera de alcance" por el Juez | **ALTO** (dos priors contradictorios) | ✅ **SANEADO** (T5 — unificado a `0.4500 / 0.2800 / 0.2700`) |
| **O-12** | `src/storage/curation_service.py`, `src/storage/seeder.py` | Gobernanza por comentario: `VARIANZA-09`, `ALT-9-A/B/C`, `ALT-8-B/C`; fixtures `TABLA_OFICIAL_J7_CONCLUIDA` (xg/xga/xpts) y momios 1.70/3.60/4.50 | Decisiones de autoridad ("Dictamen del Director 2026-10-04") sin nodo en `docs/` (grep: `VARIANZA-09` no aparece en ningún documento de gobernanza) | **MEDIO** | ⏳ Abierto (Fase 2 — requiere nodo `[LN-QBE-1xx]`) |
| **O-13** | `scratch/apply_directiva_integracion.py:53` | Duplicado de `o_dnb = o_fav * 0.75` y del bloque sellado `[VAULT-CORE-070-TRIAJE]` | Copia del algoritmo sellado fuera de `src/` y no versionada ⇒ segunda fuente de verdad | **MEDIO** | ⏳ Abierto (Fase 2 — retiro o guardián AST) |
| **O-14** | `poisson.py:66-67` (Ω `[0.40,1.60]`), `:72-73,80-81` (blend `0.65 xG + 0.35`), `:89-90` (clamp `[0.05,6.00]`); `evaluator.py` θ; `markets.py:519` (`delta_epist=0.02`) | Clamps y mezclas sin verificación documental cerrada | Literales etiquetados con nodo pero sin localización en `CONSTANTS.md` | **MEDIO** | ⏳ Abierto (Fase 2 — una línea de verificación c/u) |

---

## 5. Resumen ejecutivo

### 5.1 Por categoría de defecto
1. **Colisión de literales entre dominios** (`0.75` Γ_high vs. proxy DNB; `1.35` clamp FCF vs. baseline de liga; `1.60` clip Ω vs. momio sintético x2). El mismo número sirve a dos semánticas: el guardián AST no puede distinguirlas y la trazabilidad documental se vuelve ambigua.
2. **Fabricación de precio como clase de defecto** (O-01 y O-05): sintetizar cuota cuando no hay captura fáctica, contra `[GOVERNANCE-01]` y `ARCH.md` L1123-1125.
3. **Leyes constitucionales implementadas por convención no legislada** (O-03 centinela Zero-H2H; O-09 aduana de identidad con degradación silenciosa).
4. **Contradicción numérica con parámetro sellado** (O-02: 300 d contra `τ_H2H = 180.0` legislado) — único caso donde el código no sólo carecía de nodo, sino que **contravenía** uno vigente.

### 5.2 Clasificación
* **ESENCIAL — bloqueaba certificación `[DIRGEN-STRICT]` (alteraba masa de probabilidad, precios o capital):** O-01, O-02, O-05, O-08, O-09, O-11. De éstos, **O-01, O-02 y O-11 quedaron saneados**; **O-05, O-08 y O-09 permanecen abiertos** y requieren nodo o VARIANZA antes de cualquier commit.
* **DEUDA TÉCNICA / TRAZABILIDAD:** O-03 (saneado por nombrado), O-04, O-06, O-07, O-10, O-12, O-13, O-14.

---

## 6. Anexo A — Dictamen Arquitectónico y resoluciones (Protocolo C.2, Fase 3)

| VARIANZA | Consulta | Dictamen del Arquitecto (2026-10-08) | Materialización |
|:--|:--|:--|:--|
| **V-01** | Tarea 4 (`poisson.py`) era inviable: `H2HDecayResult` no posee `partidos_jugados` ⇒ `w_h2h ≡ 0.0` global; y `exp(-κ·días)` sin amplitud/piso era un cambio dimensional | **APROBADA OPCIÓN B** — preservar centinela contractual, sustituir la base temporal a `κ_H2H = ln2/180 = 0.00385098`, y **promulgar** amplitud `0.5000` y piso `0.1500` en `CONSTANTS.md` §1 | ✅ `CONSTANTS.md` §1 (2 filas nuevas con Prohibición de Reúso) + `poisson.py` (constantes nombradas `KAPPA_H2H`, `W_H2H_AMP`, `W_H2H_PISO`, `SENTINELA_ZERO_H2H_DIAS`) |
| **V-02** | Tarea 3 rompía la paridad `src/` ↔ Bóveda Canónica | **AUTORIZADO EL ESPEJO** — bajo `[DIRGEN-STRICT]` código y Vault deben ser idénticos | ✅ `portfolio_math.py:131-132` + `DIRGEN_VAULT.md:1497-1498` (parche atómico idéntico) |

### 6.1 Trazabilidad de los 5 saneamientos
| # | Objeto | Archivo(s) | Régimen |
|:--|:--|:--|:--|
| T1 | Persistencia del censo | `docs/ORPHAN_RULES_CENSUS.md` | `[DBBD-FUNGIBLE]` |
| T2 | Paridad Γ = 0.67 (verificación, sin edición) | `src/core/simplex_morphology.py:25` ✓ · `docs/ARCH.md:1319` ✓ · `docs/DIRGEN_VAULT.md:2022` ✓ | `[DIRGEN-STRICT]` |
| T3 | Erradicación de cuota DNB sintética (O-01) | `src/core/contracts/portfolio_math.py` + `docs/DIRGEN_VAULT.md` | `[DIRGEN-STRICT]` |
| T4 | Armonización H2H (O-02 + O-03) | `docs/CONSTANTS.md` §1 + `src/core/poisson.py` | `[DIRGEN-STRICT]` |
| T5 | Unificación del prior de mercado (O-11) | `src/web/routes/markets.py` | `[DBBD-FUNGIBLE]` |

> 🛑 **Mandato respetado:** ninguna operación de `git commit` ni `git push` fue ejecutada. El saneamiento permanece exclusivamente en el árbol de trabajo, a la espera de la prueba física de la plataforma en el navegador por el Director Humano.

---

## 7. Anexo B — Evidencia del Bucle Reflexivo (The Shield, T6)

### 7.1 Jueces focalizados — 2026-10-08

| Juez | Invariante auditado | Resultado |
|:--|:--|:--|
| `test_shield_simplex_morphology_and_gamma_slider.py` | `[LN-QBE-059]` partición exacta Γ=0.67 · `[LN-QBE-060-B]` integración · `[ARCH-1.4.30]` DTO Γ | ✅ 3 passed |
| `test_shield_legislative_registry.py` | Unicidad de nodos `[LN-*]` / `[ARCH-*]`, cero referencias colgantes, cobertura total del universo | ✅ 5 passed |
| `test_shield_dirgen_integrity.py` | Guardián criptográfico/AST de integridad DirGen sobre la Bóveda | ✅ 1 passed |
| `test_shield_market_dispatch_sovereign_source.py` | Ley 1 (cero semillas en el despacho) · Ley 2 (cuarentena canónica) · Ley 3 (`epistemic_delta`) · Ley 4 (consumo de fixture) | ✅ 4 passed |
| `abstract_test_LN_QBE_020_temporal.py` | Clase base abstracta (no coleccionable, por diseño) | ▶ ejecutada vía `test_LN_QBE_020_concrete.py` y `test_shield_bayesian_form_and_h2h.py` |

**Subtotal:** `13 passed, 3 warnings in 1.88s` — `EXIT CODE 0`

### 7.2 Suite completa de The Shield

```
........................................................................ [ 25%]
................................................................s....... [ 51%]
........................................................................ [ 77%]
...............................................................          [100%]
======================= 278 passed, 1 skipped in 20.99s =======================
SHIELD_EXIT=0    ELAPSED_SEC=28.74 (reloj de pared)
```

* **Criterio de aceptación:** ≥ 278 passed / 0 failed / 1 skipped → **CUMPLIDO**.
* **SLA (Decreto 2026-10-04):** ≤ 25.0 s en frío → **CUMPLIDO** (20.99 s reportados por pytest; los 7.75 s adicionales de reloj de pared corresponden al arranque del intérprete y a la tubería de PowerShell, fuera del presupuesto legislado).

### 7.3 Prueba física del kernel H2H (O-02 / O-03)

Verificación numérica del nuevo operador frente al anterior (`κ = 0.00385098`, amplitud `0.50`, piso `0.15`):

| Antigüedad H2H | `w_h2h` nuevo (τ=180 d) | `w_h2h` anterior (τ≈433 d efectiva) | Δ |
|:--:|:--:|:--:|:--:|
| 0 d | 0.500000 | 0.500000 | — |
| 7 d | 0.486702 | 0.488468 | −0.0018 |
| 30 d | 0.445447 | 0.452419 | −0.0070 |
| 90 d | 0.353548 | 0.370409 | −0.0169 |
| 180 d | 0.249993 | 0.274406 | −0.0244 |
| 365 d | 0.150000 (piso) | 0.150000 (piso) | — |
| ≥ 9000 d | 0.000000 (centinela Zero-H2H) | 0.000000 | — |

Interpretación: la mezcla ahora decae con la **vida media sellada de 180 días** (el peso cae a la mitad exacta de su amplitud a los 180 d: `0.25`) y alcanza el piso promulgado en ~1 año, en coherencia con `CONSTANTS.md` §1 y `[LN-QBE-020]`. El centinela `[LN-QBE-020-B]` sigue intacto.

### 7.4 Paridad Código ↔ Bóveda Canónica

| Objeto | `src/` | `docs/DIRGEN_VAULT.md` | Estado |
|:--|:--|:--|:--:|
| Mutación DNB (O-01) | `portfolio_math.py:129-132` | `L1495-1498` | ✅ idénticos |
| Γ default | `simplex_morphology.py:25` = `0.67` | `L2022` = `0.67` (y nota `L1447`) | ✅ concordante |
| Triaje con Γ dinámico | `triaje_determinista_9_estrategias(..., gamma=0.67)` | `L1450`, `L1465` | ✅ concordante |

### 7.5 Manifiesto git final (sin commit / sin push)

```
 M docs/ARCH.md                         (pre-existente)
 M docs/CONSTANTS.md                    (+2)    ← T4: promulgación w_H2H^amp / w_H2H^piso
 M docs/DESIGN.md                       (pre-existente)
 M docs/DIRGEN_VAULT.md                 (+129)  ← T3: espejo Vault (V-02 autorizado)
 M docs/GOVERNANCE.md                   (pre-existente)
 M docs/ID_REGISTRY.md                  (pre-existente)
 M docs/LOGIC.md                        (pre-existente)
 M src/core/contracts/portfolio_math.py (+6/-2) ← T3: erradicación de cuota sintética (O-01)
 M src/core/poisson.py                  (+17/-3)← T4: κ_H2H + amplitud + piso (O-02 / O-03)
M  src/core/simplex_morphology.py       (staged pre-existente: Γ 0.65 → 0.67)
 M src/web/routes/markets.py            (+8/-3) ← T5: prior unificado (O-11)
?? docs/ORPHAN_RULES_CENSUS.md          ← T1: este documento
?? scratch/                             (pre-existente, no versionado)
```

**Cero residuos verificados en `src/`:** `o_fav * 0.75` → 0 · `0.564 / 0.258 / 0.178` → 0 · decaimiento `/300.0` → 0.
**Cero mocks en producción** `[GOVERNANCE-01]` ✅ · **`git commit` / `git push`** 🛑 **NO EJECUTADOS**.

### 7.6 Deuda residual declarada (Fase 2 pendiente de nodo o VARIANZA)

O-04 (saturación madurez J=6 / baseline `1.35`), **O-05** (13 fallbacks de cuota en `evaluator.py` — riesgo ALTO), O-06 (`odd_emp 3.30`), O-07 (neutral `0.50`), **O-08** (relleno `0.3333` en conjunta Progol), **O-09** (contención por subcadena en la aduana de identidad — riesgo ALTO), O-10 (carril XHR/`verify=False`), O-12 (gobernanza por comentario `VARIANZA-09`), O-13 (duplicado en `scratch/`), O-14 (clamps sin localización en `CONSTANTS.md`).

> Estas diez reglas huérfanas **no fueron tocadas** en esta fase y permanecen vigentes en el código; su saneamiento exige dictamen previo.

**[FIN DEL CENSO]**
