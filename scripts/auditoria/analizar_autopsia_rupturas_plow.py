# -*- coding: utf-8 -*-
"""
🔬 Q-BE: AUTOPSIA FORENSE DE RUPTURAS RESIDUALES P_LOW (LOS 29 FALLOS)
[ARCH-1.4.40] Análisis de patrones comunes, convergencia con mercado y arquetipos de veto.
Régimen: [DBBD-FUNGIBLE] — Utilidad de Analítica de Solo Lectura.
Autoridad: Américo García Guerrero (Director Humano)

EXPEDIENTES: ANALISIS-RUPTURAS-PLOW · [ARCH-1.4.40] · VETO-QBE-00-FILTER

Contrato de consumo (cero invención de cifras, [GOVERNANCE-01]):
  GET /api/markets/backtesting/calibration-report?league_id=1  ([ARCH-1.4.38] / [LN-QBE-100])

🛠️ ENMIENDA DE CONTRATO FACTUAL (sustitución mecánica 1:1, SIN invención de lógica):
El Túnel de Contexto declara el esquema CONCEPTUAL anidado de la directiva; el DTO real
`CalibrationMatchOut` / `CalibrationJornadaOut` (src/models/web_schemas.py) es PLANO, tal como
ya fue resuelto por el precedente sellado `scripts/auditoria/analizar_ego_contrarian.py`
(decreto VAR-2026-EGO-CONTRARIAN-AUDIT §VAR-UI-01). Se aplica la MISMA sustitución 1:1:

    jornada["matchday"]          →  jornada["jornada"]
    partido["home_score"]        →  partido["goles_local"]
    partido["away_score"]        →  partido["goles_visitante"]
    partido["marcador"]          →  ya viene formateado ("X - Y", [ARCH-1.4.38])
    partido["cuotas"]            →  partido["momios"]  (claves "L" | "E" | "V" reales capturadas)

Sin esta proyección el detector de arquetipos mediría 0 goles por partido (campo ausente ⇒
default 0) y el arquetipo "Empate Bipolar de Fuego (≥4 goles)" quedaría estructuralmente
INERTE, además de reportar todas las jornadas como `JNone`. Cero lógica de negocio alterada:
las umbrales, los arquetipos, el orden de cascada y las fórmulas son VERBATIM de la directiva.
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


def ejecutar_autopsia():
    print("📡 Consultando el expediente completo de calibración de temporada...")
    try:
        resp = httpx.get("http://127.0.0.1:8000/api/markets/backtesting/calibration-report?league_id=1", timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"❌ Error conectando al endpoint de calibración: {e}")
        print("   Asegúrate de que run_app.py esté corriendo en http://127.0.0.1:8000")
        return 1

    partidos_ruptura: List[Dict[str, Any]] = []
    total_auditados = 0

    for j in data.get("jornadas", []):
        # [ENMIENDA 1:1] jornada["matchday"] → jornada["jornada"] (DTO plano).
        mday = j.get("jornada")
        for p in j.get("partidos", []):
            total_auditados += 1
            # Verificar si el resultado cayó en P_low (clasificacion_triada == 'P_LOW' o tipo_resultado == 'UNDERDOG')
            triada = p.get("clasificacion_triada")
            tipo = p.get("tipo_resultado")

            # Ordenar P' para confirmar
            p_prime = [
                ("LOCAL", float(p.get("p_local", 0.0))),
                ("EMPATE", float(p.get("p_empate", 0.0))),
                ("VISITANTE", float(p.get("p_visitante", 0.0)))
            ]
            p_prime.sort(key=lambda x: x[1], reverse=True)
            r_max, val_max = p_prime[0]
            r_mid, val_mid = p_prime[1]
            r_low, val_low = p_prime[2]

            res_real = p.get("resultado_real")

            # Condición canónica de ruptura: ocurrió r_low
            if res_real == r_low or triada == "P_LOW":
                p["jornada_num"] = mday
                p["r_max"] = r_max
                p["val_max"] = val_max
                p["r_mid"] = r_mid
                p["val_mid"] = val_mid
                p["r_low"] = r_low
                p["val_low"] = val_low
                partidos_ruptura.append(p)

    n_rup = len(partidos_ruptura)
    print(f"\n==========================================================================================")
    print(f"🔬 AUTOPSIA FORENSE DE RUPTURAS RESIDUALES P_LOW (TOTAL PARTIDOS: {n_rup} de {total_auditados})")
    print(f"==========================================================================================")
    print(f"{'#':<3} {'J':<3} {'PARTIDO':<33} {'FINAL':<6} {'P_max':<8} {'P_mid':<8} {'P_low (REAL)':<14} {'q_mkt':<8} {'CUOTA':<6}")
    print(f"-" * 95)

    conteo_desenlace = {"LOCAL": 0, "EMPATE": 0, "VISITANTE": 0}
    conteo_arquetipo = {
        "Falsa Paridad (Entropía Alta)": 0,
        "Empate Bipolar de Fuego (≥4 goles)": 0,
        "Empate Táctico no Detectado": 0,
        "Golpe al Gigante (P_max > 50%)": 0,
        "Ruptura Foránea Convencional": 0
    }

    mercado_acerto = 0
    mercado_fallo = 0
    cold_start_count = 0

    for idx, p in enumerate(partidos_ruptura, 1):
        jornada = p.get("jornada_num")
        local = p.get("local", "")[:15]
        vis = p.get("visitante", "")[:15]
        etiqueta = f"{local} vs {vis}"
        # [ENMIENDA 1:1] p["home_score"]/p["away_score"] → p["goles_local"]/p["goles_visitante"]
        # (el DTO plano ya expone además `marcador` formateado "X - Y").
        marcador = f"{p.get('goles_local')}-{p.get('goles_visitante')}"
        res_real = p.get("resultado_real")
        conteo_desenlace[res_real] = conteo_desenlace.get(res_real, 0) + 1

        val_max = p.get("val_max", 0.0) * 100
        val_mid = p.get("val_mid", 0.0) * 100
        val_low = p.get("val_low", 0.0) * 100
        r_low = p.get("r_low")

        # Cuota y mercado de la ruptura
        # [ENMIENDA 1:1] p["cuotas"] → p["momios"] (trío factual L|E|V capturado en el snapshot).
        cuotas = p.get("momios", {})
        q_mkt = {
            "LOCAL": p.get("q_local", 0.0),
            "EMPATE": p.get("q_empate", 0.0),
            "VISITANTE": p.get("q_visitante", 0.0)
        }
        max_q = max(q_mkt.values()) if q_mkt else 0.0
        fav_mkt = [k for k, v in q_mkt.items() if v == max_q][0] if q_mkt else ""

        # ¿El mercado lo vio venir?
        if fav_mkt == res_real:
            mercado_acerto += 1
            mkt_str = f"Mkt✓ {q_mkt[res_real]*100:.1f}%"
        else:
            mercado_fallo += 1
            mkt_str = f"Mkt✗ {q_mkt[res_real]*100:.1f}%"

        clave_cuota = "L" if res_real == "LOCAL" else ("E" if res_real == "EMPATE" else "V")
        cuota_pagada = cuotas.get(clave_cuota, 0.0)

        # Clasificación de Arquetipos Forenses
        total_goles = int(p.get("goles_local", 0)) + int(p.get("goles_visitante", 0))
        delta_p = (val_max - val_low)

        if p.get("suficiencia_S_I") == 0:
            cold_start_count += 1

        if res_real == "EMPATE" and total_goles >= 4:
            conteo_arquetipo["Empate Bipolar de Fuego (≥4 goles)"] += 1
            arq = "Bipolar Fuego"
        elif delta_p <= 15.0:
            conteo_arquetipo["Falsa Paridad (Entropía Alta)"] += 1
            arq = "Falsa Paridad"
        elif val_max >= 50.0:
            conteo_arquetipo["Golpe al Gigante (P_max > 50%)"] += 1
            arq = "Golpe Gigante"
        elif res_real == "EMPATE":
            conteo_arquetipo["Empate Táctico no Detectado"] += 1
            arq = "Empate Táctico"
        else:
            conteo_arquetipo["Ruptura Foránea Convencional"] += 1
            arq = "Ruptura Foránea"

        print(f"{idx:<3} J{jornada:<2} {etiqueta:<33} {marcador:<6} {val_max:>5.1f}%  {val_mid:>5.1f}%  {r_low[:3]} {val_low:>5.1f}%  {mkt_str:<12} @{cuota_pagada:<5.2f} [{arq}]")


    print(f"-" * 95)
    print(f"\n📊 RADIOGRAFÍA FORENSE DE LOS {n_rup} FALLOS RESIDUALES:")
    print(f"------------------------------------------------------------------------------------------")
    print(f"1. DESGLOSE POR TIPO DE DESENLACE REAL:")
    for k, v in conteo_desenlace.items():
        print(f"   • {k:<10}: {v:>2} partidos ({v/n_rup*100:.1f}%)")

    print(f"\n2. COMPORTAMIENTO DEL MERCADO (CASAS DE APUESTAS):")
    print(f"   • Mercado también falló (Sorpresa real de la naturaleza) : {mercado_fallo:>2} partidos ({mercado_fallo/n_rup*100:.1f}%)")
    print(f"   • Mercado sí acertó (Ineficiencia o ceguera de Q-BE)      : {mercado_acerto:>2} partidos ({mercado_acerto/n_rup*100:.1f}%)")
    print(f"   • Partidos en Cold Start (J1-J3, sin datos suficientes)   : {cold_start_count:>2} partidos ({cold_start_count/n_rup*100:.1f}%)")

    print(f"\n3. ARQUETIPOS DE RUPTURA IDENTIFICADOS (REGLAS CANDIDATAS PARA VETO QBE-00):")
    for k, v in conteo_arquetipo.items():
        print(f"   • {k:<38}: {v:>2} partidos ({v/n_rup*100:.1f}%)")

    print(f"\n4. IMPACTO PROYECTADO DE UN VETO INTELIGENTE (QBE-00):")
    vetables = conteo_arquetipo["Falsa Paridad (Entropía Alta)"] + conteo_arquetipo["Empate Bipolar de Fuego (≥4 goles)"]
    nueva_cobertura = ((total_auditados - (n_rup - vetables)) / (total_auditados - vetables)) * 100 if (total_auditados - vetables) > 0 else 0
    print(f"   • Rupturas eliminables mediante reglas de veto sistemático : {vetables} partidos")
    print(f"   • Tasa de Cobertura resultante si se hubieran vetado       : {nueva_cobertura:.2f}% (frente al 70.11% actual)")
    print(f"==========================================================================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(ejecutar_autopsia())

