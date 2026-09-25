# -*- coding: utf-8 -*-
"""
🏆 Q-BE CD WEB — CENTINELA AUTÓNOMO DE MERCADO Y CUOTAS MULTI-OPERADOR (CALIENTE & BETWAY)
[SDLC-02: Standalone Background Engine — Market & Ledger Edition]
[LN-QBE-007-B, C, D, E] & [ARCH-1.4.7]
Ingesta Fáctica, Normalización, Descuento de Margen, Arbitraje Cross-Market y Consenso Multi-Operador.
Base de Gobierno: Kybern Framework v12.0 / v13.5
"""

import sys
import os
import re
import time
import argparse
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy.orm.attributes import flag_modified
from src.storage.gateway import PersistenceGateway
from src.storage.models import League, FixtureSnapshot, SovereignDistribution
from src.ingestion.caliente_scraper import CalienteMarketScraper
from src.ingestion.betway_scraper import BetwayMarketScraper
from src.ingestion.normalizer import canonicalize_team_name
from src.core.triage import evaluar_viabilidad_cuotas

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CentinelaMercado")


def calcular_probabilidades_sin_comision(L: float, E: float, V: float) -> Tuple[float, float, float]:
    """
    [LN-QBE-007-C] Descuento de Margen Comercial (Vig-Free De-biasing al Símplex Δ²)
    Calcula probabilidades implícitas normalizadas desprovistas de la comisión de la casa.
    """
    if L <= 1.0 or E <= 1.0 or V <= 1.0:
        return (0.0, 0.0, 0.0)

    pi_l = 1.0 / L
    pi_e = 1.0 / E
    pi_v = 1.0 / V
    S = pi_l + pi_e + pi_v

    if S <= 0.0:
        return (0.0, 0.0, 0.0)

    return (pi_l / S, pi_e / S, pi_v / S)


def evaluar_arbitraje_partido(momios_operadores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    [LN-QBE-007-D] Detector de Arbitraje Inter-Casas (Cross-Market Surebet)
    Evalúa la combinación de mejores cuotas entre operadores para detectar ineficiencias (+EV).
    """
    best_l = {"momio": 0.0, "operador": None}
    best_e = {"momio": 0.0, "operador": None}
    best_v = {"momio": 0.0, "operador": None}

    for op_name, m in momios_operadores.items():
        if not m:
            continue
        l_val = float(m.get("L", 0.0))
        e_val = float(m.get("E", 0.0))
        v_val = float(m.get("V", 0.0))

        if l_val > best_l["momio"]:
            best_l = {"momio": l_val, "operador": op_name}
        if e_val > best_e["momio"]:
            best_e = {"momio": e_val, "operador": op_name}
        if v_val > best_v["momio"]:
            best_v = {"momio": v_val, "operador": op_name}

    if best_l["momio"] > 1.0 and best_e["momio"] > 1.0 and best_v["momio"] > 1.0:
        indice = (1.0 / best_l["momio"]) + (1.0 / best_e["momio"]) + (1.0 / best_v["momio"])
        existe = indice < 1.0000
        roi_pct = ((1.0 / indice) - 1.0) * 100.0 if existe else 0.0
    else:
        indice = 1.0
        existe = False
        roi_pct = 0.0

    return {
        "existe": existe,
        "indice": round(indice, 4),
        "roi_pct": round(roi_pct, 2),
        "mejor_L": best_l,
        "mejor_E": best_e,
        "mejor_V": best_v
    }


def calcular_consenso_y_deltas(prob_ops: Dict[str, Dict[str, float]], p_qbe: Tuple[float, float, float]) -> Dict[str, Any]:
    """
    [LN-QBE-007-E] Consenso de Mercado y Diferenciales vs. Distribución Soberana
    Promedia las probabilidades justas (sin comisión) y calcula la discrepancia (delta) vs Q-BE.
    """
    valid_ops = [p for p in prob_ops.values() if p and p.get("p_L", 0) > 0]
    if not valid_ops:
        return {
            "p_L_mercado": 0.0,
            "p_E_mercado": 0.0,
            "p_V_mercado": 0.0,
            "delta_L": 0.0,
            "delta_E": 0.0,
            "delta_V": 0.0
        }

    n = len(valid_ops)
    bar_q_l = sum(p["p_L"] for p in valid_ops) / n
    bar_q_e = sum(p["p_E"] for p in valid_ops) / n
    bar_q_v = sum(p["p_V"] for p in valid_ops) / n

    p_qbe_l, p_qbe_e, p_qbe_v = p_qbe

    return {
        "p_L_mercado": round(bar_q_l, 3),
        "p_E_mercado": round(bar_q_e, 3),
        "p_V_mercado": round(bar_q_v, 3),
        "delta_L": round(p_qbe_l - bar_q_l, 3),
        "delta_E": round(p_qbe_e - bar_q_e, 3),
        "delta_V": round(p_qbe_v - bar_q_v, 3)
    }


def extraer_mercado_viva(partidos_slate: List[Dict[str, Any]], operador: str = "todos") -> Dict[str, List[Dict[str, Any]]]:
    """
    Sincroniza la ingesta de cuotas 1X2 desde los operadores especificados (caliente, betway, todos).
    """
    resultados = {}

    if operador in ("caliente", "todos"):
        logger.info(f"Escaneando Caliente.mx para {len(partidos_slate)} partidos del slate...")
        try:
            resultados["caliente"] = CalienteMarketScraper.extraer_cuotas_focalizadas(partidos_slate)
        except Exception as e:
            logger.error(f"Error escaneando Caliente.mx: {e}")
            resultados["caliente"] = []

    if operador in ("betway", "todos"):
        logger.info(f"Escaneando Betway.mx para {len(partidos_slate)} partidos del slate...")
        try:
            resultados["betway"] = BetwayMarketScraper.extraer_cuotas_focalizadas(partidos_slate)
        except Exception as e:
            logger.error(f"Error escaneando Betway.mx: {e}")
            resultados["betway"] = []

    return resultados


def actualizar_cuotas_en_sqlite(jornada: int, dict_cuotas: Dict[str, List[Dict[str, Any]]], operador_sel: str = "todos") -> List[Dict[str, Any]]:
    gateway = PersistenceGateway()
    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    ahora_iso = datetime.now(timezone.utc).isoformat()
    partidos_procesados = []

    with gateway.write_transaction() as tx:
        league = tx.query(League).filter((League.fotmob_id == 262) | (League.id == 262)).first()
        if not league:
            raise RuntimeError("Liga MX no encontrada en SQLite.")

        fix_snap = tx.query(FixtureSnapshot).filter(
            FixtureSnapshot.league_id == league.id,
            FixtureSnapshot.matchday == jornada
        ).order_by(FixtureSnapshot.updated_at.desc()).first()

        if not fix_snap or not fix_snap.matches_json:
            raise RuntimeError(f"No existe FixtureSnapshot para la Jornada {jornada}. Ejecuta primero centinela_deportivo.py.")

        matches_actualizados = []

        for fx_orig in fix_snap.matches_json:
            fx = dict(fx_orig)
            loc_can = canonicalize_team_name(fx["local"])
            vis_can = canonicalize_team_name(fx["visitante"])
            mid = fx.get("id_partido", "")

            # Mapa de operadores preservando estado previo si existe
            momios_operadores = dict(fx.get("momios_operadores") or {})

            for op_name, cuotas_list in dict_cuotas.items():
                cuota_match = None
                for c in cuotas_list:
                    c_loc = canonicalize_team_name(c.get("local"))
                    c_vis = canonicalize_team_name(c.get("visitante"))
                    if (c_loc, c_vis) == (loc_can, vis_can):
                        cuota_match = c
                        break

                if cuota_match and cuota_match.get("L") is not None:
                    momios_operadores[op_name] = {
                        "L": float(cuota_match["L"]),
                        "E": float(cuota_match["E"]),
                        "V": float(cuota_match["V"]),
                        "pa": bool(cuota_match.get("pago_anticipado", False if op_name == "betway" else True)),
                        "updated_at": ahora_iso
                    }

            fx["momios_operadores"] = momios_operadores

            # Mantener fx["momios"] con Caliente (o Betway como fallback) para retrocompatibilidad
            momio_def = momios_operadores.get("caliente") or momios_operadores.get("betway") or fx.get("momios")
            if momio_def:
                fx["momios"] = {
                    "L": float(momio_def["L"]),
                    "E": float(momio_def["E"]),
                    "V": float(momio_def["V"]),
                    "pago_anticipado": bool(momio_def.get("pa", True))
                }

            # Probabilidades desprovistas de comisión por operador
            probabilidades_sin_comision = {}
            for op_name, m in momios_operadores.items():
                if m and m.get("L") and m["L"] > 1.0:
                    ql, qe, qv = calcular_probabilidades_sin_comision(m["L"], m["E"], m["V"])
                    probabilidades_sin_comision[op_name] = {
                        "p_L": round(ql, 3),
                        "p_E": round(qe, 3),
                        "p_V": round(qv, 3)
                    }
            fx["probabilidades_sin_comision"] = probabilidades_sin_comision

            # Arbitraje Inter-Casas
            arb_res = evaluar_arbitraje_partido(momios_operadores)
            fx["arbitraje"] = arb_res

            # Consultar probabilidad soberana real
            dist_db = tx.query(SovereignDistribution).filter(SovereignDistribution.match_id == mid).first()
            p_soberana_l = dist_db.p_local if dist_db else 0.45
            p_soberana_e = dist_db.p_empate if dist_db else 0.28
            p_soberana_v = dist_db.p_visitante if dist_db else 0.27

            # Consenso de mercado y deltas vs Q-BE
            consenso_res = calcular_consenso_y_deltas(probabilidades_sin_comision, (p_soberana_l, p_soberana_e, p_soberana_v))
            fx["consenso_mercado"] = consenso_res

            caliente_m = momios_operadores.get("caliente")
            betway_m = momios_operadores.get("betway")

            l_cal = caliente_m["L"] if caliente_m else 0.0
            e_cal = caliente_m["E"] if caliente_m else 0.0
            v_cal = caliente_m["V"] if caliente_m else 0.0

            l_btw = betway_m["L"] if betway_m else 0.0
            e_btw = betway_m["E"] if betway_m else 0.0
            v_btw = betway_m["V"] if betway_m else 0.0

            best_l = arb_res["mejor_L"]["momio"]
            best_e = arb_res["mejor_E"]["momio"]
            best_v = arb_res["mejor_V"]["momio"]

            viable = False
            motivo = "Cuotas no publicadas"
            if best_l > 1.0 and best_e > 1.0 and best_v > 1.0:
                pa_val = caliente_m.get("pa", True) if caliente_m else False
                viable, motivo = evaluar_viabilidad_cuotas(best_l, best_e, best_v, pago_anticipado=pa_val)

            fx["disponible_para_seleccion"] = True
            fx["es_operable"] = True
            fx["es_viable_triaje"] = viable
            fx["motivo_triaje"] = motivo

            partidos_procesados.append({
                "partido": f"{fx['local']} vs {fx['visitante']}",
                "horario": fx.get("horario", ""),
                "caliente": {"L": l_cal, "E": e_cal, "V": v_cal, "pa": caliente_m.get("pa") if caliente_m else False},
                "betway": {"L": l_btw, "E": e_btw, "V": v_btw, "pa": betway_m.get("pa") if betway_m else False},
                "best": {"L": best_l, "E": best_e, "V": best_v},
                "consenso": consenso_res,
                "deltas": (consenso_res["delta_L"], consenso_res["delta_E"], consenso_res["delta_V"]),
                "triaje": "APROBADO" if viable else ("DESCARTADO" if best_l > 1.0 else "PENDIENTE"),
                "arbitraje": arb_res
            })

            matches_actualizados.append(fx)

        fix_snap.matches_json = matches_actualizados
        flag_modified(fix_snap, "matches_json")
        fix_snap.updated_at = ahora

    return partidos_procesados


def imprimir_tablero_mercado(partidos: List[Dict[str, Any]], duracion: float, jornada: int, operador_sel: str) -> None:
    banner = "=" * 165
    subbanner = "-" * 165

    print("\n" + banner)
    print(f"🏆 Q-BE CD WEB — TABLERO DE MERCADO Y TELEMETRÍA MULTI-CASINO (JORNADA {jornada})")
    print(banner)
    print(f"TIEMPO DE ESCANEO: {duracion:.2f}s | OPERADOR: {operador_sel.upper()} | PERSISTENCIA: data/qbe_database.db [WAL Mode]")
    print(subbanner)
    print(
        f" #  {'HORARIO':<11} {'PARTIDO':<28} {'CALIENTE 1X2':<18} {'BETWAY 1X2':<18} "
        f"{'MEJOR 1X2':<18} {'CONSENSO SIN COMISIÓN':<23} {'Q-BE VS MERCADO (DIFF)':<24} {'ARBITRAJE'}"
    )
    print(subbanner)

    for idx, p in enumerate(partidos, 1):
        cal = p["caliente"]
        btw = p["betway"]
        bst = p["best"]
        con = p["consenso"]
        dL, dE, dV = p["deltas"]
        arb = p["arbitraje"]

        c_txt = f"{cal['L']:.2f}/{cal['E']:.2f}/{cal['V']:.2f}" if cal['L'] > 0 else "—"
        b_txt = f"{btw['L']:.2f}/{btw['E']:.2f}/{btw['V']:.2f}" if btw['L'] > 0 else "—"
        m_txt = f"{bst['L']:.2f}/{bst['E']:.2f}/{bst['V']:.2f}" if bst['L'] > 0 else "—"
        con_txt = f"{con['p_L_mercado']:.3f}/{con['p_E_mercado']:.3f}/{con['p_V_mercado']:.3f}" if con['p_L_mercado'] > 0 else "—"
        diff_txt = f"{dL:+.3f}/{dE:+.3f}/{dV:+.3f}" if con['p_L_mercado'] > 0 else "—"

        if arb["existe"]:
            arb_txt = f"⚡ ¡SÍ! (+{arb['roi_pct']:.1f}% ROI)"
        else:
            arb_txt = f"NO ({arb['indice']:.4f})"

        print(
            f" {idx:<2} {p['horario']:<11} {p['partido']:<28} {c_txt:<18} {b_txt:<18} "
            f"{m_txt:<18} {con_txt:<23} {diff_txt:<24} {arb_txt}"
        )

    print(subbanner)
    con_caliente = sum(1 for p in partidos if p["caliente"]["L"] > 1.0)
    con_betway = sum(1 for p in partidos if p["betway"]["L"] > 1.0)
    aprobados = sum(1 for p in partidos if p["triaje"] == "APROBADO")
    arbitrajes = sum(1 for p in partidos if p["arbitraje"]["existe"])

    print(f"INTEGRIDAD: Caliente ({con_caliente}/{len(partidos)}) | Betway ({con_betway}/{len(partidos)}) | Triaje Aprobados: {aprobados} | Arbitrajes (+EV): {arbitrajes}")
    print(banner + "\n")


def main():
    parser = argparse.ArgumentParser(description="Centinela de Mercado Autónomo Q-BE Multi-Operador")
    parser.add_argument("--jornada", type=int, default=10, help="Jornada a escanear (default: 10)")
    parser.add_argument("--operador", choices=["caliente", "betway", "todos"], default="todos", help="Operador objetivo (caliente|betway|todos)")
    parser.add_argument("--loop", type=int, default=0)
    args = parser.parse_args()

    while True:
        t0 = time.perf_counter()
        logger.info(f"Iniciando escaneo multi-operador [{args.operador}] para Jornada {args.jornada}...")

        gateway = PersistenceGateway()
        with gateway.read_session() as session:
            fix_snap = session.query(FixtureSnapshot).filter(FixtureSnapshot.matchday == args.jornada).order_by(FixtureSnapshot.updated_at.desc()).first()

        if not fix_snap or not fix_snap.matches_json:
            logger.error(f"No hay partidos en SQLite para Jornada {args.jornada}. Corre primero centinela_deportivo.py.")
            return

        slate = [{"local": f["local"], "visitante": f["visitante"]} for f in fix_snap.matches_json]
        dict_cuotas = extraer_mercado_viva(slate, operador=args.operador)
        partidos_proc = actualizar_cuotas_en_sqlite(args.jornada, dict_cuotas, operador_sel=args.operador)

        t_total = time.perf_counter() - t0
        imprimir_tablero_mercado(partidos_proc, t_total, args.jornada, args.operador)

        if args.loop <= 0:
            break
        time.sleep(args.loop)


if __name__ == "__main__":
    main()
