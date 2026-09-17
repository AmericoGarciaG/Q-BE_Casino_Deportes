# -*- coding: utf-8 -*-
"""
Kybern Industrial — Instrumento 3: Auditor Sombra Neuro-Simbólico con Retroceso Algorítmico
Base de Gobierno: Kybern Framework v12.0 — Protocolo de Conciliación N-Versión

[ANTI-BUG] La traza consolidada del motor (~70KB) es comprimida a un resumen auditable
~3KB antes de enviarse a Gemini. Esto previene el error "model output must contain either
output text or tool calls" causado por context overflow silencioso del LLM.
"""
import os
import sys
import json
import httpx

if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(PROJECT_ROOT, "data", "output")
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

# ── Cargar llaves Gemini y modelo canónico desde .env (fuente de verdad) ─────
GEMINI_KEYS: list[str] = []
GEMINI_MODEL_ENV: str = "gemini-2.0-flash"  # Fallback si GEMINI_MODEL no está en .env
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r", encoding="utf-8") as _f:
        for _line in _f:
            _ls = _line.strip()
            if _ls.startswith("GEMINI_MODEL="):
                _parts = _ls.split("=", 1)
                if len(_parts) == 2 and _parts[1].strip():
                    GEMINI_MODEL_ENV = _parts[1].strip().strip('"').strip("'")
            elif _ls.startswith("Gemini_API_4_QBE_") or _ls.startswith("GEMINI_API_KEY"):
                _p = _ls.split("=", 1)
                if len(_p) == 2 and _p[1].strip():
                    GEMINI_KEYS.append(_p[1].strip().strip('"').strip("'"))


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES DE PROYECCIÓN DETERMINISTA
# Reducen los payloads crudos a solo los campos auditables por el LLM.
# [ARCH-PILLAR] Delegación Cognitiva: el LLM audita semántica/estrategia,
# Python extrae y comprime los datos — nunca al revés.
# ─────────────────────────────────────────────────────────────────────────────

def _proyectar_payload_entrada(raw_inputs: dict) -> dict:
    """
    Proyecta el payload crudo (~6KB) a un resumen compacto auditable.
    Retiene: bankroll, hard-caps, momios 1X2, pts/pj y política H2H por partido.
    """
    meta = raw_inputs.get("metadata_control", {})
    partidos_resumen = []
    for p in raw_inputs.get("partidos_crudos", []):
        partidos_resumen.append({
            "partido": p.get("partido"),
            "favorito": p.get("favorito_designado"),
            "underdog": p.get("underdog_designado"),
            "momios_1x2": p.get("momios_caliente_1x2", {}),
            "fav_pts_pj": p.get("estadisticas_favorito", {}).get("pts_por_partido"),
            "fav_posicion_tabla": p.get("estadisticas_favorito", {}).get("posicion_tabla"),
            "und_pts_pj": p.get("estadisticas_underdog", {}).get("pts_por_partido"),
            "und_posicion_tabla": p.get("estadisticas_underdog", {}).get("posicion_tabla"),
            "h2h_politica": p.get("antecedentes_h2h", {}).get("politica"),
        })
    return {
        "bankroll_mxn": meta.get("bankroll_disponible_mxn"),
        "modalidad": meta.get("modalidad_asignacion"),
        "hard_cap_individual_pct": meta.get("hard_cap_individual_pct"),
        "hard_cap_global_pct": meta.get("hard_cap_global_core_pct"),
        "partidos": partidos_resumen,
    }


def _proyectar_traza_qbe(qbe_trace: dict) -> dict:
    """
    Extrae solo los campos de decisión financiera del payload consolidado Q-BE (~70KB).
    Descarta: tabla_posiciones_completa, tesis_didactica, h2h_filas, tabla_10p.
    Retiene: órdenes con boletos y montos, análisis de probabilidades, descartes, balance.
    """
    ordenes_resumidas = []
    for o in qbe_trace.get("ordenes", []):
        boletos = o.get("boletos", {})
        b1 = boletos.get("boleto_1_seguro", {})
        b2 = boletos.get("boleto_2_ganancia", {})
        ordenes_resumidas.append({
            "partido": o.get("partido"),
            "estrategia_codigo": o.get("estrategia_seleccionada", {}).get("codigo"),
            "estrategia_nombre": o.get("estrategia_seleccionada", {}).get("nombre"),
            "inversion_total_mxn": boletos.get("inversion_partido_A_i"),
            "retorno_garantizado_mxn": boletos.get("retorno_garantizado_empate_mxn"),
            "ganancia_neta_esperada_mxn": boletos.get("ganancia_neta_esperada_mxn"),
            "boleto_1_seguro": {
                "seleccion": b1.get("seleccion"),
                "monto_mxn": b1.get("monto_mxn"),
                "momio": b1.get("momio"),
            } if b1 and b1.get("monto_mxn", 0) > 0 else None,
            "boleto_2_ganancia": {
                "seleccion": b2.get("seleccion"),
                "monto_mxn": b2.get("monto_mxn"),
                "momio": b2.get("momio"),
            } if b2 else None,
            "ev_neto_roi_pct": o.get("ev_neto_roi"),
        })

    analisis_resumen = []
    for p in qbe_trace.get("partidos_analisis", []):
        tres_vias = p.get("probabilidades_3vias", [{}, {}, {}])
        analisis_resumen.append({
            "partido": p.get("partido"),
            "estrategia": p.get("strategy_code") or p.get("estrategia_codigo"),
            "lambda_local": p.get("lambda_local"),
            "mu_visita": p.get("mu_visita"),
            "prob_fav_pct": p.get("prob_fav"),
            "prob_emp_pct": p.get("prob_emp"),
            "prob_und_pct": p.get("prob_und"),
            "psi_ruina": p.get("psi_downside"),
            "phi_lead2": p.get("phi_lead2"),
            "edge_fav_pct": tres_vias[0].get("edge") if len(tres_vias) > 0 else None,
            "edge_emp_pct": tres_vias[1].get("edge") if len(tres_vias) > 1 else None,
            "edge_und_pct": tres_vias[2].get("edge") if len(tres_vias) > 2 else None,
            "theta_req_pct": p.get("theta_req"),
        })

    descartes_resumen = [
        {"partido": d.get("partido"), "motivo_codigo": d.get("motivo_codigo"), "motivo": d.get("motivo", "")[:120]}
        for d in qbe_trace.get("descartes", [])
    ]

    return {
        "ordenes_ejecucion": ordenes_resumidas,
        "partidos_analisis": analisis_resumen,
        "descartes_veto_qbe00": descartes_resumen,
        "balance_global": qbe_trace.get("balance", {}),
    }


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def ejecutar_auditor_sombra():
    print("\n" + "=" * 90)
    print("🤖 [INSTRUMENTO 3] AUDITOR SOMBRA NEURO-SIMBÓLICO (CONCILIACIÓN INDEPENDIENTE)")
    print("=" * 90)

    path_entrada = os.path.join(OUT_DIR, "payload_entrada_calculos_j8.json")
    path_traza = os.path.join(OUT_DIR, "traza_calculos_qbe_j8.json")

    if not os.path.exists(path_entrada) or not os.path.exists(path_traza):
        print("❌ Faltan archivos de entrada. Ejecuta primero:")
        print("   python scripts/auditoria/2_simulador_forense.py")
        return

    with open(path_entrada, "r", encoding="utf-8") as f:
        raw_inputs = json.load(f)
    with open(path_traza, "r", encoding="utf-8") as f:
        qbe_trace = json.load(f)

    # ── PROYECCIÓN DETERMINISTA DE PAYLOADS ───────────────────────────────────
    # [ANTI-BUG] Reducción obligatoria antes de enviar al LLM.
    # La traza consolidada pesa ~70KB; el contexto seguro para Gemini Flash es ~10KB de datos.
    entrada_compacta = _proyectar_payload_entrada(raw_inputs)
    traza_compacta = _proyectar_traza_qbe(qbe_trace)
    entrada_json = json.dumps(entrada_compacta, indent=2, ensure_ascii=False)
    traza_json = json.dumps(traza_compacta, indent=2, ensure_ascii=False)
    bankroll = raw_inputs.get("metadata_control", {}).get("bankroll_disponible_mxn", 200.0)

    print(f"📐 Payload comprimido — Entrada: {len(entrada_json):,} bytes | Traza: {len(traza_json):,} bytes")

    if not GEMINI_KEYS:
        print("⚠️ No hay llaves Gemini en .env. Se omite llamada de red.")
        return

    MODEL_NAME = GEMINI_MODEL_ENV   # Leído desde .env — fuente canónica inmutable
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    print(f"🧠 Modelo Canónico Auditor: {MODEL_NAME}")

    prompt = f"""
Eres el AGENTE AUDITOR CUANTITATIVO SOMBRA del Kybern Framework v12.0.
Tu función es auditar independientemente los cálculos matemáticos del sistema Q-BE.

Recibes dos bloques de datos compactos:

## BLOQUE A — INSUMOS CRUDOS DE MERCADO (Bankroll ${bankroll:.2f} MXN, Momios, Tabla)
```json
{entrada_json}
```

## BLOQUE B — RESULTADOS DEL MOTOR DETERMINISTA Q-BE (Órdenes, Análisis, Balance)
```json
{traza_json}
```

## INSTRUCCIONES DE AUDITORÍA CUANTITATIVA Y FINANCIERA

**1. Validación de Capital Comprometido vs. Bankroll:**
- Evalúa el capital total invertido vs el Bankroll disponible (${bankroll:.2f} MXN).
- Hard-Cap individual: cada inversión ≤ ${bankroll * 0.08:.2f} MXN (8% de ${bankroll:.2f})
- Hard-Cap global: suma total inversiones ≤ ${bankroll * 0.25:.2f} MXN (25% de ${bankroll:.2f})
- Verifica que `balance_global.capital_total_comprometido_mxn` respete ambos límites.

**2. Validación de Ganancias y ROI:**
- Audita la Ganancia Neta Potencial (Premio Bruto - Inversión) y la Ganancia Neta Esperada (+EV).
- Verifica la coherencia de la tasa ROI % esperada en el portafolio.

**3. Comparativa de Cuotas y Probabilidad Implícita:**
- Compara cada cuota 1X2 capturada en Q-BE con la probabilidad implícita del sportsbook `(1/cuota)*100`.
- Para cada partido calcula: `prob_impl_total = (1/L) + (1/E) + (1/V)` y verifica que `prob_impl_total > 1.0` (Vigorish del casino).

**4. Validación del Piso Mínimo de Apuesta ($2.00 MXN):**
- Revisa cada boleto individual en `ordenes_ejecucion` (`boleto_1_seguro` y `boleto_2_ganancia`).
- Certifica que NINGÚN boleto activo con asignación de capital posea un monto menor a $2.00 MXN (salvo boletos de $0.00 MXN de contexto en QBE-D1/D1+).

**5. TABLA DE CONCILIACIÓN — DELTA MATRIX:**
Genera esta tabla en Markdown:

| Partido | Estrategia Q-BE | Piso Min $2.00 | Tu Veredicto | Coincidencia | Δ-Comentario |
|---------|----------------|:--------------:|--------------|:------------:|--------------|

**6. PROTOCOLO BACKTRACKING:**
Si detectas divergencias matemáticas (Δ > ε), señala el nodo del grafo responsable:
- `[LN-QBE-020]` Decay H2H — `[LN-QBE-030]` Métricas FCF/E_att
- `[LN-QBE-040]` Poisson 6×6 — `[LN-QBE-050]` Breakeven θ*
- `[LN-QBE-060]` Evaluador Estrategias — `[LN-QBE-070]` Portfolio Kelly+Dutching

**IMPORTANTE:** Comienza tu respuesta EXACTAMENTE con la siguiente línea (sin ningún texto previo):
`# 🏛️ DICTAMEN DE AUDITORÍA SOMBRA — KYBERN FRAMEWORK v12.0`

Luego continúa con las secciones numeradas del dictamen en Markdown.
"""

    api_payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192},
    }

    print("📡 Invocando Gemini — Auditor Cuantitativo Sombra (rotación de llaves activa)...")
    try:
        with httpx.Client(timeout=90.0) as client:
            resp = None
            for idx, api_key in enumerate(GEMINI_KEYS, 1):
                url = f"{BASE_URL}/{MODEL_NAME}:generateContent?key={api_key}"
                print(f"   🔑 Llave #{idx}/{len(GEMINI_KEYS)}...")
                try:
                    resp = client.post(url, json=api_payload)
                except Exception as net_ex:
                    print(f"   ❌ Error de red con Llave #{idx}: {net_ex}")
                    resp = None
                    continue

                if resp.status_code == 200:
                    # [ANTI-BUG] Verificar que la respuesta no esté vacía.
                    # finishReason != STOP indica context-overflow o safety block.
                    r_json = resp.json()
                    candidates = r_json.get("candidates", [])
                    has_text = (
                        candidates
                        and candidates[0].get("content", {}).get("parts")
                        and candidates[0]["content"]["parts"][0].get("text")
                    )
                    if not has_text:
                        finish = candidates[0].get("finishReason", "UNKNOWN") if candidates else "NO_CANDIDATES"
                        print(f"   ⚠️ Llave #{idx}: Respuesta vacía (finishReason={finish}). Rotando...")
                        resp = None
                        continue
                    print(f"   ✅ Llave #{idx} respondió OK.")
                    break
                elif resp.status_code in (429, 503):
                    print(f"   ⚠️ Llave #{idx} en cuota/cooldown ({resp.status_code}). Rotando...")
                    resp = None
                    continue
                else:
                    print(f"   ⚠️ Llave #{idx} HTTP {resp.status_code}. Intentando siguiente llave...")
                    resp = None
                    continue

            if resp and resp.status_code == 200:
                res_json = resp.json()
                texto_md = res_json["candidates"][0]["content"]["parts"][0]["text"]

                out_md_path = os.path.join(OUT_DIR, "auditoria_sombra_gemini_j8.md")
                with open(out_md_path, "w", encoding="utf-8") as f_out:
                    f_out.write(texto_md)

                print("\n" + "=" * 90)
                print("📋 DICTAMEN DE CONCILIACIÓN DEL AUDITOR SOMBRA:")
                print("=" * 90)
                print(texto_md[:1500])
                print("... [Ver dictamen completo en data/output/auditoria_sombra_gemini_j8.md]")
                print("\n" + "=" * 90)
                print(f"📄 Reporte guardado en: {out_md_path}")
                print("=" * 90 + "\n")
            else:
                print("\n⚠️ [AUDITOR SOMBRA] Todas las llaves Gemini en cuota/error.")
                print("   Los payloads comprimidos están en data/output/ para auditoría manual.")

    except Exception as ex:
        print(f"❌ Error durante la auditoría IA: {ex}")


if __name__ == "__main__":
    ejecutar_auditor_sombra()
