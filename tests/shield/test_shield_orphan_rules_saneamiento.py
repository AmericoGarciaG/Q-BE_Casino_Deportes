# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DEL SANEAMIENTO O-05
[LN-QBE-060-B] & [ARCH-1.4.9] & [GOVERNANCE-01]
Régimen: [DIRGEN-STRICT]

Invariantes:
1. El triaje exige la presencia fáctica de las cuotas comerciales: si `L`, `E` o `V`
   faltan o son menores a 1.0, el partido colapsa de inmediato a `QBE-00` con alpha 0.0.
2. Los motores `evaluator.py` y `portfolio_math.py` no contienen constantes de reemplazo
   de precio (2.5, 3.0, 3.5, 1.60) usadas como fallback o proxy sintético.
"""

import ast
import math
from pathlib import Path

import pytest

import src.ingestion.normalizer as normalizer
from src.core.contracts.portfolio_math import (
    aplicar_hard_caps_con_respeto_a_piso,
    calcular_probabilidad_exito_estrategia,
    triaje_determinista_9_estrategias,
)
from src.core.contracts.progol_math import generar_universo_restringido_y_ordenar_p_prime
from src.ingestion.progol_scraper import PRIOR_IGNORANCIA_FIDUCIARIA

RAIZ = Path(__file__).resolve().parents[2]
ARCHIVOS_MOTOR = (
    RAIZ / "src" / "core" / "evaluator.py",
    RAIZ / "src" / "core" / "contracts" / "portfolio_math.py",
)
CONSTANTES_PROHIBIDAS = {2.5, 3.0, 3.5, 1.60}
CLAVES_PRECIO = {
    "L", "E", "V",
    "o_fav", "o_emp", "o_und",
    "momio_sintetico_x2", "cuota", "momio", "precio",
}
MOTIVO_VETO = "Cuotas comerciales ausentes o inválidas. Mercado suspendido o no capturado."


def _payload_soberano() -> dict:
    """Payload canónico operable: la morfología y el delta epistémico no disparan cuarentena."""
    return {
        "p_local": 0.45,
        "p_empate": 0.23,
        "p_visitante": 0.32,
        "es_operable": True,
        "delta_epist": 0.03,
    }


def _es_clave_de_precio(nodo: ast.AST) -> bool:
    return (
        isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
        and nodo.value in CLAVES_PRECIO
    )


def _constantes_prohibidas_en(nodo: ast.AST) -> set:
    """Constantes numéricas del subárbol que coinciden con los precios sintéticos prohibidos."""
    encontradas = set()
    for hijo in ast.walk(nodo):
        if (
            isinstance(hijo, ast.Constant)
            and isinstance(hijo.value, float)
            and hijo.value in CONSTANTES_PROHIBIDAS
        ):
            encontradas.add(float(hijo.value))
    return encontradas


class TestSaneamientoCuotasSinteticas:
    @pytest.mark.parametrize(
        "cuotas",
        [
            {"L": None, "E": 3.0, "V": 2.5},
            {"L": 0.0, "E": 3.0, "V": 2.5},
            {"L": 1.7, "E": None, "V": 2.5},
            {"L": 1.7, "E": 0.0, "V": 2.5},
            {"L": 1.7, "E": 3.0, "V": None},
            {"L": 1.7, "E": 3.0, "V": 0.9},
        ],
        ids=[
            "L_ausente", "L_cero",
            "E_ausente", "E_cero",
            "V_ausente", "V_menor_a_1",
        ],
    )
    def test_evaluador_rechaza_cuotas_ausentes(self, cuotas):
        """[P1-3] Mercado incompleto: veto fiduciario inmediato, sin fallback ni proxy."""
        resultado = triaje_determinista_9_estrategias(_payload_soberano(), cuotas)
        assert resultado["codigo"] == "QBE-00", (
            "🚨 VIOLACIÓN [LN-QBE-060-B / Saneamiento O-05]: el triaje emitió "
            f"{resultado['codigo']} con cuotas inválidas {cuotas}. El mercado incompleto "
            "debe colapsar a QBE-00 por Veto Fiduciario."
        )
        assert resultado["alpha"] == 0.0, (
            "🚨 VIOLACIÓN [LN-QBE-060-B]: el veto fiduciario no puede transportar alpha > 0."
        )
        assert resultado["pa"] is False, (
            "🚨 VIOLACIÓN [LN-QBE-060-B]: el veto fiduciario no puede habilitar Pago Anticipado."
        )
        assert resultado["motivo"] == MOTIVO_VETO, (
            f"Motivo de veto inesperado: {resultado.get('motivo')!r}"
        )

    def test_motores_sin_constantes_de_precio_sintetico(self):
        """AST: ningún `.get()` de precio ni asignación de cuota usa 2.5 / 3.0 / 3.5 / 1.60."""
        for archivo in ARCHIVOS_MOTOR:
            arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
            for nodo in ast.walk(arbol):
                if (
                    isinstance(nodo, ast.Call)
                    and isinstance(nodo.func, ast.Attribute)
                    and nodo.func.attr == "get"
                    and nodo.args
                    and _es_clave_de_precio(nodo.args[0])
                ):
                    for default in nodo.args[1:]:
                        prohibidas = _constantes_prohibidas_en(default)
                        assert not prohibidas, (
                            f"🚨 {archivo.name}: fallback de precio sintético {sorted(prohibidas)} "
                            f"en `.get({ast.unparse(nodo.args[0])}, ...)` (línea {nodo.lineno})."
                        )
                if isinstance(nodo, ast.Assign):
                    for objetivo in nodo.targets:
                        if isinstance(objetivo, ast.Name) and objetivo.id in CLAVES_PRECIO:
                            prohibidas = _constantes_prohibidas_en(nodo.value)
                            assert not prohibidas, (
                                f"🚨 {archivo.name}: asignación de precio sintético "
                                f"{sorted(prohibidas)} a `{objetivo.id}` (línea {nodo.lineno})."
                            )

    def test_evaluator_sin_numeros_magicos_de_precio(self):
        """AST estricto: `evaluator.py` no conserva ninguna de las cuatro constantes prohibidas."""
        archivo = RAIZ / "src" / "core" / "evaluator.py"
        arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        prohibidas = _constantes_prohibidas_en(arbol)
        assert not prohibidas, (
            f"🚨 {archivo.name}: persisten constantes de precio {sorted(prohibidas)}; "
            "el evaluador debe consumir cuotas fácticas, no fabricarlas."
        )


class TestAduanaIdentidadEstricta:
    """[P1-4 / Saneamiento O-09] Aduana de identidad sin subcadenas y Fail-Loud."""

    def test_normalizer_no_permite_subcadenas(self):
        """Una subcadena no puede secuestrar la identidad de otro club."""
        for nombre in ("Club América Femenil", "Atlas FC Sub-20"):
            try:
                resultado = normalizer.canonicalize_team_name(nombre)
            except normalizer.NormalizationException:
                continue
            raise AssertionError(
                f"'{nombre}' fue resuelto por contención de subcadena hacia '{resultado}'; "
                "debió lanzar NormalizationException."
            )

    def test_normalizer_fail_loud_unknown_team(self):
        """Un nombre inventado debe lanzar NormalizationException, jamás retornar el crudo."""
        try:
            resultado = normalizer.canonicalize_team_name("Equipo Inexistente FC")
        except normalizer.NormalizationException as exc:
            assert "Equipo Inexistente FC" in str(exc), (
                "La excepción debe identificar el nombre que no pudo resolverse."
            )
            return
        raise AssertionError(
            f"El normalizador retornó el texto crudo '{resultado}' en lugar de lanzar "
            "NormalizationException."
        )

    def test_normalizer_acepta_typos_validos(self):
        """Los typos dentro de los umbrales H10 sí deben resolver a la identidad canónica."""
        assert normalizer.canonicalize_team_name("Rayados Monterrey") == "Rayados de Monterrey"
        assert normalizer.canonicalize_team_name("Chivas Guadalajra") == "Chivas Guadalajara"


class TestProgolPriorIgnorancia:
    """[P1-5 / Saneamiento O-08] Prior fiduciario formal, sin literales 0.3333 huérfanos."""

    def test_progol_no_usa_fallback_magico_3333(self):
        """14 partidos sin `p_qbe` deben expandirse con el prior (0.3333, 0.3333, 0.3334)."""
        partidos_14 = [
            {"order": i, "local": f"Local_{i}", "visitante": f"Visita_{i}"}
            for i in range(1, 15)
        ]
        p_prime = generar_universo_restringido_y_ordenar_p_prime(partidos_14)
        assert len(p_prime) == 2 ** 14

        combinacion_modal, p_max = p_prime[0]
        assert combinacion_modal == ("V",) * 14, (
            "Con el prior formal, el desenlace de mayor masa es la visita (0.3334)."
        )

        # La función redondea a 8 decimales; la tolerancia fina distingue el prior real
        # (0.3334) de un relleno uniforme 0.3333 sin depender del redondeo.
        prior_max = max(PRIOR_IGNORANCIA_FIDUCIARIA)
        assert math.isclose(p_max, prior_max ** 14, rel_tol=0.0, abs_tol=5e-10), (
            f"La probabilidad modal {p_max!r} no corresponde a {prior_max} ** 14."
        )
        assert not math.isclose(p_max, 0.3333 ** 14, rel_tol=0.0, abs_tol=5e-10), (
            "La masa conjunta coincide con un relleno uniforme 0.3333; el prior no se aplicó."
        )

    def test_progol_sin_literal_3333_en_el_universo(self):
        """AST: la conjunción y la cobertura usan la constante formal, no un literal 0.3333."""
        archivo = RAIZ / "src" / "core" / "contracts" / "progol_math.py"
        arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        funciones = {
            "generar_universo_restringido_y_ordenar_p_prime",
            "seleccionar_cobertura_binaria_optima",
        }
        hallados = []
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.FunctionDef) and nodo.name in funciones:
                for hijo in ast.walk(nodo):
                    if (
                        isinstance(hijo, ast.Constant)
                        and isinstance(hijo.value, float)
                        and hijo.value == 0.3333
                    ):
                        hallados.append((nodo.name, hijo.lineno))
        assert not hallados, (
            f"🚨 {archivo.name}: literales 0.3333 huérfanos en {hallados}; "
            "deben provenir del prior fiduciario legislado."
        )

        nombres = {n.id for n in ast.walk(arbol) if isinstance(n, ast.Name)}
        assert (
            "PRIOR_IGNORANCIA_FIDUCIARIA" in nombres or "PROB_IGNORANCIA" in nombres
        ), (
            "La función no referencia una constante/tupla formal del prior fiduciario."
        )


class TestGuardasFinancierasO06O07:
    """[P2-6a] Fail-Loud de cuota de empate (O-06) y neutralidad cero (O-07)."""

    def test_prorrateo_exige_odd_emp(self):
        """Una orden de cobertura sin `odd_emp` que entra al prorrateo debe lanzar ValueError."""
        ordenes = [
            {"strategy_code": "QBE-H1", "inversion_total": 8.0},
            {"strategy_code": "QBE-H1", "inversion_total": 8.0, "odd_emp": 3.30},
            {"strategy_code": "QBE-H1", "inversion_total": 8.0, "odd_emp": 3.30},
            {"strategy_code": "QBE-H1", "inversion_total": 8.0, "odd_emp": 3.30},
        ]
        with pytest.raises(ValueError) as excinfo:
            aplicar_hard_caps_con_respeto_a_piso(ordenes, bankroll=100.0)
        assert "odd_emp" in str(excinfo.value).lower() or "O-06" in str(excinfo.value), (
            f"El ValueError debe identificar la cuota de empate ausente: {excinfo.value!r}"
        )

    def test_probabilidad_exito_c1_denominador_cero(self):
        """QBE-C1 con denominador cero vale estrictamente 0.0, nunca el neutral 0.50."""
        resultado = calcular_probabilidad_exito_estrategia(
            "QBE-C1", p_fav_p=0.0, p_emp_p=0.0, p_und_p=0.0
        )
        assert resultado == 0.0, (
            f"🚨 [O-07] QBE-C1 con denominador cero retornó {resultado!r}; "
            "el fallback neutral 0.50 está derogado."
        )


class TestConstantesFisicasFormalizadas:
    """[P2-6c / O-04 y O-14] Clamps y saturaciones bautizados, sin literales quemados."""

    def test_constantes_fisicas_formalizadas(self):
        """Las nueve constantes de CONSTANTS.md §8 existen y los motores las consumen."""
        prohibidos = {1.35, 6.0, 0.40, 1.60, 0.65, 0.35, 6.00, 0.05, 0.02}
        archivos = (
            RAIZ / "src" / "core" / "poisson.py",
            RAIZ / "src" / "core" / "evaluator.py",
            RAIZ / "src" / "web" / "routes" / "markets.py",
        )
        for archivo in archivos:
            fuente = archivo.read_text(encoding="utf-8")
            arbol = ast.parse(fuente, filename=str(archivo))
            padres = {
                hijo: padre
                for padre in ast.walk(arbol)
                for hijo in ast.iter_child_nodes(padre)
            }
            hallados = set()
            for nodo in ast.walk(arbol):
                if not (
                    isinstance(nodo, ast.Constant)
                    and isinstance(nodo.value, float)
                    and float(nodo.value) in prohibidos
                ):
                    continue
                padre = padres.get(nodo)
                if isinstance(padre, ast.UnaryOp) and isinstance(padre.op, ast.USub):
                    # `-0.0500` es la correlación Dixon-Coles, no el clamp positivo 0.05.
                    continue
                hallados.add(float(nodo.value))
            hallados = sorted(hallados)
            assert not hallados, (
                f"🚨 {archivo.name}: literales físicos quemados {hallados}; "
                "deben importarse de src/core/constants.py."
            )
            assert "from src.core.constants import" in fuente, (
                f"🚨 {archivo.name}: no importa las constantes formalizadas de src/core/constants.py."
            )

        from src.core import constants

        esperadas = {
            "BASELINE_LIGA": 1.35,
            "SATURACION_MADUREZ_J": 6.0,
            "OMEGA_MIN": 0.40,
            "OMEGA_MAX": 1.60,
            "BLEND_XG": 0.65,
            "BLEND_GF": 0.35,
            "CLAMP_GOLES_MIN": 0.05,
            "CLAMP_GOLES_MAX": 6.00,
            "DELTA_EPIST_DEFAULT": 0.02,
        }
        for nombre, valor in esperadas.items():
            assert hasattr(constants, nombre), f"Falta la constante `{nombre}` en src/core/constants.py"
            assert getattr(constants, nombre) == valor, (
                f"`{nombre}` = {getattr(constants, nombre)!r} ≠ valor legislado {valor!r}"
            )


class TestGobernanzaSinComentarios:
    """[P2-8 / O-12] La gobernanza vive en la ley, no en comentarios de código."""

    def test_gobernanza_por_comentarios_erradicada(self):
        """Los tags de varianza desaparecen de los comentarios y se ancla [LN-QBE-130]."""
        archivos = (
            RAIZ / "src" / "storage" / "curation_service.py",
            RAIZ / "src" / "storage" / "seeder.py",
        )
        prohibidas = ("VARIANZA-09", "ALT-9-A", "ALT-9-B", "ALT-9-C")
        for archivo in archivos:
            contenido = archivo.read_text(encoding="utf-8")
            for token in prohibidas:
                assert token not in contenido, (
                    f"🚨 {archivo.name}: persiste la gobernanza por comentarios `{token}`; "
                    "debe referenciar [LN-QBE-130]."
                )
            assert "[LN-QBE-130]" in contenido, (
                f"🚨 {archivo.name}: no referencia el nodo legislado [LN-QBE-130]."
            )

    def test_censo_regimen_correcto(self):
        """El Censo C.2 es documento inmutable: su Régimen es [DIRGEN-STRICT] puro."""
        ruta = RAIZ / "docs" / "ORPHAN_RULES_CENSUS.md"
        contenido = ruta.read_text(encoding="utf-8")
        regimen = next(
            (linea for linea in contenido.splitlines() if linea.startswith("**Régimen:**")),
            None,
        )
        assert regimen is not None, "El Censo no publica su línea de Régimen."
        assert "[DIRGEN-STRICT]" in regimen, (
            f"🚨 El Régimen del Censo no es [DIRGEN-STRICT]: {regimen!r}"
        )
        assert "HÍBRIDO" not in regimen and "DBBD-FUNGIBLE" not in regimen, (
            f"🚨 El Censo conserva un régimen fungible: {regimen!r}"
        )


class TestNudo1ErradicacionMasaFabricada:
    """[FASE 2 · BLOQUE 1 — NUDO 1] Erradicación de la masa de probabilidad fabricada.

    Régimen: [DIRGEN-STRICT]. Estos jueces certifican la legislación de
    `[LN-QBE-093]` (Enmienda Nudo 1), `[LN-QBE-070-C]` (Enmienda Nudo 1) y
    `[GOVERNANCE-01]` (Enmienda Nudo 1). En Fase 2 deben estar en ROJO; en Fase 3
    (materialización en `src/`) deben pasar sin una sola concesión.
    """

    LITERALES_PROHIBIDOS_TESIS = ("1.80", "0.80", "70.0%", "$16.00")

    def test_gemini_sensor_eliminado(self):
        """[LN-QBE-093 · Enmienda Nudo 1] El sensor de contingencia está extirpado del árbol."""
        ruta = RAIZ / "src" / "ingestion" / "providers" / "gemini_search_sensor.py"
        assert not ruta.exists(), (
            "🚨 VIOLACIÓN [LN-QBE-093 · Enmienda Nudo 1]: el sensor genérico de búsqueda "
            f"`{ruta.relative_to(RAIZ)}` sigue presente en el árbol. [ARCH-1.3.4] lo extirpó "
            "del pipeline y el Axioma de Cero Mocks prohíbe su existencia como fuente de "
            "datos de contingencia."
        )

    def test_dtos_no_fabrican_mercado_ni_confianza(self):
        """[LN-QBE-093 · Enmienda Nudo 1] Sin evidencia no hay mercado ni confianza del 100%."""
        from pydantic import ValidationError

        from src.models.raw_input import RawMatchInput

        try:
            raw = RawMatchInput()
        except ValidationError:
            # Post-Fase 3: el contrato exige evidencia y rechaza el payload vacío.
            return

        cuotas = getattr(raw, "momios", None)
        pago_anticipado = getattr(cuotas, "pago_anticipado", None) if cuotas is not None else None
        assert cuotas is None or pago_anticipado is None, (
            "🚨 VIOLACIÓN [LN-QBE-093 · Enmienda Nudo 1]: `RawMatchInput()` sin cuotas "
            "materializa un mercado sintético por defecto "
            f"({pago_anticipado!r}). La ausencia de precio debe viajar como `None`."
        )

        confiabilidad = getattr(getattr(raw, "trazabilidad_consenso", None), "confiabilidad_porcentaje", None)
        assert confiabilidad != 100.0, (
            "🚨 VIOLACIÓN [LN-QBE-093 · Enmienda Nudo 1]: `confiabilidad_porcentaje` nace en "
            f"{confiabilidad!r}. Declarar 100% por defecto desactiva la aduana de "
            "`[LN-QBE-010]` (confiabilidad < 80.0% ⇒ Veto QBE-00)."
        )

    @staticmethod
    def _ordenes_normalizadas(plan) -> list:
        """Normaliza `PortfolioExecutionPlan` (Pydantic) o su volcado plano a `[{codigo, inversion}]`."""
        crudas = getattr(plan, "ordenes_ejecucion_partidos", None)
        if crudas is None and isinstance(plan, dict):
            crudas = plan.get("ordenes_ejecucion_partidos", [])

        normalizadas = []
        for orden in crudas or []:
            if isinstance(orden, dict):
                estrategia = orden.get("estrategia_seleccionada") or {}
                boletos = orden.get("boletos") or {}
                codigo = (
                    estrategia.get("codigo")
                    if isinstance(estrategia, dict)
                    else getattr(estrategia, "codigo", None)
                )
                inversion = (
                    boletos.get("inversion_partido_A_i", 0.0)
                    if isinstance(boletos, dict)
                    else getattr(boletos, "inversion_partido_A_i", 0.0)
                )
            else:
                estrategia = getattr(orden, "estrategia_seleccionada", None)
                boletos = getattr(orden, "boletos", None)
                codigo = getattr(estrategia, "codigo", None)
                inversion = getattr(boletos, "inversion_partido_A_i", 0.0)
            normalizadas.append(
                {"codigo": str(codigo or ""), "inversion": float(inversion or 0.0)}
            )
        return normalizadas

    def test_portfolio_no_fabrica_distribucion_55_25_20(self):
        """[LN-QBE-070-C · Enmienda Nudo 1] Un candidato sin distribución no se dimensiona."""
        from pydantic import ValidationError

        from src.core.portfolio import PortfolioEngine

        candidato = {
            "id_partido": "SCR-F2-NUDO1-01",
            "partido_nombre": "Candidato sin distribución soberana",
            "horario": "Sábado 19:00",
            "strategy_code": "QBE-H1",
            "strategy_nombre": "Favorito con Seguro en Empate",
            "ev_neto_roi": 0.05,
            "psi_downside": 0.90,
            "odd_fav": 1.80,
            "odd_emp": 3.60,
            "odd_und": 4.20,
            "fav_name": "Local",
            "und_name": "Visita",
            "delta_epist": 0.02,
        }

        try:
            plan = PortfolioEngine.build_plan(
                [candidato],
                bankroll=100.0,
                mode="BANKROLL",
                total_jornada=9,
                modo_cobertura="DEF",
            )
        except Exception as exc:
            # Una excepción sólo certifica la erradicación si es de DOMINIO (dato ausente).
            # Un `KeyError` genérico —o cualquier error de implementación— NO es señal de éxito.
            assert isinstance(exc, (ValueError, ValidationError)), (
                "🚨 Excepción inesperada en `build_plan` ante un candidato sin distribución: "
                f"{type(exc).__name__}: {exc}. El motor debe rechazar el dato ausente en voz "
                "alta (ValueError/ValidationError) o vetar en cuarentena; un `KeyError` "
                "genérico no certifica la erradicación de la fábrica 55/25/20."
            )
        else:
            ordenes = self._ordenes_normalizadas(plan)
            con_capital = [
                orden
                for orden in ordenes
                if orden["inversion"] > 0.0 and orden["codigo"] != "QBE-00"
            ]
            assert not con_capital, (
                "🚨 VIOLACIÓN [LN-QBE-070-C · Enmienda Nudo 1]: `build_plan` asignó capital a "
                f"{len(con_capital)} orden(es) sobre un candidato SIN probabilidades: "
                f"{con_capital}. La distribución 55/25/20 (y 70/20/10 en la Trinidad) está "
                "prohibida: la ausencia debe reflejarse como `None` y derivar en cuarentena "
                f"(QBE-00) o en inversión $0.00 MXN; se observaron {ordenes}."
            )

    def test_tesis_madlibs_no_inventa_cifras(self):
        """[GOVERNANCE-01 · Enmienda Nudo 1] La degradación narrativa no inyecta cifras."""
        from src.reporting.narrative import generar_tesis_madlibs_fallback

        texto = generar_tesis_madlibs_fallback({})
        hallados = [literal for literal in self.LITERALES_PROHIBIDOS_TESIS if literal in texto]
        assert not hallados, (
            "🚨 VIOLACIÓN [GOVERNANCE-01 · Enmienda Nudo 1]: `generar_tesis_madlibs_fallback` "
            f"inyecta las cifras fabricadas {hallados} con un payload vacío. El fallback debe "
            "ceñirse a los datos fácticos disponibles y declarar su naturaleza determinista "
            "(sello Mad-Libs)."
        )
