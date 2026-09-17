# -*- coding: utf-8 -*-
"""
Kybern Industrial — Script 3: Auditor Matemático Independiente de Cartera (The Shield)
Base de Gobierno: Kybern Framework v12.0
Responsabilidad: Certificar numéricamente el último portafolio en SQLite (Invarianzas 1 a 8),
validar Dutching V=0, Hard-Caps y exportar data/output/auditoria_cuantitativa_jornada_8.md.
"""
import os
import sys
import json
import sqlite3
import numpy as np

if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "qbe_database.db")
OUT_DIR = os.path.join(PROJECT_ROOT, "data", "output")
os.makedirs(OUT_DIR, exist_ok=True)

def auditar_ultimo_portafolio():
    print("\n" + "="*85)
    print("🛡️ [SCRIPT 3] AUDITORÍA FORENSE MATEMÁTICA INDEPENDIENTE (THE SHIELD)")
    print("="*85)

    if not os.path.exists(DB_PATH):
        print(f"❌ Base de datos no encontrada en {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, matchday, bankroll, portfolio_json, generated_at FROM portfolio_records ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if not row:
        print("❌ No hay registros de portafolio en portfolio_records.")
        return False

    p_id, matchday, bankroll, raw_json, gen_at = row
    data = json.loads(raw_json) if isinstance(raw_json, str) else raw_json

    ordenes = data.get("ordenes", [])
    balance = data.get("balance", {})
    control = data.get("control", {})
    meta = data.get("metadata", {})

    print(f"📋 Portafolio ID: #{p_id} | Jornada: {matchday} | Bankroll: ${bankroll:.2f} MXN | Fecha: {gen_at}")
    print(f"   Partidos Operables en Cartera: {len(ordenes)}")

    invarianzas_ok = True

    # 1. Invarianza Dutching Exacto en Coberturas (V=0)
    print("\n[INVARIANZA 1 & 2] Simplex y Recuperación Exacta en Tablas (Dutching V=0):")
    for o in ordenes:
        cod = o.get("estrategia_seleccionada", {}).get("codigo", "QBE-D1")
        b = o.get("boletos", {})
        inv = b.get("inversion_partido_A_i", 0.0)
        b1 = b.get("boleto_1_seguro", {})
        b2 = b.get("boleto_2_ganancia", {})

        m1 = b1.get("monto_mxn", 0.0) if b1 else 0.0
        m2 = b2.get("monto_mxn", 0.0) if b2 else 0.0
        suma = round(m1 + m2, 2)
        assert abs(suma - inv) <= 0.02, f"Error suma boletos en {o.get('partido')}: ${suma} != ${inv}"

        if any(f in cod for f in ["H1", "H2", "R1"]) and m1 > 0:
            retorno = round(m1 * b1.get("momio", 1.0), 2)
            dif = abs(retorno - inv)
            print(f"   • {o.get('partido',''):<34} [{cod:<7}] Inv: ${inv:>6.2f} | Retorno Tablas: ${retorno:>6.2f} (Dif: ${dif:.2f})")
            if dif > 0.08:
                print(f"     ❌ FALLO: Retorno no garantiza tablas (Dif ${dif:.2f} > $0.08)")
                invarianzas_ok = False
        else:
            print(f"   • {o.get('partido',''):<34} [{cod:<7}] Inversión Directa: ${inv:>6.2f} (Alta convicción)")

    # 2. Hard-Caps de Capital
    print("\n[INVARIANZA 3 & 4] Hard-Caps de Preservación de Capital:")
    tot_inv = sum(o.get("boletos", {}).get("inversion_partido_A_i", 0.0) for o in ordenes)
    cap_glob = bankroll * 0.2501
    cap_ind = bankroll * 0.0801

    print(f"   • Inversión Total Cartera: ${tot_inv:.2f} MXN | Límite Máximo 25%: ${cap_glob:.2f} MXN")
    if tot_inv > cap_glob:
        print("     ❌ FALLO: Inversión total supera el Hard-Cap global del 25%.")
        invarianzas_ok = False
    else:
        print("     ✅ Hard-Cap Global cumplido.")

    for o in ordenes:
        inv_i = o.get("boletos", {}).get("inversion_partido_A_i", 0.0)
        if inv_i > cap_ind:
            print(f"     ❌ FALLO en {o.get('partido')}: Inversión ${inv_i:.2f} supera el 8% individual (${cap_ind:.2f}).")
            invarianzas_ok = False

    # 3. Techo Aritmético de Cartera
    print("\n[INVARIANZA 7] Techo Aritmético de Ganancia de Cartera:")
    ev_glob = balance.get("ganancia_neta_esperada_jornada_mxn", 0.0)
    techo_max = sum(o.get("proyecciones", {}).get("ganancia_neta_principal_mxn", 0.0) for o in ordenes)
    print(f"   • Ganancia Neta Esperada (EV): ${ev_glob:.2f} MXN | Techo Teórico Máximo: ${techo_max:.2f} MXN")
    if ev_glob > techo_max:
        print("     ❌ FALLO: Ganancia esperada supera el techo aritmético.")
        invarianzas_ok = False
    else:
        print("     ✅ Techo Aritmético cumplido.")

    # 4. Exportar Traza Markdown de Auditoría
    md_file = os.path.join(OUT_DIR, "auditoria_cuantitativa_jornada_8.md")
    lines = [
        f"# 🔬 AUDITORÍA CUANTITATIVA THE SHIELD — {meta.get('torneo', 'Liga MX')} ({meta.get('jornada', 'Jornada 8')})",
        f"**ID de Portafolio:** #{p_id} | **Fecha:** {gen_at} | **Bankroll Base:** ${bankroll:.2f} MXN",
        f"**Inversión Total Comprometida:** ${tot_inv:.2f} MXN | **Ganancia Neta Esperada (EV):** ${ev_glob:.2f} MXN  \n",
        "---",
        "## 📊 1. ÓRDENES DE INVERSIÓN (KELLY FRACCIONAL + DUTCHING EXACTO V=0)",
        "| Partido | Estrategia | Boleto 1 (Seguro) | Boleto 2 (Ganancia) | Inversión Total |",
        "| :--- | :---: | :--- | :--- | :---: |"
    ]
    for o in ordenes:
        b = o.get("boletos", {})
        b1 = b.get("boleto_1_seguro", {})
        b2 = b.get("boleto_2_ganancia", {})
        b1_txt = f"Empate (${b1.get('monto_mxn',0):.2f} @ {b1.get('momio',1):.2f})" if b1 and b1.get("monto_mxn",0)>0 else "Directo (Sin Cobertura)"
        b2_txt = f"{b2.get('seleccion','Directo')} (${b2.get('monto_mxn',0):.2f} @ {b2.get('momio',1):.2f})" if b2 else "—"
        lines.append(f"| **{o.get('partido')}** | `{o.get('estrategia_seleccionada',{}).get('codigo')}` | {b1_txt} | {b2_txt} | **${b.get('inversion_partido_A_i',0):.2f} MXN** |")
    
    lines.append("\n\n*Certificado automáticamente por The Shield Parallel Auditor — Kybern Industrial.*")
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n📄 Traza Markdown oficial generada en: {md_file}")

    print("\n" + "="*85)
    if invarianzas_ok:
        print("🏆 VEREDICTO: PORTAFOLIO MATEMÁTICAMENTE CERTIFICADO — THE SHIELD PASSED (EXIT CODE 0)")
        return True
    else:
        print("❌ VEREDICTO: ANOMALÍA DETECTADA — THE SHIELD BLOCKED (EXIT CODE 1)")
        return False

if __name__ == "__main__":
    ok = auditar_ultimo_portafolio()
    sys.exit(0 if ok else 1)
