# Q-BE Casino Deportes — Portfolio & Router Engine (src/core/portfolio.py)
"""
Router de Portafolio, Dimensionamiento Fraccional de Kelly y Asignación de Capital.
[LN-QBE-070] [BIZ-LOGIC] [ALGO-PROTECTED]
Calcula la asignación de capital y el Dutching exacto eliminando pisos fijos y respetando
el techo aritmético de cartera.
"""

from typing import List, Dict, Any
from src.core.catalog import STRATEGY_CATALOG
from src.models.decision import (
    MatchExecutionOrder, StrategySelection, KeyMetrics, TicketOrder,
    MatchTickets, Projections, CashoutTargets, SatelliteModule,
    PortfolioControl, PortfolioBalance, PortfolioExecutionPlan
)


class PortfolioEngine:
    DESCRIPCIONES_OFICIALES = {k: v.descripcion_ejecutiva for k, v in STRATEGY_CATALOG.items()}

    @classmethod
    def select_best_strategy(
        cls,
        evals: Dict[str, Dict[str, Any]],
        psi_ruina: float,
        pago_anticipado: bool,
        p_fav: float = 0.50
    ) -> tuple:
        """
        Escalera Canónica de Prioridad Absoluta V2.5 por Utilidad Ajustada:
        U_Directo = EV_Net * P_Fav
        U_Cobertura = EV_Net * (1.0 - Psi_Ruina)
        """
        def calc_utility(strat_key: str) -> float:
            ev = evals[strat_key]["ev_neto_roi"]
            downside = p_fav if strat_key in ("QBE_R1", "QBE_R2") else psi_ruina
            return float(ev * ((1.0 - downside) ** 2))

        def calc_direct_utility(strat_key: str) -> float:
            ev = evals[strat_key]["ev_neto_roi"]
            return float(ev * p_fav)

        def calc_coverage_utility(strat_key: str) -> float:
            ev = evals[strat_key]["ev_neto_roi"]
            return float(ev * (1.0 - psi_ruina))

        code = None

        # Nivel 1: Freeroll Doble Impacto (Joya)
        if evals.get("QBE_H2_plus", {}).get("viable"):
            code = "QBE-H2+"
        else:
            direct_viable = [s for s in ["QBE_D1_plus", "QBE_D1"] if evals.get(s, {}).get("viable")]
            coverage_viable = [s for s in ["QBE_H1_plus", "QBE_H1"] if evals.get(s, {}).get("viable")]

            if direct_viable and coverage_viable:
                direct_best = max(direct_viable, key=calc_direct_utility)
                coverage_best = max(coverage_viable, key=calc_coverage_utility)
                if psi_ruina <= 0.08 and calc_direct_utility(direct_best) >= calc_coverage_utility(coverage_best):
                    code = direct_best.replace("_plus", "+").replace("_", "-")
                else:
                    # Nivel 2: Favoritos de Alta Convicción Potenciados
                    if evals.get("QBE_D1_plus", {}).get("viable") and psi_ruina <= 0.08 and p_fav >= 0.60:
                        code = "QBE-D1+"
                    else:
                        nivel_2 = [s for s in ["QBE_H1_plus", "QBE_D1_plus"] if evals.get(s, {}).get("viable")]
                        if nivel_2:
                            best = max(nivel_2, key=calc_utility)
                            code = best.replace("_plus", "+").replace("_", "-")
                        else:
                            # Nivel 3: Favoritos y Cobertura Estándar (H1 / D1)
                            nivel_3 = [s for s in ["QBE_H1", "QBE_D1"] if evals.get(s, {}).get("viable")]
                            if nivel_3:
                                best = max(nivel_3, key=calc_utility)
                                code = best.replace("_", "-")
                            else:
                                # Nivel 4: Empate de Valor (H2)
                                if evals.get("QBE_H2", {}).get("viable"):
                                    code = "QBE-H2"
                                else:
                                    # Nivel 5: Asaltos Inversos Condicionados - Familia R (R1 / R2)
                                    nivel_5 = [s for s in ["QBE_R1", "QBE_R2"] if evals.get(s, {}).get("viable")]
                                    if nivel_5:
                                        best = max(nivel_5, key=calc_utility)
                                        code = best.replace("_", "-")
                                    else:
                                        # Nivel 6: Protección de Capital (QBE-00)
                                        return "QBE-00", evals.get("QBE_00", {}).get("nombre_oficial", "Veto Preventivo de Capital"), 0.0, "N/A"
            else:
                # Nivel 2: Favoritos de Alta Convicción Potenciados
                if evals.get("QBE_D1_plus", {}).get("viable") and psi_ruina <= 0.08 and p_fav >= 0.60:
                    code = "QBE-D1+"
                else:
                    nivel_2 = [s for s in ["QBE_H1_plus", "QBE_D1_plus"] if evals.get(s, {}).get("viable")]
                    if nivel_2:
                        best = max(nivel_2, key=calc_utility)
                        code = best.replace("_plus", "+").replace("_", "-")
                    else:
                        # Nivel 3: Favoritos y Cobertura Estándar (H1 / D1)
                        nivel_3 = [s for s in ["QBE_H1", "QBE_D1"] if evals.get(s, {}).get("viable")]
                        if nivel_3:
                            best = max(nivel_3, key=calc_utility)
                            code = best.replace("_", "-")
                        else:
                            # Nivel 4: Empate de Valor (H2)
                            if evals.get("QBE_H2", {}).get("viable"):
                                code = "QBE-H2"
                            else:
                                # Nivel 5: Asaltos Inversos Condicionados - Familia R (R1 / R2)
                                nivel_5 = [s for s in ["QBE_R1", "QBE_R2"] if evals.get(s, {}).get("viable")]
                                if nivel_5:
                                    best = max(nivel_5, key=calc_utility)
                                    code = best.replace("_", "-")
                                else:
                                    # Nivel 6: Protección de Capital (QBE-00)
                                    return "QBE-00", evals.get("QBE_00", {}).get("nombre_oficial", "Veto Preventivo de Capital"), 0.0, "N/A"

        clean_key = code.replace("+", "_plus").replace("-", "_")
        nombre = evals[clean_key]["nombre_oficial"]
        ev = evals[clean_key]["ev_neto_roi"]
        promocion = "Pago Anticipado" if ("+" in code or code == "QBE-R1" or pago_anticipado) else "Estándar"
        return code, nombre, ev, promocion

    @classmethod
    def build_plan(
        cls,
        approved_matches: List[Dict[str, Any]],
        bankroll: float,
        mode: str = "BANKROLL"
    ) -> PortfolioExecutionPlan:
        k_count = len(approved_matches)
        if k_count == 0:
            raise ValueError("No hay partidos aprobados para construir el portafolio.")

        # 1. Ruina Multi-Activo
        prod_psi = 1.0
        for m in approved_matches:
            prod_psi *= m["psi_downside"]
        p_ruina_total = prod_psi * 100.0
        blindaje = 100.0 - p_ruina_total

        # 2. Scores de Calidad y Asignación de Capital
        scores = []
        for m in approved_matches:
            s_i = max(0.01, m["ev_neto_roi"]) / max(0.01, m["psi_downside"])
            scores.append(s_i)

        sum_scores = sum(scores) if sum(scores) > 0 else 1.0
        weights = [s / sum_scores for s in scores]

        bolsa_core = bankroll * min(0.25, 0.06 * k_count)  # Tope 25%

        orders: List[MatchExecutionOrder] = []
        total_inv_core = 0.0
        ganancia_esperada_core = 0.0

        for idx, m in enumerate(approved_matches):
            code = m["strategy_code"]
            nombre = m["strategy_nombre"]
            ev_roi = m["ev_neto_roi"]
            psi = m["psi_downside"]
            phi = m["phi_lead2"]
            o_fav, o_emp, o_und = m["odd_fav"], m["odd_emp"], m["odd_und"]
            fav_name, und_name = m["fav_name"], m["und_name"]

            # Hard-Cap Individual <= 8.0%
            if mode == "BANKROLL":
                cap_i = min(0.08, max(0.02, ev_roi / (3.0 * max(0.01, psi))))
                inv_partido = min(bolsa_core * weights[idx], bankroll * cap_i)
                inv_partido = round(max(4.00, inv_partido), 2)
            else:
                inv_partido = 10.00

            total_inv_core += inv_partido

            # Estructuración de Boletos (Dutching Exacto)
            if "H2" in code:
                # Seguro en Fav, Ganancia en Empate
                b1_sel = f"Gana {fav_name}" + (" + PA" if "+" in code else "")
                b1_momio = o_fav
                b1_monto = round(inv_partido / b1_momio, 2)
                b2_sel = "Empate" + (" + PA" if "+" in code else "")
                b2_momio = o_emp
                b2_monto = round(inv_partido - b1_monto, 2)
                ganancia_neta = round((b2_monto * b2_momio) - inv_partido, 2)
                roi_pct = round((ganancia_neta / inv_partido) * 100.0, 2)
                freeroll_neta = round((b1_monto * b1_momio) + (b2_monto * b2_momio) - inv_partido, 2) if "+" in code else 0.0
                freeroll_roi = round((freeroll_neta / inv_partido) * 100.0, 2) if "+" in code else 0.0
                out_min85 = f"${round(b2_monto * b2_momio * 0.85, 2)} MXN (Asegurar ~85% del premio al minuto 85' si hay empate)"
                tablas_amt = inv_partido

            elif "H1" in code:
                # Seguro en Empate, Ganancia en Fav
                b1_sel = "Empate"
                b1_momio = o_emp
                b1_monto = round(inv_partido / b1_momio, 2)
                b2_sel = f"Gana {fav_name}" + (" + PA" if "+" in code else "")
                b2_momio = o_fav
                b2_monto = round(inv_partido - b1_monto, 2)
                ganancia_neta = round((b2_monto * b2_momio) - inv_partido, 2)
                roi_pct = round((ganancia_neta / inv_partido) * 100.0, 2)
                freeroll_neta = round((b1_monto * b1_momio) + (b2_monto * b2_momio) - inv_partido, 2) if "+" in code else 0.0
                freeroll_roi = round((freeroll_neta / inv_partido) * 100.0, 2) if "+" in code else 0.0
                out_min85 = "Sin descuento. Dejar correr al 90' para cobrar 100% Tablas o cobro anticipado por ventaja de 2 goles."
                tablas_amt = inv_partido

            elif code == "QBE-R1":
                # Seguro en Empate, Ganancia en Underdog
                b1_sel = "Empate"
                b1_momio = o_emp
                b1_monto = round(inv_partido / b1_momio, 2)
                b2_sel = f"Gana {und_name} + PA"
                b2_momio = o_und
                b2_monto = round(inv_partido - b1_monto, 2)
                ganancia_neta = round((b2_monto * b2_momio) - inv_partido, 2)
                roi_pct = round((ganancia_neta / inv_partido) * 100.0, 2)
                freeroll_neta, freeroll_roi = 0.0, 0.0
                out_min85 = "Sin descuento. Dejar correr al 90' para cobrar 100% Tablas en empate o victoria de Underdog."
                tablas_amt = inv_partido

            elif code == "QBE-R2":
                # Doble Oportunidad Sintética X2 (Dutching proporcional)
                if o_emp > 0 and o_und > 0:
                    inv_emp_w = (1.0 / o_emp) / ((1.0 / o_emp) + (1.0 / o_und))
                else:
                    inv_emp_w = 0.5
                b1_sel = "Empate"
                b1_momio = o_emp
                b1_monto = round(inv_partido * inv_emp_w, 2)
                b2_sel = f"Gana {und_name}"
                b2_momio = o_und
                b2_monto = round(inv_partido - b1_monto, 2)
                ganancia_neta = round(min(b1_monto * b1_momio, b2_monto * b2_momio) - inv_partido, 2)
                roi_pct = round((ganancia_neta / inv_partido) * 100.0, 2)
                freeroll_neta, freeroll_roi = 0.0, 0.0
                out_min85 = "Dejar correr al 90'. Ambos boletos cubren el escenario X2."
                tablas_amt = inv_partido

            else:  # QBE-D1 / QBE-D1+
                b1_sel = "N/A ($0.00)"
                b1_momio = 0.0
                b1_monto = 0.0
                b2_sel = f"Gana {fav_name}" + (" + PA" if "+" in code else "")
                b2_momio = o_fav
                b2_monto = inv_partido
                ganancia_neta = round((b2_monto * b2_momio) - inv_partido, 2)
                roi_pct = round((ganancia_neta / inv_partido) * 100.0, 2)
                freeroll_neta, freeroll_roi = 0.0, 0.0
                out_min85 = "N/A (Dejar correr al 90' o cobrado anticipadamente por ventaja de 2 goles)."
                tablas_amt = 0.0

            # Contribución aritmética pura de EV (CERO pisos artificiales)
            ev_factor = (ev_roi / 100.0) if ev_roi > 0 else 0.0
            ganancia_esperada_core += (ganancia_neta * ev_factor)

            order = MatchExecutionOrder(
                id_partido=m["id_partido"],
                partido=m["partido_nombre"],
                horario_evento=m.get("horario", "Fin de Semana"),
                estrategia_seleccionada=StrategySelection(
                    codigo=code,
                    nombre_oficial=nombre,
                    descripcion_ejecutiva=cls.DESCRIPCIONES_OFICIALES.get(code, "Estrategia Cuantitativa"),
                    linea_promocional="Pago Anticipado" if "+" in code or code == "QBE-R1" else "Estándar"
                ),
                metricas_clave=KeyMetrics(
                    score_calidad_S_i=round(scores[idx], 4),
                    peso_portafolio_w_i=round(weights[idx], 4),
                    phi_lead2_prob_ventaja_2_goles=round(phi, 4),
                    psi_downside_riesgo=round(psi, 4),
                    ev_neto_roi_porcentaje=round(ev_roi, 2)
                ),
                forma_reciente_auditada={
                    "fav_resumen": f"Posición #{m.get('fav_pos', 1)}, {m.get('fav_pts', 0)} pts | Q_mod: {m.get('q_mod_fav', 1.0)}",
                    "und_resumen": f"Posición #{m.get('und_pos', 18)}, {m.get('und_pts', 0)} pts | Q_mod: {m.get('q_mod_und', 1.0)}"
                },
                boletos=MatchTickets(
                    inversion_partido_A_i=inv_partido,
                    boleto_1_seguro=TicketOrder(seleccion=b1_sel, momio=b1_momio, monto_mxn=b1_monto),
                    boleto_2_ganancia=TicketOrder(seleccion=b2_sel, momio=b2_momio, monto_mxn=b2_monto)
                ),
                proyecciones=Projections(
                    ganancia_neta_principal_mxn=ganancia_neta,
                    roi_principal_porcentaje=roi_pct,
                    freeroll_doble_ganancia_mxn=freeroll_neta,
                    freeroll_roi_porcentaje=freeroll_roi,
                    resultado_tablas_mxn=tablas_amt,
                    perdida_maxima_posible_mxn=inv_partido
                ),
                cashout_targets=CashoutTargets(
                    monto_salida_emergencia_tablas_mxn=tablas_amt,
                    monto_salida_optima_min85=out_min85,
                    instruccion_emergencia_rompequinielas=f"CashOut en cuanto ofrezca Tablas (${inv_partido} MXN) al igualar en el 2T." if tablas_amt > 0 else "Monitorear en el 2T.",
                    instruccion_desarrollo_normal=out_min85
                )
            )
            orders.append(order)

        # 3. Satélite Asimétrico
        sat_module = SatelliteModule(
            autorizado=False,
            justificacion_financiamiento="No se autoriza boleto satélite al no existir underdogs con ventaja extrema en cuotas >= 4.50."
        )

        # 4. Consolidación de Balance con Techo Aritmético Estricto
        total_inv_core = round(total_inv_core, 2)
        ganancia_maxima_posible = sum(o.proyecciones.ganancia_neta_principal_mxn for o in orders)
        ganancia_esperada_core = round(min(ganancia_maxima_posible, max(0.0, ganancia_esperada_core)), 2)
        roi_global_esp = round((ganancia_esperada_core / total_inv_core) * 100.0, 2) if total_inv_core > 0 else 0.0

        return PortfolioExecutionPlan(
            control_portafolio=PortfolioControl(
                modalidad="BANKROLL" if mode == "BANKROLL" else "VAQUITA",
                total_partidos_core_aprobados=k_count,
                capital_total_core_mxn=total_inv_core,
                probabilidad_ruina_total_porcentaje=round(p_ruina_total, 4),
                blindaje_global_preservacion_porcentaje=round(blindaje, 4),
                desglose_vaquita={"activa": mode == "VAQUITA", "cuota_fija_por_partido_mxn": 10.0, "numero_socios": 5},
                desglose_bankroll={"activa": mode == "BANKROLL", "bankroll_total": bankroll, "porcentaje_total_arriesgado": round((total_inv_core / bankroll) * 100.0, 2)}
            ),
            ordenes_ejecucion_partidos=orders,
            modulo_satelite_asimetrico=sat_module,
            balance_global_portafolio=PortfolioBalance(
                capital_total_comprometido_mxn=total_inv_core,
                ganancia_neta_esperada_jornada_mxn=ganancia_esperada_core,
                roi_global_esperado_porcentaje=roi_global_esp
            )
        )