# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — SANEAMIENTO DE TRAYECTORIA, POSESIÓN Y CUARENTENA DE V16
Juez Inmutable: [LN-QBE-123] / [ARCH-1.4.63]
Base de Gobierno: Kybern Framework v12.0

Régimen declarado (Dual-Track honesto):
* `[DIRGEN-STRICT]` — `src/core/sovereign/factor_attribution.py`: el catálogo es TRANSCRIPCIÓN de
  magnitudes ya publicadas. Ningún λ, ninguna probabilidad y ninguna fórmula sellada se recalcula
  aquí; la trayectoria (`V31`/`V32`) es DIAGNÓSTICO y no insumo del motor.
* `[DBBD-FUNGIBLE]` — `src/core/sovereign/context_provider.py` (banderas de presencia) y
  `src/web/static/js/app.js` (vitrina: soporte forense único y barra de posesión normalizada).

Aislamiento hermético: cero red, cero navegador, cero base de datos. Las cuatro invarianzas se
verifican sobre funciones puras del catálogo y sobre el texto de los artefactos de vitrina.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from src.core.sovereign.factor_attribution import (
    _CATALOGO_44,
    derivar_taxonomia,
    estructurar_catalogo_44_variables,
)

RAIZ = Path(__file__).resolve().parents[2]


def _celda(identificador: str, datos: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Celda forense del id canónico dentro del catálogo servido (falla si no existe)."""
    catalogo = estructurar_catalogo_44_variables(datos_partido=datos or {})
    for dimension in catalogo["dimensiones"]:
        for variable in dimension["variables"]:
            if variable["id"] == identificador:
                return variable
    raise AssertionError(f"`{identificador}` desapareció del catálogo: la celda es contrato.")


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [INVARIANZA 1] V16 permanece en el catálogo de 32 y queda en CUARENTENA (FUERA DE FUENTE)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def test_v16_en_cuarentena_sin_ruta_de_extraccion():
    """V16 conserva su fila (integridad del 32V y de `𝒯_Def`) pero no enciende jamás.

    La cuarentena es ESTRUCTURAL: ni el centinela heredado `big_chances_conceded` en el bloque del
    club, ni la macro torneal, ni la telemetría pueden iluminarla. Cero cero fabricado.
    """
    catalogo = estructurar_catalogo_44_variables(datos_partido={})
    assert catalogo["total_variables"] == 32, (
        "La cuarentena NO purga el catálogo: `derivar_taxonomia` exige las 32 celdas [LN-QBE-122]."
    )

    v16 = _celda("V16")
    assert v16["estado"] == "SIN EVIDENCIA"
    assert v16["local"] is None and v16["visita"] is None
    assert v16["origen"] == "FUERA DE FUENTE", (
        "La celda no extraíble debe declarar su procedencia rota, no simular un sensor activo."
    )
    assert "big chances" in v16["nota"].lower()

    # Defensa en profundidad: la clave heredada tampoco la enciende.
    con_centinela = _celda("V16", {
        "home_team_stats": {"big_chances_conceded": 3, "bc_conceded": 3},
        "away_team_stats": {"big_chances_conceded": 1, "bc_conceded": 1},
        "insumos_factivados": {
            "macro_stats": {"local": {"big_chances_conceded_per_match": 1.5}},
        },
    })
    assert con_centinela["estado"] == "SIN EVIDENCIA", (
        "Una fuente inexistente no puede iluminarse por la espalda de una clave heredada."
    )

    # La familia 𝒯_Def sigue resolviendo (si V16 desapareciera, este `derivar_taxonomia` estallaría).
    taxonomia_def = derivar_taxonomia("𝒯_Def", {
        "V16": ("Big Chances Concedidas", "n", "Cuarentena [LN-QBE-123]"),
    })
    assert [fila[0] for fila in taxonomia_def] == ["V16"]
    assert sum(1 for fila in _CATALOGO_44 if fila[0] == "V16") == 1


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [INVARIANZA 2] V31 / V32 se encienden desde el bloque `trayectoria` (transcripción pura)
# ═════════════════════════════════════════════════════════════════════════════════════════════
def test_v31_v32_transcriben_el_bloque_trayectoria():
    """`trajectory_provider` publica `pts_last5_*` / `xpts_diff_*`: la celda los TRANSCRIBE."""
    datos = {
        "insumos_factivados": {
            "trayectoria": {
                "bloque": "trayectoria",
                "status": "OPERATIVO",
                "insumos": {
                    "pts_last5_local": 11,
                    "pts_last5_visita": 4,
                    "xpts_diff_local": 1.75,
                    "xpts_diff_visita": -0.5,
                },
            },
        },
    }

    v31 = _celda("V31", datos)
    assert v31["estado"] == "EVALUADO", "La forma 5P publicada debe encender V31."
    assert v31["local"] == "11" and v31["visita"] == "4"
    assert "[LN-QBE-123]" in v31["nota"]

    v32 = _celda("V32", datos)
    assert v32["estado"] == "EVALUADO", "La varianza ΔxPTS publicada debe encender V32."
    assert v32["local"] == "+1.75" and v32["visita"] == "-0.50", (
        "El signo de ΔxPTS es semántica: la transcripción jamás lo pierde."
    )
    assert "[LN-QBE-123]" in v32["nota"]

    # Sad path: sin bloque `trayectoria` no se fabrica una sola cifra.
    sin_bloque = estructurar_catalogo_44_variables(datos_partido={})
    planas = {
        fila["id"]: fila["estado"]
        for dimension in sin_bloque["dimensiones"]
        for fila in dimension["variables"]
    }
    assert planas["V31"] == "SIN EVIDENCIA" and planas["V32"] == "SIN EVIDENCIA"


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [INVARIANZA 3] V30 no convierte la ignorancia en `+0.0 d`
# ═════════════════════════════════════════════════════════════════════════════════════════════
def test_v30_no_emite_cero_cuando_el_fixture_no_reconstruye_fechas():
    """La ausencia DECLARADA por `context_provider` manda sobre el centinela plano `0.0`.

    `homologar_temporada_optah2h` publica `delta_descanso_dias = 0.0` cuando el corpus no tiene
    `kickoff_utc`: ese cero es ausencia, no magnitud. La celda debe quedar `SIN EVIDENCIA`.
    """
    refutado = {
        "insumos_factivados": {
            "contexto": {
                "bloque": "contexto",
                "status": "SIN EVIDENCIA",
                "insumos": {
                    "delta_descanso_dias": 0.0,
                    "descanso_local": None,
                    "descanso_visita": None,
                    "descanso_evaluado": False,
                },
            },
        },
        "delta_descanso_dias": 0.0,
    }
    celda_refutada = _celda("V30", refutado)
    assert celda_refutada["estado"] == "SIN EVIDENCIA", (
        "Un `None` de fixture jamás se publica como `+0.0 d` ([GOVERNANCE-01])."
    )
    assert celda_refutada["local"] is None and celda_refutada["visita"] is None

    # Control positivo: el descanso REALMENTE reconstruido se transcribe con su signo.
    evaluado = {
        "insumos_factivados": {
            "contexto": {
                "bloque": "contexto",
                "status": "EVALUADO",
                "insumos": {
                    "delta_descanso_dias": 2.0,
                    "descanso_local": 5.0,
                    "descanso_visita": 3.0,
                    "descanso_evaluado": True,
                },
            },
        },
    }
    celda_evaluada = _celda("V30", evaluado)
    assert celda_evaluada["estado"] == "EVALUADO"
    # ΔDías es magnitud de CONTEXTO (no bilateral): la columna de la visita permanece `None`.
    assert celda_evaluada["local"] == "+2.0 d" and celda_evaluada["visita"] is None


# ═════════════════════════════════════════════════════════════════════════════════════════════
# [INVARIANZA 4] Vitrina: soporte forense ÚNICO y posesión normalizada por complemento
# ═════════════════════════════════════════════════════════════════════════════════════════════
def test_acordeon_sin_tabla_duplicada_y_posesion_normalizada():
    """El acordeón no inyecta una segunda tabla por dimensión; la posesión se normaliza."""
    fuente = (RAIZ / "src" / "web" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    inicio = fuente.index("function _tablaDimension32(")
    fin = fuente.index("function _hidratarBadgesDimension32(")
    acordeon = fuente[inicio:fuente.index("function _soporteForense32(")]
    assert "<table" not in acordeon, (
        "La tabla duplicada por dimensión fue derogada: el Card es el único vehículo de lectura."
    )
    assert "_cardDimension32(dimension)" in acordeon
    assert "vars44-badge-slot" in acordeon

    # [DES-QBE-064] no se demuele: el soporte forense sobrevive como UNA sola tabla consolidada.
    assert "function _soporteForense32(" in fuente, (
        "El soporte de auditoría de 7 columnas debe sobrevivir en un único bloque consolidado."
    )
    soporte = fuente[fuente.index("function _soporteForense32("):]
    soporte = soporte[:soporte.index("function abrirModal44Variables(")]
    for columna in ("Variable", "Local", "Visita", "Z-Score", "Origen", "Estado", "Impacto"):
        assert f"<th>{columna}</th>" in soporte, f"Columna forense ausente en el soporte: {columna}"
    assert soporte.count("<thead>") == 1, (
        "El soporte consolidado publica UN solo encabezado de columnas; la cabecera de familia "
        "viaja en el cuerpo de la tabla (HTML válido: `thead` es único)."
    )

    assert "Posesión s/d" not in fuente, (
        "El rótulo de ausencia ya no declara un porcentaje inexistente: la barra se normaliza."
    )
    posesion = fuente[fuente.index("function _cardPosesion32("):]
    posesion = posesion[:posesion.index("function _balanzaGoles32(")]
    assert "(local / total) * 100" in posesion, (
        "El ancho de la barra se normaliza por complemento bipartito [ARCH-1.4.63]."
    )
    assert "Posesión sin evidencia" in posesion
