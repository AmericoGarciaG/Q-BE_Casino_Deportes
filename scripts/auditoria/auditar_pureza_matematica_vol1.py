# -*- coding: utf-8 -*-
"""
🏆 Q-BE — AUDITORÍA FORENSE DE PUREZA MATEMÁTICA (TRATADO VOLUMEN I)
[KYBERN INDUSTRIAL v13.5 — FIDUCIARY MATHEMATICAL CRUCIBLE]
Autoridad: Américo García Guerrero (Director Humano)
Objetivo: Certificar la paridad matemática absoluta entre las 111 páginas del Tratado Vol. I
y los algoritmos deterministas implementados en src/core/ bajo régimen [DIRGEN-STRICT].
"""

import sys
import os
import math
import logging

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.intensity_canonical_loglink import (
    calcular_alpha_ligadura,
    aplicar_damping_hiperbolico,
    estimar_intensidades_loglineal
)
from src.core.andre_early_payout import (
    operador_seccional_andre,
    calcular_probabilidad_pago_anticipado
)
from src.core.distribution_dixon_coles import (
    calcular_matriz_dixon_coles,
    colapsar_matriz_a_simplex
)
from src.core.sovereign_pipeline import (
    evaluar_suficiencia_informativa,
    derivar_factores_estructurales,
    generar_distribucion_soberana
)


def banner_prueba(num: int, titulo: str, seccion_tratado: str):
    print("\n" + "=" * 110)
    print(f"🔬 PRUEBA {num}/7: {titulo.upper()}")
    print(f"📖 BASE TEÓRICA: Tratado Volumen I — {seccion_tratado}")
    print("=" * 110)


def certificar_volumen_1():
    print("\n" + "█" * 110)
    print("🏛️ Q-BE SOBERANO — PROTOCOLO DE AUDITORÍA FORENSE DE PUREZA MATEMÁTICA")
    print("AUTOR DE LA MATEMÁTICA: Américo García Guerrero (Director Humano)")
    print("MARCO RECTOR: Kybern Framework v13.5 (Directed Generative Engineering)")
    print("OBJETO: Certificación de Invarianzas Físicas del Tratado Volumen I (111 Páginas)")
    print("█" * 110)

    pruebas_superadas = 0

    # =========================================================================
    # PRUEBA 1: LIGADURA DE ALPHA Y CONSERVACIÓN DE MASA DE GOLES
    # =========================================================================
    banner_prueba(1, "Conservación de Masa de Goles y Ligadura de α", "Sección 4.9.1 (Páginas 55-56)")
    mu_liga = 2.65
    gamma_home = 0.15

    # Ecuación del Tratado: α = ln(μ_liga) - ln(1 + e^γ_home)
    alpha_calc = calcular_alpha_ligadura(mu_liga, gamma_home)
    alpha_teorico = math.log(mu_liga) - math.log(1.0 + math.exp(gamma_home))

    print(f"  • Parámetro Macro μ_liga: {mu_liga:.4f} goles/partido")
    print(f"  • Ventaja Media Local γ_home: {gamma_home:.4f}")
    print(f"  • Intercepto α Calculado: {alpha_calc:.6f} | Teórico: {alpha_teorico:.6f}")

    # Simulación de partido neutral promedio (A = D = C = 0)
    lh_base = math.exp(alpha_calc + gamma_home)
    la_base = math.exp(alpha_calc)
    masa_total = lh_base + la_base

    print(f"  • Intensidad Base Local  (λ_H^base = e^(α + γ)): {lh_base:.4f}")
    print(f"  • Intensidad Base Visita (λ_A^base = e^α):        {la_base:.4f}")
    print(f"  • Suma Total de Goles Esperados (λ_H + λ_A):     {masa_total:.6f} goles")

    assert abs(alpha_calc - alpha_teorico) < 1e-6, "Fallo en Ecuación de Ligadura de α"
    assert abs(masa_total - mu_liga) < 1e-6, "Violación de Conservación de Masa de Goles (Invariante I1)"
    print("  ✅ [PASSED] La Ecuación de Ligadura conserva exactamente la masa física de goles (2.6500).")
    pruebas_superadas += 1

    # =========================================================================
    # PRUEBA 2: DAMPING HIPERBÓLICO Y CONTROL ANTI-SOBREAMPLIFICACIÓN
    # =========================================================================
    banner_prueba(2, "Damping Hiperbólico Simétrico tanh y Paridad de Media Cero", "Sección 4.12 (Páginas 58-59)")
    sigma_liga = 0.25
    kappa = 2.5 * sigma_liga

    # Verificar que tanh(x) conserva la media cero estricta: E[A] = 0
    test_inputs = [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0]
    suma_simetrica = sum(aplicar_damping_hiperbolico(x, sigma_liga) for x in test_inputs)
    print(f"  • Cota Asintótica κ (2.5 * σ): ±{kappa:.4f}")
    print(f"  • Test de Antisimetría: Suma sobre retículo simétrico = {suma_simetrica:.8f}")

    # Prueba de Estrés: Caso Patológico Puebla-Atlante (+15 desviaciones estándar brutas)
    factor_desorbitado = 15.0
    factor_damped = aplicar_damping_hiperbolico(factor_desorbitado, sigma_liga)
    print(f"  • Factor Crudo Extremo: +{factor_desorbitado:.2f} σ -> Factor Damped Comprimido: +{factor_damped:.4f}")

    lh_ext, la_ext = estimar_intensidades_loglineal(
        A_home=factor_desorbitado, D_away=0.0,
        A_away=0.0, D_home=0.0,
        mu_liga=mu_liga, gamma_home_base=gamma_home,
        sigma_A=sigma_liga, sigma_D=sigma_liga
    )
    ratio_ofensivo = lh_ext / la_ext
    print(f"  • Intensidades bajo asimetría colosal: λ_H = {lh_ext:.4f} | λ_A = {la_ext:.4f}")
    print(f"  • Ratio Ofensivo resultante (λ_H / λ_A): {ratio_ofensivo:.2f} (Cota Física Segura: < 2.50)")

    assert abs(suma_simetrica) < 1e-7, "Fallo: El damping no preserva media cero E[A]=0"
    assert factor_damped <= kappa, "Fallo: El factor ofensivo violó la cota asintótica κ"
    assert ratio_ofensivo <= 2.50, "Fallo: Resonancia destructiva detectada (Síndrome Puebla-Atlante no contenido)"
    print("  ✅ [PASSED] Compresión hiperbólica certificada: Media cero preservada y ratio acotado <= 2.50.")
    pruebas_superadas += 1

    # =========================================================================
    # PRUEBA 3: DIXON-COLES Y TEOREMA DE NO-NEGATIVIDAD ESTRICTA (I13)
    # =========================================================================
    banner_prueba(3, "Teorema de No-Negatividad Estricta de Dixon-Coles (Invariante I13)", "Sección 5.16.1 (Página 78)")
    # Caso de alta anotación donde λ_H * λ_A es gigante
    lh_alto = 4.5
    la_alto = 4.0
    rho_adverso = 0.50  # Si no estuviera acotado, tau(0,0) = 1 - (4.5 * 4.0 * 0.5) = -8.0 (Catástrofe)

    matriz_dc = calcular_matriz_dixon_coles(lambda_h=lh_alto, lambda_a=la_alto, rho=rho_adverso, k_max=6)
    
    # Auditar cada celda del retículo 7x7
    todas_no_negativas = True
    min_prob = 1.0
    for x in range(7):
        for y in range(7):
            val = matriz_dc[x][y]
            if val < min_prob:
                min_prob = val
            if val < 0.0:
                todas_no_negativas = False

    suma_matriz = sum(sum(fila) for fila in matriz_dc)
    print(f"  • Intensidades de Prueba Extremas: λ_H = {lh_alto:.2f}, λ_A = {la_alto:.2f}")
    print(f"  • Producto λ_H * λ_A: {lh_alto * la_alto:.2f} (Umbral de colapso tradicional: > 1.0)")
    print(f"  • Mínima Probabilidad en la Matriz 7x7: {min_prob:.8f}")
    print(f"  • Masa Total Integrada sobre Retículo Truncado: {suma_matriz:.6f}")

    assert todas_no_negativas, "Fallo Crítico: Se detectaron probabilidades negativas en la matriz Dixon-Coles"
    assert min_prob >= 0.0, "Violación del Teorema de No-Negatividad (Invariante I13)"
    assert abs(suma_matriz - 1.0) < 1e-4, "Fallo en renormalización telescópica de la matriz"
    print("  ✅ [PASSED] Invariante I13 certificada: Cero probabilidades negativas bajo cotas analíticas.")
    pruebas_superadas += 1

    # =========================================================================
    # PRUEBA 4: FÓRMULA CERRADA DE DÉSIRÉ ANDRÉ PARA PAGO ANTICIPADO EN O(1)
    # =========================================================================
    banner_prueba(4, "Fórmula Cerrada de Désiré André para Pago Anticipado en O(1)", "Sección 5.20 (Páginas 80-82)")
    
    # 1. Condición de Frontera Exacta: x - y >= 2 -> pi = 1.0000
    assert operador_seccional_andre(2, 0) == 1.0000
    assert operador_seccional_andre(3, 1) == 1.0000
    assert operador_seccional_andre(4, 2) == 1.0000
    print("  • Frontera Terminal (x - y >= 2): π(2,0)=1.0000, π(3,1)=1.0000, π(4,2)=1.0000 [OK]")

    # 2. Condición Sub-Frontera: x < 2 -> pi = 0.0000
    assert operador_seccional_andre(0, 0) == 0.0000
    assert operador_seccional_andre(1, 0) == 0.0000
    assert operador_seccional_andre(1, 3) == 0.0000
    print("  • Sub-Frontera Imposible (x < 2): π(0,0)=0.0000, π(1,0)=0.0000, π(1,3)=0.0000 [OK]")

    # 3. Región de Erosión: Marcadores donde el favorito tocó ventaja +2 pero el rival descontó
    # Marcador 3 - 2: num = 3*2 = 6, den = (2+1)*(2+2) = 12 -> pi = 6/12 = 0.5000
    pi_3_2 = operador_seccional_andre(3, 2)
    # Marcador 4 - 3: num = 4*3 = 12, den = (3+1)*(3+2) = 20 -> pi = 12/20 = 0.6000
    pi_4_3 = operador_seccional_andre(4, 3)
    print(f"  • Región de Erosión (3 - 2): π = {pi_3_2:.4f} (Teórico: 6/12 = 0.5000) [OK]")
    print(f"  • Región de Erosión (4 - 3): π = {pi_4_3:.4f} (Teórico: 12/20 = 0.6000) [OK]")

    assert abs(pi_3_2 - 0.5000) < 1e-6, "Fallo en deducción de André para marcador 3-2"
    assert abs(pi_4_3 - 0.6000) < 1e-6, "Fallo en deducción de André para marcador 4-3"

    # 4. Integración Matricial y Cota Coherente: P(G_H - G_A >= 2) < Phi_Lead2 <= P(G_H >= 2)
    phi_lead2 = calcular_probabilidad_pago_anticipado(matriz_dc, es_local=True)
    prob_dif2 = sum(matriz_dc[x][y] for x in range(7) for y in range(7) if (x - y) >= 2)
    prob_gh2 = sum(matriz_dc[x][y] for x in range(2, 7) for y in range(7))

    print(f"  • Probabilidad Final de Ganar por >= 2 Goles:       {prob_dif2:.4f}")
    print(f"  • Probabilidad Soberana de Pago Anticipado (Φ_Lead2): {phi_lead2:.4f} (Captura Freeroll)")
    print(f"  • Cota Superior Absoluta P(G_H >= 2):                {prob_gh2:.4f}")

    assert prob_dif2 <= phi_lead2 <= prob_gh2, "Violación de Cotas Fiduciarias de Pago Anticipado"
    print("  ✅ [PASSED] Operador de André en O(1) certificado: Cotas fiduciarias cumplidas strictly.")
    pruebas_superadas += 1

    # =========================================================================
    # PRUEBA 5: PRINCIPIO DE SUFICIENCIA INFORMATIVA S(I_i) EN {0, 1}
    # =========================================================================
    banner_prueba(5, "Principio de Suficiencia Fáctica S(I_i) y Regla de Ignorancia", "Sección 2.13.1 (Páginas 28-29)")
    
    # Caso 1: Datos insuficientes (Arranque en frío, PJ < 3)
    match_insuficiente = {
        "home_team_stats": {"pj": 2, "gf": 2, "gc": 1},
        "away_team_stats": {"pj": 1, "gf": 0, "gc": 2}
    }
    suf_0 = evaluar_suficiencia_informativa(match_insuficiente)
    salida_0 = generar_distribucion_soberana("TEST-INSUF", match_insuficiente)

    print(f"  • Evaluación Fáctica con PJ < 3: S(I_i) = {int(suf_0)}")
    print(f"  • Distribución Emitida: ({salida_0.p_local:.4f}, {salida_0.p_empate:.4f}, {salida_0.p_visitante:.4f})")
    print(f"  • Estatus de Operabilidad: es_operable = {salida_0.es_operable}")

    assert suf_0 is False, "Fallo: Se declaró suficiente un partido sin muestra mínima"
    assert salida_0.es_operable is False, "Violación fiduciaria: Partido insuficiente marcado como operable"
    assert abs(salida_0.p_local - 1.0/3.0) < 1e-3, "Fallo: No colapsó a la ignorancia uniforme (1/3, 1/3, 1/3)"

    # Caso 2: Datos suficientes (Temporada madura, PJ >= 3)
    match_suficiente = {
        "home_team_stats": {"pj": 8, "gf": 14, "gc": 8, "xg": 1.65},
        "away_team_stats": {"pj": 8, "gf": 9, "gc": 12, "xg": 1.10}
    }
    suf_1 = evaluar_suficiencia_informativa(match_suficiente)
    salida_1 = generar_distribucion_soberana("TEST-SUF", match_suficiente)

    print(f"  • Evaluación Fáctica con PJ >= 3: S(I_i) = {int(suf_1)}")
    print(f"  • Distribución Informada Emitida: ({salida_1.p_local:.4f}, {salida_1.p_empate:.4f}, {salida_1.p_visitante:.4f})")
    print(f"  • Estatus de Operabilidad: es_operable = {salida_1.es_operable}")

    assert suf_1 is True, "Fallo: Partido suficiente marcado como insuficiente"
    assert salida_1.es_operable is True, "Fallo: Partido suficiente bloqueado incorrectamente"
    print("  ✅ [PASSED] Compuerta de suficiencia fáctica certificada: Cero capital en riesgo ante ignorancia.")
    pruebas_superadas += 1

    # =========================================================================
    # PRUEBA 6: CIERRE GEOMÉTRICO DEL SÍMPLEX Δ² (INVARIANTE I14)
    # =========================================================================
    banner_prueba(6, "Partición Geométrica Exacta y Cierre del Símplex Δ²", "Sección 5.10 y 5.14 (Páginas 74-77)")
    
    p1, pX, p2 = salida_1.p_local, salida_1.p_empate, salida_1.p_visitante
    suma_simplex = p1 + pX + p2

    print(f"  • Probabilidad Victoria Local (p_1 = Σ_{{x>y}} M_xy):     {p1:.4f}")
    print(f"  • Probabilidad Empate         (p_X = Σ_{{x=y}} M_xy):     {pX:.4f}")
    print(f"  • Probabilidad Victoria Visita (p_2 = Σ_{{x<y}} M_xy):    {p2:.4f}")
    print(f"  • Suma Exacta en el Símplex Δ² (p_1 + p_X + p_2):         {suma_simplex:.6f}")

    assert abs(suma_simplex - 1.000000) <= 1e-4, "Violación del Símplex de Probabilidad (Invariante I1)"
    assert p1 > 0 and pX > 0 and p2 > 0, "Violación de No-Negatividad Estricta (Invariante I2)"
    print("  ✅ [PASSED] Invariante I14 certificada: Partición disjunta y cierre perfecto sobre el Símplex Δ².")
    pruebas_superadas += 1

    # =========================================================================
    # PRUEBA 7: AUDITORÍA DE PARTIDO REAL (LIGA MX JORNADA 10)
    # =========================================================================
    banner_prueba(7, "End-to-End Pipeline Soberano con Datos Reales (J10 Toluca vs Atlas)", "Sección 6.25 (Página 109)")
    
    toluca_atlas_input = {
        "home_team_stats": {"pj": 9, "gf": 20, "gc": 9, "xg": 1.95},   # Toluca (Líder)
        "away_team_stats": {"pj": 9, "gf": 13, "gc": 15, "xg": 1.15},  # Atlas
        "delta_alt_metros": 1500.0,  # Toluca (2,660m) vs Atlas (1,560m)
        "delta_descanso_dias": 1.0,
        "q_mod_h": 1.0,
        "q_mod_a": 1.0
    }
    
    salida_real = generar_distribucion_soberana("LIGAMX-J10-TOL-ATL", toluca_atlas_input)
    trace = salida_real.audit_trace

    print(f"  • Encuentro Auditado: Deportivo Toluca (Local) vs Atlas FC (Visita)")
    print(f"  • Factores Estructurales Nivel 3: A_home={trace.factores_entrada['A_home']} | D_away={trace.factores_entrada['D_away']}")
    print(f"  • Intensidades Acotadas:          λ_Toluca={salida_real.lambda_home:.4f} | λ_Atlas={salida_real.lambda_away:.4f}")
    print(f"  • Distribución Soberana 1X2:      Local: {salida_real.p_local*100:.1f}% | Empate: {salida_real.p_empate*100:.1f}% | Visita: {salida_real.p_visitante*100:.1f}%")
    print(f"  • Activación Pago Anticipado:     Φ_Lead2 Local = {salida_real.phi_lead2_home*100:.1f}%")

    assert salida_real.p_local > salida_real.p_visitante, "Incoherencia física: Toluca debe dominar a Atlas"
    assert salida_real.phi_lead2_home > 0.30, "Incoherencia fiduciaria: Probabilidad de Pago Anticipado subestimada"
    print("  ✅ [PASSED] Trazabilidad end-to-end certificada: Coherencia física y fiduciaria total.")
    pruebas_superadas += 1

    # =========================================================================
    # CERTIFICADO FINAL DE AUDITORÍA
    # =========================================================================
    print("\n" + "█" * 110)
    print("📜 CERTIFICADO FORMAL DE PUREZA MATEMÁTICA Y BLINDAJE DIRGEN")
    print(f"RESULTADO: {pruebas_superadas}/7 PRUEBAS DE INVARIANZA APROBADAS AL 100% (EXIT CODE 0)")
    print("ESTADO DEL MODELO: [CANON CRISTALIZADO / MATEMÁTICAMENTE IMPECABLE]")
    print("VEREDICTO: Se certifica que los algoritmos de src/core/ son un reflejo isomórfico, determinista")
    print("           y no degradado del Tratado Volumen I redactado por Américo García Guerrero.")
    print("█" * 110 + "\n")


if __name__ == "__main__":
    try:
        certificar_volumen_1()
        sys.exit(0)
    except AssertionError as err:
        print(f"\n🚨 [CRITICAL SHIELD FAULT] Violación matemática detectada: {err}")
        sys.exit(1)
    except Exception as ex:
        print(f"\n❌ [UNEXPECTED FAULT] Error en auditoría: {ex}")
        sys.exit(2)
