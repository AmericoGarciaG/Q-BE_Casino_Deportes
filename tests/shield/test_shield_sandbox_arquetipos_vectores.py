# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: SANDBOX DE ARQUETIPOS Y VECTORES — INDUCCIÓN DE FIRMAS POR CLASE
Gobierno: `docs/LOGIC.md` [LN-QBE-126] · `docs/ARCH.md` [ARCH-1.4.66]
Base de Gobierno: Kybern Framework v12.0 [GOV-TEST-01] (Pure Read-Only / Hermetic)

Régimen declarado (Dual-Track honesto):
* `[DIRGEN-STRICT]` — Z-Score global con guarda σ = 0, centroides por clase, Vector de
  Contraste ΔV_Ruptura = V_P_low − V_P_max y F-ratio univariado de Fisher. El Juez NO
  reimplementa el álgebra: la invoca VERBATIM (`calcular_centroide_zscore`,
  `calcular_fisher_ratio`) y exige paridad aritmética exacta, además de la guarda de
  varianza nula.
* `[DBBD-FUNGIBLE]` — composición de la matriz, tablero ASCII y CLI. Se certifica la
  FRONTERA: el sandbox no escribe en la bóveda, no importa la capa web y no fabrica celdas.

Partición factual congelada (instantánea certificada de la bóveda, 97 partidos J1–J11):
38 aciertos P_max · 35 rescates P_mid · 24 rupturas P_low (suma exacta 97), decidida por la
función pura canónica `resolver_orden_fiduciario_con_indiferencia` ([LN-QBE-124]).
"""

from __future__ import annotations

import contextlib
import io
import json
import math
from pathlib import Path

import pytest

from scripts.laboratorio.sandbox_arquetipos_vectores import (
    calcular_centroide_zscore,
    calcular_fisher_ratio,
    ejecutar_extraccion_arquetipos,
    main,
)

# ── Instantánea sellada de la partición (la bóveda de hoy; el Juez la congela, no la inventa) ──
# [LN-QBE-128] RE-CONGELADA al cierre del Sprint 3: la re-homologación de J1-J3 con el prior de
# Apertura 2025 ([ARCH-1.4.69]) movió 27 partidos del régimen ciego (0.3333/0.3333/0.3334) al
# régimen informado, de modo que la instantánea pasa de 38/35/24 a 39/31/27 (suma 97). La ley
# `[LN-QBE-126]` deuda (iv) ya declaraba que el Juez congela la partición DE HOY, no un literal
# eterno: la instantánea se actualiza con la bóveda, jamás con una expectativa.
PARTIDOS_CONCLUIDOS = 97
N_ACIERTOS_PMAX = 39
N_RESCATES_PMID = 31
N_RUPTURAS_PLOW = 27
DIMENSIONES_MINIMAS = 30
ETIQUETAS_PODER = {"DECISIVA", "MODERADA", "RUIDO", "NULO"}

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
FUENTE_SANDBOX = RAIZ_PROYECTO / "scripts" / "laboratorio" / "sandbox_arquetipos_vectores.py"


@pytest.fixture(scope="module")
def reporte():
    """Reporte único por módulo (el sandbox es read-only e idempotente: se reutiliza)."""
    return ejecutar_extraccion_arquetipos()


# ═════════════════════════════════════════════════════════════════════════════════════════════
# INVARIANZA 1 · LA PARTICIÓN ES LA DE LA BÓVEDA, NO UNA PREFERENCIA DEL INSTRUMENTO
# ═════════════════════════════════════════════════════════════════════════════════════════════
def test_invarianza_particion_factual_ternaria(reporte):
    """[INVARIANZA 1]: 38 / 35 / 24 sobre 97 partidos concluidos, sin celdas sin clasificar."""
    assert reporte["status"] == "EXITO", reporte.get("motivo")

    particion = reporte["particion"]
    assert particion["n_aciertos_pmax"] == N_ACIERTOS_PMAX
    assert particion["n_rescates_pmid"] == N_RESCATES_PMID
    assert particion["n_rupturas_plow"] == N_RUPTURAS_PLOW
    assert (
        particion["n_aciertos_pmax"] + particion["n_rescates_pmid"] + particion["n_rupturas_plow"]
    ) == PARTIDOS_CONCLUIDOS == particion["n_total"] == reporte["total_partidos"]

    # La banda de indiferencia de [LN-QBE-124] NO es ornamental: rescata vértices en la bóveda.
    assert particion["n_rescates_banda"] >= 1

    # Cero imputación declarada: la partición por jornada sólo reparte, jamás inventa partidos.
    por_jornada = particion["por_jornada"]
    assert sum(por_jornada["P_MAX"].values()) == N_ACIERTOS_PMAX
    assert sum(por_jornada["P_MID"].values()) == N_RESCATES_PMID
    assert sum(por_jornada["P_LOW"].values()) == N_RUPTURAS_PLOW


# ═════════════════════════════════════════════════════════════════════════════════════════════
# INVARIANZA 2 · CENTROIDES Z-SCORE, CONTRASTE Y GUARDA DE VARIANZA NULA
# ═════════════════════════════════════════════════════════════════════════════════════════════
def test_invarianza_centroides_zscore_y_contraste(reporte):
    """[INVARIANZA 2]: ≥ 30 dimensiones por centroide, sin NaN, y ΔV = V_P_low − V_P_max exacto."""
    vectores = {
        "pmax": reporte["vector_pmax"],
        "pmid": reporte["vector_pmid"],
        "plow": reporte["vector_plow"],
    }
    for nombre, vector in vectores.items():
        assert len(vector) >= DIMENSIONES_MINIMAS, f"{nombre} publicó {len(vector)} dimensiones"
        for clave, valor in vector.items():
            assert isinstance(valor, (int, float)), f"{nombre}.{clave} no es numérico: {valor!r}"
            assert math.isfinite(float(valor)), f"{nombre}.{clave} no es finito"

    contraste = reporte["vector_contraste_ruptura"]
    assert set(contraste) == set(vectores["plow"]) == set(vectores["pmax"])
    for clave, valor in contraste.items():
        esperado = vectores["plow"][clave] - vectores["pmax"][clave]
        assert abs(float(valor) - esperado) <= 1e-9, f"ΔV_Ruptura[{clave}] rompe la aritmética"

    # Guarda σ = 0 y ausencia declarada: el centroide promedia sólo celdas presentes.
    assert calcular_centroide_zscore([{"x": 0.0}, {"x": 0.0}]) == {"x": 0.0}
    assert calcular_centroide_zscore([{"x": None}, {"x": 2.0}, {"x": 4.0}]) == {"x": 3.0}
    assert calcular_centroide_zscore([]) == {}


# ═════════════════════════════════════════════════════════════════════════════════════════════
# INVARIANZA 3 · RANKING DE FISHER MONÓTONO Y ETIQUETADO
# ═════════════════════════════════════════════════════════════════════════════════════════════
def test_invarianza_ranking_fisher_monotono(reporte):
    """[INVARIANZA 3]: F-ratio descendente, finito, no negativo y con etiqueta fiduciaria."""
    ranking = reporte["ranking_fisher"]
    assert ranking, "El ranking de Fisher no puede quedar vacío."

    previo = math.inf
    for fila in ranking:
        for clave in ("nombre_variable", "f_ratio", "poder_separador", "delta_ruptura", "bloque"):
            assert clave in fila, f"Fila de Fisher sin `{clave}`: {fila}"
        f_ratio = float(fila["f_ratio"])
        assert math.isfinite(f_ratio) and f_ratio >= 0.0
        assert f_ratio <= previo + 1e-12, f"Ranking no monótono en {fila['nombre_variable']}"
        previo = f_ratio
        assert fila["poder_separador"] in ETIQUETAS_PODER
        assert fila["bloque"] in {"ESTRUCTURAL", "METAESTOCASTICO"}

    # Guarda del denominador: sin dispersión no hay razón (jamás división por cero).
    identicas = {clase: [{"x": 1.0}, {"x": 1.0}] for clase in ("P_MAX", "P_MID", "P_LOW")}
    for fila in calcular_fisher_ratio(identicas):
        assert float(fila["f_ratio"]) == 0.0
        assert fila["poder_separador"] == "NULO"

    # Separabilidad perfecta ⇒ F estrictamente positivo.
    separables = {
        "P_MAX": [{"x": 5.0}, {"x": 5.0}],
        "P_MID": [{"x": 0.0}, {"x": 0.0}],
        "P_LOW": [{"x": -5.0}, {"x": -5.0}],
    }
    assert float(calcular_fisher_ratio(separables)[0]["f_ratio"]) > 0.0


# ═════════════════════════════════════════════════════════════════════════════════════════════
# INVARIANZA 4 · PUREZA READ-ONLY, FRONTERA CLI-FIRST Y EXPORTACIÓN CERTIFICADA
# ═════════════════════════════════════════════════════════════════════════════════════════════
def test_invarianza_pureza_readonly_y_exportacion(reporte):
    """[INVARIANZA 4]: cero DML, cero capa web, cero celdas inventadas y JSON reproducible."""
    assert FUENTE_SANDBOX.is_file(), "El sandbox debe existir en su ubicación canónica [ARCH-1.4.66]."
    fuente = FUENTE_SANDBOX.read_text(encoding="utf-8")
    for token in (".commit(", ".add(", ".flush(", "INSERT INTO", "UPDATE ", "DELETE FROM"):
        assert token not in fuente, f"El sandbox viola la pureza read-only: `{token}`"
    for token in ("from src.web", "import fastapi", "playwright"):
        assert token not in fuente.lower(), f"El sandbox viola la frontera CLI-FIRST: `{token}`"

    # Declaración honesta de lo que NO entró a la matriz (cero fabricación).
    derivaciones = reporte["derivaciones"]
    for excluida in ("V16", "V28", "V31", "V32"):
        assert excluida in derivaciones["fuera_de_matriz"], f"{excluida} debe declararse excluida."
    assert len(reporte["cobertura"]) == len(reporte["vector_pmax"])

    # Una dimensión declarada FUERA de matriz no puede aparecer computada (contradicción = mentira).
    assert not (set(derivaciones["fuera_de_matriz"]) & set(reporte["dimensiones"]))
    assert set(reporte["dimensiones"]) <= set(reporte["cobertura"])
    assert len(reporte["dimensiones"]) == reporte["n_dimensiones"]

    # Idempotencia: dos ejecuciones producen el MISMO reporte (determinismo, cero estado).
    repetido = ejecutar_extraccion_arquetipos()
    assert json.dumps(repetido, sort_keys=True, default=str) == json.dumps(
        reporte, sort_keys=True, default=str
    )

    # Exportación materializada y re-legible.
    exportado = ejecutar_extraccion_arquetipos(exportar_json=True)
    ruta = Path(exportado["ruta_json_exportado"])
    assert ruta.is_file(), f"El reporte JSON no se materializó: {ruta}"
    assert ruta.stat().st_size > 1024, "El reporte exportado está vacío."
    contenido = json.loads(ruta.read_text(encoding="utf-8"))
    assert contenido["particion"]["n_aciertos_pmax"] == N_ACIERTOS_PMAX
    assert contenido["particion"]["n_rupturas_plow"] == N_RUPTURAS_PLOW

    # Contrato CLI [ARCH-1.4.66]: `--json` emite el reporte y el código de salida es 0 con EXITO.
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        codigo = main(["--json", "--top", "5"])
    assert codigo == 0, f"La CLI devolvió {codigo} con status EXITO."
    emitido = json.loads(salida.getvalue())
    assert emitido["ley"] == "[LN-QBE-126]" and emitido["status"] == "EXITO"
    assert emitido["particion"]["n_total"] == PARTIDOS_CONCLUIDOS
