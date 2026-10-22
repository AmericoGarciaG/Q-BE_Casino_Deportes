# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ ABSTRACTO DE LA FASE 2 · MATERIALIZACIÓN ANIDADA DE LOS CINCO PILARES
Gobierno: `[LN-QBE-118]` · `[ARCH-1.4.56]` · `[GOV-TEST-01]` aislamiento hermético sobre el clon
efímero del arnés (`tests/shield/conftest.py::boveda_gateway_aislada`): cero red, cero navegador,
cero tokens.

Régimen: `[DIRGEN-STRICT]` — los jueces NO reimplementan matemática. Invocan el generador sellado
`[VAULT-CORE-005]`, el proveedor canónico `[LN-QBE-117]` y el aplanador `[ARCH-1.4.55]`, y auditan
que el anidamiento sea una **PROYECCIÓN** (cero cálculo nuevo) y que el **Resguardo WORM** preceda a
toda DML del lote.

Invariantes vigiladas
---------------------
1. **Invarianza 1 — cinco pilares anidados con paridad plana:** toda traza publica `h2h`,
   `contexto`, `trayectoria`, `volumen_porteria` y `ataque_defensa` con el shape legislado
   `{bloque, status, insumos}`; cada clave del nido con espejo en `_MAPA_NIDOS_A_PLANO` transporta
   **exactamente** el mismo valor que su clave plana heredada; λ sigue siendo la del motor sellado
   (el nido no alimenta ninguna fórmula).
2. **Invarianza 2 — el Resguardo WORM precede a la DML:** por AST, la ÚNICA invocación de
   `crear_backup_boveda_sqlite` ocurre ANTES de `sincronizar_distribuciones_soberanas_partidos` y
   del `write_transaction` del sellado de captura; el vector homólogo publica la altitud catalogada
   y el descanso real que el motor consume (cero fórmula duplicada en el script de ingesta).
"""

import ast
import pathlib

import pytest

CLAVES_NIDO = ("h2h", "contexto", "trayectoria", "volumen_porteria", "ataque_defensa")
ESTADOS_LEGALES = frozenset(("EXITO", "PARCIAL", "SIN_EVIDENCIA"))
RUTA_HOMOLOGACION = pathlib.Path("scripts") / "ingesta" / "homologar_temporada_optah2h.py"


def _payload(match_id: str, **extra) -> dict:
    """Registro fáctico de prueba (cero invención): sólo insumos publicados por la captura."""
    datos = {
        "match_id": match_id,
        "competition_id": "MEX_LIGAMX",
        "home_team_slug": "puebla",
        "away_team_slug": "atlante",
        "home_team_stats": {
            "pj": 8, "gf": 14, "gc": 6,
            "xg": 12.8, "xga": 8.0, "sot": 40, "sota": 32, "possession": 53.5,
        },
        "away_team_stats": {
            "pj": 8, "gf": 9, "gc": 12,
            "xg": 8.8, "xga": 12.0, "sot": 24, "sota": 32, "possession": 46.5,
        },
        "home_split_stats": {"pj": 4},
        "away_split_stats": {"pj": 4},
        "h2h_matches": [
            {"dias_antiguedad": 120, "goles_local": 2, "goles_visita": 1},
            {"dias_antiguedad": 260, "goles_local": 1, "goles_visita": 1},
            {"dias_antiguedad": 400, "goles_local": 0, "goles_visita": 2},
        ],
    }
    datos.update(extra)
    return datos


def _nombre_llamado(nodo: ast.AST) -> str:
    """Nombre simple del llamable (`crear_backup_boveda_sqlite`, `write_transaction`, ...)."""
    if isinstance(nodo, ast.Attribute):
        return nodo.attr
    if isinstance(nodo, ast.Name):
        return nodo.id
    return ""


def test_invarianza_1_cinco_pilares_anidados_con_paridad_plana():
    """[LN-QBE-118] El generador sellado anida los cinco pilares como proyección pura."""
    from src.core.intensity_canonical_loglink import estimar_intensidades_loglineal
    from src.core.sovereign.factor_attribution import _MAPA_NIDOS_A_PLANO, _aplanar_insumos
    from src.core.sovereign_pipeline import generar_distribucion_soberana

    publicado = _payload("M_F2_01", delta_alt_metros=1700.0, delta_descanso_dias=2.0)
    salida = generar_distribucion_soberana(match_id="M_F2_01", raw_match_data=publicado)
    insumos = salida.audit_trace.insumos_factivados
    assert isinstance(insumos, dict), "El generador debe empaquetar `insumos_factivados` [LN-QBE-102]."

    # (a) Los cinco bloques existen SIEMPRE, con el shape legislado y un estado legal.
    for clave in CLAVES_NIDO:
        assert clave in insumos, f"[LN-QBE-118] falta el bloque anidado `{clave}` en la traza."
        bloque = insumos[clave]
        assert bloque["bloque"] == clave
        assert bloque["status"] in ESTADOS_LEGALES
        assert isinstance(bloque["insumos"], dict) and bloque["insumos"]

    # (b) Las claves planas heredadas de [LN-QBE-102] conservan nombre y valor.
    claves_planas = (
        "xg_local_rate", "xg_visita_rate", "xga_local_rate", "xga_visita_rate",
        "gc_local_rate", "gc_visita_rate", "sot_local", "sot_visita", "sota_local",
        "sota_visita", "poss_local", "poss_visita", "pj_sede_local", "pj_sede_visita",
        "h2h_conteo", "q_mod_h", "q_mod_a", "delta_alt_metros", "delta_descanso_dias",
        "xg_es_real_opta",
    )
    for clave in claves_planas:
        assert clave in insumos, f"la clave plana `{clave}` desapareció del DTO (ruptura de contrato)."
    assert insumos["delta_alt_metros"] == 1700.0
    assert insumos["delta_descanso_dias"] == 2.0
    assert insumos["poss_local"] == 53.5 and insumos["sot_local"] == 40.0

    # (c) Paridad plana ↔ nido: el aplanador de [ARCH-1.4.55] re-deriva el MISMO número.
    aplanado = _aplanar_insumos({clave: insumos[clave] for clave in CLAVES_NIDO})
    for bloque, hoja, clave_plana in _MAPA_NIDOS_A_PLANO:
        valor_nido = insumos[bloque]["insumos"][hoja]
        if valor_nido is None:
            continue
        assert valor_nido == insumos[clave_plana], (
            f"divergencia plana/nido en `{bloque}.{hoja}`: {valor_nido} != {insumos[clave_plana]}"
        )
        assert aplanado[clave_plana] == insumos[clave_plana]
    assert insumos["contexto"]["insumos"]["delta_alt_metros"] == 1700.0

    # (d) El nido NO alimenta la matemática: λ se reproduce con la ruta sellada e idénticos
    #     argumentos (contexto efectivo publicado por el registro, [LN-QBE-102]).
    lh, la = estimar_intensidades_loglineal(
        A_home=salida.audit_trace.factores_entrada["A_home"],
        D_away=salida.audit_trace.factores_entrada["D_away"],
        A_away=salida.audit_trace.factores_entrada["A_away"],
        D_home=salida.audit_trace.factores_entrada["D_home"],
        mu_liga=2.65, gamma_home_base=0.15,
        delta_alt_metros=insumos["delta_alt_metros"],
        delta_descanso_dias=insumos["delta_descanso_dias"],
        q_mod_h=insumos["q_mod_h"], q_mod_a=insumos["q_mod_a"],
        home_team_slug=publicado["home_team_slug"],
    )
    assert salida.lambda_home == pytest.approx(lh, abs=1e-12)
    assert salida.lambda_away == pytest.approx(la, abs=1e-12)


def test_invarianza_1_bis_pilares_sin_evidencia_se_declaran():
    """[LN-QBE-118] Ausencia de evidencia ⇒ `SIN_EVIDENCIA` declarada, jamás un valor fabricado."""
    from src.core.sovereign_pipeline import generar_distribucion_soberana

    # Registro mínimo: S(I)=0 (sin banca de partidos) y sin hechos de plaza publicados.
    salida = generar_distribucion_soberana(
        match_id="M_F2_02",
        raw_match_data={"home_team_stats": {"pj": 1}, "away_team_stats": {"pj": 1}},
    )
    insumos = salida.audit_trace.insumos_factivados
    assert salida.audit_trace.suficiencia_S_I == 0
    for clave in CLAVES_NIDO:
        assert insumos[clave]["status"] != "EXITO", (
            f"el bloque `{clave}` no puede declarar EXITO sin evidencia (cero fabricación)."
        )
    assert insumos["h2h"]["status"] == "SIN_EVIDENCIA"
    assert insumos["h2h"]["motivo"], "la Ley Zero-H2H debe declarar su motivo [LN-QBE-020-B]."
    assert insumos["trayectoria"]["status"] == "SIN_EVIDENCIA"
    assert insumos["volumen_porteria"]["status"] == "SIN_EVIDENCIA"
    assert insumos["trayectoria"]["insumos"]["pts_5p_local"] is None
    assert insumos["contexto"]["insumos"]["altitud_local"] is None


def test_invarianza_2_resguardo_worm_precede_a_la_dml(boveda_gateway_aislada):
    """[LN-QBE-118] Resguardo WORM antes de toda DML + hechos contextuales REALES en el vector."""
    from scripts.ingesta.homologar_temporada_optah2h import (
        COMPETENCIA_CANONICA,
        _identidad_partidos,
        _partidos_consumados,
        _partidos_de_club,
        _telemetria_3nf,
        _vector_homologo,
        _volumen_porteria_corte,
    )
    from src.core.sovereign.context_provider import altitud_estadio
    from src.core.sovereign_pipeline import generar_distribucion_soberana

    # ── (a) Auditoría AST: el resguardo es ÚNICO y precede a cualquier escritura del lote ──────
    arbol = ast.parse(RUTA_HOMOLOGACION.read_text(encoding="utf-8"))
    funcion = next(
        nodo for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.FunctionDef) and nodo.name == "homologar"
    )
    respaldo, puente, escritura = [], [], []
    for nodo in ast.walk(funcion):
        if not isinstance(nodo, ast.Call):
            continue
        nombre = _nombre_llamado(nodo.func)
        if nombre.endswith("crear_backup_boveda_sqlite"):
            respaldo.append(nodo.lineno)
        elif nombre.endswith("sincronizar_distribuciones_soberanas_partidos"):
            puente.append(nodo.lineno)
        elif nombre == "write_transaction":
            escritura.append(nodo.lineno)
    assert len(respaldo) == 1, "el resguardo del lote se invoca UNA sola vez (jamás por escritura)."
    assert puente and escritura, "el lote debe publicar por el puente 3NF y sellar la captura."
    assert respaldo[0] < min(puente), "el Resguardo WORM debe preceder a la DML del puente 3NF."
    assert respaldo[0] < min(escritura), "el Resguardo WORM debe preceder al sellado de captura."

    invocaciones = [
        nodo for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and _nombre_llamado(nodo.func).endswith("crear_backup_boveda_sqlite")
    ]
    assert len(invocaciones) == 1, "una sola materialización de respaldo en todo el módulo."

    fuente = RUTA_HOMOLOGACION.read_text(encoding="utf-8")
    assert "🛡️ [RESGUARDO WORM]" in fuente, "el lote debe anunciar su resguardo con el marcador sellado."
    assert 'parte["resguardo_worm"]' in fuente, "la ruta del respaldo debe publicarse en el parte."

    # ── (b) El vector homólogo publica los hechos de plaza REALES (altitud catalogada, [LN-QBE-109])
    gateway = boveda_gateway_aislada
    with gateway.read_session() as sesion:
        partidos = _partidos_consumados(sesion, COMPETENCIA_CANONICA)
        cache = _telemetria_3nf(sesion, _identidad_partidos(partidos))
        assert cache, "la bóveda de certificación debe portar `match_telemetry`."

        elegido = None
        for p in partidos:
            if int(p["jornada"]) < 2:
                continue
            alt_h = altitud_estadio(p["home_team_slug"])
            alt_a = altitud_estadio(p["away_team_slug"])
            if alt_h is None or alt_a is None:
                continue
            corte_h = _partidos_de_club(partidos, p["home_team_slug"], int(p["jornada"]))
            corte_a = _partidos_de_club(partidos, p["away_team_slug"], int(p["jornada"]))
            if _volumen_porteria_corte(corte_h, cache) and _volumen_porteria_corte(corte_a, cache):
                elegido = (p, alt_h, alt_a, corte_h, corte_a)
                break
        assert elegido is not None, (
            "la cartelera debe portar un duelo J>=2 con ambas plazas catalogadas y telemetría íntegra."
        )
        partido, alt_h, alt_a, corte_h, corte_a = elegido

        fixture = {
            "id_partido": partido["match_id"],
            "home_team_slug": partido["home_team_slug"],
            "away_team_slug": partido["away_team_slug"],
            "fecha_dt": None,
        }
        armado = _vector_homologo(
            sesion, 1, int(partido["jornada"]), fixture, partidos, cache, "telemetria_3nf"
        )
        assert armado is not None
        item, _traza = armado

        assert item["altitud_local"] == pytest.approx(alt_h)
        assert item["altitud_visita"] == pytest.approx(alt_a)
        assert item["delta_alt_metros"] == pytest.approx(max(0.0, alt_h - alt_a))

        # Volumen & Portería: `sot`/`sota` como TASA POR PARTIDO del corte ([LN-QBE-119]) y posesión
        # media del corte (cobertura ÍNTEGRA).
        volumen_h = _volumen_porteria_corte(corte_h, cache)
        volumen_a = _volumen_porteria_corte(corte_a, cache)
        for corte, volumen in ((corte_h, volumen_h), (corte_a, volumen_a)):
            sot_esperado = sota_esperado = suma = 0.0
            for p in corte:
                registro = (cache.get(p["match_id"]) or {})["home" if p["es_local"] else "away"]
                sot_esperado += float(registro["sot"])
                sota_esperado += float(registro["sota"])
                suma += float(registro["possession"])
            partidos_corte = float(len(corte))
            # [LN-QBE-119] La casilla `V06`/`V11` rotula «por partido»: se certifica la TASA (3
            # decimales), jamás la sumatoria del corte (que multiplicaba la magnitud exhibida por PJ).
            assert volumen["sot"] == pytest.approx(round(sot_esperado / partidos_corte, 3), abs=1e-6)
            assert volumen["sota"] == pytest.approx(round(sota_esperado / partidos_corte, 3), abs=1e-6)
            assert volumen["possession"] == pytest.approx(round(suma / partidos_corte, 3), abs=1e-6)
            assert 0.0 <= volumen["sot"] <= 15.0 and 0.0 <= volumen["sota"] <= 15.0, (
                "Violación [LN-QBE-119]: una tasa por partido no puede portar la sumatoria del corte."
            )

        assert item["home_team_stats"]["sot"] == pytest.approx(volumen_h["sot"], abs=1e-9)
        assert item["home_team_stats"]["possession"] == pytest.approx(
            volumen_h["possession"], abs=1e-9
        )

        # ── (c) Cadena E2E: el motor recibe esos hechos y los declara en la traza ──────────────
        salida = generar_distribucion_soberana(match_id=item["match_id"], raw_match_data=item)
        anidado = salida.audit_trace.insumos_factivados
        contexto = anidado["contexto"]["insumos"]
        assert contexto["delta_alt_metros"] == pytest.approx(item["delta_alt_metros"])
        assert contexto["altitud_local"] == pytest.approx(alt_h)
        assert contexto["altitud_visita"] == pytest.approx(alt_a)
        if item["descanso_local"] is not None:
            assert contexto["descanso_local"] == pytest.approx(item["descanso_local"])
        assert anidado["volumen_porteria"]["insumos"]["sot_local"] == pytest.approx(
            item["home_team_stats"]["sot"]
        )
        assert anidado["trayectoria"]["status"] == "SIN_EVIDENCIA"


