# -*- coding: utf-8 -*-
"""
🔬 Q-BE: AUTOPSIA FORENSE DE RUPTURAS RESIDUALES P_LOW (32 FALLOS) — VERSIÓN 2.0
[ARCH-1.4.40 / LN-QBE-060-C] Minería de características y evaluación del Veto Inteligente.
Régimen: [DBBD-FUNGIBLE] — Analítica Pura de Solo Lectura con Fallback a SQLite.
Autoridad: Américo García Guerrero (Director Humano)
"""

import sys
import os
import httpx
from typing import Dict, Any, List, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.storage.gateway import PersistenceGateway
from src.storage.models import FixtureSnapshot, Match, SovereignDistribution
from src.core.contracts.portfolio_math import (
    desmarcar_cuotas_proporcional,
    DELTA_P_PARIDAD_VETO,
    PMAX_MIN_OPERABLE,
    LAMBDA_SUMA_FUEGO_VETO,
    P_EMPATE_FUEGO_TECHO
)

# [ENMIENDA 1:1] La resolución de cuotas de cierre NO se espeja: se IMPORTA la ley sellada del
# Visor (`[ARCH-1.4.38]`). Cero relleno sintético de cuotas ([GOVERNANCE-01]).
from src.web.routes.markets import _cuotas_1x2_factuales  # noqa: E402

# ── ENMIENDA DE CONTRATO FACTUAL 1:1 [VAR-2026-AUTOPSIA-PLOW-V2] ───────────────────────────────
# Cero invención de lógica: los umbrales del veto, los arquetipos y las fórmulas del contrato
# `[LN-QBE-060-C]` se consumen VERBATIM de `src.core.contracts.portfolio_math`. Se corrigen
# únicamente tres llaves de ACCESO A DATOS que no existen en el diccionario de la bóveda viva:
#   (§1) `Tuple` faltaba en el `typing` ⇒ `NameError` en la firma del propio módulo.
#   (§2) El barrido offline buscaba `home_score`/`away_score` DENTRO del JSON del fixture; esas
#        llaves no existen (`matches_json` porta `id_partido`, `local`, `visitante`, `momios`,
#        `p_*`, `suficiencia_S_I`, `lambda_*`). El marcador consumado vive en `matches` (3NF),
#        que es el oráculo sellado del Visor: el barrido devolvía 0 partidos y abortaba.
#   (§3) `Match.status == "FINISHED"` no casa con la bóveda viva (97 filas `FINALIZADO`).
_ESTADOS_CONCLUIDOS = frozenset({"FINISHED", "FINALIZADO"})


def _indice_fixtures_y_lambdas() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Tuple[float, float]]]:
    """Índice `{id_partido: fixture}` (precedencia del Visor sellado) y `{id_partido: (λ_h, λ_a)}`.

    [ENMIENDA §4] El DTO REST del Visor (`CalibrationMatchOut`, `extra="ignore"`) NO expone
    `lambda_home`/`lambda_away`; sin rehidratar los xG combinados desde la bóveda la regla
    «Bipolar de Fuego» de `[LN-QBE-060-C]` quedaría estructuralmente inerte al leer de la API.
    Se transporta el insumo sellado (captura del snapshot con respaldo en `sovereign_distributions`)
    sin alterar un solo umbral ni una sola fórmula.
    """
    indice: Dict[str, Dict[str, Any]] = {}
    lambdas: Dict[str, Tuple[float, float]] = {}
    gw = PersistenceGateway()
    with gw.read_session() as session:
        snaps = session.query(FixtureSnapshot).filter(
            FixtureSnapshot.league_id == 1
        ).order_by(FixtureSnapshot.matchday.asc(), FixtureSnapshot.updated_at.desc()).all()
        for snap in snaps:
            for fx in (snap.matches_json or []):
                id_fx = str(fx.get("id_partido") or "")
                if id_fx:
                    indice.setdefault(id_fx, fx)
        for fila in session.query(SovereignDistribution).all():
            lambdas[str(fila.match_id)] = (float(fila.lambda_home), float(fila.lambda_away))

    # La captura congelada del fixture manda sobre el respaldo soberano (misma autoridad que el Visor).
    for id_fx, fx in indice.items():
        try:
            lambdas[id_fx] = (float(fx.get("lambda_home")), float(fx.get("lambda_away")))
        except (TypeError, ValueError):
            continue
    return indice, lambdas



def obtener_partidos_concluidos() -> Tuple[List[Dict[str, Any]], str]:
    """Obtiene los partidos concluidos desde la API o directamente desde SQLite 3NF."""
    try:
        resp = httpx.get("http://127.0.0.1:8000/api/markets/backtesting/calibration-report?league_id=1", timeout=5.0)
        if resp.status_code == 200:
            partidos = []
            for j in resp.json().get("jornadas", []):
                for p in j.get("partidos", []):
                    # [ENMIENDA 1:1] El DTO plano del Visor expone la jornada como `jornada`.
                    p["jornada_num"] = j.get("jornada")
                    partidos.append(p)
            # Rehidratación de los xG combinados (insumo del veto, ausente del DTO REST plano).
            _, lambdas = _indice_fixtures_y_lambdas()
            for p in partidos:
                lam = lambdas.get(str(p.get("id_partido")), (0.0, 0.0))
                if p.get("lambda_home") is None:
                    p["lambda_home"] = lam[0]
                if p.get("lambda_away") is None:
                    p["lambda_away"] = lam[1]
                # Captura de cuotas con la MISMA forma que el fixture sellado (ley [ARCH-1.4.38]).
                p["_fixture"] = {
                    "cuotas": p.get("cuotas"),
                    "momios": p.get("momios") or {},
                    "momios_operadores": p.get("momios_operadores") or {},
                }
            return partidos, "API REST (Live Web)"
    except Exception:
        pass

    # Fallback directo a SQLite 3NF — universo auditable IDÉNTICO al del Visor sellado.
    indice, lambdas = _indice_fixtures_y_lambdas()
    partidos = []
    gw = PersistenceGateway()
    with gw.read_session() as session:
        filas = session.query(Match).order_by(Match.matchday_num.asc(), Match.id.asc()).all()
        soberanas = {
            str(f.match_id): (float(f.p_local), float(f.p_empate), float(f.p_visitante))
            for f in session.query(SovereignDistribution).all()
        }
        cola = [
            fila for fila in filas
            if fila.matchday_num is not None
            and fila.score_home is not None
            and fila.score_away is not None
            and str(fila.status or "").upper() in _ESTADOS_CONCLUIDOS
        ]

    for fila in cola:
        fx = indice.get(str(fila.id), {})
        # [ENMIENDA §2] El marcador consumado se lee del oráculo 3NF (`matches`), no del JSON del fixture.
        p_prima = None
        try:
            p_prima = (float(fx.get("p_local")), float(fx.get("p_empate")), float(fx.get("p_visitante")))
        except (TypeError, ValueError):
            p_prima = None
        if p_prima is None:
            p_prima = soberanas.get(str(fila.id))
        if p_prima is None:
            continue

        cuotas = fx.get("cuotas") or fx.get("momios") or {}
        ql, qe, qv = desmarcar_cuotas_proporcional(
            float(cuotas.get("L", 0.0) or 0.0),
            float(cuotas.get("E", 0.0) or 0.0),
            float(cuotas.get("V", 0.0) or 0.0),
        )
        # [LN-QBE-100] Axioma del Prior de Mercado (Cold Start Resolution): con S(I)=0 la
        # distribución sellada es la ignorancia uniforme y se sustituye por el consenso desmarcado,
        # de modo que la ruta offline califique EXACTAMENTE el mismo universo que la ruta REST.
        s_i = fx.get("suficiencia_S_I")
        if s_i is not None and int(s_i) == 0:
            p_prima = (ql, qe, qv)

        hs, as_ = int(fila.score_home), int(fila.score_away)
        lam = lambdas.get(str(fila.id), (0.0, 0.0))
        partidos.append({
            "id_partido": str(fila.id),
            "jornada_num": int(fila.matchday_num),
            "local": fx.get("local") or str(fila.home_team_slug),
            "visitante": fx.get("visitante") or str(fila.away_team_slug),
            "goles_local": hs,
            "goles_visitante": as_,
            "resultado_real": "LOCAL" if hs > as_ else ("EMPATE" if hs == as_ else "VISITANTE"),
            "p_local": p_prima[0],
            "p_empate": p_prima[1],
            "p_visitante": p_prima[2],
            "momios": cuotas if cuotas else {},
            "suficiencia_S_I": s_i,
            "lambda_home": lam[0],
            "lambda_away": lam[1],
            # Captura cruda del fixture: los mismos insumos que consume la ley sellada de cuotas.
            "_fixture": fx,
        })
    return partidos, "SQLite 3NF Directo (Fallback Offline)"

def ejecutar_autopsia():
    partidos, fuente = obtener_partidos_concluidos()
    if not partidos:
        print("❌ No se pudieron cargar partidos concluidos.")
        return 1

    print(f"📡 Insumos cargados desde: {fuente} ({len(partidos)} partidos totales).")

    partidos_ruptura = []
    total_auditados = len(partidos)

    for p in partidos:
        pl = float(p.get("p_local", 0.3333))
        pe = float(p.get("p_empate", 0.3333))
        pv = float(p.get("p_visitante", 0.3333))
        pares = [("LOCAL", pl), ("EMPATE", pe), ("VISITANTE", pv)]
        pares.sort(key=lambda x: x[1], reverse=True)
        r_max, v_max = pares[0]
        r_mid, v_mid = pares[1]
        r_low, v_low = pares[2]

        res_real = p.get("resultado_real")
        if res_real == r_low:
            p["r_max"] = r_max
            p["val_max"] = v_max
            p["r_mid"] = r_mid
            p["val_mid"] = v_mid
            p["r_low"] = r_low
            p["val_low"] = v_low
            partidos_ruptura.append(p)

    n_rup = len(partidos_ruptura)
    cobertura_base_pct = round(((total_auditados - n_rup) / total_auditados) * 100, 2)

    print("\n" + "=" * 95)
    print(f"🔬 AUTOPSIA FORENSE DE RUPTURAS RESIDUALES P_LOW ({n_rup} FALLOS DE {total_auditados} PARTIDOS)")
    print(f"   Línea Base Actual de Cobertura: {cobertura_base_pct}%")
    print("=" * 95)
    print(f"{'#':<3} {'J':<3} {'PARTIDO':<33} {'FINAL':<6} {'P_max':<8} {'P_mid':<8} {'P_low(REAL)':<12} {'MKT':<10} {'VETO [LN-060-C]'}")
    print("-" * 95)

    conteo_desenlace = {"LOCAL": 0, "EMPATE": 0, "VISITANTE": 0}
    vetos_falsa_paridad = 0
    vetos_bipolar_fuego = 0
    conteo_mercado_fallo = 0
    sin_captura_mkt = 0

    for idx, p in enumerate(partidos_ruptura, 1):
        jornada = p.get("jornada_num")
        loc = p.get("local", "")[:15]
        vis = p.get("visitante", "")[:15]
        etiqueta = f"{loc} vs {vis}"
        marcador = f"{p.get('goles_local')}-{p.get('goles_visitante')}"
        res_real = p.get("resultado_real")
        conteo_desenlace[res_real] = conteo_desenlace.get(res_real, 0) + 1

        v_max = p["val_max"] * 100
        v_mid = p["val_mid"] * 100
        v_low = p["val_low"] * 100
        r_low = p["r_low"]

        # Cuotas de mercado — LEY SELLADA [ARCH-1.4.38] y, si el Visor ya las publica desmarcadas,
        # sus q_* canónicas. PROHIBIDO el relleno sintético 2.0/3.0/3.5 de la directiva
        # ([GOVERNANCE-01]): sin trío factual el partido se declara `Mkt n/d` y queda EXCLUIDO del
        # cruce con el Casino, en lugar de fabricar un favorito de mercado inexistente.
        q_dict = None
        try:
            q_dict = {
                "LOCAL": float(p.get("q_local")),
                "EMPATE": float(p.get("q_empate")),
                "VISITANTE": float(p.get("q_visitante")),
            }
        except (TypeError, ValueError):
            q_dict = None

        if q_dict is None:
            cuotas = _cuotas_1x2_factuales(p.get("_fixture") or {})
            if cuotas:
                ql, qe, qv = desmarcar_cuotas_proporcional(
                    float(cuotas.get("L", 0.0) or 0.0),
                    float(cuotas.get("E", 0.0) or 0.0),
                    float(cuotas.get("V", 0.0) or 0.0),
                )
                q_dict = {"LOCAL": ql, "EMPATE": qe, "VISITANTE": qv}

        if not q_dict:
            sin_captura_mkt += 1
            mkt_str = "Mkt n/d"
        else:
            max_q = max(q_dict.values())
            fav_mkt = [k for k, v in q_dict.items() if v == max_q][0]
            if fav_mkt != res_real:
                conteo_mercado_fallo += 1
                mkt_str = f"Mkt✗ {q_dict[res_real]*100:.0f}%"
            else:
                mkt_str = f"Mkt✓ {q_dict[res_real]*100:.0f}%"

        # Evaluación Ex-Ante de la Ley de Veto [LN-QBE-060-C]
        delta_p = (p["val_max"] - p["val_low"])
        lh = float(p.get("lambda_home", 0.0) or 0.0)
        la = float(p.get("lambda_away", 0.0) or 0.0)
        suma_lam = lh + la
        pe = float(p.get("p_empate", 0.0))

        veto_motivo = "NO VETADO"
        if delta_p <= DELTA_P_PARIDAD_VETO and p["val_max"] <= PMAX_MIN_OPERABLE:
            vetos_falsa_paridad += 1
            veto_motivo = "🛡️ VETO: Falsa Paridad"
        elif suma_lam >= LAMBDA_SUMA_FUEGO_VETO and pe <= P_EMPATE_FUEGO_TECHO and p["val_max"] < 0.50:
            vetos_bipolar_fuego += 1
            veto_motivo = "🛡️ VETO: Bipolar Fuego"

        print(f"{idx:<3} J{jornada:<2} {etiqueta:<33} {marcador:<6} {v_max:>5.1f}%  {v_mid:>5.1f}%  {r_low[:3]} {v_low:>5.1f}%  {mkt_str:<10} {veto_motivo}")

    total_vetados = vetos_falsa_paridad + vetos_bipolar_fuego
    n_operables = total_auditados - total_vetados
    n_fallos_restantes = n_rup - total_vetados
    cobertura_con_veto_pct = round(((n_operables - n_fallos_restantes) / n_operables) * 100, 2)

    print("-" * 95)
    print("\n📊 RADIOGRAFÍA DE PATRONES DE LAS RUPTURAS:")
    print(f"• Desglose por desenlace real: EMPATES: {conteo_desenlace.get('EMPATE', 0)} ({conteo_desenlace.get('EMPATE', 0)/n_rup*100:.1f}%) | VISITAS: {conteo_desenlace.get('VISITANTE', 0)} | LOCALES: {conteo_desenlace.get('LOCAL', 0)}")
    print(f"• Fallos compartidos con el Casino: {conteo_mercado_fallo} de {n_rup - sin_captura_mkt} ({conteo_mercado_fallo/max(1, (n_rup - sin_captura_mkt))*100:.1f}% sorpresas para todos)")
    print(f"• Rupturas sin captura factual de cuotas (excluidas del cruce con el Casino): {sin_captura_mkt}")
    print(f"\n🎯 IMPACTO FACTUAL DEL VETO INTELIGENTE [LN-QBE-060-C]:")
    print(f"• Rupturas interceptadas por Falsa Paridad (ΔP <= 12%): {vetos_falsa_paridad} partidos")
    print(f"• Rupturas interceptadas por Bipolar de Fuego (xG >= 3.0): {vetos_bipolar_fuego} partidos")
    print(f"• TOTAL RUPTURAS ELIMINABLES DE LA CARTERA : {total_vetados} partidos de {n_rup}")
    print(f"• Tasa de Cobertura Base (sin veto)         : {cobertura_base_pct}%")
    print(f"• TASA DE COBERTURA REAL CON VETO ACTIVO   : {cobertura_con_veto_pct}% (sobre {n_operables} partidos operables)")
    print("=" * 95)
    return 0


if __name__ == "__main__":
    sys.exit(ejecutar_autopsia())
