# Q-BE Casino Deportes — Pipeline Orchestrator Engine (src/pipeline/engine.py)
"""
Orquestador Determinista del Pipeline Q-BE con Telemetría de Diagnóstico y Generación Narrativa.
[LN-QBE-010 .. LN-QBE-090] [ARCH-PILLAR]
Orquesta el flujo determinista completo desde la sanidad de entrada hasta el ensamblado del payload consolidado.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from src.models.raw_input import RawMatchInput, MasterTableSnapshot
from src.models.decision import PortfolioExecutionPlan, PortfolioControl, PortfolioBalance, SatelliteModule
from src.models.consolidated import ConsolidatedPayload
from src.core.sanitizer import SanitizerEngine
from src.core.temporal import TemporalDecayEngine
from src.core.metrics import SyntheticMetricsEngine
from src.core.poisson import PoissonBivariateEngine
from src.core.breakeven import BreakevenEngine
from src.core.evaluator import StrategyEvaluatorEngine
from src.core.portfolio import PortfolioEngine
from src.core.auditor import ShieldAuditorEngine
from src.reporting.narrative import generar_tesis_partido, generar_justificacion_descarte

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}


def formatear_rango_fechas(fechas_str: list[str]) -> str:
    fechas_dt = []
    for f in fechas_str:
        if not f:
            continue
        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                fechas_dt.append(datetime.strptime(f.strip(), fmt))
                break
            except ValueError:
                pass
    if not fechas_dt:
        return "Fechas no especificadas"

    d_min = min(fechas_dt)
    d_max = max(fechas_dt)

    if d_min.year == d_max.year and d_min.month == d_max.month:
        if d_min.day == d_max.day:
            return f"{d_min.day} de {MESES_ES[d_min.month]} de {d_min.year}"
        return f"{d_min.day:02d} al {d_max.day:02d} de {MESES_ES[d_min.month]} de {d_min.year}"
    elif d_min.year == d_max.year:
        return f"{d_min.day:02d} de {MESES_ES[d_min.month]} al {d_max.day:02d} de {MESES_ES[d_max.month]} de {d_max.year}"
    return f"{d_min.strftime('%d/%m/%Y')} al {d_max.strftime('%d/%m/%Y')}"


def deducir_jornada(partidos: list, torneo_nombre: str = "") -> str:
    torneo_upper = torneo_nombre.upper()
    if any(k in torneo_upper for k in ["CUP", "LEAGUES", "COPA", "CHAMPIONS", "LIBERTADORES"]):
        for p in partidos:
            if isinstance(p, dict):
                fase = p.get("identidad_partido", {}).get("fase_torneo")
            else:
                ident = getattr(p, "identidad_partido", None)
                fase = getattr(ident, "fase_torneo", None) if ident else None
            if fase:
                return fase
        return "Fase de Grupos / Eliminatoria"

    for p in partidos:
        if isinstance(p, dict):
            j_exp = p.get("identidad_partido", {}).get("jornada_en_disputa")
        else:
            ident = getattr(p, "identidad_partido", None)
            j_exp = getattr(ident, "jornada_en_disputa", None) if ident else None
        if j_exp:
            return f"Jornada {j_exp}"

    for p in partidos:
        if isinstance(p, dict):
            ctx = p.get("contexto_tabla_posiciones", {})
            j_act = ctx.get("jornada_actual_torneo")
            if j_act:
                return f"Jornada {j_act + 1}"
            pj_fav = ctx.get("favorito", {}).get("pj") or ctx.get("favorito", {}).get("pj_torneo")
            if pj_fav:
                return f"Jornada {pj_fav + 1}"
        else:
            ctx = getattr(p, "contexto_tabla_posiciones", None)
            if ctx:
                j_act = getattr(ctx, "jornada_actual_torneo", None)
                if j_act:
                    return f"Jornada {j_act + 1}"
                fav = getattr(ctx, "favorito", None)
                if fav:
                    pj_fav = getattr(fav, "pj", None) or getattr(fav, "pj_torneo", None)
                    if pj_fav:
                        return f"Jornada {pj_fav + 1}"
    return "Jornada no especificada"


class QBEPipelineEngine:
    @classmethod
    def run(
        cls,
        matches: List[RawMatchInput],
        master_table: MasterTableSnapshot,
        bankroll: float = 200.0,
        mode: str = "BANKROLL"
    ) -> PortfolioExecutionPlan:
        plan, _ = cls.run_full(matches, master_table, bankroll, mode)
        return plan

    @classmethod
    def run_full(
        cls,
        matches: List[RawMatchInput],
        master_table: MasterTableSnapshot,
        bankroll: float = 200.0,
        mode: str = "BANKROLL",
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[PortfolioExecutionPlan, Dict[str, Any]]:
        approved_candidates = []
        discarded_candidates = []
        partidos_analisis_raw = []

        print("\n" + "─"*70)
        print(" 🔍 RADIOGRAFÍA ESTOCÁSTICA PARTIDO A PARTIDO ")
        print("─"*70)

        for m in matches:
            try:
                # 1. Sanitizer (Paso 0-C)
                SanitizerEngine.audit_and_sanitize(m, master_table)

                # 2. Temporal Decay H2H (LN-QBE-020)
                is_fav_l = (m.identidad_partido.local.strip().lower() == m.identidad_partido.favorito.strip().lower())
                h2h_matches = m.h2h_matches or m.h2h_ultimos_5_misma_liga
                h2h_res = TemporalDecayEngine.compute_decay(
                    h2h_matches,
                    m.identidad_partido.local,
                    m.identidad_partido.visitante,
                    m.identidad_partido.favorito
                )

                # 3. Metrics FCF / E_att (LN-QBE-030)
                fav_10p = m.metricas_resumen_datos.fav_10p
                und_10p = m.metricas_resumen_datos.und_10p
                if is_fav_l:
                    m_res = SyntheticMetricsEngine.compute_all(
                        fav_10p.promedio_poss, fav_10p.promedio_sot, fav_10p.promedio_sota, fav_10p.promedio_gf,
                        und_10p.promedio_poss, und_10p.promedio_sot, und_10p.promedio_sota, und_10p.promedio_gf
                    )
                    gf_loc, gf_vis = fav_10p.promedio_gf, und_10p.promedio_gf
                    pts_loc = m.contexto_tabla_posiciones.favorito.pts_por_partido
                    pts_vis = m.contexto_tabla_posiciones.underdog.pts_por_partido
                    q_loc = m.radar_cualitativo_entorno.favorito.q_mod_calculado
                    q_vis = m.radar_cualitativo_entorno.underdog.q_mod_calculado
                else:
                    m_res = SyntheticMetricsEngine.compute_all(
                        und_10p.promedio_poss, und_10p.promedio_sot, und_10p.promedio_sota, und_10p.promedio_gf,
                        fav_10p.promedio_poss, fav_10p.promedio_sot, fav_10p.promedio_sota, fav_10p.promedio_gf
                    )
                    gf_loc, gf_vis = und_10p.promedio_gf, fav_10p.promedio_gf
                    pts_loc = m.contexto_tabla_posiciones.underdog.pts_por_partido
                    pts_vis = m.contexto_tabla_posiciones.favorito.pts_por_partido
                    q_loc = m.radar_cualitativo_entorno.underdog.q_mod_calculado
                    q_vis = m.radar_cualitativo_entorno.favorito.q_mod_calculado

                # 4. Poisson con Opta xG modulation (LN-QBE-040)
                o_l = m.momios.pago_anticipado.L
                o_e = m.momios.pago_anticipado.E
                o_v = m.momios.pago_anticipado.V
                o_fav = o_l if is_fav_l else o_v
                o_und = o_v if is_fav_l else o_l

                loc_xg = getattr(fav_10p, "xg_promedio", None) if is_fav_l else getattr(und_10p, "xg_promedio", None)
                vis_xga = getattr(und_10p, "xga_promedio", None) if is_fav_l else getattr(fav_10p, "xga_promedio", None)
                vis_xg = getattr(und_10p, "xg_promedio", None) if is_fav_l else getattr(fav_10p, "xg_promedio", None)
                loc_xga = getattr(fav_10p, "xga_promedio", None) if is_fav_l else getattr(und_10p, "xga_promedio", None)
                loc_gc = getattr(fav_10p, "promedio_gc", 1.0) if is_fav_l else getattr(und_10p, "promedio_gc", 1.0)
                vis_gc = getattr(und_10p, "promedio_gc", 1.0) if is_fav_l else getattr(fav_10p, "promedio_gc", 1.0)

                p_res = PoissonBivariateEngine.compute_modulations(
                    h2h=h2h_res, metrics=m_res, gf_local_10p=gf_loc, gf_vis_10p=gf_vis,
                    pts_pj_local=pts_loc, pts_pj_vis=pts_vis,
                    jornada_tabla=m.contexto_tabla_posiciones.jornada_actual_torneo,
                    q_mod_local=q_loc, q_mod_vis=q_vis, is_fav_local=is_fav_l,
                    odd_fav=o_fav, odd_emp=o_e, odd_und=o_und,
                    pago_anticipado_activo=m.momios.pago_anticipado.disponible,
                    local_xg=loc_xg, vis_xga=vis_xga, vis_xg=vis_xg, local_xga=loc_xga,
                    local_gc_10p=loc_gc, vis_gc_10p=vis_gc
                )

                # 5. Breakeven (LN-QBE-050)
                bk_res = BreakevenEngine.compute_thresholds(
                    odd_fav=o_fav, odd_emp=o_e, odd_und=o_und,
                    psi_ruina=p_res.psi_ruina, phi_lead2=p_res.phi_lead2,
                    p_hib_fav=p_res.prob_hibrida_fav
                )

                fav_ctx = m.contexto_tabla_posiciones.favorito if m.contexto_tabla_posiciones else None
                und_ctx = m.contexto_tabla_posiciones.underdog if m.contexto_tabla_posiciones else None
                gc_fav_calc = 1.0
                if fav_ctx and fav_ctx.gc_torneo and fav_ctx.pj_torneo:
                    gc_fav_calc = fav_ctx.gc_torneo / max(1, fav_ctx.pj_torneo)

                # 6. Evaluator (LN-QBE-060)
                evals = StrategyEvaluatorEngine.evaluate_all(
                    p_fav=p_res.prob_hibrida_fav, p_emp=p_res.prob_hibrida_empate, p_und=p_res.prob_hibrida_und,
                    o_fav=o_fav, o_emp=o_e, o_und=o_und,
                    theta_fav_h1=bk_res.theta_fav_h1, theta_emp_h2=bk_res.theta_emp_h2,
                    theta_emp_pa_h2_plus=bk_res.theta_emp_pa_h2_plus, theta_und_r1=bk_res.theta_und_r1,
                    momio_sintetico_x2=bk_res.momio_sintetico_x2, phi_lead2=p_res.phi_lead2,
                    psi_ruina=p_res.psi_ruina, d_mkt=p_res.d_mkt,
                    pago_anticipado=m.momios.pago_anticipado.disponible,
                    pts_pj_fav=fav_ctx.pts_por_partido if fav_ctx else 1.35,
                    gc_10p_fav=gc_fav_calc,
                    q_mod_fav=m.radar_cualitativo_entorno.favorito.q_mod_calculado if m.radar_cualitativo_entorno else 1.0,
                    h2h_x2_prob=(h2h_res.p_emp + h2h_res.p_und)
                )

                code, nombre, ev_net, promo = PortfolioEngine.select_best_strategy(
                    evals, p_res.psi_ruina, m.momios.pago_anticipado.disponible, p_fav=p_res.prob_hibrida_fav
                )

                # Telemetría en Consola
                print(f"⚽ {m.identidad_partido.local} vs {m.identidad_partido.visitante} (Cuotas: {o_l:.2f} / {o_e:.2f} / {o_v:.2f})")
                print(f"   xG: {p_res.lambda_local:.2f} vs {p_res.mu_visitante:.2f} | Goles Totales: {p_res.goles_esperados_totales:.2f}")
                print(f"   Probabilidades: Fav {p_res.prob_hibrida_fav*100:.1f}% | Emp {p_res.prob_hibrida_empate*100:.1f}% | Und {p_res.prob_hibrida_und*100:.1f}%")
                print(f"   Edges: Fav {p_res.edge_fav*100:+.2f}% | Emp {p_res.edge_empate*100:+.2f}% | Und {p_res.edge_und*100:+.2f}%")
                print(f"   Decisión ➔ [{code}] {nombre} (EV: {ev_net:+.2f}%)")

                h2h_filas_list = []
                if h2h_matches:
                    for h in h2h_matches:
                        h2h_filas_list.append({
                            "fecha": getattr(h, "fecha", "N/A") or "N/A",
                            "marcador": getattr(h, "marcador", "N/A") or "N/A",
                            "local_real": getattr(h, "local_real", "N/A") or "N/A",
                            "visitante_real": getattr(h, "visitante_real", "N/A") or "N/A"
                        })

                match_info_full = {
                    "id_partido": m.identidad_partido.id_partido,
                    "partido": f"{m.identidad_partido.local} vs. {m.identidad_partido.visitante}",
                    "partido_nombre": f"{m.identidad_partido.local} vs {m.identidad_partido.visitante}",
                    "horario": m.identidad_partido.fecha_partido_evaluado,
                    "local": m.identidad_partido.local,
                    "visitante": m.identidad_partido.visitante,
                    "fav_name": m.identidad_partido.favorito,
                    "und_name": m.identidad_partido.underdog,
                    "is_fav_local": is_fav_l,
                    "strategy_code": code,
                    "strategy_nombre": nombre,
                    "estrategia_codigo": code,
                    "estrategia_nombre": nombre,
                    "ev_neto_roi": ev_net,
                    "psi_downside": p_res.psi_ruina,
                    "phi_lead2": p_res.phi_lead2,
                    "phi_lead2_pct": p_res.phi_lead2 * 100.0,
                    "odd_fav": o_fav,
                    "odd_emp": o_e,
                    "odd_und": o_und,
                    "odds_fav": o_fav,
                    "odds_emp": o_e,
                    "odds_und": o_und,
                    "prob_fav": p_res.prob_hibrida_fav * 100.0,
                    "prob_emp": p_res.prob_hibrida_empate * 100.0,
                    "prob_und": p_res.prob_hibrida_und * 100.0,
                    "prob_impl_fav": (1.0 / o_fav) * 100.0 if o_fav > 0 else 0.0,
                    "fav_pos": fav_ctx.posicion_tabla if fav_ctx else 1,
                    "fav_pts": fav_ctx.puntos if fav_ctx else 0,
                    "und_pos": und_ctx.posicion_tabla if und_ctx else 18,
                    "und_pts": und_ctx.puntos if und_ctx else 0,
                    "pts_pj_fav": fav_ctx.pts_por_partido if fav_ctx else 1.35,
                    "pts_pj_und": und_ctx.pts_por_partido if und_ctx else 1.00,
                    "gf_fav": fav_10p.promedio_gf,
                    "gc_fav": gc_fav_calc,
                    "gf_und": und_10p.promedio_gf,
                    "sot_und": und_10p.promedio_sot,
                    "h2h_x2_pct": (h2h_res.p_emp + h2h_res.p_und) * 100.0,
                    "q_mod_fav": q_loc if is_fav_l else q_vis,
                    "q_mod_und": q_vis if is_fav_l else q_loc,
                    "lambda_local": p_res.lambda_local,
                    "mu_visita": p_res.mu_visitante,
                    "xg_local": p_res.lambda_local,
                    "xg_visita": p_res.mu_visitante,
                    "xg_total": p_res.goles_esperados_totales,
                    "fcf_local": m_res.fcf_local,
                    "e_att_local": m_res.e_att_local,
                    "fcf_visita": m_res.fcf_vis,
                    "e_att_visita": m_res.e_att_vis,
                    "theta_req": bk_res.theta_fav_h1 * 100.0,
                    "probabilidades_3vias": [
                        {
                            "resultado": f"Victoria {m.identidad_partido.local} ({'Fav' if is_fav_l else 'No-Fav'})",
                            "prob_real": (p_res.prob_hibrida_fav if is_fav_l else p_res.prob_hibrida_und) * 100.0,
                            "prob_casino": (1.0 / o_l) * 100.0 if o_l > 0 else 0.0,
                            "edge": (p_res.edge_fav if is_fav_l else p_res.edge_und) * 100.0,
                            "momio": o_l
                        },
                        {
                            "resultado": "Empate",
                            "prob_real": p_res.prob_hibrida_empate * 100.0,
                            "prob_casino": (1.0 / o_e) * 100.0 if o_e > 0 else 0.0,
                            "edge": p_res.edge_empate * 100.0,
                            "momio": o_e
                        },
                        {
                            "resultado": f"Victoria {m.identidad_partido.visitante} ({'No-Fav' if is_fav_l else 'Fav'})",
                            "prob_real": (p_res.prob_hibrida_und if is_fav_l else p_res.prob_hibrida_fav) * 100.0,
                            "prob_casino": (1.0 / o_v) * 100.0 if o_v > 0 else 0.0,
                            "edge": (p_res.edge_und if is_fav_l else p_res.edge_fav) * 100.0,
                            "momio": o_v
                        }
                    ],
                    "tabla_10p": [
                        {
                            "equipo": m.identidad_partido.local,
                            "puesto": (fav_ctx.posicion_tabla if is_fav_l else und_ctx.posicion_tabla) if (fav_ctx and und_ctx) else 1,
                            "pts": (fav_ctx.puntos if is_fav_l else und_ctx.puntos) if (fav_ctx and und_ctx) else 0,
                            "gf_gc": f"{(fav_ctx.gf_torneo if is_fav_l else und_ctx.gf_torneo) if (fav_ctx and und_ctx) else 0}/{(fav_ctx.gc_torneo if is_fav_l else und_ctx.gc_torneo) if (fav_ctx and und_ctx) else 0}",
                            "pts_pj": (fav_ctx.pts_por_partido if is_fav_l else und_ctx.pts_por_partido) if (fav_ctx and und_ctx) else 1.0,
                            "goles_pro": f"{gf_loc:.2f} / 1.00",
                            "sot": (fav_10p.promedio_sot if is_fav_l else und_10p.promedio_sot),
                            "sota": (fav_10p.promedio_sota if is_fav_l else und_10p.promedio_sota),
                            "posesion": (fav_10p.promedio_poss if is_fav_l else und_10p.promedio_poss),
                            "bajas": getattr(m.radar_cualitativo_entorno.favorito if is_fav_l else m.radar_cualitativo_entorno.underdog, "descripcion_impacto_bajas", "Sin reporte crítico") or "Sin reporte crítico",
                            "qmod": q_loc
                        },
                        {
                            "equipo": m.identidad_partido.visitante,
                            "puesto": (und_ctx.posicion_tabla if is_fav_l else fav_ctx.posicion_tabla) if (fav_ctx and und_ctx) else 18,
                            "pts": (und_ctx.puntos if is_fav_l else fav_ctx.puntos) if (fav_ctx and und_ctx) else 0,
                            "gf_gc": f"{(und_ctx.gf_torneo if is_fav_l else fav_ctx.gf_torneo) if (fav_ctx and und_ctx) else 0}/{(und_ctx.gc_torneo if is_fav_l else fav_ctx.gc_torneo) if (fav_ctx and und_ctx) else 0}",
                            "pts_pj": (und_ctx.pts_por_partido if is_fav_l else fav_ctx.pts_por_partido) if (fav_ctx and und_ctx) else 1.0,
                            "goles_pro": f"{gf_vis:.2f} / 1.00",
                            "sot": (und_10p.promedio_sot if is_fav_l else fav_10p.promedio_sot),
                            "sota": (und_10p.promedio_sota if is_fav_l else fav_10p.promedio_sota),
                            "posesion": (und_10p.promedio_poss if is_fav_l else fav_10p.promedio_poss),
                            "bajas": getattr(m.radar_cualitativo_entorno.underdog if is_fav_l else m.radar_cualitativo_entorno.favorito, "descripcion_impacto_bajas", "Sin reporte crítico") or "Sin reporte crítico",
                            "qmod": q_vis
                        }
                    ],
                    "h2h_filas": h2h_filas_list
                }

                if code != "QBE-00":
                    approved_candidates.append(match_info_full)
                    partidos_analisis_raw.append(match_info_full)
                else:
                    motivo = evals["QBE_00"]["motivo_diagnostico"]
                    d_item = {
                        "id_partido": m.identidad_partido.id_partido,
                        "partido": f"{m.identidad_partido.local} vs {m.identidad_partido.visitante}",
                        "motivo": motivo,
                        "motivo_titulo": "QBE-00",
                        "motivo_codigo": "QBE-00",
                        "momios": {"L": o_l, "E": o_e, "V": o_v}
                    }
                    d_item["explicacion_didactica"] = generar_justificacion_descarte(d_item)
                    discarded_candidates.append(d_item)
                    print(f"   ⚠️ VETADO: {motivo}")

            except Exception as e:
                partido_nombre = getattr(getattr(m, "identidad_partido", None), "local", "Local") + " vs " + getattr(getattr(m, "identidad_partido", None), "visitante", "Visita")
                d_item_error = {
                    "id_partido": getattr(getattr(m, "identidad_partido", None), "id_partido", "ID_ERR"),
                    "partido": partido_nombre,
                    "motivo": f"Veto por Cuarentena de Datos: {e}",
                    "motivo_titulo": "QBE-00",
                    "motivo_codigo": "CUARENTENA_DATOS",
                    "momios": {"L": 0.0, "E": 0.0, "V": 0.0},
                    "explicacion_didactica": f"El partido {partido_nombre} fue puesto en cuarentena preventiva debido a inconsistencias fácticas en sus antecedentes: {e}. Capital protegido al 100%."
                }
                discarded_candidates.append(d_item_error)
                print(f"   ⚠️ VETADO A CUARENTENA: {partido_nombre} ({e})")
            print("─"*70)

        # Síntesis dinámica de metadatos (LN-QBE-013)
        fechas_partidos = [
            (p.get("identidad_partido", {}).get("fecha_partido_evaluado", "") if isinstance(p, dict) else getattr(getattr(p, "identidad_partido", None), "fecha_partido_evaluado", ""))
            for p in matches
        ]
        torneo_nombre = "Liga MX - Torneo Apertura 2026"
        if matches:
            first_p = matches[0]
            if isinstance(first_p, dict):
                torneo_nombre = first_p.get("identidad_partido", {}).get("liga_torneo", torneo_nombre)
            else:
                ident = getattr(first_p, "identidad_partido", None)
                if ident and hasattr(ident, "liga_torneo") and getattr(ident, "liga_torneo", None):
                    torneo_nombre = getattr(ident, "liga_torneo")
        if torneo_nombre:
            torneo_nombre = torneo_nombre.replace("/", "-")

        _jornada_val = deducir_jornada(matches, torneo_nombre)
        _fechas_val = formatear_rango_fechas(fechas_partidos)
        _fecha_proc = datetime.now().strftime("%d-%m-%Y %H:%M hrs")

        dynamic_metadata = {
            "torneo": torneo_nombre,
            "torneo_display": torneo_nombre,
            "jornada": _jornada_val,
            "jornada_display": _jornada_val,
            "fechas": _fechas_val,
            "fecha_procesamiento": _fecha_proc
        }

        # Si no hay aprobados, emitir plan de preservación total ($0 arriesgado)
        if not approved_candidates:
            print("\n🛡️ AVISO: Ningún partido superó los filtros de ventaja matemática (+EV).")
            print("   Capital preservado al 100% ($0.00 en riesgo).")
            empty_plan = PortfolioExecutionPlan(
                control_portafolio=PortfolioControl(
                    modalidad="BANKROLL", total_partidos_core_aprobados=0,
                    capital_total_core_mxn=0.0, probabilidad_ruina_total_porcentaje=0.0,
                    blindaje_global_preservacion_porcentaje=100.0,
                    desglose_vaquita={"activa": False},
                    desglose_bankroll={"activa": True, "bankroll_total": bankroll, "porcentaje_total_arriesgado": 0.0}
                ),
                ordenes_ejecucion_partidos=[],
                modulo_satelite_asimetrico=SatelliteModule(autorizado=False, justificacion_financiamiento="Sin operaciones Core."),
                balance_global_portafolio=PortfolioBalance(capital_total_comprometido_mxn=0.0, ganancia_neta_esperada_jornada_mxn=0.0, roi_global_esperado_porcentaje=0.0)
            )
            empty_meta = metadata or dynamic_metadata
            if "fecha_procesamiento" not in empty_meta or not empty_meta["fecha_procesamiento"]:
                empty_meta["fecha_procesamiento"] = datetime.now().strftime("%d-%m-%Y %H:%M hrs")

            empty_control = empty_plan.control_portafolio.model_dump()
            total_evaluados = len(matches)
            empty_control["total_partidos_escaneados"] = total_evaluados
            empty_control["total_partidos_core_aprobados"] = 0
            empty_control["partidos_core"] = f"0 / {total_evaluados}"
            empty_control["partidos_core_sub"] = f"0 de {total_evaluados} con valor (+EV)"

            _pos_list_empty = []
            if master_table and hasattr(master_table, "posiciones") and master_table.posiciones:
                _pos_list_empty = [p.model_dump() if hasattr(p, "model_dump") else p for p in master_table.posiciones]

            empty_payload = {
                "metadata": empty_meta,
                "control": empty_control,
                "balance": empty_plan.balance_global_portafolio.model_dump(),
                "ordenes": [],
                "satelite": empty_plan.modulo_satelite_asimetrico.model_dump(),
                "partidos_analisis": [],
                "descartes": discarded_candidates,
                "tabla_posiciones_completa": _pos_list_empty,
                "cartelera_completa": []
            }
            return empty_plan, empty_payload

        # 7. Portfolio Engine (LN-QBE-070)
        portfolio_plan = PortfolioEngine.build_plan(approved_candidates, bankroll, mode)

        # 8. Shield Audit (LN-QBE-090)
        is_valid, audit_logs = ShieldAuditorEngine.audit(portfolio_plan.model_dump(), bankroll)
        if not is_valid:
            raise RuntimeError(f"Shield Release Gate BLOQUEADO:\n" + "\n".join(audit_logs))

        # 9. Ensamblado del Payload Consolidado con Generador Narrativo
        plan_dict = portfolio_plan.model_dump()
        ordenes_dict = plan_dict.get("ordenes_ejecucion_partidos", [])

        ordenes_map = {o["id_partido"]: o for o in ordenes_dict}
        for p_analisis in partidos_analisis_raw:
            id_p = p_analisis["id_partido"]
            orden_correspondiente = ordenes_map.get(id_p, {})
            tesis_text = generar_tesis_partido(orden_correspondiente, p_analisis)
            p_analisis["tesis_didactica"] = tesis_text
            p_analisis["interpretacion_didactica"] = tesis_text

        final_meta = metadata or dynamic_metadata
        if "fecha_procesamiento" not in final_meta or not final_meta["fecha_procesamiento"]:
            final_meta["fecha_procesamiento"] = datetime.now().strftime("%d-%m-%Y %H:%M hrs")

        control_dict = plan_dict.get("control_portafolio", {})
        total_evaluados = len(matches)
        total_aprobados = len(ordenes_dict)
        control_dict["total_partidos_escaneados"] = total_evaluados
        control_dict["total_partidos_core_aprobados"] = total_aprobados
        control_dict["total_posiciones_core_label"] = f"{total_aprobados} Posición Core" if total_aprobados == 1 else f"{total_aprobados} Posiciones Core"
        control_dict["partidos_core"] = f"{total_aprobados} / {total_evaluados}"
        control_dict["partidos_core_sub"] = f"{total_aprobados} de {total_evaluados} con valor (+EV)"

        _pos_list = []
        if master_table and hasattr(master_table, "posiciones") and master_table.posiciones:
            _pos_list = [p.model_dump() if hasattr(p, "model_dump") else p for p in master_table.posiciones]

        _cartelera_all = partidos_analisis_raw + discarded_candidates

        consolidated_dict = {
            "metadata": final_meta,
            "control": control_dict,
            "balance": plan_dict.get("balance_global_portafolio", {}),
            "ordenes": ordenes_dict,
            "satelite": plan_dict.get("modulo_satelite_asimetrico", {}),
            "partidos_analisis": partidos_analisis_raw,
            "descartes": discarded_candidates,
            "tabla_posiciones_completa": _pos_list,
            "cartelera_completa": _cartelera_all
        }
        if _pos_list:
            consolidated_dict["standings_raw"] = {
                "jornada_concluida": getattr(master_table, "jornada_concluida", 7),
                "posiciones": _pos_list
            }

        return portfolio_plan, consolidated_dict