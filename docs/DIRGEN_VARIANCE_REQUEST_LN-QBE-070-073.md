# 📋 FICHA DE VARIANZA: CONTRATO DE `approved_matches` PARA KELLY ATENUADO (FAMILIA LN-QBE-070 … LN-QBE-073)
**ID:** `VAR-2026-LN-QBE-070-073`  
**ESTADO:** `ABIERTO — NODO DE SEGUIMIENTO DECLARADO (mitigación operativa aplicada)`  
**ORIGEN LEGISLATIVO:** `docs/LOGIC.md:456` (nodo `[LN-QBE-070]` *Router de Utilidad Pura, Kelly y Techo Aritmético* — Proceso 5, *Asignación de Capital*), que declara textualmente la existencia de esta ficha.  
**ALCANCE:** Familia `[LN-QBE-070]` … `[LN-QBE-073]` — Router de Utilidad Pura/Kelly (`[LN-QBE-070]`, `[LN-QBE-070-B]`), piso de ventanilla (`[LN-QBE-071]`), contracción baricéntrica y asignación monótona (`[LN-QBE-081]`, `[LN-QBE-082]`) y Slider Dinámico de Certeza (`[LN-QBE-073]`).

**TRANSCRIPCIÓN ÍNTEGRA DE LA NOTA DE MATERIALIZACIÓN (FASE 4) VIGENTE:**
> **Nota de materialización (Fase 4):** la sustitución directa en `PortfolioEngine.build_plan` exige que el contrato de `approved_matches` exponga $p_i$, $O_i$ y $\Delta_{\text{epist}}$. Mientras ese contrato no se extienda, el techo de cartera se aplica con `aplicar_hard_caps_constitucionales` (8% individual / 25% global) y el piso con `[LN-QBE-071]`.

**HALLAZGO FÁCTICO (Paso 0 — Auditoría de Registro Legislativo):** esta ficha era citada por `docs/LOGIC.md:456` y no existía físicamente en disco (referencia colgante detectada por el Juez de Registro). Se materializa por **transcripción estricta** del texto normativo ya vigente: **aquí no se legisla ninguna resolución nueva** ni se altera una coma del libro lógico. La única adición es el registro documental del nodo de seguimiento ya declarado.

**RESOLUCIÓN PENDIENTE (competencia exclusiva del Director y del Arquitecto):** extender el contrato de `approved_matches` para exponer $p_i$, $O_i$ y $\Delta_{\text{epist}}$, habilitando la sustitución directa del techo por `calcular_kelly_atenuado` (`[VAULT-CORE-070-KELLY]` / `src/core/contracts/portfolio_math.py`, gobernado por `[LN-QBE-070-B]`).

**MITIGACIÓN OPERATIVA VIGENTE (no bloqueante):** techo con `aplicar_hard_caps_constitucionales` (8% individual / 25% global) y piso de ventanilla de $2.00 MXN (`[LN-QBE-071]`, `PISO_MINIMO_BOLETO`).

**CRITERIO FIDUCIARIO:** cero invención normativa · cero modificación de constantes protegidas · trazabilidad inmutable hacia el nodo fuente `docs/LOGIC.md:456`.
