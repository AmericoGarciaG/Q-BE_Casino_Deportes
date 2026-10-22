# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — H2H DIMENSION POPULATION & ACCORDION UI SUITE
Juez Inmutable: [LN-QBE-105]
Base de Gobierno: Kybern Framework v13.5

Régimen declarado (Dual-Track honesto):
* `[DIRGEN-STRICT]` — `src/core/sovereign/h2h_provider.py` (bandera de sede), la agregación
  aritmética de `h2h_stats` en `src/core/sovereign_pipeline.py` y su transcripción a V39/V40/V41
  en `src/core/sovereign/factor_attribution.py`. Cero recálculo de fórmulas selladas.
* `[DBBD-FUNGIBLE]` — exhibición del acordeón forense (`app.js`).

Aislamiento hermético: cero red, cero navegador, cero base de datos. El corpus H2H se materializa
en `tmp_path` y el orquestador se invoca en memoria.
"""

import json
from datetime import datetime
from pathlib import Path

from src.core.sovereign.factor_attribution import estructurar_catalogo_44_variables


def test_invarianza_variables_h2h_calculadas_y_formateadas():
    """[INVARIANZA 1]: V26, V27 y V28 deben estar EVALUADAS y formateadas correctamente."""
    datos_mock = {
        "insumos_factivados": {
            "h2h_stats": {
                "record_general": "2V - 1E - 1D",
                "dif_goles": "+2",
                "record_sede": "0V - 1E - 1D (Visita)"
            }
        }
    }

    cat = estructurar_catalogo_44_variables(datos_partido=datos_mock)

    # [LN-QBE-120] La memoria longitudinal vive en 𝒯_Ctx ("Memoria, Forma y Contexto").
    dim_h2h = next(d for d in cat["dimensiones"] if "Memoria" in d["nombre"])
    v26 = next(v for v in dim_h2h["variables"] if v["id"] == "V26")
    v27 = next(v for v in dim_h2h["variables"] if v["id"] == "V27")
    v28 = next(v for v in dim_h2h["variables"] if v["id"] == "V28")
    v32 = next(v for v in dim_h2h["variables"] if v["id"] == "V32")

    # Aserciones V26 (antiguo V39: récord H2H)
    assert v26["estado"] == "EVALUADO"
    assert v26["local"] == "2V - 1E - 1D"

    # Aserciones V27 (antiguo V40: diferencial de goles)
    assert v27["estado"] == "EVALUADO"
    assert v27["local"] == "+2"

    # Aserciones V28 (antiguo V41: récord en sede)
    assert v28["estado"] == "EVALUADO"
    assert v28["local"] == "0V - 1E - 1D (Visita)"

    # Aserciones V32 (Varianza ΔxPTS: debe permanecer intocable en Fase 6)
    assert v32["estado"] == "SIN EVIDENCIA"


# ═════════════════════════════════════════════════════════════════════════════════════════════
# Inversiones complementarias ratificadas (Dictamen 2026-10-17, Opción A)
# ═════════════════════════════════════════════════════════════════════════════════════════════
CORPUS_SEDE = {
    "esquema": "h2h_corpus_v1",
    "partidos": [
        # Sede del local evaluado (Chivas local ⇒ es_local_sede = True).
        {"fecha": "2025-08-15", "local_slug": "chivas-guadalajara",
         "visitante_slug": "club-america", "goles_local": 1, "goles_visita": 1},
        # Sede del visitante (América local ⇒ es_local_sede = False para Chivas).
        {"fecha": "2026-05-01", "local_slug": "club-america",
         "visitante_slug": "chivas-guadalajara", "goles_local": 0, "goles_visita": 3},
    ],
}


def _payload_suficiente(**extra) -> dict:
    """Registro fáctico suficiente (Puebla vs Atlante): sólo insumos publicados."""
    datos = {
        "match_id": "M_H2H_105",
        "competition_id": "MEX_LIGAMX",
        "home_team_slug": "puebla",
        "away_team_slug": "atlante",
        "home_team_stats": {
            "pj": 8, "gf": 14, "gc": 6,
            "xg": 12.8, "xga": 8.0, "sot": 40, "sota": 32, "possession": 53.5,
        },
        "away_team_stats": {
            "pj": 8, "gf": 9, "gc": 12,
            "xg": 8.8, "xga": 12.0, "sot": 24, "sota": 32, "possession": 46.5,
        },
        "home_split_stats": {"pj": 4},
        "away_split_stats": {"pj": 4},
    }
    datos.update(extra)
    return datos


def test_proveedor_h2h_publica_bandera_de_sede(tmp_path):
    """[INVARIANZA 2 — SAD PATH DEL PROVEEDOR]: cada duelo declara si el local evaluado jugó en
    su propia sede, sin destruir la proyección de perspectiva ya sellada.
    """
    from src.core.sovereign.h2h_provider import CAMPOS_DUELO, obtener_h2h_unificado

    ruta = tmp_path / "corpus_sede_105.json"
    ruta.write_text(json.dumps(CORPUS_SEDE, ensure_ascii=False), encoding="utf-8")

    duelos = obtener_h2h_unificado(
        None, "chivas-guadalajara", "club-america", datetime(2026, 6, 1), ruta_corpus=ruta
    )
    assert len(duelos) == 2, f"El corpus sintético publica dos duelos: {len(duelos)}"
    assert "es_local_sede" in CAMPOS_DUELO, "El contrato debe publicar la bandera de sede."

    por_fecha = {duelo["fecha"]: duelo for duelo in duelos}
    assert por_fecha["2025-08-15"]["es_local_sede"] is True, (
        "Chivas fue local en ese duelo histórico: la bandera debe ser True."
    )
    assert por_fecha["2026-05-01"]["es_local_sede"] is False, (
        "América fue local en ese duelo histórico: para Chivas la bandera debe ser False."
    )

    # La perspectiva sellada NO se altera por la bandera: 1-1 y 3-0 desde Chivas.
    assert (por_fecha["2025-08-15"]["goles_local"], por_fecha["2025-08-15"]["goles_visita"]) == (1, 1)
    assert (por_fecha["2026-05-01"]["goles_local"], por_fecha["2026-05-01"]["goles_visita"]) == (3, 0)


def test_precedencia_legacy_v39_sin_h2h_stats():
    """[INVARIANZA 3 — RETROCOMPATIBILIDAD]: sin bloque `h2h_stats` la ruta heredada de V26 (V39→V26, [LN-QBE-120])
    (`"N partidos"`) permanece byte-idéntica y EVALUADA.
    """
    catalogo = estructurar_catalogo_44_variables({
        "insumos_factivados": {"h2h_conteo": 5},
    })
    planas = {v["id"]: v for d in catalogo["dimensiones"] for v in d["variables"]}

    assert planas["V26"]["estado"] == "EVALUADO"
    assert planas["V26"]["local"] == "5 partidos", (
        "La telemetría heredada de la ventana H2H no puede degradarse por la ampliación."
    )
    assert planas["V26"]["visita"] is None


def test_pipeline_agrega_h2h_stats_y_declara_sede_vacia():
    """[INVARIANZA 4 — AGREGACIÓN Y SAD PATH DE SEDE]: el orquestador cuenta W-D-L, suma ΔG y
    emite `"Sin antecedentes locales"` cuando ningún duelo acredita la sede evaluada.
    """
    from src.core.sovereign_pipeline import generar_distribucion_soberana

    # Caso A — tres duelos con bandera: 1V-1E-1D, ΔG = -1, visitante 1V-0E-1D en sede.
    con_sede = generar_distribucion_soberana(
        match_id="M_H2H_105_SEDE",
        raw_match_data=_payload_suficiente(h2h_matches=[
            {"dias_antiguedad": 100, "goles_local": 2, "goles_visita": 1, "es_local_sede": True},
            {"dias_antiguedad": 200, "goles_local": 1, "goles_visita": 1, "es_local_sede": False},
            {"dias_antiguedad": 300, "goles_local": 0, "goles_visita": 2, "es_local_sede": True},
        ]),
    )
    stats = con_sede.audit_trace.insumos_factivados["h2h_stats"]
    assert stats["record_general"] == "1V - 1E - 1D"
    assert stats["dif_goles"] == "-1"
    assert stats["record_sede"] == "1V - 0E - 1D (Visita)"

    # Caso B — filas históricas sin bandera: no se fabrica sede alguna.
    sin_bandera = generar_distribucion_soberana(
        match_id="M_H2H_105_LEGACY",
        raw_match_data=_payload_suficiente(h2h_matches=[
            {"dias_antiguedad": 100, "goles_local": 2, "goles_visita": 1},
            {"dias_antiguedad": 200, "goles_local": 1, "goles_visita": 1},
        ]),
    )
    heredado = sin_bandera.audit_trace.insumos_factivados["h2h_stats"]
    assert heredado["record_general"] == "1V - 1E - 0D"
    assert heredado["dif_goles"] == "+1"
    assert heredado["record_sede"] == "Sin antecedentes locales"

    # Caso C — rama de ignorancia S(I)=0: el paquete también declara h2h_stats (Axioma 3).
    ignorancia = generar_distribucion_soberana(
        match_id="M_H2H_105_IGN",
        raw_match_data={
            "home_team_stats": {"pj": 1},
            "away_team_stats": {"pj": 1},
            "h2h_matches": [
                {"dias_antiguedad": 100, "goles_local": 3, "goles_visita": 0, "es_local_sede": True},
            ],
        },
    )
    assert ignorancia.audit_trace.suficiencia_S_I == 0
    assert ignorancia.audit_trace.insumos_factivados["h2h_stats"] == {
        "record_general": "1V - 0E - 0D",
        "dif_goles": "+3",
        "record_sede": "0V - 0E - 1D (Visita)",
    }


def test_acordeon_forense_sin_rotulo_literal_en_la_plantilla():
    """[INVARIANZA 5 — REPARACIÓN UI · DBBD-FUNGIBLE]: el `<summary>` del acordeón jamás porta un
    rótulo hardcodeado; el badge se hidrata desde los contadores servidos.
    """
    raiz = Path(__file__).resolve().parents[2]
    fuente = (raiz / "src" / "web" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    inicio = fuente.index("function _tablaDimension32(")
    fin = fuente.index("function _hidratarBadgesDimension32(")
    plantilla = fuente[inicio:fin]
    assert "SIN EVALUAR" not in plantilla, (
        "El rótulo de ausencia debe venir del badge servido, no de la plantilla del acordeón."
    )
    assert "vars44-badge-slot" in plantilla

    constructor = fuente[fuente.index("function _badgeDimension32("):inicio]
    assert "variables_evaluadas" in constructor and "total_variables" in constructor
    assert "textContent" in constructor and "innerHTML" not in constructor


