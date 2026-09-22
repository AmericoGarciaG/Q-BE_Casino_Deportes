# -*- coding: utf-8 -*-
"""
🏆 Q-BE CD WEB — CENTINELA AUTÓNOMO DE MERCADO Y CUOTAS (CALIENTE.MX)
[SDLC-02: Standalone Background Engine — Market & Ledger Edition]
Base de Gobierno: Kybern Framework v12.0
"""

import sys
import os
import re
import time
import argparse
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy.orm.attributes import flag_modified
from src.storage.gateway import PersistenceGateway
from src.storage.models import League, FixtureSnapshot, SovereignDistribution
from src.ingestion.caliente_scraper import CalienteMarketScraper
from src.core.triage import evaluar_viabilidad_cuotas

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CentinelaMercado")


def extraer_mercado_viva(partidos_slate: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    logger.info(f"Escaneando Caliente.mx para {len(partidos_slate)} partidos del slate...")
    return CalienteMarketScraper.extraer_cuotas_focalizadas(partidos_slate)


def actualizar_cuotas_en_sqlite(jornada: int, cuotas_caliente: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    gateway = PersistenceGateway()
    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
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

        cuotas_map = {(c["local"], c["visitante"]): c for c in cuotas_caliente}
        matches_actualizados = []

        for fx_orig in fix_snap.matches_json:
            fx = dict(fx_orig)
            key = (fx["local"], fx["visitante"])
            c = cuotas_map.get(key)
            prev_momios = fx.get("momios")
            mid = fx.get("id_partido", "")

            # Consultar probabilidad soberana real de la BD
            dist_db = tx.query(SovereignDistribution).filter(SovereignDistribution.match_id == mid).first()
            p_soberana_l = dist_db.p_local if dist_db else 0.50

            if c and c.get("L") is not None:
                momio_l = float(c["L"])
                momio_e = float(c["E"])
                momio_v = float(c["V"])
                pa = bool(c.get("pago_anticipado", True))

                delta_l = round(momio_l - float(prev_momios["L"]), 2) if (prev_momios and prev_momios.get("L")) else 0.0
                overround = ((1.0 / momio_l) + (1.0 / momio_e) + (1.0 / momio_v) - 1.0) * 100.0

                viable, motivo = evaluar_viabilidad_cuotas(momio_l, momio_e, momio_v, pago_anticipado=pa)

                # Cálculo de GAP real (+EV) frente a probabilidad soberana
                prob_impl_l = 1.0 / momio_l
                gap_l = round((p_soberana_l - prob_impl_l) * 100.0, 1)

                momios_obj = {"L": momio_l, "E": momio_e, "V": momio_v, "pago_anticipado": pa}
                fx["momios"] = momios_obj
                fx["disponible_para_seleccion"] = True
                fx["es_operable"] = True
                fx["es_viable_triaje"] = viable
                fx["motivo_triaje"] = motivo

                partidos_procesados.append({
                    "partido": f"{fx['local']} vs {fx['visitante']}",
                    "horario": fx.get("horario", ""),
                    "L": momio_l, "E": momio_e, "V": momio_v,
                    "delta_L": delta_l,
                    "gap_L": gap_l,
                    "margen_casa": overround,
                    "pa": "SÍ" if pa else "NO",
                    "triaje": "APROBADO" if viable else "DESCARTADO",
                    "via_valor": motivo
                })
            else:
                partidos_procesados.append({
                    "partido": f"{fx['local']} vs {fx['visitante']}",
                    "horario": fx.get("horario", ""),
                    "L": 0.0, "E": 0.0, "V": 0.0, "delta_L": 0.0, "gap_L": 0.0,
                    "margen_casa": 0.0, "pa": "NO",
                    "triaje": "PENDIENTE", "via_valor": "Cuotas no publicadas"
                })

            matches_actualizados.append(fx)

        fix_snap.matches_json = matches_actualizados
        flag_modified(fix_snap, "matches_json")
        fix_snap.updated_at = ahora

    return partidos_procesados


def imprimir_tablero_mercado(partidos: List[Dict[str, Any]], duracion: float, jornada: int) -> None:
    banner = "=" * 135
    subbanner = "-" * 135

    print("\n" + banner)
    print(f"🏆 Q-BE CD WEB — CENTINELA DE MERCADO: MONITOR DE CUOTAS Y ARBITRAJE (JORNADA {jornada})")
    print(banner)
    print(f"TIEMPO DE ESCANEO: {duracion:.2f}s | OPERADOR: Caliente.mx | PERSISTENCIA: data/qbe_database.db (WAL Mode)")
    print(subbanner)
    print(f" #  {'HORARIO':<15} {'PARTIDO':<38} {'MOMIO L':<9} {'MOMIO E':<9} {'MOMIO V':<9} {'GAP (+EV)':<10} {'MARGEN':<8} {'PA':<4} {'TRIAJE':<11} {'VÍA DE VALOR'}")
    print(subbanner)

    for idx, p in enumerate(partidos, 1):
        delta_str = f"({p['delta_L']:+.2f})" if p['delta_L'] != 0.0 else ""
        momio_l_txt = f"{p['L']:.2f} {delta_str}".strip()
        gap_txt = f"{p.get('gap_L', 0.0):+.1f}%" if p['L'] > 0 else "—"
        print(
            f" {idx:<2} {p['horario']:<15} {p['partido']:<38} {momio_l_txt:<9} {p['E']:<9.2f} {p['V']:<9.2f} "
            f"{gap_txt:<10} {p['margen_casa']:<7.1f}% {p['pa']:<4} {p['triaje']:<11} {p['via_valor']}"
        )

    print(subbanner)
    con_momios = sum(1 for p in partidos if p["L"] > 1.0)
    aprobados = sum(1 for p in partidos if p["triaje"] == "APROBADO")
    print(f"INTEGRIDAD: {con_momios}/{len(partidos)} Cuotas Sincronizadas | {aprobados} Partidos con Ineficiencia Detectada (+EV)")
    print(banner + "\n")


def main():
    parser = argparse.ArgumentParser(description="Centinela de Mercado Autónomo Q-BE")
    parser.add_argument("--jornada", type=int, default=9)
    parser.add_argument("--loop", type=int, default=0)
    args = parser.parse_args()

    while True:
        t0 = time.perf_counter()
        logger.info(f"Iniciando escaneo de mercado para Jornada {args.jornada}...")

        gateway = PersistenceGateway()
        with gateway.read_session() as session:
            fix_snap = session.query(FixtureSnapshot).filter(FixtureSnapshot.matchday == args.jornada).order_by(FixtureSnapshot.updated_at.desc()).first()

        if not fix_snap or not fix_snap.matches_json:
            logger.error(f"No hay partidos en SQLite para Jornada {args.jornada}. Corre primero centinela_deportivo.py.")
            return

        slate = [{"local": f["local"], "visitante": f["visitante"]} for f in fix_snap.matches_json]
        cuotas = extraer_mercado_viva(slate)
        partidos_proc = actualizar_cuotas_en_sqlite(args.jornada, cuotas)

        t_total = time.perf_counter() - t0
        imprimir_tablero_mercado(partidos_proc, t_total, args.jornada)

        if args.loop <= 0:
            break
        time.sleep(args.loop)


if __name__ == "__main__":
    main()
