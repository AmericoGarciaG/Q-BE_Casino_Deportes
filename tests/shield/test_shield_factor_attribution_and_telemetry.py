# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DE LA ATRIBUCIÓN FACTORIAL Y LA TELEMETRÍA DE INSUMOS
Gobierno: `docs/LOGIC.md` [LN-QBE-101] / `docs/ARCH.md` [ARCH-1.4.42] / `docs/DESIGN.md` [DES-QBE-064]

Régimen declarado (Dual-Track honesto):
- [DIRGEN-STRICT] en la matemática pura de atribución (`src/core/sovereign/factor_attribution.py`).
- [DBBD-FUNGIBLE] en la capa de presentación (Micro-HUD / modal de 44 variables).

[GOV-TEST-01] Aislamiento hermético en memoria: cero red, cero navegador, cero tokens.

NOTA DE CONTRATO (Cláusula de Amortiguamiento Canónico, LOGIC [LN-QBE-101].P.1):
la fixture porta los factores CRUDOS (pre-damping) que produce `derivar_factores_estructurales` y
las intensidades `λ` que produce `estimar_intensidades_loglineal`; por [VAULT-CORE-001] esas `λ`
son la imagen `κ_net · tanh(A / κ_net)` con κ_net = 0.2500. El juez exige, por tanto:
  (a) la conservación exacta de la SUMA de las tres componentes canónicas contra `delta_neto_total`;
  (b) la identidad `delta_neto_total ≡ ln(λ_H / λ_A)` dentro de 1e-3;
  (c) la transcripción del vector CRUDO en las claves `*_cruda` (evidencia forense, sin maquillaje).
"""

import math
from pathlib import Path

import pytest

RUTA_MODULO = Path("src/core/sovereign/factor_attribution.py")

# ── Fixture de verdad sellada: el mismo vector que consume el motor soberano ────────────────────
A_H, D_A, A_A, D_H = -0.0114, 0.6869, 0.3354, -0.1241
LAMBDA_H, LAMBDA_A = 1.0988, 1.7099
GAMMA_HOME = 0.1500
C_H, C_A = 0.0, 0.0


def test_atribucion_loglineal_conservacion():
    """[INVARIANZA 1 — CONSERVACIÓN DE ENERGÍA EN ESPACIO LOGARÍTMICO]:
    La descomposición aditiva debe reproducir `ln(λ_H / λ_A)` sin residuo atribuible
    (tolerancia 1e-3) y la suma de sus tres componentes debe clausurar contra el neto.
    """
    from src.core.sovereign.factor_attribution import calcular_atribucion_loglineal

    res = calcular_atribucion_loglineal(
        A_h=A_H, D_a=D_A, A_a=A_A, D_h=D_H,
        gamma_home=GAMMA_HOME, C_h=C_H, C_a=C_A,
        lambda_h=LAMBDA_H, lambda_a=LAMBDA_A,
    )

    suma = (
        res["delta_ofensiva"]
        + res["delta_defensiva"]
        + res["delta_contexto"]
    )
    assert abs(suma - res["delta_neto_total"]) < 1e-4, (
        f"La suma de componentes no clausura contra el neto: {suma} ≠ {res['delta_neto_total']}"
    )

    teorico = math.log(LAMBDA_H / LAMBDA_A)
    assert abs(res["delta_neto_total"] - teorico) < 1e-3, (
        f"El delta neto no reproduce ln(λ_H/λ_A): {res['delta_neto_total']} ≠ {teorico}"
    )

    # (c) Evidencia forense del vector CRUDO pre-damping (cero maquillaje).
    assert abs(res["delta_ofensiva_cruda"] - (A_H - D_A)) < 1e-6
    assert abs(res["delta_defensiva_cruda"] - (D_H - A_A)) < 1e-6
    assert abs(res["delta_ofensiva_cruda"] - (-0.6983)) < 1e-4
    assert abs(res["delta_defensiva_cruda"] - (-0.4595)) < 1e-4

    # El contexto jamás se amortigua: la localía es un término aditivo puro.
    assert abs(res["delta_contexto"] - GAMMA_HOME) < 1e-6


def test_driver_principal_deterministico():
    """[INVARIANZA 2 — MOTOR DE FUERZA PRINCIPAL]:
    El driver es `argmax |Δ_k|`; el signo decide el bando y el empate técnico se resuelve
    por el orden canónico OFENSIVA → DEFENSIVA → CONTEXTO (reproducibilidad estricta).
    """
    from src.core.sovereign.factor_attribution import resolver_driver_principal

    driver = resolver_driver_principal({
        "delta_ofensiva": -0.6983,
        "delta_defensiva": 0.1241,
        "delta_contexto": 0.0500,
    })
    assert driver["dimension"] == "OFENSIVA"
    assert driver["favorece"] == "VISITANTE"
    assert abs(driver["magnitud"] - 0.6983) < 1e-4
    assert "Ofensiva Visita" in driver["etiqueta"]

    positivo = resolver_driver_principal({
        "delta_ofensiva": 0.0100,
        "delta_defensiva": 0.4200,
        "delta_contexto": 0.1500,
    })
    assert positivo["dimension"] == "DEFENSIVA"
    assert positivo["favorece"] == "LOCAL"

    # Empate técnico en magnitud ⇒ gana OFENSIVA por precedencia legislada.
    empate = resolver_driver_principal({
        "delta_ofensiva": -0.3000,
        "delta_defensiva": 0.3000,
        "delta_contexto": 0.3000,
    })
    assert empate["dimension"] == "OFENSIVA"
    assert empate["favorece"] == "VISITANTE"


def test_semaforos_salud_datos():
    """[INVARIANZA 3 — LOS 5 SEMÁFOROS DE SALUD FÁCTICA]:
    OPTA, SEDE, H2H, EPIST y CTX degradan honestamente ante evidencia parcial.
    """
    from src.core.sovereign.factor_attribution import evaluar_semaforos_salud_datos

    optimo = evaluar_semaforos_salud_datos(
        xg_disponible=True,
        pj_sede_local=8,
        pj_sede_visita=7,
        h2h_partidos_conteo=5,
        delta_epist=0.0100,
        q_mod=1.00,
    )
    assert optimo == {
        "opta": "VERDE", "sede": "VERDE", "h2h": "VERDE",
        "epist": "VERDE", "ctx": "VERDE",
    }

    degradado = evaluar_semaforos_salud_datos(
        xg_disponible=False,
        xg_calibrado=True,
        pj_sede_local=2,
        pj_sede_visita=8,
        h2h_partidos_conteo=3,
        delta_epist=0.0800,
        q_mod=0.97,
    )
    assert degradado == {
        "opta": "AMARILLO", "sede": "AMARILLO", "h2h": "AMARILLO",
        "epist": "AMARILLO", "ctx": "AMARILLO",
    }

    # Ley Zero-H2H [LN-QBE-020-B]: sin duelos directos el semáforo es NEUTRO, nunca rojo.
    sin_h2h = evaluar_semaforos_salud_datos(
        xg_disponible=True,
        pj_sede_local=5,
        pj_sede_visita=5,
        h2h_partidos_conteo=0,
        delta_epist=0.0000,
        q_mod=1.00,
    )
    assert sin_h2h["h2h"] == "NEUTRO"

    ruptura = evaluar_semaforos_salud_datos(
        xg_disponible=False,
        xg_calibrado=False,
        pj_sede_local=0,
        pj_sede_visita=0,
        h2h_partidos_conteo=2,
        delta_epist=0.2000,
        q_mod=0.93,
    )
    assert ruptura == {
        "opta": "ROJO", "sede": "ROJO", "h2h": "AMARILLO",
        "epist": "ROJO", "ctx": "ROJO",
    }


def test_catalogo_44_variables():
    """[INVARIANZA 4 — TAXONOMÍA DE 32 VARIABLES EN 6 DIMENSIONES · [LN-QBE-120]]:
    Partición canónica del dossier §3, sin duplicados, con las columnas del modal forense;
    la evidencia ausente degrada a `None` (prohibido fabricar cifras).
    """
    from src.core.sovereign.factor_attribution import estructurar_catalogo_44_variables

    catalogo = estructurar_catalogo_44_variables({})
    dimensiones = catalogo["dimensiones"]
    assert catalogo["total_variables"] == 32, "Catálogo [LN-QBE-120]: 32 variables PRE-KICKOFF."
    assert len(dimensiones) == 6

    ids = [v["id"] for d in dimensiones for v in d["variables"]]
    assert len(ids) == 32
    assert len(set(ids)) == 32, "El catálogo [LN-QBE-120] contiene variables duplicadas."

    for dimension in dimensiones:
        assert dimension["variables"], f"Dimensión vacía: {dimension['dimension']}"
        for variable in dimension["variables"]:
            for clave in ("id", "variable", "local", "visita", "z_score", "origen", "estado"):
                assert clave in variable, f"Columna forense ausente '{clave}' en {variable}"

    # Sin evidencia, ninguna cifra se inventa.
    primera = dimensiones[0]["variables"][0]
    assert primera["local"] is None and primera["visita"] is None
    assert primera["estado"] == "SIN EVIDENCIA"

    # Con evidencia fáctica, el valor se transcribe (xG acumulado ⇒ tasa por PJ, [ARCH-1.4.41]).
    con_datos = estructurar_catalogo_44_variables({
        "home_team_stats": {"pj": 8, "gf": 16, "gc": 8, "xg": 13.2, "xga": 8.8, "opp_box_touches": 96},
        "away_team_stats": {"pj": 8, "gf": 8, "gc": 12, "xg": 8.0, "xga": 12.8, "opp_box_touches": 64},
    })
    planas = {v["id"]: v for d in con_datos["dimensiones"] for v in d["variables"]}
    assert abs(planas["V06"]["local"] - (13.2 / 8)) < 1e-9  # ancla xG/PJ (V05→V06 [LN-QBE-120])
    assert abs(planas["V12"]["visita"] - (12.8 / 8)) < 1e-9  # ancla xGA/PJ (V10→V12 [LN-QBE-120])
    assert planas["V06"]["origen"] == "OPTA"
    assert planas["V06"]["estado"] == "VALIDADO"
    assert planas["V02"]["local"] == 96.0  # V02 = toques en área rival (dossier §3)
    assert planas["V02"]["visita"] == 64.0
    assert planas["V07"]["local"] is None  # SoT no publicado: cero fabricación
    assert planas["V07"]["estado"] == "SIN EVIDENCIA"


def test_pureza_del_modulo():
    """[INVARIANZA 5 — PUREZA DEL MOTOR]:
    El módulo es O(1), sin I/O, sin red y sin ORM: sólo matemática y el canon de amortiguamiento.
    """
    assert RUTA_MODULO.exists(), "El motor de atribución factorial no existe."

    fuente = RUTA_MODULO.read_text(encoding="utf-8")
    for prohibido in ("requests", "httpx", "urllib", "sqlalchemy", "sqlite3", "open(", "Path("):
        assert prohibido not in fuente, (
            f"[DIRGEN-STRICT] El motor puro no puede portar '{prohibido}'."
        )

    import src.core.sovereign.factor_attribution as motor

    for nombre in (
        "calcular_atribucion_loglineal",
        "resolver_driver_principal",
        "evaluar_semaforos_salud_datos",
        "estructurar_catalogo_44_variables",
    ):
        assert callable(getattr(motor, nombre, None)), f"Función canónica ausente: {nombre}"


def test_ui_micro_hud_y_modal_forense():
    """[INVARIANZA 6 — CONTRATO DE PRESENTACIÓN (DES-QBE-064)]:
    El micro-HUD de la tarjeta (semáforos OPTA · SEDE · H2H · EPIST, badge del driver y
    botón `🔬 44 Variables`) y el modal `#modal-44-variables` existen con la geometría
    legislada. El pintor transcribe el bloque servido: cero derivación local.
    """
    app_js = Path("src/web/static/js/app.js").read_text(encoding="utf-8")
    html = Path("src/web/templates/index.html").read_text(encoding="utf-8")
    css = Path("src/web/static/css/theme.css").read_text(encoding="utf-8")

    # 1) Micro-HUD: tira de semáforos + badge + acceso al desglose.
    for marcador in ('class="bt-micro-hud"', 'class="hud-tira-semaforos"',
                     'class="badge-driver-principal"', 'class="btn-ver-44-vars"',
                     '🔬 44 Variables'):
        assert marcador in app_js, f"Micro-HUD incompleto: falta '{marcador}'."
    for semaforo in ("opta", "sede", "h2h", "epist"):
        assert f'"{semaforo}"' in app_js, f"Semáforo ausente en la tira: {semaforo}"

    # 2) Consumo del bloque servido (no derivación local).
    assert "p.atribucion_factorial" in app_js
    assert "abrirModal44Variables" in app_js and "cerrarModal44Variables" in app_js
    assert 'evento.key !== "Escape"' in app_js, "El modal debe cerrar con Escape [DES-QBE-064]."

    # 3) Modal forense: contenedor, cuerpo hidratable y geometría legislada.
    assert 'id="modal-44-variables"' in html
    assert 'id="vars44-cuerpo"' in html
    assert "max-width: 980px" in html
    assert "#0F172A" in html and "1px solid #334155" in html

    # 4) Acordeón de 12 dimensiones con la tabla de 7 columnas + ID canónico.
    for columna in ("Variable", "Local", "Visita", "Z-Score", "Origen", "Estado", "Impacto"):
        assert f"<th>{columna}</th>" in app_js, f"Columna forense ausente: {columna}"
    assert 'class="vars44-dimension"' in app_js
    assert "dimensiones.map(_tablaDimension44)" in app_js

    # 5) Colorimetría Dark Fintech legislada.
    for color in ("#10B981", "#F59E0B", "#EF4444", "#94A3B8"):
        assert color in css, f"Colorimetría de semáforos ausente: {color}"
    assert "#38BDF8" in css
    assert "grid-column: 1 / -1" in css
