# 📋 FICHA DE VARIANZA HISTÓRICA: RECONCILIACIÓN DE LITERALES CANÓNICOS EN LA INGESTA NOVIBET.MX
**ID:** `VAR-2026-NOVIBET-FASE1-PASO2`  
**ESTADO:** `RATIFICADO HISTÓRICO` *(sellado y cerrado; ficha materializada por Decreto del Sprint 3)*  
**RÉGIMEN:** `[DIRGEN-STRICT]` (dos planos sellados en tensión: la Directiva esperada vs. el contrato del normalizador)  
**COORDENADAS:** `tests/shield/test_shield_novibet_ingestion.py:8-17` (nota de trazabilidad del Juez) · `tests/shield/test_shield_novibet_ingestion.py:28-40` (`test_normalizacion_clubes_novibet`) · `src/ingestion/normalizer.py` (normalizador sellado, `[LN-QBE-012]`) · `[ARCH-1.4.6-F]` (Sensor de Ingesta Novibet.mx por Intercepción de Feed JSON).  
**NATURALEZA:** registro histórico ratificado — **NO** hay deuda de código pendiente; documenta una desviación ya resuelta y sirve como referencia normativa del Juez citante.

**ANCLAS LEGISLATIVAS:** `[ARCH-1.4.6-F]` (sensor de ingesta *feed-first* de Novibet.mx por intercepción de feed JSON) y `[DES-QBE-057]` (`test_shield_novibet_ingestion`), bajo el axioma `[GOVERNANCE-01]` de cero mocks sintéticos (cero llamadas de red en pruebas unitarias).

**EVIDENCIA FÁCTICA (verbatim del Juez, `test_shield_novibet_ingestion.py:8-17`):**
```
[VARIANCE-01 — Novibet §V-1] Ajuste de calibración legislativa sobre 3 de las 6 tuplas de
`test_normalizacion_clubes_novibet`: la Directiva esperaba "Puebla", "Toluca" y "Pachuca",
identidades que el normalizador sellado `src/ingestion/normalizer.py` (LN-QBE-012) **jamás
emite** — su tabla canónica publica "Club Puebla", "Deportivo Toluca" y "Club Pachuca"
(evidencia empírica del intérprete: `canonicalize_team_name("Club Puebla") -> 'Club Puebla'`,
`("Deportivo Toluca") -> 'Deportivo Toluca'`, `("CF Pachuca") -> 'Club Pachuca'`). Se preserva
el axioma del Juez (toda caption de competidor de Novibet resuelve a identidad canónica) y se
corrigen exclusivamente los literales esperados, en lugar de mutar el contrato sellado del
normalizador (lo que rompería `test_shield_multi_bookmaker_ingestion.py` y el catálogo
`CLUBS_MASTER`).
```

**RESOLUCIÓN RATIFICADA (ALT-1):** se preserva **íntegro** el contrato del normalizador sellado `[LN-QBE-012]` y se corrigen **exclusivamente los literales esperados del Juez** (`Club Puebla`, `Deportivo Toluca`, `Club Pachuca`). El axioma auditado —toda caption de competidor de Novibet resuelve a una identidad canónica, nunca a una cadena arbitraria— permanece intacto.

**ALTERNATIVA RECHAZADA (ALT-2):** mutar `canonicalize_team_name` para emitir los literales cortos `Puebla` / `Toluca` / `Pachuca`. **Rechazada:** habría roto el contrato sellado `[LN-QBE-012]`, el Juez `test_shield_multi_bookmaker_ingestion.py` y el catálogo `CLUBS_MASTER`, propagando la varianza a toda la cadena de identidad (colisión de granularidad ya erradicada por `docs/ID_REGISTRY.md`).

**CRITERIO FIDUCIARIO:** *fail-loud documental*. La tensión se resolvió en el plano de la **evidencia esperada** (el Juez) y jamás en el plano del **contrato canónico** (el normalizador), preservando la pureza de la fuente única de verdad de identidad de clubes.
