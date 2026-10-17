# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DEL GOLDEN CSV DE INVESTIGACIÓN
Contrato vigilado:
- [UTIL-GOLDEN-01] `scripts/utilidades/exportar_dataset_investigacion.py` — exportación tabular
  plana de los partidos concluidos (Jornadas 1..11) para el Data Scientist aislado
  (`docs/QBE_RESEARCH_DOSSIER.md`).
- [VAULT-CORE-007-C] Desmarque proporcional de vig `desmarcar_cuotas_proporcional(oL, oX, oV)`.
- [LN-QBE-100] Brier Score Multicategórico `calcular_brier_multicategorico` y cláusula cold start
  (S(I) = 0 ⇒ Prior Fiduciario de Mercado).
- [ARCH-1.4.38] Ley sellada de resolución de cuotas de cierre `_cuotas_1x2_factuales`.
- [GOVERNANCE-01] Cero invención de cifras: sin trío de cuotas la ley degrada a la ignorancia
  uniforme (1/3, 1/3, 1/3); jamás un relleno sintético.
Regímenes: [DBBD-FUNGIBLE] en la capa de transporte/tabulación; toda la matemática es
[DIRGEN-STRICT] y se DELEGA (el juez prohíbe su reimplementación).
Gobierno: [GOV-TEST-01] Aislamiento hermético (cero red / cero bóveda / cero tokens).
"""

import csv
import os
from types import SimpleNamespace

RUTA_UTILIDAD = os.path.join("scripts", "utilidades", "exportar_dataset_investigacion.py")


def _partido_sintetico(id_partido: str, jornada: int, goles_local: int, goles_visita: int):
    """Sustituto inerte de `Match` (3NF): el juez no toca la bóveda viva."""
    return SimpleNamespace(
        id=id_partido,
        matchday_num=jornada,
        score_home=goles_local,
        score_away=goles_visita,
        status="FINALIZADO",
        home_team_slug="local-fc",
        away_team_slug="visita-fc",
    )


def _fixture_sintetico(suficiencia: int, con_cuotas: bool = True):
    """Fixture sellado sintético con el contrato de captura (P′, λ, S(I), trío 1X2)."""
    fixture = {
        "id_partido": "LIGAMX-J9-99",
        "local": "Local FC",
        "visitante": "Visita FC",
        "p_local": 0.55,
        "p_empate": 0.25,
        "p_visitante": 0.20,
        "lambda_home": 1.7500,
        "lambda_away": 0.9000,
        "suficiencia_S_I": suficiencia,
    }
    if con_cuotas:
        fixture["cuotas"] = {"L": 2.00, "E": 3.40, "V": 4.00}
    return fixture


def test_juez_1_contrato_de_columnas_del_golden_csv(tmp_path):
    """[UTIL-GOLDEN-01] El CSV materializado porta EXACTAMENTE el contrato declarado de 21
    columnas, en el orden sellado, y la cabecera coincide con `COLUMNAS_GOLDEN`."""
    from scripts.utilidades.exportar_dataset_investigacion import (
        COLUMNAS_GOLDEN,
        _construir_fila,
        exportar_csv,
    )

    contrato_esperado = (
        "match_id", "jornada", "local", "visitante",
        "home_score", "away_score", "resultado_real",
        "odd_L", "odd_E", "odd_V",
        "q_L", "q_E", "q_V",
        "p_L", "p_E", "p_V",
        "lambda_H", "lambda_A",
        "brier_qbe", "brier_mkt",
        "suficiencia_s_i",
    )
    assert COLUMNAS_GOLDEN == contrato_esperado
    assert len(COLUMNAS_GOLDEN) == 21

    fila, _ = _construir_fila(
        _partido_sintetico("LIGAMX-J9-99", 9, 2, 1), _fixture_sintetico(1), None
    )
    assert set(fila.keys()) == set(COLUMNAS_GOLDEN)
    assert "" not in fila.values(), f"Celda vacía en el contrato sellado: {fila}"

    destino = tmp_path / "golden.csv"
    exportar_csv([fila], str(destino))

    crudo = destino.read_bytes()
    assert not crudo.startswith(b"\xef\xbb\xbf"), "UTF-8 SIN BOM: pandas no debe ver '\\ufeffmatch_id'"
    with open(destino, encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)
        cabecera = list(lector.fieldnames or [])
        filas = list(lector)
    assert cabecera == list(COLUMNAS_GOLDEN)
    assert len(filas) == 1
    assert filas[0]["match_id"] == "LIGAMX-J9-99"
    assert filas[0]["resultado_real"] == "LOCAL"


def test_juez_2_delegacion_de_la_matematica_sellada():
    """[DBBD-FUNGIBLE / DIRGEN-STRICT] `q_*` es la salida verbatim de
    `desmarcar_cuotas_proporcional` y `brier_*` la de `calcular_brier_multicategorico`:
    la utilidad NO reimplementa una sola fórmula."""
    from src.core.contracts.portfolio_math import (
        calcular_brier_multicategorico,
        desmarcar_cuotas_proporcional,
    )

    from scripts.utilidades.exportar_dataset_investigacion import _construir_fila

    fixture = _fixture_sintetico(1)
    fila, metadatos = _construir_fila(_partido_sintetico("LIGAMX-J9-99", 9, 2, 1), fixture, None)

    ql, qe, qv = desmarcar_cuotas_proporcional(2.00, 3.40, 4.00)
    assert (float(fila["q_L"]), float(fila["q_E"]), float(fila["q_V"])) == (ql, qe, qv)
    assert abs(sum((ql, qe, qv)) - 1.0) <= 1e-6, "El consenso desmarcado debe clausurar en 1.0"
    assert (float(fila["odd_L"]), float(fila["odd_E"]), float(fila["odd_V"])) == (2.0, 3.4, 4.0)

    p = (float(fila["p_L"]), float(fila["p_E"]), float(fila["p_V"]))
    assert abs(sum(p) - 1.0) <= 1e-6
    assert p == (0.55, 0.25, 0.20), "Con S(I)=1 la columna p_* es la P′ sellada de la captura"
    assert (float(fila["lambda_H"]), float(fila["lambda_A"])) == (1.75, 0.90)

    brier_qbe = calcular_brier_multicategorico(
        [{"p_local": p[0], "p_empate": p[1], "p_visitante": p[2], "resultado": "LOCAL"}]
    )
    brier_mkt = calcular_brier_multicategorico(
        [{"p_local": ql, "p_empate": qe, "p_visitante": qv, "resultado": "LOCAL"}]
    )
    assert float(fila["brier_qbe"]) == float(f"{brier_qbe:.6f}")
    assert float(fila["brier_mkt"]) == float(f"{brier_mkt:.6f}")
    assert metadatos["brier_qbe"] == brier_qbe and metadatos["brier_mkt"] == brier_mkt


def test_juez_3_clausula_cold_start_prior_fiduciario_de_mercado():
    """[LN-QBE-100] Con suficiencia S(I) = 0 la ley sellada publica el Prior Fiduciario de
    Mercado: `p_* == q_*` (ignorancia declarada), jamás una cifra fabricada."""
    from src.core.contracts.portfolio_math import desmarcar_cuotas_proporcional

    from scripts.utilidades.exportar_dataset_investigacion import _construir_fila

    fila, metadatos = _construir_fila(
        _partido_sintetico("LIGAMX-J1-99", 1, 0, 0), _fixture_sintetico(0), None
    )

    ql, qe, qv = desmarcar_cuotas_proporcional(2.00, 3.40, 4.00)
    p = (float(fila["p_L"]), float(fila["p_E"]), float(fila["p_V"]))
    assert p == (ql, qe, qv), "Cold start: p_* debe ser el Prior Fiduciario de Mercado"
    assert fila["suficiencia_s_i"] == "0"
    assert metadatos["ignorancia_declarada"] is True
    assert fila["resultado_real"] == "EMPATE"


def test_juez_4_cero_invencion_de_cifras_sin_trio_de_cuotas():
    """[GOVERNANCE-01] Un fixture sin trío completo NO se repara con rellenos sintéticos: el
    desmarque sellado degrada a la ignorancia uniforme (1/3, 1/3, 1/3) y la degradación se declara."""
    from scripts.utilidades.exportar_dataset_investigacion import _construir_fila

    fila, metadatos = _construir_fila(
        _partido_sintetico("LIGAMX-J9-98", 9, 1, 1), _fixture_sintetico(1, con_cuotas=False), None
    )

    assert metadatos["sin_cuotas"] is True
    assert (fila["odd_L"], fila["odd_E"], fila["odd_V"]) == ("0.0000", "0.0000", "0.0000")
    assert (fila["q_L"], fila["q_E"], fila["q_V"]) == ("0.3333", "0.3333", "0.3333")
    assert (float(fila["q_L"]), float(fila["q_E"]), float(fila["q_V"])) == (0.3333, 0.3333, 0.3333)


def test_juez_5_invarianza_de_solo_lectura_y_rango_de_jornadas():
    """[UTIL-GOLDEN-01] La utilidad es de SOLO LECTURA (cero `write_transaction`, cero
    `session.add`/`commit`) y el parser de jornadas conserva el contrato `'1-11'` / `'9'` / `'1,4,7'`."""
    with open(RUTA_UTILIDAD, encoding="utf-8") as archivo:
        codigo = archivo.read()
    for prohibido in ("write_transaction", "session.add", ".commit(", "requests.", "httpx."):
        assert prohibido not in codigo, f"La utilidad de exportación viola solo-lectura: {prohibido}"

    from scripts.utilidades.exportar_dataset_investigacion import _parsear_rango_jornadas

    assert _parsear_rango_jornadas("1-11") == list(range(1, 12))
    assert _parsear_rango_jornadas("9") == [9]
    assert _parsear_rango_jornadas("1,4,7") == [1, 4, 7]
    assert _parsear_rango_jornadas("3-5,3") == [3, 4, 5]
    assert _parsear_rango_jornadas("") == []

