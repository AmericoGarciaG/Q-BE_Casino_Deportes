# 🧾 FICHA DE VARIANZA — `VAR-2026-LAB5-FCF-COTAS`

**Estado:** `RESUELTA — VECTOR DE PRUEBA CORREGIDO (CERO MUTACIÓN DE PLANO SELLADO)`
**Nodos afectados:** `[LN-QBE-111]` / `[ARCH-1.4.50]` → delegación `[LN-QBE-030]` / `[LN-QBE-039]`
**Juez afectado:** `tests/shield/test_shield_sandbox_volumen_porteria_pipeline.py` · `INVARIANZA 4`
**Régimen:** `[DIRGEN-STRICT]` — Alto al Fuego ejecutado al primer fallo (Protocolo Anti-Bandazos)
**Fecha:** 2026-10-19

---

## 1. Coordenadas exactas

| Artefacto | Elemento | Línea (antes del parche) |
|---|---|---|
| `tests/shield/test_shield_sandbox_volumen_porteria_pipeline.py` | `test_invarianza_4_residuo_volumen_ortogonal_cotas_y_delegacion` | 110-111 |
| `scripts/laboratorio/sandbox_volumen_porteria_pipeline.py` | `calcular_residuo_volumen_ortogonal` (delegación VERBATIM) | 439-453 |
| `src/core/metrics.py` | `SyntheticMetricsEngine._compute_fcf` (**intacto, no se toca**) | 45-52 |

## 2. Evidencia fáctica real

```
$ python -m pytest tests/shield/test_shield_sandbox_volumen_porteria_pipeline.py -v
tests/.../test_invarianza_4_residuo_volumen_ortogonal_cotas_y_delegacion FAILED

>       assert abs(calcular_residuo_volumen_ortogonal(65.0, 2, 6) - (-0.35)) < 1e-6
E       assert 0.12999999999999998 < 1e-06
E        +  where 0.12999999999999998 = abs((-0.22 - -0.35))
E        +    where -0.22 = calcular_residuo_volumen_ortogonal(65.0, 2, 6)
```

Aritmética del plano sellado `[LN-QBE-030]` con los mismos insumos:

```
denom    = SoT + SoTA + 2.0 = 2 + 6 + 2 = 10.0
raw_fcf  = (65/50) · (2·(2+1)/10) = 1.30 · 0.60 = 0.78
clamp    = max(0.65, min(1.35, 0.78)) = 0.78        ← 0.78 YA ESTÁ DENTRO DE LA BANDA
v_Vol⊥   = 0.78 − 1.0 = −0.22
```

## 3. Diagnóstico causal

El fallo **no está en el plano sellado ni en la delegación**: `SyntheticMetricsEngine._compute_fcf`
devuelve `0.78` porque `0.78 ∈ [0.65, 1.35]`; el clamp **no se activa**. El defecto es del **vector de
prueba**: el comentario del Juez afirmaba «Raw_FCF = 0.78 ⇒ clamp 0.65», una premisa aritméticamente
falsa (confunde «raw bajo» con «raw por debajo de la cota inferior»). El resto de los vectores del
mismo Juez son correctos y permanecen verdes:

```
(55, 7, 2) → raw 1.60 ⇒ clamp 1.35 ⇒ +0.35 ✔
(50, 5, 5) → raw 1.00 ⇒ sin clamp ⇒  0.00 ✔
(35, 1,10) → raw 0.22 ⇒ clamp 0.65 ⇒ −0.35 ✔
( 0, 0, 0) → raw 0.00 ⇒ clamp 0.65 ⇒ −0.35 ✔
```

## 4. Abanico de alternativas evaluadas

| Opción | Contenido | Riesgo fiduciario | Dictamen |
|---|---|---|---|
| **A** | Corregir el vector del Juez a un caso **realmente** acotado (`30, 2, 6 ⇒ raw 0.36 ⇒ clamp 0.65 ⇒ −0.35`) y **conservar** `(65, 2, 6)` como vector de **no-clamp** (`−0.22`) que certifica la delegación verbatim | Nulo: fortalece el Juez y no toca `src/` | **RATIFICADA** |
| **B** | Endurecer `calcular_residuo_volumen_ortogonal` (clamp propio) para forzar `−0.35` con `(65,2,6)` | **Alto**: la consola emitiría un FCF distinto al del servidor para el mismo insumo ⇒ viola `[ARCH-1.4.50]` §Delegación y reimplementa `[LN-QBE-030]` | Rechazada |
| **C** | Relajar la aserción a `valor ∈ [−0.35, +0.35]` | Medio: pierde el vector de saturación inferior y la prueba se vuelve tautológica | Rechazada |

## 5. Solución ratificada y criterio fiduciario

Se corrige **sólo el Juez**. El plano sellado (`src/core/metrics.py`), los clamps `FCF_MIN = 0.65` /
`FCF_MAX = 1.35` y la delegación del sandbox quedan **byte-idénticos**. Criterio: la única fuente de
verdad del FCF es `SyntheticMetricsEngine._compute_fcf`; si el Juez y el plano discrepan, se enmienda
el Juez, jamás el plano.

## 6. Diff aplicado

```diff
--- a/tests/shield/test_shield_sandbox_volumen_porteria_pipeline.py
+++ b/tests/shield/test_shield_sandbox_volumen_porteria_pipeline.py
@@
-    # Presión estéril: poss 65 %, SoT 2 vs SoTA 6 ⇒ Raw_FCF = 0.78 ⇒ clamp 0.65 ⇒ −0.35
-    assert abs(calcular_residuo_volumen_ortogonal(65.0, 2, 6) - (-0.35)) < 1e-6
+    # Presión estéril saturada: poss 30 %, SoT 2 vs SoTA 6 ⇒ Raw_FCF = 0.36 ⇒ clamp 0.65 ⇒ −0.35
+    assert abs(calcular_residuo_volumen_ortogonal(30.0, 2, 6) - (-0.35)) < 1e-6
+    # Banda interior SIN clamp (delegación verbatim): poss 65 %, SoT 2 vs SoTA 6 ⇒ 0.78 ⇒ −0.22
+    assert abs(calcular_residuo_volumen_ortogonal(65.0, 2, 6) - (-0.22)) < 1e-6
```

**Cierre:** varianza resuelta sin mutación de planos sellados, sin imputación de datos y con un Juez
estrictamente más exigente que el anterior.
