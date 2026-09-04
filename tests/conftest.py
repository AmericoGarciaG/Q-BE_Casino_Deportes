"""
Fixtures globales inmutables para The Shield (Kybern Framework v12.0).
Provee datos canónicos de prueba anclados a la Liga MX y Leagues Cup.
"""

import pytest
from src.models.raw_input import (
    RawMatchInput, MasterTableSnapshot, MasterTablePosition,
    IdentidadPartido, ContextoTablaPosiciones, ContextoEquipoTabla,
    MetricasResumenDatos, Promedios10P, RadarCualitativoEntorno, RadarEquipo,
    MomiosSnapshot, CuotasPagoAnticipado, H2HMatchRaw
)


@pytest.fixture
def sample_master_table() -> MasterTableSnapshot:
    """Tabla Maestra congelada oficial de 18 clubes (Jornada 7)."""
    return MasterTableSnapshot(
        jornada_concluida=7,
        torneo="Liga MX - Apertura 2026",
        posiciones=[
            MasterTablePosition(pos=1, equipo="Cruz Azul", puntos=19, pj=8, gf=16, gc=6, dif=10, pts_por_partido=2.38, xg=15.4, xga=6.2),
            MasterTablePosition(pos=2, equipo="Deportivo Toluca", puntos=17, pj=8, gf=15, gc=7, dif=8, pts_por_partido=2.13, xg=14.8, xga=7.1),
            MasterTablePosition(pos=3, equipo="Tigres UANL", puntos=17, pj=8, gf=12, gc=4, dif=8, pts_por_partido=2.13, xg=13.2, xga=4.8),
            MasterTablePosition(pos=4, equipo="Rayados de Monterrey", puntos=16, pj=8, gf=14, gc=10, dif=4, pts_por_partido=2.00, xg=13.9, xga=9.8),
            MasterTablePosition(pos=5, equipo="Club América", puntos=14, pj=8, gf=13, gc=8, dif=5, pts_por_partido=1.75, xg=12.5, xga=8.2),
            MasterTablePosition(pos=6, equipo="Pumas UNAM", puntos=13, pj=8, gf=11, gc=9, dif=2, pts_por_partido=1.63, xg=11.2, xga=9.5),
            MasterTablePosition(pos=7, equipo="Club Pachuca", puntos=13, pj=8, gf=14, gc=12, dif=2, pts_por_partido=1.63, xg=13.1, xga=11.8),
            MasterTablePosition(pos=8, equipo="Chivas Guadalajara", puntos=12, pj=8, gf=10, gc=8, dif=2, pts_por_partido=1.50, xg=10.8, xga=8.1),
            MasterTablePosition(pos=9, equipo="Atlético San Luis", puntos=11, pj=8, gf=9, gc=10, dif=-1, pts_por_partido=1.38, xg=9.4, xga=10.2),
            MasterTablePosition(pos=10, equipo="Club Tijuana", puntos=11, pj=8, gf=10, gc=12, dif=-2, pts_por_partido=1.38, xg=9.8, xga=11.5),
            MasterTablePosition(pos=11, equipo="Atlas FC", puntos=10, pj=8, gf=8, gc=9, dif=-1, pts_por_partido=1.25, xg=8.5, xga=9.2),
            MasterTablePosition(pos=12, equipo="Necaxa", puntos=9, pj=8, gf=9, gc=11, dif=-2, pts_por_partido=1.13, xg=8.9, xga=10.8),
            MasterTablePosition(pos=13, equipo="Club Puebla", puntos=8, pj=8, gf=8, gc=13, dif=-5, pts_por_partido=1.00, xg=7.5, xga=12.8),
            MasterTablePosition(pos=14, equipo="Club León", puntos=8, pj=8, gf=7, gc=12, dif=-5, pts_por_partido=1.00, xg=7.2, xga=11.9),
            MasterTablePosition(pos=15, equipo="Querétaro FC", puntos=7, pj=8, gf=6, gc=13, dif=-7, pts_por_partido=0.88, xg=6.8, xga=13.1),
            MasterTablePosition(pos=16, equipo="Mazatlán FC", puntos=6, pj=8, gf=5, gc=11, dif=-6, pts_por_partido=0.75, xg=6.1, xga=11.2),
            MasterTablePosition(pos=17, equipo="Santos Laguna", puntos=5, pj=8, gf=6, gc=14, dif=-8, pts_por_partido=0.63, xg=6.4, xga=13.8),
            MasterTablePosition(pos=18, equipo="FC Juárez", puntos=4, pj=8, gf=5, gc=15, dif=-10, pts_por_partido=0.50, xg=5.2, xga=14.5),
        ]
    )


@pytest.fixture
def sample_match_input() -> RawMatchInput:
    """Partido canónico de prueba (FC Juárez vs Club Pachuca)."""
    return RawMatchInput(
        identidad_partido=IdentidadPartido(
            id_partido="OCR-02",
            local="FC Juárez",
            visitante="Club Pachuca",
            favorito="Club Pachuca",
            underdog="FC Juárez",
            fecha_partido_evaluado="05-09-2026",
            liga_torneo="Liga MX - Apertura 2026",
            jornada_en_disputa=7
        ),
        momios=MomiosSnapshot(
            pago_anticipado=CuotasPagoAnticipado(L=3.65, E=3.50, V=1.99, disponible=True)
        ),
        contexto_tabla_posiciones=ContextoTablaPosiciones(
            jornada_actual_torneo=7,
            favorito=ContextoEquipoTabla(posicion_tabla=7, puntos=13, gf_torneo=14, gc_torneo=12, pj_torneo=8, pts_por_partido=1.63),
            underdog=ContextoEquipoTabla(posicion_tabla=18, puntos=4, gf_torneo=5, gc_torneo=15, pj_torneo=8, pts_por_partido=0.50)
        ),
        metricas_resumen_datos=MetricasResumenDatos(
            fav_10p=Promedios10P(promedio_poss=55.0, promedio_sot=5.0, promedio_sota=3.5, promedio_gf=1.6, promedio_gc=1.0, xg_promedio=1.65, xga_promedio=1.10),
            und_10p=Promedios10P(promedio_poss=45.0, promedio_sot=3.5, promedio_sota=5.0, promedio_gf=1.0, promedio_gc=1.5, xg_promedio=0.95, xga_promedio=1.60)
        ),
        radar_cualitativo_entorno=RadarCualitativoEntorno(
            favorito=RadarEquipo(q_mod_calculado=0.98, descripcion_impacto_bajas="Sin reporte crítico"),
            underdog=RadarEquipo(q_mod_calculado=0.94, descripcion_impacto_bajas="Sin reporte crítico")
        ),
        h2h_matches=[
            H2HMatchRaw(num=1, fecha="02-03-2026", dias_transcurridos=186.0, local_real="Club Pachuca", visitante_real="FC Juárez", marcador="3-2", resultado_qbe="1"),
            H2HMatchRaw(num=2, fecha="21-09-2025", dias_transcurridos=348.0, local_real="FC Juárez", visitante_real="Club Pachuca", marcador="1-1", resultado_qbe="X"),
            H2HMatchRaw(num=3, fecha="09-03-2025", dias_transcurridos=544.0, local_real="Club Pachuca", visitante_real="FC Juárez", marcador="2-1", resultado_qbe="1"),
            H2HMatchRaw(num=4, fecha="02-11-2024", dias_transcurridos=671.0, local_real="FC Juárez", visitante_real="Club Pachuca", marcador="0-1", resultado_qbe="2"),
            H2HMatchRaw(num=5, fecha="02-03-2024", dias_transcurridos=916.0, local_real="Club Pachuca", visitante_real="FC Juárez", marcador="3-2", resultado_qbe="1"),
        ]
    )
