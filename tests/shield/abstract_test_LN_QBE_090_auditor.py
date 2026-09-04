import abc
from typing import Tuple, List, Dict, Any

class AbstractTestAuditor(abc.ABC):
    @abc.abstractmethod
    def audit_plan(self, plan_dict: Dict[str, Any], bankroll: float) -> Tuple[bool, List[str]]:
        pass

    def test_shield_blocks_on_hard_cap_violation(self):
        """[SHIELD-INVARIANTE #4] Violación de Hard-Cap Global (>25%) debe ser rechazada."""
        mock_plan = {
            "control_portafolio": {"capital_total_core_mxn": 60.0},
            "ordenes_ejecucion_partidos": [],
            "balance_global_portafolio": {"ganancia_neta_esperada_jornada_mxn": 5.0}
        }
        is_valid, logs = self.audit_plan(mock_plan, bankroll=200.0)
        assert is_valid is False
        assert any("Hard-Cap Global" in log for log in logs)

    def test_shield_blocks_on_arithmetic_ceiling_violation(self):
        """[SHIELD-INVARIANTE #7] EV Esperado > Ganancia Máxima Posible debe ser bloqueado."""
        mock_plan = {
            "control_portafolio": {"capital_total_core_mxn": 12.0},
            "ordenes_ejecucion_partidos": [
                {"proyecciones": {"ganancia_neta_principal_mxn": 3.48}, "boletos": {"inversion_partido_A_i": 12.0}, "estrategia_seleccionada": {"codigo": "QBE-D1"}}
            ],
            "balance_global_portafolio": {"ganancia_neta_esperada_jornada_mxn": 3.50}
        }
        is_valid, logs = self.audit_plan(mock_plan, bankroll=200.0)
        assert is_valid is False
        assert any("Techo Aritmético" in log for log in logs)
