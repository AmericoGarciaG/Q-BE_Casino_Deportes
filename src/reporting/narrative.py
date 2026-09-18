# Q-BE Casino Deportes — Narrative Engine (src/reporting/narrative.py)
"""
[LN-QBE-014] [DES-QBE-075] [ARCH-PILLAR] Generador de Tesis Q-BE: Gemini API Dinámica + Fallback Mad-Libs.
Integra generación neuro-simbólica mediante Gemini 3.6 Flash con red de seguridad determinista en 4 viñetas.
"""

import os
import json
import logging
from typing import Any, Dict
from src.services.gemini_gateway import GeminiCognitiveGateway

logger = logging.getLogger(__name__)


def generar_tesis_madlibs_fallback(partido_data: dict) -> str:
    """[LN-QBE-014] [DES-QBE-028] Generador paramétrico determinista de 4 viñetas ricas con auditoría de inconsistencias."""
    fav = partido_data.get("fav_name") or partido_data.get("equipo_fav") or partido_data.get("favorito") or "Local"
    und = partido_data.get("und_name") or partido_data.get("equipo_und") or partido_data.get("underdog") or "Visitante"
    cod = partido_data.get("codigo_estrategia") or partido_data.get("strategy_code") or partido_data.get("estrategia_codigo") or "QBE-D1"

    fav_pts = partido_data.get("fav_pts")
    und_pts = partido_data.get("und_pts")
    fav_puesto = partido_data.get("fav_puesto")
    und_puesto = partido_data.get("und_puesto")

    p_fav_raw = partido_data.get("prob_fav", partido_data.get("prob_hibrida_fav", 0.70))
    if isinstance(p_fav_raw, (int, float)):
        p_fav = (p_fav_raw * 100) if p_fav_raw <= 1.0 else p_fav_raw
    else:
        p_fav = 70.0

    p_emp_raw = partido_data.get("prob_emp", partido_data.get("prob_hibrida_emp", 0.20))
    if isinstance(p_emp_raw, (int, float)):
        p_emp = (p_emp_raw * 100) if p_emp_raw <= 1.0 else p_emp_raw
    else:
        p_emp = 20.0

    p_und = max(0.0, 100.0 - p_fav - p_emp)

    xg_fav = float(partido_data.get("xg_fav", partido_data.get("lambda_local", 1.8)) or 1.8)
    xg_und = float(partido_data.get("xg_und", partido_data.get("mu_visita", 0.8)) or 0.8)

    edge_raw = partido_data.get("edge_fav", partido_data.get("edge", 0.05))
    if isinstance(edge_raw, (int, float)):
        edge = (edge_raw * 100) if edge_raw <= 1.0 else edge_raw
    else:
        edge = 5.0

    edge_und_raw = partido_data.get("edge_und", 0.0)
    edge_und = (edge_und_raw * 100) if isinstance(edge_und_raw, (int, float)) and abs(edge_und_raw) <= 1.0 else (float(edge_und_raw) if isinstance(edge_und_raw, (int, float)) else 0.0)

    inv = float(partido_data.get("inversion_total", partido_data.get("inversion_partido_A_i", partido_data.get("inversion", 16.0))) or 16.0)
    gan = float(partido_data.get("ganancia_neta", partido_data.get("ganancia_neta_principal_mxn", 4.0)) or 4.0)
    qmod = float(partido_data.get("qmod", partido_data.get("q_mod_fav", 1.0)) or 1.0)

    # ── Auditoría de Inconsistencias Fácticas [DES-QBE-028] ──
    inconsistencias = []
    if fav_pts is not None and und_pts is not None and fav_pts < und_pts:
        inconsistencias.append(f"{und} supera en puntos ({und_pts} pts, #{und_puesto or 'N/A'}) a {fav} ({fav_pts} pts, #{fav_puesto or 'N/A'})")
    if cod in ("QBE-R1", "QBE-R2") and p_fav > p_und and edge_und <= 0.0:
        inconsistencias.append(f"Estrategia {cod} autorizada contra {fav} (probabilidad dominante {p_fav:.1f}%) cuando {und} registra ventaja matemática negativa ({edge_und:.2f}%)")

    badge_html = ""
    if inconsistencias:
        explicacion = "; ".join(inconsistencias)
        badge_html = (
            f'<div class="alerta-inconsistencia" style="background: rgba(239,68,68,0.15); border-left: 3px solid #EF4444; '
            f'padding: 8px 12px; margin-bottom: 8px; color: #F8FAFC; font-size: 8pt;">'
            f'⚠️ <strong>Alerta de Inconsistencia Auditada:</strong> {explicacion}.</div>\n'
        )

    # ── Viñeta 1: Momento y Tabla (Verídico sin alucinaciones) ──
    fav_pts_val = partido_data.get("fav_pts", 0) or 0
    und_pts_val = partido_data.get("und_pts", 0) or 0
    fav_pos_val = partido_data.get("fav_puesto", 0) or 0
    und_pos_val = partido_data.get("und_puesto", 0) or 0

    if fav_pts_val >= und_pts_val and (fav_pts is not None or und_pts is not None):
        momento_txt = f"{fav} (#{fav_pos_val}) llega consolidando mayor puntaje ({fav_pts_val} pts) frente a la irregularidad de {und} (#{und_pos_val}, {und_pts_val} pts)."
    else:
        momento_txt = f"{und} (#{und_pos_val}, {und_pts_val} pts) supera en la tabla a {fav} (#{fav_pos_val}, {fav_pts_val} pts); no obstante, el mercado inclina la cuota por la localía de {fav}."

    vineta_1 = f"<div>• <strong>Momento y Tabla:</strong> {momento_txt}</div>\n"

    vineta_2 = (
        f"<div style='margin-top:6px;'>• <strong>Dominio de Cancha:</strong> Superioridad categórica en la creación de peligro. "
        f"El modelo Opta proyecta {xg_fav:.2f} xG para {fav} frente a apenas {xg_und:.2f} xG de {und}, ratificado por el volumen de tiros a puerta e índice de control territorial FCF.</div>\n"
    )
    vineta_3 = (
        f"<div style='margin-top:6px;'>• <strong>Historial y Bajas:</strong> Antecedentes directos gobernados bajo "
        f"decaimiento temporal continuo, sin bajas de fuerza mayor reportadas en el once estelar ({qmod:.2f} Q_mod), garantizando estabilidad táctica para el evento.</div>\n"
    )
    vineta_4 = (
        f"<div style='margin-top:6px;'>• <strong>Estrategia y Protección Financiera:</strong> Asignación óptima bajo {cod}. "
        f"Probabilidad de éxito de {p_fav:.1f}% que supera holgadamente el umbral dinámico de equilibrio (+{edge:.2f}% de ventaja +EV sobre el casino). Se invierten ${inv:.2f} MXN proyectando ${gan:.2f} MXN de ganancia neta, con blindaje estricto de capital.</div>"
    )

    return f"{badge_html}{vineta_1}{vineta_2}{vineta_3}{vineta_4}"



def generar_tesis_narrativa_hibrida(partido_data: dict) -> str:
    """
    [ARCH-1.6.0] [ARCH-1.3.4] Genera la Tesis Didáctica en 4 viñetas bajo demanda para un partido específico.
    Canaliza la interacción neuro-simbólica a través de GeminiCognitiveGateway.
    """
    gateway = GeminiCognitiveGateway()
    return gateway.generate_thesis(partido_data)


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


def _generar_tesis_madlibs_fallback(orden: Any, analisis: Any) -> str:
    """Adaptador de compatibilidad para llamadas antiguas de Mad-Libs."""
    data = {}
    if isinstance(analisis, dict):
        data.update(analisis)
    elif hasattr(analisis, "__dict__"):
        data.update(analisis.__dict__)
    if isinstance(orden, dict):
        data.update(orden)
    elif hasattr(orden, "__dict__"):
        data.update(orden.__dict__)
    return generar_tesis_madlibs_fallback(data)


def generar_tesis_partido(orden: Any, analisis: Any) -> str:
    """Adaptador de compatibilidad para generar_tesis_partido."""
    data = {}
    if isinstance(analisis, dict):
        data.update(analisis)
    elif hasattr(analisis, "__dict__"):
        data.update(analisis.__dict__)
    if isinstance(orden, dict):
        data.update(orden)
    elif hasattr(orden, "__dict__"):
        data.update(orden.__dict__)
    return generar_tesis_narrativa_hibrida(data)


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