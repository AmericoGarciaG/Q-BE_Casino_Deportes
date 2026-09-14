# -*- coding: utf-8 -*-
"""
Kybern Industrial — Instrumento 1: Simulador Forense de Observabilidad Cuantitativa
Base de Gobierno: Kybern Framework v12.0
Responsabilidad: Desglosar en consola las variables intermedias (λ, μ, 6x6, θ*, Edges, Kelly)
y exportar los payloads crudos con Bankroll y Momios para el Auditor Sombra LLM.
"""
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.storage.database import SessionLocal
from src.storage.models import League, StandingSnapshot, FixtureSnapshot
from src.pipeline.adapter import construir_master_table_snapshot, hidratar_partidos_cuantitativos
from src.pipeline.engine import QBEPipelineEngine

OUT_DIR = os.path.join(PROJECT_ROOT, "data", "output")
os.makedirs(OUT_DIR, exist_ok=True)

BANKROLL_BASE = 200.0
MODO_CARTERA = "BANKROLL"

def ejecutar_simulacion_forense():
    print("\n" + "="*90)
    print("🔬 [INSTRUMENTO 1] SIMULADOR FORENSE DE OBSERVABILIDAD CUANTITATIVA")
    print(f"💰 Bankroll Base: ${BANKROLL_BASE:.2f} MXN | Modo: {MODO_CARTERA}")
    print("="*90)

    db = SessionLocal()
    try:
        liga = db.query(League).filter((League.fotmob_id == 262) | (League.id == 262)).first()
        if not liga:
            print("❌ Liga MX no encontrada en SQLite.")
            return

        f_snap = db.query(FixtureSnapshot).filter(FixtureSnapshot.league_id == liga.id).order_by(FixtureSnapshot.updated_at.desc()).first()
        s_snap = db.query(StandingSnapshot).filter(StandingSnapshot.league_id == liga.id).order_by(StandingSnapshot.captured_at.desc()).first()

        if not f_snap or not s_snap:
            print("❌ Snapshots no encontrados en SQLite.")
            return

        # Filtrar partidos operables con cuotas reales
        operables = [f for f in f_snap.matches_json if f.get("disponible_para_seleccion") is True and f.get("estado") != "FINALIZADO"]
        print(f"📋 Partidos operables seleccionados para cálculo: {len(operables)}")

        master_table = construir_master_table_snapshot(s_snap.positions_json, jornada=8)
        raw_matches = hidratar_partidos_cuantitativos(operables, master_table, jornada=8)

        # ── 1. GENERAR PAYLOAD DE ENTRADA CRUDA (CON BANKROLL Y MOMIOS) ──────
        payload_entrada = {
            "metadata_control": {
                "torneo": "Liga MX - Apertura 2026",
                "jornada": 8,
                "timestamp_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "bankroll_disponible_mxn": BANKROLL_BASE,
                "modalidad_asignacion": MODO_CARTERA,
                "hard_cap_individual_pct": 8.0,
                "hard_cap_global_core_pct": 25.0,
                "total_partidos_evaluados": len(raw_matches)
            },
            "partidos_crudos": []
        }

        for idx, m in enumerate(raw_matches, 1):
            ident = m.identidad_partido
            ctx_fav = m.contexto_tabla_posiciones.favorito
            ctx_und = m.contexto_tabla_posiciones.underdog
            odds = m.momios.pago_anticipado

            item_crudo = {
                "id_partido": ident.id_partido,
                "partido": f"{ident.local} vs {ident.visitante}",
                "horario": ident.fecha_partido_evaluado,
                "favorito_designado": ident.favorito,
                "underdog_designado": ident.underdog,
                "momios_caliente_1x2": {
                    "L": odds.L,
                    "E": odds.E,
                    "V": odds.V,
                    "pago_anticipado_activo": odds.disponible
                },
                "estadisticas_favorito": {
                    "equipo": ident.favorito,
                    "posicion_tabla": ctx_fav.posicion_tabla,
                    "puntos": ctx_fav.puntos,
                    "pj": ctx_fav.pj_torneo,
                    "gf": ctx_fav.gf_torneo,
                    "gc": ctx_fav.gc_torneo,
                    "pts_por_partido": ctx_fav.pts_por_partido,
                    "sot": m.metricas_resumen_datos.fav_10p.sot,
                    "sota": m.metricas_resumen_datos.fav_10p.sota,
                    "xg_promedio": m.metricas_resumen_datos.fav_10p.xg_promedio,
                    "xga_promedio": m.metricas_resumen_datos.fav_10p.xga_promedio,
                    "q_mod": m.radar_cualitativo_entorno.favorito.q_mod_calculado
                },
                "estadisticas_underdog": {
                    "equipo": ident.underdog,
                    "posicion_tabla": ctx_und.posicion_tabla,
                    "puntos": ctx_und.puntos,
                    "pj": ctx_und.pj_torneo,
                    "gf": ctx_und.gf_torneo,
                    "gc": ctx_und.gc_torneo,
                    "pts_por_partido": ctx_und.pts_por_partido,
                    "sot": m.metricas_resumen_datos.und_10p.sot,
                    "sota": m.metricas_resumen_datos.und_10p.sota,
                    "xg_promedio": m.metricas_resumen_datos.und_10p.xg_promedio,
                    "xga_promedio": m.metricas_resumen_datos.und_10p.xga_promedio,
                    "q_mod": m.radar_cualitativo_entorno.underdog.q_mod_calculado
                },
                "antecedentes_h2h": {
                    "partidos_reales_encontrados": len(m.h2h_matches),
                    "politica": "ZERO_H2H_LAW" if len(m.h2h_matches) == 0 else "DECAY_EXPONENCIAL"
                }
            }
            payload_entrada["partidos_crudos"].append(item_crudo)

        path_entrada = os.path.join(OUT_DIR, "payload_entrada_calculos_j8.json")
        with open(path_entrada, "w", encoding="utf-8") as f:
            json.dump(payload_entrada, f, indent=2, ensure_ascii=False)
        print(f"📦 [PAYLOAD CRUDO] Guardado con Bankroll y Momios en: {path_entrada}")

        # ── 2. EJECUTAR MOTOR CUANTITATIVO E2E (POISSON, KELLY & DUTCHING) ────
        plan, consolidated = QBEPipelineEngine.run_full(
            matches=raw_matches,
            master_table=master_table,
            bankroll=BANKROLL_BASE,
            mode=MODO_CARTERA
        )

        path_traza = os.path.join(OUT_DIR, "traza_calculos_qbe_j8.json")
        with open(path_traza, "w", encoding="utf-8") as f:
            json.dump(consolidated, f, indent=2, ensure_ascii=False)
        print(f"📊 [TRAZA MOTOR Q-BE] Guardada con etapas intermedias en: {path_traza}")

        # ── 3. DESPLIEGUE EN CONSOLA CON MÁXIMA OBSERVABILIDAD ─────────────────
        print("\n" + "="*90)
        print("🧮 RADIOGRAFÍA DE OBSERVABILIDAD ETAPA POR ETAPA")
        print("="*90)

        for p in consolidated.get("partidos_analisis", []):
            print(f"\n⚽ PARTIDO: {p['partido']}")
            print(f"   • Momios Caliente: L @{p.get('odds_fav', p.get('odd_fav', 0)):.2f} | E @{p.get('odds_emp', p.get('odd_emp', 0)):.2f} | V @{p.get('odds_und', p.get('odd_und', 0)):.2f} | PA: ✅ Activo")
            print(f"   • Proyección Poisson 6x6: λ (Local) = {p['lambda_local']:.2f} | μ (Visita) = {p['mu_visita']:.2f} | Goles Totales = {p['xg_total']:.2f}")
            print(f"   • Probabilidades Reales Q-BE: Fav {p.get('prob_fav', 0):.1f}% | Emp {p.get('prob_emp', 0):.1f}% | Und {p.get('prob_und', 0):.1f}%")
            print(f"   • Derivadas de Ruina: Ψ_Ruina = {p.get('psi_downside', 0)*100:.2f}% | Φ_Lead2 (+2 goles) = {p.get('phi_lead2', 0)*100:.2f}%")
            print(f"   • Breakeven Analítico: θ*_Fav = {p.get('theta_req', 0):.2f}% | Edges 3-Vías: Fav {p['probabilidades_3vias'][0]['edge']:+.2f}% | Emp {p['probabilidades_3vias'][1]['edge']:+.2f}% | Und {p['probabilidades_3vias'][2]['edge']:+.2f}%")
            print(f"   • Estrategia Seleccionada: [{p.get('strategy_code', p.get('estrategia_codigo', 'QBE-??'))}] - {p.get('strategy_nombre', p.get('estrategia_nombre', '?'))}")

        print("\n" + "="*90)
        print(f"💰 RESUMEN GLOBAL: Inversión Total: ${consolidated['balance']['capital_total_comprometido_mxn']:.2f} MXN | EV: +${consolidated['balance']['ganancia_neta_esperada_jornada_mxn']:.2f} MXN | ROI: +{consolidated['balance']['roi_global_esperado_porcentaje']:.1f}%")
        print("="*90 + "\n")

    finally:
        db.close()

if __name__ == "__main__":
    ejecutar_simulacion_forense()
