# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [LN-QBE-027] Reconciliación Arqueológica y Purga de Malas Prácticas
Base de Gobierno: Kybern Framework v8.0 / v12.0
Axioma: Erradicación de H2H falso, eliminación de diccionarios rígidos y verificación AST.
"""
import abc
import ast
import os
from typing import Dict, Any, List
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AbstractTestLN_QBE_027_ArcheologyReconciliation(abc.ABC):

    @abc.abstractmethod
    def ejecutar_pipeline_con_h2h_vacio(self) -> Dict[str, Any]:
        """Ejecuta el pipeline pasando una lista vacía de H2H para comprobar la ley Zero-H2H."""
        pass

    # =========================================================================
    # INVARIANTES DEL ESCUDO (THE SHIELD)
    # =========================================================================

    def test_invariante_ast_cero_h2h_sintetico_en_adapter(self):
        """
        [INVARIANZA 1 - GOVERNANCE-01 - PURGA H8]
        Inspección de Árbol Sintáctico (AST): adapter.py NO debe contener
        fechas hardcodeadas como '2026-03-15' o partidos H2H inventados.
        """
        adapter_path = os.path.join(PROJECT_ROOT, "src", "pipeline", "adapter.py")
        assert os.path.exists(adapter_path), "adapter.py no existe."

        with open(adapter_path, "r", encoding="utf-8") as f:
            code = f.read()

        assert "2026-03-15" not in code, "Violación [GOVERNANCE-01]: adapter.py aún contiene la fecha falsa '2026-03-15'."
        assert "2025-09-20" not in code, "Violación [GOVERNANCE-01]: adapter.py aún contiene la fecha falsa '2025-09-20'."
        assert "2024-01-28" not in code, "Violación [GOVERNANCE-01]: adapter.py aún contiene partidos H2H sintéticos."

    def test_invariante_ast_cero_fallback_rivals_hardcodeado(self):
        """
        [INVARIANZA 2 - GOVERNANCE-02 - PURGA H2]
        Inspección AST: sync_service.py NO debe contener el diccionario
        hardcodeado FALLBACK_RIVALS con pareos estáticos.
        """
        sync_path = os.path.join(PROJECT_ROOT, "src", "storage", "sync_service.py")
        assert os.path.exists(sync_path), "sync_service.py no existe."

        with open(sync_path, "r", encoding="utf-8") as f:
            code = f.read()

        assert "FALLBACK_RIVALS" not in code, (
            "Violación [GOVERNANCE-02]: sync_service.py aún contiene el diccionario "
            "estático FALLBACK_RIVALS. Debe ser erradicado por completo."
        )

    def test_invariante_ast_cero_fechas_rigidas_septiembre(self):
        """
        [INVARIANZA 3 - GOVERNANCE-02 - PURGA H5]
        Inspección AST: sync_service.py NO debe condicionar reprogramados
        a fórmulas sobreajustadas como 'mes > 9' o cadenas '15/09'.
        """
        sync_path = os.path.join(PROJECT_ROOT, "src", "storage", "sync_service.py")
        with open(sync_path, "r", encoding="utf-8") as f:
            code = f.read()

        assert "mes > 9" not in code, "Violación [GOVERNANCE-02]: sync_service.py aún tiene el hardcode 'mes > 9'."
        assert 'dia > 15 and mes == 9' not in code, "Violación [GOVERNANCE-02]: sync_service.py sobreajustado a septiembre."

    def test_invariante_ley_zero_h2h_matematica(self):
        """
        [INVARIANZA 4 - LN-QBE-020-B]
        Cuando no hay antecedentes H2H (h2h_matches=[]), el motor estocástico
        debe operar al 100% sobre la liga (w_liga = 1.0, w_h2h = 0.0) sin arrojar errores.
        """
        res = self.ejecutar_pipeline_con_h2h_vacio()
        assert res is not None, "El pipeline colapsó ante H2H vacío."
        assert res.get("status") != "FAILED", "El motor no soportó la ley Zero-H2H."
