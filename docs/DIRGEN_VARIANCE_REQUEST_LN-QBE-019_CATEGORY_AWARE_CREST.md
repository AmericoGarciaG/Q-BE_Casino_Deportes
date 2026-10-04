# 📋 FICHA DE VARIANZA: ESCALERA DE ESCUDOS CIEGA A LA CATEGORÍA DE GÉNERO
**ID:** `VAR-2026-LN-QBE-019-CATEGORY-AWARE-CREST`  
**ESTADO:** `ABIERTO — REQUIERE DICTAMEN DE LA TRÍADA`  
**RÉGIMEN:** `[DIRGEN-STRICT]` (colisión de dos planos sellados; **prohibida la corrección autónoma**)  
**COORDENADAS:** `src/normalization/league_provisioner.py` — sección *4. Clubes* (invocación de la escalera sellada para el `crest_url` del club) · `src/storage/crest_resolver.py:37-51 y 56-92` (`obtener_slug_club` / `resolver_escudo_canonico`, sellados por `[LN-QBE-019]`).

**EVIDENCIA FÁCTICA (verificación funcional en vivo del Paso 3 de SPRINT 2 Capa 2, ejecutada en DB SQLite en memoria — cero escrituras en `data/qbe_database.db`):**
```
OK provision 1: FOTMOB_999001 MEX_2026_APERTURA ['club-america-femenil', 'real-sociedad-b'] mu = 2.6
OK escudo anti-hotlink del club femenil: /static/img/crests/club-america.png ...
```
El `canonical_slug` se discrimina **correctamente** (`club-america-femenil`, guarda `[LN-QBE-095]` en verde), pero el activo persistido corresponde al **primer equipo varonil**: `_generar` la escalera sellada resuelve por nombre canónico, y `canonicalize_team_name("Club América Femenil")` colapsa a `"Club América"` (`src/ingestion/normalizer.py:35-38`, precedencia de alias), produciendo el slug `club-america` y ancorando el escudo varonil (`49169` bytes, piso `[LN-QBE-019]` superado ⇒ nivel 1 de la escalera).

**DIAGNÓSTICO CAUSAL:** asimetría de granularidad entre dos planos sellados — `[LN-QBE-095]` legisla identidad **categorizada** (slug con sufijo), mientras `[LN-QBE-019]` legisla una escalera de activos **ciega a la categoría** (nombre canónico plano → slug plano). El acoplamiento `[ARCH-1.5.12]` los encuentra por primera vez, y la intersección produce un *binding cosmético falso* (identidad misma institución, rama distinta). No hay corrupción de identidad, de marcadores ni de probabilidad: `canonical_slug`, vínculos de `Match` y distribuciones soberanas permanecen correctos.

**ABANICO DE ALTERNATIVAS EVALUADAS:**
* **ALT-1 (recomendada):** volver **categoría-consciente** la escalera sellada `[LN-QBE-019]` en `crest_resolver.py` (nivel 1 con slug categorizado y prohibición explícita de anclar un activo cuyo slug difiera del categorizado, degradando al fallback institucional). Preserva la identidad visual de cada rama. **Requiere autorización explícita** (toca un componente sellado `[DIRGEN-STRICT]`).
* **ALT-2:** legislar en `[ARCH-1.5.12]` que toda entidad **no neutra** (`FEMENIL`/`FILIAL`/`SUB20`) jamás consume la escalera ciega y persiste el activo institucional neutro mientras el HITL no ancle el activo categorizado. Cero cambios en código sellado, pero deja el escudo femenil en espera de curación.

**SOLUCIÓN RECOMENDADA Y CRITERIO FIDUCIARIO:** **ALT-1**, por coherencia con el axioma de identidad única de `[LN-QBE-095]` y porque la rama femenil es una entidad soberana distinta (no un alias del varonil). Preservación matemática intacta: el cambio es exclusivamente de resolución de activos, sin tocar una constante ni una fórmula.

**DIFF PROPUESTO:** diferido — **ALTO AL FUEGO**: no se toca `src/storage/crest_resolver.py` ni se inventa regla alguna sin dictamen de la Tríada.
