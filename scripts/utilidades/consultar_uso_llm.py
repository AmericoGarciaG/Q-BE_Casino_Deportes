# -*- coding: utf-8 -*-
"""
Kybern Industrial — Monitor de Salud de Llaves Gemini y Consumo de Tokens
Base de Gobierno: Kybern Framework v12.0
"""
import os
import sys
import time
import httpx
import sqlite3

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import functools
print = functools.partial(print, flush=True)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "qbe_database.db")

def auditar_llaves_y_consumo():
    print("\n" + "="*85)
    print("🧠 [MONITOR LLM] AUDITORÍA DE LLAVES GEMINI Y REGISTRO DE TOKENS")
    print("="*85)

    keys = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Gemini_API_4_QBE_") or line.startswith("GEMINI_API_KEY"):
                    k, v = line.split("=", 1)
                    keys.append((k.strip(), v.strip().strip("'").strip('"')))

    print(f"🔑 Llaves detectadas en .env: {len(keys)}")
    print("-" * 85)
    print(f"{'ALIAS':<25} | {'ESTADO EN VIVO (PROBE HTTP)':<35} | {'LATENCIA'}")
    print("-" * 85)

    base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

    for alias, key in keys:
        t0 = time.perf_counter()
        try:
            with httpx.Client(timeout=8.0) as client:
                r = client.post(
                    f"{base_url}?key={key}",
                    json={"contents": [{"parts": [{"text": "ping"}]}], "generationConfig": {"maxOutputTokens": 1}}
                )
                lat = (time.perf_counter() - t0) * 1000.0
                if r.status_code == 200:
                    status = "✅ VIVA (200 OK - Lista para Inferencia)"
                elif r.status_code == 429:
                    status = "⚠️ SATURADA (429 Rate Limit Exceeded)"
                else:
                    status = f"❌ ERROR HTTP {r.status_code}"
                print(f"{alias:<25} | {status:<35} | {lat:.0f} ms")
        except Exception as e:
            print(f"{alias:<25} | ❌ ERROR CONEXIÓN: {str(e)[:30]} | —")

    print("-" * 85)
    # Consultar SQLite Ledger
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*), SUM(prompt_tokens), SUM(candidates_tokens), SUM(cost_usd) FROM llm_token_ledger")
            row = cur.fetchone()
            llamadas = row[0] or 0
            p_tok = row[1] or 0
            c_tok = row[2] or 0
            cost = row[3] or 0.0
            print(f"\n📊 HISTORIAL EN BD (llm_token_ledger):")
            print(f" • Llamadas registradas: {llamadas}")
            print(f" • Tokens Prompt: {p_tok:,} | Tokens Candidates: {c_tok:,} | Total: {p_tok+c_tok:,}")
            print(f" • Costo Acumulado Estimado: ${cost:.6f} USD")
        except Exception as ex:
            print(f"Tabla llm_token_ledger aún vacía o no creada: {ex}")
        finally:
            conn.close()
    print("="*85 + "\n")

if __name__ == "__main__":
    auditar_llaves_y_consumo()
