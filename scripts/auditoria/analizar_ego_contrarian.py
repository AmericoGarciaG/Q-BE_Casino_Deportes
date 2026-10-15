# -*- coding: utf-8 -*-
"""
🔬 Q-BE: AUDITORÍA DE SESGO CONTRARIAN (EL TEST DE ARROGANCIA)
[DBBD-FUNGIBLE] — Utilidad ANALÍTICA DE SOLO LECTURA. No muta la bóveda, no emite vetos,
no recalcula ninguna ley de calibración: consume el reporte ya sellado por el Visor.

Clasifica los partidos de la temporada en dos grupos:
1. ALINEADOS: Q-BE y el Mercado tienen el mismo favorito.
2. CONTRARIAN (Arrogantes): Q-BE contradice al favorito del Mercado.

Pregunta fiduciaria: cuando Q-BE se aparta del consenso desmarcado del mercado, ¿compra Alpha
o compra arrogancia? El segmento ALINEADOS mide la calibración compartida; el segmento
CONTRARIAN aísla el valor (o el costo) de la divergencia propia.

Contrato de consumo (cero invención de cifras, [GOVERNANCE-01]):
  GET /api/markets/backtesting/calibration-report?league_id=1   ([ARCH-1.4.38] / [LN-QBE-100])
  `CalibrationMatchOut` PLANO (src/models/web_schemas.py) — decreto VAR-2026-EGO-CONTRARIAN-AUDIT
  §VAR-UI-01 aprobado (sustitución mecánica 1:1 de los nombres anidados de la directiva):
      p_local | p_empate | p_visitante  →  P′ fiduciaria sellada (P_prime)
      q_local | q_empate | q_visitante  →  consenso desmarcado del mercado (q_mkt)
      brier_qbe | brier_mercado         →  error de Brier ya calculado por la bóveda
      tipo_resultado                    →  FAVORITO | EMPATE | UNDERDOG (clasificación factual)
      suficiencia_S_I                   →  0 ⇒ Cold Start (P′ espeja q_mkt): EXCLUIDO del test

Degradación honesta: si la API local no responde, se declara el fallo y se aborta en claro.
Cero cifras sintéticas, cero mocks (`[GOVERNANCE-01]`).

Uso:
    python scripts/auditoria/analizar_ego_contrarian.py
"""

import sys

import httpx

URL_CALIBRACION = (
    "http://127.0.0.1:8000/api/markets/backtesting/calibration-report?league_id=1"
)
TIMEOUT_S = 15.0


def analizar_ego():
    print("📡 Obteniendo datos de calibración...")
    try:
        resp = httpx.get(URL_CALIBRACION, timeout=TIMEOUT_S)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Error conectando a la API local: {e}. Asegúrate de que run_app.py está corriendo.")
        return

    data = resp.json()
    partidos = []
    for j in data.get("jornadas", []):
        partidos.extend(j.get("partidos", []))

    if not partidos:
        print("❌ No hay partidos en la temporada.")
        return

    alineados = []
    contrarian = []
    excluidos_cold_start = 0

    for p in partidos:
        # Ignorar partidos de Cold Start
        if p.get("suficiencia_S_I") == 0:
            excluidos_cold_start += 1
            continue

        # Contrato PLANO del DTO (VAR-UI-01): proyección 1:1 al esquema conceptual del test.
        p_prime = {"L": p["p_local"], "E": p["p_empate"], "V": p["p_visitante"]}
        q_mkt = {"L": p["q_local"], "E": p["q_empate"], "V": p["q_visitante"]}

        # Determinar favorito Q-BE
        fav_qbe = "L"
        max_p = p_prime["L"]
        if p_prime["V"] > max_p:
            fav_qbe = "V"
            max_p = p_prime["V"]

        # Determinar favorito Mercado
        fav_mkt = "L"
        max_q = q_mkt["L"]
        if q_mkt["E"] > max_q:
            fav_mkt = "E"
            max_q = q_mkt["E"]
        if q_mkt["V"] > max_q:
            fav_mkt = "V"

        if fav_qbe == fav_mkt:
            alineados.append(p)
        else:
            contrarian.append(p)

    def reporte_grupo(nombre, grupo):
        if not grupo:
            print(f"\n🔹 GRUPO {nombre}: 0 partidos.")
            return

        bs_qbe = sum(p["brier_qbe"] for p in grupo) / len(grupo)
        bs_mkt = sum(p["brier_mercado"] for p in grupo) / len(grupo)
        alpha = (1.0 - (bs_qbe / bs_mkt)) * 100 if bs_mkt > 0 else 0.0

        # Aciertos: ¿Ganó el favorito de Q-BE?
        aciertos_qbe = sum(1 for p in grupo if p["tipo_resultado"] == "FAVORITO")

        print(f"\n🔹 GRUPO {nombre} ({len(grupo)} partidos):")
        print(f"   Tasa de Acierto Favorito Q-BE : {(aciertos_qbe/len(grupo))*100:.1f}% ({aciertos_qbe} de {len(grupo)})")
        print(f"   Brier Score Q-BE              : {bs_qbe:.4f}")
        print(f"   Brier Score Mercado           : {bs_mkt:.4f}")
        print(f"   Alpha en este segmento        : {alpha:+.2f}%")

    print("\n" + "=" * 60)
    print("📊 RESULTADOS DEL TEST DE ARROGANCIA (EXCLUYENDO J1-J3 COLD START)")
    print("=" * 60)
    reporte_grupo("ALINEADOS AL MERCADO", alineados)
    reporte_grupo("CONTRARIAN (Q-BE CONTRADICE AL MERCADO)", contrarian)
    print("=" * 60)
    print(
        f"Universo evaluado: {len(alineados) + len(contrarian)} partidos · "
        f"excluidos por Cold Start S(I)=0: {excluidos_cold_start}"
    )
    print("=" * 60)


if __name__ == "__main__":
    # Consola Windows: los glifos del reporte exigen UTF-8 (convención de run_app.py).
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    analizar_ego()
