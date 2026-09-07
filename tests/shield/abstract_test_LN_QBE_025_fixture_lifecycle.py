# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [LN-QBE-025] Ciclo de Vida del Fixture, Estatus Semántico y UX de Selección
Base de Gobierno: Kybern Framework v8.0 / v12.0
Axioma: Erradicación de fechas hardcodeadas, partidos finalizados como apuestas y clics rígidos.
Referencia Legislativa: [ARCH-1.6.3] [DES-QBE-016-C] [GOVERNANCE-01]
"""
import abc
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pytest


class AbstractTestLN_QBE_025_FixtureLifecycle(abc.ABC):

    @abc.abstractmethod
    def obtener_fixtures_live_board(self, league_id: int) -> List[Dict[str, Any]]:
        """Retorna la lista de fixtures estructurados tal como los entrega el endpoint /api/leagues/{id}/live-board."""
        pass

    @abc.abstractmethod
    def evaluar_es_hoy(self, fecha_partido_str: str) -> bool:
        """Evalúa dinámicamente si la fecha del partido corresponde al día de hoy."""
        pass

    # =========================================================================
    # INVARIANTES DEL ESCUDO (THE SHIELD)
    # =========================================================================

    def test_invariante_dinamismo_estricto_etiqueta_hoy(self):
        """
        [INVARIANZA 1 - ANTI-BUG]
        La bandera 'es_hoy' debe ser VERDADERA única y exclusivamente si la fecha
        del evento coincide con la fecha de ejecución del sistema.
        Prohibido hardcodear 'HOY' en fechas pasadas o futuras.
        """
        hoy_real = datetime.now().strftime("%Y-%m-%d")
        ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        assert self.evaluar_es_hoy(f"{hoy_real}T20:00:00") is True, \
            "Falló: La fecha de hoy debe marcar es_hoy = True"
        assert self.evaluar_es_hoy(f"{ayer}T20:00:00") is False, \
            "Violación: Una fecha de ayer se marcó falsamente como HOY"
        assert self.evaluar_es_hoy(f"{manana}T20:00:00") is False, \
            "Violación: Una fecha de mañana se marcó falsamente como HOY"

    def test_invariante_partidos_finalizados_al_fondo(self):
        """
        [INVARIANZA 2 - BIZ-LOGIC]
        En la lista de fixtures devuelta para la jornada activa, ningún partido
        en estado 'FINALIZADO' puede aparecer antes de un partido 'PROGRAMADO' o 'EN_CURSO'.
        Todos los concluidos deben residir al fondo de la colección.
        """
        fixtures = self.obtener_fixtures_live_board(league_id=262)
        assert len(fixtures) > 0, "No se recibieron fixtures de la jornada."

        indices_programados = [i for i, f in enumerate(fixtures) if f.get("estado") in ["PROGRAMADO", "EN_CURSO"]]
        indices_finalizados = [i for i, f in enumerate(fixtures) if f.get("estado") == "FINALIZADO"]

        if indices_finalizados and indices_programados:
            primer_finalizado = min(indices_finalizados)
            ultimo_programado = max(indices_programados)
            assert primer_finalizado > ultimo_programado, (
                f"Violación Topológica: Existe un partido FINALIZADO en el índice {primer_finalizado} "
                f"que aparece antes de un partido PROGRAMADO/EN CURSO en el índice {ultimo_programado}."
            )

    def test_invariante_partidos_finalizados_contienen_marcador(self):
        """
        [INVARIANZA 3 - ARCH-PILLAR]
        Todo fixture marcado como 'FINALIZADO' debe tener obligatoriamente su 'marcador_actual'
        definido (ej. '0 - 2', '1 - 1') y no ser nulo ni vacío.
        """
        fixtures = self.obtener_fixtures_live_board(league_id=262)
        finalizados = [f for f in fixtures if f.get("estado") == "FINALIZADO"]

        for f in finalizados:
            marcador = f.get("marcador_actual")
            partido = f"{f.get('local')} vs {f.get('visitante')}"
            assert marcador is not None and len(marcador.strip()) > 0, (
                f"Inconsistencia Fáctica: El partido finalizado '{partido}' no contiene marcador oficial."
            )
            assert "-" in marcador, f"Formato inválido de marcador en '{partido}': {marcador}"

    def test_invariante_bloqueo_seleccion_partidos_no_operables(self):
        """
        [INVARIANZA 4 - BIZ-LOGIC]
        Los partidos 'FINALIZADO' o 'REPROGRAMADO' deben tener su bandera 'disponible_para_seleccion'
        en False, impidiendo que el usuario o el motor asignen capital a eventos ya ocurridos.
        """
        fixtures = self.obtener_fixtures_live_board(league_id=262)
        for f in fixtures:
            estado = f.get("estado")
            disponible = f.get("disponible_para_seleccion", True)
            partido = f"{f.get('local')} vs {f.get('visitante')}"

            if estado in ["FINALIZADO", "REPROGRAMADO"]:
                assert disponible is False, (
                    f"Riesgo Financiero: El partido '{partido}' con estado '{estado}' "
                    f"permite ser seleccionado para cálculo de portafolio."
                )

    def test_invariante_anti_partidos_pasados_disfrazados(self):
        """
        [INVARIANZA 5 - GOVERNANCE-01]
        Ningún partido con horario de inicio anterior a la hora actual por más de 150 minutos
        puede mantener el estado 'PROGRAMADO'. Debe ser 'FINALIZADO' o 'EN_CURSO'.
        """
        fixtures = self.obtener_fixtures_live_board(league_id=262)
        ahora = datetime.now()

        for f in fixtures:
            fecha_iso = f.get("fecha_dt")
            if fecha_iso:
                try:
                    dt_partido = datetime.fromisoformat(fecha_iso)
                    diferencia_horas = (ahora - dt_partido).total_seconds() / 3600.0

                    if diferencia_horas > 2.5:  # Partido inició hace más de 2.5 horas
                        estado = f.get("estado")
                        partido = f"{f.get('local')} vs {f.get('visitante')}"
                        assert estado in ["FINALIZADO", "EN_CURSO"], (
                            f"Violación [GOVERNANCE-01]: El partido '{partido}' se jugó en {fecha_iso} "
                            f"({diferencia_horas:.1f} hrs atrás) pero sigue catalogado como '{estado}'."
                        )
                except ValueError:
                    pass
