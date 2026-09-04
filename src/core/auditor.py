# Q-BE Casino Deportes — Shield Auditor Engine (src/core/auditor.py)
"""
Auditor Forense de Invarianzas Numéricas y Compuerta de Liberación (The Shield).
[LN-QBE-090] [GOVERNANCE] [ANTI-BUG]
Ejecuta la auditoría estricta de las 8 Invarianzas del Escudo antes de liberar cualquier cartera.
"""

from typing import Tuple, List, Dict, Any


class ShieldAuditorEngine:
    @classmethod
    def audit(cls, plan_dict: Dict[str, Any], bankroll: float) -> Tuple[bool, List[str]]:
        logs = []
        is_valid = True

        ctrl = plan_dict.get("control_portafolio", {})
        orders = plan_dict.get("ordenes_ejecucion_partidos", [])
        total_inv = ctrl.get("capital_total_core_mxn", 0.0)

        # Prueba 4: Hard-Cap Global (<= 25.0%)
        if total_inv > (bankroll * 0.2501):
            is_valid = False
            logs.append(f"❌ REPROBADO: Violación de Hard-Cap Global ({total_inv} MXN > 25% de {bankroll} MXN).")
        else:
            logs.append("✅ CONFORME: Hard-Cap Global respetado (<= 25.0%).")

        # Invarianza #7: Techo Aritmético de Cartera (EV <= Ganancia Máxima)
        ganancia_maxima = sum(o.get("proyecciones", {}).get("ganancia_neta_principal_mxn", 0.0) for o in orders)
        ev_esperado = plan_dict.get("balance_global_portafolio", {}).get("ganancia_neta_esperada_jornada_mxn", 0.0)
        if ev_esperado > (ganancia_maxima + 0.01):
            is_valid = False
            logs.append(f"❌ REPROBADO: Violación de Techo Aritmético (EV {ev_esperado} MXN > Ganancia Máxima {ganancia_maxima} MXN).")
        else:
            logs.append("✅ CONFORME: Techo Aritmético de Cartera respetado.")

        # Pruebas Individuales por Partido
        for ord in orders:
            boletos = ord.get("boletos", {})
            inv_p = boletos.get("inversion_partido_A_i", 0.0)
            b1 = boletos.get("boleto_1_seguro", {})
            b2 = boletos.get("boleto_2_ganancia", {})
            code = ord.get("estrategia_seleccionada", {}).get("codigo", "")
            partido = ord.get("partido", "Partido")

            # Prueba 3: Hard-Cap Individual (<= 8.0%)
            if inv_p > (bankroll * 0.0801):
                is_valid = False
                logs.append(f"❌ REPROBADO en {partido}: Inversión ({inv_p} MXN) supera el 8.0% del Bankroll.")
            else:
                logs.append(f"✅ CONFORME en {partido}: Hard-Cap individual respetado.")

            # Prueba 2: Invarianza de Cobertura según la Familia Estratégica
            if code in ["QBE-H1", "QBE-H1+", "QBE-H2", "QBE-H2+", "QBE-R1"]:
                # Cobertura Asimétrica: El seguro debe devolver el 100% de la inversión ($0.00 pérdida)
                ret_seguro = b1.get("monto_mxn", 0.0) * b1.get("momio", 1.0)
                if abs(ret_seguro - inv_p) > 0.08:
                    is_valid = False
                    logs.append(f"❌ REPROBADO en {partido}: Fallo en cobertura de Tablas (|{ret_seguro:.2f} - {inv_p:.2f}| > 0.08).")
                else:
                    logs.append(f"✅ CONFORME en {partido}: Cobertura de Tablas exacta ($0.00 pérdida).")

            elif code == "QBE-R2":
                # Doble Oportunidad Sintética X2: Ambos retornos deben estar perfectamente balanceados
                ret_emp = b1.get("monto_mxn", 0.0) * b1.get("momio", 1.0)
                ret_und = b2.get("monto_mxn", 0.0) * b2.get("momio", 1.0)
                if abs(ret_emp - ret_und) > 0.25:
                    is_valid = False
                    logs.append(f"❌ REPROBADO en {partido}: Desbalance en Doble Oportunidad X2 (|{ret_emp:.2f} - {ret_und:.2f}| > 0.25).")
                else:
                    logs.append(f"✅ CONFORME en {partido}: Doble Oportunidad X2 balanceada (Ganancia en Empate o No-Favorito).")

            elif code in ["QBE-D1", "QBE-D1+"]:
                # Posición Directa: Todo el capital asignado al Boleto 2
                if b1.get("monto_mxn", 0.0) != 0.0:
                    is_valid = False
                    logs.append(f"❌ REPROBADO en {partido}: Incoherencia en asignación directa de D1.")
                else:
                    logs.append(f"✅ CONFORME en {partido}: Asignación directa 100% conforme.")

        # Prueba 5: Colchón Financiero Satélite (Regla 3x)
        sat = plan_dict.get("modulo_satelite_asimetrico", {})
        if sat.get("autorizado", False):
            monto_sat = sat.get("monto_satelite_mxn", 0.0)
            if ev_esperado < (3.0 * monto_sat):
                is_valid = False
                logs.append(f"❌ REPROBADO: Ganancia Core ({ev_esperado} MXN) insuficiente para financiar Satélite ({monto_sat} MXN).")
            else:
                logs.append("✅ CONFORME: Colchón Satélite 3x validado.")

        return is_valid, logs