# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [FASE 5 CIERRE] Prueba Ácida de Integración E2E y Persistencia en BD
Doctrina: Kybern Framework v12.0 [DIRGEN-SEALED] [GOV-TEST-01 a 07]
Régimen: [DIRGEN-STRICT]
"""

import pytest
from sqlalchemy import text
from src.storage.gateway import PersistenceGateway
from src.storage.models import Base, Competition, Match, SovereignDistribution

# En esta fase (previo a materialización en src/), esta importación DEBE FALLAR (RED STATE)
from src.storage.distribution_sync import sincronizar_distribuciones_soberanas_partidos


def test_integracion_e2e_persistencia_distribucion_real():
    """
    Prueba Ácida de Cierre de Fase 5:
    Inserta un partido 3NF real en SQLite, ejecuta el orquestador soberano,
    persiste en 'sovereign_distributions' y verifica que los datos físicos en disco
    cumplan con las invarianzas matemáticas del Tratado Volumen I.
    """
    gateway = PersistenceGateway()
    gateway.create_all_tables(Base.metadata)

    match_id = "MATCH_TEST_INTEGRATION_01"
    comp_id = "MEX_LIGAMX"

    # 1. Preparación de entorno fáctico en BD
    with gateway.write_transaction() as tx:
        # Asegurar competición
        comp = tx.query(Competition).filter(Competition.id == comp_id).first()
        if not comp:
            comp = Competition(id=comp_id, name="Liga MX", country="México", macro_mu_liga=2.65, macro_gamma_home=0.15)
            tx.add(comp)

        # Crear partido de prueba
        m = tx.query(Match).filter(Match.id == match_id).first()
        if not m:
            m = Match(
                id=match_id, competition_id=comp_id, matchday_num=9,
                home_team_slug="puebla", away_team_slug="atlante",
                status="SCHEDULED"
            )
            tx.add(m)

    # Payload fáctico representativo
    datos_partido = {
        "match_id": match_id,
        "competition_id": comp_id,
        "home_team_stats": {"pj": 8, "gf": 10, "gc": 10, "xg": 1.46, "xga": 1.29},
        "away_team_stats": {"pj": 8, "gf": 7, "gc": 12, "xg": 1.07, "xga": 1.52}
    }

    # 2. Ejecución del servicio de integración
    resultado = sincronizar_distribuciones_soberanas_partidos(
        partidos_datos=[datos_partido],
        gateway=gateway
    )
    assert resultado["procesados"] == 1
    assert resultado["exitosos"] == 1

    # 3. Verificación forense en el disco físico (Lectura limpia desde Gateway)
    with gateway.read_session() as session:
        dist_db = session.query(SovereignDistribution).filter(SovereignDistribution.match_id == match_id).first()
        
        assert dist_db is not None, "Fallo Fiduciario: La distribución no se guardó físicamente en SQLite."
        assert dist_db.model_version == "v13.0-DIRGEN"
        
        # Validar invarianzas en los datos leídos de la BD
        suma_simplex = dist_db.p_local + dist_db.p_empate + dist_db.p_visitante
        assert abs(suma_simplex - 1.0000) <= 0.0001
        
        # Puebla contenido en paridad deportiva
        assert 0.52 <= dist_db.p_local <= 0.60
        assert dist_db.lambda_home <= 2.00
        assert dist_db.lambda_away >= 0.75
        assert dist_db.phi_lead2_home > 0.0

        # Validar que la traza forense JSON esté intacta
        assert dist_db.audit_trace_json is not None
        assert "intensidades" in dist_db.audit_trace_json

    # 4. Limpieza higiénica de prueba
    with gateway.write_transaction() as tx:
        tx.query(SovereignDistribution).filter(SovereignDistribution.match_id == match_id).delete()
        tx.query(Match).filter(Match.id == match_id).delete()
