# DIRGEN_VARIANCE_REQUEST — VAR-2026-10-16-ESCALA-XG

> **Régimen:** `[DIRGEN-STRICT]` (núcleo matemático `src/core/sovereign_pipeline.py` + Jueces Sellados).
> **Estado:** ✅ **RESUELTO / CERRADO — OPCIÓN A APROBADA Y MATERIALIZADA** (Dictamen del Director, 2026-10-16). Ejecutado el Plan §7 íntegro; evidencia de cierre en **§9**.
> **Emisor:** Agente Constructor Kybern v12.0 · **Fecha:** 2026-10-16 · **Ruta SDLC:** SDLC-04.
> **Plantilla madre:** `docs/DIRGEN_VARIANCE_REQUEST_TEMPLATE.md` (ley `[GOVERNANCE §4.2-A]`).
> **Destinatarios:** Director + Arquitecto. **Cero commits:** el entregable es el working tree.
> **Tarea origen:** Directiva de 4 Actos sobre `sovereign_pipeline.py` / `centinela_deportivo.py`.

---

## 0. RESUMEN EJECUTIVO

El contrato de unidad de `xg`/`xga` **nunca fue reconciliado** entre la ingesta y el plano canónico:

* **La ingesta publica ACUMULADO de temporada** (`seeder.py` L83-100: `xg=12.8` con `pj=6`;
  `centinela_deportivo.py` L470: `xg ≈ gf·1.05+1.2`; `homologar_temporada_optah2h.py` acumula el
  sensor partido a partido).
* **El plano canónico `docs/DIRGEN_VAULT.md` (L498/504/511/517) declara una TASA POR PARTIDO**
  (`xg_h_per_game = float(h.get("xg", gf_h_per_game * 1.05))`, sin división por `pj`).

Para absorber ambos universos se insertó en el núcleo —**sin decreto**— un conmutador de unidad
(`> 5.0`, cuatro sitios: L221/228/235/242). Es un **shim de doble unidad en el corazón matemático**:
la unidad de medida pasa a depender de la **magnitud** del dato. Consecuencia medida: en temporada
temprana (acumulado ≤ 5) el `xg` acumulado se interpreta como tasa ⇒ **inflación ≈ pj×**.

La rectificación canónica (vault L483-521, verbatim) es **numéricamente inocua para todo productor
de producción** (todos publican acumulado), pero **rompe 2 Jueces Sellados y 1 auditor** cuyas
fixtures declaran `xg` **por partido**. Por el Protocolo Anti-Bandazos de `AGENTS.md` se detiene la
ejecución y se emite este parte: **Actos 3.1 y 3.3 bloqueados**; Actos 1, 2 y 3.2 materializados
(ninguno bajo `[DIRGEN-STRICT]`).

---

## 1. COORDENADAS EXACTAS

| # | Archivo | Línea(s) | Símbolo / contenido | Régimen |
|---|---|---|---|---|
| C1 | `src/core/sovereign_pipeline.py` | **220-221** | `xg_total_h` / `xg_h_per_game = (xg_total_h / pj_h) if xg_total_h > 5.0 else (xg_total_h or gf_h_per_game)` | 🔴 `[DIRGEN-STRICT]` |
| C2 | `src/core/sovereign_pipeline.py` | **227-228** | `xga_total_a` / `xga_a_per_game = … if xga_total_a > 5.0 else …` | 🔴 `[DIRGEN-STRICT]` |
| C3 | `src/core/sovereign_pipeline.py` | **234-235** | `xg_total_a` / `xg_a_per_game = … if xg_total_a > 5.0 else …` | 🔴 `[DIRGEN-STRICT]` |
| C4 | `src/core/sovereign_pipeline.py` | **241-242** | `xga_total_h` / `xga_h_per_game = … if xga_total_h > 5.0 else …` | 🔴 `[DIRGEN-STRICT]` |
| C5 | `docs/DIRGEN_VAULT.md` | **483-521** | plano canónico de `derivar_factores_estructurales` — **sin** conmutador `> 5.0`, tasa directa | 📜 Canónico |
| C6 | `src/core/sovereign_pipeline.py` | **205-282** | función derivadora + `[LN-QBE-039]` GSL-3D + `[LN-QBE-036]` Capa 4 (intactas) | 🔴 `[DIRGEN-STRICT]` |
| B1 | `tests/shield/test_shield_sovereign_pipeline.py` | **37-39, 57-60** | fixture Puebla/Atlante `{"pj": 8, "gf": 10, "gc": 10, "xg": 1.46, "xga": 1.29}` + cota `0.52 ≤ p_local ≤ 0.60` | 🔴 Juez Sellado |
| B2 | `tests/shield/test_shield_sovereign_integration_e2e.py` | **49-54** | idéntico fixture unit-incoherente (`pj=8` con `xg=1.46`) y orquestador E2E real | 🔴 Juez Sellado |
| B3 | `scripts/auditoria/auditar_pureza_matematica_vol1.py` | **220-221, 259-260** (+ cota **L118**) | fixtures `xg=1.65/pj=8`, `1.10/pj=8`, `1.95/pj=9`, `1.15/pj=9`; cota `ratio_ofensivo ≤ 2.50` | 🟡 Auditoría |

---

## 2. EVIDENCIA FÁCTICA REAL (CERO MOCKS)

### 2.1 Juez de criba — Invarianza 1 (RED certificado)

`python -m pytest tests/shield/test_shield_unified_ingestion_and_xg_scale.py -v` → **1 failed, 2 passed**:

```
AssertionError: 🚨 [ARCH-1.4.41] Los factores dependen del TOTAL acumulado, no de la TASA por partido:
  temporada temprana=(0.7081, -0.5515, 0.7081, -0.5515)
  vs. temporada madura=(-0.1592, 0.2814, -0.1592, 0.2814)
```

Ambos registros son **el mismo equipo** (1.20 xG/partido, 1.00 GF/partido, 1.00 xGA/partido):
`(pj=3, xg=3.60)` y `(pj=9, xg=10.80)`. Bajo el plano canónico el resultado es único
`(-0.1592, 0.2814, -0.1592, 0.2814)`; bajo el shim, la temporada temprana queda **sobre-amplificada**
(`A_home = +0.7081`). Trazabilidad: el pitido de la Invarianza 2 (ingesta unificada) pasó a **GREEN**
tras el Acto 3.2; la Invarianza 3 (custodia de plantilla) ya estaba **GREEN**.

### 2.2 A/B forense sobre clon del motor (`scratch/forensic_shield_ab.py`)

Mutación temporal + `finally` con reversión byte-exacta (artefacto `scratch/forensic_shield_postfix.txt`).
Con la **transcripción canónica** aplicada:

```
FAILED tests/shield/test_shield_sovereign_integration_e2e.py::test_integracion_e2e_persistencia_distribucion_real
FAILED tests/shield/test_shield_sovereign_pipeline.py::test_pipeline_soberano_caso_puebla_atlante
2 failed, 336 passed, 25 warnings in 18.23s
```

Daño colateral verbatim (artefacto L100-103):

```
>       assert 0.52 <= salida.p_local <= 0.60, f"Puebla desbordado: {salida.p_local}"
E       AssertionError: Puebla desbordado: 0.3438
E        +  where 0.3438 = SovereignDistributionOutput(match_id='LIGAMX-J9-01', p_local=0.3438, …)
```

Causa: la fixture declara `xg=1.46` **como tasa** con `pj=8`; el plano canónico la lee como
acumulado (0.1825 xG/partido) y hace colapsar a Puebla. **La fixture viola el contrato de unidad,
no la ley.** Nótese que ambas fixtures (B1 y B2) son **copia literal** del mismo registro
(`{"pj": 8, "gf": 10, "gc": 10, "xg": 1.46, "xga": 1.29}`), lo que confirma que el error es de
plantilla heredada, no de diseño independiente.

### 2.3 Estado real del árbol ([DIRGEN-STRICT] intacto)

* `git hash-object src/core/sovereign_pipeline.py` = `c3f06b665d7c2a6449c12ee2b100a012ec374625`
  = `git rev-parse HEAD:src/core/sovereign_pipeline.py` ⇒ **cero drift de contenido**
  (la marca ` M` de `git status` es exclusivamente ruido CRLF/stat).
* `git diff --numstat -- scripts/daemons/centinela_deportivo.py` ⇒ `30 7` (única edición del Acto 3.2).
* Sondas y evidencia forense confinadas a `scratch/` (**fuera** del árbol de producción, untracked).

### 2.4 DoD parcial verificado en el árbol actual

| Criterio | Comando | Resultado |
|---|---|---|
| Escudo completo | `pytest tests/shield/ -q` | **340 passed · 1 failed** (única roja = criba §2.1) · ≈12 s |
| Pre-vuelo de cartelera | `python -m scripts.auditoria.auditar_coherencia_cartelera --check --todo` | **EXIT 0** · 153 partidos · **cero 🔴** · 70 🟡 |
| Registro legislativo | `python -m scripts.auditoria.reconciliar_registro_legislativo` | **191 nodos · 100%** · filas preservadas 193 |
| Commits | `git status --porcelain` | **cero commits** (working tree + `scratch/` untracked) |

---

## 3. DIAGNÓSTICO CAUSAL

**Causa raíz (sistémica, no sintáctica):** existe **un solo campo físico** (`TeamStanding.xg`) para
**dos magnitudes distintas** (temporada acumulada vs. tasa por partido) y ninguna autoridad de
frontera que lo declare. La ingesta acumula (P1-P3); el plano canónico divide... sólo cuando el dato
ya **parece** acumulado.

**Origen del shim:** el conmutador `> 5.0` no aparece en `docs/DIRGEN_VAULT.md` (C5). Se trata, por
tanto, de **drift no autorizado** en `src/core/` — bajo Régimen B el plano es INMUTABLE y toda
divergencia requiere decreto. El shim fue una **reconciliación silenciosa de unidades dentro del
núcleo matemático**: la peor localización posible, porque propaga el defecto a Poisson, a las cotas
κ y a la calibración ρ.

**Mecánica del defecto:** `umin = (T > 5.0) ? T/PJ : T`. Es una función **discontinua** y
**no invariante al calendario**: con el mismo rendimiento por partido, `T` crece con las jornadas,
y al cruzar `T = 5.0` **la unidad de medida cambia de golpe** (salto de ≈ PJ×). Consecuencias:

1. **Jornadas tempranas (J1-J4):** `T ≤ 5` ⇒ el valor acumulado se usa como tasa ⇒ inflación ≈ `PJ×`
   (evidencia §2.1: `A_home = +0.7081` para un ataque de 1.20 xG/partido).
2. **Discontinuidad intra-temporada:** el mismo equipo se recalibra de un plumazo al superar el umbral,
   lo que viola la continuidad exigible a una transformación estructural y contamina la
   reproductibilidad del sellado (una captura sellada en J3 y la misma realidad en J9 no son
   comparables ⇒ riesgo directo a la "congelación" `[ARCH-1.4.37]`).
3. **Coherencia con la cota de resonancia:** el shim hace que cotas como `ratio_ofensivo ≤ 2.50`
   (B3, L118) se evalúen sobre magnitudes de unidad variable, es decir, miden cosas distintas en
   cada jornada. La no-resonancia se vuelve **estacionalmente condicional**.

**¿Por qué el Escudo no lo detectó?** Las fixtures heredadas (B1, B2, B3) declaran `xg` **por
partido**, es decir, **el otro universo**: el shim las deja pasar porque en esos valores (`1.46 ≤ 5`)
el conmutador es un no-op. El Escudo validaba así una reconciliación de unidades **que el plano no
autoriza**, y ningún juez cruzaba los dos universos (temprano vs. maduro). Ese hueco es exactamente
lo que cierra el juez de criba J1 (`[ARCH-1.4.41]`).

---

## 4. ABANICO DE ALTERNATIVAS EVALUADAS

| Opción | Enunciado | Veredicto |
|---|---|---|
| **A** | **Restaurar el plano verbatim** (tasa = `total / pj`, incondicional) + **enmendar el vault** para declarar el contrato **ACUMULADO** (con fallback `gf·1.05·pj`) + **re-unitar** las 3 fixtures legadas (× `pj`) | ✅ **RECOMENDADA** — cero cambio numérico en producción; `src` == vault; capturas selladas vigentes |
| **B** | Mantener el plano por partido y **dividir en ingesta** (publicar `xg/pj`) | ❌ Reescribe **81 capturas selladas** ⇒ rompe continuidad y el censo sellado (E1-E5); traslada la ambigüedad a la frontera |
| **C** | **Renombrar el contrato** (`xg_total` / `xg_juego`) y purgar el campo ambiguo | ❌ Máximo radio de explosión (DTOs, esquema 3NF, UI, 3 jueces, ingesta); correcto a largo plazo, sobredimensionado ahora |
| **D** | **Legislar el shim** (`> 5.0` como ley) | ❌ Inadmisible: medida dependiente de la magnitud, discontinua respecto al calendario, y contradictoria con C5 |

**Aritmética de la Opción A (verificada en el A/B de §2.2):** con `xg=1.46` y `pj=8` el shim produce
`xg_h_per_game = 1.46` (rama `else`); con el contrato acumulado (`xg=11.68`, `pj=8`) el plano produce
`11.68/8 = 1.46` ⇒ **factor idéntico** ⇒ las fixtures B1/B2 recuperan su semántica original **sin
tocar una sola cota** (× `pj` = 8 en `xg`/`xga` de ambas). Ésa es la prueba de que la rectificación
es de **frontera**, no de matemática.

---

## 5. SOLUCIÓN RECOMENDADA Y CRITERIO FIDUCIARIO

**Recomendación: Opción A** — el contrato de unidad se declara en las **dos fronteras** (vault + fixtures)
y el núcleo vuelve a ser lo que el vault dice, sin ramas.

**Criterio fiduciario de preservación matemática (por qué A y no otra):**

1. **Cero cambio numérico en producción:** los tres productores (P1, P2, P3) publican **acumulado**;
   con la ley canónica obtienen hoy `total/pj` — exactamente el mismo número que ya obtenían por la
   rama `> 5.0` una vez madura la temporada. La Opción A sólo corrige la **ventana temprana**.
2. **Cero reescritura de historia:** las capturas selladas (censo E1-E5) contienen acumulados válidos;
   ninguna se invalida (contraste con la Opción B, que las obligaría a re-sellarse).
3. **`src` == `vault` (Régimen B restaurado):** desaparece el drift no autorizado; cualquier futura
   divergencia será detectable por hash y no por inspección visual.
4. **Invariante de calendario:** el resultado pasa a ser función **sólo** del rendimiento por partido;
   J3 y J9 del mismo equipo coinciden (lo que el juez J1 certifica).
5. **Continuidad de la cota de no-resonancia:** `ratio_ofensivo ≤ 2.50` (B3, L118) recupera una unidad
   fija y deja de ser estacionalmente condicional.
6. **Costo acotado y auditable:** 4 líneas de núcleo + 4 líneas de vault + 3 fixtures (×`pj`) + 1
   auditor; ningún DTO, esquema, UI ni ingesta se toca.

**Riesgo de no actuar (justificación de la urgencia):** mientras el shim siga en producción, toda
cartelera de jornadas tempranas (J1-J4) se calcula con xG **inflado ≈ pj×**, lo que es **exactamente
el patrón del Síndrome Puebla-Atlante** que el propio vault y B3 declaran desterrado (`[ARCH-1.4.33]`).
No es un riesgo latente: es una patología activa en la ventana temprana de cada temporada.

**Radio de acción declarado:** `src/core/sovereign_pipeline.py` (4 sitios), `docs/DIRGEN_VAULT.md`
(4 sitios), 2 Jueces Sellados (fixtures), 1 auditor y — encadenado — la **re-homologación
`--jornadas 1-11 --forzar`** (Acto 3.3), ejecutable **sólo después** del decreto porque re-sella
capturas bajo la ley nueva.

---

## 6. DIFF PROPUESTO (NINGUNO APLICADO — ESPERA AUTORIZACIÓN)

> ⛔ **CERO CAMBIOS MATERIALIZADOS.** `src/core/sovereign_pipeline.py` es byte-exacto a `HEAD`
> (§2.3). Todo lo siguiente es **texto propuesto** sujeto a decreto; el Constructor no ha tocado
> ninguna de estas líneas.

### 6.1 🔴 `[DIRGEN-STRICT]` Núcleo — `src/core/sovereign_pipeline.py` L218-244

```diff
     # 1. Ataque Local (Tasa por partido)
     gf_h_per_game = float(h.get("gf", 10)) / pj_h
-    xg_total_h = float(h.get("xg", 0.0) or 0.0)
-    xg_h_per_game = (xg_total_h / pj_h) if xg_total_h > 5.0 else (xg_total_h or gf_h_per_game)
+    xg_total_h = float(h.get("xg") or (h.get("gf", 0.0) or 0.0) * 1.05)
+    xg_h_per_game = xg_total_h / pj_h
     att_h_rate = (0.65 * xg_h_per_game) + (0.35 * gf_h_per_game)
     A_home = math.log(max(0.2, att_h_rate) / mu_base_equipo)

     # 2. Defensa Visita (Tasa por partido)
     gc_a_per_game = float(a.get("gc", 12)) / pj_a
-    xga_total_a = float(a.get("xga", 0.0) or 0.0)
-    xga_a_per_game = (xga_total_a / pj_a) if xga_total_a > 5.0 else (xga_total_a or gc_a_per_game)
+    xga_total_a = float(a.get("xga") or (a.get("gc", 0.0) or 0.0) * 0.95)
+    xga_a_per_game = xga_total_a / pj_a

     # 3. Ataque Visita
     gf_a_per_game = float(a.get("gf", 7)) / pj_a
-    xg_total_a = float(a.get("xg", 0.0) or 0.0)
-    xg_a_per_game = (xg_total_a / pj_a) if xg_total_a > 5.0 else (xg_total_a or gf_a_per_game)
+    xg_total_a = float(a.get("xg") or (a.get("gf", 0.0) or 0.0) * 1.05)
+    xg_a_per_game = xg_total_a / pj_a

     # 4. Defensa Local
     gc_h_per_game = float(h.get("gc", 10)) / pj_h
-    xga_total_h = float(h.get("xga", 0.0) or 0.0)
-    xga_h_per_game = (xga_total_h / pj_h) if xga_total_h > 5.0 else (xga_total_h or gc_h_per_game)
+    xga_total_h = float(h.get("xga") or (h.get("gc", 0.0) or 0.0) * 0.95)
+    xga_h_per_game = xga_total_h / pj_h
```

**Racional de los coeficientes:** se preservan los del vault (1.05 ataque, 0.95 defensa) pero
**re-expresados en unidades acumuladas** (`gf_total·1.05`, `gc_total·0.95`) para que el fallback
tenga la misma unidad que el campo. La rama desaparece: la unidad ya no depende de la magnitud.
El `or` mantiene el comportamiento ante `xg` nulo/ausente (cae al fallback, nunca a `0` ciego).

### 6.2 📜 `[DIRGEN-STRICT]` Vault — `docs/DIRGEN_VAULT.md` L496-519 (enmienda legislativa)

```diff
     # 1. Ataque Local
-    gf_h_per_game = float(h.get("gf", 10)) / pj_h
-    xg_h_per_game = float(h.get("xg", gf_h_per_game * 1.05))
+    gf_h_total = float(h.get("gf", 10))
+    gf_h_per_game = gf_h_total / pj_h
+    # CONTRATO DE UNIDAD: xg/xga se publican ACUMULADOS de temporada [ARCH-1.4.41]
+    xg_total_h = float(h.get("xg", gf_h_total * 1.05))
+    xg_h_per_game = xg_total_h / pj_h
```
(análogamente en los bloques 2, 3 y 4 con `gc_a_total·0.95`, `gf_a_total·1.05`, `gc_h_total·0.95`.)

Motivo: sin esta enmienda, `src` canónico y `vault` seguirían **contradiciéndose** en la unidad del
campo (el vault no declara ni acumulado ni tasa). La enmienda es lo que hace posible cumplir
Régimen B (`src == vault`) y a la vez hablar el idioma de los productores.

### 6.3 🔴 `[DIRGEN-STRICT]` Jueces Sellados — re-unitar fixtures (× `pj`)

```diff
 # tests/shield/test_shield_sovereign_pipeline.py L37-39 (espejo en L57-60)
-        "home_team_stats": {"pj": 8, "gf": 10, "gc": 10, "xg": 1.46, "xga": 1.29},
-        "away_team_stats": {"pj": 8, "gf": 7, "gc": 12, "xg": 1.07, "xga": 1.52},
+        "home_team_stats": {"pj": 8, "gf": 10, "gc": 10, "xg": 11.68, "xga": 10.32},
+        "away_team_stats": {"pj": 8, "gf": 7, "gc": 12, "xg": 8.56, "xga": 12.16},

 # tests/shield/test_shield_sovereign_integration_e2e.py L52-53   (mismo ×8, idéntico fixture)
```
**Cero cambio de cotas ni de narrativa** (aritmética de §4): `11.68/8 = 1.46` ⇒ `p_local ∈ [0.52, 0.60]`
se satisface con los mismos números que el juez esperaba hoy.

### 6.4 🟡 `[DBBD-FUNGIBLE]` Auditor de pureza — `scripts/auditoria/auditar_pureza_matematica_vol1.py`

`xg` × `pj` en L220-221 (`1.65→13.2`, `1.10→8.8`) y L259-260 (`1.95→17.55`, `1.15→10.35`); **verificar**
post-rectificación la cota `ratio_ofensivo ≤ 2.50` (L118) — paso 5 del §7.

### 6.5 ⛔ BLOQUEADO EN CONJUNTO — Acto 3.3

`python -m scripts.ingesta.homologar_temporada_optah2h --jornadas 1-11 --forzar` **no debe ejecutarse**
antes del decreto: re-sellaría capturas bajo una ley que va a cambiar (violaría "una unidad, un sello").

---

## 7. PLAN DE EJECUCIÓN (POSTERIOR A LA AUTORIZACIÓN)

| # | Paso | Comando / acción | Criterio de cierre |
|---|---|---|---|
| 1 | Aplicar 6.1 + 6.2 (núcleo y vault) | edición dirigida | `git diff --numstat src/core/sovereign_pipeline.py` = `8 4` |
| 2 | Aplicar 6.3 (fixtures) | edición dirigida | `pytest tests/shield/test_shield_sovereign_pipeline.py tests/shield/test_shield_sovereign_integration_e2e.py -q` ⇒ 2 passed |
| 3 | Certificar la ley nueva | `pytest tests/shield/test_shield_unified_ingestion_and_xg_scale.py -v` | **3 passed** (Invarianza 1 GREEN; 2 y 3 ya GREEN) |
| 4 | Escudo completo | `pytest tests/shield/ -q` | **≥341 passed · 0 failed · 0 skipped · ≤25 s** |
| 5 | Aplicar 6.4 + verificar cota | `python -m scripts.auditoria.auditar_pureza_matematica_vol1` | EXIT 0, `ratio_ofensivo ≤ 2.50` |
| 6 | Re-sellado (Acto 3.3) | `python -m scripts.ingesta.homologar_temporada_optah2h --jornadas 1-11 --forzar` | censo sellado íntegro + recibo |
| 7 | Pre-vuelo y cierre | `auditar_coherencia_cartelera --check --todo` · `reconciliar_registro_legislativo` · `git status` | EXIT 0 / 0 🔴 · 100% nodos · cero commits |

**Presupuesto de reversión:** cada paso es de una sola edición; los pasos 1-3 son revertibles con
`git checkout -- <archivo>` (nada está commiteado). Ningún paso toca la bóveda de datos.

---

## 8. ANEXOS

### 8.1 Comandos ejecutados por el Constructor (evidencia cruda)

```
pytest tests/shield/test_shield_unified_ingestion_and_xg_scale.py -v      # 1 failed, 2 passed
pytest tests/shield/ -q                                                   # 340 passed, 1 failed
python -m scripts.auditoria.auditar_coherencia_cartelera --check --todo   # EXIT 0 · 153 partidos · 0 🔴
python -m scripts.auditoria.reconciliar_registro_legislativo              # 191 nodos · 100%
git hash-object src/core/sovereign_pipeline.py                            # == HEAD:... (cero drift)
git diff --numstat -- scripts/daemons/centinela_deportivo.py              # 30 7
```

### 8.2 Artefactos de sonda

`scratch/forensic_shield_ab.py`, `scratch/forensic_shield_postfix.txt`, `scratch/probe_xg_scale_ab.py`
— **untracked, fuera del árbol de producción** (la evidencia forense no se mezcla con `src/` ni
`scripts/`).

### 8.3 Entregado SIN decreto (no pertenece a este bloqueo)

| Acto | Régimen | Evidencia |
|---|---|---|
| Acto 1 — Gobernanza (plantilla `DIRGEN_VARIANCE_REQUEST_TEMPLATE.md`, `docs/variances/`, `[GOVERNANCE §4.2-A]`, `[ARCH-1.4.41]`, `ID_REGISTRY`) | `[DBBD-FUNGIBLE]` | Invarianza 3 GREEN |
| Acto 2 — Juez de criba `test_shield_unified_ingestion_and_xg_scale.py` | `[DBBD-FUNGIBLE]` | RED certificado en Invarianza 1 |
| Acto 3.2 — Daemon fill-if-absent (`centinela_deportivo.py` L642+, L737-744) | `[DBBD-FUNGIBLE]` | amparado en decreto previo `VAR-2026-J7-HOMOLOGACION §6.4·E4`; Invarianza 2 GREEN |

### 8.4 Trazabilidad del bloqueo

* **Ley aplicada:** `AGENTS.md` → Protocolo Anti-Bandazos (Régimen B: prohibido ensayo y error);
  `[DIRGEN-STRICT]`: "PROHIBIDO alterar una sola coma o constante".
* **Decisión solicitada:** autorizar (o no) la Opción A del §4 y el diff del §6.
* **Sin autorización:** el árbol permanece en el estado aquí certificado (núcleo intacto,
  Actos 1/2/3.2 entregados, Actos 3.1/3.3 detenidos).

---

## 9. RESOLUCIÓN DEL EXPEDIENTE (DICTAMEN DEL DIRECTOR — 2026-10-16)

**FALLO:** Opción A **APROBADA** con orden de materialización inmediata (transcripción verbatim del
bloque canónico en el núcleo). **Estado: ✅ CERRADO.**

### 9.1 Materialización ejecutada (Plan §7)

| Paso | Acción | Resultado |
|---|---|---|
| 1 | Núcleo `src/core/sovereign_pipeline.py` L221/228/235/242 — erradicación del conmutador `> 5.0` | `git diff --numstat` = **`4 4`** ⇒ exactamente las 4 líneas del dictamen, cero ediciones colaterales |
| 1b | Contrato de unidad declarado en `docs/DIRGEN_VAULT.md` `[VAULT-CORE-005]` + sincronización del bloque canónico | **PARIDAD `src == vault` = True** (4/4 patrones byte-idénticos) |
| 2 | Fixtures re-unificadas ×`pj` (juez pipeline L38-41 + juez e2e L49-55) | `11.68/8 = 1.46` ⇒ cotas selladas intactas ⇒ **3 passed** (0 daño colateral) |
| 3 | Auditor de pureza re-unificado ×`pj` (Pruebas 5 y 7) | **EXIT 0 · 7/7** `[CANON CRISTALIZADO / MATEMÁTICAMENTE IMPECABLE]` |
| 4 | Llave Maestra `homologar_temporada_optah2h --jornadas 1-11 --forzar` | **EXIT 0** · 97 partidos · 99 fixtures · 99/99 en 3NF (0 errores) · paridad captura↔3NF **99 idénticas / 0 divergentes / 0 ausentes** |

### 9.2 Huella empírica de la extirpación (prueba del diagnóstico §3)

El re-sellado tocó **17 capturas** con una distribución que **coincide exactamente** con la ventana
predicha por el diagnóstico (temporada temprana, acumulado ≤ 5):

* **J4 = 8 · J5 = 6 · J6 = 1 · J7 = 1 · J8 = 1** ⇒ 17 capturas donde el shim inflaba el xG.
* **J1-J3 sin cambio:** `PJ < 3` ⇒ `S(I) = 0` ⇒ ignorancia uniforme (33/33/33), insensible a la escala.
* **J9-J11 sin cambio:** acumulado > 5 ⇒ el shim ya era un no-op (coincide con la rama canónica).

*La firma de 17 sellos —y no otra— es la huella dactilar del shim erradicado.*

### 9.3 DoD de liberación final (verificado en el árbol congelado)

| Criterio | Comando | Resultado |
|---|---|---|
| Invarianza 1 | `pytest tests/shield/test_shield_unified_ingestion_and_xg_scale.py -v` | **3 passed** (Invarianzas 1, 2 y 3 en VERDE) |
| Escudo completo | `pytest tests/shield/ -q` | **341 passed · 0 failed · 0 skipped** · 15.04 s frío / 13.87 s caliente |
| Auditor de pureza | `python -m scripts.auditoria.auditar_pureza_matematica_vol1` | **EXIT 0** · 7/7 |
| Pre-vuelo de cartelera | `auditar_coherencia_cartelera --check --todo` | **EXIT 0** · 153 partidos (J1-J17) · **0 🔴** · 430 conformes / 61 🟡 |
| Registro legislativo | `reconciliar_registro_legislativo` | **191 nodos · 100%** |
| Commits | `git status` | **cero commits** (`HEAD` = `e1be553`) |

### 9.4 Saldo fiduciario

* La ley es **una sola** en las tres capas: vault, núcleo y productores (todos acumulado).
* La unidad de medida **ya no depende de la magnitud** ni del calendario ⇒ el síndrome
  Puebla-Atlante de temporada temprana queda estructuralmente imposible.
* La historia queda **auditada**: 82 capturas preservadas sin cambio + 17 re-selladas con paridad
  total contra 3NF.



| P1 | `scripts/seeder.py` | **83-100, 173** | standings canónicos con `xg` **acumulado** (`12.8 / pj=6`) | 🟢 Ingesta |
| P2 | `scripts/daemons/centinela_deportivo.py` | **470** | `"xg": round(gf * 1.05 + 1.2, 1)` — escala de `gf` acumulado | 🟢 Ingesta |
| P3 | `scripts/ingesta/homologar_temporada_optah2h.py` | **295, 448** | acumulación estacional del xG por partido del sensor `[ARCH-1.4.39]` | 🟢 Ingesta |
| J1 | `tests/shield/test_shield_unified_ingestion_and_xg_scale.py` | **45-86** | Juez de criba (Invarianza 1) que certifica la ley de escala | 🆕 Sin sello |
