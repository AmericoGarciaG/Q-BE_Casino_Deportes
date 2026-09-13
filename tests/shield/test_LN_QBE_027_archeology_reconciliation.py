# -*- coding: utf-8 -*-
"""
Prueba Concreta: [LN-QBE-027] Reconciliación Arqueológica
"""
from typing import Dict, Any
from tests.shield.abstract_test_LN_QBE_027_archeology_reconciliation import AbstractTestLN_QBE_027_ArcheologyReconciliation
from src.pipeline.adapter import construir_master_table_snapshot, hidratar_partidos_cuantitativos
from src.pipeline.engine import QBEPipelineEngine

class TestLN_QBE_027_ArcheologyReconciliation_Concrete(AbstractTestLN_QBE_027_ArcheologyReconciliation):

    def ejecutar_pipeline_con_h2h_vacio(self) -> Dict[str, Any]:
        posiciones_sample = [
            {"pos": 1, "equipo": "Club América", "pj": 6, "puntos": 16, "gf": 12, "gc": 2},
            {"pos": 2, "equipo": "Cruz Azul", "pj": 7, "puntos": 12, "gf": 12, "gc": 11}
        ]
        master = construir_master_table_snapshot(posiciones_sample, jornada=8)
        fixtures_sample = [{
            "id_partido": "TEST-01", "local": "Cruz Azul", "visitante": "Club América",
            "horario": "12/09 21:15 hr",
            "momios": {"L": 2.50, "E": 3.40, "V": 2.70, "pago_anticipado": True}
        }]
        raw = hidratar_partidos_cuantitativos(fixtures_sample, master, jornada=8)
        assert len(raw[0].h2h_matches) == 0, "Violación: h2h_matches no está vacío."
        
        plan, payload = QBEPipelineEngine.run_full(raw, master, bankroll=200.0, mode="BANKROLL")
        return {"status": "SUCCESS", "plan": plan, "payload": payload}
