# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DE LA ESCALA xG Y DE LA INGESTA UNIFICADA
Gobierno: `docs/ARCH.md` [ARCH-1.4.41] / `docs/GOVERNANCE.md` §4.2-A / [GOV-TEST-01 a 07]

Régimen declarado (Dual-Track honesto):
  * Invarianza 1 — Escala xG del motor soberano: la tasa canónica es `xg_total / PJ` … [DIRGEN-STRICT]
  * Invarianza 2 — Ingesta unificada: el daemon JAMÁS pisa el contrato sellado P′    … [DBBD-FUNGIBLE]
  * Invarianza 3 — Custodia de la plantilla madre de varianza                        … [GOVERNANCE]

Aislamiento: [GOV-TEST-01] sobre `tests/shield/conftest.py::boveda_gateway_aislada`
(clon efímero de la bóveda; cero red, cero navegador, cero tokens, cero mocks en producción).
"""

import math
from pathlib import Path

import pytest

MU_LIGA_JUEZ = 2.65
JORNADA_SINTETICA = 10
FOTMOB_ID_SINTETICO = 99991

# Contrato soberano de captura P′ (7 claves) — verdad ABSURDA por diseño: si el motor la pisa,
# el contrato sellado quedó corrompido y el juez debe verlo sin ambigüedad numérica.
SELLADO_SINTETICO = {
    "p_local": 0.1111,
    "p_empate": 0.2222,
    "p_visitante": 0.6667,
    "lambda_home": 9.99,
    "lambda_away": 8.88,
    "phi_lead2_home": 0.7777,
    "suficiencia_S_I": 0,
}


def _registro_simetrico(pj: int, gf: int, gc: int, xg: float, xga: float) -> dict:
    """Registro fáctico mínimo del contrato de ingesta (ambos clubes idénticos por simetría)."""
    bloque = {"pj": pj, "gf": gf, "gc": gc, "xg": xg, "xga": xga}
    return {
        "home_team_stats": dict(bloque),
        "away_team_stats": dict(bloque),
        "home_split_stats": {},
        "away_split_stats": {},
    }


def test_invarianza_1_escala_xg_siempre_dividida_por_pj():
    """[ARCH-1.4.41] La tasa canónica es `xg_total / PJ`: escala única, cero heurística de magnitud."""
    import inspect

    from src.core.sovereign_pipeline import derivar_factores_estructurales

    # (a) Invarianza de escala: mismo ritmo por partido con totales distintos ⇒ factores IDÉNTICOS.
    #     (pj=3, xG=3.60) y (pj=9, xG=10.80) son el MISMO equipo a 1.20 xG/partido y 1.00 GF/partido.
    temprano = derivar_factores_estructurales(_registro_simetrico(3, 3, 3, 3.60, 3.00), MU_LIGA_JUEZ)
    maduro = derivar_factores_estructurales(_registro_simetrico(9, 9, 9, 10.80, 9.00), MU_LIGA_JUEZ)
    assert temprano == maduro, (
        "🚨 [ARCH-1.4.41] Los factores dependen del TOTAL acumulado, no de la TASA por partido: "
        f"temporada temprana={temprano} vs. temporada madura={maduro}"
    )

    # (b) Anclaje numérico (Tratado Vol. I, §4.5/4.6): ataque = 0.65·(xG/PJ) + 0.35·(GF/PJ).
    mu_base = max(0.5, MU_LIGA_JUEZ / 2.0)
    ataque = (0.65 * (3.60 / 3)) + (0.35 * (3 / 3))       # 1.13 goles equivalentes por partido
    defensa = (0.65 * (3.00 / 3)) + (0.35 * (3 / 3))      # 1.00
    esperado = (
        round(math.log(max(0.2, ataque) / mu_base), 4),
        round(-math.log(max(0.2, defensa) / mu_base), 4),
        round(math.log(max(0.2, ataque) / mu_base), 4),
        round(-math.log(max(0.2, defensa) / mu_base), 4),
    )
    assert temprano == esperado, f"🚨 Factores fuera de la Sección 4.5/4.6: {temprano} ≠ {esperado}"

    # (c) Sad path anti-inflación: un ataque de 1.20 xG/partido NO es élite frente a μ_base = 1.325.
    assert temprano[0] < 0.0, (
        f"🚨 [ARCH-1.4.41] Ataque sobre-amplificado en temporada temprana: A_home={temprano[0]} ≥ 0"
    )

    # (d) Guardián sintáctico: la escala artificial `5.0` no existe en el derivador.
    fuente = inspect.getsource(derivar_factores_estructurales)
    assert "> 5.0" not in fuente and ">5.0" not in fuente, (
        "🚨 [ARCH-1.4.41] El derivador conserva el conmutador de escala artificial `> 5.0`: la "
        "magnitud del acumulado decide la unidad de medida y las primeras jornadas se sobre-amplifican."
    )


def _fila_standings(equipo: str, abreviatura: str, fotmob_team_id: int, pos: int) -> dict:
    """Fila de `standings_viva` conforme al contrato de ingesta del daemon (sync 3NF incluida)."""
    return {
        "equipo": equipo,
        "short_name": abreviatura,
        "escudo_url": "https://x.invalid/escudo.png",
        "fotmob_team_id": fotmob_team_id,
        "pos": pos,
        "puntos": 10,
        "pj": 8,
        "pg": 3,
        "pe": 1,
        "pp": 4,
        "gf": 10,
        "gc": 10,
        "dif": 0,
        "xg": 11.7,
        "xga": 11.7,
        "forma": ["G", "E"],
    }


def test_invarianza_2_ingesta_unificada_no_pisa_el_contrato_sellado(boveda_gateway_aislada):
    """[ARCH-1.4.41] Un solo camino de ingesta: el daemon rellena lo ausente y JAMÁS pisa el contrato P′.

    Verdad sellada ABSURDA por diseño (λ ≈ 9.9, p_local = 0.1111): si la captura releída desde la
    bóveda deja de publicarla verbatim, el motor sobreescribió en vuelo un corte ya homologado.
    """
    from scripts.daemons.centinela_deportivo import persistir_en_sqlite
    from src.storage.models import Competition, FixtureSnapshot, League

    gateway = boveda_gateway_aislada
    pareja = ("Club Puebla", "Atlante")

    # ── 1. Sembrado declarativo del clon efímero (liga sintética: cero colisión con la cartelera) ──
    with gateway.write_transaction() as tx:
        liga = League(
            name="Liga Sintética Shield [ARCH-1.4.41]",
            country="MX",
            flag="MX",
            fotmob_id=FOTMOB_ID_SINTETICO,
        )
        tx.add(liga)
        if tx.query(Competition).filter(Competition.id == "MEX_LIGAMX").first() is None:
            tx.add(Competition(id="MEX_LIGAMX", name="Liga MX (Shield)", country="MX"))
        tx.flush()
        liga_id = int(liga.id)

        tx.add(FixtureSnapshot(
            league_id=liga_id,
            matchday=JORNADA_SINTETICA,
            matches_json=[{
                "id_partido": "SHIELD-J10-SELLADO",
                "local": pareja[0],
                "visitante": pareja[1],
                "estado": "PROGRAMADO",
                "fecha_dt": "2026-10-16T19:00:00",
                **SELLADO_SINTETICO,
            }],
        ))

    # ── 2. Fotografía fresca del sensor: el sello NO viaja en la captura nueva (llega vacía) ──
    captura_sellada = {
        "id_partido": "SHIELD-J10-SELLADO",
        "local": pareja[0], "visitante": pareja[1],
        "estado": "PROGRAMADO", "fecha_dt": "2026-10-16T19:00:00",
        "marcador_actual": "", "momios": {"local": 2.5, "empate": 3.1, "visita": 2.9},
    }
    captura_virgen = {
        "id_partido": "SHIELD-J10-VIRGEN",
        "local": pareja[1], "visitante": pareja[0],
        "estado": "PROGRAMADO", "fecha_dt": "2026-10-16T21:00:00",
        "marcador_actual": "", "momios": {},
    }
    datos = {
        "standings_viva": [
            _fila_standings(pareja[0], "PUE", 9911, 1),
            _fila_standings(pareja[1], "ATL", 9912, 2),
        ],
        "tablas_historicas": {},
        "fixtures_por_jornada": {JORNADA_SINTETICA: [captura_sellada, captura_virgen]},
        "reprogramados": [],
    }

    # ── 3. Ingesta real por el punto de sellado del daemon ──
    persistir_en_sqlite(datos, FOTMOB_ID_SINTETICO, MU_LIGA_JUEZ)

    with gateway.read_session() as sesion:
        snap = (
            sesion.query(FixtureSnapshot)
            .filter(FixtureSnapshot.league_id == liga_id,
                    FixtureSnapshot.matchday == JORNADA_SINTETICA)
            .order_by(FixtureSnapshot.id.desc())
            .first()
        )
        assert snap is not None, "🚨 [ARCH-1.4.41] El daemon no persistió el corte de la jornada."
        capturas = {c.get("id_partido"): c for c in (snap.matches_json or [])}

    # ── 4. Ley de no-sobreescritura: el corte homologado sobrevive intacto ──
    sellado = capturas.get("SHIELD-J10-SELLADO")
    assert sellado is not None, (
        f"🚨 El corte sellado desapareció del payload persistido: {sorted(capturas)}"
    )
    for clave, valor in SELLADO_SINTETICO.items():
        assert sellado.get(clave) == valor, (
            f"🚨 [ARCH-1.4.41] El daemon pisó el sello homologado `{clave}`: "
            f"{sellado.get(clave)!r} ≠ {valor!r} — el motor no puede sobreescribir en vuelo un corte sellado."
        )

    # ── 5. Sad path anti-hueco: un corte inaugural SÍ nace sellado por el motor (cero regresión) ──
    virgen = capturas.get("SHIELD-J10-VIRGEN")
    assert virgen is not None, (
        f"🚨 El corte inaugural desapareció del payload persistido: {sorted(capturas)}"
    )
    huecos = [clave for clave in SELLADO_SINTETICO if virgen.get(clave) is None]
    assert not huecos, f"🚨 [ARCH-1.4.41] Corte inaugural sin sellar (huecos en P′): {huecos}"
    suma = sum(float(virgen[clave]) for clave in ("p_local", "p_empate", "p_visitante"))
    assert abs(suma - 1.0) < 1e-4, f"🚨 Distribución no normalizada en corte inaugural: ΣP = {suma}"


def test_invarianza_3_custodia_de_la_plantilla_madre_de_varianza():
    """[GOVERNANCE §4.2-A] La plantilla madre es INMUTABLE y toda varianza nueva acuña archivo propio."""
    raiz = Path(__file__).resolve().parents[2]
    plantilla = raiz / "docs" / "DIRGEN_VARIANCE_REQUEST_TEMPLATE.md"
    assert plantilla.is_file(), (
        "🚨 [GOVERNANCE §4.2-A] Desapareció la plantilla madre `docs/DIRGEN_VARIANCE_REQUEST_TEMPLATE.md`."
    )
    assert not (raiz / "docs" / "DIRGEN_VARIANCE_REQUEST.md").exists(), (
        "🚨 [GOVERNANCE §4.2-A] Un artefacto de varianza volvió a ocupar la raíz de `docs/`: "
        "los dossiers viven en `docs/variances/VAR_{ID}.md`."
    )
    assert (raiz / "docs" / "variances").is_dir(), (
        "🚨 [GOVERNANCE §4.2-A] No existe el repositorio de dossiers `docs/variances/`."
    )
    texto = plantilla.read_text(encoding="utf-8")
    for seccion in (
        "## 1. COORDENADAS EXACTAS",
        "## 2. EVIDENCIA FÁCTICA REAL",
        "## 3. DIAGNÓSTICO CAUSAL",
        "## 4. ABANICO DE ALTERNATIVAS EVALUADAS",
        "## 5. SOLUCIÓN RECOMENDADA",
        "## 6. DIFF PROPUESTO",
    ):
        assert seccion in texto, (
            f"🚨 [GOVERNANCE §4.2-A] La plantilla madre perdió la sección obligatoria `{seccion}` "
            "(protocolo anti-bandazos de AGENTS.md)."
        )
    gobierno = (raiz / "docs" / "GOVERNANCE.md").read_text(encoding="utf-8")
    assert "docs/DIRGEN_VARIANCE_REQUEST_TEMPLATE.md" in gobierno, (
        "🚨 [GOVERNANCE §4.2-A] La ley de custodia no está legislada en `docs/GOVERNANCE.md`."
    )
    assert "docs/variances/VAR_{ID}.md" in gobierno, (
        "🚨 [GOVERNANCE §4.2-A] La ruta soberana de dossiers no está legislada en `docs/GOVERNANCE.md`."
    )
