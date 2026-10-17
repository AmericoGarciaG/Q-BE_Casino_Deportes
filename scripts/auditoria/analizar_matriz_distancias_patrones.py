# -*- coding: utf-8 -*-
"""
🔬 Q-BE: MOTOR DE MATRIZ DE DISTANCIAS Y ANÁLISIS DE PATRONES P' vs q_mkt (97 PARTIDOS)
Régimen: [DBBD-FUNGIBLE] — Analítica Pura de Solo Lectura.
Autoridad: Américo García Guerrero (Director Humano)

Clasifica el universo evaluable de la temporada en los cinco patrones de acuerdo/desacuerdo
entre la P′ fiduciaria de Q-BE y el consenso desmarcado del mercado (q_mkt), midiendo además
tres distancias Manhattan sobre Δ²: interna Q-BE, interna Mercado y cruzada (P′ ↔ q_mkt).

Contrato de consumo ([GOVERNANCE-01], cero cifras inventadas):
  GET /api/markets/backtesting/calibration-report?league_id=1   ([ARCH-1.4.38] / [LN-QBE-100])
  `CalibrationMatchOut` (src/models/web_schemas.py):
      p_local | p_empate | p_visitante  →  P′ fiduciaria sellada
      q_local | q_empate | q_visitante  →  consenso desmarcado del mercado (q_mkt)
      momios                            →  trío 1X2 factual de cierre (claves L, E, V)
      resultado_real                    →  LOCAL | EMPATE | VISITANTE (cancha consumada)
      suficiencia_S_I                   →  0 ⇒ Cold Start (P′ espeja q_mkt): EXCLUIDO del test

Nota de fidelidad ([VAULT-CORE-007-C]): q_mkt se reconstruye aquí con la LEY DE BÓVEDA
`desmarcar_cuotas_proporcional` (importada, jamás modificada) sobre el trío `momios`. Un trío
ausente o degenerado NO se repara con cuotas supuestas: la propia ley lo degrada a la
ignorancia uniforme (1/3, 1/3, 1/3) y el caso se declara en el encabezado del reporte.

Uso:
    python scripts/auditoria/analizar_matriz_distancias_patrones.py
"""

import sys
import os
import httpx
from typing import Dict, Any, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.core.contracts.portfolio_math import desmarcar_cuotas_proporcional

URL_CALIBRACION = "http://127.0.0.1:8000/api/markets/backtesting/calibration-report?league_id=1"
TIMEOUT_S = 15.0


def analizar_patrones_temporada():
    print("📡 Consultando el expediente completo de calibración de temporada...")
    try:
        resp = httpx.get(URL_CALIBRACION, timeout=TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"❌ Error conectando a la API local: {e}")
        return 1

    partidos: List[Dict[str, Any]] = []
    for j in data.get("jornadas", []):
        for p in j.get("partidos", []):
            partidos.append(p)

    total_n = len(partidos)
    print(f"📊 Total de partidos recolectados de la temporada: {total_n}\n")

    # Contadores y acumuladores para los patrones
    patron_1_consenso_exitoso = []
    patron_2_qbe_vence_mkt = []
    patron_3_mkt_vence_qbe = []
    patron_4_consenso_fracasado = []
    patron_5_empates_analisis = []
    # Cierre de taxonomía: P_1 ≠ q_mkt_1 y AMBOS fallan (fuera de los 4 patrones de acuerdo).
    patron_residual_desacuerdo_fallido = []

    # Contadores de honestidad de cobertura (cero cifras inventadas)
    excluidos_cold_start = 0
    sin_trio_cuotas = 0

    for p in partidos:
        if p.get("suficiencia_S_I") == 0:
            excluidos_cold_start += 1
            continue  # Excluir Cold Start para evitar ruido

        res_real = str(p.get("resultado_real", "")).upper()

        # Probabilidades Q-BE (P')
        pl = float(p.get("p_local", 0.3333))
        pe = float(p.get("p_empate", 0.3333))
        pv = float(p.get("p_visitante", 0.3333))

        pares_qbe = [("LOCAL", pl), ("EMPATE", pe), ("VISITANTE", pv)]
        pares_qbe.sort(key=lambda x: x[1], reverse=True)
        fav_qbe = pares_qbe[0][0]
        seg_qbe = pares_qbe[1][0]

        # Probabilidades Mercado (q_mkt) — trío 1X2 factual de cierre
        cuotas = p.get("momios") or p.get("cuotas") or {}
        try:
            ol = float(cuotas.get("L", 0.0) or 0.0)
            oe = float(cuotas.get("E", 0.0) or 0.0)
            ov = float(cuotas.get("V", 0.0) or 0.0)
        except (TypeError, ValueError):
            ol = oe = ov = 0.0
        if not (ol > 1.0 and oe > 1.0 and ov > 1.0):
            # [GOVERNANCE-01] Sin trío completo no se presta cuota: la ley de bóveda degrada
            # a la ignorancia uniforme y el caso se declara en el encabezado.
            sin_trio_cuotas += 1
        ql, qe, qv = desmarcar_cuotas_proporcional(ol, oe, ov)

        pares_mkt = [("LOCAL", ql), ("EMPATE", qe), ("VISITANTE", qv)]
        pares_mkt.sort(key=lambda x: x[1], reverse=True)
        fav_mkt = pares_mkt[0][0]
        seg_mkt = pares_mkt[1][0]

        # Cálculo de Distancias Manhattan internas y cruzadas
        p_vec = {"LOCAL": pl, "EMPATE": pe, "VISITANTE": pv}
        q_vec = {"LOCAL": ql, "EMPATE": qe, "VISITANTE": qv}

        p["dist_interna_qbe"] = abs(pl - pe) + abs(pl - pv) + abs(pe - pv)
        p["dist_interna_mkt"] = abs(ql - qe) + abs(ql - qv) + abs(qe - qv)
        p["dist_cruzada"] = abs(pl - ql) + abs(pe - qe) + abs(pv - qv)
        p["fav_qbe"] = fav_qbe
        p["fav_mkt"] = fav_mkt

        # Clasificación en Patrones
        # 1. P_1 y q_mkt_1 COINCIDEN con el Resultado
        if fav_qbe == fav_mkt == res_real:
            patron_1_consenso_exitoso.append(p)
        # 2. P_1 COINCIDE con Resultado, pero q_mkt_1 NO (Q-BE vence a Mkt)
        elif fav_qbe == res_real and fav_mkt != res_real:
            patron_2_qbe_vence_mkt.append(p)
        # 3. q_mkt_1 COINCIDE con Resultado, pero P_1 NO (Mkt vence a Q-BE)
        elif fav_mkt == res_real and fav_qbe != res_real:
            patron_3_mkt_vence_qbe.append(p)
        # 4. P_1 y q_mkt_1 COINCIDEN, pero NO con el Resultado (Consenso Fracasado)
        elif fav_qbe == fav_mkt and fav_qbe != res_real:
            patron_4_consenso_fracasado.append(p)
        # 5. Residual de taxonomía: P_1 ≠ q_mkt_1 y AMBOS fallan (desacuerdo inútil)
        else:
            patron_residual_desacuerdo_fallido.append(p)

        if res_real == "EMPATE":
            patron_5_empates_analisis.append(p)

    universo_evaluable = total_n - excluidos_cold_start
    print(f"   • Excluidos por Cold Start S(I)=0 : {excluidos_cold_start}")
    print(f"   • Universo evaluable             : {universo_evaluable}")
    print(f"   • Partidos sin trío 1X2 factual  : {sin_trio_cuotas} (q_mkt degrada a 1/3 por ley de bóveda)")

    def resumen_grupo(nombre, lista):
        print(f"\n🔹 {nombre} ({len(lista)} partidos):")
        if not lista:
            print("   (Sin partidos en esta categoría)")
            return
        locs = sum(1 for p in lista if p["resultado_real"] == "LOCAL")
        emps = sum(1 for p in lista if p["resultado_real"] == "EMPATE")
        viss = sum(1 for p in lista if p["resultado_real"] == "VISITANTE")
        dist_cruz_prom = sum(p["dist_cruzada"] for p in lista) / len(lista)
        print(f"   • Desglose Real de Resultado : Local: {locs} | Empate: {emps} | Visita: {viss}")
        print(f"   • Distancia Cruzada Promedio  : {dist_cruz_prom:.4f}")

    print("=" * 80)
    print("📊 REPORTE DE ANÁLISIS DE PATRONES (FUSIONADO EN UN SOLO GRUPO)")
    print("=" * 80)
    resumen_grupo("1. P_1 y q_mkt_1 COINCIDEN con el Resultado (Consenso Exitoso)", patron_1_consenso_exitoso)
    resumen_grupo("2. P_1 COINCIDE con el Resultado, q_mkt_1 NO (Q-BE Outsmarts Market)", patron_2_qbe_vence_mkt)
    resumen_grupo("3. q_mkt_1 COINCIDE con el Resultado, P_1 NO (Mercado Vence a Q-BE)", patron_3_mkt_vence_qbe)
    resumen_grupo("4. P_1 y q_mkt_1 COINCIDEN, pero AMBOS FALLAN (Consenso Fracasado)", patron_4_consenso_fracasado)
    resumen_grupo("5. UNIVERSO EXCLUSIVO DE EMPATES (La Criptonita X)", patron_5_empates_analisis)

    # Análisis específico del Empate (Patrón 5)
    if patron_5_empates_analisis:
        emp_fav_qbe_era_emp = sum(1 for p in patron_5_empates_analisis if p["fav_qbe"] == "EMPATE")
        emp_fav_mkt_era_emp = sum(1 for p in patron_5_empates_analisis if p["fav_mkt"] == "EMPATE")
        n_emp = len(patron_5_empates_analisis)
        print(f"\n   🔍 ANATOMÍA ESPECÍFICA DE LOS {n_emp} EMPATES REALES:")
        print(f"      - Veces que Q-BE puso al Empate como P_1 (Favorito principal) : {emp_fav_qbe_era_emp}")
        print(f"      - Veces que el Mercado puso al Empate como q_mkt_1         : {emp_fav_mkt_era_emp}")
        print(
            f"      - Lectura factual: el Empate fue P_1 en {emp_fav_qbe_era_emp}/{n_emp} "
            f"({(emp_fav_qbe_era_emp / n_emp) * 100:.1f}%) y q_mkt_1 en {emp_fav_mkt_era_emp}/{n_emp} "
            f"({(emp_fav_mkt_era_emp / n_emp) * 100:.1f}%) de los empates consumados."
        )

    print("\n🧾 CIERRE DE TAXONOMÍA (universo evaluable)")
    cubiertos = (
        len(patron_1_consenso_exitoso)
        + len(patron_2_qbe_vence_mkt)
        + len(patron_3_mkt_vence_qbe)
        + len(patron_4_consenso_fracasado)
    )
    print(f"   • Patrones 1+2+3+4                        : {cubiertos}")
    print(f"   • Residual (P_1 ≠ q_mkt_1 y AMBOS fallan) : {len(patron_residual_desacuerdo_fallido)}")
    print(f"   • Universo evaluable                      : {universo_evaluable}")
    cuadre = cubiertos + len(patron_residual_desacuerdo_fallido) == universo_evaluable
    print(f"   • Cuadre                                  : {'OK' if cuadre else 'DESCUADRE'}")

    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(analizar_patrones_temporada())
