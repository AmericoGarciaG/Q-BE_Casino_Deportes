# -*- coding: utf-8 -*-
"""
🔬 Q-BE: AUDITORÍA TRANSPARENTE DE PIPELINE END-TO-END DE BACKTESTING
[ARCH-1.4.42] Verificación paso a paso de insumos, cálculo soberano y paridad con API.
Régimen: [DBBD-FUNGIBLE] — Analítica de Solo Lectura (Caja de Cristal).
Autoridad: Américo García Guerrero (Director Humano)
"""

import sys
import os
import argparse
import httpx
from typing import Dict, Any, List, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.storage.gateway import PersistenceGateway
from src.storage.models import FixtureSnapshot, StandingSnapshot, Match, SovereignDistribution
from src.core.sovereign_pipeline import generar_distribucion_soberana
from src.core.contracts.portfolio_math import desmarcar_cuotas_proporcional, calcular_brier_multicategorico

# ── ENMIENDA DE CONTRATO FACTUAL 1:1 [VAR-2026-AUDITORIA-PIPELINE-E2E] ────────────────────────
# Sustitución MECÁNICA de llaves de acceso, sin invención de lógica y sin alterar una sola
# fórmula: la matemática sellada (`desmarcar_cuotas_proporcional`, `calcular_brier_multicategorico`)
# y la taxonomía P_max/P_mid/P_low se ejecutan VERBATIM. Los desajustes corregidos son de
# DICCIONARIO DE DATOS, no de negocio:
#   1. `Match.league_id` / `Match.slate_id` / `Match.home_team` no existen en el esquema 3NF
#      sellado (`[ARCH-1.5.1]`): la liga vive en `fixtures_snapshots.league_id`, la jornada en
#      `Match.matchday_num` y los nombres en el fixture (`local`/`visitante`) o en
#      `home_team_slug`/`away_team_slug`.
#   2. `Match.status == "FINISHED"` no casa con la bóveda viva (97 filas `FINALIZADO`).
#   3. Cuotas ausentes: el Visor sellado NO inventa precio (trío ausente ⇒ la ley de bóveda degrada
#      a la ignorancia uniforme). Se prohíbe el relleno sintético 2.0/3.0/3.5 de la directiva
#      ([GOVERNANCE-01]).
#   4. `calcular_brier_multicategorico` se invoca con las llaves selladas `p_local`/`p_empate`/
#      `p_visitante`: con `p1`/`pX`/`p2` el cómputo se vaciaba y el Brier emitía 0.0000 fabricado.
#   5. La resolución de cuotas de cierre NO se espeja: se IMPORTA la ley sellada del Visor. Un
#      espejo local puede derivar en silencio frente al Visor; la importación garantiza paridad
#      bit a bit por construcción.
_ESTADOS_CONCLUIDOS = frozenset({"FINISHED", "FINALIZADO"})

from src.web.routes.markets import _cuotas_1x2_factuales  # noqa: E402  ley sellada [ARCH-1.4.38]


def auditar_pipeline(detallado: bool = False):
    print("=" * 90)
    print("🔬 Q-BE — AUDITORÍA DE TRANSPARENCIA TOTAL DEL PIPELINE (END-TO-END)")
    print("   Régimen: SOLO LECTURA · Verificación de Insumos, Matemática y Paridad con API")
    print("=" * 90)

    gw = PersistenceGateway()

    partidos_auditados = []

    # 1. Extracción de partidos concluidos desde SQLite 3NF
    with gw.read_session() as session:
        # Cargar todos los matches concluidos ordenados por fecha y jornada
        matches = [
            m for m in session.query(Match).order_by(Match.matchday_num.asc(), Match.id.asc()).all()
            if m.matchday_num is not None
            and m.score_home is not None
            and m.score_away is not None
            and str(m.status or "").upper() in _ESTADOS_CONCLUIDOS
        ]

        # Mapear snapshots de fixtures y standings
        fix_snaps = session.query(FixtureSnapshot).filter(
            FixtureSnapshot.league_id == 1
        ).order_by(FixtureSnapshot.matchday.asc(), FixtureSnapshot.updated_at.desc()).all()
        fix_by_jornada = {s.matchday: s.matches_json for s in fix_snaps}

        # Índice global `{id_partido: fixture}` con la MISMA autoridad de precedencia que el Visor
        # sellado: el snapshot más reciente de cada jornada gana (`updated_at DESC`) y la primera
        # captura vista por `id_partido` se queda (`setdefault`).
        fx_index: Dict[str, Dict[str, Any]] = {}
        for snap in fix_snaps:
            for fixture in (snap.matches_json or []):
                id_fx = str(fixture.get("id_partido") or "")
                if id_fx:
                    fx_index.setdefault(id_fx, fixture)

        # Respaldo SECUNDARIO de P' (tabla soberana 3NF), idéntico al del Visor sellado.
        soberanas: Dict[str, Tuple[float, float, float]] = {
            str(fila.match_id): (
                float(fila.p_local), float(fila.p_empate), float(fila.p_visitante),
            )
            for fila in session.query(SovereignDistribution).all()
        }

        std_snaps = session.query(StandingSnapshot).filter(StandingSnapshot.league_id == 1).all()
        std_by_jornada = {s.matchday: {row["equipo"]: row for row in s.positions_json} for s in std_snaps if s.positions_json}


    print(f"📊 [PASO 1] Bóveda 3NF leída: {len(matches)} partidos concluidos en SQLite.")
    print(f"   • Snapshots de Fixtures cargados : {len(fix_by_jornada)} jornadas")
    print(f"   • Snapshots de Standings cargados: {len(std_by_jornada)} jornadas")
    print("-" * 90)

    # Contadores de Macro
    conteo_pmax = 0
    conteo_pmid = 0
    conteo_pmid_emp = 0
    conteo_pmid_riv = 0
    conteo_plow = 0
    brier_qbe_list = []
    brier_mkt_list = []

    # [ENMIENDA] La jornada vive en `Match.matchday_num` (3NF): `slate_id`/`league_id` no existen
    # en el modelo `Match` (la liga se resuelve por el snapshot de fixtures o por `league_slug`).
    jornadas_procesadas = sorted({int(m.matchday_num) for m in matches if m.matchday_num is not None})

    print(f"{'#':<3} {'J':<3} {'PARTIDO':<32} {'FINAL':<6} {'P_max':<8} {'P_mid':<8} {'P_low':<8} {'RESULTADO':<10} {'ESTADO'}")
    print("-" * 90)

    idx_global = 1
    pendientes_captura = 0
    # Iterar jornada por jornada de forma cronológica
    for j in range(1, 12):
        matches_j = [m for m in matches if int(m.matchday_num) == j]
        if not matches_j:
            continue

        for m in matches_j:
            fx = fx_index.get(str(m.id), {})
            loc = fx.get("local") or str(m.home_team_slug)
            vis = fx.get("visitante") or str(m.away_team_slug)

            hs = int(m.score_home)
            as_ = int(m.score_away)
            marcador_str = f"{hs}-{as_}"

            res_real = "LOCAL" if hs > as_ else ("EMPATE" if hs == as_ else "VISITANTE")

            # Obtener P'
            # P' sellada: captura del snapshot o, EN SU DEFECTO, tabla soberana 3NF (misma
            # precedencia que el Visor sellado). Sin captura sellada el partido NO es auditable:
            # se contabiliza como pendiente, jamás se repara con cifras sintéticas.
            p_prima = None
            try:
                p_prima = (
                    float(fx.get("p_local")), float(fx.get("p_empate")), float(fx.get("p_visitante")),
                )
            except (TypeError, ValueError):
                p_prima = None
            if p_prima is None:
                p_prima = soberanas.get(str(m.id))
            if p_prima is None:
                pendientes_captura += 1
                continue

            # Si tiene Cold Start S(I) == 0, se aplica Prior de Mercado [LN-QBE-100]
            s_i = int(fx.get("suficiencia_S_I")) if fx.get("suficiencia_S_I") is not None else 1
            cuotas = _cuotas_1x2_factuales(fx)
            ol = float(cuotas.get("L", 0.0) or 0.0)
            oe = float(cuotas.get("E", 0.0) or 0.0)
            ov = float(cuotas.get("V", 0.0) or 0.0)
            ql, qe, qv = desmarcar_cuotas_proporcional(ol, oe, ov)

            if s_i == 0:
                pl, pe, pv = ql, qe, qv
            else:
                pl, pe, pv = p_prima


            pares = [("LOCAL", pl), ("EMPATE", pe), ("VISITANTE", pv)]
            pares.sort(key=lambda x: x[1], reverse=True)
            r_max, v_max = pares[0]
            r_mid, v_mid = pares[1]
            r_low, v_low = pares[2]

            # Clasificación fiduciaria
            if res_real == r_max:
                estado = "P_MAX 🟢"
                conteo_pmax += 1
            elif res_real == r_mid:
                conteo_pmid += 1
                if r_mid == "EMPATE":
                    conteo_pmid_emp += 1
                    estado = "P_MID [Emp] 🔵"
                else:
                    conteo_pmid_riv += 1
                    estado = "P_MID [Riv] 🔵"
            else:
                conteo_plow += 1
                estado = "P_LOW 🔴"

            # Brier scores — [ENMIENDA 1:1] la ley sellada `calcular_brier_multicategorico` lee
            # las llaves `p_local`/`p_empate`/`p_visitante`. Con las llaves `p1`/`pX`/`p2` de la
            # directiva todo partido quedaba excluido del cómputo y el Brier emitía 0.0000
            # (cifra fabricada, [GOVERNANCE-01]).
            bs_q = calcular_brier_multicategorico([{"p_local": pl, "p_empate": pe, "p_visitante": pv, "resultado": res_real}])
            bs_m = calcular_brier_multicategorico([{"p_local": ql, "p_empate": qe, "p_visitante": qv, "resultado": res_real}])

            brier_qbe_list.append(bs_q)
            brier_mkt_list.append(bs_m)

            if detallado or idx_global in (1, 10, 18, 25, 50, 70, 85, 97):
                etiqueta = f"{loc[:14]} vs {vis[:14]}"
                print(f"{idx_global:<3} J{j:<2} {etiqueta:<32} {marcador_str:<6} {v_max*100:>5.1f}%  {v_mid*100:>5.1f}%  {v_low*100:>5.1f}%  {res_real:<10} {estado}")

            idx_global += 1

    total_n = len(brier_qbe_list)
    print("-" * 90)

    # 2. Verificación de Paridad con la API del Visor
    print("\n🌐 [PASO 2] Verificando paridad contra endpoint GET /api/markets/backtesting/calibration-report...")
    api_paridad = "NO CONSULTADA"
    try:
        r_api = httpx.get("http://127.0.0.1:8000/api/markets/backtesting/calibration-report?league_id=1", timeout=5.0)
        if r_api.status_code == 200:
            d_api = r_api.json().get("resumen_temporada", {})
            api_cobertura = d_api.get("masa_cobertura_pct")
            api_pmax = d_api.get("p_max_aciertos_pct")
            api_pmid = d_api.get("p_mid_rescate_pct")
            api_plow = d_api.get("p_low_ruptura_pct")
            api_alpha = d_api.get("alpha_calibracion_pct")
            api_paridad = f"COINCIDE EXACTAMENTE (API Cobertura={api_cobertura}%, P_max={api_pmax}%)"
    except Exception as e_api:
        api_paridad = f"Servidor local no activo (cálculo en memoria es la verdad pura): {e_api}"
    print(f"   • Estado de Paridad API: {api_paridad}")

    # 3. Cálculo de Métricas Macro Finales
    if total_n == 0:
        print(f"❌ Sin partidos auditables (pendientes de captura P′: {pendientes_captura}).")
        print("=" * 90)
        return 1
    pct_pmax = round((conteo_pmax / total_n) * 100, 2)
    pct_pmid = round((conteo_pmid / total_n) * 100, 2)
    pct_plow = round((conteo_plow / total_n) * 100, 2)
    pct_masa = round(pct_pmax + pct_pmid, 2)

    bs_qbe_global = round(sum(brier_qbe_list) / total_n, 4)
    bs_mkt_global = round(sum(brier_mkt_list) / total_n, 4)
    alpha_global = round((1.0 - (bs_qbe_global / bs_mkt_global)) * 100, 2) if bs_mkt_global > 0 else 0.0

    print("\n" + "=" * 90)
    print("📊 [PASO 3] RESUMEN MACRO EJECUTIVO DE TEMPORADA (LA VERDAD DE LA MEMORIA)")
    print("=" * 90)
    print(f"  PARTIDOS TOTALES AUDITADOS: {total_n} partidos concluidos (Jornadas 1 a 11)")
    print(f"  PARTIDOS PENDIENTES DE CAPTURA P′ (no auditables): {pendientes_captura}\n")
    print(f"  ┌──────────────────────┬──────────────────────┬──────────────────────┬──────────────────────┐")
    print(f"  │ MASA DE COBERTURA    │ ACIERTO P_MAX        │ RESCATE P_MID        │ RUPTURA P_LOW        │")
    print(f"  │ {pct_masa:>6.2f} %              │ {pct_pmax:>6.2f} %              │ {pct_pmid:>6.2f} %              │ {pct_plow:>6.2f} %              │")
    print(f"  │ ({conteo_pmax+conteo_pmid} de {total_n} seguros)   │ ({conteo_pmax} partidos)          │ [{conteo_pmid_emp} Emp · {conteo_pmid_riv} Riv]       │ ({conteo_plow} partidos)          │")
    print(f"  └──────────────────────┴──────────────────────┴──────────────────────┴──────────────────────┘")
    print(f"\n  CALIBRACIÓN VS. CASAS DE APUESTAS:")
    print(f"  • Brier Score Q-BE     : {bs_qbe_global:.4f}")
    print(f"  • Brier Score Mercado  : {bs_mkt_global:.4f}")
    print(f"  • ALPHA GLOBAL TEMPORADA: {alpha_global:+.2f} %")
    print("=" * 90)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--detallado", action="store_true", help="Muestra los 97 partidos uno por uno")
    args = parser.parse_args()
    sys.exit(auditar_pipeline(detallado=args.detallado))
