# 🧾 FICHA DE VARIANZA — `VAR-2026-10-21-FASE-C-UI-32V-MICRO`

**Estado:** `RESUELTO — ALT-B RATIFICADA Y MATERIALIZADA` (Fase C · `[DES-QBE-070-B]` / `[ARCH-1.4.62]`)
**Nodos afectados:** `[ARCH-1.4.61]` (deuda declarada «fuera del alcance») · `[DES-QBE-070]` → `[DES-QBE-070-B]` · `[ARCH-1.4.62]` (nuevo) · `[LN-QBE-112]` (sandbox espejo)
**Jueces afectados:** `test_shield_fasec_visual_and_micro_dynamics.py` (nuevo) · `test_shield_fase3_polymorphic_cards_ui.py` (realineado, sólo literales) · `test_shield_sandbox_micro_dinamicas_pipeline.py` (realineado al contrato de 5 celdas)
**Régimen:** `[DBBD-FUNGIBLE]` en vitrina (`src/web/**`) y composición del sandbox · `[DIRGEN-STRICT]` intacto en `src/core/**`, `src/storage/**`, `src/models/web_schemas.py` y las tres funciones puras de `[LN-QBE-112]`
**Fecha:** 2026-10-21

---

## 1. Coordenadas exactas

| Artefacto | Elemento | Línea(s) | Defecto |
|---|---|---|---|
| `src/web/static/js/app.js` | botón del micro-HUD: `🔬 44 Variables` + `title="… vector de 44 variables"` | 4051 | Literal 44V en la vitrina (rótulo derogado) |
| `src/web/static/js/app.js` | comentario del pintor: «desglose forense de 44 variables» | 4028 | Nombre derogado en cabecera de bloque |
| `src/web/static/js/app.js` | aviso de degradación: «catálogo de 44 variables» | 4611 | Literal 44V en mensaje de ausencia |
| `src/web/static/js/app.js` | helpers `_cardDimension44`, `_tablaDimension44`, `_familiaCard44`, `_variable44`, `_celda44`, `_valor44`, `_balanzaGoles44`, `_rejillaCard44`, `_badgeDimension44`, `_hidratarBadgesDimension44`, `_cardPosesion44`, `_recordH2HCard44`, `_fichaShockCard44`, `_porcentaje44`, `_delta44`, `_bloqueSemaforos44`, `ETIQUETAS_SEMAFORO_44`, `COLORES_ESTADO_44` | 4181-4511 | Deriva nominal interna del régimen 44V |
| `src/web/static/js/app.js` | ramas de familia `𝒯_Shk` / `𝒯_H2H` | 4494-4497 | Familias **inexistentes** en el catálogo de 32 (`[ARCH-1.4.61]` §4): ramas muertas |
| `src/web/templates/index.html` | `<h3 id="vars44-titulo">🔬 Inspección forense · 44 variables</h3>` | 979 | Título visible del modal |
| `src/web/templates/index.html` | `.vars44-subtitulo` «… catálogo canónico del dossier §3 en **12 dimensiones**» | 980-983 | Cardinalidad derogada (12 dims / 44 vars) |
| `src/web/templates/index.html` | comentario del modal «INSPECCIÓN FORENSE DE 44 VARIABLES» | 970 | Nombre derogado |
| `src/web/templates/index.html` | botón del Centro de Control `🔍 Auditoría de Completitud Fáctica (44V)` + tooltip «catálogo de 44 variables» | 922 | Literal 44V en la vitrina del panel `🛡️` |
| `scripts/laboratorio/sandbox_micro_dinamicas_pipeline.py` | `_TAXONOMIA` con `V18`-`V44` (15 celdas) | 99-190 | Taxonomía derogada |
| `scripts/laboratorio/sandbox_micro_dinamicas_pipeline.py` | `_DIMENSIONES` con 5 claves | 193-199 | Claves derogadas (`dimension_6_disciplina`, `dimension_9_cronometria`, `dimension_10_banca`, `dimension_12_cierre`) |
| `scripts/laboratorio/sandbox_micro_dinamicas_pipeline.py` | `_construir_dimension_5/6/9/10/12` | 596-694 | Cinco composiciones de dimensiones inexistentes |
| `scripts/laboratorio/sandbox_micro_dinamicas_pipeline.py` | `_semaforos` con `disciplina_roja` sobre `V24` | 752-872 | Semáforo sobre celda reasignada (`V24` = penales, no rojas) |
| `scripts/laboratorio/sandbox_micro_dinamicas_pipeline.py` | `ratios_cronometria` (V33/V34) e `indice_riesgo_roja` (V24) | 938 · 1087-1090 | Bloques derivados de celdas inexistentes |
| `tests/shield/test_shield_sandbox_micro_dinamicas_pipeline.py` | 4 Jueces del contrato de 15 variables / 5 dimensiones | 15-76 | Contrato derogado |
| `tests/shield/test_shield_fase3_polymorphic_cards_ui.py` | Test 3: `_cardDimension44(`, `_valor44(`, `dimensiones.map(_tablaDimension44)` | 130-157 | Nombres internos pre-purga (axiomas intactos) |

## 2. Evidencia fáctica real

Línea base certificada **antes** de tocar código (documentos ya legislados, código intacto):

```
$ python -m pytest tests/shield -q
492 passed, 371 warnings in 21.28s

$ python -m scripts.auditoria.reconciliar_registro_legislativo --check
✅ REGISTRO COMPLETO: 235 nodos anclados simbólicamente (cobertura 100%).
   Modo SOLO LECTURA (por defecto). Filas con estado preservado: 237.
```

Barrido de literales derogados en la capa visible (`Select-String` / regex `44 Variables|de 44|44V`):
`app.js` ⇒ 3 literales visibles (4028, 4051, 4611) · `index.html` ⇒ 3 literales visibles (922, 970-979) + 1 subtítulo con «12 dimensiones» (982).

Catálogo vigente leído del código (no de la prosa) — `DIMENSIONES_CANONICAS` de `src/core/sovereign/factor_attribution.py`:

```
𝒯_Vol V01-V05 · 𝒯_Rem V06-V11 · 𝒯_Def V12-V16 · 𝒯_Por V17-V20 · 𝒯_Spc V21-V25 · 𝒯_Ctx V26-V32
```

## 3. Diagnóstico causal

`[ARCH-1.4.61]` purgó la nomenclatura en los **proveedores de evidencia** y en los cinco sandboxes ratificados, pero dejó dos deudas explícitas: (a) la **vitrina** seguía publicando 44V y (b) `sandbox_micro_dinamicas_pipeline.py` seguía emitiendo cinco dimensiones del régimen derogado. Ambas son la misma clase de defecto: **deriva nominal de presentación** — el símbolo sobrevive más que la magnitud que lo sostenía.

El agravante del sandbox es fiduciario, no cosmético: sus claves `dimension_9_cronometria` / `dimension_10_banca` / `dimension_12_cierre` **no existen en el catálogo**, y su semáforo `disciplina_roja` leía `V24`, celda que el catálogo vigente reasigna a **Penales Favor/Contra**. Un semáforo así no mide rojas: mide otra magnitud con el rótulo viejo — la peor forma de maquillaje (`[GOVERNANCE-01]`).


## 4. Abanico de alternativas evaluadas

| Opción | Descripción | Coste | Riesgo fiduciario |
|---|---|---|---|
| **ALT-A** | Renombrar también las **anclas de contrato** (`#modal-44-variables`, `vars44-*`, `.btn-ver-44-vars`, `abrirModal44Variables()`, `variables_44`) | Alto (JS + HTML + CSS + Jueces + DTO + endpoint) | Alto: `variables_44` es contrato de red sellado (`[ARCH-1.4.57]`); exigiría tocar `web_schemas.py` (`[DIRGEN-STRICT]`) por un motivo estético |
| **ALT-B** | **Purga nominal de vitrina + realineación de helpers internos**, conservando las anclas de contrato; sandbox espejo de una sola dimensión forzada a FASE 6 | Medio (2 archivos de vitrina + 1 sandbox + 3 Jueces) | Bajo: cero líneas en `src/core/**` y `src/storage/**`; el DTO no cambia |
| **ALT-C** | Congelar el sandbox tal cual y sólo editar la UI | Bajo | Alto: deja vivo el semáforo `disciplina_roja` midiendo penales y cinco dimensiones fantasma en el reporte |

## 5. Solución recomendada y criterio fiduciario

**ALT-B ratificada.** Criterios:

1. **El nombre del contrato no es vitrina.** `variables_44` viaja por la red y `#modal-44-variables` / `vars44-*` / `.btn-ver-44-vars` / `abrirModal44Variables()` son anclas de DOM y de JS ya referenciadas por `[ARCH-1.4.57]` y por el Juez de Fase 3. Renombrarlas no cambia una sola magnitud: sólo acerca el riesgo a `[DIRGEN-STRICT]` sin beneficio fiduciario. Se renombran **sólo** los helpers internos (`_cardDimension32`, `_tablaDimension32`, `_familiaCard32`, `_variable32`, `_celda32`, `_valor32`, …).
2. **Cero magnitud aparente.** El sandbox deja de consultar el corpus para `𝒯_Spc` y **declara** las cinco celdas `SIN EVIDENCIA` / `FASE 6` con `local = visita = None`. No hay feed de pelota parada, córners, penales ni tarjetas en el corpus congelado: cualquier cifra sería invención.
3. **La aritmética sellada no se toca.** `calcular_ratio_cronometria`, `evaluar_alerta_fragilidad_cierre` y `calcular_indice_rotacion_xi` quedan **byte-idénticas**; se retira su inyección al reporte (que leía celdas inexistentes), no su código. `[LN-QBE-083]` sobrevive como lectura *no computable declarada* vía `evaluar_alerta_fragilidad_cierre(None)`.
4. **`𝒯_Ctx` consolidado, no amputado.** Las familias extintas `𝒯_Shk` y `𝒯_H2H` no desaparecen de la lectura: se funden en un solo Card (`V26`/`V27` H2H, `V29` altitud, `V30` descanso, `V32` ΔxPTS, rejilla `V28`/`V31`), todas con ids del catálogo vigente.
5. **Cero mocks.** El Juez nuevo lee archivos del repositorio y ejecuta el sandbox real contra la persistencia en sólo lectura; no hay dobles ni fixtures inventados.

## 6. Diff propuesto (y materializado)

```
docs/DESIGN.md                    [DES-QBE-070]  → [DES-QBE-070-B] (6 familias + 𝒯_Ctx consolidado)
docs/ARCH.md                      + [ARCH-1.4.62] (Fase C de vitrina + sandbox espejo)
docs/ID_REGISTRY.md               + fila SELLADO [ARCH-1.4.62] + fila de esta ficha
src/web/static/js/app.js          helpers *_44 → *_32 · ramas 𝒯_Spc y 𝒯_Ctx · literales «44V» → «32V»
src/web/templates/index.html      títulos y tooltips 32V · «12 dimensiones» → «6 dimensiones canónicas»
scripts/laboratorio/sandbox_micro_dinamicas_pipeline.py
                                  _DIMENSIONES = {"dimension_5_balon_parado_y_disciplina": V21…V25}
                                  TOTAL_VARIABLES = 5 · celdas forzadas SIN EVIDENCIA / FASE 6
tests/shield/test_shield_fasec_visual_and_micro_dynamics.py   (nuevo, 3 Jueces)
tests/shield/test_shield_fase3_polymorphic_cards_ui.py        (3 literales de nombre)
tests/shield/test_shield_sandbox_micro_dinamicas_pipeline.py  (contrato de 5 celdas)
```

**Prohibido y verificado como intacto:** `src/core/**`, `src/storage/**`, `src/models/web_schemas.py`, `src/core/sovereign/factor_attribution.py`.

## 7. Verificación de cierre

```
$ python -m pytest tests/shield/test_shield_fasec_visual_and_micro_dynamics.py -q   → 3 passed in 0.46s
$ python -m pytest tests/shield -q                                                  → 495 passed, 371 warnings in 20.07s
$ python -m scripts.auditoria.auditar_coherencia_cartelera --check                  → EXIT 0 (rojas=0, partidos=9, jornada 13)
$ python -m scripts.auditoria.auditar_completitud_visor                             → EXIT CODE 0 (rojas=0, ámbar=6 declaradas)
$ python -m scripts.auditoria.reconciliar_registro_legislativo --check              → cobertura 100%
$ python -m scripts.laboratorio.sandbox_micro_dinamicas_pipeline --partido LIGAMX-J11-07  → EXIT 0 (0/5 SIN EVIDENCIA)
```

**Deuda declarada (fuera de alcance):** `scripts/auditoria/auditar_completitud_visor.py` conserva el rótulo de consola
«44V» y las claves `cobertura_44v_pct` / `SIN_CATALOGO_44V` de su parte JSON; ya computa sobre 32 celdas
(`[ARCH-1.4.59]`), pero esas claves son **contrato de artefacto** y su renombre exige varianza propia. No afecta la
vitrina del Visor y el Juez de Fase C no la audita.

