# -*- coding: utf-8 -*-
"""
🏆 Q-BE PROGOL ENGINE — DETECCIÓN DE SESGO POPULAR Y OPTIMIZADOR COMBINATORIO
[LN-QBE-037] Explotación de la Venta Pública Nacional vs Probabilidad Soberana.
[LN-QBE-074] Optimizador de Quinielas Progol por Presupuesto (2^D × 3^T ≤ B).
Base de Gobierno: Kybern Framework v12.0
"""

from typing import Dict, Any, List


def calcular_sesgo_quiniela(v_publico: Dict[str, float], p_soberana: Dict[str, float]) -> Dict[str, Any]:
    """
    [LN-QBE-037] Compara la venta pública nacional contra la probabilidad real de Q-BE:
    Sesgo_k = V_publico_k - P_soberana_k
    Si el sesgo local supera +20% (0.20), el valor esperado se desplaza hacia el empate/visita (X2).
    """
    sesgo_l = round(float(v_publico.get("L", 0.0)) - float(p_soberana.get("L", 0.0)), 4)
    sesgo_e = round(float(v_publico.get("E", 0.0)) - float(p_soberana.get("E", 0.0)), 4)
    sesgo_v = round(float(v_publico.get("V", 0.0)) - float(p_soberana.get("V", 0.0)), 4)

    alerta = False
    rec = "BASE_SIMPLE"

    # Detección de sesgo abrumador del público
    if sesgo_l >= 0.20:
        alerta = True
        rec = "DOBLE_COBERTURA_SESGO (X2)"
    elif sesgo_v >= 0.20:
        alerta = True
        rec = "DOBLE_COBERTURA_SESGO (1X)"
    elif float(p_soberana.get("L", 0.0)) >= 0.65:
        rec = "BASE_SIMPLE (L)"
    elif float(p_soberana.get("V", 0.0)) >= 0.65:
        rec = "BASE_SIMPLE (V)"
    else:
        rec = "TRIPLE_ESTRATÉGICO (1X2)"

    return {
        "sesgo_local": sesgo_l,
        "sesgo_empate": sesgo_e,
        "sesgo_visitante": sesgo_v,
        "alerta_sesgo": alerta,
        "recomendacion_cobertura": rec
    }


def optimizar_quiniela_por_presupuesto(items: List[Dict[str, Any]], presupuesto_mxn: float = 360.0) -> Dict[str, Any]:
    """
    [LN-QBE-074] Asigna matemáticamente Triples y Dobles maximizando cobertura sobre sesgo popular:
    Costo Oficial Progol = 15.00 * (2^D) * (3^T) <= Presupuesto.

    Regla de Asignación:
    - Ordena los 14 encuentros por magnitud de sesgo popular absoluto descendente.
    - Asigna Triples a los partidos de máxima incertidumbre/sesgo.
    - Asigna Dobles a los partidos con sesgo >= +0.20.
    - Fija como Bases Simples los partidos de alta probabilidad (P_L >= 0.65 o P_V >= 0.65).
    """
    precio_simple = 15.0
    presupuesto = float(presupuesto_mxn)

    # 1. Encontrar la combinación óptima (D, T) que maximice el costo sin superar el presupuesto
    mejor_d, mejor_t, mejor_costo = 0, 0, precio_simple

    for t in range(5):      # 0 a 4 triples
        for d in range(9):  # 0 a 8 dobles
            comb = (2 ** d) * (3 ** t)
            costo = comb * precio_simple
            if costo <= presupuesto and costo > mejor_costo:
                mejor_costo = costo
                mejor_d = d
                mejor_t = t

    # 2. Calcular sesgos y ordenar por magnitud descendente
    items_analizados = []
    for p in items:
        sesgo_data = calcular_sesgo_quiniela(p.get("v_pub", {}), p.get("p_qbe", {}))
        magnitud_sesgo = abs(sesgo_data.get("sesgo_local", 0.0)) + abs(sesgo_data.get("sesgo_visitante", 0.0))
        items_analizados.append({
            **p,
            "sesgo_magnitud": magnitud_sesgo,
            "analisis": sesgo_data
        })

    items_ordenados = sorted(items_analizados, key=lambda x: x["sesgo_magnitud"], reverse=True)

    # 3. Asignar Triples, Dobles y Simples según la Regla de Asignación [LN-QBE-074]
    triples_restantes = mejor_t
    dobles_restantes = mejor_d
    matriz_resultado = []

    for item in items_ordenados:
        s = item["analisis"]
        p_qbe = item.get("p_qbe", {})

        juega_l, juega_e, juega_v = False, False, False
        rec = "SIMPLE"

        if triples_restantes > 0:
            # Triple estratégico: cubre las 3 casillas (1, X, 2)
            juega_l, juega_e, juega_v = True, True, True
            triples_restantes -= 1
            rec = "TRIPLE_ESTRATÉGICO (1X2)"
        elif dobles_restantes > 0 and s.get("alerta_sesgo"):
            # Doble en la dirección opuesta al sesgo popular
            if s.get("sesgo_local", 0.0) >= 0.20:
                juega_e, juega_v = True, True
                rec = "DOBLE_SESGO (X2)"
            elif s.get("sesgo_visitante", 0.0) >= 0.20:
                juega_l, juega_e = True, True
                rec = "DOBLE_SESGO (1X)"
            else:
                juega_l, juega_v = True, True
                rec = "DOBLE_EXTREMOS (12)"
            dobles_restantes -= 1
        elif dobles_restantes > 0:
            # Doble en las dos opciones de mayor probabilidad Q-BE
            sorted_probs = sorted(
                [("L", p_qbe.get("L", 0.33)), ("E", p_qbe.get("E", 0.33)), ("V", p_qbe.get("V", 0.33))],
                key=lambda x: x[1],
                reverse=True
            )
            top_2 = [x[0] for x in sorted_probs[:2]]
            juega_l = "L" in top_2
            juega_e = "E" in top_2
            juega_v = "V" in top_2
            dobles_restantes -= 1
            rec = f"DOBLE_VALOR ({top_2[0]}{top_2[1]})"
        else:
            # Simple a la probabilidad más alta según Q-BE
            sorted_probs = sorted(
                [("L", p_qbe.get("L", 0.33)), ("E", p_qbe.get("E", 0.33)), ("V", p_qbe.get("V", 0.33))],
                key=lambda x: x[1],
                reverse=True
            )
            top_1 = sorted_probs[0][0]
            juega_l = (top_1 == "L")
            juega_e = (top_1 == "E")
            juega_v = (top_1 == "V")
            rec = f"BASE_SIMPLE ({top_1})"

        matriz_resultado.append({
            "order": item.get("order"),
            "local": item.get("local"),
            "visitante": item.get("visitante"),
            "juega_L": juega_l,
            "juega_E": juega_e,
            "juega_V": juega_v,
            "alerta_sesgo": s.get("alerta_sesgo", False),
            "recomendacion": rec
        })

    # Reordenar por el número oficial del partido (1 al 14)
    matriz_final = sorted(matriz_resultado, key=lambda x: x["order"])

    return {
        "costo_total_mxn": mejor_costo,
        "combinaciones_totales": (2 ** mejor_d) * (3 ** mejor_t),
        "dobles_asignados": mejor_d,
        "triples_asignados": mejor_t,
        "matriz_quiniela": matriz_final
    }
