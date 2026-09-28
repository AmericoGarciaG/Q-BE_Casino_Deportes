# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [LN-QBE-075] Ingesta Fáctica Progol Regular + Revancha (14 + 7).
Doctrina: Kybern Framework v12.0 [GOV-TEST-01 a 07]
Régimen: [DIRGEN-STRICT] — Cero red, cero dependencia de la bóveda, determinismo absoluto.

Twin-Test: `AbstractTestProgolIngestion` declara la ley; `TestProgolIngestion` la materializa.
"""

import pytest
from unittest.mock import patch

from src.ingestion.progol_scraper import ProgolMarketScraper, PRIOR_IGNORANCIA_FIDUCIARIA
from scripts.daemons.centinela_progol import _bolsa_a_float, procesar_casilla_con_resiliencia

# [VARIANCE-04] Fixture fáctico VERBATIM del DOM de miloteria.mx (concurso 2352, captura 2026-09-25).
# Cada casilla son tres líneas con una línea de TABULADOR (separador de celdas del DOM) entre el local
# y el visitante, terminadas por doble salto en blanco. Fuente: data/output/diag_progol_dom.txt
CUERPO_PROGOL_2352_DOM_REAL = "\n".join([
    "Concurso",
    "2352",
    "¡A JUGAR!",
    "00D : 00H : 20M : 02S para concurso 2352 del dia viernes 25 de septiembre",
    "Local\tEmpate\tVisitante",
    "",
    "1.", "MEXICO", "\t", "COLOMBIA", "", "",
    "2.", "REP. COREA", "\t", "URUGUAY", "", "",
    "3.", "TIJUANA", "\t", "ATLAS", "", "",
    "4.", "C. AZUL", "\t", "TOLUCA", "", "",
    "5.", "TLAXCALA", "\t", "CANCUN", "", "",
    "6.", "MERIDA", "\t", "MORELIA", "", "",
    "7.", "ESLOVENIA", "\t", "ESCOCIA", "", "",
    "8.", "CHEQUIA", "\t", "CROACIA", "", "",
    "9.", "INGLATERRA", "\t", "ESPANA", "", "",
    "10.", "NORUEGA", "\t", "PORTUGAL", "", "",
    "11.", "TURQUIA", "\t", "ITALIA", "", "",
    "12.", "DALLAS", "\t", "LOS ANGELES", "", "",
    "13.", "ESTUDIANTES", "\t", "ROSARIO CEN", "", "",
    "14.", "GOIAS", "\t", "ATL. GO",
    "Revancha",
    "Local\tEmpate\tVisitante",
    "",
    "1.", "GUADALAJARA", "\t", "QUERETARO", "", "",
    "2.", "S. LAGUNA", "\t", "PACHUCA", "", "",
    "3.", "TIGRES", "\t", "PUEBLA", "", "",
    "4.", "PUMAS", "\t", "SAN LUIS", "", "",
    "5.", "NECAXA", "\t", "AGUILAS", "", "",
    "6.", "SERBIA", "\t", "PAISES BAJO", "", "",
    "7.", "BELGICA", "\t", "FRANCIA",
    "Precios",
    "Progol",
    "Revancha",
    "Total",
    "Sorteo 2352 del 2026-09-28",
    "Bolsa",
    "$8,800,000.00",
    "",
])

# Layout compacto heredado (una línea por casilla) — tolerancia de retrocompatibilidad.
CUERPO_PROGOL_2352_LAYOUT_COMPACTO = """00D : 01H : 06M : 51S para concurso 2352 del dia viernes 25 de septiembre

Bolsa
$8,800,000.00

Progol
Local   Empate  Visitante
1. MEXICO COLOMBIA
2. REP. COREA URUGUAY
3. TIJUANA ATLAS
4. C. AZUL TOLUCA
5. TLAXCALA CANCUN
6. MERIDA MORELIA
7. ESLOVENIA ESCOCIA
8. CHEQUIA CROACIA
9. INGLATERRA ESPANA
10. NORUEGA PORTUGAL
11. TURQUIA ITALIA
12. DALLAS LOS ANGELES
13. ESTUDIANTES ROSARIO CEN
14. GOIAS ATL. GO

Revancha
Local   Empate  Visitante
1. GUADALAJARA QUERETARO
2. S. LAGUNA PACHUCA
3. TIGRES PUEBLA
4. PUMAS SAN LUIS
5. NECAXA AGUILAS
6. SERBIA PAISES BAJO
7. BELGICA FRANCIA
"""


CUERPO_LAYOUT_MULTILINEA = """concurso 2400
1.
TOLUCA
TIJUANA
2.
NECAXA
ATLAS
"""


class AbstractTestProgolIngestion:
    """Contrato abstracto e inmutable del sensor Progol y de la resiliencia multi-torneo."""

    def test_ingesta_factica_de_21_casillas_y_bolsa(self):
        """[LN-QBE-075] El DOM real (3 líneas + TAB) produce 14 Regular + 7 Revancha sin perder ninguna."""
        data = ProgolMarketScraper.parse_progol_text(CUERPO_PROGOL_2352_DOM_REAL)

        assert data["concurso_id"] == "PROGOL-2352"
        assert "$8,800,000" in data["bolsa"]
        assert "viernes" in data["fecha_cierre"].lower()

        assert len(data["partidos_regular"]) == 14, "Faltan casillas de Progol Regular"
        assert len(data["partidos_revancha"]) == 7, "Faltan casillas de Progol Revancha"

        casilla_1 = data["partidos_regular"][0]
        assert casilla_1["posicion"] == 1
        assert casilla_1["local_raw"] == "MEXICO"
        assert casilla_1["visitante_raw"] == "COLOMBIA"
        assert casilla_1["tipo"] == "REGULAR"

        casilla_revancha_5 = data["partidos_revancha"][4]
        assert casilla_revancha_5["posicion"] == 5
        assert casilla_revancha_5["local_raw"] == "NECAXA"
        assert casilla_revancha_5["visitante_raw"] == "AGUILAS"
        assert casilla_revancha_5["tipo"] == "REVANCHA"

        assert [p["posicion"] for p in data["partidos_regular"]] == list(range(1, 15))
        assert [p["posicion"] for p in data["partidos_revancha"]] == list(range(1, 8))

        # [VARIANCE-04] Invariante anti-corrupción silenciosa: ninguna casilla puede quedar a medias.
        todas = data["partidos_regular"] + data["partidos_revancha"]
        incompletas = [p["posicion"] for p in todas if not p["local_raw"] or not p["visitante_raw"]]
        assert incompletas == [], f"Casillas con par local/visitante incompleto: {incompletas}"

    def test_layout_compacto_heredado_entrega_las_mismas_casillas(self):
        """[LN-QBE-075] Tolerancia dual-layout: el formato de una línea corta las mismas 21 casillas."""
        compacto = ProgolMarketScraper.parse_progol_text(CUERPO_PROGOL_2352_LAYOUT_COMPACTO)

        assert len(compacto["partidos_regular"]) == 14
        assert len(compacto["partidos_revancha"]) == 7
        assert [p["posicion"] for p in compacto["partidos_regular"]] == list(range(1, 15))
        assert [p["posicion"] for p in compacto["partidos_revancha"]] == list(range(1, 8))

        todas = compacto["partidos_regular"] + compacto["partidos_revancha"]
        incompletas = [p["posicion"] for p in todas if not p["local_raw"] or not p["visitante_raw"]]
        assert incompletas == [], f"Casillas con par local/visitante incompleto: {incompletas}"

        por_pos = {p["posicion"]: p for p in compacto["partidos_regular"]}
        assert por_pos[4]["local_canonico"] == "Cruz Azul"
        assert por_pos[4]["visitante_canonico"] == "Deportivo Toluca"
        assert por_pos[13]["local_raw"] == "ESTUDIANTES"
        assert por_pos[13]["visitante_raw"] == "ROSARIO CEN"

    def test_resiliencia_club_desconocido_inyecta_prior_fiduciario(self):
        """[LN-QBE-075] Club fuera de catálogo => Prior (0.3333, 0.3333, 0.3334) sin excepción fatal."""
        resultado = procesar_casilla_con_resiliencia("CLUB FANTASMA ALPHA", "EQUIPO INEXISTENTE BETA", db_session=None)

        assert resultado["es_prior_ignorancia"] is True
        assert resultado["match_id"] is None
        assert resultado["p_local"] == pytest.approx(PRIOR_IGNORANCIA_FIDUCIARIA[0], abs=1e-6)
        assert resultado["p_empate"] == pytest.approx(PRIOR_IGNORANCIA_FIDUCIARIA[1], abs=1e-6)
        assert resultado["p_visitante"] == pytest.approx(PRIOR_IGNORANCIA_FIDUCIARIA[2], abs=1e-6)
        assert resultado["p_local"] + resultado["p_empate"] + resultado["p_visitante"] == pytest.approx(1.0, abs=1e-4)
        assert "PRIOR" in resultado["estado_qbe"]

        assert resultado["local_canonico"] == "CLUB FANTASMA ALPHA"
        assert resultado["visitante_canonico"] == "EQUIPO INEXISTENTE BETA"

    def test_resiliencia_ante_colapso_del_catalogo(self):
        """[LN-QBE-075] Si el normalizador colapsa, la casilla no congela al centinela."""
        with patch("scripts.daemons.centinela_progol.canonicalize_team_name", side_effect=RuntimeError("catálogo caído")):
            resultado = procesar_casilla_con_resiliencia("TOLUCA", "TIJUANA", db_session=None)

        assert resultado["es_prior_ignorancia"] is True
        assert resultado["match_id"] is None
        assert resultado["local_canonico"] == "TOLUCA"
        assert resultado["visitante_canonico"] == "TIJUANA"
        assert resultado["p_local"] == pytest.approx(PRIOR_IGNORANCIA_FIDUCIARIA[0], abs=1e-6)

    def test_corte_canonico_y_tolerancia_de_layout_multilinea(self):
        """[LN-QBE-075] El corte resuelve abreviaturas (C. AZUL, S. LAGUNA) y tolera el layout sin separador."""
        data_real = ProgolMarketScraper.parse_progol_text(CUERPO_PROGOL_2352_DOM_REAL)
        real = {p["posicion"]: p for p in data_real["partidos_regular"]}
        assert real[3]["local_canonico"] == "Club Tijuana"
        assert real[3]["visitante_canonico"] == "Atlas FC"

        rev = {p["posicion"]: p for p in data_real["partidos_revancha"]}
        assert rev[2]["local_canonico"] == "Santos Laguna"
        assert rev[2]["visitante_canonico"] == "Club Pachuca"
        assert rev[5]["local_canonico"] == "Necaxa"

        data_simple = ProgolMarketScraper.parse_progol_text(CUERPO_PROGOL_2352_LAYOUT_COMPACTO)
        abreviaturas = {p["posicion"]: p for p in data_simple["partidos_regular"]}

        assert abreviaturas[4]["local_raw"] == "C. AZUL"
        assert abreviaturas[4]["visitante_raw"] == "TOLUCA"
        assert abreviaturas[4]["local_canonico"] == "Cruz Azul"
        assert abreviaturas[13]["local_raw"] == "ESTUDIANTES"
        assert abreviaturas[13]["visitante_raw"] == "ROSARIO CEN"

        data_multilinea = ProgolMarketScraper.parse_progol_text(CUERPO_LAYOUT_MULTILINEA)
        assert data_multilinea["concurso_id"] == "PROGOL-2400"
        assert len(data_multilinea["partidos_regular"]) == 2
        assert data_multilinea["partidos_regular"][0]["local_raw"] == "TOLUCA"
        assert data_multilinea["partidos_regular"][0]["visitante_raw"] == "TIJUANA"
        assert data_multilinea["partidos_regular"][1]["local_canonico"] == "Necaxa"


    def test_fidelidad_monetaria_de_la_bolsa(self):
        """[ARCH-1.5.1-C] La bolsa fáctica '$8,800,000.00' se persiste como 8.8e6, no como 8.8e8."""
        assert _bolsa_a_float("$8,800,000.00") == 8800000.0
        assert _bolsa_a_float("$8,800,000") == 8800000.0
        assert _bolsa_a_float("Bolsa por Definir") is None

        data = ProgolMarketScraper.parse_progol_text(CUERPO_PROGOL_2352_DOM_REAL)
        assert _bolsa_a_float(data["bolsa"]) == 8800000.0


class TestProgolIngestion(AbstractTestProgolIngestion):
    """Materialización concreta del Juez Inmutable [LN-QBE-075]."""
    pass

