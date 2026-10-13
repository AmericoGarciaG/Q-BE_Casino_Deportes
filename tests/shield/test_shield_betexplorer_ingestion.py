# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — [ARCH-1.4.36] SENSOR DE INGESTA HISTÓRICA BETEXPLORER
Régimen: [HÍBRIDO DUAL-TRACK] — parser/transporte `[DBBD-FUNGIBLE]`, corte acumulado
`[DIRGEN-STRICT]` por REUTILIZACIÓN del plano canónico (`reconstruir_tabla_acumulada`).

Tres jueces:
  1. Parser dual-DOM + oráculo de ganador (clase `colored`) + deduplicación de encabezado.
  2. Anti-leakage (future-blindness) + identidad canónica del algoritmo de corte.
  3. Persistencia 3NF no destructiva e idempotente sobre el clon efímero del conftest.

Evidencia: fragmentos DOM **reales y verbatim** de la captura del Paso 0
(`scratch/betexplorer_results_raw.html`). Cero DOM sintético, cero fixture de partido inventado.
"""
from __future__ import annotations

import json
from typing import Dict, List

from scripts.ingesta.ingestar_historico_betexplorer import (
    ALGORITMO_CORTE,
    canonizar_partidos,
    construir_corte,
    parsear_resultados_betexplorer,
    persistir_corte_si_ausente,
    rellenar_marcadores_3nf,
    resolver_identidad_en_catalogo,
)

# ── EVIDENCIA VERBATIM: encabezado + 5 filas reales del bloque `11. Round` de la captura ────────
_ENCABEZADO_J11 = (
    '<tr><th class="h-text-left" colspan="2">11. Round</th>'
    '<th class="h-text-center">1</th><th class="h-text-center">X</th>'
    '<th class="h-text-center">2</th><th>\u00a0</th></tr>'
)
_FILA_SAN_LUIS_SANTOS = (
    '<tr><td class="h-text-left"><a class="in-match" data-test="10708679" '
    'href="/football/mexico/liga-mx/atletico-san-luis-santos-laguna/U1bZkiAd/">'
    '<span>Atl. San Luis</span> - <span><strong>Santos Laguna</strong></span></a></td>'
    '<td class="h-text-center"><a '
    'href="/football/mexico/liga-mx/atletico-san-luis-santos-laguna/U1bZkiAd/">1:2</a></td>'
    '<td class="table-main__odds" data-odd="2.12" data-oid="a6pm7xv464x0xrvmvb"></td>'
    '<td class="table-main__odds" data-odd="3.51" data-oid="a6pm7xv498x0x0"></td>'
    '<td class="table-main__odds colored" data-oid="a6pm7xv464x0xrvmvd">'
    '<span><span><span data-odd="3.09"></span></span></span></td>'
    '<td class="h-text-right h-text-no-wrap">Today</td></tr>'
)
_FILA_PACHUCA_NECAXA = (
    '<tr><td class="h-text-left"><a class="in-match" data-test="10708677" '
    'href="/football/mexico/liga-mx/pachuca-necaxa/dl0RiDup/">'
    '<span>Pachuca</span> - <span>Necaxa</span></a></td>'
    '<td class="h-text-center"><a '
    'href="/football/mexico/liga-mx/pachuca-necaxa/dl0RiDup/">3:3</a></td>'
    '<td class="table-main__odds" data-odd="1.66" data-oid="a6pm5xv464x0xrvmv7"></td>'
    '<td class="table-main__odds colored" data-oid="a6pm5xv498x0x0">'
    '<span><span><span data-odd="3.82"></span></span></span></td>'
    '<td class="table-main__odds" data-odd="4.59" data-oid="a6pm5xv464x0xrvmv9"></td>'
    '<td class="h-text-right h-text-no-wrap">Today</td></tr>'
)
_FILA_ATLAS_CHIVAS = (
    '<tr><td class="h-text-left"><a class="in-match" data-test="10708673" '
    'href="/football/mexico/liga-mx/atlas-guadalajara-chivas/phVoCsRb/">'
    '<span>Atlas</span> - <span>Guadalajara Chivas</span></a></td>'
    '<td class="h-text-center"><a '
    'href="/football/mexico/liga-mx/atlas-guadalajara-chivas/phVoCsRb/">1:1</a></td>'
    '<td class="table-main__odds" data-odd="3.25" data-oid="a6pm1xv464x0xrvmuv"></td>'
    '<td class="table-main__odds colored" data-oid="a6pm1xv498x0x0">'
    '<span><span><span data-odd="3.43"></span></span></span></td>'
    '<td class="table-main__odds" data-odd="2.08" data-oid="a6pm1xv464x0xrvmv1"></td>'
    '<td class="h-text-right h-text-no-wrap">Yesterday</td></tr>'
)
_FILA_AMERICA_RAYADOS = (
    '<tr><td class="h-text-left"><a class="in-match" data-test="10708675" '
    'href="/football/mexico/liga-mx/club-america-monterrey/hIYgALeB/">'
    '<span>Club America</span> - <span>Monterrey</span></a></td>'
    '<td class="h-text-center"><a '
    'href="/football/mexico/liga-mx/club-america-monterrey/hIYgALeB/">1:1</a></td>'
    '<td class="table-main__odds" data-odd="1.82" data-oid="a6pm3xv464x0xrvmv3"></td>'
    '<td class="table-main__odds colored" data-oid="a6pm3xv498x0x0">'
    '<span><span><span data-odd="3.73"></span></span></span></td>'
    '<td class="table-main__odds" data-odd="3.84" data-oid="a6pm3xv464x0xrvmv5"></td>'
    '<td class="h-text-right h-text-no-wrap">Yesterday</td></tr>'
)
_FILA_QUERETARO_ATLANTE = (
    '<tr><td class="h-text-left"><a class="in-match" data-test="10708665" '
    'href="/football/mexico/liga-mx/queretaro-atlante/2oeEcrC5/">'
    '<span><strong>Queretaro</strong></span> - <span>Atlante</span></a></td>'
    '<td class="h-text-center"><a '
    'href="/football/mexico/liga-mx/queretaro-atlante/2oeEcrC5/">2:0</a></td>'
    '<td class="table-main__odds colored" data-oid="a6plpxv464x0xrvmuf">'
    '<span><span><span data-odd="2.08"></span></span></span></td>'
    '<td class="table-main__odds" data-odd="3.40" data-oid="a6plpxv498x0x0"></td>'
    '<td class="table-main__odds" data-odd="3.27" data-oid="a6plpxv464x0xrvmuh"></td>'
    '<td class="h-text-right h-text-no-wrap">Yesterday</td></tr>'
)

_FILAS_REALES = (
    _FILA_SAN_LUIS_SANTOS, _FILA_PACHUCA_NECAXA, _FILA_ATLAS_CHIVAS,
    _FILA_AMERICA_RAYADOS, _FILA_QUERETARO_ATLANTE,
)
_FRAGMENTO_J11 = _ENCABEZADO_J11 + "".join(_FILAS_REALES)
_FRAGMENTO_ENCABEZADO_DUPLICADO = _ENCABEZADO_J11 + _FILA_SAN_LUIS_SANTOS * 2

# Catalogo 3NF REAL (`teams.canonical_slug` -> `teams.name`), transcrito del bus SQLite.
CATALOGO_3NF_REAL: Dict[str, str] = {
    "club-tijuana": "Club Tijuana",
    "cruz-azul": "Cruz Azul",
    "pumas-unam": "Pumas UNAM",
    "necaxa": "Necaxa",
    "atletico-san-luis": "Atlético San Luis",
    "atlante": "Atlante",
    "tigres-uanl": "Tigres UANL",
    "santos-laguna": "Santos Laguna",
    "fc-juarez": "FC Juárez",
    "deportivo-toluca": "Deportivo Toluca",
    "club-america": "Club América",
    "chivas-guadalajara": "Chivas Guadalajara",
    "queretaro-fc": "Querétaro FC",
    "club-leon": "Club León",
    "atlas-fc": "Atlas FC",
    "club-puebla": "Club Puebla",
    "rayados-de-monterrey": "Rayados de Monterrey",
    "club-pachuca": "Club Pachuca",
}
_POR_NOMBRE = {nombre: slug for slug, nombre in CATALOGO_3NF_REAL.items()}
_CLUBES = sorted(CATALOGO_3NF_REAL.values())

# ── JUEZ 1: PARSER DUAL-DOM, ORÁCULO DE GANADOR Y DEDUPLICACIÓN ─────────────────────────────────
_VOCABULARIO_REAL = (
    "Atl. San Luis", "Atlante", "Atlas", "Club America", "Club Leon", "Club Tijuana",
    "Cruz Azul", "Guadalajara Chivas", "Juarez", "Monterrey", "Necaxa", "Pachuca",
    "Puebla", "Queretaro", "Santos Laguna", "Tigres UANL", "Toluca", "UNAM Pumas",
)
# (etiqueta local, etiqueta visita, gf, gc, oráculo, nombre canónico local, nombre canónico visita)
_FILAS_ESPERADAS = (
    ("Atl. San Luis", "Santos Laguna", 1, 2, 2, "Atlético San Luis", "Santos Laguna"),
    ("Pachuca", "Necaxa", 3, 3, 1, "Club Pachuca", "Necaxa"),
    ("Atlas", "Guadalajara Chivas", 1, 1, 1, "Atlas FC", "Chivas Guadalajara"),
    ("Club America", "Monterrey", 1, 1, 1, "Club América", "Rayados de Monterrey"),
    ("Queretaro", "Atlante", 2, 0, 0, "Querétaro FC", "Atlante"),
)


def test_juez_1_parser_dual_dom_oraculo_y_deduplicacion():
    """[DBBD-FUNGIBLE] DOM real -> partidos canónicos con ganador certificado por la fuente."""
    bloques = parsear_resultados_betexplorer(_FRAGMENTO_J11)
    assert set(bloques) == {11}, "la captura contiene un único bloque `11. Round`"
    assert len(bloques[11]) == 5

    for partido, esperado in zip(bloques[11], _FILAS_ESPERADAS):
        raw_local, raw_visita, gf, gc, odd, _, _ = esperado
        assert partido["jornada"] == 11
        assert partido["local"] == raw_local and partido["visitante"] == raw_visita
        assert (partido["goles_local"], partido["goles_visitante"]) == (gf, gc)
        # Oráculo de la fuente: índice 0 = local, 1 = empate, 2 = visita (clase `colored`).
        assert partido["odd_ganadora"] == odd
        assert partido["odd_ganadora"] == (0 if gf > gc else (1 if gf == gc else 2))

    # Identidad canónica contra el catálogo 3NF real (18/18, sin huérfanos ni invenciones).
    canonico = canonizar_partidos(bloques, CATALOGO_3NF_REAL)
    assert set(canonico) == {11} and len(canonico[11]) == 5
    for partido, esperado in zip(canonico[11], _FILAS_ESPERADAS):
        _, _, gf, gc, _, n_local, n_visita = esperado
        assert partido["local"] == n_local and partido["visitante"] == n_visita
        assert partido["local_slug"] == _POR_NOMBRE[n_local]
        assert partido["visitante_slug"] == _POR_NOMBRE[n_visita]
        assert (partido["goles_local"], partido["goles_visitante"]) == (gf, gc)

    resueltos = {resolver_identidad_en_catalogo(n, CATALOGO_3NF_REAL) for n in _VOCABULARIO_REAL}
    assert resueltos == set(CATALOGO_3NF_REAL.values()), "el vocabulario real debe resolver 18/18"
    assert resolver_identidad_en_catalogo("Equipo Fantasma FC", CATALOGO_3NF_REAL) is None

    # Deduplicación: `11. Round` repetido y fila repetida -> un único registro, cero inflado.
    assert len(parsear_resultados_betexplorer(_FRAGMENTO_ENCABEZADO_DUPLICADO)[11]) == 1
    # Fila sin bloque de jornada: se descarta (jamás se inventa una jornada).
    assert parsear_resultados_betexplorer(_FILA_SAN_LUIS_SANTOS) == {}


# ── JUEZ 2: ANTI-LEAKAGE Y IDENTIDAD CANÓNICA DEL ALGORITMO DE CORTE ────────────────────────────
def test_juez_2_anti_leakage_y_identidad_canonica_del_algoritmo():
    """[DIRGEN-STRICT] El corte se REUTILIZA del plano y la jornada N jamás ve el futuro."""
    from scripts.daemons.centinela_deportivo import reconstruir_tabla_acumulada

    # Identidad, no reimplementación: el sensor no duplica la matemática del plano canónico.
    assert ALGORITMO_CORTE is reconstruir_tabla_acumulada

    canonico = canonizar_partidos(parsear_resultados_betexplorer(_FRAGMENTO_J11), CATALOGO_3NF_REAL)
    tabla = construir_corte(canonico, 11, _CLUBES)
    por_equipo = {f["equipo"]: f for f in tabla}
    assert len(tabla) == 18 and set(por_equipo) == set(_CLUBES)
    assert [f["pos"] for f in tabla] == list(range(1, 19))

    for f in tabla:
        assert f["pj"] <= 11, "anti-leakage: pj nunca puede exceder la jornada del corte"
        assert f["pj"] == f["pg"] + f["pe"] + f["pp"]
        assert f["puntos"] == 3 * f["pg"] + f["pe"]
        assert f["dif"] == f["gf"] - f["gc"]
        assert f["xg"] == round(f["gf"] * 1.05 + 1.2, 1)
        assert f["xga"] == round(f["gc"] * 0.95 + 0.8, 1)
        assert f["xpts"] == round(f["pg"] * 2.8 + f["pe"] * 0.9, 1)
        assert f["pts_pj"] == (round(f["puntos"] / f["pj"], 2) if f["pj"] else 0.0)
        assert f["escudo_url"] == f"/static/img/crests/{_POR_NOMBRE[f['equipo']]}.png"
        assert len(f["forma"]) <= 5 and set(f["forma"]) <= {"G", "E", "P"}

    # Orden canónico del plano: puntos descendente, luego diferencia de goles y luego goles a favor.
    claves = [(f["puntos"], f["dif"], f["gf"]) for f in tabla]
    assert claves == sorted(claves, reverse=True)

    # Forma derivada exclusivamente de los 5 resultados reales publicados en J11.
    assert por_equipo["Santos Laguna"]["forma"] == ["G"]
    assert por_equipo["Querétaro FC"]["forma"] == ["G"]
    assert por_equipo["Atlético San Luis"]["forma"] == ["P"]
    assert por_equipo["Atlante"]["forma"] == ["P"]
    assert por_equipo["Atlas FC"]["forma"] == ["E"]
    assert por_equipo["Necaxa"]["forma"] == ["E"]
    assert por_equipo["Chivas Guadalajara"]["forma"] == ["E"]
    # Club sin partidos publicados: fallback canónico del plano, sin inventar resultados.
    assert por_equipo["Cruz Azul"]["pj"] == 0
    assert por_equipo["Cruz Azul"]["forma"] == ["G", "E", "P"]
    assert por_equipo["Cruz Azul"]["pts_pj"] == 0.0
    assert por_equipo["Cruz Azul"]["xg"] == 1.2

    # FUTURE-BLINDNESS: jornadas futuras (datos reales re-etiquetados) no contaminan el corte N.
    con_futuro = {j: [dict(p) for p in ps] for j, ps in canonico.items()}
    for futura in (12, 13, 20):
        con_futuro[futura] = [dict(p, jornada=futura) for p in canonico[11]]
    assert construir_corte(con_futuro, 11, _CLUBES) == tabla
    # Sonda sensible: el corte 12 sí refleja la jornada 12 (la inyección no es un no-op).
    tabla_12 = construir_corte(con_futuro, 12, _CLUBES)
    assert tabla_12 != tabla
    assert all(f["pj"] <= 2 for f in tabla_12)


# ── JUEZ 3: PERSISTENCIA 3NF NO DESTRUCTIVA E IDEMPOTENTE (CLON EFÍMERO DEL CONFTEST) ──────────
_MARCADORES_REALES = {
    ("atletico-san-luis", "santos-laguna"): (1, 2),
    ("club-pachuca", "necaxa"): (3, 3),
    ("atlas-fc", "chivas-guadalajara"): (1, 1),
    ("club-america", "rayados-de-monterrey"): (1, 1),
    ("queretaro-fc", "atlante"): (2, 0),
}
_PENDIENTE_J11 = "LIGAMX-J11-09"  # Pumas UNAM vs Cruz Azul: sin resultado publicado en la fuente.


def _estado_matches(sesion) -> Dict[str, tuple]:
    """Fotografía de `matches` (id -> jornada, slugs, estado, marcadores) en la sesión dada."""
    from src.storage.models import Match
    return {m.id: (m.matchday_num, m.home_team_slug, m.away_team_slug,
                   m.status, m.score_home, m.score_away)
            for m in sesion.query(Match).all()}


def _estado_cortes(sesion) -> Dict[int, tuple]:
    """Fotografía de `standings_snapshots` de la liga 1 (jornada -> captura + payload íntegro)."""
    from src.storage.models import StandingSnapshot
    return {r.matchday: (r.captured_at, json.dumps(r.positions_json, sort_keys=True))
            for r in sesion.query(StandingSnapshot).filter(StandingSnapshot.league_id == 1).all()}


def test_juez_3_persistencia_3nf_no_destructiva_e_idempotente(boveda_gateway_aislada):
    """[ARCH-1.4.36] Fill-if-null en marcadores e insert-if-absent en cortes; cero borrado."""
    gateway = boveda_gateway_aislada
    canonico = canonizar_partidos(parsear_resultados_betexplorer(_FRAGMENTO_J11), CATALOGO_3NF_REAL)
    sesion = gateway.SessionFactory()
    try:
        # [Dictamen V-2 · PREMISA HERMÉTICA DECLARADA] El relleno fill-if-null EXIGE huecos: la
        # bóveda viva ya trae los marcadores de J11 sellados por la ingesta real, de modo que el juez
        # abre los 5 huecos publicados DENTRO del clon efímero. Cero mutación de la bóveda viva: la
        # sesión se revierte en el `finally`. La premisa queda DECLARADA por el propio juez, jamás
        # heredada del estado temporal de la base (que es lo que lo hacía rojo en HEAD).
        estado_original = _estado_matches(sesion)
        from src.storage.models import Match
        huecos_abiertos = 0
        for fila in sesion.query(Match).filter(Match.matchday_num == 11).all():
            par = (fila.home_team_slug, fila.away_team_slug)
            if par in _MARCADORES_REALES or (par[1], par[0]) in _MARCADORES_REALES:
                fila.score_home = None
                fila.score_away = None
                fila.status = "PROGRAMADO"
                huecos_abiertos += 1
        sesion.flush()
        assert huecos_abiertos == len(_MARCADORES_REALES), (
            "el clon debe contener los 5 pares publicados de J11 para probar el fill-if-null"
        )

        partidos_previos = _estado_matches(sesion)
        cortes_previos = _estado_cortes(sesion)
        # [DICTAMEN DIRECTOR 2026-10-12 / RESOLUCIÓN V-1] La igualdad rígida colisionaba con la
        # bóveda VIVA, que ya declara el corte REAL J11 (`standings_snapshots` = J1..J11): el
        # juez exige los 10 cortes históricos como SUBCONJUNTO, admitiendo cortes adicionales
        # legítimos sin degradar la garantía (la ausencia de un corte sí falla).
        assert set(range(1, 11)).issubset(set(cortes_previos)), (
            f"Faltan jornadas históricas en standings_snapshots: {set(range(1, 11)) - set(cortes_previos)}"
        )
        assert len(partidos_previos) >= 9

        # 1. FILL-IF-NULL: sólo se rellenan marcadores ausentes de partidos publicados.
        reporte = rellenar_marcadores_3nf(sesion, league_id=1, partidos_por_jornada=canonico)
        assert reporte["actualizados"] == 5
        assert reporte["sin_fila_3nf"] == [], "los 5 pares reales existen en el calendario 3NF"
        tras_relleno = _estado_matches(sesion)
        for (local_slug, visita_slug), (gf, gc) in _MARCADORES_REALES.items():
            filas = [v for v in tras_relleno.values() if (v[1], v[2]) == (local_slug, visita_slug)]
            assert len(filas) == 1, f"par ({local_slug}, {visita_slug}) duplicado en el calendario"
            assert filas[0][3] == "FINALIZADO"
            assert (filas[0][4], filas[0][5]) == (gf, gc)
        # El partido sin resultado publicado permanece intacto: cero invención de marcadores.
        assert tras_relleno[_PENDIENTE_J11] == partidos_previos[_PENDIENTE_J11]
        # Ninguna otra jornada del calendario 3NF fue tocada.
        for identificador, estado in partidos_previos.items():
            if estado[0] != 11:
                assert tras_relleno[identificador] == estado

        # 2. IDEMPOTENCIA: la segunda pasada no muta absolutamente nada.
        segunda = rellenar_marcadores_3nf(sesion, league_id=1, partidos_por_jornada=canonico)
        assert segunda["actualizados"] == 0 and segunda["preservados"] == 5
        assert _estado_matches(sesion) == tras_relleno

        # 3. INSERT-IF-ABSENT: el corte J11 entra una vez; los 10 cortes previos quedan intactos.
        # [DICTAMEN DIRECTOR 2026-10-12 / RESOLUCIÓN V-1.b — PREMISA HERMÉTICA DECLARADA]
        # La bóveda VIVA ya declara el corte REAL J11 (misma causa raíz que V-1), de modo que el
        # juez ABRE el hueco DENTRO del clon efímero antes de exigir la inserción. Cero mutación de
        # la bóveda viva: la sesión se revierte en el `finally`. Con ello el juez conserva ÍNTEGRAS
        # ambas ramas del contrato: inserción real (True) e idempotencia (False), sin heredar la
        # premisa del estado temporal de la base.
        from src.storage.models import StandingSnapshot
        for _fila_j11_previa in sesion.query(StandingSnapshot).filter_by(league_id=1, matchday=11).all():
            sesion.delete(_fila_j11_previa)
        sesion.flush()
        assert 11 not in _estado_cortes(sesion), "la premisa exige el corte J11 AUSENTE en el clon"
        tabla = construir_corte(canonico, 11, _CLUBES)
        assert persistir_corte_si_ausente(sesion, league_id=1, jornada=11, tabla=tabla) is True
        cortes_con_j11 = _estado_cortes(sesion)
        assert set(range(1, 12)).issubset(set(cortes_con_j11)), (
            f"el corte J11 no quedó persistido en el clon: {sorted(cortes_con_j11)}"
        )
        for jornada, payload in cortes_previos.items():
            # El J11 es la premisa hermética re-insertada (se valida por identidad más abajo); los
            # 10 cortes históricos J1..J10 jamás pueden ser mutados por el sensor.
            if jornada == 11:
                continue
            assert cortes_con_j11[jornada] == payload, f"el corte J{jornada} fue mutado (prohibido)"
        guardado = sesion.query(StandingSnapshot).filter_by(league_id=1, matchday=11).one()
        assert guardado.season == "2026"
        assert guardado.positions_json == tabla
        assert [f["pos"] for f in guardado.positions_json] == list(range(1, 19))

        # 4. IDEMPOTENCIA DEL CORTE: la segunda llamada no inserta ni duplica.
        assert persistir_corte_si_ausente(sesion, league_id=1, jornada=11, tabla=tabla) is False
        assert _estado_cortes(sesion) == cortes_con_j11
        assert sesion.query(StandingSnapshot).filter_by(league_id=1, matchday=11).count() == 1
    finally:
        sesion.rollback()  # Axioma de inocuidad del arnés: el clon queda tal como estaba
        sesion.close()

    # 5. El sensor NO comitea por su cuenta: la Unit of Work pertenece al Gateway.
    with gateway.read_session() as verificacion:
        assert _estado_cortes(verificacion) == cortes_previos
        # [Dictamen V-2] La referencia es el estado ORIGINAL del clon (previo a abrir los huecos de
        # la premisa): si el sensor hubiera comiteado por su cuenta, los 5 marcadores abiertos
        # sobrevivirían aquí y el juez rugiría.
        assert _estado_matches(verificacion) == estado_original



