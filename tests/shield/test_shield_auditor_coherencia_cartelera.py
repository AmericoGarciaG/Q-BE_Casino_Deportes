# -*- coding: utf-8 -*-
"""
🛡️ JUEZ INMUTABLE: [ARCH-1.4.34] SONDA DIAGNÓSTICA DE COHERENCIA RELACIONAL
Y PRE-VUELO DEL CONSTRUCTOR (CLI AUDITOR)

Base de Gobierno: `docs/ARCH.md` (`[ARCH-1.4.34]`), `docs/CONSTANTS.md` (`OVERROUND_MIN/MAX_ADMISIBLE`,
`[LN-QBE-007-H]`), `docs/LOGIC.md` (`[LN-QBE-040-B]`, `[LN-QBE-071-B]`, `[LN-QBE-060-B]`).
Régimen: utilidad `Read-Only` (`[DBBD-FUNGIBLE]`); sus cotas numéricas son `[DIRGEN-STRICT]`.

Invariantes auditadas:
  1. Aduana de Overround anclada a las constantes canónicas selladas [0.8500, 1.3000] + banda de
     vigilancia diagnóstica (1.25, 1.30] — la sonda JAMÁS contradice la aduana de `[LN-QBE-007-H]`.
  2. Piso de ventanilla ($2.00) y piso bivariado ($4.00) de `[LN-QBE-071-B]` en familias con cobertura.
  3. Techo de goles (2.20 xG) con banda de vigilancia anti-resonancia (1.86, 2.20] de `[LN-QBE-040-B]`
     + degradación honesta (`SIN VEREDICTO`, cero veto fabricado) ante evidencia ausente.
  4. Coherencia Capa 0 vs. estrategia declarada (cotejo con el triaje canónico), divergencia de
     mercado (TVD ≤ 0.22) y contrato de salida del CLI (`--check` falla sólo ante 🔴).
"""

from pathlib import Path

RUTA_CONSTANTES = Path("docs/CONSTANTS.md")


# ---------------------------------------------------------------------------
# 1. [LN-QBE-007-H] ADUANA DE OVERROUND ANCLADA A LAS CONSTANTES CANÓNICAS
# ---------------------------------------------------------------------------
def test_invarianza_aduana_overround_anclada_a_constantes_canonicas():
    """Las cotas de la sonda son las constantes selladas, no invenciones locales."""
    from scripts.auditoria.auditar_coherencia_cartelera import (
        OVERROUND_MAX_ADMISIBLE,
        OVERROUND_MIN_ADMISIBLE,
        OVERROUND_VIGILANCIA_MAX,
        NivelSeveridad,
        auditar_coherencia_partido,
    )

    # -- Anclaje legislativo: los valores deben existir en el Libro de Constantes --
    assert RUTA_CONSTANTES.exists(), "Falta docs/CONSTANTS.md (bóveda de constantes)"
    libro = RUTA_CONSTANTES.read_text(encoding="utf-8")
    assert f"{OVERROUND_MIN_ADMISIBLE:.4f}" in libro, "S_min no coincide con CONSTANTS.md"
    assert f"{OVERROUND_MAX_ADMISIBLE:.4f}" in libro, "S_max no coincide con CONSTANTS.md"
    assert (OVERROUND_MIN_ADMISIBLE, OVERROUND_MAX_ADMISIBLE) == (0.85, 1.30)
    assert OVERROUND_MIN_ADMISIBLE < OVERROUND_VIGILANCIA_MAX <= OVERROUND_MAX_ADMISIBLE

    def nivel(momios):
        reporte = auditar_coherencia_partido(
            {"id_partido": "TEST-OVERROUND", "momios": {"L": momios[0], "E": momios[1], "V": momios[2]}}
        )
        return next(h for h in reporte.hallazgos if h.sonda == "overround_comercial").nivel

    # S = 1.0570 (mercado real Liga MX J11): margen comercial sano ⇒ CERTIFICA
    assert nivel((2.98, 3.40, 2.34)) == NivelSeveridad.CONFORME

    # S = 1.2823: dentro de la aduana canónica pero en banda de vigilancia ⇒ ADVIERTE, no veta
    assert nivel((1.60, 3.20, 2.90)) == NivelSeveridad.ADVERTENCIA

    # S = 0.9744: margen no positivo (posible arbitraje / captura corrupta) ⇒ ADVIERTE
    assert nivel((2.60, 3.90, 3.00)) == NivelSeveridad.ADVERTENCIA

    # S = 1.3704 ⇒ DISCREPANCIA (cuota usuraria o mercado suspendido)
    assert nivel((1.50, 3.00, 2.70)) == NivelSeveridad.DISCREPANCIA

    # S = 0.6061 (el caso del Juez de Varianza: 4.95 × 4.95) ⇒ DISCREPANCIA
    assert nivel((4.95, 4.95, 4.95)) == NivelSeveridad.DISCREPANCIA


# ---------------------------------------------------------------------------
# 2. [LN-QBE-071] / [LN-QBE-071-B] PISO DE VENTANILLA Y PISO BIVARIADO
# ---------------------------------------------------------------------------
def test_invarianza_piso_bivariado_de_4_mxn_en_familias_con_cobertura():
    """Ningún boleto < $2.00 y ninguna posición con seguro+ataque < $4.00 MXN."""
    from scripts.auditoria.auditar_coherencia_cartelera import (
        FAMILIAS_CON_COBERTURA,
        PISO_BIVARIADO_MXN,
        PISO_VENTANILLA_MXN,
        NivelSeveridad,
        auditar_coherencia_partido,
    )

    assert (PISO_VENTANILLA_MXN, PISO_BIVARIADO_MXN) == (2.00, 4.00)
    assert set(FAMILIAS_CON_COBERTURA) == {"QBE-H1", "QBE-H2", "QBE-R1", "QBE-R2", "QBE-C1"}

    def nivel(codigo, boletos):
        reporte = auditar_coherencia_partido(
            {"id_partido": "TEST-PISO", "estrategia_codigo": codigo, "boletos": boletos}
        )
        return next(h for h in reporte.hallazgos if h.sonda == "piso_ventanilla").nivel

    # Boleto bajo el piso legal ⇒ DISCREPANCIA
    assert nivel("QBE-H1", [1.50, 2.50]) == NivelSeveridad.DISCREPANCIA
    assert nivel("QBE-C1", [1.90, 2.20]) == NivelSeveridad.DISCREPANCIA
    assert nivel("QBE-H2", [2.00, 1.50]) == NivelSeveridad.DISCREPANCIA
    assert nivel("QBE-R2", [2.00, 1.80]) == NivelSeveridad.DISCREPANCIA

    # Familia con cobertura y piso bivariado satisfecho ⇒ CERTIFICA
    assert nivel("QBE-R1", [2.00, 2.00]) == NivelSeveridad.CONFORME
    assert nivel("QBE-H1", [2.50, 3.00]) == NivelSeveridad.CONFORME

    # Familia directa: el piso bivariado no aplica (un solo boleto), el legal sí
    assert nivel("QBE-D1", [2.00]) == NivelSeveridad.CONFORME
    assert nivel("QBE-D1", [1.00]) == NivelSeveridad.DISCREPANCIA

    # Sin boletos declarados no hay veredicto: cero veto fabricado
    sin_evidencia = auditar_coherencia_partido({"id_partido": "TEST-PISO", "estrategia_codigo": "QBE-R1"})
    assert sin_evidencia.nivel_global == NivelSeveridad.SIN_VEREDICTO
    assert sin_evidencia.apto_pre_vuelo is True


# ---------------------------------------------------------------------------
# 3. [LN-QBE-040-B] TECHO DE GOLES / ANTI-RESONANCIA Y DEGRADACIÓN HONESTA
# ---------------------------------------------------------------------------
def test_invarianza_techo_goles_antiresonancia_y_degradacion_honesta():
    """λ ≤ 2.20 xG es inviolable; (1.86, 2.20] es banda de vigilancia, no veto."""
    from scripts.auditoria.auditar_coherencia_cartelera import (
        GAMMA_BASE,
        SONDA_COHERENCIA_CAPA0,
        SONDA_DIVERGENCIA_MERCADO,
        SONDA_OVERROUND,
        SONDA_PARIDAD,
        SONDA_PISO_VENTANILLA,
        SONDA_TECHO_GOLES,
        TECHO_XG,
        TECHO_XG_ANTIRESONANCIA,
        NivelSeveridad,
        auditar_coherencia_partido,
    )

    assert (TECHO_XG_ANTIRESONANCIA, TECHO_XG) == (1.86, 2.20)
    assert GAMMA_BASE == 0.67
    assert {
        SONDA_PARIDAD,
        SONDA_OVERROUND,
        SONDA_PISO_VENTANILLA,
        SONDA_TECHO_GOLES,
        SONDA_COHERENCIA_CAPA0,
        SONDA_DIVERGENCIA_MERCADO,
    } == {
        "paridad_simplex",
        "overround_comercial",
        "piso_ventanilla",
        "techo_goles",
        "coherencia_capa0",
        "divergencia_mercado",
    }

    def nivel(lambda_home, lambda_away):
        reporte = auditar_coherencia_partido(
            {"id_partido": "TEST-XG", "lambda_home": lambda_home, "lambda_away": lambda_away}
        )
        return next(h for h in reporte.hallazgos if h.sonda == "techo_goles").nivel

    assert nivel(1.60, 1.20) == NivelSeveridad.CONFORME
    # Evidencia fáctica real (LIGAMX-J11-06): 2.0553 xG ⇒ vigilancia anti-resonancia
    assert nivel(2.0553, 1.1658) == NivelSeveridad.ADVERTENCIA
    # Evidencia fáctica real (LIGAMX-J17-04): 1.9971 xG ⇒ vigilancia anti-resonancia
    assert nivel(1.5509, 1.9971) == NivelSeveridad.ADVERTENCIA
    # Sobre el techo declarado ⇒ DISCREPANCIA
    assert nivel(2.45, 1.30) == NivelSeveridad.DISCREPANCIA

    # -- Degradación honesta: payload vacío (jornada sin mercado) ⇒ 🇾🇪, jamás 🔴 --
    vacio = auditar_coherencia_partido({})
    assert vacio.nivel_global == NivelSeveridad.SIN_VEREDICTO
    assert vacio.apto_pre_vuelo is True
    assert all(h.nivel == NivelSeveridad.SIN_VEREDICTO for h in vacio.hallazgos)
    assert len(vacio.hallazgos) == 6


# ---------------------------------------------------------------------------
# 4. COHERENCIA CAPA 0, DIVERGENCIA DE MERCADO Y CONTRATO DE SALIDA DEL CLI
# ---------------------------------------------------------------------------
def test_invarianza_coherencia_capa0_tvd_y_contrato_de_salida():
    """La estrategia declarada debe ser la que emite el triaje canónico; `--check` sólo ve 🔴."""
    from scripts.auditoria.auditar_coherencia_cartelera import (
        TVD_MAX,
        NivelSeveridad,
        auditar_coherencia_partido,
        calcular_codigo_salida,
    )

    assert TVD_MAX == 0.22

    # Cartelera ideal: P' = (0.45, 0.30, 0.25) ⇒ ASIMETRIA_LOCAL ⇒ el triaje canónico emite QBE-H1
    cartelera = {
        "id_partido": "TEST-CAPA0",
        "p_local": 0.45,
        "p_empate": 0.30,
        "p_visitante": 0.25,
        "momios": {"L": 2.50, "E": 3.90, "V": 2.60},
        "estrategia_codigo": "QBE-H1",
        "boletos": [2.50, 3.00],
        "lambda_home": 1.60,
        "lambda_away": 1.20,
    }
    conformes = auditar_coherencia_partido(cartelera)
    assert conformes.nivel_global == NivelSeveridad.CONFORME
    assert conformes.apto_pre_vuelo is True
    assert all(h.nivel == NivelSeveridad.CONFORME for h in conformes.hallazgos)
    assert {h.sonda for h in conformes.hallazgos} == {
        "paridad_simplex",
        "overround_comercial",
        "piso_ventanilla",
        "techo_goles",
        "coherencia_capa0",
        "divergencia_mercado",
    }

    # Drift de estrategia declarada vs. triaje canónico ⇒ DISCREPANCIA
    drift = auditar_coherencia_partido({**cartelera, "estrategia_codigo": "QBE-D1"})
    capa0 = next(h for h in drift.hallazgos if h.sonda == "coherencia_capa0")
    assert capa0.nivel == NivelSeveridad.DISCREPANCIA
    assert "ASIMETRIA_LOCAL" in capa0.detalle or "QBE-H1" in capa0.detalle
    assert drift.nivel_global == NivelSeveridad.DISCREPANCIA
    assert drift.apto_pre_vuelo is False

    # Sin estrategia declarada: se publica la morfología observada, sin inventar el código
    observada = auditar_coherencia_partido({k: v for k, v in cartelera.items() if k != "estrategia_codigo"})
    hallazgo_morfologico = next(h for h in observada.hallazgos if h.sonda == "coherencia_capa0")
    assert hallazgo_morfologico.nivel == NivelSeveridad.SIN_VEREDICTO
    assert "ASIMETRIA_LOCAL" in hallazgo_morfologico.detalle

    # Divergencia extrema P' vs. mercado ⇒ DISCREPANCIA (TVD = 0.5157 > 0.22)
    divergente = auditar_coherencia_partido(
        {**cartelera, "p_local": 0.90, "p_empate": 0.06, "p_visitante": 0.04}
    )
    hallazgo_tvd = next(h for h in divergente.hallazgos if h.sonda == "divergencia_mercado")
    assert hallazgo_tvd.nivel == NivelSeveridad.DISCREPANCIA

    # Contrato de salida: EXIT 1 sólo ante DISCREPANCIA; 🟡 y 🇾🇪 no bloquean el pre-vuelo
    assert calcular_codigo_salida([]) == 0
    assert calcular_codigo_salida([conformes]) == 0
    assert calcular_codigo_salida([auditar_coherencia_partido({})]) == 0
    assert calcular_codigo_salida([conformes, drift]) == 1
