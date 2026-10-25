# -*- coding: utf-8 -*-
"""
🛡️ JUEZ INMUTABLE: PARIDAD Y NO-DUPLICIDAD DEL AUDITOR DE COHERENCIA RELACIONAL
[ARCH-1.4.34 · Enmienda de Saneamiento] · [ARCH-1.6.4 · Enmienda Nudo 3]

Régimen: [DIRGEN-STRICT] sobre la fuente de verdad (`src/core/coherence_auditor.py`, INMUTABLE)
y sobre este Juez; [DBBD-FUNGIBLE] sobre la capa de presentación (`scripts/auditoria/`).

Invariantes auditadas:
  1. NO-DUPLICIDAD (AST): la capa de `scripts/` no define funciones, clases ni constantes de
     negocio propias; sólo publica `main()` —delegación pura al núcleo— y la guarda
     `if __name__ == "__main__":`. Prohibido re-transcribir las seis sondas, el agregador
     semafórico o el contrato de salida.
  2. PARIDAD DE IMPORTACIÓN: el script declara `from src.core.coherence_auditor import ...` y los
     símbolos que re-exporta son EL MISMO objeto que el del núcleo (`is`), no una copia rebautizada.
  3. PARIDAD FUNCIONAL: la batería de expedientes —incluidos los Sad Paths (evidencia ausente,
     vector fuera de Δ², overround fuera de aduana, λ ≤ 0, boletos bajo piso, S(I) = 0)— produce
     salida JSON idéntica por el núcleo y por el wrapper, y el CLI emite el mismo contrato.

Doctrina de la Triple Aserción (por juez): (1) contrato positivo; (2) Sad Path / control negativo;
(3) auto-verificación del propio detector (el juez demuestra que SÍ detecta la violación, para no
certificar por vacuidad).

Estado esperado en Fase 2: ROJO (el script conserva la copia duplicada). En Fase 3: VERDE.
"""

import ast
import contextlib
import io
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUTA_SCRIPT = RAIZ / "scripts" / "auditoria" / "auditar_coherencia_cartelera.py"
RUTA_NUCLEO = RAIZ / "src" / "core" / "coherence_auditor.py"
MODULO_NUCLEO = "src.core.coherence_auditor"

# Nombres que la capa de presentación SÍ puede conservar: la guarda de entrada del CLI.
FUNCIONES_PERMITIDAS_EN_SCRIPT = {"main"}


# ---------------------------------------------------------------------------
# Helpers de inspección estática (AST) — no importan los módulos auditados.
# ---------------------------------------------------------------------------
def _fuente(ruta: Path) -> str:
    assert ruta.exists(), f"Artefacto canónico no encontrado: {ruta.relative_to(RAIZ)}"
    return ruta.read_text(encoding="utf-8")


def _arbol(ruta: Path) -> ast.Module:
    return ast.parse(_fuente(ruta), filename=ruta.name)


def _definiciones(fuente: str) -> dict:
    """Inventario de lo que un módulo DEFINE localmente (no lo que importa)."""
    arbol = ast.parse(fuente)
    funciones = [
        nodo.name
        for nodo in ast.walk(arbol)
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    clases = [nodo.name for nodo in ast.walk(arbol) if isinstance(nodo, ast.ClassDef)]
    asignaciones = []
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign):
            asignaciones.extend(
                objetivo.id for objetivo in nodo.targets if isinstance(objetivo, ast.Name)
            )
        elif isinstance(nodo, ast.AnnAssign) and isinstance(nodo.target, ast.Name):
            asignaciones.append(nodo.target.id)
    return {"funciones": funciones, "clases": clases, "asignaciones": asignaciones}


def _simbolos_importados_del_nucleo(fuente: str) -> set:
    """Símbolos que el módulo declara importar explícitamente del núcleo canónico."""
    arbol = ast.parse(fuente)
    simbolos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module == MODULO_NUCLEO:
            simbolos.update(alias.asname or alias.name for alias in nodo.names)
    return simbolos


def _alias_del_nucleo(fuente: str) -> set:
    """Alias bajo los cuales el módulo enlaza el MÓDULO del núcleo (para auditar la delegación)."""
    arbol = ast.parse(fuente)
    alias = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module == "src.core":
            for nombre in nodo.names:
                if nombre.name == "coherence_auditor":
                    alias.add(nombre.asname or nombre.name)
        elif isinstance(nodo, ast.Import):
            for nombre in nodo.names:
                if nombre.name == MODULO_NUCLEO:
                    alias.add(nombre.asname or nombre.name.split(".")[0])
    return alias


def _tiene_guardia_main(arbol: ast.Module) -> bool:
    """La guarda `if __name__ == "__main__": ...` debe existir y terminar en el CLI."""
    for nodo in arbol.body:
        if not isinstance(nodo, ast.If):
            continue
        prueba = nodo.test
        comparacion = (
            isinstance(prueba, ast.Compare)
            and isinstance(prueba.left, ast.Name)
            and prueba.left.id == "__name__"
            and len(prueba.comparators) == 1
            and isinstance(prueba.comparators[0], ast.Constant)
            and prueba.comparators[0].value == "__main__"
        )
        if not comparacion:
            continue
        for llamada in (sub for sub in ast.walk(nodo) if isinstance(sub, ast.Call)):
            funcion = llamada.func
            if isinstance(funcion, ast.Attribute) and funcion.attr == "exit":
                return True
            if isinstance(funcion, ast.Name) and funcion.id == "main":
                return True
    return False


def _main_delega_en_el_nucleo(fuente: str) -> bool:
    """`main()` sólo puede invocar `<alias_núcleo>.main(argv)` y devolver su resultado."""
    alias = _alias_del_nucleo(fuente)
    arbol = ast.parse(fuente)
    for nodo in arbol.body:
        if not (isinstance(nodo, ast.FunctionDef) and nodo.name == "main"):
            continue
        for sub in ast.walk(nodo):
            if not isinstance(sub, ast.Call):
                continue
            funcion = sub.func
            if (
                isinstance(funcion, ast.Attribute)
                and funcion.attr == "main"
                and isinstance(funcion.value, ast.Name)
                and funcion.value.id in alias
            ):
                return True
    return False


# ---------------------------------------------------------------------------
# 1. NO-DUPLICIDAD LÓGICA EN LA CAPA DE SCRIPTS (AST)
# ---------------------------------------------------------------------------
def test_no_duplicidad_logica_auditor():
    """El script NO puede re-transcribir la matemática del núcleo: sólo `main()` delega."""
    fuente_script = _fuente(RUTA_SCRIPT)
    definidas = _definiciones(fuente_script)
    nucleo = _definiciones(_fuente(RUTA_NUCLEO))

    # -- Aserción 1 (contrato positivo): la capa de scripts sólo publica la guarda de entrada --
    excedentes = sorted(set(definidas["funciones"]) - FUNCIONES_PERMITIDAS_EN_SCRIPT)
    assert not excedentes, (
        "🚨 VIOLACIÓN [ARCH-1.4.34 · Enmienda de Saneamiento]: el script define funciones de "
        f"auditoría propias: {excedentes}. Toda la lógica debe residir en `{MODULO_NUCLEO}`; "
        "la capa de scripts sólo puede publicar `main()` como wrapper delegante."
    )

    # -- Aserción 2 (Sad Path / control negativo): ni clases ni constantes de negocio copiadas --
    assert not definidas["clases"], (
        "🚨 VIOLACIÓN: el script define clases propias "
        f"({definidas['clases']}); el contrato (`NivelSeveridad`, `HallazgoSonda`, "
        f"`ReporteCoherenciaPartido`) es exclusivo de `{MODULO_NUCLEO}`."
    )
    constantes_nucleo = {
        nombre for nombre in nucleo["asignaciones"] if nombre.isupper() and not nombre.startswith("_")
    }
    duplicadas = sorted(set(definidas["asignaciones"]) & constantes_nucleo)
    assert not duplicadas, (
        f"🚨 VIOLACIÓN: el script re-declara constantes selladas del núcleo: {duplicadas}. "
        "Deben importarse, jamás transcribirse."
    )
    publicas = [
        nombre for nombre in definidas["asignaciones"] if not nombre.startswith("_") and nombre != "__all__"
    ]
    assert not publicas, (
        f"🚨 VIOLACIÓN: el script publica asignaciones de módulo no privadas: {publicas}. "
        "El wrapper sólo admite bootstrap privado (`_PROJECT_ROOT`) y `__all__`."
    )

    # -- Aserción 3 (auto-verificación del juez): el detector SÍ detecta una copia duplicada --
    copia = (
        "TVD_MAX = 0.22\n\n"
        "class NivelSeveridad: ...\n\n"
        "def _sonda_paridad(data):\n"
        "    return data\n\n"
        "def auditar_coherencia_partido(data):\n"
        "    return data\n"
    )
    deteccion = _definiciones(copia)
    assert "_sonda_paridad" in deteccion["funciones"], (
        "El juez no detecta funciones duplicadas: certificaría por vacuidad."
    )
    assert "NivelSeveridad" in deteccion["clases"], (
        "El juez no detecta clases duplicadas: certificaría por vacuidad."
    )
    assert "TVD_MAX" in deteccion["asignaciones"], (
        "El juez no detecta constantes duplicadas: certificaría por vacuidad."
    )

    # -- Contrato del CLI: guarda `__main__` presente y delegación explícita al núcleo --
    assert _tiene_guardia_main(_arbol(RUTA_SCRIPT)), (
        '🚨 VIOLACIÓN: falta la guarda `if __name__ == "__main__":` en el wrapper CLI.'
    )
    assert _main_delega_en_el_nucleo(fuente_script), (
        "🚨 VIOLACIÓN: `main()` no delega en el núcleo; el wrapper debe invocar "
        "`coherence_auditor.main(argv)` y devolver su resultado."
    )


# ---------------------------------------------------------------------------
# 2. PARIDAD DE IMPORTACIÓN (el wrapper re-exporta OBJETOS, no copias)
# ---------------------------------------------------------------------------
def test_paridad_importacion_auditor():
    """El script importa el contrato del núcleo y sus símbolos son el MISMO objeto."""
    fuente = _fuente(RUTA_SCRIPT)
    simbolos = _simbolos_importados_del_nucleo(fuente)

    # -- Aserción 1: importación explícita del contrato público del núcleo --
    requeridos = {
        "auditar_coherencia_partido",
        "calcular_codigo_salida",
        "NivelSeveridad",
        "HallazgoSonda",
        "ReporteCoherenciaPartido",
    }
    faltantes = sorted(requeridos - simbolos)
    assert not faltantes, (
        f"🚨 VIOLACIÓN [ARCH-1.4.34]: el script no importa explícitamente {faltantes} desde "
        f"`{MODULO_NUCLEO}`; la duplicidad sigue vigente."
    )

    # -- Aserción 2: identidad de objeto (no basta con re-bautizar el mismo nombre) --
    from scripts.auditoria import auditar_coherencia_cartelera as capa_cli
    from src.core import coherence_auditor as nucleo

    assert capa_cli.auditar_coherencia_partido is nucleo.auditar_coherencia_partido, (
        "🚨 VIOLACIÓN: `auditar_coherencia_partido` del script NO es el objeto del núcleo."
    )
    assert capa_cli.calcular_codigo_salida is nucleo.calcular_codigo_salida, (
        "🚨 VIOLACIÓN: `calcular_codigo_salida` del script NO es el objeto del núcleo."
    )
    assert capa_cli.NivelSeveridad is nucleo.NivelSeveridad, (
        "🚨 VIOLACIÓN: `NivelSeveridad` del script NO es el enum del núcleo."
    )
    assert capa_cli.auditar_coherencia_partido.__module__ == MODULO_NUCLEO, (
        "🚨 VIOLACIÓN: la función re-exportada conserva un `__module__` ajeno al núcleo: "
        f"{capa_cli.auditar_coherencia_partido.__module__!r}."
    )

    # -- Aserción 3 (Sad Path): un wrapper que importe una COPIA local no certifica --
    impostor = (
        "from scripts.auditoria.copia_del_auditor import auditar_coherencia_partido\n"
        "def main(argv=None):\n"
        "    return auditar_coherencia_partido(argv)\n"
    )
    assert _simbolos_importados_del_nucleo(impostor) == set(), (
        "El juez aceptaría un wrapper que importa una copia local en lugar del núcleo canónico."
    )


# ---------------------------------------------------------------------------
# 3. PARIDAD FUNCIONAL (núcleo vs. wrapper: JSON, contrato de salida y CLI idénticos)
# ---------------------------------------------------------------------------
def _bateria_expedientes():
    """Batería declarativa: camino feliz + los Sad Paths del contrato `[ARCH-1.4.34]`."""
    return [
        # Camino feliz certificado: seis sondas conformes.
        {
            "id_partido": "PARIDAD-OK",
            "etiqueta": "Local vs Visita",
            "p_local": 0.45,
            "p_empate": 0.30,
            "p_visitante": 0.25,
            "momios": {"L": 2.50, "E": 3.90, "V": 2.60},
            "estrategia_codigo": "QBE-H1",
            "boletos": [2.50, 3.00],
            "lambda_home": 1.60,
            "lambda_away": 1.20,
        },
        # Sad Path 0: expediente vacío ⇒ degradación honesta ⚪ (jamás 🔴).
        {},
        # Sad Path 1: P' fuera de Δ² (Σ = 1.16) ⇒ ruptura axiomática 🔴.
        {
            "id_partido": "PARIDAD-SIMPLEX",
            "momios": {"L": 1.30, "E": 5.00, "V": 9.00},
            "p_local": 0.90,
            "p_empate": 0.06,
            "p_visitante": 0.20,
            "suficiencia_S_I": 1,
        },
        # Sad Path 2: overround S = 1.3704 fuera de la aduana [0.85, 1.30] ⇒ 🔴.
        {
            "id_partido": "PARIDAD-ADUANA",
            "momios": {"L": 1.50, "E": 3.00, "V": 2.70},
            "p_local": 0.45,
            "p_empate": 0.30,
            "p_visitante": 0.25,
        },
        # Sad Path 3: λ ≤ 0 xG ⇒ 🔴 (captura corrupta o dirección invertida).
        {"id_partido": "PARIDAD-LAMBDA", "lambda_home": 0.0, "lambda_away": 1.30},
        # Sad Path 4: boleto bajo el piso legal de $2.00 MXN ⇒ 🔴.
        {"id_partido": "PARIDAD-PISO", "estrategia_codigo": "QBE-R1", "boletos": [1.50, 2.50]},
        # Sad Path 5: S(I) = 0 declarado ⇒ ⚪ con métrica publicada (no bloquea).
        {
            "id_partido": "PARIDAD-SI0",
            "momios": {"L": 1.30, "E": 5.00, "V": 9.00},
            "p_local": 0.3333,
            "p_empate": 0.3333,
            "p_visitante": 0.3334,
            "suficiencia_S_I": 0,
        },
        # Sad Path 6: drift de Capa 0 (declara QBE-D1, morfología ASIMETRIA_LOCAL) ⇒ 🔴.
        {
            "id_partido": "PARIDAD-CAPA0",
            "p_local": 0.45,
            "p_empate": 0.30,
            "p_visitante": 0.25,
            "momios": {"L": 2.50, "E": 3.90, "V": 2.60},
            "estrategia_codigo": "QBE-D1",
            "boletos": [2.50, 3.00],
            "lambda_home": 1.60,
            "lambda_away": 1.20,
        },
        # Sad Path 7: evidencia parcial (sin cuotas ni boletos) ⇒ 🟡 de cobertura, sin veto.
        {"id_partido": "PARIDAD-PARCIAL", "p_local": 0.45, "p_empate": 0.30, "p_visitante": 0.25},
    ]


def _salida_json(reportes) -> str:
    return json.dumps(
        [reporte.model_dump(mode="json") for reporte in reportes],
        ensure_ascii=False,
        sort_keys=True,
    )


def test_paridad_funcional_auditor():
    """La lógica del núcleo y la del wrapper emiten EXACTAMENTE la misma salida."""
    from scripts.auditoria import auditar_coherencia_cartelera as capa_cli
    from src.core import coherence_auditor as nucleo

    bateria = _bateria_expedientes()

    # -- Aserción 1: mismo JSON por el núcleo directo y por el wrapper --
    por_nucleo = [nucleo.auditar_coherencia_partido(expediente) for expediente in bateria]
    por_wrapper = [capa_cli.auditar_coherencia_partido(expediente) for expediente in bateria]
    salida_nucleo = _salida_json(por_nucleo)
    salida_wrapper = _salida_json(por_wrapper)
    assert salida_nucleo == salida_wrapper, (
        "🚨 VIOLACIÓN [ARCH-1.4.34]: la capa de scripts divergió del núcleo (paridad rota)."
    )

    # Contrato de salida del CLI (EXIT 1 exclusivamente ante 🔴) idéntico en ambos frentes.
    for corte in range(len(bateria) + 1):
        assert nucleo.calcular_codigo_salida(por_nucleo[:corte]) == capa_cli.calcular_codigo_salida(
            por_wrapper[:corte]
        ), f"Divergencia en el contrato de salida del CLI para el corte {corte}."

    # Los Sad Paths se ejercitaron de verdad: los cuatro niveles semafóricos aparecen.
    niveles = {hallazgo.nivel.value for reporte in por_nucleo for hallazgo in reporte.hallazgos}
    niveles |= {reporte.nivel_global.value for reporte in por_nucleo}
    assert {"CONFORME", "ADVERTENCIA", "DISCREPANCIA", "SIN_VEREDICTO"} <= niveles, (
        f"La batería no ejercitó todos los veredictos: {sorted(niveles)}."
    )

    # -- Aserción 2: mismo contrato de consola/JSON en el CLI real (misma jornada, mismo dictamen) --
    salidas = []
    for modulo in (nucleo, capa_cli):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            codigo = modulo.main(["--json", "--jornada", "0"])
        salidas.append((codigo, buffer.getvalue()))
    assert salidas[0] == salidas[1], (
        "🚨 VIOLACIÓN: el contrato de salida del CLI difiere entre el núcleo y el wrapper."
    )
    assert json.loads(salidas[0][1])["sonda"] == "ARCH-1.4.34", (
        "El CLI no publica el contrato JSON sellado de la sonda [ARCH-1.4.34]."
    )

    # -- Aserción 3 (Sad Path / control negativo): el comparador SÍ distingue una divergencia --
    manipulado = [reporte.model_dump(mode="json") for reporte in por_wrapper]
    manipulado[0]["nivel_global"] = "DISCREPANCIA"
    assert json.dumps(manipulado, ensure_ascii=False, sort_keys=True) != salida_nucleo, (
        "El comparador de paridad es vacuos: no detecta una divergencia de veredicto."
    )
