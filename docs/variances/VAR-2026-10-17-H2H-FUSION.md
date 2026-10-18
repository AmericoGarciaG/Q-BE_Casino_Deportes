# DIRGEN_VARIANCE_REQUEST — VAR-2026-10-17-H2H-FUSION

> **Régimen:** `[DIRGEN-STRICT]` (ley de mezcla, métrica de discrepancia y magnitud persistida) · `[DBBD-FUNGIBLE]` (cartelera de calibración).
> **Estado:** ✅ **RESUELTO / CERRADO — ALT-C + E-2 + E-3 APROBADAS Y MATERIALIZADAS** (Dictamen del Director, 2026-10-17). Evidencia de cierre en **§7**.
> **Emisor:** Agente Constructor Kybern v12.0 · **Fecha:** 2026-10-17 · **Ruta SDLC:** SDLC-04 (Feature Injection).
> **Plantilla madre:** `docs/DIRGEN_VARIANCE_REQUEST_TEMPLATE.md` (ley `[GOVERNANCE §4.2-A]`).
> **Destinatarios:** Director + Arquitecto. **Cero commits:** el entregable es el working tree.
> **Tarea origen:** `[LN-QBE-104]` — Fusión Convexa del Símplex Soberano y Persistencia de la Δ_epist Real.

---

## 0. RESUMEN EJECUTIVO

El ensemble Poisson ∪ H2H estaba **legislado pero no materializado**, y la columna que lo delataba
mentía por partida doble:

1. **El kernel H2H no tocaba la vitrina.** `generar_distribucion_soberana` invocaba
   `calcular_matriz_h2h_empirica()` (`[LN-QBE-020-C]`) **sólo** para derivar `Δ_epist`; el símplex
   publicado (`p_local`, `p_empate`, `p_visitante`) seguía siendo el Poisson puro del Generador A.
   El kernel movía la telemetría de discrepancia, nunca la probabilidad de la cartelera.
2. **La discrepancia persistida era un `ratio` de tasas.** `distribution_sync.py` escribía
   `epistemic_delta = intensidades["ratio"] = round(λ_home / λ_away, 2)`, una magnitud **sin cota
   superior** (λ puede ser 4.0 vs 0.5 ⇒ `ratio = 8.0`) y sin relación con la diferencia entre
   generadores. La columna 3NF que el frontend consume como discrepancia epistémica publicaba, por
   tanto, un número que **no era** una discrepancia: violación directa de `[GOVERNANCE-01]`.

A esto se sumaban dos defectos de presentación detectados en la misma pasada (§1, D3/D4): el
acordeón forense exhibía `0/0 evaluadas` sobre dimensiones sin una sola variable evaluada (finge
medición) y la cartelera de calibración carecía de una vía gobernada para excluir los partidos
vetados por discrepancia epistémica, lo que obligaba al operador a leer KPI contaminados por
partidos en cuarentena.

**Dictamen:** `ALT-C` (fusión convexa con tope fiduciario 0.25 y métrica ∞-norma), `E-2` (enmienda
de los Jueces sellados a los invariantes de mezcla) y `E-3` (persistencia de la Δ real con cadena de
lectura `salida → traza → piso R-1`). Cero cambio a Dixon-Coles, al operador de André o a
`estimar_intensidades_loglineal`.

---

## 1. COORDENADAS EXACTAS

| # | Archivo | Línea(s) | Símbolo / contenido | Régimen |
|---|---|---|---|---|
| C1 | `src/core/sovereign_pipeline.py` | **507-521** | `calcular_peso_h2h()` — `w_H2H = min(0.25, N · 0.05)` | 🔴 `[DIRGEN-STRICT]` |
| C2 | `src/core/sovereign_pipeline.py` | **524-582** | `fusionar_simplex_con_h2h()` — mezcla convexa + `Δ(∞) = max_k |P_A − P_C|` | 🔴 `[DIRGEN-STRICT]` |
| C3 | `src/core/sovereign_pipeline.py` | **~505-512** | constantes `PESO_H2H_POR_DUELO=0.05`, `PESO_H2H_TOPE=0.25`, `DELTA_EPISTEMICO_SIN_EVIDENCIA=0.02` | 🔴 `[DIRGEN-STRICT]` |
| C4 | `src/core/sovereign_pipeline.py` | `generar_distribucion_soberana` | publicación del símplex híbrido + `epistemic_delta` + `simplex_poisson` en la traza | 🔴 `[DIRGEN-STRICT]` |
| C5 | `src/storage/distribution_sync.py` | `_delta_epistemico_publicado` | cadena de lectura `salida → traza → 0.02`, acotada a `[0,1]` | 🔴 `[DIRGEN-STRICT]` |
| D3 | `src/web/static/js/app.js` | `_badgeDimension44` | rótulo `SIN EVALUAR` cuando `tiene_datos === false` | 🟢 `[DBBD-FUNGIBLE]` |
| D4 | `src/web/templates/index.html` · `src/web/static/js/app.js` · `theme.css` | `#chk-excluir-vetados` | filtro anti-cuarentena de la cartelera (presentación pura) | 🟢 `[DBBD-FUNGIBLE]` |
| B1 | `tests/shield/test_shield_ensemble_fusion_and_ui_sync.py` | **1-449** | Juez NUEVO · 6 inversiones | 🆕 Sin sello previo |
| B2 | `tests/shield/test_shield_bayesian_form_and_h2h.py` | enmienda E-2 | invariantes de mezcla sobre el dominio del kernel | 🔴 Juez Sellado enmendado |
| B3 | `tests/shield/test_shield_venue_splits_and_h2h_deep.py` | enmienda E-2 | idem | 🔴 Juez Sellado enmendado |
| B4 | `tests/shield/test_shield_gsl3d_orthogonal_engine.py` | enmienda E-2 | idem | 🔴 Juez Sellado enmendado |

---

## 2. EVIDENCIA FÁCTICA (al abrirse el parte)

### 2.1 El símplex publicado no contenía el kernel

```python
# ESTADO ANTERIOR (esquema del orquestador sellado):
delta_epist, kernel_telemetria = _discrepancia_epistemica(...)   # kernel H2H usado AQUÍ
...
trace = StochasticAuditTrace(..., kernel_h2h_empirico=kernel_telemetria)  # telemetría
return SovereignDistributionOutput(p_local=p1, p_empate=pX, p_visitante=p2, ...)  # Poisson puro
```

`p1/pX/p2` provenían exclusivamente de `calcular_distribucion_dixon_coles()`. El kernel aparecía en
la traza como **espectador**: ninguna de sus tres masas entraba en la vitrina.

### 2.2 La discrepancia persistida no era una discrepancia

```python
# ESTADO ANTERIOR (distribution_sync.py):
epist_delta = float(trace_dict.get("intensidades", {}).get("ratio", 0.0) or 0.0)
```

`ratio = λ_home / λ_away` no está acotado a `[0,1]`, no mide separación entre distribuciones y no
distingue dos fixtures con λ idénticas y kernels opuestos (`ratio = 1.0` ⇒ se persistía `1.0` tanto
con acuerdo perfecto como con discrepancia máxima).

### 2.3 Consecuencia operativa medida

* La frontera de veto `τ_disp = 0.12` (`[LN-QBE-070-B]`) se evaluaba sobre la TVD en memoria, pero el
  valor **persistido** —el que leen los visores y los reportes de calibración— era el `ratio`.
* El operador no disponía de un medio gobernado para excluir los partidos vetados de los KPI sin
  desincronizar la fuente (violación del principio de presentación pura, `[GOVERNANCE-01]`).

---

## 3. DIAGNÓSTICO CAUSAL

1. **Causa raíz #1 — frontera de cálculo vs. frontera de publicación.** El kernel se computaba en la
   rama de discrepancia y su resultado nunca cruzaba a la rama de publicación. La deuda no era
   aritmética sino de **flujo**: faltaba una operación de codominio (`Δ² × Δ² → Δ²`).
2. **Causa raíz #2 — colisión de semántica en una columna.** `epistemic_delta` designaba dos
   magnitudes distintas en dos capas (TVD en memoria, `ratio` en 3NF). El `ratio` **nunca fue
   candidato** a métrica de discrepancia: se usó por conveniencia de acceso (`intensidades` estaba a
   mano) y sobrevivió porque ninguna prueba cotejaba la columna contra la traza.
3. **Causa raíz #3 — deuda de presentación.** El badge `0/0` nacía de dividir contadores servidos sin
   discriminar la ausencia de fuente; el filtro anti-cuarentena no existía porque la cuarentena era
   sólo un semáforo de color, no un estado operable.
4. **Causa raíz #4 — colisión de identificador.** El borrador de diseño citaba `[ARCH-1.6.15]`, ya
   **sellado** a *Apertura Dinámica de Jornada en Live Board*, con el sufijo `-C` ocupado por la
   frontera del sensor de mercado (`[ARCH-1.6.21]`).

---

## 4. ABANICO DE ALTERNATIVAS EVALUADAS

| Alt | Ley de fusión | Métrica | Veredicto |
|---|---|---|---|
| **A** | Reemplazo duro: si hay H2H, el kernel **sustituye** al Poisson | TVD | ❌ Descartada: destruye la señal paramétrica con muestras de 1-2 duelos; un barrido de 3 partidos reescribe el símplex completo (varianza muestral sin control). |
| **B** | Media aritmética simple (50/50) cuando hay H2H | TVD | ❌ Descartada: el peso no depende de la evidencia; 1 duelo pesa como 10 y el tope fiduciario desaparece. |
| **C** | **Mezcla convexa con peso monótono y tope:** `w_H2H = min(0.25, N·0.05)` | **∞-norma sobre Δ²** | ✅ **RATIFICADA** — cierra el símplex, acota por componente, satura la influencia empírica en ¼ y la ∞-norma acota la TVD por arriba (`TVD ≤ Δ(∞)`), preservando el orden de la frontera 0.12. |
| **D** | Log-odds pooling (media geométrica normalizada) | TVD | ❌ Descartada: no es convexa sobre Δ² (puede desbordar las cotas por componente), rompe la garantía `min ≤ P_hib ≤ max` y exige pseudoconteos inventados ante ceros. |

**Persistencia (E-3):** se evaluó (i) dejar el `ratio` y renombrar la columna, (ii) persistir la TVD,
(iii) persistir `Δ(∞)`. Se ratificó **(iii)**: es la magnitud que la fusión ya calcula, está acotada
a `[0,1]` por construcción y su cadena de lectura degrada honestamente al piso R-1.

---

## 5. DICTAMEN

**ALT-C · E-2 · E-3 — APROBADAS.** Ley de mezcla, métrica y magnitud persistida:

$$w_{H2H} = \min(0.25,\; N \cdot 0.05), \qquad P_{hib}(k) = (1-w_{H2H})\,P_A(k) + w_{H2H}\,P_C(k)$$

$$\Delta_{epist}(\infty) = \max_{k \in \{1,X,2\}} \left| P_A(k) - P_C(k) \right| \in [0,1], \qquad \text{TVD} \le \Delta(\infty)$$

**Ley Zero-H2H:** `kernel=None` o `N = 0` ⇒ `w_H2H = 0`, la fusión es la **identidad** y
`Δ_epist(∞) = 0.02` (`DELTA_EPISTEMICO_SIN_EVIDENCIA`, piso de ignorancia del Contrato R-1) — jamás
`0.0`: ausencia de evidencia no es coincidencia.

---

## 6. DIFF APLICADO

### 6.1 Núcleo — operación nueva sobre el codominio

```python
def calcular_peso_h2h(n_duelos: int) -> float:
    try:
        duelos = int(n_duelos or 0)
    except (TypeError, ValueError):
        duelos = 0
    return min(PESO_H2H_TOPE, max(0, duelos) * PESO_H2H_POR_DUELO)


def fusionar_simplex_con_h2h(distribucion_parametrica, kernel=None, n_duelos=0) -> Dict[str, float]:
    ...
    peso_h2h = calcular_peso_h2h(n_duelos) if kernel is not None else 0.0
    if kernel is None or peso_h2h <= 0.0:
        return {..., "delta_epist": DELTA_EPISTEMICO_SIN_EVIDENCIA}
    peso_liga = 1.0 - peso_h2h
    delta_epist = max(abs(p_local - q_local), abs(p_empate - q_empate), abs(p_visitante - q_visita))
    return {"p_local": peso_liga * p_local + peso_h2h * q_local, ...}
```

Transcripción íntegra y sellada en `docs/DIRGEN_VAULT.md` → adenda de `[VAULT-CORE-005]`
(firma `SHA256-VAULT-CORE-005-LN-QBE-104-CONVEX-SIMPLEX-FUSION`).

### 6.2 Puente — magnitud persistida

```diff
-            epist_delta = float(trace_dict.get("intensidades", {}).get("ratio", 0.0) or 0.0)
+            epist_delta = _delta_epistemico_publicado(dist_out, trace_dict)
```

`ratio` **permanece** en `intensidades` (`[LN-QBE-102]`: la evidencia 3NF no se reescribe); deja de
ser la fuente de `epistemic_delta`. **Cero backfill** sobre filas históricas.

### 6.3 Jueces enmendados (E-2)

`test_shield_bayesian_form_and_h2h.py`, `test_shield_venue_splits_and_h2h_deep.py` y
`test_shield_gsl3d_orthogonal_engine.py` verificaban propiedades del Generador A **puro** sobre la
salida del orquestador. Tras la fusión, esas cotas se trasladan al canal `simplex_poisson` de la
traza (el Poisson puro sigue publicado) y la salida soberana se verifica con los invariantes de
mezcla: cierre del símplex, acotamiento por componente y tope fiduciario.

### 6.4 Cartelera (`[DES-QBE-067]`)

* `index.html`: control `#chk-excluir-vetados` + etiqueta gobernada en la barra de la cartelera.
* `theme.css`: estilos del filtro (`.bt-filtro-vetados` y estados `checked`/`disabled`).
* `app.js`: suite de filtro/agregación de la cartelera — `_partidoVetadoBacktesting()` (criterio
  único: `atribucion_factorial.semaforos.epist === "ROJO"`), `_universoCalibracion()` (proyección
  inmutable del payload y re-derivación por conteos enteros), `_pintarVisorBacktesting()` (repintado
  sin refetch) y `_badgeDimension44()` endurecido → `SIN EVALUAR`.

---

## 7. RESOLUCIÓN DEL EXPEDIENTE (DICTAMEN DEL DIRECTOR — 2026-10-17)

**FALLO:** ALT-C + E-2 + E-3 **APROBADAS** con orden de materialización inmediata.
**Estado: ✅ CERRADO.** Materialización verificada en el árbol de trabajo (cero commits).

| Criterio | Comando | Resultado |
|---|---|---|
| Juez nuevo | `pytest tests/shield/test_shield_ensemble_fusion_and_ui_sync.py -q` | **6 passed** · 0.59 s |
| Escudo completo | `pytest tests/shield/ -q` | **378 passed · 0 failed · 0 skipped** · 16.39 s / 15.21 s |
| Sintaxis de la cartelera | `node --check src/web/static/js/app.js` | **EXIT 0** |
| Registro legislativo | `docs/LOGIC.md` · `docs/DIRGEN_VAULT.md` · `docs/ARCH.md` · `docs/DESIGN.md` · `docs/ID_REGISTRY.md` | `[LN-QBE-104]` · adendas de `[VAULT-CORE-005]`/`[VAULT-DATA-002]` · `[ARCH-1.6.22]` · `[DES-QBE-067]` · 3 filas de registro |
| Homologación real | `python -m scripts.ingesta.homologar_temporada_optah2h --jornadas 1-11 --forzar` | **EXIT 0** · `procesados=99 exitosos=99 errores=0` · paridad 3NF ↔ captura `idénticas=99 divergentes=0 ausentes=0` |
| Pre-vuelo de cartelera | `python -m scripts.auditoria.auditar_coherencia_cartelera --check` | **EXIT 0** · **0 DISCREPANCIA (🔴)** · 9 partidos (J12) · 31 sondas conformes |
| Auditor de pureza | `python -m scripts.auditoria.auditar_pureza_matematica_vol1` | **EXIT 0** · **7/7** · `[CANON CRISTALIZADO / MATEMÁTICAMENTE IMPECABLE]` |
| Registro legislativo | `python -m scripts.auditoria.reconciliar_registro_legislativo` | **EXIT 0** · **200 nodos · cobertura 100%** |

### 7.1 Huella empírica de la enmienda (prueba del diagnóstico §2.2)

Medición directa sobre las **99** filas de `sovereign_distributions` tras la homologación:

| Magnitud | Rango observado | Lectura |
|---|---|---|
| `intensidades.ratio` (traza, intacta) | **0.44 – 2.96** | fuera de `[0,1]` ⇒ nunca fue una probabilidad ni una discrepancia |
| `audit_trace_json.epistemic_delta` (Δ_epist ∞) | **0.02 – 0.6794** | acotado a `[0,1]` por construcción |
| `sovereign_distributions.epistemic_delta` (columna 3NF) | **0.02 – 0.6794** | **paridad exacta con la traza** (mín/máx idénticos) |
| Cierre del símplex (`|Σp − 1| > 1e-9`) | **0 de 99** | la mezcla convexa preserva Δ² |

*La coincidencia exacta de mín y máx entre columna y traza es la huella dactilar del puente corregido:
la columna dejó de espejar el `ratio` y pasó a espejar la discrepancia real.*

### 7.2 Saldo fiduciario

* El símplex publicado **es** el ensemble: el kernel H2H desplaza hasta ¼ de la masa, nunca más.
* `sovereign_distributions.epistemic_delta` contiene por fin una discrepancia: `Δ(∞) ∈ [0,1]`.
* La evidencia sellada permanece intacta: `intensidades`, `discrepancia_epist` (TVD) y los tres
  generadores no pierden un solo atributo.
* La cartelera declara su universo: badge `SIN EVALUAR` en vez de `0/0` y filtro anti-cuarentena
  reversible, idempotente e inmutable sobre `backtestingReportCache`.


