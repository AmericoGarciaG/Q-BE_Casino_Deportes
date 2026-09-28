# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [VARIANCE-03 extirpada / VARIANCE-05 ratificada] Tablero Progol Dinámico + Vínculo Elástico.
Doctrina: Kybern Framework v12.0 [GOV-TEST-01 a 07]
Régimen: [HÍBRIDO DUAL-TRACK] — [DIRGEN-STRICT] en el vínculo soberano / Prior Fiduciario;
[DBBD-FUNGIBLE] en la hidratación del tablero desde la bóveda 3NF.

Twin-Test: `AbstractTestProgolSlateDynamic` declara las 3 leyes; `TestProgolSlateDynamic` las materializa.

Ley 1 [VARIANCE-05] Barrido elástico: sin la capa de traducción de jerga comercial, la casilla
        Necaxa/AGUILAS NO se vincula (Prior Fiduciario); con la traducción SÍ se vincula — y la
        probabilidad sigue proviniendo EXCLUSIVAMENTE de `sovereign_distributions`.
Ley 2 [VARIANCE-03] Slate dinámico: bóveda sin concurso OPEN => None (cero casillas inventadas);
        bóveda con 21 casillas 3NF => tablero íntegro y venta pública declarada SÓLO si existe
        captura fáctica de momios de la jornada [GOVERNANCE-01].
Ley 3 [SHIELD-AST] Cero constantes de slate quemadas en `markets.py` y cero identidades sintéticas
        de concurso en el código de producción.

Hermeticidad: cero red, cero dependencia de la bóveda real (SQLite efímero en memoria).
"""

import ast
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.storage.database import Base
from src.storage.models import (
    Competition,
    FixtureSnapshot,
    League,
    Match,
    Slate,
    SlateItem,
    SovereignDistribution,
)
from src.ingestion.progol_scraper import PRIOR_IGNORANCIA_FIDUCIARIA
from src.web.routes.markets import _cargar_slate_progol
from scripts.daemons.centinela_progol import procesar_casilla_con_resiliencia

ROOT = Path(__file__).resolve().parent.parent.parent

# Casilla 19 del concurso fáctico 2352: Necaxa (local) vs AGUILAS (jerga comercial del sitio).
MATCH_NECAXA_AMERICA = "LIGAMX-J10-19"
ID_CONCURSO_FACTICO = "PROGOL-9999"
MOMIOS_CASINO_JORNADA = {"L": 2.50, "E": 3.20, "V": 3.60}


def _boveda_efimera():
    """Sesión SQLite efímera en memoria: cero red y cero contaminación de la bóveda real."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _sembrar_partido_necaxa_america(sesion, con_distribucion: bool):
    """Partido real en `matches` con o sin su distribución soberana en la 3NF."""
    sesion.add(Competition(id="MEX_LIGAMX", name="Liga MX", country="México"))
    sesion.add(Match(
        id=MATCH_NECAXA_AMERICA,
        competition_id="MEX_LIGAMX",
        matchday_num=10,
        home_team_slug="necaxa",
        away_team_slug="america",
    ))
    if con_distribucion:
        sesion.add(SovereignDistribution(
            match_id=MATCH_NECAXA_AMERICA,
            model_version="PIR-VARIANCE-05",
            p_local=0.51,
            p_empate=0.27,
            p_visitante=0.22,
            lambda_home=1.45,
            lambda_away=1.10,
        ))
    sesion.commit()
    return sesion


def _sembrar_concurso_3nf(sesion):
    """Concurso completo (14 REGULAR + 7 REVANCHA) con captura fáctica de momios de la jornada.

    Nota de ingeniería: `src/storage/gateway.py` registra un listener global `Engine → PRAGMA
    foreign_keys = ON`, de modo que el motor efímero aplica integridad referencial estricta.
    Se fuerza el orden padre→hijo con `flush()` explícito (padres, cabecera, casillas, snapshot).
    """
    sesion.add(Competition(id="MEX_LIGAMX", name="Liga MX", country="México"))
    sesion.add(League(id=262, name="Liga MX", country="México", flag="mx", fotmob_id=262))
    sesion.add(Match(
        id=MATCH_NECAXA_AMERICA,
        competition_id="MEX_LIGAMX",
        matchday_num=10,
        home_team_slug="necaxa",
        away_team_slug="america",
    ))
    sesion.flush()

    sesion.add(Slate(
        id=ID_CONCURSO_FACTICO,
        name="Progol Concurso 9999",
        competition_id="MEX_LIGAMX",
        matchday_num=10,
        bolsa_estimada=8800000.0,
        status="OPEN",
    ))
    sesion.flush()

    for i in range(1, 22):
        sesion.add(SlateItem(
            slate_id=ID_CONCURSO_FACTICO,
            tipo_concurso="REGULAR" if i <= 14 else "REVANCHA",
            position=i,
            local_raw="LOCAL %02d" % i,
            visitante_raw="VISITANTE %02d" % i,
            local_canonico=("Necaxa" if i == 19 else None),
            visitante_canonico=("Club América" if i == 19 else None),
            match_id=(MATCH_NECAXA_AMERICA if i == 19 else None),
            p_local=0.40,
            p_empate=0.30,
            p_visitante=0.30,
            es_prior_ignorancia=(i != 19),
        ))
    sesion.flush()

    sesion.add(FixtureSnapshot(
        league_id=262,
        matchday=10,
        matches_json=[
            {"id_partido": MATCH_NECAXA_AMERICA, "momios": dict(MOMIOS_CASINO_JORNADA)},
            {"id_partido": "LIGAMX-J10-20", "momios": {}},
        ],
    ))
    sesion.commit()
    return sesion


class AbstractTestProgolSlateDynamic:
    """Contrato abstracto e inmutable del tablero Progol dinámico y del vínculo elástico."""

    def test_ley_1_barrido_elastico_twin_test_no_fabrica_probabilidad(self):
        """
        [VARIANCE-05] Twin-Test del vínculo Caso A.
        Rama ROJA (sin traducción de jerga): 'AGUILAS' no resuelve identidad => Prior Fiduciario.
        Rama VERDE (con traducción): la casilla se vincula al partido real de `matches`.
        Contragolpe [GOVERNANCE-01]: el vínculo NO fabrica probabilidad — si falta la fila en
        `sovereign_distributions`, la casilla permanece en Prior aunque el partido exista.
        """
        sesion = _sembrar_partido_necaxa_america(_boveda_efimera(), con_distribucion=True)

        with patch("scripts.daemons.centinela_progol.PROGOL_JARGON_MAP", {}):
            rojo = procesar_casilla_con_resiliencia("NECAXA", "AGUILAS", db_session=sesion)
        verde = procesar_casilla_con_resiliencia("NECAXA", "AGUILAS", db_session=sesion)

        # ── Rama ROJA: la jerga cruda del sitio no se vincula (el barrido elástico no adivina identidades) ──
        assert rojo["visitante_raw"] == "AGUILAS"
        assert rojo["match_id"] is None
        assert rojo["es_prior_ignorancia"] is True
        assert rojo["p_local"] == pytest.approx(PRIOR_IGNORANCIA_FIDUCIARIA[0], abs=1e-6)
        assert rojo["p_empate"] == pytest.approx(PRIOR_IGNORANCIA_FIDUCIARIA[1], abs=1e-6)
        assert rojo["p_visitante"] == pytest.approx(PRIOR_IGNORANCIA_FIDUCIARIA[2], abs=1e-6)

        # ── Rama VERDE: SÓLO la capa de traducción materializa el vínculo elástico ──
        assert verde["visitante_canonico"] == "Club América"
        assert verde["visitante_canonico"] != rojo["visitante_canonico"]
        assert verde["match_id"] == MATCH_NECAXA_AMERICA
        assert verde["es_prior_ignorancia"] is False
        assert verde["p_local"] == pytest.approx(0.51, abs=1e-6)
        assert verde["p_empate"] == pytest.approx(0.27, abs=1e-6)
        assert verde["p_visitante"] == pytest.approx(0.22, abs=1e-6)
        assert verde["model_version"] == "PIR-VARIANCE-05"

        # ── Contragolpe: partido presente SIN distribución soberana => Prior (identidad ≠ probabilidad) ──
        huerfana = procesar_casilla_con_resiliencia(
            "NECAXA", "AGUILAS",
            db_session=_sembrar_partido_necaxa_america(_boveda_efimera(), con_distribucion=False),
        )
        assert huerfana["visitante_canonico"] == "Club América"
        assert huerfana["match_id"] is None
        assert huerfana["es_prior_ignorancia"] is True
        assert huerfana["p_local"] == pytest.approx(PRIOR_IGNORANCIA_FIDUCIARIA[0], abs=1e-6)
        assert huerfana["p_local"] + huerfana["p_empate"] + huerfana["p_visitante"] == pytest.approx(1.0, abs=1e-4)


    def test_ley_2_slate_dinamico_desde_la_boveda_3nf(self):
        """
        [VARIANCE-03 extirpada] Twin-Test de la hidratación dinámica del tablero Progol.
        RAMA ROJA: bóveda sin concurso OPEN => None (prohibido inventar casillas de respaldo).
        RAMA VERDE: concurso 3NF de 21 casillas => tablero íntegro; la venta pública sólo se puebla
        con captura fáctica de momios de esa jornada.
        """
        vacia = _boveda_efimera()
        assert _cargar_slate_progol(vacia) is None

        sesion = _sembrar_concurso_3nf(_boveda_efimera())
        tablero = _cargar_slate_progol(sesion)

        assert tablero is not None
        assert tablero["slate_id"] == ID_CONCURSO_FACTICO
        assert tablero["status"] == "OPEN"
        assert tablero["matchday_num"] == 10
        assert tablero["bolsa_estimada"] == pytest.approx(8800000.0)
        assert len(tablero["items"]) == 21
        assert [i["order"] for i in tablero["items"]] == list(range(1, 22))
        assert [i["order"] for i in tablero["items"] if i["tipo_concurso"] == "REGULAR"] == list(range(1, 15))
        assert tablero["sesgo_fuente"] == "MOMIOS_DE_CASINO"

        casilla19 = tablero["items"][18]
        assert casilla19["order"] == 19
        assert casilla19["tipo_concurso"] == "REVANCHA"
        assert casilla19["local"] == "Necaxa"
        assert casilla19["visitante"] == "Club América"
        assert casilla19["visitante_raw"] == "VISITANTE 19"
        assert casilla19["match_id"] == MATCH_NECAXA_AMERICA
        assert casilla19["estado_qbe"] == "SOBERANO-3NF"
        assert casilla19["es_prior_ignorancia"] is False
        assert casilla19["sesgo_disponible"] is True
        assert casilla19["sesgo_motivo"] == "MOMIOS_DE_CASINO_DE_LA_JORNADA"
        assert casilla19["v_pub"] == pytest.approx(
            {clave: 1.0 / valor for clave, valor in MOMIOS_CASINO_JORNADA.items()}, rel=1e-4
        )
        assert casilla19["analisis_sesgo"] is not None

        # Juez de coherencia aritmética: la venta pública implícita NO altera la probabilidad soberana.
        assert casilla19["p_qbe"] == {"L": 0.40, "E": 0.30, "V": 0.30}
        assert sum(casilla19["p_qbe"].values()) == pytest.approx(1.0, abs=1e-6)

        casilla01 = tablero["items"][0]
        assert casilla01["v_pub"] == {}
        assert casilla01["sesgo_disponible"] is False
        assert casilla01["sesgo_motivo"] == "VENTA_PUBLICA_NO_INGESTADA_PARA_ESTE_PARTIDO"
        assert casilla01["analisis_sesgo"] is None
        assert casilla01["estado_qbe"] == "PRIOR-FIDUCIARIO-1/3"
        assert casilla01["es_prior_ignorancia"] is True

        # `slate_id` explícito inexistente => degrada al concurso OPEN (jamás 404 ni tablero fabricado).
        assert _cargar_slate_progol(sesion, slate_id=ID_CONCURSO_FACTICO)["slate_id"] == ID_CONCURSO_FACTICO
        assert _cargar_slate_progol(sesion, slate_id="PROGOL-INEXISTENTE")["slate_id"] == ID_CONCURSO_FACTICO


    def test_ley_3_cero_constantes_de_slate_quemadas(self):
        """
        [SHIELD-AST / VARIANCE-03] Prohíbe re-introducir el tablero quemado en `markets.py` y prohíbe
        identidades sintéticas de concurso en el código de producción.
        """
        mercados = ROOT / "src" / "web" / "routes" / "markets.py"
        codigo = mercados.read_text(encoding="utf-8")
        arbol = ast.parse(codigo, filename=str(mercados))

        # (a) Ninguna constante de módulo puede contener un contenedor de casillas quemadas.
        prohibidos = []
        for nodo in arbol.body:
            if not isinstance(nodo, ast.Assign) or not isinstance(nodo.value, (ast.List, ast.Tuple, ast.Dict, ast.Set)):
                continue
            if not (getattr(nodo.value, "elts", None) or getattr(nodo.value, "keys", None)):
                continue  # contenedor vacío: inocuo
            for objetivo in nodo.targets:
                if isinstance(objetivo, ast.Name) and ("SLATE" in objetivo.id.upper() or "QUINIELA" in objetivo.id.upper()):
                    prohibidos.append("L%d: %s" % (nodo.lineno, objetivo.id))
        assert not prohibidos, "[VARIANCE-03] Constante de slate quemada en markets.py => " + ", ".join(prohibidos)

        # (a2) Ninguna REFERENCIA viva a la constante extirpada (la mención documental en el
        # comentario de extirpación es legítima y no constituye código ejecutable).
        asignados = [
            objetivo.id
            for nodo in arbol.body if isinstance(nodo, ast.Assign)
            for objetivo in nodo.targets if isinstance(objetivo, ast.Name)
        ]
        referencias = [n.id for n in ast.walk(arbol) if isinstance(n, ast.Name) and n.id == "SLATE_PROGOL_14_ITEMS"]
        referencias += [n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute) and n.attr == "SLATE_PROGOL_14_ITEMS"]
        assert "SLATE_PROGOL_14_ITEMS" not in asignados + referencias, (
            "[VARIANCE-03] Referencia viva a SLATE_PROGOL_14_ITEMS en markets.py"
        )

        # (b) Ambos endpoints Progol deben hidratarse de la bóveda 3NF, jamás de una constante local.
        for nombre_func in ("get_active_progol_slate", "optimize_progol_endpoint"):
            funcion = next(
                (n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name == nombre_func),
                None,
            )
            assert funcion is not None, "Endpoint Progol ausente: %s" % nombre_func
            assert "_cargar_slate_progol" in ast.dump(funcion), "%s no se hidrata de la bóveda 3NF" % nombre_func

        # (c) Identidades y ventas públicas sintéticas: prohibidas en TODO el código de producción.
        sinteticas = []
        for raiz in (ROOT / "src", ROOT / "scripts"):
            for archivo in raiz.rglob("*.py"):
                texto = archivo.read_text(encoding="utf-8", errors="ignore")
                if "PROGOL_2245" in texto or "Concurso Progol 2245" in texto:
                    sinteticas.append(str(archivo.relative_to(ROOT)))
        assert not sinteticas, "[GOVERNANCE-01] Concurso sintético detectado en producción => " + ", ".join(sinteticas)
        assert "25000000" not in codigo and "25_000_000" not in codigo


class TestProgolSlateDynamic(AbstractTestProgolSlateDynamic):
    """Materialización concreta del Juez Inmutable [VARIANCE-03 / VARIANCE-05]."""
    pass



