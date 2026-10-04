# -*- coding: utf-8 -*-
"""
[ARCH-1.4.25] Paquete de Normalización, Jerga y Desambiguación (Capa 2 — Identity Brain).

Encapsula la inteligencia de resolución de entidades del Data Nexus en un paquete autónomo:
* `gender_guards.py`        → `[LN-QBE-095]` Guardas léxicas de género y categoría.
* `temporal_disambiguator.py`→ `[LN-QBE-094]` Desambiguación temporal en ventana [t_cierre ± 72h].
* `entity_resolver.py`      → Mapeo de jerga de quinielas a identidades oficiales.
* `asset_vault_service.py`  → Bóveda soberana de activos locales (anti-hotlinking).
* `league_provisioner.py`   → `[ARCH-1.5.12]` Aprovisionador JIT de ligas y clubes.

Régimen: [DIRGEN-STRICT] (nodos sellados de `docs/LOGIC.md` y `docs/ARCH.md`).
"""
