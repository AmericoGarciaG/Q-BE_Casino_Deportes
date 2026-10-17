# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ ABSTRACTO DE LA LEY DE SELLADO DEL CONTRATO DE CAPTURA P′
Orden Ejecutiva del Director: LLAVE MAESTRA DE SOBREESCRITURA (`--forzar`).
Gobierno: [GOV-TEST-01] aislamiento hermético sobre el clon efímero del arnés
(`tests/shield/conftest.py::boveda_gateway_aislada`), cero red / cero navegador / cero tokens.

Régimen: `[DBBD-FUNGIBLE]` — transporte e identidad de captura. El juez NO ejecuta el motor
matemático: los valores sembrados son CONSTANTES DECLARADAS de prueba (cero fórmulas, cero
parámetros de la bóveda) y el sellador sólo se ocupa de propagarlas al JSON de captura.

Invariantes vigiladas
---------------------
1. Ley por defecto `fill-if-absent` POR CAMPO ([VAR-2026-J7-HOMOLOGACION §6.5 · E5], Pilar 4):
   un contrato MUTILADO se COMPLETA en sus claves ausentes y lo YA sellado JAMÁS se sobreescribe.
2. `--forzar`: sobreescritura destructiva de las 7 claves del contrato contra la verdad fáctica
   nueva (el reporte lo declara con `ley = overwrite-forzado (--forzar)`).
3. Idempotencia del modo forzado: si el valor capturado YA coincide, la pasada siguiente escribe
   cero — la llave maestra no degrada la garantía de no-reescritura inútil.
"""

JORNADA_JUEZ = 990
ID_PARTIDO = "SHIELD-J990-01"

# Verdad fáctica declarada por el juez (constantes de prueba: cero matemática, cero fórmulas).
VERDAD_3NF = {
    "p_local": 0.3821,
    "p_empate": 0.3093,
    "p_visitante": 0.3086,
    "lambda_home": 1.4102,
    "lambda_away": 1.3988,
    "phi_lead2_home": -0.0412,
}
SUFICIENCIA_3NF = 1
# Captura preexistente MUTILADA: 1 clave numérica desactualizada + sello S(I) obsoleto.
CAPTURA_MUTILADA = {"id_partido": ID_PARTIDO, "p_local": 0.1111, "suficiencia_S_I": 0}


def _captura_publicada(gateway, liga_id: int, jornada: int = JORNADA_JUEZ) -> dict:
    """Relectura fáctica del fixture sembrado en el clon (evidencia, no relato)."""
    from src.storage.models import FixtureSnapshot

    with gateway.read_session() as sesion:
        snap = (
            sesion.query(FixtureSnapshot)
            .filter(FixtureSnapshot.league_id == liga_id, FixtureSnapshot.matchday == jornada)
            .one()
        )
    return dict((snap.matches_json or [{}])[0])


def test_invarianza_ley_de_sellado_fill_if_absent_vs_forzar(boveda_gateway_aislada):
    """[ORDEN EJECUTIVA · LLAVE MAESTRA] Las tres invariantes de la ley de sellado de P′."""
    from scripts.utilidades.poblar_temporada_completa_backtesting import (
        CLAVES_CAPTURA_P_PRIMA,
        CLAVE_SUFICIENCIA_SI,
        LEY_SELLADO_FILL_IF_ABSENT,
        LEY_SELLADO_FORZADO,
        _sellar_p_prima_en_capturas,
    )
    from src.storage.models import FixtureSnapshot, League

    gateway = boveda_gateway_aislada
    with gateway.read_session() as sesion:
        liga = sesion.query(League).first()
        assert liga is not None, "el clon de la bóveda debe portar el catálogo de ligas (FK estricta ON)"
        liga_id = int(liga.id)

    # Sembrado hermético: jornada sintética J990 (jamás colisiona con la cartelera viva).
    with gateway.write_transaction() as tx:
        tx.add(
            FixtureSnapshot(
                league_id=liga_id, matchday=JORNADA_JUEZ, matches_json=[dict(CAPTURA_MUTILADA)]
            )
        )
        tx.flush()

    # ── INVARIANTE 1 · LEY POR DEFECTO: `fill-if-absent` POR CAMPO ────────────────────────────────
    with gateway.write_transaction() as tx:
        reporte = _sellar_p_prima_en_capturas(
            tx, liga_id, [JORNADA_JUEZ], {ID_PARTIDO: dict(VERDAD_3NF)}, {ID_PARTIDO: SUFICIENCIA_3NF}
        )
    assert reporte["ley"] == LEY_SELLADO_FILL_IF_ABSENT and reporte["forzar"] is False
    assert reporte["selladas"] == 1, "el contrato mutilado debe COMPLETARSE (unidad = CAMPO)"
    assert reporte["preservadas"] == 0
    assert reporte["suficiencia_selladas"] == 0 and reporte["suficiencia_preservadas"] == 1, (
        "🚨 sin `--forzar` el sello S(I) preexistente (0) se PRESERVA, aunque la 3NF porte 1: "
        "esa es precisamente la ley que la llave maestra suspende"
    )

    captura = _captura_publicada(gateway, liga_id)
    assert captura["p_local"] == CAPTURA_MUTILADA["p_local"], (
        "🚨 VIOLACIÓN DE PILAR 4: sin `--forzar` la clave ya sellada JAMÁS se sobreescribe"
    )
    assert captura[CLAVE_SUFICIENCIA_SI] == CAPTURA_MUTILADA[CLAVE_SUFICIENCIA_SI], (
        "🚨 VIOLACIÓN DE PILAR 4: sin `--forzar` el sello S(I) preexistente se preserva"
    )
    # ── INVARIANTE 2 · LLAVE MAESTRA `--forzar`: SOBREESCRITURA DESTRUCTIVA DE LAS 7 CLAVES ───────
    with gateway.write_transaction() as tx:
        reporte = _sellar_p_prima_en_capturas(
            tx, liga_id, [JORNADA_JUEZ], {ID_PARTIDO: dict(VERDAD_3NF)},
            {ID_PARTIDO: SUFICIENCIA_3NF}, forzar=True,
        )
    assert reporte["ley"] == LEY_SELLADO_FORZADO and reporte["forzar"] is True
    assert reporte["selladas"] == 1, "la verdad nueva debe imponerse sobre la clave divergente"
    assert reporte["suficiencia_selladas"] == 1, "el séptimo campo se sobreescribe bajo `--forzar`"

    captura = _captura_publicada(gateway, liga_id)
    for clave in CLAVES_CAPTURA_P_PRIMA:
        assert captura[clave] == VERDAD_3NF[clave], (
            f"🚨 `--forzar` debe sincronizar la clave {clave} con la 3NF: "
            f"captura={captura[clave]} verdad={VERDAD_3NF[clave]}"
        )
    assert captura[CLAVE_SUFICIENCIA_SI] == SUFICIENCIA_3NF, "el séptimo campo también se sincroniza"

    # ── INVARIANTE 3 · IDEMPOTENCIA FORZADA: valor idéntico ⇒ CERO ESCRITURAS ─────────────────────
    with gateway.write_transaction() as tx:
        reporte = _sellar_p_prima_en_capturas(
            tx, liga_id, [JORNADA_JUEZ], {ID_PARTIDO: dict(VERDAD_3NF)},
            {ID_PARTIDO: SUFICIENCIA_3NF}, forzar=True,
        )
    assert reporte["selladas"] == 0 and reporte["suficiencia_selladas"] == 0, (
        "🚨 `--forzar` debe seguir siendo idempotente: una segunda pasada escribe cero"
    )
    assert reporte["preservadas"] == 1 and reporte["suficiencia_preservadas"] == 1
    assert reporte["por_jornada"][JORNADA_JUEZ] == {
        "selladas": 0, "fixtures": 1, "suficiencia_selladas": 0,
    }
    assert _captura_publicada(gateway, liga_id) == captura, "la captura no se degrada en la re-pasada"


def test_invarianza_forzar_cero_invencion_sin_valor_en_la_3nf(boveda_gateway_aislada):
    """[CERO INVENCIÓN] Sin valor en la 3NF no hay clave que escribir ni borrar, aun con `--forzar`."""
    from scripts.utilidades.poblar_temporada_completa_backtesting import _sellar_p_prima_en_capturas
    from src.storage.models import FixtureSnapshot, League

    gateway = boveda_gateway_aislada
    jornada = JORNADA_JUEZ + 1
    # Captura con UNA sola clave y SIN sello S(I): el hueco del séptimo campo debe declararse.
    captura_aislada = {"id_partido": "SHIELD-J991-01", "p_local": CAPTURA_MUTILADA["p_local"]}
    with gateway.read_session() as sesion:
        liga_id = int(sesion.query(League).first().id)

    with gateway.write_transaction() as tx:
        tx.add(
            FixtureSnapshot(league_id=liga_id, matchday=jornada, matches_json=[captura_aislada])
        )
        tx.flush()

    with gateway.write_transaction() as tx:
        reporte = _sellar_p_prima_en_capturas(tx, liga_id, [jornada], {}, {}, forzar=True)
    assert reporte["forzar"] is True
    assert reporte["selladas"] == 0, "sin verdad homóloga en la 3NF no hay nada que sobreescribir"
    assert reporte["sin_valor"] == ["SHIELD-J991-01"]
    assert reporte["sin_suficiencia"] == ["SHIELD-J991-01"]
    assert _captura_publicada(gateway, liga_id, jornada) == captura_aislada, (
        "🚨 CERO INVENCIÓN: una captura sin verdad homóloga debe permanecer INTACTA"
    )
