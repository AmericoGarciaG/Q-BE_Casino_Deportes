# -*- coding: utf-8 -*-
"""
[LN-QBE-096] Coordinador Orquestador Atómico del Ciclo de Vida de Datos (Data Nexus Bus).
[ARCH-1.4.27] Módulo de Servicios de Composición y Orquestación (`src/services/`).

Régimen: [HÍBRIDO DUAL-TRACK].
  * Región [DIRGEN-STRICT] (NO fungible): el orden legislado de composición, la atomicidad de la
    Unit of Work, la aduana de integridad fail-fast y la degradación gobernada al Prior Fiduciario.
  * Región [DBBD-FUNGIBLE]: el cableado, el logging y los adaptadores de entrada/salida.

Axioma de diseño — el Coordinador es un COMPOSITOR, jamás un motor:
  1. Cero matemática propia: el símplex proviene EXCLUSIVAMENTE de `generar_distribucion_soberana`
     (`[VAULT-CORE-005]`), que publica el Prior Fiduciario `[LN-QBE-075]` cuando S(I) = 0.
  2. Cero fabricación de datos: toda evidencia fáctica entra por puerto inyectado (`[ARCH-1.4.24]`);
     sin evidencia la operación falla en voz alta (`[GOVERNANCE-01]`).
  3. Cero transacción parcial: `slates` + `slate_items` se escriben o no se escriben (todo o nada).
"""

import logging
import time
from typing import Any, Callable, List, Mapping, Optional, Sequence

from pydantic import BaseModel, Field

from src.core.sovereign_pipeline import generar_distribucion_soberana
from src.ingestion.schemas import ProgolContestDTO, ScheduledMatchDTO
from src.normalization.entity_resolver import resolver_entidad_oficial
from src.normalization.temporal_disambiguator import desambiguar_partido_por_ventana
from src.storage.models import Slate, SlateItem

logger = logging.getLogger("IngestionCoordinator")

OPERACION_PROGOL_FULL = "PROGOL_FULL"
ESTADO_EXITOSO = "SUCCESS"
ESTADO_FALLIDO = "FAILED"
ESTADO_SLATE_ABIERTO = "OPEN"
PLANTILLA_NOMBRE_CONCURSO = "Progol Concurso #{}"


class OperacionSinEvidencia(RuntimeError):
    """[LN-QBE-096].P.1 — [GOVERNANCE-01] FAIL-LOUD: jamás se sintetiza un concurso."""


class DTOInvalido(RuntimeError):
    """[LN-QBE-096].P.2 — la aduana de integridad rechaza el lote y aborta la operación."""


class CoordinatorExecutionReport(BaseModel):
    """
    [LN-QBE-096].O — Contrato de salida del orquestador atómico.

    `exitosos == 0` con `status == "FAILED"` es la evidencia de rollback total: el sistema jamás
    publica un snapshot parcial del concurso.
    """

    operacion: str
    status: str
    procesados: int = 0
    exitosos: int = 0
    errores: List[str] = Field(default_factory=list)
    duracion_s: float = 0.0


class IngestionCoordinator:
    """[LN-QBE-096] [ARCH-1.4.27] Puerta única de orquestación del Data Nexus Bus (Capa 5)."""

    def __init__(
        self,
        gateway: Optional[Any] = None,
        concurso_loader: Optional[Callable[[int], ProgolContestDTO]] = None,
    ) -> None:
        self._gateway = gateway
        self._concurso_loader = concurso_loader

    # ------------------------------------------------------------------ puertos
    @property
    def gateway(self):
        """Resolución PEREZOSA del singleton `PersistenceGateway` ([GOV-TEST-01]).

        Instanciar el coordinador jamás toca disco ni red: el adaptador de persistencia se resuelve
        en la primera operación real (import diferido).
        """
        if self._gateway is None:
            from src.storage.gateway import PersistenceGateway

            self._gateway = PersistenceGateway()
        return self._gateway

    # ------------------------------------------------------------------ orquestación
    def sincronizar_progol_pipeline_completo(
        self,
        concurso_num: Optional[int] = None,
        session: Optional[Any] = None,
        concurso_dto_inyectado: Optional[ProgolContestDTO] = None,
        candidatos_partidos: Optional[Sequence[ScheduledMatchDTO]] = None,
        datos_facticos_por_match: Optional[Mapping[str, Mapping[str, Any]]] = None,
    ) -> CoordinatorExecutionReport:
        """
        [LN-QBE-096].P — Orquestación atómica del ciclo de vida de un concurso de Progol.

        Composición encadenada: Sensor de Ingesta → Identity Brain → Desambiguación Temporal →
        Motor Soberano → Persistencia 3NF, dentro de UNA sola Unit of Work.

        Devuelve SIEMPRE un `CoordinatorExecutionReport`; una falla en vuelo jamás se silencia: la
        Unit of Work se revierte en su totalidad y la causa se publica en `errores`.
        """
        inicio = time.perf_counter()
        procesados = 0
        try:
            dto = self._adquirir_concurso(concurso_num, concurso_dto_inyectado)
            casillas = self._aduanar_lote(dto)
            procesados = len(casillas)
            if session is not None:
                self._persistir_agregado(
                    session, dto, casillas, candidatos_partidos, datos_facticos_por_match
                )
            else:
                with self.gateway.write_transaction() as sesion:
                    self._persistir_agregado(
                        sesion, dto, casillas, candidatos_partidos, datos_facticos_por_match
                    )
            logger.info(
                "[LN-QBE-096] %s consolidado atómicamente: concurso=%s casillas=%s",
                OPERACION_PROGOL_FULL, dto.contest_id, procesados,
            )
            return CoordinatorExecutionReport(
                operacion=OPERACION_PROGOL_FULL,
                status=ESTADO_EXITOSO,
                procesados=procesados,
                exitosos=procesados,
                errores=[],
                duracion_s=round(time.perf_counter() - inicio, 6),
            )
        except Exception as ex:  # FAIL-LOUD: la causa se publica, jamás se silencia.
            logger.error(
                "[LN-QBE-096] Operación %s abortada con rollback total: %s",
                OPERACION_PROGOL_FULL, ex,
            )
            return CoordinatorExecutionReport(
                operacion=OPERACION_PROGOL_FULL,
                status=ESTADO_FALLIDO,
                procesados=procesados,
                exitosos=0,
                errores=[str(ex)],
                duracion_s=round(time.perf_counter() - inicio, 6),
            )

    # ------------------------------------------------------------------ internos
    def _adquirir_concurso(
        self,
        concurso_num: Optional[int],
        concurso_dto_inyectado: Optional[ProgolContestDTO],
    ) -> ProgolContestDTO:
        """[LN-QBE-096].P.1 — Puerto inyectado primero; sensor `concurso_loader` después.

        Sin evidencia fáctica la operación es FAIL-LOUD: queda terminantemente prohibido sintetizar
        un concurso o rellenarlo con datos de fantasía ([GOVERNANCE-01]).
        """
        if concurso_dto_inyectado is not None:
            return concurso_dto_inyectado
        if self._concurso_loader is not None and concurso_num is not None:
            dto = self._concurso_loader(concurso_num)
            if dto is None:
                raise OperacionSinEvidencia(
                    f"El sensor de ingesta no publicó evidencia para el concurso {concurso_num}."
                )
            return dto
        raise OperacionSinEvidencia(
            "Sin evidencia fáctica: se requiere `concurso_dto_inyectado` o un `concurso_loader` "
            "registrado junto con su `concurso_num`. Prohibido sintetizar el concurso "
            "[GOVERNANCE-01]."
        )

    @staticmethod
    def _aduanar_lote(dto: ProgolContestDTO) -> List[dict]:
        """[LN-QBE-096].P.2 — Aduana de integridad fail-fast, previa a abrir la Unit of Work."""
        if not str(dto.contest_id or "").strip():
            raise DTOInvalido("Concurso inválido: `contest_id` vacío.")
        if not dto.items:
            raise DTOInvalido(f"Concurso {dto.contest_id} inválido: `items` vacío.")
        casillas: List[dict] = []
        for indice, item in enumerate(dto.items, start=1):
            posicion = int(item.get("position") or indice)
            local = str(item.get("local_raw") or "").strip()
            visitante = str(item.get("visitante_raw") or "").strip()
            if not local or not visitante:
                raise DTOInvalido(
                    f"Casilla {posicion} del concurso {dto.contest_id} incompleta: "
                    "se exigen ambos literales (`local_raw`, `visitante_raw`)."
                )
            casillas.append(
                {"position": posicion, "local_raw": local, "visitante_raw": visitante}
            )
        return casillas

    def _persistir_agregado(
        self,
        sesion: Any,
        dto: ProgolContestDTO,
        casillas: Sequence[Mapping[str, Any]],
        candidatos_partidos: Optional[Sequence[ScheduledMatchDTO]],
        datos_facticos_por_match: Optional[Mapping[str, Mapping[str, Any]]],
    ) -> None:
        """[LN-QBE-096].P.3–P.6 — Agregado de quiniela íntegro dentro de UNA Unit of Work.

        Idempotente: cabecera por `slates.id` y casillas por la clave única `(slate_id, position)`.
        """
        cabecera = sesion.get(Slate, dto.contest_id)
        if cabecera is None:
            cabecera = Slate(
                id=dto.contest_id, name=PLANTILLA_NOMBRE_CONCURSO.format(dto.contest_id)
            )
            sesion.add(cabecera)
        cabecera.name = PLANTILLA_NOMBRE_CONCURSO.format(dto.contest_id)
        cabecera.bolsa_estimada = float(dto.bolsa_estimada)
        cabecera.fecha_cierre = dto.cierre_utc
        cabecera.status = ESTADO_SLATE_ABIERTO

        for casilla in casillas:
            composicion = self._componer_casilla(
                dto.contest_id,
                casilla,
                dto.cierre_utc,
                candidatos_partidos,
                datos_facticos_por_match,
            )
            registro = (
                sesion.query(SlateItem)
                .filter(
                    SlateItem.slate_id == dto.contest_id,
                    SlateItem.position == casilla["position"],
                )
                .one_or_none()
            )
            if registro is None:
                registro = SlateItem(slate_id=dto.contest_id, position=casilla["position"])
                sesion.add(registro)
            for campo, valor in composicion.items():
                setattr(registro, campo, valor)

        sesion.flush()

    @staticmethod
    def _componer_casilla(
        contest_id: str,
        casilla: Mapping[str, Any],
        cierre_utc: Optional[Any],
        candidatos_partidos: Optional[Sequence[ScheduledMatchDTO]],
        datos_facticos_por_match: Optional[Mapping[str, Mapping[str, Any]]],
    ) -> dict:
        """[LN-QBE-096].P.4–P.5 — Composición pura: Identity Brain → Desambiguación → Motor Soberano.

        El Coordinador NO calcula: transcribe verbatim el símplex publicado por el motor sellado y
        jamás publica una probabilidad propia.
        """
        local = resolver_entidad_oficial(casilla["local_raw"])
        visitante = resolver_entidad_oficial(casilla["visitante_raw"])

        vinculo = None
        if cierre_utc is not None:
            vinculo = desambiguar_partido_por_ventana(
                local.canonical_name,
                visitante.canonical_name,
                cierre_utc,
                list(candidatos_partidos or []),
            )

        if vinculo is not None:
            etiqueta_traza = vinculo.match_id
            evidencia = dict((datos_facticos_por_match or {}).get(vinculo.match_id) or {})
        else:
            # Etiqueta de TRAZA interna (coordenada sellada del concurso): no es identidad de
            # partido y jamás se persiste. Sin vínculo ⇒ evidencia vacía ⇒ S(I) = 0.
            etiqueta_traza = "{}-{:02d}".format(contest_id, casilla["position"])
            evidencia = {}

        salida = generar_distribucion_soberana(etiqueta_traza, evidencia)

        return {
            "local_raw": casilla["local_raw"],
            "visitante_raw": casilla["visitante_raw"],
            "local_canonico": local.canonical_name,
            "visitante_canonico": visitante.canonical_name,
            # Sin vínculo soberano operativo no se reclama partido: casilla ⇒ Prior [LN-QBE-075].
            "match_id": vinculo.match_id if (vinculo is not None and salida.es_operable) else None,
            "p_local": salida.p_local,
            "p_empate": salida.p_empate,
            "p_visitante": salida.p_visitante,
            "es_prior_ignorancia": not salida.es_operable,
        }
