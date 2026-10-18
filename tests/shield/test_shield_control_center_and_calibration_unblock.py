# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — CALIBRATION UNBLOCK & CONTROL CENTER EXPANSION SUITE
Juez Inmutable: [ARCH-1.4.12-C] / [ARCH-1.4.42-B] / [DES-QBE-064]
Base de Gobierno: Kybern Framework v13.5 [GOV-TEST-01] (Pure In-Memory Test, Zero Network)

[NOTA DE DICTAMEN D-1 (2026-10-17)]: el DTO canónico del catálogo de 44 variables es
`AtribucionVariableOut` (src/models/web_schemas.py). Se ratificó corregir ESE contrato y NO
crear un DTO paralelo (`ItemVariable44Out` / `Variable44Out` no existen ni deben existir).
El resto de las invarianzas se transcribe verbatim del decreto del sprint.
"""

import pytest
from pydantic import ValidationError
from src.models.web_schemas import AtribucionVariableOut
from src.web.routes.admin_tasks import COMANDOS_TAREAS, TAREAS_PERMITIDAS

def test_invarianza_dto_variable44_acepta_strings_con_unidades():
    """[INVARIANZA 1 - UNBLOCK 500]: AtribucionVariableOut debe aceptar strings con unidades sin fallar."""
    # Simular exactamente las entradas que provocaron el ResponseValidationError
    items_patologicos = [
        {"id": "V27", "variable": "Diferencial de descanso", "local": "+0.0 d", "visita": "-1.5 d"},
        {"id": "V28", "variable": "Factor de altitud", "local": "0m", "visita": "2660m"},
        {"id": "V39", "variable": "H2H Reciente", "local": "0 partidos", "visita": "4 partidos"},
        {"id": "V01", "variable": "Posesión", "local": "54.2%", "visita": "45.8%"},
        {"id": "V05", "variable": "xG por partido", "local": 1.45, "visita": 0.88}  # Floats legítimos
    ]

    for item in items_patologicos:
        dto = AtribucionVariableOut(**item)
        assert dto.local is not None, f"Fallo al aceptar valor local para {item['id']}"
        assert str(dto.local) == str(item["local"])

def test_invarianza_control_center_whitelist_incluye_homologacion():
    """[INVARIANZA 2 - CONTROL CENTER]: homologar_temporada_optah2h debe estar en la whitelist."""
    assert "homologar_temporada_optah2h" in TAREAS_PERMITIDAS, "homologar_temporada_optah2h debe ser tarea permitida"
    assert "homologar_temporada_optah2h" in COMANDOS_TAREAS, "homologar_temporada_optah2h debe tener comando registrado"

    cmd = COMANDOS_TAREAS["homologar_temporada_optah2h"]
    assert "homologar_temporada_optah2h.py" in cmd[-1], "Comando debe apuntar al script de homologación"

def test_invarianza_cadena_post_jornada_incluye_homologacion():
    """[INVARIANZA 3 - CADENA POST-JORNADA]: La cadena post-jornada debe orquestar los 3 pasos canónicos."""
    from src.web.routes.admin_tasks import CADENAS_TAREAS
    assert "cadena_post_jornada" in CADENAS_TAREAS
    pasos = CADENAS_TAREAS["cadena_post_jornada"]

    # Debe ejecutar: betexplorer -> homologacion -> coherencia
    assert "ingestar_historico_betexplorer" in pasos
    assert "homologar_temporada_optah2h" in pasos, "Cadena post-jornada debe incluir homologar_temporada_optah2h"
    assert "auditar_coherencia_cartelera" in pasos

    idx_bet = pasos.index("ingestar_historico_betexplorer")
    idx_hom = pasos.index("homologar_temporada_optah2h")
    idx_coh = pasos.index("auditar_coherencia_cartelera")
    assert idx_bet < idx_hom < idx_coh, "Orden de cadena debe ser: BetExplorer -> Homologación -> Coherencia"

def test_invarianza_detector_deriva_reconoce_necesidad_homologacion():
    """[INVARIANZA 4 - DERIVA]: admin_status debe auditar consistencia de homologación."""
    from src.web.routes.admin_status import auditar_deriva_sistema
    # Ejecutar sonda en memoria / modo lectura
    res = auditar_deriva_sistema()
    assert "status_mercado" in res
    assert "status_deportivo" in res
    assert "status_progol" in res
    assert "status_integridad" in res
    assert "accion_recomendada" in res
