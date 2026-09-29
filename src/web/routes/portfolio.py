# -*- coding: utf-8 -*-
"""
Kybern Industrial — Portfolio REST Router [ARCH-PILLAR]
[ARCH-1.3.4] POST /api/portfolio/generate deprecado y desconectado: delega al controlador
desacoplado 3NF de markets.py. Conserva exclusivamente el servicio /api/portfolio/match-thesis.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.storage.database import get_db
from src.web.routes.markets import generate_sportsbook_portfolio_endpoint, SportsbookPortfolioRequest


router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.post("/generate")
def generate_portfolio(req: SportsbookPortfolioRequest, db: Session = Depends(get_db)):
    """
    [ARCH-1.3.4] Deprecado y desconectado del monolito legacy.
    Redirige la ejecución íntegramente al controlador desacoplado 3NF de markets.py,
    consumiendo el request moderno (SportsbookPortfolioRequest).
    """
    return generate_sportsbook_portfolio_endpoint(req, db)


import logging
from typing import Dict, Any
from pydantic import BaseModel

logger = logging.getLogger("PortfolioRouter")

class MatchThesisRequest(BaseModel):
    partido_id: str
    partido_data: Dict[str, Any]


@router.post("/match-thesis")
def generate_match_thesis_endpoint(req: MatchThesisRequest):
    """
    [ARCH-1.3.4 / ARCH-1.6.10] Invocación real de Gemini 3.6 Flash bajo demanda.
    """
    logger.info(f"🧠 [ON-DEMAND] Redactando Tesis con Gemini para partido {req.partido_id}...")
    print(f"🧠 [ON-DEMAND] Redactando Tesis con Gemini para partido {req.partido_id}...")
    from src.services.gemini_gateway import GeminiCognitiveGateway
    gateway = GeminiCognitiveGateway()
    tesis_html = gateway.generate_thesis(req.partido_data)
    return {"partido_id": req.partido_id, "tesis_html": tesis_html}
