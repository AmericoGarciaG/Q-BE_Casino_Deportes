# -*- coding: utf-8 -*-
"""
🏆 THE SHIELD — SANDBOX VOLUMEN & PORTERÍA (DIM 1 & 4) SUITE
Juez Inmutable: [LN-QBE-111] / [ARCH-1.4.50]
Base de Gobierno: Kybern Framework v13.5 [GOV-TEST-01] (Pure Read-Only / In-Memory Test)
Varianza ratificada: VAR-2026-LAB5-EVIDENCIA — Opción A EJECUTADA (decretos D1/D2/D3, 2026-10-19)
"""

import hashlib
import json
from pathlib import Path

import pytest
from sqlalchemy import select

from src.core.metrics import SyntheticMetricsEngine
from src.storage.gateway import PersistenceGateway
from src.storage.models import Match
from scripts.laboratorio.sandbox_volumen_porteria_pipeline import (
    ejecutar_sandbox_volumen_porteria_partido,
    calcular_save_percentage,
    calcular_residuo_volumen_ortogonal,
    calcular_delta_posesion,
)

MATCH_ID = "LIGAMX-J11-07"
ESTADOS_VALIDOS = ("EXITO", "PARCIAL")
JORNADA_OBJETIVO = 11
ESTADOS_TERMINALES = ("FINALIZADO", "FINISHED")
CELDAS_SIN_SENSOR = ("V02", "V03", "V04", "V15", "V17")
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_TELEMETRIA = RAIZ_PROYECTO / "data" / "cache_telemetria_liga_mx_2026.json"


def _cargar_artefacto() -> dict:
    """Artefacto congelado de telemetría óptica (jamás se sintetiza aquí)."""
    assert RUTA_TELEMETRIA.exists(), (
        f"Falta el artefacto congelado {RUTA_TELEMETRIA.name}: ejecute "
        "`python -m scripts.ingesta.congelar_telemetria_fotmob` antes de sondear el Juez."
    )
    return json.loads(RUTA_TELEMETRIA.read_text(encoding="utf-8"))


def _identidades_3nf() -> dict:
    """Identidad canónica por fixture: `{match_id: (home_slug, away_slug, matchday_num)}`."""
    gateway = PersistenceGateway()
    with gateway.read_session() as sesion:
        filas = sesion.execute(select(Match)).scalars().all()
    return {
        str(fila.id): (
            str(fila.home_team_slug),
            str(fila.away_team_slug),
            int(fila.matchday_num or 0),
            str(fila.status or ""),
        )
        for fila in filas
    }


def _posesiones_de_corte(slug: str, identidades: dict, partidos: dict) -> list:
    """Muestra de posesión del corte futuro-ciego N−1 de un club (oráculo independiente)."""
    muestras = []
    for match_id, (home_slug, away_slug, jornada, estado) in identidades.items():
        if jornada >= JORNADA_OBJETIVO or estado not in ESTADOS_TERMINALES:
            continue
        registro = partidos.get(match_id)
        if registro is None:
            continue
        if home_slug == slug:
            muestras.append(float(registro["home"]["possession"]))
        elif away_slug == slug:
            muestras.append(float(registro["away"]["possession"]))
    return muestras


def test_invarianza_1_contrato_factico_volumen_y_porteria():
    """[INVARIANZA 1 - E2E]: V01 y V16 publican magnitudes REALES desde `match_telemetry`.

    DoD ratificado (decreto `D1`, 2026-10-19): con la telemetría óptica congelada el veredicto es
    `PARCIAL` (V01 y V16 `EVALUADO`); `EXITO` es inalcanzable por contrato porque V02/V03/V04/V15/V17
    no tienen sensor en `[LN-QBE-111]`. Se certifica además que esas cinco celdas degradan en
    `SIN EVIDENCIA (FASE 6)` sin imputar una sola cifra (`[GOVERNANCE-01]`).
    """
    res = ejecutar_sandbox_volumen_porteria_partido(match_id=MATCH_ID)

    assert res is not None
    assert res["status"] in ESTADOS_VALIDOS
    assert res["status"] == "PARCIAL", (
        "Con evidencia fáctica el techo es PARCIAL: EXITO exigiría 7/7 celdas EVALUADO y "
        "V02/V03/V04/V15/V17 carecen de sensor por contrato (decreto D1)."
    )
    assert res["escritura_bd"] is False
    assert res["llamadas_red"] is False
    assert "dimension_1_volumen" in res
    assert "dimension_4_porteria" in res
    assert len(res["dimension_1_volumen"]) == 4, "DIM 1 debe publicar V01-V04"
    assert len(res["dimension_4_porteria"]) == 3, "DIM 4 debe publicar V15-V17"

    for dimension, identificador in (
        (res["dimension_1_volumen"], "V01"),
        (res["dimension_4_porteria"], "V16"),
    ):
        celda = dimension[identificador]
        assert celda["id"] == identificador
        assert celda["estado"] == "EVALUADO", (
            f"{identificador} debe publicar EVALUADO con la telemetría congelada "
            "(posesión y SoTA reales en AMBOS clubes)"
        )
        assert celda["unidad"] == "%"
        assert str(celda["local"]).endswith("%") and str(celda["visita"]).endswith("%")
        for lado in ("local", "visita"):
            numero = celda[f"{lado}_num"]
            assert numero is not None
            assert 0.0 <= float(numero) <= 100.0

    # Posesión estrictamente positiva: el `0.0` es centinela de ausencia, jamás una medición.
    assert float(res["dimension_1_volumen"]["V01"]["local_num"]) > 0.0
    assert float(res["dimension_1_volumen"]["V01"]["visita_num"]) > 0.0

    # Cobertura íntegra del feed en AMBOS cortes: nada promediado sobre huecos.
    for lado in ("local", "visita"):
        cobertura = res["cobertura"]["telemetria"][lado]
        assert cobertura["cubiertos"] == cobertura["total"], (
            f"El corte {lado} debe tener telemetría íntegra, obtuvo "
            f"{cobertura['cubiertos']}/{cobertura['total']}"
        )
        assert cobertura["faltantes"] == []

    # Celdas sin sensor: degradación honesta, cero imputación.
    for identificador in CELDAS_SIN_SENSOR:
        dimension = (
            res["dimension_1_volumen"]
            if identificador.startswith("V0")
            else res["dimension_4_porteria"]
        )
        celda = dimension[identificador]
        assert celda["estado"] == "SIN EVIDENCIA"
        assert celda["local"] is None and celda["visita"] is None
        assert celda["local_num"] is None and celda["visita_num"] is None
        assert "FASE 6" in celda["nota"]

    # Residuo ortogonal y ΔPosición: cifras reales dentro de contrato.
    residuo = res["residuo_volumen"]
    for lado in ("local", "visita"):
        valor = residuo[lado]["residuo"]
        assert valor is not None
        assert -0.35 - 1e-9 <= float(valor) <= 0.35 + 1e-9
        assert abs(float(residuo[lado]["fcf"]) - (float(valor) + 1.0)) < 1e-5
    assert residuo["delta"] is not None
    assert res["delta_posesion"]["valor"] is not None


def test_invarianza_2_bipartita_por_partido_identidad_de_corte_y_delta():
    """[INVARIANZA 2 - BIPARTITA · decreto D2]: triple aserción fáctica.

    (i) `poss_H + poss_A ≡ 100.0` en CADA partido del artefacto congelado (identidad por partido),
        con reciprocidad defensiva `sota_H ≡ sot_A` y verificación de sede contra la 3NF.
    (ii) `V01.local_num == mean(posesión del corte N−1)` con tolerancia 1e-4 (identidad del corte).
    (iii) `ΔPosición == local_num − visita_num == +2.1 pp` con tolerancia 1e-4.

    La complementariedad NO es una identidad entre medias de cortes independientes
    (52.9 % + 50.8 % = 103.7 %): semejante aserción sería una falsa invariante, vetada por D2.
    """
    artefacto = _cargar_artefacto()
    partidos = artefacto["partidos"]
    identidades = _identidades_3nf()

    # Integridad del artefacto: la huella debe reproducirse sobre el cuerpo canónico.
    cuerpo = dict(artefacto)
    huella = str(cuerpo.pop("hash_sha256", ""))
    esperado = hashlib.sha256(
        json.dumps(cuerpo, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert huella == esperado, "La evidencia congelada fue alterada: huella SHA-256 no reproducible"
    assert int(artefacto["liga_fotmob_id"]) == 230
    assert partidos, "El artefacto congelado está vacío"
    assert artefacto["faltantes"] == [], f"La ingesta declaró faltantes: {artefacto['faltantes']}"

    # (i) Bipartita por partido: la ÚNICA suma 100 % legítima entre locales y visitas.
    for match_id, registro in partidos.items():
        home, away = registro["home"], registro["away"]
        total = float(home["possession"]) + float(away["possession"])
        assert abs(total - 100.0) <= 1e-9, (
            f"{match_id}: la posesión bipartita debe sumar exactamente 100 %, obtuvo {total}"
        )
        assert 0.0 < float(home["possession"]) < 100.0
        assert 0.0 < float(away["possession"]) < 100.0
        assert float(home["sota"]) == float(away["sot"]), "Reciprocidad: SoTA_H ≡ SoT_A"
        assert float(away["sota"]) == float(home["sot"]), "Reciprocidad: SoTA_A ≡ SoT_H"
        assert match_id in identidades, f"{match_id} no existe en la 3NF `matches`"
        home_slug, away_slug, _, _ = identidades[match_id]
        assert home["slug"] == home_slug and away["slug"] == away_slug, (
            f"{match_id}: sede invertida o club mal homologado ({home['slug']} vs {home_slug})"
        )

    res = ejecutar_sandbox_volumen_porteria_partido(match_id=MATCH_ID)
    v01 = res["dimension_1_volumen"]["V01"]
    assert v01["estado"] == "EVALUADO", "INVARIANZA 2 exige V01 con evidencia fáctica"

    # (ii) Identidad del corte: V01 publica la MEDIA de la muestra del club, no una cifra fabricada.
    home_slug, away_slug, _, _ = identidades[MATCH_ID]
    for lado, slug in (("local", home_slug), ("visita", away_slug)):
        muestras = _posesiones_de_corte(slug, identidades, partidos)
        assert muestras, f"El corte N−1 de {slug} no tiene muestra de posesión"
        assert len(muestras) == int(res["corte_n_1"][lado]["pj"]), (
            f"El oráculo del Juez y el sandbox discrepan en PJ del corte {lado}"
        )
        media = sum(muestras) / len(muestras)
        assert float(v01[f"{lado}_num"]) == pytest.approx(media, abs=1e-4), (
            f"V01.{lado}_num debe ser la media del corte de {slug}: {media} vs "
            f"{v01[f'{lado}_num']}"
        )

    # (iii) ΔPosición: identidad aritmética contra V01 y ancla sellada del decreto D2.
    delta = res["delta_posesion"]
    assert float(delta["valor"]) == pytest.approx(
        float(v01["local_num"]) - float(v01["visita_num"]), abs=1e-4
    ), "ΔPosición debe ser exactamente local_num − visita_num"
    assert float(delta["local"]) == pytest.approx(float(v01["local_num"]), abs=1e-4)
    assert float(delta["visita"]) == pytest.approx(float(v01["visita_num"]), abs=1e-4)
    assert float(delta["valor"]) == pytest.approx(2.1, abs=1e-4), (
        f"ΔPosición de {MATCH_ID} certificado en +2.1 pp, obtuvo {delta['valor']}"
    )
    assert delta["lectura"] == "PARIDAD TERRITORIAL"

    # Identidad matemática pura: independiente de la disponibilidad de feed.
    assert calcular_delta_posesion(56.4, 43.6) == 12.8
    assert calcular_delta_posesion(43.6, 56.4) == -12.8
    assert calcular_delta_posesion(50.0, 50.0) == 0.0
    with pytest.raises(ValueError):
        calcular_delta_posesion(120.0, -20.0)


def test_invarianza_3_save_percentage_acotado_y_exacto():
    """[INVARIANZA 3 - MATEMÁTICA]: Save% = 100·(SoTA − GC)/SoTA, acotado en [0, 100]."""
    assert calcular_save_percentage(10, 8) == 20.0
    assert calcular_save_percentage(10, 2) == 80.0
    assert calcular_save_percentage(5, 7) == 0.0, "GC > SoTA debe saturar a 0, nunca publicar negativo"
    assert calcular_save_percentage(0, 0) == 100.0, "Sin remates a puerta no hay nada que atajar"

    for sota, gc in ((12, 3), (1, 0), (25, 25), (40, 7), (8, 8)):
        valor = calcular_save_percentage(sota, gc)
        assert 0.0 <= valor <= 100.0

    with pytest.raises(ValueError):
        calcular_save_percentage(-1, 0)
    with pytest.raises(ValueError):
        calcular_save_percentage(5, -2)


def test_invarianza_4_residuo_volumen_ortogonal_cotas_y_delegacion():
    """[INVARIANZA 4 - DIRGEN]: v_Vol⊥ = FCF − 1 delegado VERBATIM a [LN-QBE-030], en [−0.35, +0.35]."""
    # Presión estéril saturada: poss 30 %, SoT 2 vs SoTA 6 ⇒ Raw_FCF = 0.36 ⇒ clamp 0.65 ⇒ −0.35
    assert abs(calcular_residuo_volumen_ortogonal(30.0, 2, 6) - (-0.35)) < 1e-6
    # Banda interior SIN clamp (delegación verbatim [VAR-2026-LAB5-FCF-COTAS]):
    # poss 65 %, SoT 2 vs SoTA 6 ⇒ Raw_FCF = 0.78 ∈ [0.65, 1.35] ⇒ −0.22
    assert abs(calcular_residuo_volumen_ortogonal(65.0, 2, 6) - (-0.22)) < 1e-6
    # Dominio convertido: poss 55 %, SoT 7 vs SoTA 2 ⇒ Raw_FCF = 1.60 ⇒ clamp 1.35 ⇒ +0.35
    assert abs(calcular_residuo_volumen_ortogonal(55.0, 7, 2) - 0.35) < 1e-6
    # Neutralidad territorial: poss 50 %, SoT 0, SoTA 0 ⇒ Raw_FCF = 1.00 ⇒ 0.00
    assert abs(calcular_residuo_volumen_ortogonal(50.0, 0, 0)) < 1e-6

    for poss, sot, sota in ((50, 5, 5), (60, 3, 9), (70, 8, 1), (35, 1, 10), (0, 0, 0)):
        valor = calcular_residuo_volumen_ortogonal(poss, sot, sota)
        assert -0.35 - 1e-6 <= valor <= 0.35 + 1e-6

    # Delegación verbatim al plano sellado: cero reimplementación del FCF.
    fcf = SyntheticMetricsEngine._compute_fcf(51.0, 5.0, 4.0)
    assert abs(calcular_residuo_volumen_ortogonal(51.0, 5.0, 4.0) - round(fcf - 1.0, 6)) < 1e-9

    with pytest.raises(ValueError):
        calcular_residuo_volumen_ortogonal(120.0, 5, 4)
