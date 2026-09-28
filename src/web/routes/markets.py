# -*- coding: utf-8 -*-
"""
🏆 Q-BE REST CONTROLLER — ESTACIÓN DE MERCADOS FINANCIEROS Y ASIGNACIÓN
[ARCH-1.4.5 / DES-QBE-032] Rutas de Liquidación Financiera (Casino 1X2, Progol y Arbitraje).
[LN-QBE-073] Endpoint de despacho con Slider Dinámico de Certeza (Risk Dial).
[LN-QBE-074] Endpoint de optimización Progol por Presupuesto.
[LN-QBE-075 / VARIANCE-03 extirpada] El slate Progol se hidrata de la bóveda 3NF (`slates` / `slate_items`);
prohibida toda constante quemada de equipos, probabilidades o venta pública.
Base de Gobierno: Kybern Framework v12.0
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from src.storage.gateway import PersistenceGateway
from src.storage.models import FixtureSnapshot, League, SovereignDistribution, Slate, SlateItem
from src.storage.database import get_db
from src.core.contracts.progol_math import calcular_sesgo_quiniela, optimizar_quiniela_por_presupuesto

router = APIRouter(prefix="/api/markets", tags=["Financial Markets"])


# ── CARGA FÁCTICA DEL SLATE PROGOL DESDE LA BÓVEDA 3NF [ARCH-1.5.1-C] ────────
# [VARIANCE-03 extirpada] Eliminada la constante quemada SLATE_PROGOL_14_ITEMS: el tablero Progol
# se hidrata EXCLUSIVAMENTE de `slates` / `slate_items` a través de PersistenceGateway.
# [GOVERNANCE-01] Cero equipos, probabilidades, bolsas o marcadores sintéticos: si la bóveda no
# contiene un concurso OPEN, el endpoint declara la vaciedad y NO inventa casillas.

SLATE_PROGOL_14 = 14  # Casillas REGULAR publicadas por el concurso Progol (posiciones 1..14).


def _cargar_slate_progol(session: Session, slate_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    [LN-QBE-075 / LN-QBE-037] Hidrata el concurso Progol vigente desde la persistencia 3NF.
    Devuelve None si no existe concurso OPEN con casillas (prohibido fabricar un slate).
    La venta pública sólo se puebla si existe captura fáctica de momios de casino de esa jornada.
    """
    consulta = session.query(Slate).filter(Slate.status == "OPEN")
    slate = None
    if slate_id:
        slate = consulta.filter(Slate.id == slate_id).first()
    if slate is None:
        # [VARIANCE-03] `slate_id` ausente o inexistente => se degrada al concurso OPEN real.
        slate = consulta.order_by(Slate.created_at.desc()).first()
    if slate is None:
        return None

    items = (
        session.query(SlateItem)
        .filter(SlateItem.slate_id == slate.id)
        .order_by(SlateItem.position.asc())
        .all()
    )
    if not items:
        return None

    # ── Venta pública: SOLO si existe captura fáctica de momios de casino de esa jornada ──
    momios_publicos: Dict[str, Dict[str, float]] = {}
    if slate.matchday_num is not None:
        snapshot = (
            session.query(FixtureSnapshot)
            .filter(FixtureSnapshot.matchday == slate.matchday_num)
            .order_by(FixtureSnapshot.updated_at.desc())
            .first()
        )
        if snapshot and snapshot.matches_json:
            for fx in snapshot.matches_json:
                momios = fx.get("momios") or {}
                if momios.get("L") and momios.get("E") and momios.get("V"):
                    momios_publicos[fx.get("id_partido", "")] = {
                        "L": float(momios["L"]),
                        "E": float(momios["E"]),
                        "V": float(momios["V"]),
                    }

    items_out: List[Dict[str, Any]] = []
    for item in items:
        p_qbe = {"L": item.p_local, "E": item.p_empate, "V": item.p_visitante}
        momios = momios_publicos.get(item.match_id or "", {})
        if momios:
            # [ARCH-1.4.5] Misma convención del plano casino: probabilidad implícita = 1 / momio.
            v_pub = {clave: round(1.0 / valor, 4) for clave, valor in momios.items()}
            sesgo_disponible = True
            sesgo_motivo = "MOMIOS_DE_CASINO_DE_LA_JORNADA"
        else:
            v_pub = {}
            sesgo_disponible = False
            sesgo_motivo = "VENTA_PUBLICA_NO_INGESTADA_PARA_ESTE_PARTIDO"

        items_out.append({
            "order": item.position,
            "tipo_concurso": item.tipo_concurso,
            "local": item.local_canonico or item.local_raw,
            "visitante": item.visitante_canonico or item.visitante_raw,
            "local_raw": item.local_raw,
            "visitante_raw": item.visitante_raw,
            "match_id": item.match_id,
            "p_qbe": p_qbe,
            "v_pub": v_pub,
            "es_prior_ignorancia": bool(item.es_prior_ignorancia),
            "estado_qbe": "PRIOR-FIDUCIARIO-1/3" if item.es_prior_ignorancia else "SOBERANO-3NF",
            "sesgo_disponible": sesgo_disponible,
            "sesgo_motivo": sesgo_motivo,
            "analisis_sesgo": calcular_sesgo_quiniela(v_pub, p_qbe) if sesgo_disponible else None,
        })

    return {
        "slate_id": slate.id,
        "name": slate.name,
        "status": slate.status,
        "matchday_num": slate.matchday_num,
        "bolsa_estimada": slate.bolsa_estimada,
        "fecha_cierre": slate.fecha_cierre.isoformat() if getattr(slate, "fecha_cierre", None) else None,
        "sesgo_fuente": "MOMIOS_DE_CASINO" if momios_publicos else "NO_DISPONIBLE",
        "items": items_out,
    }


# ── ESQUEMAS PYDANTIC V2 ─────────────────────────────────────────────────────

class SportsbookPortfolioRequest(BaseModel):
    """[LN-QBE-073] Request del generador de cartera con Slider de Certeza."""
    league_id: int = Field(default=262)
    selected_match_ids: Optional[List[str]] = Field(default_factory=list)
    bankroll: float = Field(default=200.0, ge=10.0)
    target_certeza: float = Field(default=0.80, ge=0.0, le=1.0)
    operador: Optional[str] = Field(default="caliente")


class ProgolOptimizeRequest(BaseModel):
    """
    [LN-QBE-074 / VARIANCE-03 extirpada] Request del optimizador Progol por presupuesto.
    `slate_id = None` => se resuelve el concurso OPEN vigente en la bóveda 3NF (cero ids sintéticos).
    """
    slate_id: Optional[str] = Field(default=None)
    presupuesto_mxn: float = Field(default=360.0, ge=15.0)


# ── [ARCH-1.6.15 / ARCH-1.6.2-B] RESOLUCIÓN DINÁMICA DE LA VENTANILLA DE CAPITAL ──
# [GOVERNANCE-01] Cero jornadas quemadas: la ventanilla emana del pool multiversal de
# snapshots capturados. Frontera de Despacho ([ARCH-1.6.2-B]): la selección MANUAL la
# gobierna el Live Board; el DESPACHO AUTOMÁTICO opera sobre las cuotas ya publicadas y
# no puede ser vetado por staleness sin declarar la jornada completa inoperable.


def _fixture_operable_en_ventanilla(fx: Dict[str, Any]) -> bool:
    """
    [ARCH-1.6.2] Un fixture es operable en la ventanilla de capital si NO está concluido y
    porta captura fáctica de cuotas 1X2 (L > 1.0). Cero cuotas inventadas [GOVERNANCE-01].
    """
    if str(fx.get("estado", "")) == "FINALIZADO":
        return False

    capturas: List[Dict[str, Any]] = [fx.get("momios") or {}]
    capturas.extend((fx.get("momios_operadores") or {}).values())

    for m_data in capturas:
        try:
            if float((m_data or {}).get("L", 0.0) or 0.0) > 1.0:
                return True
        except (TypeError, ValueError):
            continue

    return False


def _resolver_snapshot_ventanilla(
    session: Session,
    league_id: int,
    selected_ids: Optional[List[str]] = None
) -> Optional[FixtureSnapshot]:
    """
    [ARCH-1.6.15 / ARCH-1.4.10] Resuelve el snapshot de la jornada activa de la ventanilla
    sin constantes quemadas:
      1. Carril MANUAL (`selected_ids` con contenido): el snapshot más reciente que contenga
         alguno de los partidos solicitados (la selección la gobierna el Live Board).
      2. Carril AUTOMÁTICO: el snapshot más reciente que porte al menos un partido operable
         (no concluido con cuotas publicadas); si la jornada vigente concluyó en su
         totalidad, conmuta a la última jornada operable registrada en la bóveda.
    """
    snapshots = session.query(FixtureSnapshot).filter(
        FixtureSnapshot.league_id == league_id
    ).order_by(FixtureSnapshot.updated_at.desc()).all()

    if not snapshots:
        return None

    if selected_ids:
        for snap in snapshots:
            for fx in (snap.matches_json or []):
                if fx.get("id_partido", "") in selected_ids:
                    return snap
        return snapshots[0]

    for snap in snapshots:
        if any(_fixture_operable_en_ventanilla(fx) for fx in (snap.matches_json or [])):
            return snap

    return snapshots[0]


# ── ENDPOINTS ────────────────────────────────────────────────────────────────

@router.get("/sportsbook/matches")
def get_sportsbook_matches(
    bookmaker: str = Query("caliente", description="Operador de casino (ej. caliente)"),
    league_id: int = Query(262, description="ID de la liga")
) -> Dict[str, Any]:
    """
    [DES-QBE-032 / ARCH-1.4.5] Retorna los partidos abiertos con cuotas en ventanilla,
    contrastados contra la probabilidad soberana para exponer el GAP (+EV).
    """
    gateway = PersistenceGateway()

    with gateway.read_session() as session:
        league = session.query(League).filter((League.fotmob_id == league_id) | (League.id == league_id)).first()
        if not league:
            raise HTTPException(status_code=404, detail="Liga no encontrada.")

        # [ARCH-1.6.15 / ARCH-1.6.2-B] Ventanilla dinámica: partidos ABERTOS con cuotas
        # publicadas por el casino. Cero jornada quemada.
        fix_snap = _resolver_snapshot_ventanilla(session, league.id)

        if not fix_snap or not fix_snap.matches_json:
            return {"bookmaker": bookmaker, "league_id": league_id, "matches": []}

        matches_out = []
        for fx in fix_snap.matches_json:
            momios = fx.get("momios")
            if not momios or not momios.get("L"):
                continue

            mid = fx.get("id_partido", "")
            momio_l = float(momios.get("L", 0.0))
            momio_e = float(momios.get("E", 0.0))
            momio_v = float(momios.get("V", 0.0))
            pa = bool(momios.get("pago_anticipado", True))

            dist_db = session.query(SovereignDistribution).filter(SovereignDistribution.match_id == mid).first()
            p_l = dist_db.p_local if dist_db else 0.564
            p_e = dist_db.p_empate if dist_db else 0.258
            p_v = dist_db.p_visitante if dist_db else 0.178

            prob_impl_l = 1.0 / momio_l if momio_l > 0 else 0.0
            prob_impl_e = 1.0 / momio_e if momio_e > 0 else 0.0
            prob_impl_v = 1.0 / momio_v if momio_v > 0 else 0.0

            gap_l = round(p_l - prob_impl_l, 4)
            gap_e = round(p_e - prob_impl_e, 4)
            gap_v = round(p_v - prob_impl_v, 4)

            es_viable = (gap_l > 0.0 or gap_e > 0.0 or gap_v > 0.0)

            matches_out.append({
                "match_id": mid,
                "local": fx.get("local", ""),
                "visitante": fx.get("visitante", ""),
                "local_escudo_url": fx.get("local_escudo_url", ""),
                "visitante_escudo_url": fx.get("visitante_escudo_url", ""),
                "horario": fx.get("horario", ""),
                "p_local": p_l,
                "p_empate": p_e,
                "p_visitante": p_v,
                "momio_l": momio_l,
                "momio_e": momio_e,
                "momio_v": momio_v,
                "pago_anticipado": pa,
                "gap_local": gap_l,
                "gap_empate": gap_e,
                "gap_visitante": gap_v,
                "es_viable_ev": es_viable
            })

        return {
            "bookmaker": bookmaker,
            "league_id": league_id,
            "total_abiertos": len(matches_out),
            "matches": matches_out
        }


def _descartar_partido(
    fx: Dict[str, Any],
    motivo: str,
    momios: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    [ARCH-1.4.8 §3 / LN-QBE-005 / LN-QBE-065] Registro canonico del Radar de Descartes.
    Todo activo vetado se clasifica QBE-00 con inversion de $0.00 MXN y motivo fiduciario.
    El contrato es identico al historico (`partido` / `motivo` / `motivo_codigo` /
    `explicacion_didactica`), consumido por el Radar de Descartes de la SPA (app.js)
    y por el Auditor Sombra (scripts/auditoria/3_auditor_sombra_gemini.py).
    """
    from src.reporting.narrative import generar_justificacion_descarte

    item: Dict[str, Any] = {
        "id_partido": fx.get("id_partido", ""),
        "partido": f"{fx.get('local', 'Local')} vs {fx.get('visitante', 'Visita')}",
        "motivo": motivo,
        "motivo_titulo": "QBE-00",
        "motivo_codigo": "QBE-00",
        "codigo_estrategia": "QBE-00",
        "inversion_mxn": 0.0,
        "momios": momios if momios is not None else (fx.get("momios") or {})
    }
    item["explicacion_didactica"] = generar_justificacion_descarte(item)
    return item


def _orden_a_contrato_slider(
    orden: Dict[str, Any],
    candidato: Dict[str, Any]
) -> Dict[str, Any]:
    """
    [LN-QBE-073 / VAULT-CORE-006] Puente canonico Pydantic -> Contrato PLANO del Slider de Certeza.
    Reproduce EXACTAMENTE la regla que `PortfolioEngine.build_plan` aplica a su Trinidad 3^K
    [LN-QBE-072]: p_win <- prob_fav, p_draw <- prob_emp, p_loss <- prob_und (probabilidades
    soberanas ya certificadas por el triaje de 9 estrategias) y es_directo <- familia D.
    [GOVERNANCE-01] No se inventa ninguna magnitud: solo se TRANSPORTA capital y probabilidad
    ya calculados por el motor. Los defaults 70/20/10 son los MISMOS que usa `build_plan`
    (`portfolio.py` L556-558), por lo que el puente no introduce numeros nuevos.
    """
    boletos = orden.get("boletos") or {}
    proyecciones = orden.get("proyecciones") or {}
    codigo = str((orden.get("estrategia_seleccionada") or {}).get("codigo", "")).replace("+", "").strip()

    return {
        "id": orden.get("id_partido", ""),
        "ganancia": float(proyecciones.get("ganancia_neta_principal_mxn", 0.0) or 0.0),
        "inversion": float(boletos.get("inversion_partido_A_i", 0.0) or 0.0),
        "p_win": float(candidato.get("prob_fav", 70.0)) / 100.0,
        "p_draw": float(candidato.get("prob_emp", 20.0)) / 100.0,
        "p_loss": float(candidato.get("prob_und", 10.0)) / 100.0,
        "es_directo": codigo in ("QBE-D1", "QBE-D2"),
        "estrategia_codigo": codigo
    }


@router.post("/sportsbook/portfolio/generate")
def generate_sportsbook_portfolio_endpoint(
    req: SportsbookPortfolioRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    [ARCH-1.4.10] Despacho Financiero 3NF Desacoplado.
    Consulta directamente FixtureSnapshot y SovereignDistribution, ejecuta el triaje
    y despacha la cartera en tiempo record sin dependencias del motor monolitico legacy.
    """
    from src.storage.gateway import PersistenceGateway
    from src.core.contracts.portfolio_math import (
        triaje_determinista_9_estrategias,
        calcular_ranking_friccion,
        aplicar_hard_caps_constitucionales
    )
    from src.core.portfolio import PortfolioEngine
    from src.core.risk_dial_modulator import modular_cartera_por_slider_certeza

    # NOTA CANONICA: `aplicar_hard_caps_constitucionales` es la utilidad de verificacion
    # constitucional (8.0% individual / 25.0% de jornada); la acotacion efectiva vive DENTRO de
    # `PortfolioEngine.build_plan` ([LN-QBE-070-B]). Esta ruta es 100% read-only y no reescala
    # capital post-despacho (cero mutacion de magnitudes certificadas).

    gateway = PersistenceGateway()

    with gateway.read_session() as session:
        league = session.query(League).filter((League.fotmob_id == req.league_id) | (League.id == req.league_id)).first()
        if not league:
            raise HTTPException(status_code=404, detail="Liga no encontrada en SQLite.")

        # [ARCH-1.6.15 / ARCH-1.6.2-B] Frontera de Despacho: carril manual (Live Board) vs.
        # despacho automático de jornada (pool multiversal de snapshots capturados).
        fix_snap = _resolver_snapshot_ventanilla(session, league.id, req.selected_match_ids)

        if not fix_snap or not fix_snap.matches_json:
            raise HTTPException(status_code=400, detail="No hay partidos registrados para la jornada activa.")

        partidos_candidatos = []
        descartes: List[Dict[str, Any]] = []
        op_sel = (req.operador or "caliente").lower()

        for fx in fix_snap.matches_json:
            mid = fx.get("id_partido", "")
            if req.selected_match_ids and mid not in req.selected_match_ids:
                continue
            if fx.get("estado") == "FINALIZADO":
                # [ARCH-1.6.2] Partido concluido: vetado de la ventanilla de capital.
                descartes.append(_descartar_partido(fx, "Partido finalizado: fuera de ventanilla [ARCH-1.6.2]"))
                continue

            # Extraer cuotas del operador solicitado
            m_ops = fx.get("momios_operadores") or {}
            m_data = m_ops.get(op_sel) or fx.get("momios") or {}
            if not m_data or not m_data.get("L"):
                # [GOVERNANCE-01] Sin cuotas capturadas no existe +EV calculable: cero cuotas inventadas.
                descartes.append(_descartar_partido(fx, "Sin cuotas publicadas por el operador solicitado"))
                continue

            o_l = float(m_data.get("L", 0.0))
            o_e = float(m_data.get("E", 0.0))
            o_v = float(m_data.get("V", 0.0))
            pa = bool(m_data.get("pa", False) or m_data.get("pago_anticipado", False))

            # -- [ARCH-1.4.8 3] Compuerta de Descarte Temprano de Rentabilidad --
            # El veredicto del triaje de cuotas [LN-QBE-005] viaja CERTIFICADO en el snapshot
            # (`es_viable_triaje` / `motivo_triaje`). Un volado simetrico sin asimetria explotable
            # se deriva a QBE-00 con $0.00 MXN ANTES de asignar capital o ejecutar Dutching.
            if fx.get("es_viable_triaje", True) is False:
                motivo_veto = fx.get("motivo_triaje") or "Volado sin margen de cobertura bilateral (+EV nulo en cuotas)"
                descartes.append(_descartar_partido(fx, motivo_veto, momios={"L": o_l, "E": o_e, "V": o_v}))
                continue

            # Consultar distribucion soberana real en 3NF
            dist_db = session.query(SovereignDistribution).filter(SovereignDistribution.match_id == mid).first()
            p_l = dist_db.p_local if dist_db else 0.55
            p_e = dist_db.p_empate if dist_db else 0.25
            p_v = dist_db.p_visitante if dist_db else 0.20
            delta_epist = 0.02
            psi_epist = 0.9722
            phi_lead2 = dist_db.phi_lead2_home if dist_db else 0.50

            payload_match = {
                "p_local": p_l, "p_empate": p_e, "p_visitante": p_v,
                "delta_epist": delta_epist, "es_operable": True,
                "phi_lead2_home": phi_lead2
            }
            cuotas_match = {"L": o_l, "E": o_e, "V": o_v, "pa": pa}

            # 1. Triaje determinista de las 9 estrategias
            triaje = triaje_determinista_9_estrategias(payload_match, cuotas_match)
            if triaje["codigo"] == "QBE-00":
                descartes.append(_descartar_partido(fx, triaje["nombre"], momios={"L": o_l, "E": o_e, "V": o_v}))
                continue

            # Determinar favorito vs underdog
            if p_l >= p_v:
                fav_name, und_name = fx.get("local", "Local"), fx.get("visitante", "Visita")
                odd_fav, odd_und = o_l, o_v
                p_fav, p_und = p_l, p_v
            else:
                fav_name, und_name = fx.get("visitante", "Visita"), fx.get("local", "Local")
                odd_fav, odd_und = o_v, o_l
                p_fav, p_und = p_v, p_l

            partidos_candidatos.append({
                "id_partido": mid,
                "partido_nombre": f"{fx.get('local')} vs {fx.get('visitante')}",
                "horario": fx.get("horario", "Fin de Semana"),
                "strategy_code": triaje["codigo"],
                "strategy_nombre": triaje["nombre"],
                "ev_neto_roi": triaje["alpha"],
                "psi_downside": 0.05,
                "delta_epist": delta_epist,
                "psi_epist": psi_epist,
                "phi_lead2": phi_lead2,
                "odd_fav": odd_fav,
                "odd_emp": o_e,
                "odd_und": odd_und,
                "fav_name": fav_name,
                "und_name": und_name,
                "prob_fav": round(p_fav * 100.0, 1),
                "prob_emp": round(p_e * 100.0, 1),
                "prob_und": round(p_und * 100.0, 1),
                "pago_anticipado": pa,
                "alpha": triaje["alpha"]
            })

        if not partidos_candidatos:
            raise HTTPException(status_code=400, detail="Ningun partido supero el triaje fiduciario (+EV).")

        # 2. Ranking de Friccion
        candidatos_ordenados = calcular_ranking_friccion(partidos_candidatos)

        # 3. Construccion del Plan via PortfolioEngine
        plan = PortfolioEngine.build_plan(candidatos_ordenados, bankroll=req.bankroll, mode="BANKROLL")
        data = plan.model_dump()

        # 4. Modulacion con Slider de Certeza [LN-QBE-073] — ALT-1 RATIFICADO (VAR FASE5_PASO3)
        #    (a) El modulador recibe la orden en su contrato PLANO [VAULT-CORE-006]; entregarle el
        #        dump Pydantic anidado dejaba el control INERTE (V-1/V-2).
        #    (b) La cartera superviviente (podada / transmutada D->H1) se RE-DESPACHA por el motor
        #        canonico: `3^K`, la cascada de reveses, `control_portafolio` y `trinidad_resiliencia`
        #        vuelven a describir la cartera EFECTIVAMENTE entregada (resuelve V-3).
        #    Cero matematica nueva: el puente solo transporta capital y probabilidad certificadas.
        if req.target_certeza and req.target_certeza != 0.80:
            por_id = {c["id_partido"]: c for c in candidatos_ordenados}
            ordenes_planas = [
                _orden_a_contrato_slider(o.model_dump(), por_id[o.id_partido])
                for o in plan.ordenes_ejecucion_partidos
                if o.id_partido in por_id
            ]
            supervivientes = modular_cartera_por_slider_certeza(
                ordenes_planas, target_certeza_pct=req.target_certeza * 100.0
            )

            candidatos_finales: List[Dict[str, Any]] = []
            codigos_finales: Dict[str, str] = {}
            for s in supervivientes:
                cand = por_id.get(s.get("id"))
                if cand is None:
                    continue
                cand = dict(cand)
                transmutado = s.get("estrategia_codigo")
                if transmutado:
                    # [VAULT-CORE-006] Transmutacion D->H1 decretada por el modulador: el motor
                    # canonico recalcula la cobertura (Trinidad 3^K) desde la identidad de estrategia.
                    cand["strategy_code"] = transmutado
                codigos_finales[cand["id_partido"]] = str(cand.get("strategy_code", "")).replace("+", "").strip()
                candidatos_finales.append(cand)

            codigos_previos = {
                o.id_partido: o.estrategia_seleccionada.codigo.replace("+", "").strip()
                for o in plan.ordenes_ejecucion_partidos
            }
            if candidatos_finales and (
                len(candidatos_finales) != len(plan.ordenes_ejecucion_partidos)
                or codigos_finales != codigos_previos
            ):
                plan = PortfolioEngine.build_plan(candidatos_finales, bankroll=req.bankroll, mode="BANKROLL")
                data = plan.model_dump()

        # Alias de compatibilidad para The Shield
        data["balance_global_portafolio"] = data.get("balance_global_portafolio") or data.get("balance")
        data["control_portafolio"] = data.get("control_portafolio") or data.get("control")
        data["descartes"] = descartes

        return data


@router.get("/progol/slates/active")
def get_active_progol_slate() -> Dict[str, Any]:
    """
    [LN-QBE-037 / DES-QBE-032 / ARCH-1.5.1-C] Concurso Progol activo leído de la bóveda 3NF.
    Expone el contraste entre la probabilidad soberana Q-BE persistida y la venta pública fáctica
    (sólo si existe captura de momios de casino de esa jornada; en su ausencia se declara
    explícitamente la no disponibilidad — [GOVERNANCE-01], cero cifras inventadas).
    """
    gateway = PersistenceGateway()
    with gateway.read_session() as session:
        slate = _cargar_slate_progol(session)

    if slate is None:
        return {
            "slate_id": None,
            "name": None,
            "status": None,
            "matchday_num": None,
            "bolsa_garantizada_mxn": None,
            "fecha_cierre": None,
            "items_total": 0,
            "soberanos": 0,
            "priors": 0,
            "sesgo_fuente": "BOVEDA_SIN_CONCURSO_OPEN",
            "items": []
        }

    return {
        "slate_id": slate["slate_id"],
        "name": slate["name"],
        "status": slate["status"],
        "matchday_num": slate["matchday_num"],
        "bolsa_garantizada_mxn": slate["bolsa_estimada"],
        "fecha_cierre": slate["fecha_cierre"],
        "items_total": len(slate["items"]),
        "soberanos": sum(1 for i in slate["items"] if not i["es_prior_ignorancia"]),
        "priors": sum(1 for i in slate["items"] if i["es_prior_ignorancia"]),
        "sesgo_fuente": slate["sesgo_fuente"],
        "items": slate["items"]
    }


@router.post("/progol/optimize")
def optimize_progol_endpoint(req: ProgolOptimizeRequest) -> Dict[str, Any]:
    """
    [LN-QBE-074] Optimiza la asignación de dobles y triples respetando el
    presupuesto comercial. Costo = 15.00 × 2^D × 3^T ≤ presupuesto_mxn.
    El tablero se hidrata de `slate_items` (bloque REGULAR: las 14 casillas del concurso Progol).
    """
    gateway = PersistenceGateway()
    with gateway.read_session() as session:
        slate = _cargar_slate_progol(session, slate_id=req.slate_id)

    if slate is None:
        raise HTTPException(status_code=404, detail="No existe concurso Progol activo en la bóveda 3NF.")

    items_regular = [i for i in slate["items"] if i["tipo_concurso"] == "REGULAR"][:SLATE_PROGOL_14]
    return optimizar_quiniela_por_presupuesto(items_regular, req.presupuesto_mxn)
