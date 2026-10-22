# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — REINGENIERÍA MACRO FASE A (32 VARIABLES) SUITE
Juez Inmutable: [LN-QBE-120] / [ARCH-1.4.59]
Base de Gobierno: Kybern Framework v13.5
"""

import os
import pytest
from src.core.sovereign.factor_attribution import _CATALOGO_44, DIMENSIONES_CANONICAS

def test_invarianza_catalogo_reducido_a_32_variables():
    """[INVARIANZA 1 - CATÁLOGO 32V]: _CATALOGO_44 debe tener exactamente 32 elementos."""
    assert len(_CATALOGO_44) == 32, f"El catálogo debe tener 32 variables, se encontraron {len(_CATALOGO_44)}"
    
    ids_esperados = [f"V{i:02d}" for i in range(1, 33)]
    ids_actuales = [v[0] for v in _CATALOGO_44]
    assert ids_actuales == ids_esperados, "Los IDs deben ser estrictamente correlativos V01 a V32"

def test_invarianza_dimensiones_consolidadas():
    """[INVARIANZA 2 - DIMENSIONES]: Las dimensiones deben ser exactamente 6."""
    assert len(DIMENSIONES_CANONICAS) == 6, f"Deben existir 6 dimensiones, se encontraron {len(DIMENSIONES_CANONICAS)}"
    nombres_dim = [d[1] for d in DIMENSIONES_CANONICAS]
    assert "Volumen Territorial y Fricción" in nombres_dim
    assert "Calidad de Remate" in nombres_dim
    assert "Resistencia Defensiva" in nombres_dim
    assert "Rendimiento de Portería" in nombres_dim
    assert "Balón Parado y Disciplina" in nombres_dim
    assert "Memoria, Forma y Contexto" in nombres_dim

def test_invarianza_centinela_macro_declara_argumentos():
    """[INVARIANZA 3 - CLI MACRO]: El centinela debe existir y exponer --liga-id."""
    ruta_script = os.path.join("scripts", "ingesta", "centinela_macro_estadisticas.py")
    assert os.path.exists(ruta_script), "Falta el script centinela_macro_estadisticas.py"
    
    with open(ruta_script, "r", encoding="utf-8") as f:
        contenido = f.read()
    
    assert "argparse.ArgumentParser" in contenido
    assert "--liga-id" in contenido
    assert "cache_macro_stats" in contenido
