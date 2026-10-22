# -*- coding: utf-8 -*-
"""
🔍 Q-BE: SONDA DE COMPLETITUD FÁCTICA DEL VISOR DE CALIBRACIÓN (44V · J1-J17)
[LN-QBE-119] / [ARCH-1.4.58] — Auditoría de SÓLO LECTURA sobre la salida REAL del contrato Pydantic.
Régimen: [DIRGEN-STRICT] · Cero DML, cero red, cero cifra fabricada [GOVERNANCE-01].
Autoridad: Américo García Guerrero (Director Humano)

QUÉ CERTIFICA
-------------
1. Cero `0 de 0`: toda dimensión publicada declara `total_variables > 0` y
   `variables_evaluadas <= total_variables`; el catálogo suma exactamente 32 variables
   ([LN-QBE-120] deroga la partición 12×44 de [LN-QBE-101]).
2. Coherencia de badge: `tiene_datos` ⟺ (`variables_evaluadas` > 0). Un `SIN EVALUAR` con
   evidencia evaluada —o un encendido sin evidencia— es anomalía 🔴.
3. Cotas físicas: SoT/SoTA por partido (`V07`/`V13`) en `[0, 15.0]` y posesión (`V01`) en `[0, 100]`.
   Una sumatoria de torneo en una casilla de tasa rebasa la cota y se declara 🔴.
4. Identidad de universo: `partidos_auditados + partidos_pendientes_captura == partidos_concluidos_boveda`
   (una jornada concluida jamás desaparece del Visor).
5. Sincronía declarada: las jornadas del rango sin evidencia en la bóveda se NOMBRAN (🟡); jamás se
   inventan marcadores ni se reproyecta una distribución (ausencia honesta).

El objeto auditado es la salida YA VALIDADA por `CalibrationReportResponse` (el mismo DTO que sirve
el endpoint `GET /api/markets/backtesting/calibration-report`): si el esquema descarta un contador, la
sonda lo ve exactamente como lo ve el navegador.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.models.web_schemas import CalibrationReportResponse  # noqa: E402
from src.storage.gateway import PersistenceGateway  # noqa: E402
from src.storage.models import Match  # noqa: E402
from src.web.routes.markets import (  # noqa: E402
    _construir_reporte_calibracion,
    _ESTADOS_CONCLUIDOS_BACKTESTING,
)

LIGA_ID_CANONICA = 1
RANGO_JORNADAS_DEFAULT = "1-17"
RUTA_SALIDA_DEFAULT = os.path.join("data", "output", "auditoria_completitud_visor.json")

# [LN-QBE-120] Cardinalidad vigente del catálogo PRE-KICKOFF (deroga la partición 12×44).
TOTAL_VARIABLES_CATALOGO = 32
# [LN-QBE-119] Cota física de la tasa por partido: una sumatoria de corte (41, 56, …) la rebasa.
COTA_SOT_MAX = 15.0
COTA_POSS_MIN = 0.0
COTA_POSS_MAX = 100.0

NIVEL_ROJO = "🔴"
NIVEL_AMBAR = "🟡"
NIVEL_VERDE = "🟢"


# ── Utilidades de rango ───────────────────────────────────────────────────────────────────────
def _expandir_rango(texto: str) -> List[int]:
    """`'1-13'` → `[1..13]`; `'1,4,7'` → `[1,4,7]`. Rango inválido ⇒ `ValueError` (cero silencio)."""
    jornadas: List[int] = []
    for tramo in str(texto or "").split(","):
        tramo = tramo.strip()
        if not tramo:
            continue
        if "-" in tramo:
            inicio, _, fin = tramo.partition("-")
            desde, hasta = int(inicio), int(fin)
            if hasta < desde:
                raise ValueError(f"rango de jornadas invertido: '{tramo}'")
            jornadas.extend(range(desde, hasta + 1))
        else:
            jornadas.append(int(tramo))
    if not jornadas:
        raise ValueError("rango de jornadas vacío")
    return sorted(set(jornadas))


def _num(valor: Any) -> Optional[float]:
    """Convierte a float sin inventar: `None`/texto no numérico ⇒ `None`."""
    if valor is None or isinstance(valor, bool):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


# ── Universo factual de la bóveda (independiente del Visor) ──────────────────────────────────
def _universo_boveda(session) -> Tuple[int, Dict[int, int], int]:
    """`(partidos concluidos, {jornada: concluidos}, nº de competencias distintas)`.

    Universo factual puro: marcador consumado + estado concluido. La ley de estados NO se
    reimplementa: se importa la constante sellada del Visor.
    """
    filas = session.query(Match).all()
    por_jornada: Dict[int, int] = {}
    competencias = set()
    concluidos = 0
    for fila in filas:
        competencias.add(str(fila.competition_id or ""))
        if fila.matchday_num is None or fila.score_home is None or fila.score_away is None:
            continue
        if str(fila.status or "").upper() not in _ESTADOS_CONCLUIDOS_BACKTESTING:
            continue
        jornada = int(fila.matchday_num)
        por_jornada[jornada] = por_jornada.get(jornada, 0) + 1
        concluidos += 1
    return concluidos, por_jornada, len(competencias)


def _anomalia(nivel: str, codigo: str, detalle: str, jornada: Any = None,
              id_partido: Any = None) -> Dict[str, Any]:
    return {
        "nivel": nivel,
        "codigo": codigo,
        "detalle": detalle,
        "jornada": jornada,
        "id_partido": id_partido,
    }


# ── Auditoría de una casilla micro ──────────────────────────────────────────────────────────
def _auditar_partido(partido: Dict[str, Any]) -> Dict[str, Any]:
    """Valida la telemetría dimensional de 32V de UNA casilla micro del Visor.

    Retorna `{evaluadas, total, cobertura_pct, sot, poss, anomalias}`. `sot` es la media de las dos
    porterías cuando ambas están publicadas (`None` si el partido no porta evidencia de volumen).
    """
    jornada = partido.get("jornada")
    id_partido = partido.get("id_partido")
    anomalias: List[Dict[str, Any]] = []

    atribucion = partido.get("atribucion_factorial") or {}
    catalogo = atribucion.get("variables_44") or {}
    dimensiones = catalogo.get("dimensiones") or []

    if not dimensiones:
        anomalias.append(_anomalia(
            NIVEL_ROJO, "SIN_CATALOGO_44V",
            "la casilla micro no publica dimensiones del catálogo de 32 variables [LN-QBE-120]", jornada, id_partido,
        ))
        return {
            "evaluadas": 0, "total": 0, "cobertura_pct": 0.0,
            "sot": None, "poss": None, "anomalias": anomalias,
        }

    evaluadas = 0
    total = 0
    valores: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
    for dimension in dimensiones:
        evaluadas_dim = int(dimension.get("variables_evaluadas") or 0)
        total_dim = int(dimension.get("total_variables") or 0)
        evaluadas += evaluadas_dim
        total += total_dim

        # (1) Cero `0 de 0`: un denominador nulo jamás se publica como medición.
        if total_dim <= 0:
            anomalias.append(_anomalia(
                NIVEL_ROJO, "DENOMINADOR_NULO",
                f"dimensión '{dimension.get('dimension')}' declara 0 variables totales", jornada, id_partido,
            ))
        if evaluadas_dim > total_dim:
            anomalias.append(_anomalia(
                NIVEL_ROJO, "EVALUADAS_EXCEDE_TOTAL",
                f"dimensión '{dimension.get('dimension')}': {evaluadas_dim} evaluadas > {total_dim} totales",
                jornada, id_partido,
            ))
        # `[ARCH-1.4.58]` El alias histórico `conteo` debe seguir espejando `total_variables`: si
        # divergen, un consumidor forense cuenta un denominador que ya no existe.
        if int(dimension.get("conteo") or 0) != total_dim:
            anomalias.append(_anomalia(
                NIVEL_ROJO, "CONTEO_DIVERGENTE",
                f"dimensión '{dimension.get('dimension')}': conteo={dimension.get('conteo')} ≠ "
                f"total_variables={total_dim}", jornada, id_partido,
            ))
        # (2) Coherencia del badge bicolor: `tiene_datos` ⟺ evidencia realmente evaluada.
        declarado = bool(dimension.get("tiene_datos"))
        if declarado != (evaluadas_dim > 0):
            anomalias.append(_anomalia(
                NIVEL_ROJO, "BADGE_INCOHERENTE",
                f"dimensión '{dimension.get('dimension')}': tiene_datos={declarado} con "
                f"{evaluadas_dim} evaluadas", jornada, id_partido,
            ))

        for variable in dimension.get("variables") or []:
            identificador = str(variable.get("id") or "")
            if identificador in ("V01", "V07", "V13"):
                valores[identificador] = (_num(variable.get("local")), _num(variable.get("visita")))

    # (3) Cota física de la tasa por partido (detector de sumatoria de torneo en casilla de tasa).
    # [LN-QBE-120] SoT = V07 y SoTA = V13 tras la renumeración de 32 variables.
    for identificador in ("V07", "V13"):
        for lado, valor in zip(("local", "visita"), valores.get(identificador, (None, None))):
            if valor is None:
                continue
            if valor < 0.0 or valor > COTA_SOT_MAX:
                anomalias.append(_anomalia(
                    NIVEL_ROJO, "COTA_SOT",
                    f"{identificador}.{lado} = {valor} fuera de [0, {COTA_SOT_MAX}] (¿sumatoria de corte?)",
                    jornada, id_partido,
                ))
    for lado, valor in zip(("local", "visita"), valores.get("V01", (None, None))):
        if valor is None:
            continue
        if valor < COTA_POSS_MIN or valor > COTA_POSS_MAX:
            anomalias.append(_anomalia(
                NIVEL_ROJO, "COTA_POSS",
                f"V01.{lado} = {valor} fuera de [0, 100]", jornada, id_partido,
            ))

    if total != TOTAL_VARIABLES_CATALOGO:
        anomalias.append(_anomalia(
            NIVEL_ROJO, "CATALOGO_INCOMPLETO",
            f"el catálogo suma {total} variables (contrato: {TOTAL_VARIABLES_CATALOGO})",
            jornada, id_partido,
        ))

    porterias = [v for v in valores.get("V07", (None, None)) if v is not None]
    posesiones = [v for v in valores.get("V01", (None, None)) if v is not None]
    return {
        "evaluadas": evaluadas,
        "total": total,
        "cobertura_pct": round((evaluadas / total) * 100.0, 2) if total else 0.0,
        "sot": round(sum(porterias) / len(porterias), 3) if porterias else None,
        "poss": round(sum(posesiones) / len(posesiones), 2) if posesiones else None,
        "anomalias": anomalias,
    }


def _media(valores: List[float]) -> Optional[float]:
    """Media aritmética sin inventar: lista vacía ⇒ `None` (jamás `0.0` fabricado)."""
    return round(sum(valores) / len(valores), 3) if valores else None


# ── Orquestación de la sonda ──────────────────────────────────────────────────────────────────
def auditar_completitud(
    liga_id: Optional[int] = LIGA_ID_CANONICA,
    jornadas: str = RANGO_JORNADAS_DEFAULT,
    ruta_salida: str = RUTA_SALIDA_DEFAULT,
) -> Dict[str, Any]:
    """Barre el rango completo contra la salida REAL del Visor y devuelve el parte auditable."""
    esperadas = _expandir_rango(jornadas)
    anomalias: List[Dict[str, Any]] = []

    gateway = PersistenceGateway()
    with gateway.read_session() as session:
        crudo = _construir_reporte_calibracion(session, liga_id)
        concluidos_boveda, boveda_por_jornada, competencias = _universo_boveda(session)

    # El objeto auditado es la salida YA VALIDADA por el DTO del endpoint (lo que ve el navegador).
    reporte = CalibrationReportResponse.model_validate(crudo).model_dump()
    resumen_reporte = reporte.get("resumen_temporada") or {}

    detalle_jornadas: List[Dict[str, Any]] = []
    partidos_auditados = 0
    evaluadas_global = 0
    total_global = 0
    for bloque in reporte.get("jornadas") or []:
        numero = int(bloque.get("jornada"))
        partidos = bloque.get("partidos") or []
        metricas = [_auditar_partido(partido) for partido in partidos]
        rojos_jornada = 0
        for metrica in metricas:
            anomalias.extend(metrica["anomalias"])
            rojos_jornada += sum(1 for a in metrica["anomalias"] if a["nivel"] == NIVEL_ROJO)
            evaluadas_global += metrica["evaluadas"]
            total_global += metrica["total"]

        sots = [m["sot"] for m in metricas if m["sot"] is not None]
        coberturas = [m["cobertura_pct"] for m in metricas if m["total"] > 0]
        partidos_auditados += len(partidos)
        if rojos_jornada:
            estado = NIVEL_ROJO
        elif not sots or not coberturas or max(coberturas) <= 0.0:
            estado = NIVEL_AMBAR
        else:
            estado = NIVEL_VERDE
        detalle_jornadas.append({
            "jornada": numero,
            "partidos": len(partidos),
            "cobertura_44v_pct": _media(coberturas) if coberturas else None,
            "sot_promedio": _media(sots),
            "evaluadas": sum(m["evaluadas"] for m in metricas),
            "total_variables": sum(m["total"] for m in metricas),
            "estado": estado,
            "anomalias": rojos_jornada,
        })

    publicadas = {int(bloque["jornada"]) for bloque in detalle_jornadas}
    pendientes = int(resumen_reporte.get("partidos_pendientes_captura") or 0)

    # (4) Sincronía: una jornada con partidos CONSUMADOS en la bóveda no puede faltar del Visor.
    faltantes = sorted((set(esperadas) & set(boveda_por_jornada)) - publicadas)
    for numero in faltantes:
        anomalias.append(_anomalia(
            NIVEL_ROJO, "SINCRONIA_JORNADA",
            f"la bóveda porta {boveda_por_jornada[numero]} partidos consumados de J{numero} y el "
            "Visor no publica la jornada", numero, None,
        ))

    # (5) Ausencia honesta: jornadas del rango sin evidencia en la bóveda se NOMBRAN, jamás se fabrican.
    sin_evidencia = sorted(set(esperadas) - set(boveda_por_jornada))
    for numero in sin_evidencia:
        anomalias.append(_anomalia(
            NIVEL_AMBAR, "JORNADA_SIN_EVIDENCIA",
            f"J{numero} no porta marcadores consumados en la bóveda: ausencia declarada, cero invención",
            numero, None,
        ))

    # (6) Identidad de universo Visor ↔ bóveda (merma de partidos auditables).
    merma = concluidos_boveda - (partidos_auditados + pendientes)
    if merma != 0:
        nivel = NIVEL_ROJO if competencias <= 1 else NIVEL_AMBAR
        anomalias.append(_anomalia(
            nivel, "UNIVERSO_MERMA",
            f"concluidos en bóveda={concluidos_boveda} vs auditados={partidos_auditados} + "
            f"pendientes={pendientes} (merma {merma})", None, None,
        ))

    rojos = sum(1 for a in anomalias if a["nivel"] == NIVEL_ROJO)
    ambar = sum(1 for a in anomalias if a["nivel"] == NIVEL_AMBAR)
    nivel_global = NIVEL_ROJO if rojos else (NIVEL_AMBAR if ambar else NIVEL_VERDE)

    parte = {
        "sonda": "auditar_completitud_visor",
        "nodo": "[LN-QBE-119] / [ARCH-1.4.58]",
        "regimen": "[DIRGEN-STRICT] · solo lectura",
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "liga_id": liga_id,
        "rango_jornadas": jornadas,
        "resumen": {
            "nivel_global": nivel_global,
            "codigo_salida": 1 if rojos else 0,
            "anomalias_rojas": rojos,
            "anomalias_ambar": ambar,
            "jornadas_publicadas": sorted(publicadas),
            "jornadas_boveda": sorted(boveda_por_jornada.keys()),
            "jornadas_sin_evidencia": sin_evidencia,
            "jornadas_faltantes_sync": faltantes,
            "partidos_auditados": partidos_auditados,
            "partidos_pendientes_captura": pendientes,
            "partidos_concluidos_boveda": concluidos_boveda,
            "competencias_en_boveda": competencias,
            "cobertura_44v_pct": round((evaluadas_global / total_global) * 100.0, 2) if total_global else 0.0,
            "brier_score_qbe": resumen_reporte.get("brier_score_qbe"),
            "brier_score_mercado": resumen_reporte.get("brier_score_mercado"),
            "alpha_calibracion_pct": resumen_reporte.get("alpha_calibracion_pct"),
        },
        "jornadas": detalle_jornadas,
        "anomalias": anomalias,
    }
    if ruta_salida:
        parte["ruta_salida"] = _escribir_json(parte, ruta_salida)
    return parte


def _escribir_json(parte: Dict[str, Any], ruta_salida: str) -> str:
    """Materializa el parte auditable en disco (UTF-8) y devuelve la ruta absoluta escrita."""
    ruta_absoluta = ruta_salida if os.path.isabs(ruta_salida) else os.path.join(PROJECT_ROOT, ruta_salida)
    os.makedirs(os.path.dirname(ruta_absoluta), exist_ok=True)
    with open(ruta_absoluta, "w", encoding="utf-8") as manejador:
        json.dump(parte, manejador, ensure_ascii=False, indent=2)
    return ruta_absoluta


# ── Presentación en consola ──────────────────────────────────────────────────────────────────
def _imprimir_tabla(parte: Dict[str, Any]) -> None:
    """Cartelera ASCII del barrido J1→J17 (sin color: legible en cualquier terminal)."""
    resumen = parte["resumen"]
    ancho = 98
    print("=" * ancho)
    print("SONDA DE COMPLETITUD FACTICA DEL VISOR 44V  ·  [LN-QBE-119] / [ARCH-1.4.58]")
    print(f"  Liga: {parte['liga_id']}  ·  Rango: J{parte['rango_jornadas']}  ·  "
          f"Regimen: solo lectura  ·  {parte['generado_utc']}")
    print("=" * ancho)
    print(f"{'J':>4} {'PART':>5} {'COBERT.44V':>11} {'SoT MEDIO':>10} {'ANOM':>5}  ESTADO")
    print("-" * ancho)

    detalle = {int(fila["jornada"]): fila for fila in parte["jornadas"]}
    sin_evidencia = set(resumen["jornadas_sin_evidencia"])
    faltantes = set(resumen["jornadas_faltantes_sync"])
    for numero in _expandir_rango(parte["rango_jornadas"]):
        fila = detalle.get(numero)
        if fila is None:
            if numero in faltantes:
                print(f"{numero:>4} {'-':>5} {'-':>11} {'-':>10} {'-':>5}  🔴 NO PUBLICADA (boveda con consumados)")
            elif numero in sin_evidencia:
                print(f"{numero:>4} {'-':>5} {'-':>11} {'-':>10} {'-':>5}  🟡 SIN EVIDENCIA EN BOVEDA")
            else:
                print(f"{numero:>4} {'-':>5} {'-':>11} {'-':>10} {'-':>5}  ⚪ FUERA DE ALCANCE")
            continue
        cobertura = fila["cobertura_44v_pct"]
        sot = fila["sot_promedio"]
        texto_cobertura = f"{cobertura:.1f}%" if cobertura is not None else "-"
        texto_sot = f"{sot:.3f}" if sot is not None else "-"
        print(f"{numero:>4} {fila['partidos']:>5} {texto_cobertura:>11} {texto_sot:>10} "
              f"{fila['anomalias']:>5}  {fila['estado']}")

    print("-" * ancho)
    print(f"  Partidos auditados .........: {resumen['partidos_auditados']}")
    print(f"  Concluidos en boveda .......: {resumen['partidos_concluidos_boveda']}"
          f"   (pendientes declarados: {resumen['partidos_pendientes_captura']})")
    print(f"  Cobertura global 44V .......: {resumen['cobertura_44v_pct']:.2f}%")
    print(f"  Jornadas publicadas ........: {resumen['jornadas_publicadas']}")
    print(f"  Sin evidencia (ambar) ......: {resumen['jornadas_sin_evidencia'] or 'ninguna'}")
    print(f"  Faltantes de sincronia .....: {resumen['jornadas_faltantes_sync'] or 'ninguna'}")
    print(f"  Brier QBE / Mercado ........: {resumen['brier_score_qbe']} / {resumen['brier_score_mercado']}"
          f"   alpha = {resumen['alpha_calibracion_pct']}%")

    for nivel in (NIVEL_ROJO, NIVEL_AMBAR):
        bloque = [a for a in parte["anomalias"] if a["nivel"] == nivel]
        if not bloque:
            continue
        print("-" * ancho)
        print(f"  Anomalias {nivel} ({len(bloque)}):")
        for anomalia in bloque[:40]:
            ubicacion = f"J{anomalia['jornada']}" if anomalia["jornada"] else "global"
            print(f"    {nivel} [{anomalia['codigo']}] {ubicacion} · {anomalia['detalle']}")
        if len(bloque) > 40:
            print(f"    ... {len(bloque) - 40} anomalias adicionales en el JSON")

    print("=" * ancho)
    print(f"  VEREDICTO: {resumen['nivel_global']}  ·  rojas={resumen['anomalias_rojas']}  "
          f"ambar={resumen['anomalias_ambar']}  ·  EXIT CODE {resumen['codigo_salida']}")
    if parte.get("ruta_salida"):
        print(f"  Parte JSON: {parte['ruta_salida']}")
    print("=" * ancho)


# ── CLI ──────────────────────────────────────────────────────────────────────────────────────
def _liga(valor: str) -> Optional[int]:
    """`'1'` → 1; `'global'`/`'todas'` → `None` (universo completo, sin filtro de liga)."""
    if str(valor).strip().lower() in ("global", "todas", "todos", "none", ""):
        return None
    return int(valor)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sonda de completitud factica del Visor de Calibracion 44V (solo lectura)."
    )
    parser.add_argument("--liga-id", type=_liga, default=LIGA_ID_CANONICA,
                        help="liga a auditar (por defecto 1 = Liga MX canonica; 'global' = todas)")
    parser.add_argument("--jornadas", default=RANGO_JORNADAS_DEFAULT,
                        help="rango de jornadas a barrer (por defecto '1-17')")
    parser.add_argument("--salida", default=RUTA_SALIDA_DEFAULT,
                        help="ruta del parte JSON (relativa a la raiz del proyecto)")
    parser.add_argument("--json", action="store_true", help="emitir el parte JSON integro por stdout")
    argumentos = parser.parse_args(argv)

    parte = auditar_completitud(argumentos.liga_id, argumentos.jornadas, argumentos.salida)
    if argumentos.json:
        print(json.dumps(parte, ensure_ascii=False, indent=2))
    else:
        _imprimir_tabla(parte)
    return int(parte["resumen"]["codigo_salida"])


if __name__ == "__main__":
    sys.exit(main())
