# -*- coding: utf-8 -*-
"""
🏆 Q-BE PERSISTENCE BRIDGE — SINCRONIZACIÓN DE DISTRIBUCIONES SOBERANAS
[ARCH-1.6.11] Puente Transaccional E2E: Hechos Deportivos -> Sovereign Pipeline -> SQLite 3NF.
Base de Gobierno: Kybern Framework v12.0 / Tratado Volumen I
"""

import logging
from typing import Dict, Any, List, Optional
from src.storage.gateway import PersistenceGateway
from src.storage.models import Competition, Match, SovereignDistribution
from src.core.sovereign_pipeline import generar_distribucion_soberana

logger = logging.getLogger("DistributionSync")


def sincronizar_distribuciones_soberanas_partidos(
    partidos_datos: List[Dict[str, Any]],
    gateway: Optional[PersistenceGateway] = None
) -> Dict[str, Any]:
    """
    [ARCH-1.6.11] Ejecuta la generación y persistencia transaccional atómica
    de distribuciones soberanas sobre la tabla 3NF 'sovereign_distributions'.
    """
    gw = gateway or PersistenceGateway()
    procesados = 0
    exitosos = 0
    errores = []

    for item in partidos_datos:
        match_id = item.get("match_id")
        comp_id = item.get("competition_id", "MEX_LIGAMX")

        if not match_id:
            continue

        procesados += 1

        try:
            # 1. Obtener parámetros macro de la competición desde la BD
            mu_liga = 2.65
            gamma_home = 0.15

            with gw.read_session() as session:
                comp = session.query(Competition).filter(Competition.id == comp_id).first()
                if comp:
                    mu_liga = float(comp.macro_mu_liga or 2.65)
                    gamma_home = float(comp.macro_gamma_home or 0.15)

            # 2. Generación matemática soberana con el pipeline del Tratado Vol. I
            dist_out = generar_distribucion_soberana(
                match_id=match_id,
                raw_match_data=item,
                mu_liga=mu_liga,
                gamma_home_base=gamma_home,
                delta_alt_metros=float(item.get("delta_alt_metros", 0.0) or 0.0),
                delta_descanso_dias=float(item.get("delta_descanso_dias", 0.0) or 0.0),
                q_mod_h=float(item.get("q_mod_h", 1.0) or 1.0),
                q_mod_a=float(item.get("q_mod_a", 1.0) or 1.0)
            )

            # 3. Persistencia atómica en la tabla 3NF 'sovereign_distributions'
            trace_dict = dist_out.audit_trace.model_dump()
            epist_delta = float(trace_dict.get("intensidades", {}).get("ratio", 0.0) or 0.0)

            with gw.write_transaction() as tx:
                dist_rec = tx.query(SovereignDistribution).filter(
                    SovereignDistribution.match_id == match_id
                ).first()

                if not dist_rec:
                    dist_rec = SovereignDistribution(
                        match_id=match_id,
                        model_version="v13.0-DIRGEN",
                        p_local=dist_out.p_local,
                        p_empate=dist_out.p_empate,
                        p_visitante=dist_out.p_visitante,
                        lambda_home=dist_out.lambda_home,
                        lambda_away=dist_out.lambda_away,
                        phi_lead2_home=dist_out.phi_lead2_home,
                        phi_lead2_away=dist_out.phi_lead2_away,
                        epistemic_delta=epist_delta,
                        audit_trace_json=trace_dict
                    )
                    tx.add(dist_rec)
                else:
                    dist_rec.model_version = "v13.0-DIRGEN"
                    dist_rec.p_local = dist_out.p_local
                    dist_rec.p_empate = dist_out.p_empate
                    dist_rec.p_visitante = dist_out.p_visitante
                    dist_rec.lambda_home = dist_out.lambda_home
                    dist_rec.lambda_away = dist_out.lambda_away
                    dist_rec.phi_lead2_home = dist_out.phi_lead2_home
                    dist_rec.phi_lead2_away = dist_out.phi_lead2_away
                    dist_rec.epistemic_delta = epist_delta
                    dist_rec.audit_trace_json = trace_dict

            exitosos += 1
            logger.info(f"✅ [SOVEREIGN PERSISTED] Distribución guardada en SQLite para {match_id}: ({dist_out.p_local:.4f}, {dist_out.p_empate:.4f}, {dist_out.p_visitante:.4f})")

        except Exception as ex:
            logger.error(f"❌ Error sincronizando distribución para {match_id}: {ex}")
            errores.append({"match_id": match_id, "error": str(ex)})

    return {
        "procesados": procesados,
        "exitosos": exitosos,
        "errores": errores
    }
