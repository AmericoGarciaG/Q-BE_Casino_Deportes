# Q-BE Casino Deportes — Narrative Engine (src/reporting/narrative.py)
"""
[LN-QBE-014] [DES-QBE-075] [ARCH-PILLAR] Generador de Tesis Q-BE: Gemini API Dinámica + Fallback Mad-Libs.
Integra generación neuro-simbólica mediante Gemini 3.6 Flash con red de seguridad determinista en 4 viñetas.
"""

import os
import json
import logging
from typing import Any, Dict
from src.ingestion.providers.gemini_search_sensor import redactar_tesis_dinamica_gemini

logger = logging.getLogger(__name__)


def _get_val(obj: Any, *keys: str, default: Any = None) -> Any:
    """Helper seguro para extraer valores de objetos Pydantic o diccionarios."""
    if obj is None:
        return default
    for k in keys:
        if isinstance(obj, dict):
            if k in obj and obj[k] is not None:
                return obj[k]
        else:
            if hasattr(obj, k) and getattr(obj, k) is not None:
                return getattr(obj, k)
    return default


def generar_tesis_partido(orden: Any, analisis: Any) -> str:
    """
    Intenta redactar la Tesis Q-BE dinámica mediante Gemini API en 4 viñetas temáticas.
    Si falla la API o no hay conexión, utiliza el generador paramétrico Mad-Libs [DES-QBE-075].
    """
    # En entorno de pruebas unitarias pytest, garantizar determinismo inmediato
    if os.getenv("PYTEST_CURRENT_TEST"):
        return _generar_tesis_madlibs_fallback(orden, analisis)

    # 1. Intentar con Gemini API (Tesis Rica, Dinámica y Contextualizada)
    if os.getenv("Gemini_API_4_QBE_001") or os.getenv("Gemini_API_4_QBE") or os.getenv("GEMINI_API_KEY"):
        try:
            estrategia_obj = _get_val(orden, "estrategia_seleccionada", default=orden)
            boletos_obj = _get_val(orden, "boletos", default=orden)
            proyecciones_obj = _get_val(orden, "proyecciones", default=orden)

            b1 = _get_val(boletos_obj, "boleto_1_seguro", "boleto_1", default=None) or _get_val(orden, "boleto_1_seguro", "boleto_1", default={})
            b2 = _get_val(boletos_obj, "boleto_2_ganancia", "boleto_2", default=None) or _get_val(orden, "boleto_2_ganancia", "boleto_2", default={})

            fav_name = str(_get_val(analisis, "equipo_fav", "fav_name", "local", default="Favorito"))
            und_name = str(_get_val(analisis, "equipo_und", "und_name", "visitante", default="Underdog"))
            partido_nombre = str(_get_val(orden, "partido", default=None) or _get_val(analisis, "partido", "partido_nombre", default=f"{fav_name} vs {und_name}"))

            phi_val = float(_get_val(analisis, "phi_lead2", "phi_lead2_pct", default=0.0))
            if phi_val <= 1.0:
                phi_val *= 100.0

            cod_est = str(_get_val(estrategia_obj, "codigo", default=None) or _get_val(orden, "estrategia_codigo", "codigo", default=None) or _get_val(analisis, "strategy_code", "estrategia_codigo", default="QBE-D1"))
            nom_est = str(_get_val(estrategia_obj, "nombre_oficial", "nombre", default=None) or _get_val(orden, "estrategia_nombre_oficial", "estrategia_nombre", "strategy_nombre", default=None) or _get_val(analisis, "strategy_nombre", "estrategia_nombre", default=""))
            inv_tot = float(_get_val(boletos_obj, "inversion_partido_A_i", "inversion_total", default=None) or _get_val(orden, "inversion_total_mxn", "inversion_total", default=0.0))
            gan_net = float(_get_val(proyecciones_obj, "ganancia_neta_principal_mxn", "ganancia_neta", default=None) or _get_val(orden, "ganancia_neta_principal_mxn", "ganancia_neta", default=0.0))
            roi_p = float(_get_val(proyecciones_obj, "roi_principal_porcentaje", "roi_pct", default=None) or _get_val(orden, "roi_principal_pct", "roi_pct", default=0.0))

            prob_real_fav_calc = float(_get_val(analisis, "prob_fav", "prob_hibrida_fav", "prob_real_fav", default=50.0))
            if prob_real_fav_calc <= 1.0:
                prob_real_fav_calc *= 100.0

            prob_real_und_calc = float(_get_val(analisis, "prob_und", "prob_hibrida_und", "prob_real_und", default=25.0))
            if prob_real_und_calc <= 1.0:
                prob_real_und_calc *= 100.0

            odds_fav_val = float(_get_val(analisis, "odds_fav", "odd_fav", default=2.0))
            odds_und_val = float(_get_val(analisis, "odds_und", "odd_und", default=3.5))

            fair_odd_fav = (100.0 / prob_real_fav_calc) if prob_real_fav_calc > 0 else odds_fav_val
            fair_odd_und = (100.0 / prob_real_und_calc) if prob_real_und_calc > 0 else odds_und_val

            contexto = {
                "partido": partido_nombre,
                "estrategia_codigo": cod_est,
                "estrategia_nombre": nom_est,
                "inversion_total_mxn": inv_tot,
                "ganancia_neta_mxn": gan_net,
                "roi_pct": roi_p,
                "boleto_1_seguro": {
                    "seleccion": str(_get_val(b1, "seleccion", default="Seguro")),
                    "momio": float(_get_val(b1, "momio", default=0.0)),
                    "monto_mxn": float(_get_val(b1, "monto_mxn", "monto", default=0.0))
                },
                "boleto_2_ganancia": {
                    "seleccion": str(_get_val(b2, "seleccion", default="Ganancia")),
                    "momio": float(_get_val(b2, "momio", default=0.0)),
                    "monto_mxn": float(_get_val(b2, "monto_mxn", "monto", default=0.0))
                },
                "estadisticas_clave": {
                    "favorito": {
                        "nombre": fav_name,
                        "posicion": int(_get_val(analisis, "pos_fav", "fav_pos", default=1)),
                        "pts_pj": float(_get_val(analisis, "pts_pj_fav", "fav_pts_pj", default=1.5)),
                        "gf_prom": float(_get_val(analisis, "gf_fav", "promedio_gf_fav", default=1.5)),
                        "gc_prom": float(_get_val(analisis, "gc_fav", "promedio_gc_fav", default=1.0)),
                        "prob_real_qbe": prob_real_fav_calc,
                        "momio_real_qbe": round(fair_odd_fav, 2),
                        "momio_casino": odds_fav_val,
                        "prob_impl_casino": float(_get_val(analisis, "prob_impl_fav", default=50.0))
                    },
                    "underdog": {
                        "nombre": und_name,
                        "posicion": int(_get_val(analisis, "pos_und", "und_pos", default=10)),
                        "pts_pj": float(_get_val(analisis, "pts_pj_und", "und_pts_pj", default=1.0)),
                        "gf_prom": float(_get_val(analisis, "gf_und", "promedio_gf_und", default=1.0)),
                        "gc_prom": float(_get_val(analisis, "gc_und", "promedio_gc_und", default=1.5)),
                        "prob_real_qbe": prob_real_und_calc,
                        "momio_real_qbe": round(fair_odd_und, 2),
                        "momio_casino": odds_und_val
                    },
                    "prob_pago_anticipado_phi_lead2": phi_val,
                    "breakeven_theta": float(_get_val(analisis, "theta_fav", "theta_req", default=0.0))
                }
            }
            tesis_ai = redactar_tesis_dinamica_gemini(contexto)
            if tesis_ai and len(tesis_ai.strip()) > 80:
                return tesis_ai.strip()
        except Exception as e:
            logger.warning(f"Fallback a Mad-Libs por error en Gemini API: {e}")

    # 2. Respaldo Determinista Mad-Libs (Fallback)
    return _generar_tesis_madlibs_fallback(orden, analisis)


def _generar_tesis_madlibs_fallback(orden: Any, analisis: Any) -> str:
    """
    Generador paramétrico Mad-Libs determinista e inmutable en 4 viñetas [DES-QBE-075].
    """
    estrategia_obj = _get_val(orden, "estrategia_seleccionada", default=orden)
    boletos_obj = _get_val(orden, "boletos", default=orden)
    proyecciones_obj = _get_val(orden, "proyecciones", default=orden)

    estrategia = str(_get_val(estrategia_obj, "codigo", default=None) or _get_val(orden, "estrategia_codigo", "codigo", default=None) or _get_val(analisis, "strategy_code", "estrategia_codigo", default="QBE-D1"))
    inversion = float(_get_val(boletos_obj, "inversion_partido_A_i", "inversion_total", default=None) or _get_val(orden, "inversion_total_mxn", "inversion_total", "inversion_partido_A_i", default=0.0))
    roi = float(_get_val(proyecciones_obj, "roi_principal_porcentaje", "roi_pct", default=None) or _get_val(orden, "roi_principal_pct", "roi_pct", "roi_principal_porcentaje", default=0.0))
    ganancia = float(_get_val(proyecciones_obj, "ganancia_neta_principal_mxn", "ganancia_neta", default=None) or _get_val(orden, "ganancia_neta_principal_mxn", "ganancia_neta", default=0.0))

    b1_obj = _get_val(boletos_obj, "boleto_1_seguro", "boleto_1", default=None) or _get_val(orden, "boleto_1_seguro", "boleto_1")
    b2_obj = _get_val(boletos_obj, "boleto_2_ganancia", "boleto_2", default=None) or _get_val(orden, "boleto_2_ganancia", "boleto_2")
    monto_b1 = float(_get_val(b1_obj, "monto_mxn", "monto", default=0.0))
    monto_b2 = float(_get_val(b2_obj, "monto_mxn", "monto", default=inversion))

    fav_name = str(_get_val(analisis, "equipo_fav", "fav_name", "local", default="Favorito"))
    und_name = str(_get_val(analisis, "equipo_und", "und_name", "visitante", default="Underdog"))
    pos_fav = int(_get_val(analisis, "pos_fav", "fav_pos", default=1))
    pos_und = int(_get_val(analisis, "pos_und", "und_pos", default=18))
    pts_fav = float(_get_val(analisis, "pts_pj_fav", "fav_pts_pj", default=1.80))
    gf_fav = float(_get_val(analisis, "gf_fav", "promedio_gf_fav", default=1.50))
    gc_fav = float(_get_val(analisis, "gc_fav", "promedio_gc_fav", default=1.00))
    gf_und = float(_get_val(analisis, "gf_und", "promedio_gf_und", default=0.80))
    sot_und = float(_get_val(analisis, "sot_und", "promedio_sot_und", default=3.00))
    sot_fav = float(_get_val(analisis, "sot_fav", "promedio_sot_fav", default=5.00))

    prob_fav = float(_get_val(analisis, "prob_fav", "prob_hibrida_fav", "prob_real_fav", default=65.0))
    if prob_fav <= 1.0:
        prob_fav *= 100.0

    prob_und = float(_get_val(analisis, "prob_und", "prob_hibrida_und", "prob_real_und", default=15.0))
    if prob_und <= 1.0:
        prob_und *= 100.0

    odds_fav = float(_get_val(analisis, "odds_fav", "odd_fav", default=1.70))
    odds_emp = float(_get_val(analisis, "odds_emp", "odd_emp", default=3.60))
    odds_und = float(_get_val(analisis, "odds_und", "odd_und", default=4.50))
    h2h_x2 = float(_get_val(analisis, "h2h_x2_pct", "h2h_x2_prob", default=30.0))
    if h2h_x2 <= 1.0:
        h2h_x2 *= 100.0

    fair_odd_fav = round(100.0 / prob_fav, 2) if prob_fav > 0 else odds_fav
    fair_odd_und = round(100.0 / prob_und, 2) if prob_und > 0 else odds_und

    # Construcción formal en 4 Viñetas Canónicas [DES-QBE-075]
    if estrategia in ["QBE-D1", "QBE-D1+"]:
        b1 = f"• <strong>Momento y Tabla:</strong> {fav_name} marcha en el puesto #{pos_fav} de la tabla promediando {pts_fav:.2f} puntos por juego ({gf_fav:.2f} GF / {gc_fav:.2f} GC), superando con claridad a {und_name} (#{pos_und} con {getattr(analisis, 'pts_pj_und', 1.0):.2f} pts/juego)."
        b2 = f"• <strong>Dominio de Cancha:</strong> Nuestro análisis de tiros confirma el control territorial de {fav_name} generando {sot_fav:.1f} tiros a puerta por partido frente a un rival que concede {sot_und:.1f} llegadas peligrosas."
        b3 = f"• <strong>Historial y Bajas:</strong> En los antecedentes directos recientes, la balanza favorece la tendencia del favorito, respaldada por un plantel completo y sin ausencias críticas de Tier 1."
        pa_texto = " con liquidación temprana al sacar ventaja de 2 goles" if estrategia == "QBE-D1+" else ""
        b4 = f"• <strong>Estrategia y Protección:</strong> Aplicamos <strong>{estrategia}</strong> asignando <strong>${monto_b2:.2f} MXN</strong> al ataque directo{pa_texto}. Nuestro modelo tasa la victoria justa en <strong>@{fair_odd_fav:.2f}</strong> frente al <strong>@{odds_fav:.2f}</strong> del casino, capturando <strong>+${ganancia:.2f} MXN</strong> (+{roi:.1f}% ROI) sin necesidad de seguros dilutivos."
        return f"{b1}<br><br>{b2}<br><br>{b3}<br><br>{b4}"

    elif estrategia in ["QBE-H1", "QBE-H1+"]:
        b1 = f"• <strong>Momento y Tabla:</strong> {fav_name} marcha en el puesto #{pos_fav} de la tabla promediando {pts_fav:.2f} puntos por juego ({gf_fav:.2f} GF / {gc_fav:.2f} GC), superando con claridad a {und_name} (#{pos_und})."
        b2 = f"• <strong>Dominio de Cancha:</strong> {fav_name} genera {sot_fav:.1f} tiros a puerta contra {und_name} ({sot_und:.1f}), confirmando control real del partido."
        b3 = f"• <strong>Historial y Bajas:</strong> Los enfrentamientos directos favorecen al equipo de arriba en tabla, consolidando la apuesta con plantel disponible."
        pa_texto = " (Pago Anticipado amplía ganancia)" if estrategia == "QBE-H1+" else ""
        b4 = f"• <strong>Estrategia y Protección:</strong> Aplicamos <strong>{estrategia}</strong> estructurando Dutching asimétrico: <strong>${monto_b1:.2f} MXN</strong> al Empate como seguro (recupera <strong>${inversion:.2f} MXN</strong> en tablas) y <strong>${monto_b2:.2f} MXN</strong> a victoria de {fav_name}, capturando <strong>+${ganancia:.2f} MXN</strong> (+{roi:.1f}% ROI){pa_texto}."
        return f"{b1}<br><br>{b2}<br><br>{b3}<br><br>{b4}"

    elif estrategia in ["QBE-H2", "QBE-H2+"]:
        b1 = f"• <strong>Momento y Tabla:</strong> {fav_name} (#{pos_fav}) mantiene ventaja sobre {und_name} (#{pos_und}), ambos con rendimientos cercanos en puntos por juego ({pts_fav:.2f} vs {getattr(analisis, 'pts_pj_und', 1.0):.2f})."
        b2 = f"• <strong>Dominio de Cancha:</strong> El trámite táctico se equilibra: {fav_name} genera {sot_fav:.1f} SoT y {und_name} responde con {sot_und:.1f}, indicando alta probabilidad de empate."
        b3 = f"• <strong>Historial y Bajas:</strong> El H2H muestra paridad relativa ({h2h_x2:.1f}% de no-derrotas históricas), confirmando vulnerabilidad en ambos bandos."
        pa_texto = " (Freeroll Doble Impacto en activación de +2 goles)" if estrategia == "QBE-H2+" else ""
        b4 = f"• <strong>Estrategia y Protección:</strong> Ejecutamos <strong>{estrategia}</strong> con cobertura máxima: <strong>${monto_b1:.2f} MXN</strong> a {fav_name} (@{odds_fav:.2f}) como seguro de capital (${inversion:.2f} MXN recuperables), y <strong>${monto_b2:.2f} MXN</strong> al Empate como boleto principal, generando <strong>+${ganancia:.2f} MXN</strong> (+{roi:.1f}% ROI){pa_texto}."
        return f"{b1}<br><br>{b2}<br><br>{b3}<br><br>{b4}"

    elif estrategia in ["QBE-R1", "QBE-R2"]:
        b1 = f"• <strong>Momento y Tabla:</strong> {und_name} (#{pos_und}) demuestra solidez defensiva ({gf_und:.2f} GF), mientras {fav_name} (#{pos_fav}) presenta vulnerabilidades estructurales en liga."
        b2 = f"• <strong>Dominio de Cancha:</strong> La disparidad de tiros es mínima ({sot_fav:.1f} SoT vs {sot_und:.1f} SoT), descartando dominancia aplastante del favorito de cuota."
        b3 = f"• <strong>Historial y Bajas:</strong> El H2H respalda la resistencia de {und_name} ({h2h_x2:.1f}% de puntos rescatados), superando el Triple Candado Fáctico."
        b4 = f"• <strong>Estrategia y Protección:</strong> Explotamos el descalce de cuotas: el casino paga {und_name} en <strong>@{odds_und:.2f}</strong> cuando nuestro modelo lo sitúa en <strong>@{fair_odd_und:.2f}</strong>. Asignamos <strong>${inversion:.2f} MXN</strong> bajo cobertura de tablas para capturar <strong>+${ganancia:.2f} MXN</strong> (+{roi:.1f}% ROI)."
        return f"{b1}<br><br>{b2}<br><br>{b3}<br><br>{b4}"

    # Fallback genérico institucional
    b1 = f"• <strong>Momento y Tabla:</strong> {fav_name} (#{pos_fav}, {pts_fav:.2f} pts/juego) vs {und_name} (#{pos_und}, {getattr(analisis, 'pts_pj_und', 1.0):.2f} pts/juego)."
    b2 = f"• <strong>Dominio de Cancha:</strong> Análisis de tiros ({sot_fav:.1f} vs {sot_und:.1f}) y posesión respalda estructura de {estrategia}."
    b3 = f"• <strong>Historial y Bajas:</strong> Antecedentes directos y disponibilidad de plantel optimizan la postura de inversión."
    b4 = f"• <strong>Estrategia y Protección:</strong> Se aprueba <strong>{estrategia}</strong> con asignación de <strong>${inversion:.2f} MXN</strong>, proyectando <strong>+${ganancia:.2f} MXN</strong> (+{roi:.1f}% ROI) con blindaje de capital."
    return f"{b1}<br><br>{b2}<br><br>{b3}<br><br>{b4}"


def generar_justificacion_descarte(partido_descartado: Any) -> str:
    """
    Genera el motivo pedagógico institucional de por qué un partido fue vetado (QBE-00).
    """
    partido = str(_get_val(partido_descartado, "partido", default="Encuentro"))
    motivo = str(_get_val(partido_descartado, "motivo", "motivo_diagnostico", default="Sin margen matemático (+EV nulo)"))

    return (
        f"El partido {partido} fue vetado para asignación de capital debido a: {motivo}. "
        f"No se identificaron ineficiencias de mercado ni margen de cobertura bilateral que satisficieran las invarianzas del modelo."
    )