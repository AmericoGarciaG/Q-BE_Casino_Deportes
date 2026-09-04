# Q-BE Casino Deportes — Sanitizer Engine (src/core/sanitizer.py)
"""
[LN-QBE-010] Motor de Aduana de Sanidad, Integridad y Anclaje a Tabla Maestra.
[ANTI-BUG] [ARCH-PILLAR] Veto determinista ante corrupción de datos, baja confiabilidad,
desanclaje de tabla o fabricación de antecedentes H2H sintéticos.
"""

from typing import Optional
from src.models.raw_input import RawMatchInput, MasterTableSnapshot


class SanitizerEngine:
    @staticmethod
    def audit_and_sanitize(match_input: RawMatchInput, master_table: Optional[MasterTableSnapshot] = None) -> bool:
        """
        Audita el objeto de partido contra las reglas de sanidad e integridad:
        1. Confiabilidad >= 80% y estado de extracción != "CUARENTENA".
        2. Anclaje estricto con la Tabla Maestra (Puntos, Posición, Pts/PJ).
        3. Linaje H2H sin fechas duplicadas ni datos sintéticos.
        """
        # 1. Cuarentena de Fuentes
        if match_input.trazabilidad_consenso:
            conf = match_input.trazabilidad_consenso.confiabilidad_porcentaje
            estado = match_input.trazabilidad_consenso.estado_extraccion
            if conf < 80.0:
                raise ValueError(f"Veto QBE-00: Confiabilidad insuficiente ({conf:.1f}% < 80.0%)")
            if estado and estado.upper() in ["CUARENTENA", "CUARENTENA_DATOS_INSUFICIENTES"]:
                raise ValueError("Veto QBE-00: Estado de extracción marcado en CUARENTENA")

        # 2. Candado de Anclaje a Tabla Maestra
        if master_table and master_table.posiciones and match_input.contexto_tabla_posiciones:
            posiciones = master_table.posiciones
            identidad = match_input.identidad_partido
            contexto = match_input.contexto_tabla_posiciones

            # Verificar Favorito
            if contexto.favorito:
                fav_ctx = contexto.favorito
                fav_nombre = identidad.favorito if identidad else None
                ref = SanitizerEngine._find_position(posiciones, fav_nombre, fav_ctx.posicion_tabla)
                if ref:
                    SanitizerEngine._validate_anchor(fav_ctx, ref, "favorito")

            # Verificar Underdog
            if contexto.underdog:
                und_ctx = contexto.underdog
                und_nombre = identidad.underdog if identidad else None
                ref = SanitizerEngine._find_position(posiciones, und_nombre, und_ctx.posicion_tabla)
                if ref:
                    SanitizerEngine._validate_anchor(und_ctx, ref, "underdog")

        # 3. Candado de Linaje Cronológico H2H (Cero Mocks en Producción)
        h2h_list = match_input.h2h_matches or match_input.h2h_ultimos_5_misma_liga
        if h2h_list and len(h2h_list) == 5:
            fechas = [m.fecha for m in h2h_list if m.fecha]
            if len(fechas) == 5:
                # Prohibición de fechas 100% duplicadas o sintéticas
                if len(set(fechas)) <= 2:
                    raise ValueError("Veto QBE-00: Linaje H2H corrupto (fechas duplicadas o mockeadas detectadas)")

            locales = [m.local_real.strip().lower() for m in h2h_list if m.local_real]
            if len(locales) == 5 and len(set(locales)) == 1:
                # Prohibición de localía estática al 100% en los 5 duelos
                raise ValueError("Veto QBE-00: Linaje H2H corrupto (100% de duelos con la misma localía estática)")

        return True

    @staticmethod
    def _find_position(posiciones, team_name: Optional[str], pos_num: Optional[int]):
        if team_name:
            t_norm = team_name.strip().lower()
            for p in posiciones:
                if p.equipo.strip().lower() == t_norm:
                    return p
        if pos_num is not None:
            for p in posiciones:
                if p.pos == pos_num:
                    return p
        return None

    @staticmethod
    def _validate_anchor(ctx, ref, rol: str):
        if ctx.posicion_tabla is not None and ctx.posicion_tabla != ref.pos:
            raise ValueError(
                f"Veto QBE-00: Discrepancia detectada con la Tabla Maestra para {rol} "
                f"(posicion {ctx.posicion_tabla} vs {ref.pos})"
            )
        if ctx.puntos is not None and ctx.puntos != ref.puntos:
            raise ValueError(
                f"Veto QBE-00: Discrepancia detectada con la Tabla Maestra para {rol} "
                f"(puntos {ctx.puntos} vs {ref.puntos})"
            )
        if ctx.pts_por_partido is not None and abs(ctx.pts_por_partido - ref.pts_por_partido) > 0.05:
            raise ValueError(
                f"Veto QBE-00: Discrepancia detectada con la Tabla Maestra para {rol} "
                f"(pts_por_partido {ctx.pts_por_partido} vs {ref.pts_por_partido})"
            )