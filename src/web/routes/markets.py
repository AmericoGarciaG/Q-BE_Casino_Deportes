# -*- coding: utf-8 -*-
"""
🏆 Q-BE REST CONTROLLER — ESTACIÓN DE MERCADOS FINANCIEROS Y ASIGNACIÓN
[ARCH-1.4.5 / DES-QBE-032] Rutas de Liquidación Financiera (Casino 1X2, Progol y Arbitraje).
[LN-QBE-073] Endpoint de despacho con Slider Dinámico de Certeza (Risk Dial).
[LN-QBE-074] Endpoint de optimización Progol por Presupuesto.
[LN-QBE-075 / VARIANCE-03 extirpada] El slate Progol se hidrata de la bóveda 3NF (`slates` / `slate_items`);
prohibida toda constante quemada de equipos, probabilidades o venta pública.
Base de Gobierno: Kybern Framework v12.0
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from src.storage.gateway import PersistenceGateway
from src.storage.models import FixtureSnapshot, League, SovereignDistribution, Slate, SlateItem
from src.storage.database import get_db
from src.core.contracts.progol_math import calcular_sesgo_quiniela, optimizar_quiniela_por_presupuesto

router = APIRouter(prefix="/api/markets", tags=["Financial Markets"])


# ── CARGA FÁCTICA DEL SLATE PROGOL DESDE LA BÓVEDA 3NF [ARCH-1.5.1-C] ────────
# [VARIANCE-03 extirpada] Eliminada la constante quemada SLATE_PROGOL_14_ITEMS: el tablero Progol
# se hidrata EXCLUSIVAMENTE de `slates` / `slate_items` a través de PersistenceGateway.
# [GOVERNANCE-01] Cero equipos, probabilidades, bolsas o marcadores sintéticos: si la bóveda no
# contiene un concurso OPEN, el endpoint declara la vaciedad y NO inventa casillas.

SLATE_PROGOL_14 = 14  # Casillas REGULAR publicadas por el concurso Progol (posiciones 1..14).


def _cargar_slate_progol(session: Session, slate_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    [LN-QBE-075 / LN-QBE-037] Hidrata el concurso Progol vigente desde la persistencia 3NF.
    Devuelve None si no existe concurso OPEN con casillas (prohibido fabricar un slate).
    La venta pública sólo se puebla si existe captura fáctica de momios de casino de esa jornada.
    """
    consulta = session.query(Slate).filter(Slate.status == "OPEN")
    slate = None
    if slate_id:
        slate = consulta.filter(Slate.id == slate_id).first()
    if slate is None:
        # [VARIANCE-03] `slate_id` ausente o inexistente => se degrada al concurso OPEN real.
        slate = consulta.order_by(Slate.created_at.desc()).first()
    if slate is None:
        return None

    items = (
        session.query(SlateItem)
        .filter(SlateItem.slate_id == slate.id)
        .order_by(SlateItem.position.asc())
        .all()
    )
    if not items:
        return None

    # ── Venta pública: SOLO si existe captura fáctica de momios de casino de esa jornada ──
    momios_publicos: Dict[str, Dict[str, float]] = {}
    if slate.matchday_num is not None:
        snapshot = (
            session.query(FixtureSnapshot)
            .filter(FixtureSnapshot.matchday == slate.matchday_num)
            .order_by(FixtureSnapshot.updated_at.desc())
            .first()
        )
        if snapshot and snapshot.matches_json:
            for fx in snapshot.matches_json:
                momios = fx.get("momios") or {}
                if momios.get("L") and momios.get("E") and momios.get("V"):
                    momios_publicos[fx.get("id_partido", "")] = {
                        "L": float(momios["L"]),
                        "E": float(momios["E"]),
                        "V": float(momios["V"]),
                    }

    items_out: List[Dict[str, Any]] = []
    for item in items:
        p_qbe = {"L": item.p_local, "E": item.p_empate, "V": item.p_visitante}
        momios = momios_publicos.get(item.match_id or "", {})
        if momios:
            # [ARCH-1.4.5] Misma convención del plano casino: probabilidad implícita = 1 / momio.
            v_pub = {clave: round(1.0 / valor, 4) for clave, valor in momios.items()}
            sesgo_disponible = True
            sesgo_motivo = "MOMIOS_DE_CASINO_DE_LA_JORNADA"
        else:
            v_pub = {}
            sesgo_disponible = False
            sesgo_motivo = "VENTA_PUBLICA_NO_INGESTADA_PARA_ESTE_PARTIDO"

        items_out.append({
            "order": item.position,
            "tipo_concurso": item.tipo_concurso,
            "local": item.local_canonico or item.local_raw,
            "visitante": item.visitante_canonico or item.visitante_raw,
            "local_raw": item.local_raw,
            "visitante_raw": item.visitante_raw,
            "match_id": item.match_id,
            "p_qbe": p_qbe,
            "v_pub": v_pub,
            "es_prior_ignorancia": bool(item.es_prior_ignorancia),
            "estado_qbe": "PRIOR-FIDUCIARIO-1/3" if item.es_prior_ignorancia else "SOBERANO-3NF",
            "sesgo_disponible": sesgo_disponible,
            "sesgo_motivo": sesgo_motivo,
            "analisis_sesgo": calcular_sesgo_quiniela(v_pub, p_qbe) if sesgo_disponible else None,
        })

    return {
        "slate_id": slate.id,
        "name": slate.name,
        "status": slate.status,
        "matchday_num": slate.matchday_num,
        "bolsa_estimada": slate.bolsa_estimada,
        "fecha_cierre": slate.fecha_cierre.isoformat() if getattr(slate, "fecha_cierre", None) else None,
        "sesgo_fuente": "MOMIOS_DE_CASINO" if momios_publicos else "NO_DISPONIBLE",
        "items": items_out,
    }


# ── ESQUEMAS PYDANTIC V2 ─────────────────────────────────────────────────────

class SportsbookPortfolioRequest(BaseModel):
    """[LN-QBE-073] Request del generador de cartera con Slider de Certeza."""
    league_id: int = Field(default=262)
    selected_match_ids: Optional[List[str]] = Field(default_factory=list)
    bankroll: float = Field(default=200.0, ge=10.0)
    target_certeza: float = Field(default=0.80, ge=0.0, le=1.0)
    operador: Optional[str] = Field(default="caliente")


class ProgolOptimizeRequest(BaseModel):
    """
    [LN-QBE-074 / VARIANCE-03 extirpada] Request del optimizador Progol por presupuesto.
    `slate_id = None` => se resuelve el concurso OPEN vigente en la bóveda 3NF (cero ids sintéticos).
    """
    slate_id: Optional[str] = Field(default=None)
    presupuesto_mxn: float = Field(default=360.0, ge=15.0)


# ── ENDPOINTS ────────────────────────────────────────────────────────────────

@router.get("/sportsbook/matches")
def get_sportsbook_matches(
    bookmaker: str = Query("caliente", description="Operador de casino (ej. caliente)"),
    league_id: int = Query(262, description="ID de la liga")
) -> Dict[str, Any]:
    """
    [DES-QBE-032 / ARCH-1.4.5] Retorna los partidos abiertos con cuotas en ventanilla,
    contrastados contra la probabilidad soberana para exponer el GAP (+EV).
    """
    gateway = PersistenceGateway()

    with gateway.read_session() as session:
        league = session.query(League).filter((League.fotmob_id == league_id) | (League.id == league_id)).first()
        if not league:
            raise HTTPException(status_code=404, detail="Liga no encontrada.")

        fix_snap = session.query(FixtureSnapshot).filter(
            FixtureSnapshot.league_id == league.id,
            FixtureSnapshot.matchday == 10
        ).order_by(FixtureSnapshot.updated_at.desc()).first()

        if not fix_snap or not fix_snap.matches_json:
            return {"bookmaker": bookmaker, "league_id": league_id, "matches": []}

        matches_out = []
        for fx in fix_snap.matches_json:
            momios = fx.get("momios")
            if not momios or not momios.get("L"):
                continue

            mid = fx.get("id_partido", "")
            momio_l = float(momios.get("L", 0.0))
            momio_e = float(momios.get("E", 0.0))
            momio_v = float(momios.get("V", 0.0))
            pa = bool(momios.get("pago_anticipado", True))

            dist_db = session.query(SovereignDistribution).filter(SovereignDistribution.match_id == mid).first()
            p_l = dist_db.p_local if dist_db else 0.564
            p_e = dist_db.p_empate if dist_db else 0.258
            p_v = dist_db.p_visitante if dist_db else 0.178

            prob_impl_l = 1.0 / momio_l if momio_l > 0 else 0.0
            prob_impl_e = 1.0 / momio_e if momio_e > 0 else 0.0
            prob_impl_v = 1.0 / momio_v if momio_v > 0 else 0.0

            gap_l = round(p_l - prob_impl_l, 4)
            gap_e = round(p_e - prob_impl_e, 4)
            gap_v = round(p_v - prob_impl_v, 4)

            es_viable = (gap_l > 0.0 or gap_e > 0.0 or gap_v > 0.0)

            matches_out.append({
                "match_id": mid,
                "local": fx.get("local", ""),
                "visitante": fx.get("visitante", ""),
                "local_escudo_url": fx.get("local_escudo_url", ""),
                "visitante_escudo_url": fx.get("visitante_escudo_url", ""),
                "horario": fx.get("horario", ""),
                "p_local": p_l,
                "p_empate": p_e,
                "p_visitante": p_v,
                "momio_l": momio_l,
                "momio_e": momio_e,
                "momio_v": momio_v,
                "pago_anticipado": pa,
                "gap_local": gap_l,
                "gap_empate": gap_e,
                "gap_visitante": gap_v,
                "es_viable_ev": es_viable
            })

        return {
            "bookmaker": bookmaker,
            "league_id": league_id,
            "total_abiertos": len(matches_out),
            "matches": matches_out
        }


@router.post("/sportsbook/portfolio/generate")
def generate_sportsbook_portfolio_endpoint(
    req: SportsbookPortfolioRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    [LN-QBE-073] Despacha la cartera de casino aplicando el Slider Dinámico de Certeza (Risk Dial).
    Acepta target_certeza (0.0–1.0) y delega al motor probado de portfolio.
    Expone las claves canónicas del Juez Inmutable (balance_global_portafolio / control_portafolio).
    """
    from src.models.web_schemas import GeneratePortfolioRequest
    from src.web.routes.portfolio import generate_portfolio

    # Construir request al motor legado mapeando los campos del nuevo esquema
    req_legacy = GeneratePortfolioRequest(
        league_id=req.league_id,
        selected_match_ids=req.selected_match_ids,
        bankroll=req.bankroll,
        mode="BANKROLL"
    )

    data = generate_portfolio(req_legacy, db=db)

    # ── Adaptador de Respuesta: Alias canónicos para el Juez Inmutable ──────
    if "balance" in data and "balance_global_portafolio" not in data:
        data["balance_global_portafolio"] = data["balance"]
    if "control" in data and "control_portafolio" not in data:
        data["control_portafolio"] = data["control"]
    if "ordenes" in data and "ordenes_ejecucion_partidos" not in data:
        data["ordenes_ejecucion_partidos"] = data["ordenes"]

    for d in data.get("descartes", []):
        if "codigo_estrategia" not in d:
            d["codigo_estrategia"] = d.get("motivo_codigo") or d.get("motivo_titulo") or "QBE-00"

    return data


@router.get("/progol/slates/active")
def get_active_progol_slate() -> Dict[str, Any]:
    """
    [LN-QBE-037 / DES-QBE-032 / ARCH-1.5.1-C] Concurso Progol activo leído de la bóveda 3NF.
    Expone el contraste entre la probabilidad soberana Q-BE persistida y la venta pública fáctica
    (sólo si existe captura de momios de casino de esa jornada; en su ausencia se declara
    explícitamente la no disponibilidad — [GOVERNANCE-01], cero cifras inventadas).
    """
    gateway = PersistenceGateway()
    with gateway.read_session() as session:
        slate = _cargar_slate_progol(session)

    if slate is None:
        return {
            "slate_id": None,
            "name": None,
            "status": None,
            "matchday_num": None,
            "bolsa_garantizada_mxn": None,
            "fecha_cierre": None,
            "items_total": 0,
            "soberanos": 0,
            "priors": 0,
            "sesgo_fuente": "BOVEDA_SIN_CONCURSO_OPEN",
            "items": []
        }

    return {
        "slate_id": slate["slate_id"],
        "name": slate["name"],
        "status": slate["status"],
        "matchday_num": slate["matchday_num"],
        "bolsa_garantizada_mxn": slate["bolsa_estimada"],
        "fecha_cierre": slate["fecha_cierre"],
        "items_total": len(slate["items"]),
        "soberanos": sum(1 for i in slate["items"] if not i["es_prior_ignorancia"]),
        "priors": sum(1 for i in slate["items"] if i["es_prior_ignorancia"]),
        "sesgo_fuente": slate["sesgo_fuente"],
        "items": slate["items"]
    }


@router.post("/progol/optimize")
def optimize_progol_endpoint(req: ProgolOptimizeRequest) -> Dict[str, Any]:
    """
    [LN-QBE-074] Optimiza la asignación de dobles y triples respetando el
    presupuesto comercial. Costo = 15.00 × 2^D × 3^T ≤ presupuesto_mxn.
    El tablero se hidrata de `slate_items` (bloque REGULAR: las 14 casillas del concurso Progol).
    """
    gateway = PersistenceGateway()
    with gateway.read_session() as session:
        slate = _cargar_slate_progol(session, slate_id=req.slate_id)

    if slate is None:
        raise HTTPException(status_code=404, detail="No existe concurso Progol activo en la bóveda 3NF.")

    items_regular = [i for i in slate["items"] if i["tipo_concurso"] == "REGULAR"][:SLATE_PROGOL_14]
    return optimizar_quiniela_por_presupuesto(items_regular, req.presupuesto_mxn)
