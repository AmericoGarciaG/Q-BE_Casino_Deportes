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
    """[LN-QBE-014] [DES-QBE-028] Generador paramétrico determinista de 4 viñetas ricas.

    [GOVERNANCE-01 · Enmienda Nudo 1] La degradación narrativa se declara con el sello
    Mad-Libs y JAMÁS inventa magnitudes: toda cifra ausente del payload se publica como
    `--` o `[Dato no disponible]`.
    """
    fav = partido_data.get("fav_name") or partido_data.get("equipo_fav") or partido_data.get("favorito") or "Local"
    und = partido_data.get("und_name") or partido_data.get("equipo_und") or partido_data.get("underdog") or "Visitante"
    cod = partido_data.get("codigo_estrategia") or partido_data.get("strategy_code") or partido_data.get("estrategia_codigo") or "QBE-D1"

    fav_pts = partido_data.get("fav_pts")
    und_pts = partido_data.get("und_pts")
    fav_puesto = partido_data.get("fav_puesto")
    und_puesto = partido_data.get("und_puesto")

    def _numero(valor):
        """Número fáctico del payload o `None`. Cero invención de magnitudes."""
        if isinstance(valor, bool) or valor is None:
            return None
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            return None
        return numero if numero == numero else None

    def _a_pct(valor):
        """Probabilidad normalizada a porcentaje (0–100) o `None`."""
        numero = _numero(valor)
        if numero is None:
            return None
        return numero * 100.0 if numero <= 1.0 else numero

    def _pct(valor):
        numero = _a_pct(valor)
        return f"{numero:.1f}%" if numero is not None else "--"

    def _dec(valor):
        numero = _numero(valor)
        return f"{numero:.2f}" if numero is not None else "[Dato no disponible]"

    def _monto(valor):
        numero = _numero(valor)
        return f"${numero:.2f} MXN" if numero is not None else "[Monto no disponible]"

    def _pos(valor):
        numero = _numero(valor)
        return f"#{int(numero)}" if numero is not None else "#--"

    def _pts(valor):
        numero = _numero(valor)
        return f"{int(numero)} pts" if numero is not None else "puntos no disponibles"

    p_fav = _numero(partido_data.get("prob_fav", partido_data.get("prob_hibrida_fav")))
    p_emp = _numero(partido_data.get("prob_emp", partido_data.get("prob_hibrida_emp")))
    p_und = _numero(partido_data.get("prob_und", partido_data.get("prob_hibrida_und")))

    xg_fav = _numero(partido_data.get("xg_fav", partido_data.get("lambda_local")))
    xg_und = _numero(partido_data.get("xg_und", partido_data.get("mu_visita")))
    edge = _numero(partido_data.get("edge_fav", partido_data.get("edge")))
    edge_und = _numero(partido_data.get("edge_und"))
    inv = _numero(partido_data.get("inversion_total", partido_data.get("inversion_partido_A_i", partido_data.get("inversion"))))
    gan = _numero(partido_data.get("ganancia_neta", partido_data.get("ganancia_neta_principal_mxn")))
    qmod = _numero(partido_data.get("qmod", partido_data.get("q_mod_fav")))

    # ── Sello de degradación determinista [GOVERNANCE-01 · Enmienda Nudo 1] ──
    sello_madlibs = '<div class="badge-fallback">Narrativa Determinista (Fallback)</div>\n'

    # ── Auditoría de Inconsistencias Fácticas [DES-QBE-028] ──
    inconsistencias = []
    pts_fav = _numero(fav_pts)
    pts_und = _numero(und_pts)
    if pts_fav is not None and pts_und is not None and pts_fav < pts_und:
        inconsistencias.append(
            f"{und} supera en puntos ({_pts(und_pts)}, {_pos(und_puesto)}) a "
            f"{fav} ({_pts(fav_pts)}, {_pos(fav_puesto)})"
        )
    p_fav_pct, p_und_pct = _a_pct(p_fav), _a_pct(p_und)
    edge_und_pct = _a_pct(edge_und)
    if (
        cod in ("QBE-R1", "QBE-R2")
        and p_fav_pct is not None and p_und_pct is not None and edge_und_pct is not None
        and p_fav_pct > p_und_pct and edge_und_pct <= 0.0
    ):
        inconsistencias.append(
            f"Estrategia {cod} autorizada contra {fav} (probabilidad dominante "
            f"{p_fav_pct:.1f}%) cuando {und} registra ventaja matemática negativa "
            f"({edge_und_pct:.2f}%)"
        )

    badge_html = ""
    if inconsistencias:
        explicacion = "; ".join(inconsistencias)
        badge_html = (
            f'<div class="alerta-inconsistencia" style="background: rgba(239,68,68,0.15); border-left: 3px solid #EF4444; '
            f'padding: 8px 12px; margin-bottom: 8px; color: #F8FAFC; font-size: 8pt;">'
            f'⚠️ <strong>Alerta de Inconsistencia Auditada:</strong> {explicacion}.</div>\n'
        )

    # ── Viñeta 1: Momento y Tabla (verídica: jamás inventa puntos ni puestos) ──
    if pts_fav is not None and pts_und is not None and pts_fav >= pts_und:
        momento_txt = (
            f"{fav} ({_pos(fav_puesto)}) llega consolidando mayor puntaje ({_pts(fav_pts)}) "
            f"frente a la irregularidad de {und} ({_pos(und_puesto)}, {_pts(und_pts)})."
        )
    elif pts_fav is not None and pts_und is not None:
        momento_txt = (
            f"{und} ({_pos(und_puesto)}, {_pts(und_pts)}) supera en la tabla a "
            f"{fav} ({_pos(fav_puesto)}, {_pts(fav_pts)}); no obstante, el mercado inclina "
            f"la cuota por la localía de {fav}."
        )
    else:
        momento_txt = (
            f"Lectura de tabla no disponible en el payload para {fav} vs {und}: "
            "esta narrativa determinista se ciñe a la evidencia fáctica disponible."
        )

    vineta_1 = f"<div>• <strong>Momento y Tabla:</strong> {momento_txt}</div>\n"

    vineta_2 = (
        f"<div style='margin-top:6px;'>• <strong>Dominio de Cancha:</strong> Peligro proyectado "
        f"con los insumos disponibles: {_dec(xg_fav)} xG para {fav} frente a {_dec(xg_und)} xG de {und}, "
        f"ratificado —cuando exista— por el volumen de tiros a puerta e índice de control territorial FCF.</div>\n"
    )
    vineta_3 = (
        f"<div style='margin-top:6px;'>• <strong>Historial y Bajas:</strong> Antecedentes directos "
        f"gobernados bajo decaimiento temporal continuo. Factor contextual Q_mod: {_dec(qmod)}. "
        f"El reporte médico no consta en el payload y esta narrativa determinista no lo presume.</div>\n"
    )
    edge_txt = f"+{_dec(edge)}%" if edge is not None else "[Dato no disponible]"
    vineta_4 = (
        f"<div style='margin-top:6px;'>• <strong>Estrategia y Protección Financiera:</strong> Asignación bajo {cod}. "
        f"Probabilidad de éxito: {_pct(p_fav)}; ventaja (+EV) sobre el casino: {edge_txt}. "
        f"Inversión: {_monto(inv)}; ganancia neta proyectada: {_monto(gan)}.</div>"
    )

    return f"{sello_madlibs}{badge_html}{vineta_1}{vineta_2}{vineta_3}{vineta_4}"



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