# 🧾 FICHA DE VARIANZA — `VAR-2026-10-21-FASE-B-PURGA-V`

**Estado:** `RESUELTO — ALT-B RATIFICADA Y MATERIALIZADA` (Fase B.2 · `[LN-QBE-122]` / `[ARCH-1.4.61]`)
**Nodos afectados:** `[LN-QBE-121]` §P.5 (purga nominal 44V) → `[LN-QBE-120]` (catálogo 32V) · `[LN-QBE-119]` (ley de unidad «por partido»)
**Jueces afectados:** `test_shield_fase1_master_integration_providers.py` · `test_shield_sandbox_h2h_pipeline.py` · `test_shield_h2h_dimension_population.py` · `test_shield_sandbox_ataque_defensa_pipeline.py` · `test_shield_sandbox_contexto_shocks_pipeline.py` · `test_shield_sandbox_trayectoria_momento_pipeline.py` · `test_shield_sandbox_volumen_porteria_pipeline.py` · `test_shield_factor_attribution_and_telemetry.py` · `test_shield_fase3_polymorphic_cards_ui.py` · `test_shield_control_center_and_calibration_unblock.py`
**Régimen:** `[DIRGEN-STRICT]` en los cinco proveedores de evidencia · `[DBBD-FUNGIBLE]` en los sandboxes
**Fecha:** 2026-10-21

---

## 1. Coordenadas exactas

| Artefacto | Elemento | Línea(s) | Ocurrencias |
|---|---|---|---|
| `src/core/sovereign/telemetry_provider.py` | `_TAXONOMIA_DIM_1` (`V01-V04`) · `_TAXONOMIA_DIM_4` (`V15-V17`) | 77-94 · 418-442 | 4 |
| `src/core/sovereign/attack_defense_core.py` | `_TAXONOMIA_DIM_2` (`V05-V09`) · `_TAXONOMIA_DIM_3` (`V10-V14`) | 68-91 · 323-336 | 18 |
| `src/core/sovereign/context_provider.py` | celdas `V25-V28` (rama oscura y rama evaluada) | 584-591 · 677-710 | 12 |
| `src/core/sovereign/trajectory_provider.py` | celdas `V29-V32` | 589-708 · 779 | 5 |
| `scripts/laboratorio/sandbox_ataque_defensa_pipeline.py` | `_TAXONOMIA_DIM_2` / `_TAXONOMIA_DIM_3` | 94-118 · 543-557 | 18 |
| `scripts/laboratorio/sandbox_volumen_porteria_pipeline.py` | `_TAXONOMIA_DIM_4` (`V15-V17`) | 106-120 · 514-524 | 5 |
| `scripts/laboratorio/sandbox_contexto_shocks_pipeline.py` | `_celdas_dim7` (`V25-V28`) | 553-576 | 10 |
| `scripts/laboratorio/sandbox_trayectoria_momento_pipeline.py` | `V29-V32` | 719-924 | 14 |
| `scripts/laboratorio/sandbox_h2h_pipeline.py` | Dimensión 11 (`V39/V40/V41/V42`) | 159-225 · 730-740 · 800-824 | 39 |
| `tests/shield/*` (10 archivos) | aserciones sobre identificadores legados | — | ≈30 |

## 2. Evidencia fáctica real

Suite soberana al momento del Alto al Fuego (`[LN-QBE-121]` §P.1–§P.4 ya materializado):

```
$ python -m pytest tests/shield -q
467 passed, 371 warnings in 15.10s          ← macro conectada, λ bit-idéntica

$ python -m scripts.auditoria.auditar_coherencia_cartelera --check
✅ PRE-VUELO APTO: ninguna DISCREPANCIA (🔴) detectada.   EXIT=0
```

Conteo de identificadores legados vigentes (`Select-String`), por artefacto:

```
sandbox_h2h_pipeline.py                => 39      (V39/V40/V41/V42)
attack_defense_core.py                 => 18      (V05-V14)
sandbox_ataque_defensa_pipeline.py     => 18
sandbox_trayectoria_momento_pipeline.py=> 14
context_provider.py                    => 12      (V25-V28)
sandbox_contexto_shocks_pipeline.py    => 10
telemetry_provider.py                  =>  4      (V01-V04 · V15-V17)
trajectory_provider.py                 =>  5      (V29-V32)
sandbox_volumen_porteria_pipeline.py   =>  5
```

## 3. Diagnóstico causal

§P.5 ordena «derivar de `_CATALOGO_32` por dimensión». La derivación **no puede ser posicional**: la
cardinalidad de cada dimensión del catálogo no coincide con las magnitudes que los proveedores publican.

| Dimensión | Celdas del catálogo | Magnitudes publicadas | Desajuste |
|---|:--:|:--:|---|
| `𝒯_Vol` | 5 (`V01-V05`) | 4 (`V01-V04`; falta `V05` Faltas) | 1 celda sin feed |
| `𝒯_Rem` | 6 (`V06-V11`) | 5 (xG, SoT, xGOT, BC+, BC−) | `V11` (xA) sin feed |
| `𝒯_Def` | 5 (`V12-V16`) | 5 (xGA, SoTA, **PPDA**, rec. tercio medio, BC−) | PPDA **sin celda** |
| `𝒯_Por` | 4 (`V17-V20`) | 3 (Goles evitados, Save%, Salidas) | `V20` (CS) sin feed |
| `𝒯_Ctx` | 7 (`V26-V32`) | 12 (Contexto 4 + Trayectoria 4 + H2H 4) | **saturación ×2** |

Tres conflictos exigen dictamen del Director (no son renombres mecánicos):

* **C1 · UNIDAD (`[LN-QBE-119]`):** el proveedor publica `V05 = xG/90 min` y `V10 = xGA/90 min`; el catálogo
  rotula `V06 = xG por Partido` y `V12 = xGA por Partido`. Renombrar sin recomputar violaría la ley de unidad
  (misma clase de defecto que certificó `[LN-QBE-119]`, SoT = 47.722); recomputar a `Σ/PJ` **cambia la
  magnitud** publicada por un componente `[DIRGEN-STRICT]`.
* **C2 · SEMÁNTICA (`𝒯_Vol`):** `V03 = Pases progresivos completados` y `V04 = Entradas al último tercio`
  no son `V03 = Pases Precisos` ni `V04 = Pases Largos Precisos`: magnitudes distintas con etiqueta ajena.
* **C3 · SATURACIÓN (`𝒯_Ctx`):** `V26/V27/V28` ya son reclamadas por la memoria H2H (Dimensión 11) y por el
  artefacto macro (`V26`, `V27` figuran en `_CLAVES_MACRO_STATS`), mientras Contexto y Trayectoria reclaman
  `V27→V30`, `V28→V29`, `V29→V31`, `V32→V32`. Un remapeo completo publicaría **dos magnitudes distintas en la
  misma celda** salvo que las magnitudes huérfanas salgan del catálogo como `AUX_*`.

## 4. Abanico de alternativas evaluadas

| Opción | Contenido | Riesgo fiduciario | Dictamen |
|---|---|---|---|
| **A** | Nominal mínimo: diccionario de equivalencias `legacy ↔ 32V` en `docs/CONSTANTS.md`, sin tocar proveedores ni sandboxes | Nulo en λ, pero **deja §P.5 sin cumplir** («desaparecen del núcleo, de los sandboxes y de The Shield») | Rechazada |
| **B** | Remapeo semántico con `AUX_*`: las celdas del catálogo se reservan a la evidencia del corte; las magnitudes sin celda (`xG/90`, `xGA/90`, `SoT/90`, `SoTA/90`, `PPDA`, bajas ofensivas/defensivas, `m_xG`, `m_xGA`, `xG histórico`) se publican como `AUX_*` sin código. H2H DIM11 → `V26/V27/V28`; Contexto `V27→V30`, `V28→V29`; Trayectoria `V29→V31`, `V32→V32` | Medio: reescribe claves de ~10 jueces, **λ intacta** | **RECOMENDADA** |
| **C** | Derivación posicional por dimensión (adoptar los renglones del catálogo en orden y alimentar lo alimentable) | **Alto**: rotula `xG/90` como «xG por Partido» (viola `[LN-QBE-119]`) y expulsa magnitudes con evidencia real | Rechazada |

## 5. Solución recomendada y criterio fiduciario

**ALT-B**, ejecutada en una **ventana de contexto limpia** (Fase C) y en el orden del Motor de 3 Pasos:
(1) Jueces RED que exijan `AUX_*` y prohíban identificadores legados; (2) materialización de las taxonomías
derivadas de `_CATALOGO_32`; (3) certificación `pytest tests/shield -q` ⇒ `EXIT 0` ≤ 25 s.
Criterio fiduciario: ninguna magnitud se pierde (pasa a `AUX_*`), ninguna se reetiqueta, ninguna celda recibe
dos magnitudes y **λ permanece bit-idéntica** (`[LN-QBE-121]` §P.4 no se toca).

## 6. Diff propuesto

**Ninguno aplicado** — Alto al Fuego. El esquema futuro del diff es:

```diff
--- a/src/core/sovereign/attack_defense_core.py
+++ b/src/core/sovereign/attack_defense_core.py
@@
-_TAXONOMIA_DIM_2 = (("V05", "xG por 90 minutos (ancla npxG)", "npxG/90", ...), ...)
+_AUX_DIM_2       = (("AUX_XG_90", "xG por 90 minutos (ancla npxG)", "npxG/90", ...), ...)
+_TAXONOMIA_DIM_2 = (("V06", "xG por Partido (ancla npxG)", "npxG/PJ", ...), ...)
```


---

## 7. Resolución materializada (Fase B.2 · `SPRINT-REINGENIERIA-MACRO-FASE-B2-24`)

**Dictamen:** el Director ratificó la Opción **ALT-B** y emitió `Proceda` sobre cuatro directrices:
(1) catálogo fiel a FotMob; (2) `AUX_*` para lo que no tiene casilla; (3) jueces en RED; (4) purga
quirúrgica + re-homologación con WORM. Ley nueva: `[LN-QBE-122]` · `[ARCH-1.4.61]`.

### 7.1 Corrección del diagnóstico de `C1` (unidad)

La ficha sostuvo que `xG/90` no podía ocupar «xG por Partido». La lectura del código demostró que la
magnitud publicada por el proveedor **ya era `acumulado / PJ`** (`_tasa(acum_xg, pj)`), exactamente la
misma que `_FORMATO_INSUMO` consume para encender `V06`. El error era **la etiqueta de unidad**
(`npxG/90`), no la magnitud: `V05 → V06` **sin** degradar a auxiliar. Idéntico razonamiento en
`SoT → V07`, `xGA → V12`, `SoTA → V13`. `C1` queda cerrado por relabelado de unidad, con cero pérdida
de magnitud y cero reetiquetado de semántica.

### 7.2 Tabla final aplicada (celda del catálogo ↔ evidencia que la sostiene)

| Módulo | Casilla anterior | Casilla vigente | Unidad declarada |
|---|---|---|---|
| `attack_defense_core` (DIM 2) | `V05` xG · `V06` SoT · `V07` xGOT · `V08` · `V09` | `V06` · `V07` · `AUX_XGOT_90` · `V08` · `V09` | xG/PJ · SoT/PJ · xGOT/90 |
| `attack_defense_core` (DIM 3) | `V10` xGA · `V11` SoTA · `V12` PPDA · `V13` rec · `V14` BC | `V12` · `V13` · `AUX_PPDA` · `V15` · `V16` | xGA/PJ · SoTA/PJ · índice |
| `telemetry_provider` (DIM 1) | `V01` · `V02` · `V03` · `V04` | `V01` · `V02` · `AUX_PASES_PROG` · `AUX_ENTRADAS_UT` | % · toques/PJ |
| `telemetry_provider` (DIM 4) | `V15` · `V16` · `V17` | `V17` · `V18` · `V19` | xGOT−GC/PJ · % · salidas/PJ |
| `context_provider` | `V25` · `V26` · `V27` · `V28` | `AUX_XG_BAJAS` · `AUX_XGA_BAJAS` · `V30` · `V29` | % merma · días · metros |
| `trajectory_provider` | `V29` · `V30` · `V31` · `V32` | `V31` · `AUX_M_XG` · `AUX_M_XGA` · `V32` | puntos · xG/PJ · xGA/PJ · puntos |
| `sandbox_h2h` (DIM 11) | `V39` · `V40` · `V41` · `V42` | `V26` · `V27` · `V28` · `AUX_XG_HIST` | récord · Δgoles · récord sede · Fase 6 |

**C2 (semántica `𝒯_Vol`) y C3 (saturación `𝒯_Ctx`)** quedan cerrados por la propia tabla: `V03/V04`
(pases progresivos / entradas al último tercio) **no** son «pases precisos» ni «pases largos precisos»
y por tanto viajan como auxiliares; `V26/V27/V28` se reservan a la memoria H2H y `V29/V30` a los shocks,
sin que la macro ni Contexto/Trayectoria reclamen dos veces la misma casilla.

### 7.3 Auxiliares publicados (sin código, sin casilla)

`AUX_XGOT_90`, `AUX_PPDA`, `AUX_PASES_PROG`, `AUX_ENTRADAS_UT`, `AUX_XG_BAJAS`, `AUX_XGA_BAJAS`,
`AUX_Q_MOD_H`, `AUX_Q_MOD_A`, `AUX_M_XG`, `AUX_M_XGA`, `AUX_XG_HIST`.

### 7.4 Evidencia de cierre (medida, no declarada)

```
$ python -m pytest tests/shield -q
492 passed, 371 warnings in 15.74s               ← 467 + 25 jueces nuevos · EXIT 0 · ≤ 25 s

$ python -m scripts.auditoria.auditar_coherencia_cartelera --check
✅ PRE-VUELO APTO: ninguna DISCREPANCIA (🔴)     ← EXIT=0

$ python -m scripts.ingesta.homologar_temporada_optah2h --jornadas 1-13 --forzar
🛡️ [RESGUARDO WORM] data/backups/qbe_database_backup_20261021_*.db
procesados=117 exitosos=117 errores=0
Paridad 3NF ↔ captura: idénticas=117 divergentes=0 ausentes=0

$ python -m scripts.auditoria.auditar_completitud_visor
rojas=0  ambar=6 (J12–J17 sin marcadores consumados)     ← EXIT=0
```

Catálogo sobre las 117 trazas selladas: **22–29 celdas encendidas** por partido, `macro_stats`
presente en 117/117 y cotejo `V01/V06/V07/V12/V13` intacto; λ_home ∈ [0.8640, 2.3626] y
λ_away ∈ [0.7273, 1.9721] — idénticas a la captura previa (`idénticas=117`).

### 7.5 Deuda residual declarada

`sandbox_micro_dinamicas_pipeline.py` conserva las dimensiones 5/6/9/10/12 del régimen 44V derogado
(`V18-V24`, `V33-V44`): **fuera** del alcance ratificado por esta varianza y sujeto a varianza propia.
`docs/DESIGN.md` conserva la nomenclatura histórica como registro forense.

**Cierre:** `[LN-QBE-121]` §P.1–§P.5 **completos**. Ninguna línea de `[DIRGEN-STRICT]` fue mutada por
ensayo y error: la única transformación fue nominal, verificada por 25 jueces nuevos y por la
paridad de captura.

