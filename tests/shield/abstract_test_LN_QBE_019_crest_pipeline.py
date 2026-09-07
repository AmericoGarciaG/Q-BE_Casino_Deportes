# -*- coding: utf-8 -*-
"""
JUEZ INMUTABLE: [LN-QBE-019] Pipeline de Resolución de Escudos y Bóveda Soberana
Base de Gobierno: Kybern Framework v8.0 / v12.0
Axioma: Cero hotlinks rotos por HTTP 403 y resolución determinista de activos visuales.
"""
import abc
import os
import re
from typing import Dict, Any, List
import pytest

class AbstractTestLN_QBE_019_CrestPipeline(abc.ABC):

    @abc.abstractmethod
    def resolver_escudo(self, equipo_nombre: str, fotmob_id: int = None) -> str:
        """Invoca la función o servicio del nodo LN-QBE-019."""
        pass

    @abc.abstractmethod
    def obtener_live_board_standings(self, league_id: int) -> List[Dict[str, Any]]:
        """Simula o ejecuta la llamada que nutre StandingRowOut en el Live Board."""
        pass

    # =========================================================================
    # INVARIANTES DEL ESCUDO (THE SHIELD)
    # =========================================================================

    def test_invariante_anti_hotlinking_externo(self):
        """
        [INVARIANZA 1 - ANTI-BUG]
        Ningún escudo devuelto puede pertenecer a dominios externos vulnerables
        a bloqueos por CORS o Anti-Hotlinking (ej. images.fotmob.com).
        """
        equipos_prueba = ["América", "Guadalajara", "Cruz Azul", "Tigres UANL", "Pumas UNAM"]
        for equipo in equipos_prueba:
            url_resuelta = self.resolver_escudo(equipo)
            assert not url_resuelta.startswith("https://images.fotmob.com"), (
                f"Violación [ANTI-BUG]: El club '{equipo}' devuelve una URL de FotMob externa "
                f"({url_resuelta}), susceptible de bloqueo HTTP 403 por Anti-Hotlinking."
            )
            assert not url_resuelta.startswith("http://") or url_resuelta.startswith("http://localhost"), (
                f"Violación: URL insegura o externa no autorizada: {url_resuelta}"
            )

    def test_invariante_formato_ruta_servible_o_data_uri(self):
        """
        [INVARIANZA 2 - ARCH-PILLAR]
        La URL debe ser una ruta estática servible montada (/static/img/crests/...)
        o un Data URI de SVG autocontenido (data:image/svg+xml...).
        """
        url_resuelta = self.resolver_escudo("Toluca")
        es_estatica_local = url_resuelta.startswith("/static/img/crests/") and url_resuelta.endswith(".png")
        es_data_svg = url_resuelta.startswith("data:image/svg+xml")

        assert es_estatica_local or es_data_svg, (
            f"Violación de Formato: La URL '{url_resuelta}' no es una ruta servible /static/ "
            f"ni un Data URI SVG válido."
        )

    def test_invariante_existencia_fisica_si_es_estatica(self):
        """
        [INVARIANZA 3 - GOVERNANCE-01]
        Si el resolutor devuelve una ruta '/static/img/crests/{archivo}.png',
        el archivo físico DEBE existir obligatoriamente en disco en src/web/static/...
        y no ser un archivo vacío (0 bytes).
        """
        url_resuelta = self.resolver_escudo("América")
        if url_resuelta.startswith("/static/"):
            ruta_relativa = url_resuelta.lstrip("/")
            ruta_fisica = os.path.join("src", "web", ruta_relativa)
            assert os.path.exists(ruta_fisica), (
                f"Violación de Integridad FÍSICA: Se resolvió '{url_resuelta}', "
                f"pero el archivo no existe en el sistema de archivos: {ruta_fisica}"
            )
            assert os.path.getsize(ruta_fisica) > 100, (
                f"Violación de Integridad: El archivo {ruta_fisica} está vacío o corrupto."
            )

    def test_invariante_fallback_elegante_equipo_desconocido(self):
        """
        [INVARIANZA 4 - SAD PATH]
        Ante un equipo desconocido o no catalogado, el sistema no debe fallar ni devolver None,
        sino un SVG válido generado al vuelo o el default.svg institucional.
        """
        url_fantasma = self.resolver_escudo("Club Deportivo Desconocido FC", fotmob_id=9999999)
        assert url_fantasma is not None and len(url_fantasma) > 0, "El resolutor devolvió vacío."
        assert url_fantasma.startswith("data:image/svg+xml") or "default.svg" in url_fantasma, (
            f"El equipo desconocido no degradó a un fallback seguro y legible: {url_fantasma}"
        )

    def test_invariante_live_board_standings_cero_hotlinks(self):
        """
        [INVARIANZA 5 - INTEGRACIÓN REAL]
        La lista completa de posiciones del Live Board para la Liga MX (18 clubes)
        debe tener el 100% de escudos con rutas locales válidas o SVG seguros.
        Cero URLs externas permitidas.
        """
        standings = self.obtener_live_board_standings(league_id=262)
        assert len(standings) == 18, f"Se esperaban 18 clubes en Liga MX, se recibieron {len(standings)}"

        for fila in standings:
            escudo = fila.get("escudo_url")
            equipo = fila.get("equipo", "Desconocido")
            assert escudo is not None, f"El equipo '{equipo}' tiene escudo_url nulo."
            assert "images.fotmob.com" not in escudo, (
                f"Contaminación en Live Board: '{equipo}' aún expone URL remota de FotMob: {escudo}"
            )
            assert escudo.startswith("/static/") or escudo.startswith("data:image/svg+xml"), (
                f"Ruta inválida en Live Board para '{equipo}': {escudo}"
            )
