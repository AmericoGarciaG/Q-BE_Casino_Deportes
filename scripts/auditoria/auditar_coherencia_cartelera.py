# -*- coding: utf-8 -*-
"""
🔎 Q-BE — WRAPPER CLI DE LA SONDA DIAGNÓSTICA DE COHERENCIA RELACIONAL
[ARCH-1.4.34 · Enmienda de Saneamiento] · [ARCH-1.6.4 · Enmienda Nudo 3]
CLI Auditor (Read-Only, semáforo forense)

Régimen: `[DBBD-FUNGIBLE]` (capa de presentación). La FUENTE DE VERDAD es INMUTABLE y reside
EXCLUSIVAMENTE en `src/core/coherence_auditor.py` (`[DIRGEN-STRICT]`): las seis sondas, el
agregador semafórico, los modelos Pydantic y el contrato de salida del CLI.

Este módulo es un **Wrapper Puro**: no define funciones, clases ni constantes de auditoría.
Prohibido re-transcribir aquí la matemática del núcleo (Juez: `tests/shield/test_auditor_parity.py`).

Responsabilidades — las tres únicas permitidas:
  1. **Bootstrap de `sys.path`:** habilita la invocación por ruta de archivo
     (`python scripts/auditoria/auditar_coherencia_cartelera.py`) desde cualquier cwd; el
     Centro de Control despacha con rutas absolutas y `cwd` = raíz del repositorio.
  2. **Re-exportación explícita** del contrato público del núcleo, preservando la compatibilidad
     de importación de los consumidores históricos (`tests/shield/...`).
  3. **`main(argv)` delegante:** invoca `coherence_auditor.main(argv)` y devuelve su resultado;
     jamás una copia de la lógica.

Uso (contrato sellado, idéntico al histórico):
    python -m scripts.auditoria.auditar_coherencia_cartelera                 # diagnóstico (read-only)
    python -m scripts.auditoria.auditar_coherencia_cartelera --check         # EXIT 1 sólo ante 🔴
    python -m scripts.auditoria.auditar_coherencia_cartelera --jornada 11    # jornada explícita
    python -m scripts.auditoria.auditar_coherencia_cartelera --todo --json   # todas las jornadas

Semántica de salida: `--check` retorna `EXIT CODE 1` exclusivamente ante `DISCREPANCIA` (🔴);
`ADVERTENCIA` (🟡) y `SIN_VEREDICTO` (⚪) no bloquean el pre-vuelo. `--json` emite un único
objeto JSON puro por `stdout`. Degradación honesta (`[GOVERNANCE-01]`): la ausencia de evidencia
emite ⚪ y JAMÁS una discrepancia.
"""

import sys
from pathlib import Path
from typing import Optional, Sequence

# ── Nivel 1: bootstrap de ruta (la raíz del proyecto debe ser importable como paquete) ──────────
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ── Nivel 2: importación explícita del núcleo canónico (única fuente de verdad) ─────────────────
from src.core import coherence_auditor as _nucleo  # noqa: E402
from src.core.coherence_auditor import (  # noqa: E402
    FAMILIAS_CON_COBERTURA,
    GAMMA_BASE,
    GLIFO_NIVEL,
    ORDEN_SONDAS,
    OVERROUND_MAX_ADMISIBLE,
    OVERROUND_MIN_ADMISIBLE,
    OVERROUND_VIGILANCIA_MAX,
    OVERROUND_VIGILANCIA_MIN,
    PISO_BIVARIADO_MXN,
    PISO_VENTANILLA_MXN,
    SONDA_COHERENCIA_CAPA0,
    SONDA_DIVERGENCIA_MERCADO,
    SONDA_OVERROUND,
    SONDA_PARIDAD,
    SONDA_PISO_VENTANILLA,
    SONDA_TECHO_GOLES,
    TECHO_XG,
    TECHO_XG_ANTIRESONANCIA,
    TOL_PARIDAD_SIMPLEX,
    TVD_MAX,
    TVD_VIGILANCIA,
    HallazgoSonda,
    NivelSeveridad,
    ReporteCoherenciaPartido,
    auditar_coherencia_partido,
    calcular_codigo_salida,
)

__all__ = [
    "FAMILIAS_CON_COBERTURA",
    "GAMMA_BASE",
    "GLIFO_NIVEL",
    "ORDEN_SONDAS",
    "OVERROUND_MAX_ADMISIBLE",
    "OVERROUND_MIN_ADMISIBLE",
    "OVERROUND_VIGILANCIA_MAX",
    "OVERROUND_VIGILANCIA_MIN",
    "PISO_BIVARIADO_MXN",
    "PISO_VENTANILLA_MXN",
    "SONDA_COHERENCIA_CAPA0",
    "SONDA_DIVERGENCIA_MERCADO",
    "SONDA_OVERROUND",
    "SONDA_PARIDAD",
    "SONDA_PISO_VENTANILLA",
    "SONDA_TECHO_GOLES",
    "TECHO_XG",
    "TECHO_XG_ANTIRESONANCIA",
    "TOL_PARIDAD_SIMPLEX",
    "TVD_MAX",
    "TVD_VIGILANCIA",
    "HallazgoSonda",
    "NivelSeveridad",
    "ReporteCoherenciaPartido",
    "auditar_coherencia_partido",
    "calcular_codigo_salida",
    "main",
]


# ── Nivel 3: delegación pura al núcleo (única función local permitida) ──────────────────────────
def main(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada CLI. Read-Only: no muta la bóveda ni escribe archivos.

    Delegación pura: la semántica (argumentos, semáforo, JSON, código de salida) es la del núcleo
    `src/core/coherence_auditor.py` ([ARCH-1.4.34]); este wrapper no la replica ni la altera.
    """
    return _nucleo.main(argv)


if __name__ == "__main__":
    sys.exit(main())
