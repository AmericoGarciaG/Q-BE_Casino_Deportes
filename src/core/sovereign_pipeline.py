# -*- coding: utf-8 -*-
"""
🏆 Q-BE SOVEREIGN ENGINE — REGISTRO DE VARIABLES, SUFICIENCIA S(I) Y ORQUESTADOR SOBERANO
[VAULT-CORE-005] Generador Soberano Universal de la Distribución del Partido y Traza Forense.
Base de Gobierno: Kybern Framework v12.0 [ARCH-1.3.4] / Tratado Volumen I (Sección 2.13.1, 4.5, 5.20)

Cableado de Capa 4 (Sprint 3 — erradicación de código muerto [H-16]):
* `[LN-QBE-036]` Operador de Contracción Bayesiana de Forma Reciente → `src/core/sovereign/bayesian_form.py`.
  Interviene en `derivar_factores_estructurales` SOLO cuando el registro fáctico publica `form_10p`.
* `[LN-QBE-020-C]` Kernel H2H Empírico en Eje Localía → `src/core/sovereign/h2h_kernel.py`.
  Interviene en `generar_distribucion_soberana` SOLO cuando el registro publica `h2h_matches` no vacío,
  para derivar Δ_epist contra el consenso Poisson paramétrico (Ley Zero-H2H `[LN-QBE-020-B]` si está vacío).
* Regla de oro: si el registro NO publica estas fuentes, el motor permanece EXACTAMENTE igual
  (ruta analítica sellada `[LN-QBE-035-B]` y Δ_epist = 0.0). Cero invención, cero fabricación de datos.
"""

import math
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

from src.core.intensity_canonical_loglink import estimar_intensidades_loglineal
from src.core.distribution_dixon_coles import calcular_matriz_dixon_coles, colapsar_matriz_a_simplex
from src.core.andre_early_payout import calcular_probabilidad_pago_anticipado

# Capa 4 — Sovereign Memory ([ARCH-1.4.26]): módulos puros, sin I/O ni dependencias de src.storage.
from src.core.sovereign.bayesian_form import contraer_factores_forma_bayesiana
from src.core.sovereign.h2h_kernel import calcular_matriz_h2h_empirica


class StochasticAuditTrace(BaseModel):
    """Traza forense inmutable de la generación de la distribución soberana."""
    match_id: str
    suficiencia_S_I: int = Field(description="1 si satisface datos mínimos, 0 si entra en ignorancia")
    factores_entrada: Dict[str, float]
    intensidades: Dict[str, float]
    distribucion_simplex: Dict[str, float]
    phi_lead2: Dict[str, float]
    matriz_resumen: Dict[str, float]
    # --- Capa 4 (aditivo, cero ruptura de contrato para consumidores previos) ---
    origen_factores: str = Field(
        default="analitico_base",
        description="Procedencia legislada de (A, D): 'analitico_base' [LN-QBE-035-B] o 'bayesiano_10p' [LN-QBE-036].",
    )
    discrepancia_epist: float = Field(
        default=0.0,
        description="Δ_epist ∈ [0,1): distancia de variación total entre el consenso Poisson paramétrico y el Kernel H2H empírico [LN-QBE-020-C].",
    )
    kernel_h2h_empirico: Dict[str, float] = Field(
        default_factory=dict,
        description="Símplex empírico Δ² del Generador C; vacío bajo la Ley Zero-H2H [LN-QBE-020-B] (w_H2H = 0.0, w_Liga = 1.0).",
    )


class SovereignDistributionOutput(BaseModel):
    """Contrato formal de salida de la Capa Probabilística Soberana."""
    match_id: str
    p_local: float
    p_empate: float
    p_visitante: float
    lambda_home: float
    lambda_away: float
    phi_lead2_home: float
    phi_lead2_away: float
    es_operable: bool
    audit_trace: StochasticAuditTrace
    # --- Capa 4 (aditivo, espejo de la traza forense para consumidores directos de la Capa 5) ---
    delta_epist: float = Field(
        default=0.0,
        description="Δ_epist ∈ [0,1) publicado al exterior: 0.0 cuando no hay evidencia H2H [LN-QBE-020-B].",
    )
    origen_factores: str = Field(
        default="analitico_base",
        description="'analitico_base' [LN-QBE-035-B] o 'bayesiano_10p' [LN-QBE-036].",
    )


def evaluar_suficiencia_informativa(raw_match_data: Dict[str, Any]) -> bool:
    """
    [Sección 2.13.1] Evalúa la función indicadora S(I_i) in {0, 1}.
    Requiere al menos 3 partidos jugados por equipo y datos básicos de goles.
    """
    h_data = raw_match_data.get("home_team_stats", {})
    a_data = raw_match_data.get("away_team_stats", {})

    pj_h = int(h_data.get("pj", 0) or 0)
    pj_a = int(a_data.get("pj", 0) or 0)

    if pj_h < 3 or pj_a < 3:
        return False
    return True


def _extraer_bloque_forma_10p(raw_match_data: Dict[str, Any]) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Lectura tolerante del bloque fáctico `form_10p` exigido por [LN-QBE-036].

    Formatos admitidos (misma carga semántica; no se inventan campos):
      * Diccionario: {"home": {...}, "away": {...}}
      * Secuencia:   [{...local...}, {...visita...}]
    Campos por equipo: xg_10p, gf_10p, xga_10p, gc_10p, xg_macro, gf_macro, xga_macro, gc_macro
    y el modificador contextual opcional q_mod.

    Devuelve `None` cuando el registro no publica forma reciente: en ese caso la Capa 4 NO
    interviene y el motor continúa por la ruta analítica sellada [LN-QBE-035-B].
    """
    bloque = raw_match_data.get("form_10p")
    if not bloque:
        return None
    if isinstance(bloque, dict):
        home = bloque.get("home")
        away = bloque.get("away")
        if home is None or away is None:
            return None
        return dict(home), dict(away)
    if isinstance(bloque, (list, tuple)) and len(bloque) >= 2:
        return dict(bloque[0]), dict(bloque[1])
    return None


def _factores_forma_bayesiana(raw_match_data: Dict[str, Any], mu_liga: float) -> Optional[Tuple[float, float, float, float]]:
    """
    [LN-QBE-036] Deriva (A_home, D_away, A_away, D_home) desde la forma reciente (10P) + ancla macro.

    Se consume `a_contraido` (A*) — el factor log-diferencial CONTRAÍDO, pre-amortiguamiento. El
    damping hiperbólico canónico NO se aplica aquí: permanece delegado aguas abajo en
    `estimar_intensidades_loglineal` ([VAULT-CORE-001], κ_damp = 2.5·σ_liga), exactamente como en la
    ruta base [LN-QBE-035-B]. Amortiguar dos veces comprimiría dos veces el mismo factor y rompería
    la comparabilidad entre ambas rutas (evidencia en `BayesianFormResult.a_amortiguado`, disponible
    para auditoría).

    Simetría defensiva: el MISMO operador se aplica al par (xGA, GC) y se invierte el signo, conforme
    a la legislación defensiva [LN-QBE-035-B] (D = −ln(tasa / μ_base)). Cero reglas nuevas.
    Devuelve `None` si el registro no publica `form_10p` (Capa 4 inactiva, ruta base intacta).
    """
    bloque = _extraer_bloque_forma_10p(raw_match_data)
    if bloque is None:
        return None
    home, away = bloque
    q_mod_home = float(home.get("q_mod", 1.0) or 1.0)
    q_mod_away = float(away.get("q_mod", 1.0) or 1.0)

    # 1. Ataque Local (A*_home) y Defensa Local (D*_home, signo legislado)
    a_home = contraer_factores_forma_bayesiana(
        float(home["xg_10p"]), float(home["gf_10p"]),
        float(home["xg_macro"]), float(home["gf_macro"]),
        mu_liga=mu_liga, q_mod=q_mod_home,
    ).a_contraido
    d_home = -contraer_factores_forma_bayesiana(
        float(home["xga_10p"]), float(home["gc_10p"]),
        float(home["xga_macro"]), float(home["gc_macro"]),
        mu_liga=mu_liga, q_mod=q_mod_home,
    ).a_contraido

    # 2. Ataque Visita (A*_away) y Defensa Visita (D*_away, signo legislado)
    a_away = contraer_factores_forma_bayesiana(
        float(away["xg_10p"]), float(away["gf_10p"]),
        float(away["xg_macro"]), float(away["gf_macro"]),
        mu_liga=mu_liga, q_mod=q_mod_away,
    ).a_contraido
    d_away = -contraer_factores_forma_bayesiana(
        float(away["xga_10p"]), float(away["gc_10p"]),
        float(away["xga_macro"]), float(away["gc_macro"]),
        mu_liga=mu_liga, q_mod=q_mod_away,
    ).a_contraido

    return round(a_home, 4), round(d_away, 4), round(a_away, 4), round(d_home, 4)


def derivar_factores_estructurales(raw_match_data: Dict[str, Any], mu_liga: float = 2.65) -> Tuple[float, float, float, float]:
    """
    [Sección 4.5 y 4.6] Convierte métricas de Nivel 1 en factores log-diferenciales centrados en media cero:
    Retorna: (A_home, D_away, A_away, D_home)
    """
    h = raw_match_data.get("home_team_stats", {})
    a = raw_match_data.get("away_team_stats", {})

    pj_h = max(1, int(h.get("pj", 8)))
    pj_a = max(1, int(a.get("pj", 8)))

    mu_base_equipo = max(0.5, mu_liga / 2.0)

    # 1. Ataque Local (Tasa por partido)
    gf_h_per_game = float(h.get("gf", 10)) / pj_h
    xg_total_h = float(h.get("xg", 0.0) or 0.0)
    xg_h_per_game = (xg_total_h / pj_h) if xg_total_h > 5.0 else (xg_total_h or gf_h_per_game)
    att_h_rate = (0.65 * xg_h_per_game) + (0.35 * gf_h_per_game)
    A_home = math.log(max(0.2, att_h_rate) / mu_base_equipo)

    # 2. Defensa Visita (Tasa por partido)
    gc_a_per_game = float(a.get("gc", 12)) / pj_a
    xga_total_a = float(a.get("xga", 0.0) or 0.0)
    xga_a_per_game = (xga_total_a / pj_a) if xga_total_a > 5.0 else (xga_total_a or gc_a_per_game)
    def_a_rate = (0.65 * xga_a_per_game) + (0.35 * gc_a_per_game)
    D_away = -math.log(max(0.2, def_a_rate) / mu_base_equipo)

    # 3. Ataque Visita
    gf_a_per_game = float(a.get("gf", 7)) / pj_a
    xg_total_a = float(a.get("xg", 0.0) or 0.0)
    xg_a_per_game = (xg_total_a / pj_a) if xg_total_a > 5.0 else (xg_total_a or gf_a_per_game)
    att_a_rate = (0.65 * xg_a_per_game) + (0.35 * gf_a_per_game)
    A_away = math.log(max(0.2, att_a_rate) / mu_base_equipo)

    # 4. Defensa Local
    gc_h_per_game = float(h.get("gc", 10)) / pj_h
    xga_total_h = float(h.get("xga", 0.0) or 0.0)
    xga_h_per_game = (xga_total_h / pj_h) if xga_total_h > 5.0 else (xga_total_h or gc_h_per_game)
    def_h_rate = (0.65 * xga_h_per_game) + (0.35 * gc_h_per_game)
    D_home = -math.log(max(0.2, def_h_rate) / mu_base_equipo)

    # [SPRINT 3 / H-16] Capa 4 — Capa 4 ([LN-QBE-036]): si el registro fáctico publica `form_10p`,
    # el operador bayesiano sellado SUSTITUYE de forma gobernada la mezcla analítica base; si no,
    # se conserva la ruta sellada [LN-QBE-035-B] sin una sola variación.
    factores_bayesianos = _factores_forma_bayesiana(raw_match_data, mu_liga)
    if factores_bayesianos is not None:
        return factores_bayesianos
    return round(A_home, 4), round(D_away, 4), round(A_away, 4), round(D_home, 4)


def derivar_factores_con_procedencia(
    raw_match_data: Dict[str, Any], mu_liga: float = 2.65
) -> Tuple[Tuple[float, float, float, float], str]:
    """
    Envoltorio trazable de `derivar_factores_estructurales`: publica los factores y su PROCEDENCIA
    legislada ('bayesiano_10p' [LN-QBE-036] o 'analitico_base' [LN-QBE-035-B]) para la traza forense.
    """
    if _extraer_bloque_forma_10p(raw_match_data) is not None:
        return derivar_factores_estructurales(raw_match_data, mu_liga), "bayesiano_10p"
    return derivar_factores_estructurales(raw_match_data, mu_liga), "analitico_base"


def derivar_discrepancia_epistemica(
    distribucion_parametrica: Dict[str, float],
    h2h_matches: Optional[Any] = None,
) -> Tuple[float, Dict[str, float]]:
    """
    [LN-QBE-020-C] Δ_epist — discrepancia entre el consenso Poisson paramétrico y el Kernel H2H empírico.

    Métrica legislada: distancia de variación total (media L1) sobre el símplex Δ²
        Δ_epist = ½ · (|p_local − q_local| + |p_empate − q_empate| + |p_visitante − q_visita|) ∈ [0, 1).
    Es invariante ante la permutación de etiquetas, no amplifica ruido y se anula exactamente en la
    coincidencia perfecta (Δ_epist = 0 ⟺ ambos generadores publican el mismo símplex); la frontera de
    cuarentena fiduciaria τ_disp = 0.12 ([LN-QBE-070-B]) se evalúa aguas abajo, no aquí.

    Ley Zero-H2H ([LN-QBE-020-B]): sin enfrentamientos directos ⇒ w_H2H = 0.0, w_Liga = 1.0 y
    Δ_epist = 0.0. El kernel NO se invoca con evidencia vacía (jamás se fabrican partidos sintéticos).

    Devuelve (Δ_epist, evidencia_del_Generador_C) para la traza forense.
    """
    partidos = list(h2h_matches or [])
    if not partidos:
        return 0.0, {"peso_h2h": 0.0, "peso_liga": 1.0}

    kernel = calcular_matriz_h2h_empirica(partidos)
    delta_epist = 0.5 * (
        abs(float(distribucion_parametrica["p_local"]) - kernel.p_local)
        + abs(float(distribucion_parametrica["p_empate"]) - kernel.p_empate)
        + abs(float(distribucion_parametrica["p_visitante"]) - kernel.p_visita)
    )
    return round(delta_epist, 6), {
        "p_local": round(kernel.p_local, 6),
        "p_empate": round(kernel.p_empate, 6),
        "p_visita": round(kernel.p_visita, 6),
        "peso_total_efectivo": round(kernel.peso_total_efectivo, 6),
    }


def generar_distribucion_soberana(
    match_id: str,
    raw_match_data: Dict[str, Any],
    mu_liga: float = 2.65,
    gamma_home_base: float = 0.15,
    delta_alt_metros: float = 0.0,
    delta_descanso_dias: float = 0.0,
    q_mod_h: float = 1.0,
    q_mod_a: float = 1.0,
    rho: float = -0.05
) -> SovereignDistributionOutput:
    """
    [TRATADO VOLUMEN I] Generador Soberano Universal de la Distribución del Partido.
    Pipeline completo: Datos -> S(I) -> Factores -> Intensidades acotadas -> Dixon-Coles 2D -> André -> Simplex.
    """
    # 1. Comprobación de Suficiencia Fáctica S(I_i)
    if not evaluar_suficiencia_informativa(raw_match_data):
        trace_insuf = StochasticAuditTrace(
            match_id=match_id,
            suficiencia_S_I=0,
            factores_entrada={},
            intensidades={"lambda_h": 1.325, "lambda_a": 1.325},
            distribucion_simplex={"p_1": 0.3333, "p_X": 0.3333, "p_2": 0.3334},
            phi_lead2={"phi_h": 0.0, "phi_a": 0.0},
            matriz_resumen={}
        )
        return SovereignDistributionOutput(
            match_id=match_id,
            p_local=0.3333, p_empate=0.3333, p_visitante=0.3334,
            lambda_home=1.325, lambda_away=1.325,
            phi_lead2_home=0.0, phi_lead2_away=0.0,
            es_operable=False,
            audit_trace=trace_insuf
        )

    # 2. Derivación de Factores Estructurales (procedencia legislada publicada por Capa 4)
    (A_h, D_a, A_a, D_h), origen_factores = derivar_factores_con_procedencia(raw_match_data, mu_liga)

    # 3. Estimación de Intensidades con Ligadura de alpha y Damping tanh
    lh, la = estimar_intensidades_loglineal(
        A_home=A_h, D_away=D_a,
        A_away=A_a, D_home=D_h,
        mu_liga=mu_liga, gamma_home_base=gamma_home_base,
        delta_alt_metros=delta_alt_metros,
        delta_descanso_dias=delta_descanso_dias,
        q_mod_h=q_mod_h, q_mod_a=q_mod_a
    )

    # 4. Construcción de la Matriz Conjunta Dixon-Coles 2D
    matriz_2d = calcular_matriz_dixon_coles(lambda_h=lh, lambda_a=la, rho=rho, k_max=6)

    # 5. Colapso Geométrico al Símplex Delta^2
    p1, pX, p2 = colapsar_matriz_a_simplex(matriz_2d)

    # 6. Evaluación de la Cláusula de Pago Anticipado (Operador de André en O(1))
    phi_h = calcular_probabilidad_pago_anticipado(matriz_2d, es_local=True)
    phi_a = calcular_probabilidad_pago_anticipado(matriz_2d, es_local=False)

    # 7. [LN-QBE-020-C] Δ_epist: consenso Poisson paramétrico vs Kernel H2H empírico.
    #    Ley Zero-H2H ([LN-QBE-020-B]): sin enfrentamientos directos ⇒ w_H2H = 0.0, w_Liga = 1.0
    #    y Δ_epist = 0.0 (el kernel jamás se invoca con evidencia vacía).
    delta_epist, kernel_h2h = derivar_discrepancia_epistemica(
        {"p_local": p1, "p_empate": pX, "p_visitante": p2},
        raw_match_data.get("h2h_matches"),
    )

    # 8. Consolidación de Traza Forense
    trace = StochasticAuditTrace(
        match_id=match_id,
        suficiencia_S_I=1,
        factores_entrada={"A_home": A_h, "D_away": D_a, "A_away": A_a, "D_home": D_h},
        intensidades={"lambda_home": lh, "lambda_away": la, "ratio": round(lh / la, 2)},
        distribucion_simplex={"p_1": p1, "p_X": pX, "p_2": p2},
        phi_lead2={"phi_home": phi_h, "phi_away": phi_a},
        matriz_resumen={"0_0": round(matriz_2d[0][0], 4), "1_0": round(matriz_2d[1][0], 4), "1_1": round(matriz_2d[1][1], 4)},
        origen_factores=origen_factores,
        discrepancia_epist=delta_epist,
        kernel_h2h_empirico=kernel_h2h
    )

    return SovereignDistributionOutput(
        match_id=match_id,
        p_local=p1, p_empate=pX, p_visitante=p2,
        lambda_home=lh, lambda_away=la,
        phi_lead2_home=phi_h, phi_lead2_away=phi_a,
        es_operable=True,
        audit_trace=trace,
        delta_epist=delta_epist,
        origen_factores=origen_factores
    )
