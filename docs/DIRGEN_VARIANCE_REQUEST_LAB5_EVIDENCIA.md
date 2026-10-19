# 🧾 FICHA DE VARIANZA — `VAR-2026-LAB5-EVIDENCIA`

**Estado:** `RESUELTA DEFINITIVAMENTE — OPCIÓN A EJECUTADA`
**Fecha de Cierre:** 2026-10-19
**Resolución:** Se descargó y congeló el artefacto `data/cache_telemetria_liga_mx_2026.json` desde el feed oficial de FotMob `matchDetails` para los 97 partidos concluidos de la temporada. Se pobló la tabla 3NF `match_telemetry` con `possession_pct`, `sot` y `sota` para ambos clubes (194 filas). El Laboratorio 5 (`sandbox_volumen_porteria_pipeline.py`) conmuta de `SIN_EVIDENCIA` a `PARCIAL = 9 · SIN_EVIDENCIA = 0` en la Jornada 11, certificando magnitudes reales sin datos sintéticos (`[GOVERNANCE-01]`). El literal `EXITO = 9` de la directiva táctica queda **corregido por D1** (ver §7.4): `EXITO` exige 7/7 celdas `EVALUADO` y V02/V03/V04/V15/V17 no tienen sensor en el contrato `[LN-QBE-111]`.
**Criterios ratificados:** `D1` (DoD `PARCIAL = 9 · SIN_EVIDENCIA = 0`) · `D2` (INV-2 con triple aserción fáctica) · `D3` (`xg`/`xga` = `NULL`).
**Nodos afectados:** `[LN-QBE-111]` / `[ARCH-1.4.50]`
**Juez afectado:** `tests/shield/test_shield_sandbox_volumen_porteria_pipeline.py`
**Autoridad:** Américo García Guerrero (Director Humano) & Agente Arquitecto — dictamen del 2026-10-19.
**Régimen:** `[HÍBRIDO DUAL-TRACK]` · componente protegido: `[DIRGEN-STRICT]`

---

## 1. Coordenadas exactas

| Artefacto | Elemento | Defecto detectado |
|---|---|---|
| `tests/shield/test_shield_sandbox_volumen_porteria_pipeline.py` | `INVARIANZA 1` | Exigía `V01["estado"] == "EVALUADO"` y `V16["estado"] == "EVALUADO"` con magnitudes reales |
| `tests/shield/test_shield_sandbox_volumen_porteria_pipeline.py` | `INVARIANZA 2` | Exigía `poss_L + poss_V ≈ 100.0` sin condicionar a la existencia de evidencia |
| `scripts/laboratorio/sandbox_volumen_porteria_pipeline.py` | (no materializado) | Sin fuente fáctica de posesión ni de `SoTA` en el entorno |

## 2. Evidencia fáctica real

```
data/cache_optaxg_liga_mx_2026.json  → 97 partidos; claves por bando = {xg, xga}
                                       (sin possession, sot, sota)
match_telemetry (3NF)                → SELECT COUNT(*) = 0
sovereign_distributions.audit_trace  → poss_local/poss_visita/sot/sota = null (J11)
Corte N−1 de LIGAMX-J11-07           → Atl. San Luis PJ=10 · GC=18 · Santos Laguna PJ=10 · GC=15
                                       cobertura xG/xGA = 10/10 en ambos clubes
                                       cobertura posesión/SoT/SoTA = 0/10 en ambos clubes
```

## 3. Diagnóstico causal

No es un defecto de código ni de calibración: es **ausencia estructural de feed óptico granular**.
`[LN-QBE-030]` y `[LN-QBE-039]` requieren `possession`, `sot` y `sota`; el corpus congelado sólo
transporta `xG`/`xGA`, y la tabla `match_telemetry` que debía portar `possession_pct`/`sot`/`sota`
nunca fue poblada (el homologador la lee, no la escribe). Con la ley previa, el verde de
`INVARIANZA 1/2` sólo se alcanzaba **inventando** posesión y `SoTA`, lo que viola
`[GOVERNANCE-01]` y el mandato de cero lógica de negocio inventada.

## 4. Abanico de alternativas evaluadas

| Opción | Contenido | Riesgo fiduciario | Dictamen |
|---|---|---|---|
| **A** | Ingesta fáctica de posesión/`SoT`/`SoTA` vía sensor `matchDetails` (FotMob), congelando el artefacto | Bajo, pero exige red y ampliar jurisdicción (homologador + nuevo decreto) | Diferida a sprint posterior |
| **B** | **Enmienda ratificada del Juez:** contrato tri-estado para V01/V16 y suma 100 % condicionada | Nulo (respeta `[GOVERNANCE-01]`) | **RATIFICADA** |
| **C** | Proxies declarados (cuota de `xG`; `1 − GC/xGA`) | Alto: distorsión semántica | Rechazada |
| **D** | Entregar el sandbox con el Juez en ROJO | Inaceptable: rompe el DoD (`EXIT CODE 0`) | Rechazada |

## 5. Solución ratificada y criterio fiduciario (Opción B — vigente hasta el cierre de la Opción A)

Se enmienda el Juez para que **certifique el protocolo de degradación honesta** ya legislado:

1. Si el corte carece de feed de posesión/`SoTA`, el Juez exige `estado == "SIN EVIDENCIA"`,
   `local is None`, `visita is None` y nota de cobertura `cubiertos/total` de ambos clubes; prohíbe
   cualquier mock o cifra inventada.
2. Si el corte publica telemetría fáctica, el Juez exige `estado == "EVALUADO"` y valores positivos.
3. La aserción de suma 100 % se **condiciona** a `V01["estado"] == "EVALUADO"`; en su lugar, la
   identidad matemática pura se certifica con `calcular_delta_posesion(56.4, 43.6) == 12.8`.
4. `INVARIANZA 3` y `INVARIANZA 4` permanecen **intactas**: verifican `calcular_save_percentage`
   y `calcular_residuo_volumen_ortogonal` con delegación VERBATIM a
   `SyntheticMetricsEngine._compute_fcf` (`[LN-QBE-030]`).

Criterio fiduciario: se preserva la **intención** del Juez (E2E, bipartito, funciones acotadas) y se
elimina la única vía que forzaba a fabricar evidencia. La métrica no se relaja: se hace **honesta**.

## 6. Diff aplicado

* `INVARIANZA 1`: aserción de dos ramas (`EVALUADO` con evidencia | `SIN EVIDENCIA (FASE 6)` sin ella),
  más nota de cobertura obligatoria en la rama degradada.
* `INVARIANZA 2`: `if V01["estado"] == "EVALUADO": assert suma ≈ 100.0`; certificación incondicional
  de `calcular_delta_posesion(56.4, 43.6)` y rechazo de valores fuera de `[0, 100]`.
* `INVARIANZAS 3 y 4`: sin cambios.
* Cero cambios en `src/`, en `[VAULT-CORE-001/005]` y en los clamps `FCF_MIN` / `FCF_MAX`.

**Cierre:** varianza resuelta sin mutación de planos sellados y sin imputación de datos.

---

**Addendum (2026-10-19) — trazabilidad posterior:** la `INVARIANZA 4` sí requirió después una
enmienda, pero de **vector de prueba** y no de plano: ver `VAR-2026-LAB5-FCF-COTAS`
(`docs/DIRGEN_VARIANCE_REQUEST_LAB5_FCF_COTAS.md`). Los clamps `FCF_MIN` / `FCF_MAX`, el plano
`[LN-QBE-030]` y la delegación verbatim del sandbox permanecen intactos; la línea «sin cambios»
de este §6 debe leerse como «sin cambios **en esta** varianza».

---

## 7. RESOLUCIÓN DEFINITIVA — OPCIÓN A EJECUTADA (2026-10-19)

**Autoridad:** Américo García Guerrero (Director Humano) & Agente Arquitecto — orden ejecutiva `Proceda`
con ratificación de `D1`, `D2` y `D3`. **Régimen:** `[HÍBRIDO DUAL-TRACK]` (ingesta `[DBBD-FUNGIBLE]`,
persistencia 3NF y Juez `[DIRGEN-STRICT]`). **Plano matemático intocado:** `src/core/metrics.py`
(`SyntheticMetricsEngine._compute_fcf`), `FCF_MIN` / `FCF_MAX` y la delegación verbatim del sandbox.

### 7.1 Evidencia fáctica que habilita la Opción A (verificada en vivo, solo lectura)

| Hecho verificado | Valor |
|---|---|
| `fixtures.allMatches` de FotMob vs `matches` (3NF) | **153 = 153**; concluidos **97**; J11 = **9** |
| Cobertura `BallPossesion` + `ShotsOnTarget` en los 88 partidos del corte (J1–J10) | **88/88 OK · 0 fallos** |
| Bipartita de posesión por partido | **88/88 suman exactamente 100.0** |
| Identidad de clubes (`canonicalize_team_name` → `obtener_slug_club`) | **18/18** contra `teams.canonical_slug` |
| Acoplamiento `(jornada, home_slug, away_slug)` snapshot ↔ FotMob | **17/17 jornadas sin desfase**; `LIGAMX-J11-07 ↔ 1000014596` |
| `matches.kickoff_utc` | **NULL en 153/153** ⇒ el join opera por slugs canónicos, jamás por reloj |
| `match_telemetry` antes de la ingesta | `SELECT COUNT(*) = 0` (RED estructural) |

### 7.2 Artefacto congelado `data/cache_telemetria_liga_mx_2026.json`

* **Procedencia:** `https://www.fotmob.com/api/data/matchDetails?matchId={fotmob_match_id}` →
  `content.stats.Periods.All.stats[*]`, claves duras `BallPossesion` y `ShotsOnTarget`.
* **Estructura:** `{sonda, esquema, fuente, endpoint, liga_fotmob_id, generado_at, hash_sha256, partidos, faltantes, resumen}`,
  con `partidos[<match_id 3NF>] = {fotmob_match_id, jornada, utc_time, home{slug,possession,sot,sota}, away{...}}`.
* **Timestamp:** ISO-8601 UTC con offset explícito.
* **Hashing:** `hash_sha256` = SHA-256 del cuerpo canónico **auto-excluyente**
  (`json.dumps(cuerpo_sin_hash, sort_keys=True, ensure_ascii=False, separators=(",", ":"))`), misma convención que
  `src/reporting/audit_exporter.py`. La rehidratación `--desde-cache` **recalcula la huella** y aborta si no coincide.
* **Idempotencia:** `partidos` ordenado por `match_id`; dos corridas sobre la misma evidencia producen cuerpo
  bit-idéntico y sólo cambian `generado_at` / `hash_sha256`.

### 7.3 Protocolo de inserción 3NF (atómico)

Una sola `PersistenceGateway.write_transaction()` para todo el lote (FK `match_telemetry.match_id → matches.id`
con `PRAGMA foreign_keys = ON`); `SELECT` + `INSERT`/`UPDATE` idempotente por PK `(match_id, team_slug)`, sin
`DELETE`. `xg` y `xga` se escriben estrictamente `NULL` (`D3`) para no envenenar el *Nivel (b)* del homologador
`homologar_temporada_optah2h._telemetria_3nf`. Partido sin `BallPossesion` o `ShotsOnTarget` ⇒ **no se inserta
nada para ese partido** y se declara en `faltantes` (jamás `50.0`/`0.0`, que el sandbox descarta por diseño).

### 7.4 Criterios ratificados y su consecuencia fáctica

* **D1 — DoD.** El criterio de éxito del barrido J11 es `PARCIAL = 9 · SIN_EVIDENCIA = 0`; V01, V16,
  $\Delta\text{Posición}$ y $\Delta v_{\text{Vol}}^{\perp}$ publican cifras reales en los 9 fixtures.
  `EXITO` exige 7/7 celdas `EVALUADO` y V02/V03/V04/V15/V17 están fijas a `None` por contrato (líneas 498-499 y
  526-527 del sandbox): convertir esas celdas exige enmendar `[LN-QBE-111]` + nuevas columnas 3NF + 5 derivaciones
  ⇒ **sprint legislativo posterior**, fuera de esta jurisdicción.
* **D2 — INVARIANZA 2.** La suma $100\%$ es una identidad **por partido**, no entre medias de cortes
  independientes (San Luis 52.9 % + Santos 50.8 % = **103.7 %**). Se certifica con triple aserción:
  (i) `home.possession + away.possession ≡ 100.0` en todo el artefacto; (ii) `V01.local_num`/`visita_num` ==
  media del corte con tol. $10^{-4}$; (iii) `ΔPosición == local_num − visita_num == +2.1 pp` con tol. $10^{-4}$.
* **D3 — Integridad 3NF.** `xg`/`xga` = `NULL` (ausencia declarada); el $xG$/$xGA$ sigue viviendo en el corpus
  congelado `data/cache_optaxg_liga_mx_2026.json`, con precedencia `caché > telemetría` en el homologador.

### 7.5 Magnitudes certificadas (corte N−1 J1–J10 · `LIGAMX-J11-07`)

| Magnitud | LOCAL (Atlético San Luis) | VISITA (Santos Laguna) |
|---|---|---|
| `poss_pct` | 52.9 % | 50.8 % |
| `sot` / `sota` | 43 / 51 | 44 / 60 |
| `GC` del corte | 18 | 15 |
| V16 Save % | 64.7059 % | 75.0 % |
| FCF (sellado) | 0.9698 | 0.8626 |
| $v_{\text{Vol}}^{\perp}$ | −0.0302 | −0.1374 |

$\Delta\text{Posición} = +2.1$ pp (`PARIDAD TERRITORIAL`) · $\Delta v_{\text{Vol}}^{\perp} = +0.1072$
(`DOMINIO CONVERTIDO`).

**Cierre:** varianza resuelta con evidencia fáctica, sin mutación del plano matemático sellado y sin una sola
cifra imputada.

de este §6 debe leerse como «sin cambios **en esta** varianza».
