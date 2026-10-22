# -*- coding: utf-8 -*-
"""[LN-QBE-122] Juez de la Purga Nominal ALT-B — Régimen: [DBBD-FUNGIBLE] (in-memory, cero red).

Ratifica `VAR-2026-10-21-FASE-B-PURGA-V` (Opción ALT-B) sobre `[LN-QBE-121]` §P.5:

1. **INVARIANTA 1 — Derivación estructural:** `derivar_taxonomia` toma NOMBRE y ORDEN del catálogo
   único (`[LN-QBE-120]`) y anexa los `AUX_*` al final; un `VXX` de otra familia es un error de
   contrato (jamás una celda robada).
2. **INVARIANTA 2 — Taxonomías servidas:** los proveedores publican EXACTAMENTE las celdas del
   catálogo que pueden sostener más sus auxiliares declarados.
3. **INVARIANTA 3 — Cero ids derogados:** ningún módulo del alcance ratificado porta un
   identificador `VXX` fuera del catálogo de 32 variables, ni en código ni en literales.
4. **INVARIANTA 4 — Prefijo auxiliar:** toda magnitud sin celda se publica con `AUX_` y jamás con
   un `VXX`.
5. **INVARIANTA 5 — UI alineada:** `app.js` sólo consume celdas del catálogo (las tarjetas del Hero
   Card leen `V06`/`V12`/`V18`/`V26`/`V27`/`V28`/`V29`/`V30`).

Base de Gobierno: Kybern Framework v12.0 [GOV-TEST-01] (Pure In-Memory, Zero Network, Zero DB).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.core.sovereign.attack_defense_core import _TAXONOMIA_DIM_2, _TAXONOMIA_DIM_3
from src.core.sovereign.factor_attribution import (
    PREFIJO_AUXILIAR,
    _CATALOGO_44,
    derivar_taxonomia,
    es_identificador_auxiliar,
    nombre_de_celda,
)
from src.core.sovereign.telemetry_provider import _TAXONOMIA_DIM_1, _TAXONOMIA_DIM_4

RAIZ = Path(__file__).resolve().parents[2]

# Módulos bajo el alcance ratificado por la varianza FASE-B-PURGA-V.
MODULOS_PURGADOS = (
    "src/core/sovereign/attack_defense_core.py",
    "src/core/sovereign/telemetry_provider.py",
    "src/core/sovereign/context_provider.py",
    "src/core/sovereign/trajectory_provider.py",
    "scripts/laboratorio/sandbox_ataque_defensa_pipeline.py",
    "scripts/laboratorio/sandbox_volumen_porteria_pipeline.py",
    "scripts/laboratorio/sandbox_contexto_shocks_pipeline.py",
    "scripts/laboratorio/sandbox_trayectoria_momento_pipeline.py",
    "scripts/laboratorio/sandbox_h2h_pipeline.py",
)

# Identificadores derogados por `[LN-QBE-120]`: fuera del catálogo de 32 variables.
IDS_DEROGADOS = frozenset({f"V{n:02d}" for n in range(33, 45)})
CELDAS_CATALOGO = frozenset(fila[0] for fila in _CATALOGO_44)

# Celdas que cada módulo del alcance puede citar: su dimensión del catálogo + sus `AUX_*`.
ESPERADOS = {
    "src/core/sovereign/attack_defense_core.py":
        {"V06", "V07", "V08", "V09", "AUX_XGOT_90", "V12", "V13", "V15", "V16", "AUX_PPDA"},
    "scripts/laboratorio/sandbox_ataque_defensa_pipeline.py":
        {"V06", "V07", "V08", "V09", "AUX_XGOT_90", "V12", "V13", "V15", "V16", "AUX_PPDA"},
    "src/core/sovereign/telemetry_provider.py":
        {"V01", "V02", "AUX_PASES_PROG", "AUX_ENTRADAS_UT", "V17", "V18", "V19"},
    "scripts/laboratorio/sandbox_volumen_porteria_pipeline.py":
        {"V01", "V02", "AUX_PASES_PROG", "AUX_ENTRADAS_UT", "V17", "V18", "V19"},
    "src/core/sovereign/context_provider.py":
        {"V29", "V30", "AUX_XG_BAJAS", "AUX_XGA_BAJAS"},
    "scripts/laboratorio/sandbox_contexto_shocks_pipeline.py":
        {"V29", "V30", "AUX_Q_MOD_H", "AUX_Q_MOD_A"},
    "src/core/sovereign/trajectory_provider.py":
        {"V31", "V32", "AUX_M_XG", "AUX_M_XGA"},
    "scripts/laboratorio/sandbox_trayectoria_momento_pipeline.py":
        {"V31", "V32", "AUX_M_XG", "AUX_M_XGA"},
    "scripts/laboratorio/sandbox_h2h_pipeline.py":
        {"V26", "V27", "V28", "AUX_XG_HIST"},
}

_CELDA_CITADA = re.compile(r"[\"'](V\d\d|AUX_[A-Z0-9_]+)[\"']")


def _ids(taxonomia) -> list:
    return [identificador for identificador, _n, _u, _no in taxonomia]


# ── INVARIANTA 1 · Derivación estructural desde el catálogo único ──────────────────────────────
def test_invarianza_1_nombre_y_orden_vienen_del_catalogo():
    """El nombre forense y el orden son los del catálogo; el proveedor sólo aporta unidad y nota."""
    locales = {
        "V08": ("alias local", "BC/PJ", "nota local"),
        "V06": ("alias local", "xG/PJ", "nota local"),
        "AUX_XGOT_90": ("xGOT sin celda", "xGOT/90", "nota auxiliar"),
    }
    derivada = derivar_taxonomia("𝒯_Rem", locales)
    assert [fila[0] for fila in derivada] == ["V06", "V08", "AUX_XGOT_90"]
    assert derivada[0][1] == nombre_de_celda("V06") == "xG por Partido (ancla npxG)"
    assert derivada[1][1] == "Big Chances Creadas"
    assert derivada[0][2] == "xG/PJ" and derivada[0][3] == "nota local"
    assert derivada[2][1] == "xGOT sin celda", "El AUX conserva su nombre local (no usurpa celda)."


def test_invarianza_1_rechaza_celda_de_otra_familia():
    """Un `VXX` ajeno a la familia es un error de contrato: se rechaza en voz alta."""
    with pytest.raises(ValueError, match="LN-QBE-122"):
        derivar_taxonomia("𝒯_Vol", {"V12": ("xGA", "xGA/PJ", "no pertenece a 𝒯_Vol")})


def test_invarianza_1_prefijo_auxiliar_legislado():
    assert PREFIJO_AUXILIAR == "AUX_"
    assert es_identificador_auxiliar("AUX_PPDA") is True
    assert es_identificador_auxiliar("V12") is False
    assert es_identificador_auxiliar(None) is False


# ── INVARIANTA 2 · Taxonomías servidas por los proveedores ────────────────────────────────────
def test_invarianza_2_taxonomia_volumen():
    assert _ids(_TAXONOMIA_DIM_1) == ["V01", "V02", "AUX_PASES_PROG", "AUX_ENTRADAS_UT"]
    assert _ids(_TAXONOMIA_DIM_4) == ["V17", "V18", "V19"]


def test_invarianza_2_taxonomia_ataque_defensa():
    assert _ids(_TAXONOMIA_DIM_2) == ["V06", "V07", "V08", "V09", "AUX_XGOT_90"]
    assert _ids(_TAXONOMIA_DIM_3) == ["V12", "V13", "V15", "V16", "AUX_PPDA"]
    for identificador, nombre, _unidad, _nota in _TAXONOMIA_DIM_2 + _TAXONOMIA_DIM_3:
        if identificador.startswith("V"):
            assert nombre == nombre_de_celda(identificador), (
                f"{identificador} debe rotularse con el nombre del catálogo (fidelidad FotMob)."
            )


# ── INVARIANTAS 3 y 4 · Cero ids derogados y prefijo auxiliar ─────────────────────────────────
@pytest.mark.parametrize("ruta", MODULOS_PURGADOS)
def test_invarianza_3_solo_celdas_esperadas(ruta):
    """Cada módulo sólo cita su dimensión del catálogo + sus auxiliares declarados."""
    texto = (RAIZ / ruta).read_text(encoding="utf-8")
    citados = set(_CELDA_CITADA.findall(texto))
    fuera = sorted(citados - ESPERADOS[ruta])
    assert fuera == [], f"{ruta} cita identificadores fuera de su taxonomía ratificada: {fuera}"
    assert citados & IDS_DEROGADOS == set(), f"{ruta} conserva ids derogados (V33-V44)."


@pytest.mark.parametrize("ruta", MODULOS_PURGADOS)
def test_invarianza_4_auxiliares_bien_formados(ruta):
    """Toda magnitud sin celda se publica como `AUX_*` en mayúsculas (jamás como `VXX`)."""
    texto = (RAIZ / ruta).read_text(encoding="utf-8")
    auxiliares = {identificador for identificador in _CELDA_CITADA.findall(texto)
                  if identificador.startswith(PREFIJO_AUXILIAR)}
    for identificador in auxiliares:
        assert re.fullmatch(r"AUX_[A-Z0-9_]+", identificador), identificador
    # El sufijo del auxiliar nunca es un número de celda (cero usurpación encubierta).
    assert all(not identificador.startswith("AUX_V") for identificador in auxiliares)


def test_invarianza_3_ningun_id_derogado_es_auxiliar():
    """Los auxiliares declarados en el alcance no reutilizan nombres de celdas derogadas."""
    exportados = set()
    for ruta in MODULOS_PURGADOS:
        texto = (RAIZ / ruta).read_text(encoding="utf-8")
        exportados |= {identificador for identificador in _CELDA_CITADA.findall(texto)
                       if identificador.startswith(PREFIJO_AUXILIAR)}
    assert exportados, "La purga debe declarar auxiliares (m_xG, PPDA, bajas, xGOT/90)."
    assert exportados & IDS_DEROGADOS == set()


# ── INVARIANTA 5 · UI alineada al catálogo ────────────────────────────────────────────────────
def test_invarianza_5_appjs_solo_consume_celdas_del_catalogo():
    texto = (RAIZ / "src/web/static/js/app.js").read_text(encoding="utf-8")
    citados = {identificador for identificador in _CELDA_CITADA.findall(texto)
               if identificador.startswith("V")}
    assert citados, "El Hero Card debe citar celdas del catálogo."
    ajenas = sorted(citados - CELDAS_CATALOGO)
    assert ajenas == [], f"app.js cita celdas ajenas al catálogo de 32 variables: {ajenas}"
    assert citados & IDS_DEROGADOS == set()
    # Las tarjetas anatómicas leen las celdas canónicas del remapeo [LN-QBE-120].
    for identificador in ("V06", "V12", "V18", "V26", "V27", "V28", "V29", "V30"):
        assert identificador in citados, f"app.js debe leer {identificador}."
