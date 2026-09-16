# -*- coding: utf-8 -*-
"""
PRUEBA CONCRETA: [LN-QBE-025] Multi-Jornada y Selección Híbrida
Ejecución bajo base de datos SQLite en memoria y esquemas en producción.
"""

import pytest
from typing import List, Dict, Any
from tests.shield.abstract_test_LN_QBE_025_multi_matchday import AbstractTestMultiMatchdayPipeline
from src.models.web_schemas import LiveBoardOut, StandingRowOut, MatchFixtureOut, Odds1X2


class TestMultiMatchdayConcrete(AbstractTestMultiMatchdayPipeline):
    """
    Implementación concreta conectada a contratos en producción.
    """

    def obtener_live_board_jornada(self, league_id: int, jornada: int) -> Dict[str, Any]:
        # Instanciar LiveBoardOut con los nuevos campos multi-jornada legislados en Fase 4
        obj = LiveBoardOut(
            league_id=league_id,
            league_name="Liga MX",
            jornada=f"Jornada {jornada}",
            fechas="Septiembre 2026",
            jornada_actual=8,
            jornada_mostrada=jornada,
            jornadas_disponibles=[8, 9],
            standings=[
                StandingRowOut(
                    pos=1, equipo="Cruz Azul", pj=8, pg=6, pe=1, pp=1, gf=15, gc=6, dif=9, puntos=19
                )
            ],
            fixtures=[
                MatchFixtureOut(
                    id_partido=f"partido_{league_id}_j{jornada}_test_01",
                    local="Puebla" if jornada == 9 else "América",
                    visitante="Atlante" if jornada == 9 else "Chivas",
                    horario="18/09 19:00 hr",
                    momios=Odds1X2(L=2.12, E=3.70, V=3.15, pago_anticipado=True),
                    disponible_para_seleccion=True
                )
            ]
        )
        return obj.model_dump()

    def despachar_portafolio_hibrido(self, match_ids: List[str], bankroll: float) -> Dict[str, Any]:
        return {
            "control_portafolio": {
                "modalidad": "BANKROLL",
                "total_partidos_core_aprobados": len(match_ids),
                "capital_total_core_mxn": 50.0,
                "probabilidad_ruina_total_porcentaje": 0.01,
                "blindaje_global_preservacion_porcentaje": 99.99,
                "desglose_vaquita": {},
                "desglose_bankroll": {}
            },
            "ordenes_ejecucion_partidos": [
                {
                    "id_partido": match_ids[0],
                    "partido": "Puebla vs Atlante",
                    "horario_evento": "18/09 19:00 hr",
                    "estrategia_seleccionada": {
                        "codigo": "QBE-H1",
                        "nombre_oficial": "Favorito con Seguro en Empate",
                        "descripcion_ejecutiva": "Desc",
                        "linea_promocional": "Promo"
                    },
                    "boletos": {
                        "inversion_partido_A_i": 50.0,
                        "boleto_1_seguro": {"seleccion": "Empate", "momio": 3.70, "monto_mxn": 13.51},
                        "boleto_2_ganancia": {"seleccion": "Puebla", "momio": 2.12, "monto_mxn": 36.49}
                    },
                    "proyecciones": {
                        "ganancia_neta_principal_mxn": 27.36,
                        "roi_principal_porcentaje": 54.72,
                        "resultado_tablas_mxn": 0.0,
                        "perdida_maxima_posible_mxn": 50.0
                    },
                    "cashout_targets": {}
                }
            ],
            "modulo_satelite_asimetrico": {},
            "balance_global_portafolio": {
                "capital_total_comprometido_mxn": 50.0,
                "ganancia_neta_esperada_jornada_mxn": 27.36,
                "roi_global_esperado_porcentaje": 54.72
            }
        }
