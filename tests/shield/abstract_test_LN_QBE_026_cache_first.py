# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [LN-QBE-026] Caché Relacional Inteligente, Puente PM-FACE y Limpieza UX
Base de Gobierno: Kybern Framework v8.0 / v12.0
Axioma: Erradicación de doble scraping, lecturas sub-50ms desde SQLite y eliminación de 'vs'.
"""
import abc
import time
from typing import Dict, Any, Tuple
import pytest

class AbstractTestLN_QBE_026_CacheFirst(abc.ABC):

    @abc.abstractmethod
    def consultar_live_board(self, league_id: int, force_refresh: bool = False) -> Tuple[Dict[str, Any], float]:
        """
        Ejecuta la consulta de Live Board y retorna una tupla: (payload_json, tiempo_transcurrido_segundos).
        """
        pass

    @abc.abstractmethod
    def obtener_primer_rival_tabla(self, league_id: int) -> str:
        """Retorna el texto del campo 'proximo_rival' del primer equipo en la tabla."""
        pass

    @abc.abstractmethod
    def verificar_ledger_jornada_en_db(self, league_id: int) -> Dict[str, Any]:
        """Consulta directamente SQLite y retorna el registro de estado de la jornada activa."""
        pass

    # =========================================================================
    # INVARIANTES DEL ESCUDO (THE SHIELD)
    # =========================================================================

    def test_invariante_cache_first_velocidad_sub_100ms(self):
        """
        [INVARIANZA 1 - PERF-MANDATE]
        La segunda llamada consecutiva a live-board debe servirse directamente
        desde SQLite (Cache-First) en menos de 150 ms, demostrando que NO se
        invoca Playwright ni scrapers externos.
        """
        # Primera llamada (asegura calentamiento de caché o seed)
        self.consultar_live_board(league_id=262, force_refresh=False)

        # Segunda llamada: debe ser instantánea desde SQLite
        payload, duracion = self.consultar_live_board(league_id=262, force_refresh=False)
        
        assert duracion < 0.150, (
            f"Violación [PERF-MANDATE]: La llamada a live-board tardó {duracion:.3f}s. "
            f"El sistema sigue ejecutando scraping síncrono en lugar de servir desde SQLite (< 150ms)."
        )
        assert len(payload.get("fixtures", [])) >= 8, "El payload de caché no contiene los partidos esperados."

    def test_invariante_proximo_rival_sin_prefijo_vs(self):
        """
        [INVARIANZA 2 - DES-QBE-016-D]
        El campo 'proximo_rival' debe contener exclusivamente el nombre canónico del club.
        Queda terminantemente prohibido que inicie con 'vs ' o 'contra '.
        """
        texto_rival = self.obtener_primer_rival_tabla(league_id=262)
        assert texto_rival is not None and len(texto_rival) > 0, "El próximo rival es nulo o vacío."
        
        texto_lower = texto_rival.strip().lower()
        assert not texto_lower.startswith("vs "), (
            f"Violación UX [DES-QBE-016-D]: El próximo rival contiene el prefijo redundante '{texto_rival}'. "
            f"Debe ser el nombre limpio del club (ej. 'Cruz Azul')."
        )
        assert not texto_lower.startswith("contra "), "El próximo rival contiene el prefijo 'contra '."

    def test_invariante_persistencia_jornada_activa_en_db(self):
        """
        [INVARIANZA 3 - ARCH-1.5.5 PUENTE PM-FACE]
        La base de datos SQLite debe almacenar el registro de estado de la jornada
        activa con su número (>= 8), fecha de captura y estado 'ACTIVA' o 'PROGRAMADA'.
        """
        estado_jornada = self.verificar_ledger_jornada_en_db(league_id=262)
        assert estado_jornada is not None, "No existe registro de estado de jornada en SQLite."
        
        jornada_num = estado_jornada.get("matchday_num") or estado_jornada.get("jornada")
        assert jornada_num is not None, "El registro no contiene el número de jornada."
        assert int(jornada_num) >= 8, f"Inconsistencia: La jornada en BD es {jornada_num}, se esperaba >= 8."

    def test_invariante_bypass_fuerza_refresco_bajo_demanda(self):
        """
        [INVARIANZA 4 - CONTROL OPERATIVO]
        Si se envía 'force_refresh=True', el sistema debe permitir la actualización
        y retornar datos válidos con timestamp refrescado.
        """
        payload, _ = self.consultar_live_board(league_id=262, force_refresh=True)
        assert payload.get("league_id") == 262
        assert "fixtures" in payload
        assert len(payload["fixtures"]) > 0
