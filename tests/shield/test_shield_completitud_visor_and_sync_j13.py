# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DE COMPLETITUD DEL VISOR 44V Y SINCRONÍA DE JORNADAS
Gobierno: `[LN-QBE-119]` · `[ARCH-1.4.58]` · `[GOV-TEST-01]` (hermético: cero red, cero DML, cero
navegador). Régimen dual: la telemetría dimensional (`[ARCH-1.4.58]`) es aditiva sobre el DTO y la
tasa por partido (`[LN-QBE-119]`) es una ley de UNIDAD sobre una suma ya existente — ninguna
constante matemática sellada cambia.

Qué certifica este Juez
-----------------------
1. Los tres contadores dimensionales sobreviven al DTO (`extra="ignore"`) y el catálogo suma 32.
2. La sonda `auditar_completitud_visor` detecta la sumatoria de torneo en una casilla de tasa y
   certifica la tasa limpia; también el `0 de 0`, el badge incoherente y el alias `conteo` roto.
3. La homologación publica `sot`/`sota` como TASA por partido (3 decimales), no como acumulado.
4. El Centro de Control despacha la sonda como 19ª tarea certificada.
5. El Visor barre J1→J17 sin techo de jornada escondido y la UI declara la sub-pestaña renombrada.
"""

from pathlib import Path

import pytest

from src.core.sovereign.factor_attribution import estructurar_catalogo_44_variables
from src.models.web_schemas import (
    AtribucionDimensionOut,
    Catalogo44Out,
    SimulatePortfolioRequest,
)

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
TAMANOS_CATALOGO = (5, 6, 5, 4, 5, 7)  # 32 variables en las 6 dimensiones [LN-QBE-120]


# ── Constructores de casillas sintéticas (cero base de datos) ─────────────────────────────────
def _variable(identificador: str, local, visita) -> dict:
    """Celda forense con la anatomía servida por `[LN-QBE-101]`."""
    return {
        "id": identificador,
        "variable": identificador,
        "local": local,
        "visita": visita,
        "z_score": None,
        "origen": "Q-BE",
        "estado": "EVALUADO" if (local is not None or visita is not None) else "SIN EVIDENCIA",
        "impacto": "",
        "nota": "",
    }


def _dimension(nombre: str, tamano: int, variables: list, **sobrescrituras) -> dict:
    """Dimensión canónica con contadores coherentes salvo que el caso pida romperlos."""
    evaluadas = sum(1 for v in variables if v["local"] is not None or v["visita"] is not None)
    fila = {
        "dimension": nombre,
        "titulo": nombre,
        "conteo": tamano,
        "total_variables": tamano,
        "variables_evaluadas": evaluadas,
        "tiene_datos": evaluadas > 0,
        "variables": variables,
    }
    fila.update(sobrescrituras)
    return fila


def _casilla(sot=(None, None), poss=(None, None)) -> dict:
    """Casilla micro con el catálogo íntegro de 32 variables repartidas en 6 dimensiones."""
    dimensiones = []
    for indice, tamano in enumerate(TAMANOS_CATALOGO):
        variables = []
        if indice == 0:
            variables.append(_variable("V01", *poss))
        elif indice == 1:
            variables.append(_variable("V07", *sot))
        elif indice == 2:
            variables.append(_variable("V13", *sot))
        while len(variables) < tamano:
            variables.append(_variable(f"R{indice}{len(variables)}", None, None))
        dimensiones.append(_dimension(f"𝒯_{indice}", tamano, variables))
    return {
        "jornada": 5,
        "id_partido": "LIGAMX-J05-01",
        "atribucion_factorial": {"variables_44": {"dimensiones": dimensiones}},
    }


# ── 1. CONTRATO ADITIVO DEL DTO ([ARCH-1.4.58]) ───────────────────────────────────────────────
def test_arch_1_4_58_telemetria_dimensional_sobrevive_al_dto():
    """El DTO publica `total_variables`/`variables_evaluadas`/`tiene_datos` sin romper `[LN-QBE-101]`."""
    campos = AtribucionDimensionOut.model_fields
    for nombre in ("total_variables", "variables_evaluadas", "tiene_datos"):
        assert nombre in campos, f"Falta el contador aditivo `{nombre}` en `AtribucionDimensionOut`."
        # Aditivo de verdad: con default ⇒ ningún consumidor previo queda obligado a enviarlo.
        assert not campos[nombre].is_required(), f"`{nombre}` debe portar default (contrato aditivo)."
    assert campos["total_variables"].default == 0
    assert campos["variables_evaluadas"].default == 0
    assert campos["tiene_datos"].default is False

    catalogo = Catalogo44Out.model_validate(estructurar_catalogo_44_variables({}))
    assert catalogo.total_variables == 32
    assert len(catalogo.dimensiones) == 6
    assert sum(dimension.total_variables for dimension in catalogo.dimensiones) == 32
    for dimension in catalogo.dimensiones:
        # Cero `0 de 0`: toda dimensión declara denominador real y `conteo` lo espeja.
        assert dimension.total_variables > 0, f"`{dimension.dimension}` publica denominador nulo."
        assert dimension.conteo == dimension.total_variables
        assert dimension.tiene_datos == (dimension.variables_evaluadas > 0)
        assert dimension.variables_evaluadas == 0  # insumo vacío ⇒ cero evidencia, cero invención
        assert dimension.tiene_datos is False


# ── 2. SONDA: LEY DE UNIDAD Y COTAS FÍSICAS ([LN-QBE-119]) ────────────────────────────────────
def test_ln_qbe_119_sonda_detecta_sumatoria_de_torneo_en_casilla_de_tasa():
    """Una sumatoria de corte (41 tiros a puerta) en la casilla «por partido» se declara 🔴."""
    from scripts.auditoria.auditar_completitud_visor import _auditar_partido

    acumulada = _auditar_partido(_casilla(sot=(41.0, 56.0), poss=(52.0, 48.0)))
    codigos = [anomalia["codigo"] for anomalia in acumulada["anomalias"]]
    assert "COTA_SOT" in codigos, "La sonda debe detectar la sumatoria de torneo en V07/V13."
    assert acumulada["anomalias"], "Una casilla con sumatoria no puede salir limpia."
    assert acumulada["sot"] == pytest.approx(48.5)

    limpia = _auditar_partido(_casilla(sot=(5.0, 7.0), poss=(55.0, 45.0)))
    assert limpia["anomalias"] == [], f"Tasa limpia con anomalías: {limpia['anomalias']}"
    assert limpia["sot"] == pytest.approx(6.0)
    assert limpia["poss"] == pytest.approx(50.0)
    assert limpia["evaluadas"] == 3 and limpia["total"] == 32


def test_ln_qbe_119_sonda_certifica_cero_sobre_cero_y_badge_coherente():
    """`0 de 0`, badge sin evidencia, alias `conteo` roto y catálogo ausente son anomalías 🔴."""
    from scripts.auditoria.auditar_completitud_visor import _auditar_partido

    # (a) Denominador nulo: la dimensión no puede declarar 0 variables totales.
    nula = _casilla()
    nula["atribucion_factorial"]["variables_44"]["dimensiones"][3] = _dimension(
        "𝒯_Por", 0, [], conteo=0
    )
    codigos = [a["codigo"] for a in _auditar_partido(nula)["anomalias"]]
    assert "DENOMINADOR_NULO" in codigos

    # (b) Badge incoherente: `SIN EVALUAR` con evidencia evaluada (o al revés).
    incoherente = _casilla(sot=(4.0, 6.0), poss=(50.0, 50.0))
    incoherente["atribucion_factorial"]["variables_44"]["dimensiones"][1]["tiene_datos"] = False
    codigos = [a["codigo"] for a in _auditar_partido(incoherente)["anomalias"]]
    assert "BADGE_INCOHERENTE" in codigos

    # (c) Alias histórico `conteo` divergente del denominador real.
    desalineada = _casilla(sot=(4.0, 6.0), poss=(50.0, 50.0))
    desalineada["atribucion_factorial"]["variables_44"]["dimensiones"][2]["conteo"] = 99
    codigos = [a["codigo"] for a in _auditar_partido(desalineada)["anomalias"]]
    assert "CONTEO_DIVERGENTE" in codigos

    # (d) Casilla sin catálogo 44V: no se inventa una medición vacía.
    sin_catalogo = _auditar_partido({"jornada": 7, "id_partido": "X", "atribucion_factorial": {}})
    assert [a["codigo"] for a in sin_catalogo["anomalias"]] == ["SIN_CATALOGO_44V"]
    assert sin_catalogo["total"] == 0 and sin_catalogo["sot"] is None




# ── 3. HOMOLOGACIÓN: TASA POR PARTIDO (3 DECIMALES) ───────────────────────────────────────────
def test_ln_qbe_119_homologacion_publica_tasa_por_partido():
    """`_volumen_porteria_corte` divide entre el tamaño del corte: la casilla V06 deja de mentir."""
    from scripts.ingesta.homologar_temporada_optah2h import _volumen_porteria_corte

    cache = {
        "A": {"home": {"sot": 2.0, "sota": 1.0, "possession": 50.0, "procedencia": "telemetria_3nf"}},
        "B": {"away": {"sot": 1.0, "sota": 1.0, "possession": 60.0, "procedencia": "telemetria_3nf"}},
        "C": {"home": {"sot": 3.0, "sota": 2.0, "possession": 70.0, "procedencia": "telemetria_3nf"}},
    }
    corte = [
        {"match_id": "A", "es_local": True},
        {"match_id": "B", "es_local": False},
        {"match_id": "C", "es_local": True},
    ]
    volumen = _volumen_porteria_corte(corte, cache)

    assert volumen["sot"] == pytest.approx(2.0)  # 6 / 3, NO 6 (sumatoria pre-[LN-QBE-119])
    assert volumen["sota"] == pytest.approx(round(4 / 3, 3))
    assert volumen["possession"] == pytest.approx(60.0)
    assert 0.0 <= volumen["sot"] <= 15.0 and 0.0 <= volumen["sota"] <= 15.0

    # Cobertura íntegra heredada de `[LN-QBE-118]`: una sola ausencia ⇒ el bloque no se publica.
    incompleto = dict(cache)
    incompleto["C"] = {"home": {"sot": 3.0, "sota": None, "possession": 70.0,
                                "procedencia": "telemetria_3nf"}}
    assert _volumen_porteria_corte(corte, incompleto) == {}

    # Cero mezcla de fuentes: dos niveles de procedencia ⇒ no hay agregado.
    mixto = dict(cache)
    mixto["A"] = {"home": {"sot": 2.0, "sota": 1.0, "possession": 50.0, "procedencia": "opta_cache"}}
    assert _volumen_porteria_corte(corte, mixto) == {}
    assert _volumen_porteria_corte([], cache) == {}


# ── 4. CENTRO DE CONTROL: 19ª TAREA CERTIFICADA ([ARCH-1.4.58]) ───────────────────────────────
def test_arch_1_4_58_centro_control_despacha_la_sonda():
    """La sonda es tarea gobernada: whitelist de 20 exactas y comando interno sin shell."""
    from src.web.routes.admin_tasks import COMANDOS_TAREAS, TAREAS_PERMITIDAS

    # [ARCH-1.4.67] Enmienda 2026-10-23: 19 ➔ 20 exactas al certificar `generar_matriz_investigacion`
    # (matriz canónica de investigación de 4 zonas, solo lectura). La igualdad ESTRICTA se conserva:
    # ninguna otra tarea puede colarse en la whitelist sin una enmienda registrada.
    # [ARCH-1.4.69 / ARCH-1.4.70] Enmienda Sprint 3: 20 ➔ 22 exactas al certificar
    # `sembrar_prior_apertura2025` y `mineria_factores_shannon` (instrumentos de sólo lectura).
    assert len(TAREAS_PERMITIDAS) == 22, (
        "[ARCH-1.4.58 / ARCH-1.4.67 / ARCH-1.4.69 / ARCH-1.4.70]: la whitelist debe ser de "
        "exactamente 22 tareas certificadas."
    )
    assert "auditar_completitud_visor" in TAREAS_PERMITIDAS
    assert COMANDOS_TAREAS["auditar_completitud_visor"][-1] == [
        "scripts", "auditoria", "auditar_completitud_visor.py"
    ], "El despacho debe apuntar a la sonda materializada (cero texto libre del cliente)."

    ruta = RAIZ_PROYECTO / "scripts" / "auditoria" / "auditar_completitud_visor.py"
    assert ruta.exists(), "Falta la sonda scripts/auditoria/auditar_completitud_visor.py"
    codigo = ruta.read_text(encoding="utf-8")
    assert "[LN-QBE-119]" in codigo and "[ARCH-1.4.58]" in codigo
    assert "sys.exit(main())" in codigo
    assert "write_transaction" not in codigo, "La sonda es de SÓLO LECTURA: cero DML."


# ── 5. SINCRONÍA DE JORNADAS Y PRESENTACIÓN ([ARCH-1.4.58] · V-5 intacta) ─────────────────────
def test_ln_qbe_119_visor_barre_j17_sin_techo_de_jornada():
    """El reporte de calibración no esconde jornadas y el default financiero «1-11» sigue intacto."""
    import inspect

    from scripts.auditoria import auditar_completitud_visor as sonda
    from src.web.routes import markets

    fuente = inspect.getsource(markets._construir_reporte_calibracion)
    assert "1-11" not in fuente, "El Visor no puede portar el techo financiero «1-11»."
    assert "matchday_num <=" not in fuente and "matchday_num <" not in fuente, (
        "El Visor publica toda jornada concluida con P' sellada: cero filtro de jornada."
    )

    # V-5: el default del simulador de cartera es una ley financiera distinta, no un techo del Visor.
    assert SimulatePortfolioRequest.model_fields["rango_jornadas"].default == "1-11"

    # El barrido declarativo cubre J1→J17 y acepta rangos explícitos (J13 incluida).
    assert sonda.RANGO_JORNADAS_DEFAULT == "1-17"
    assert sonda._expandir_rango("1-13") == list(range(1, 14))
    assert sonda._expandir_rango("1, 13") == [1, 13]
    with pytest.raises(ValueError):
        sonda._expandir_rango("13-1")

    # UI: sub-pestaña renombrada y sonda accesible desde `🛡️ Auditoría y Diagnóstico`.
    html = (RAIZ_PROYECTO / "src" / "web" / "templates" / "index.html").read_text(encoding="utf-8")
    assert "🎯 Calibración y Distribuciones" in html
    assert "ejecutarTareaAdmin('auditar_completitud_visor')" in html
    assert "🔍 Auditoría de Completitud Fáctica (32V)" in html
