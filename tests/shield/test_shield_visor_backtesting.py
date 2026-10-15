# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DEL VISOR DE BACKTESTING Y CALIBRACIÓN FACTUAL DE TEMPORADA
Contrato vigilado:
- [LN-QBE-100] Tasa de Coincidencia Fiduciaria Global (H_fid), Brier Score Multicategórico
  (BS_QBE vs BS_MKT) y Alpha de Calibración sobre resultados reales consumados.
- [ARCH-1.4.38] Endpoint REST de solo lectura `GET /api/markets/backtesting/calibration-report`.
- [VAULT-CORE-007-C] Desmarque proporcional de vig `desmarcar_cuotas_proporcional(oL, oX, oV)`.
Regímenes: [DIRGEN-STRICT] en la matemática de calibración (verbatim de bóveda),
[DBBD-FUNGIBLE] en la capa de presentación.
Gobierno: [GOV-TEST-01] Aislamiento hermético en memoria (cero red / cero navegador / cero tokens).
"""


def test_juez_4_parrilla_micro_semantica_visual():
    """[ARCH-1.4.38 / ARCH-1.4.38-R3] El desenlace real consumado conserva la colorimetría
    fiduciaria de su POSICIÓN en el ranking P′ (verde 1er favorito · cian 2º favorito · rojo
    underdog), y la franja inferior desplegada NO re-introduce la pastilla derogada."""
    from pathlib import Path

    js = Path("src/web/static/js/app.js").read_text(encoding="utf-8")
    css = Path("src/web/static/css/theme.css").read_text(encoding="utf-8")

    assert 'p.resultado_real === c.clave ? claseResultado : "micro-box-inactivo"' in js
    # [ARCH-1.4.38-R3] La clase de colorimetría se ancla a la POSICIÓN en el ranking P′
    # descendente (jamás al rol nominal del resultado).
    assert "const rankReal = clavesPorPRima.indexOf(p.resultado_real);" in js
    assert "rankReal === 0" in js
    assert "rankReal === 1" in js
    assert '"box-resultado-dog"' in js
    # [ARCH-1.4.38-R3] Retiro definitivo del Nivel 3 derogado: pastilla fiduciaria izquierda y
    # texto central de pronóstico/marcador.
    assert "🎯 ACIERTO FAVORITO" not in js
    assert "🛡️ COBERTURA TABLAS" not in js
    assert "💀 RUPTURA UNDERDOG" not in js
    assert "Pronóstico P′:" not in js
    assert "· Final:" not in js
    assert "Brier: Q-BE" in js
    assert "bt-casilla-ganadora" not in js

    for color_class, color, background in (
        ("box-resultado-fav", "#00E676", "rgba(0, 230, 118, 0.12)"),
        ("box-resultado-emp", "#38BDF8", "rgba(56, 189, 248, 0.12)"),
        ("box-resultado-dog", "#EF4444", "rgba(239, 68, 68, 0.12)"),
    ):
        rule_start = css.index(f".{color_class} {{")
        rule_end = css.index("}", rule_start)
        rule = css[rule_start:rule_end]
        assert color in rule
        assert background in rule
        assert "border:" in rule

    assert ".micro-box-inactivo" in css


def test_juez_1_desmarque_proporcional_de_vig():
    """
    [INVARIANZA 1 - DESMARQUE PROPORCIONAL DE VIG]:
    Dado un triplete de cuotas de ventanilla con comisión (oL=2.00, oX=3.40, oV=4.00),
    la función canónica debe extraer el consenso sin vig repartiendo el sobreprecio
    de forma estrictamente proporcional a la probabilidad implícita bruta.
    Sobreprecio de la casa: S = 1/2.00 + 1/3.40 + 1/4.00 = 1.0441 (> 1.0).
    """
    from src.core.contracts.portfolio_math import desmarcar_cuotas_proporcional

    ql, qe, qv = desmarcar_cuotas_proporcional(2.00, 3.40, 4.00)

    # 1. Preservación del orden fiduciario del mercado
    assert ql > qe > qv, f"El consenso desmarcado perdió el orden del mercado: {(ql, qe, qv)}"
    # 2. Reparto proporcional exacto contra el sobreprecio S = 1.0441
    assert abs(ql - (0.50 / 1.0441)) <= 0.001, f"q_LOCAL fuera de tolerancia: {ql}"
    # 3. Clausura estricta de la medida de probabilidad
    assert abs((ql + qe + qv) - 1.0) <= 0.001, f"El consenso no normaliza a 1.0: {ql + qe + qv}"


def test_juez_2_brier_multicategorico():
    """
    [INVARIANZA 2 - BRIER SCORE MULTICATEGÓRICO]:
    El evaluador debe promediar el error cuadrático de las 3 casillas (1, X, 2) con
    normalización 1/(3N), penalizando por igual la sobreconfianza y la subconfianza.
    Dos partidos sellados: (0.60/0.25/0.15 -> LOCAL) y (0.30/0.50/0.20 -> EMPATE)
    deben rendir BS = 0.1042 exacto.
    """
    from src.core.contracts.portfolio_math import calcular_brier_multicategorico

    partidos = [
        {"p_local": 0.60, "p_empate": 0.25, "p_visitante": 0.15, "resultado": "LOCAL"},
        {"p_local": 0.30, "p_empate": 0.50, "p_visitante": 0.20, "resultado": "EMPATE"},
    ]

    bs = calcular_brier_multicategorico(partidos)

    assert abs(bs - 0.1042) <= 0.001, f"Brier Score multicategórico desviado: {bs}"


def test_juez_3_endpoint_calibration_report_contrato():
    """
    [INVARIANZA 3 - ENDPOINT DE SOLO LECTURA Y CONTRATO FACTUAL]:
    El endpoint debe responder HTTP 200 (jamás 400/500) y emitir el contrato
    {resumen_temporada, jornadas} con las métricas macro de calibración.
    Universo auditable factual: jornadas J10 ∪ J11 de la bóveda viva (18 partidos concluidos).
    """
    from fastapi.testclient import TestClient
    from src.web.app import app

    client = TestClient(app)
    response = client.get("/api/markets/backtesting/calibration-report?league_id=1")

    assert response.status_code == 200, (
        f"🚨 ERROR EN ENDPOINT: Retornó {response.status_code} en lugar de 200 OK. "
        f"Detalle: {response.text}"
    )
    data = response.json()
    assert "resumen_temporada" in data, "Falta el bloque macro `resumen_temporada`"
    assert "jornadas" in data, "Falta la tabla meso `jornadas`"

    resumen = data["resumen_temporada"]
    for clave in (
        "total_partidos",
        "tasa_coincidencia_fiduciaria_pct",
        "brier_score_qbe",
        "brier_score_mercado",
    ):
        assert clave in resumen, f"Falta la métrica macro `{clave}` en el resumen de temporada"

    assert resumen["total_partidos"] >= 18, (
        "El universo auditable factual (J10 ∪ J11) no fue resuelto desde la bóveda: "
        f"total_partidos={resumen['total_partidos']}"
    )
    assert len(data["jornadas"]) >= 2, "Faltan las jornadas con resultados consumados"


def test_juez_5_marcador_favorito_mercado_parrilla_micro():
    """
    [INVARIANZA 5 - MARCADOR FACTUAL DEL FAVORITO DE MERCADO]:

    La parrilla micro debe derivar el favorito del MERCADO del máximo del consenso desmarcado
    `q_mkt` sobre el contrato PLANO del DTO (`q_local` / `q_empate` / `q_visitante`, decreto
    `VAR-2026-EGO-CONTRARIAN-AUDIT` §VAR-UI-01) y señalarlo con la barra gris (`#94A3B8`) de la
    BASE INFERIOR de la casilla (`.fav-base-mkt`) tras el rediseño tridimensional
    [ARCH-1.4.38-R3]; la antigua barra vertical del extremo izquierdo queda retirada.

    Leyes vigiladas:
      1. Igualdad estricta (`===`) contra el máximo: un empate técnico de mercado marca TODAS las
         casillas que alcanzan el máximo; la UI no fuerza desempates invisibles (§VAR-UI-02).
      2. Geometría declarada en la hoja de estilos (`box-sizing: border-box` es global): la barra
         de 4px no degrada el layout (§VAR-UI-03 preservada).
      3. Cero regresión del contrato visual del Juez 4 (clase de colorimetría de resultado).
    """
    from pathlib import Path

    js = Path("src/web/static/js/app.js").read_text(encoding="utf-8")
    css = Path("src/web/static/css/theme.css").read_text(encoding="utf-8")

    assert "Math.max(p.q_local, p.q_empate, p.q_visitante)" in js, (
        "La parrilla micro no deriva el favorito del mercado desde el contrato plano del DTO "
        "(q_local / q_empate / q_visitante)."
    )
    assert "p.q_local === maxQmkt" in js, "Falta la marca factual de la casilla 1 LOCAL."
    assert "p.q_empate === maxQmkt" in js, "Falta la marca factual de la casilla X EMPATE."
    assert "p.q_visitante === maxQmkt" in js, "Falta la marca factual de la casilla 2 VISITANTE."

    # [ARCH-1.4.38-R3] La barra gris migró del extremo izquierdo a la BASE inferior de la casilla.
    assert 'esFavMercado(c.clave) ? "fav-base-mkt" : ""' in js, (
        "La casilla del favorito de mercado no porta la clase `.fav-base-mkt` de la base inferior."
    )
    assert "border-left: 5px solid #94A3B8" not in js, (
        "La barra gris del extremo izquierdo debía quedar definitivamente retirada."
    )
    regla_base_start = css.index(".fav-base-mkt {")
    regla_base = css[regla_base_start:css.index("}", regla_base_start)]
    assert "border-bottom: 4px solid #94A3B8 !important;" in regla_base, (
        "La base gris del favorito de mercado no declara el borde inferior (#94A3B8, 4px)."
    )

    # Cero regresión: el contrato visual sellado del Juez 4 permanece intacto.
    assert 'p.resultado_real === c.clave ? claseResultado : "micro-box-inactivo"' in js


def test_juez_6_rediseno_tridimensional_parrilla_micro():
    """
    [INVARIANZA 6 - REDISEÑO TRIDIMENSIONAL 1X2 DE LA PARRILLA MICRO] [ARCH-1.4.38-R3]:

    Cada casilla 1X2 codifica SIMULTÁNEAMENTE tres dimensiones cromático-geométricas:
      1. Techo blanco  (`.fav-techo-qbe`, 4px `#FFFFFF`) → 1er favorito de Q-BE (argmax P′).
      2. Base gris     (`.fav-base-mkt`,  4px `#94A3B8`) → favorito del mercado (argmax q_mkt).
      3. Bordes laterales y fondo del desenlace real consumado, según su POSICIÓN en el ranking
         P′ descendente (verde / azul cian / rojo carmín) — contrato sellado del Juez 4.

    El Nivel 3 (franja inferior) queda limpio de la pastilla fiduciaria y del texto central
    derogados, y despliega las métricas cuantitativas en 3 columnas flex
    (`.micro-partido-footer-v2`): postura fiduciaria (Consenso / Contrarian), Brier Score dual con
    Alpha individual `Alpha_i = (1 − BS_QBE / BS_MKT) · 100` y masa fiduciaria protegida
    `(P′(1) + P′(2)) · 100`.

    El Juez lee los artefactos reales: cero etiquetas ni cifras inventadas por el test.
    """
    from pathlib import Path

    js = Path("src/web/static/js/app.js").read_text(encoding="utf-8")
    css = Path("src/web/static/css/theme.css").read_text(encoding="utf-8")

    # ── Dimensión 1: TECHO BLANCO del favorito de Q-BE (argmax P′) ──────────────────────────
    techo_start = css.index(".fav-techo-qbe {")
    regla_techo = css[techo_start:css.index("}", techo_start)]
    assert "border-top: 4px solid #FFFFFF !important;" in regla_techo, (
        "El techo blanco del favorito de Q-BE no declara el borde superior (#FFFFFF, 4px)."
    )
    assert 'c.clave === favQbeClave ? "fav-techo-qbe" : ""' in js, (
        "La casilla del favorito de Q-BE no porta la clase `.fav-techo-qbe`."
    )
    assert "const clavesPorPRima = ordenClaves" in js, (
        "Falta el ranking fiduciario P′ descendente que resuelve 1er / 2º / 3er favorito."
    )

    # ── Dimensión 2: BASE GRIS del favorito del mercado (argmax q_mkt) ─────────────────────
    base_start = css.index(".fav-base-mkt {")
    regla_base = css[base_start:css.index("}", base_start)]
    assert "border-bottom: 4px solid #94A3B8 !important;" in regla_base, (
        "La base gris del favorito del mercado no declara el borde inferior (#94A3B8, 4px)."
    )
    assert 'esFavMercado(c.clave) ? "fav-base-mkt" : ""' in js, (
        "La casilla del favorito del mercado no porta la clase `.fav-base-mkt`."
    )

    # ── Dimensión 3: POSTURA FIDUCIARIA (Consenso / Contrarian) ────────────────────────────
    assert "const badgePostura = favQbeClave === favMktClave" in js, (
        "La postura fiduciaria debe comparar el favorito de Q-BE contra el favorito del mercado."
    )
    assert "badge-postura badge-consenso" in js and "🤝 Consenso" in js, (
        "Falta la pastilla 🤝 Consenso del caso `fav_qbe === fav_mkt`."
    )
    assert "badge-postura badge-contrarian" in js and "⚡ Contrarian" in js, (
        "Falta la pastilla ⚡ Contrarian del caso `fav_qbe !== fav_mkt`."
    )
    assert "badge-fiduciario" not in js, (
        "La pastilla fiduciaria derogada (ACIERTO FAVORITO / COBERTURA TABLAS) no debe regresar."
    )

    # ── Nivel 3: FRANJA INFERIOR de 3 columnas con métricas cuantitativas ──────────────────
    assert "micro-partido-footer-v2" in js and ".micro-partido-footer-v2 {" in css, (
        "Falta el contenedor flex de 3 columnas de la franja inferior del Nivel 3."
    )
    assert "Masa Cubierta:" in js, (
        "Falta la masa fiduciaria protegida (P′(1) + P′(2)) de la columna derecha."
    )
    assert "'(Alpha ${signoAlpha}${alphaPct}%)'" in js or "(Alpha ${signoAlpha}${alphaPct}%)" in js, (
        "Falta el Alpha individual del partido con su signo porcentual en la columna central."
    )
    assert "(1 - bsQbeRaw / bsMktRaw) * 100" in js, (
        "Falta la fórmula sellada del Alpha individual: Alpha_i = (1 − BS_QBE / BS_MKT) · 100."
    )
    assert "Brier: Q-BE" in js and "· Mkt " in js, (
        "La columna central debe desplegar el Brier Score dual (Q-BE vs Mkt)."
    )
    assert "opacity: 0.75;" in css and ".micro-box-inactivo" in css, (
        "Las dos casillas que no ocurrieron deben conservar el fondo neutro `.micro-box-inactivo`."
    )
