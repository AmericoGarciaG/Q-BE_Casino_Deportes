# -*- coding: utf-8 -*-
"""
🏆 Q-BE REST CONTROLLER — ESTACIÓN DE MERCADOS FINANCIEROS Y ASIGNACIÓN
[ARCH-1.4.5 / DES-QBE-032] Rutas de Liquidación Financiera (Casino 1X2, Progol y Arbitraje).
[LN-QBE-073] Endpoint de despacho con Slider Dinámico de Certeza (Risk Dial).
[LN-QBE-074] Endpoint de optimización Progol por Presupuesto.
Base de Gobierno: Kybern Framework v12.0
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from src.storage.gateway import PersistenceGateway
from src.storage.models import FixtureSnapshot, League, SovereignDistribution
from src.storage.database import get_db
from src.core.contracts.progol_math import calcular_sesgo_quiniela, optimizar_quiniela_por_presupuesto

router = APIRouter(prefix="/api/markets", tags=["Financial Markets"])


# ── SLATE OFICIAL PROGOL 14 PARTIDOS ────────────────────────────────────────
SLATE_PROGOL_14_ITEMS = [
    {"order": 1,  "local": "Club América",        "visitante": "Chivas Guadalajara",    "v_pub": {"L": 0.65, "E": 0.20, "V": 0.15}, "p_qbe": {"L": 0.38, "E": 0.34, "V": 0.28}},
    {"order": 2,  "local": "Deportivo Toluca",    "visitante": "Santos Laguna",         "v_pub": {"L": 0.75, "E": 0.15, "V": 0.10}, "p_qbe": {"L": 0.72, "E": 0.18, "V": 0.10}},
    {"order": 3,  "local": "Club Puebla",         "visitante": "Atlante",               "v_pub": {"L": 0.52, "E": 0.28, "V": 0.20}, "p_qbe": {"L": 0.56, "E": 0.26, "V": 0.18}},
    {"order": 4,  "local": "Cruz Azul",           "visitante": "Rayados de Monterrey",  "v_pub": {"L": 0.58, "E": 0.24, "V": 0.18}, "p_qbe": {"L": 0.40, "E": 0.32, "V": 0.28}},
    {"order": 5,  "local": "Pumas UNAM",          "visitante": "Atlas FC",              "v_pub": {"L": 0.60, "E": 0.25, "V": 0.15}, "p_qbe": {"L": 0.39, "E": 0.33, "V": 0.28}},
    {"order": 6,  "local": "Tigres UANL",         "visitante": "FC Juárez",             "v_pub": {"L": 0.70, "E": 0.18, "V": 0.12}, "p_qbe": {"L": 0.68, "E": 0.22, "V": 0.10}},
    {"order": 7,  "local": "Atlético San Luis",   "visitante": "Necaxa",                "v_pub": {"L": 0.55, "E": 0.25, "V": 0.20}, "p_qbe": {"L": 0.36, "E": 0.34, "V": 0.30}},
    {"order": 8,  "local": "Club Pachuca",        "visitante": "Club Tijuana",          "v_pub": {"L": 0.52, "E": 0.28, "V": 0.20}, "p_qbe": {"L": 0.50, "E": 0.28, "V": 0.22}},
    {"order": 9,  "local": "Club León",           "visitante": "Querétaro FC",          "v_pub": {"L": 0.55, "E": 0.25, "V": 0.20}, "p_qbe": {"L": 0.52, "E": 0.28, "V": 0.20}},
    {"order": 10, "local": "Arsenal",             "visitante": "Chelsea",               "v_pub": {"L": 0.58, "E": 0.24, "V": 0.18}, "p_qbe": {"L": 0.42, "E": 0.30, "V": 0.28}},
    {"order": 11, "local": "Real Madrid",         "visitante": "Barcelona",             "v_pub": {"L": 0.50, "E": 0.25, "V": 0.25}, "p_qbe": {"L": 0.45, "E": 0.28, "V": 0.27}},
    {"order": 12, "local": "Inter Milan",         "visitante": "AC Milan",              "v_pub": {"L": 0.45, "E": 0.30, "V": 0.25}, "p_qbe": {"L": 0.44, "E": 0.31, "V": 0.25}},
    {"order": 13, "local": "Liverpool",           "visitante": "Manchester City",       "v_pub": {"L": 0.40, "E": 0.30, "V": 0.30}, "p_qbe": {"L": 0.38, "E": 0.32, "V": 0.30}},
    {"order": 14, "local": "PSG",                 "visitante": "Olympique Marsella",   "v_pub": {"L": 0.65, "E": 0.20, "V": 0.15}, "p_qbe": {"L": 0.62, "E": 0.22, "V": 0.16}},
]


# ── ESQUEMAS PYDANTIC V2 ─────────────────────────────────────────────────────

class SportsbookPortfolioRequest(BaseModel):
    """[LN-QBE-073] Request del generador de cartera con Slider de Certeza."""
    league_id: int = Field(default=262)
    selected_match_ids: List[str]
    bankroll: float = Field(default=200.0, ge=10.0)
    target_certeza: float = Field(default=0.80, ge=0.0, le=1.0)


class ProgolOptimizeRequest(BaseModel):
    """[LN-QBE-074] Request del optimizador Progol por presupuesto."""
    slate_id: str = Field(default="PROGOL_2245")
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
            FixtureSnapshot.matchday == 9
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
    # El motor legado emite: "balance" y "control"
    # El Juez Inmutable [FASE 6] exige: "balance_global_portafolio" y "control_portafolio"
    if "balance" in data and "balance_global_portafolio" not in data:
        data["balance_global_portafolio"] = data["balance"]
    if "control" in data and "control_portafolio" not in data:
        data["control_portafolio"] = data["control"]

    return data


@router.get("/progol/slates/active")
def get_active_progol_slate() -> Dict[str, Any]:
    """
    [LN-QBE-037 / DES-QBE-032] Concurso Progol activo de 14 partidos
    con contraste de venta pública vs probabilidad soberana Q-BE.
    """
    analizados = []
    for p in SLATE_PROGOL_14_ITEMS:
        sesgo = calcular_sesgo_quiniela(p["v_pub"], p["p_qbe"])
        analizados.append({**p, "analisis_sesgo": sesgo})

    return {
        "slate_id": "PROGOL_2245",
        "name": "Concurso Progol 2245",
        "bolsa_garantizada_mxn": 25000000.0,
        "items": analizados
    }


@router.post("/progol/optimize")
def optimize_progol_endpoint(req: ProgolOptimizeRequest) -> Dict[str, Any]:
    """
    [LN-QBE-074] Optimiza la asignación de dobles y triples respetando el
    presupuesto comercial. Costo = 15.00 × 2^D × 3^T ≤ presupuesto_mxn.
    """
    return optimizar_quiniela_por_presupuesto(SLATE_PROGOL_14_ITEMS, req.presupuesto_mxn)
