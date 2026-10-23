# 🧾 FICHA DE VARIANZA — `VAR-2026-10-22-TRAYECTORIA-POSESION-V16`

**Estado:** `RESUELTO — OPCIÓN B RATIFICADA Y MATERIALIZADA` (Sprint `SPRINT-SANEAMIENTO-TRAYECTORIA-POSESION-PURGA-V16-27`)
**Nodos afectados:** `[LN-QBE-123]` (nuevo) · `[ARCH-1.4.63]` (nuevo) · `[DES-QBE-070-B]` (enmendado) · `[DES-QBE-064]` (cardinalidad 6→1) · `[LN-QBE-120]` / `[ARCH-1.4.60]` (catálogo de 32 **intacto**)
**Jueces afectados:** `test_shield_saneamiento_trayectoria_ui_purga_v16.py` (nuevo, 4 jueces) · `test_shield_fase1_master_integration_providers.py` (realineado: `_EVALUADAS_FASE_1` + `V31`/`V32`) · `test_shield_fase3_polymorphic_cards_ui.py` (sin tocar axiomas)
**Régimen:** `[HÍBRIDO DUAL-TRACK]` — `[DIRGEN-STRICT]` en `src/core/sovereign/**` (transcripción pura, λ y P′ intactas) · `[DBBD-FUNGIBLE]` en `src/web/**` (vitrina)
**Fecha:** 2026-10-22

---

## 1. Coordenadas exactas

| Artefacto | Elemento | Línea(s) | Defecto |
|---|---|---|---|
| `src/core/sovereign/factor_attribution.py` | fila `V16` de `_CATALOGO_44` | `_CATALOGO_44` (`V12`-`V16`) | Celda exhibida como ACTIVA sin feed que la sostenga: **ignorancia convertida en dato** |
| `src/core/sovereign/factor_attribution.py` | bucle de `estructurar_catalogo_44_variables` | 1093-1101 | Sin cortafuegos previo a la telemetría y a la ruta heredada: `big_chances_conceded` podía encender `V16` por la espalda |
| `src/core/sovereign/factor_attribution.py` | `_celda_telemetria` | 665-787 | `V31`/`V32` publicadas por `trajectory_provider` en `trayectoria.insumos` y **no transcritas**: trayectoria medida y no exhibida |
| `src/core/sovereign/factor_attribution.py` | `_PRESENCIA_CONTEXTO` / `_presencia_refutada` | 788-830 (nuevo) | `V30` publicaba `+0.0 d` desde el centinela `or 0.0` de `homologar_temporada_optah2h.py`: **ausencia disfrazada de medición** |
| `src/core/sovereign/context_provider.py` | `insumos` del bloque `contexto` | 191-261 · 585-595 | No declaraba si el descanso/altitud fueron **evaluados**: el consumidor no podía distinguir `0` de «no medido» |
| `src/core/sovereign/context_provider.py` | `_celdas_contexto` | 663-761 | Celdas `V29`/`V30` con `EVALUADO` heredado aunque el fixture no reconstruyera fechas |
| `src/web/static/js/app.js` | `_tablaDimension32` | 4255-4275 | Emitía un `<table>` de 7 columnas **idéntico** dentro de cada `details`: seis transcripciones por partida |
| `src/web/static/js/app.js` | `_cardPosesion32` | 4389-4430 | Rótulo `Posesión s/d` sobre un dato existente (`54.0%` / `45.0%` = redondeo, no contradicción) |
| `src/web/static/js/app.js` | acordeón `#vars44-acordeon` | 4660 | Sin soporte de auditoría tras la purga de la tabla por dimensión |
| `src/web/static/css/theme.css` | bloque `.vars44-*` | 1636-1684 | Sin estilos para el soporte consolidado (`.vars44-soporte`, `.vars44-tabla-soporte`) |

## 2. Diagnóstico causal

1. **`V16` — «FUERA DE FUENTE».** FotMob no publica leaderboard de big chances concedidas para la temporada homologada. El catálogo la servía con `estado=EVALUADO` porque la ruta heredada encontraba la clave `big_chances_concedidas` del dossier legacy; el valor, cuando existía, era un residuo de otra temporada. **Purga descartada (ALT-A):** `V16` integra la familia `𝒯_Def` (`V12`-`V16`) y el contrato `derivar_taxonomia("𝒯_Def")` + ~40 Jueces dependen de la integridad del 32V; purgarla rompería el contrato de red sellado por `[ARCH-1.4.57]` sin ganar un solo dato.
2. **`V31`/`V32` — puente roto.** `trajectory_provider` entrega `pts_last5_local/visita` y `xpts_diff_local/visita` en `trayectoria.insumos` desde `[LN-QBE-112]`, pero `_celda_telemetria` solo consultaba `h2h_stats`, `volumen_stats`, `ataque_defensa` y la ruta heredada. La trayectoria existía como diagnóstico y **nunca llegaba a la vitrina**: dos de las 32 celdas quedaban muertas por omisión de cableado.
3. **`V30` — el cero que miente.** `homologar_temporada_optah2h.py` normaliza ausencia con `or 0.0`; cuando el fixture no reconstruye fechas, el artefacto persistido trae `0.0` y la celda lo transcribe como `+0.0 d`. El `0.0` es correcto para el motor sellado (ausencia de BONO), pero es **falso** como telemetría. La única defensa posible en la capa forense es una bandera de presencia explícita.

## 3. Abanico de alternativas evaluadas

| Alternativa | Contenido | Veredicto |
|---|---|---|
| **ALT-A — Purga nominal de `V16`** (catálogo 31V) | Eliminar la fila de `_CATALOGO_44` y renumerar `𝒯_Def` | ❌ **Descartada.** Rompe el contrato `derivar_taxonomia("𝒯_Def")`, el DTO `variables_44` sellado por `[ARCH-1.4.57]` y ~40 Jueces; no gana evidencia, solo borra la declaración de ausencia |
| **ALT-B — Cuarentena declarada + cableado de trayectoria + guardián de presencia** | `V16` se conserva vacía y rotulada `FUERA DE FUENTE`; `V31`/`V32` se cablean a `trayectoria.insumos`; `V30` se apaga cuando el descanso no fue evaluado; vitrina con soporte único y posesión normalizada | ✅ **RATIFICADA por el Director (Opción B)** |
| **ALT-C — Imputar `V16` con proxy de tiros concedidos** | Derivar big chances de `shots_conceded` con un factor heurístico | ❌ **Descartada.** Fabrica una magnitud no medida: viola `[GOVERNANCE-01]` y el principio de cero invención |

## 4. Solución materializada (Opción B)

**Backend `[DIRGEN-STRICT]` — `src/core/sovereign/factor_attribution.py`:**
* `ESTADO_FUERA_DE_FUENTE = "FUERA DE FUENTE"` + `_CUARENTENA = {"V16": "<motivo>"}`; la fila de `V16` pasa a `modo="cuarentena"` con cero claves de extracción.
* Cortafuegos **estructural** en `estructurar_catalogo_44_variables` (1093-1101): se resuelve **antes** de `_celda_telemetria` y de la ruta heredada ⇒ `local = visita = None`, `origen = FUERA DE FUENTE`, `estado = SIN EVIDENCIA`.
* `_CLAVES_TRAYECTORIA` + `_celda_trayectoria` (489-540): `V31 ← pts_last5_*` (`num0`) y `V32 ← xpts_diff_*` (`delta2`, con signo). Invocada en `_celda_telemetria` **después** de `h2h_stats` y **antes** de la ruta heredada; clave ausente o `None` ⇒ la celda cae a la ruta byte-idéntica de `_FORMATO_INSUMO` (cero ruptura de comportamiento).
* `_PRESENCIA_CONTEXTO` + `_presencia_refutada` (788-830): `V30` se apaga si `contexto.descanso_evaluado is False` **o** si `descanso_local` y `descanso_visita` llegan ambos en `None`, con nota honesta: sobreescribe el centinela `0.0`.

**Backend — `src/core/sovereign/context_provider.py`:**
* `altitud_evaluada` / `descanso_evaluado` calculadas en ambas ramas (con datos: 191-201; sin datos: 590-591) y publicadas en `insumos` (260-261) y en el bloque de celdas (760-761). Las celdas `V29`/`V30` derivan su `estado` de esas banderas (702-723) y emiten `None` en vez de `Δ = 0.0` cuando la magnitud no se midió. **El `0.0` que recibe el motor sellado sigue siendo ausencia de BONO:** λ y P′ no cambian.

**Vitrina `[DBBD-FUNGIBLE]` — `src/web/static/js/app.js` + `theme.css`:**
* `_tablaDimension32` (4255-4275) deja de emitir `<table>`: solo `details.vars44-dimension` + `summary` (badge, conteo) + `_cardDimension32(dimension)`. Anclas de contrato preservadas: nombre de función, clase, `data-dimension`, invocación `dimensiones.map(_tablaDimension32)`.
* `_soporteForense32(dimensiones)` (4276-4344): UNA tabla replegable (`.vars44-soporte`) con las columnas de `[DES-QBE-064]` (`ID`, `Variable`, `Local`, `Visita`, `Z-Score`, `Origen`, `Estado`, `Impacto`) y cabecera por familia; wireada en el modal (4660).
* `_cardPosesion32` (4389-4430): `proporcionLocal = local / (local + visita) * 100`, visita por complemento; con Σ ≤ 0 ⇒ `Posesión sin evidencia` y carriles 50/50 (queda derogado `Posesión s/d`).
* `theme.css` 1658-1684: estilos del soporte consolidado (`.vars44-soporte`, `.vars44-tabla-soporte`, `.vars44-soporte-familia`).

## 5. Aritmética intocable (verificación de preservación)

Cero edición de `estimar_intensidades_loglineal`, `calcular_alpha_ligadura`, Poisson, Kelly, `web_schemas.py` y del endpoint `atribucion_factorial.variables_44`. Las 32 celdas del catálogo siguen siendo 32 y `derivar_taxonomia("𝒯_Def")` sigue resolviendo con `V16` en su rejilla.

## 6. Evidencias del bucle reflexivo

| Comprobación | Resultado |
|---|---|
| Juez nuevo **antes** de materializar | 🔴 RED 4/4 (certificó la varianza) |
| Juez nuevo **después** | ✅ GREEN 4/4 |
| Suite completa de The Shield | ✅ **499 passed / 0 failed** — 21.62 s en frío · 19.75 s en caliente (post-edición CSS: 20.09 s) |
| Presupuesto `[GOV-LLM-01]` / Enmienda SLA | ✅ ≤ 25.0 s frío / ≤ 21.0 s caliente |
| `auditar_coherencia_cartelera --check` | ✅ `PRE-VUELO APTO` — **cero 🔴** (0 discrepancias, 6 sondas ámbar, 18 sin veredicto) |
| `auditar_completitud_visor` | ✅ **EXIT CODE 0** — rojas=0, ámbar=6 (J12-J17 sin evidencia declarada) |
| `reconciliar_registro_legislativo --check` | ✅ **237 nodos anclados, cobertura 100%** |

## 7. Deuda declarada

1. La cuarentena de `V16` caduca si algún día se ingesta un corpus con leaderboard de big chances concedidas; hasta entonces la celda permanece **declarada y vacía**.
2. El centinela `0.0` de `homologar_temporada_optah2h.py` sigue existiendo en el artefacto persistido: neutralizarlo **en origen** exige una varianza propia sobre el homologador (fuera del alcance ratificado). El guardián de presencia lo neutraliza en la frontera forense, no en la fuente.
3. `theme.css` conserva las reglas `.vars44-tabla` que el soporte consolidado reutiliza; no se retiran.
