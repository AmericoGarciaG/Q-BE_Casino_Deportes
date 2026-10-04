# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DE CAPA 2 (DATA NEXUS)
Validación de:
- [LN-QBE-095] Guardas de Género y Categoría.
- [LN-QBE-094] Desambiguación Temporal en Ventana Crítica [t ± 72h].
- [ARCH-1.4.25] Módulo de Normalización, Jerga y Desambiguación (`src/normalization/`).
- [ARCH-1.5.12] Aprovisionamiento JIT de Ligas y Bóveda Soberana de Activos.
Nota de trazabilidad (VAR-2026-ARCH-1.5.11): el bloque fue inyectado como [ARCH-1.5.11] y
remapeado a [ARCH-1.5.12] por colisión con el nodo sellado (PROGOL_GLOBAL_ALIASES).
Ver docs/DIRGEN_VARIANCE_REQUEST_ARCH-1.5.11_COLLISION.md
"""

from datetime import datetime, timezone, timedelta
import pytest
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# 1. PRUEBA DE GUARDAS DE GÉNERO Y CATEGORÍA ([LN-QBE-095])
# ---------------------------------------------------------------------------
def test_ln_qbe_095_gender_and_category_guards():
    """Audita que equipos femeniles, filiales y juveniles no colisionen con el primer equipo."""
    try:
        from src.normalization.gender_guards import categorizar_entidad_deportiva
    except ImportError as e:
        pytest.fail(f"❌ [LN-QBE-095] Faltan las guardas de género en src/normalization/gender_guards.py: {e}")

    # Caso 1: Femenil
    ent_fem = categorizar_entidad_deportiva("América Femenil")
    assert ent_fem.category == "FEMENIL"
    assert "femenil" in ent_fem.canonical_slug
    assert ent_fem.canonical_slug != "club-america"

    # Caso 2: Filial 'B'
    ent_b = categorizar_entidad_deportiva("Real Sociedad B")
    assert ent_b.category == "FILIAL"
    assert ent_b.canonical_slug.endswith("-b")

    # Caso 3: Juvenil Sub-20
    ent_sub = categorizar_entidad_deportiva("Santos Laguna Sub-20")
    assert ent_sub.category == "SUB20"
    assert "sub20" in ent_sub.canonical_slug

    # Caso 4: Varonil Mayor (Neutro)
    ent_masc = categorizar_entidad_deportiva("Tigres UANL")
    assert ent_masc.category == "VARONIL_MAYOR"
    assert "femenil" not in ent_masc.canonical_slug


# ---------------------------------------------------------------------------
# 2. PRUEBA DE DESAMBIGUACIÓN TEMPORAL ([LN-QBE-094])
# ---------------------------------------------------------------------------
def test_ln_qbe_094_temporal_disambiguation_window():
    """Audita que partidos idénticos en torneos distintos se desambigüen por ventana [t_cierre ± 72h]."""
    try:
        from src.normalization.temporal_disambiguator import desambiguar_partido_por_ventana
        from src.ingestion.schemas import ScheduledMatchDTO
    except ImportError as e:
        pytest.fail(f"❌ [LN-QBE-094] Falta el desambiguador temporal: {e}")

    t_cierre = datetime(2026, 10, 15, 17, 0, tzinfo=timezone.utc)

    # Simular dos partidos idénticos: uno en la ventana de la jornada y otro 13 días después (Copa)
    partido_liga_mx = ScheduledMatchDTO(
        match_id="LIGAMX-2026-J12-01",
        home_team="Club América",
        away_team="CF Monterrey",
        kickoff_utc=datetime(2026, 10, 16, 21, 0, tzinfo=timezone.utc), # +28 horas (DENTRO)
        tournament_id=262
    )

    partido_concachampions = ScheduledMatchDTO(
        match_id="CONCACAF-2026-QF-01",
        home_team="Club América",
        away_team="CF Monterrey",
        kickoff_utc=datetime(2026, 10, 28, 2, 0, tzinfo=timezone.utc), # +300 horas (FUERA)
        tournament_id=227
    )

    candidatos = [partido_concachampions, partido_liga_mx]

    resultado = desambiguar_partido_por_ventana(
        team_a="Club América",
        team_b="CF Monterrey",
        t_cierre=t_cierre,
        candidatos=candidatos
    )

    assert resultado is not None, "El desambiguador debió encontrar el partido válido"
    assert resultado.match_id == "LIGAMX-2026-J12-01", "Debió seleccionar el partido dentro de la ventana de 72h"
    assert resultado.competition_id == 262
    assert not resultado.is_ambiguous


# ---------------------------------------------------------------------------
# 3. PRUEBA DE LA BÓVEDA DE ACTIVOS Y RUTAS LOCALES ([ARCH-1.5.12])
# ---------------------------------------------------------------------------
def test_arch_1_5_12_asset_vault_local_paths_and_anti_hotlinking():
    """Audita que el servicio de bóveda entregue exclusivamente URIs locales y rechace hotlinks."""
    try:
        from src.normalization.asset_vault_service import resolver_uri_activo_local
    except ImportError as e:
        pytest.fail(f"❌ [ARCH-1.5.12] Falta el servicio de bóveda en src/normalization/asset_vault_service.py: {e}")

    # Verificar resolución de ruta local para clubes
    uri_club = resolver_uri_activo_local("cruz-azul", tipo="team")
    assert uri_club.startswith("/static/img/crests/"), "La URI del club debe apuntar a la ruta estática local"
    assert "images.fotmob.com" not in uri_club, "Prohibido hotlinking en URLs de clubes"

    # Verificar resolución de ruta local para ligas
    uri_liga = resolver_uri_activo_local("laliga", tipo="league")
    assert uri_liga.startswith("/static/img/leagues/"), "La URI de la liga debe apuntar a la ruta estática local"


# ---------------------------------------------------------------------------
# 4. PRUEBA DE CONTRATO DEL APROVISIONADOR DE LIGAS ([ARCH-1.5.12])
# ---------------------------------------------------------------------------
def test_arch_1_5_12_league_provisioner_interface():
    """Audita que el aprovisionador de ligas exponga la función canónica requerida."""
    try:
        from src.normalization.league_provisioner import provisionar_competicion_y_clubes_jit
    except ImportError as e:
        pytest.fail(f"❌ [ARCH-1.5.12] Falta el aprovisionador JIT en src/normalization/league_provisioner.py: {e}")

    import inspect
    sig = inspect.signature(provisionar_competicion_y_clubes_jit)
    assert "fotmob_league_id" in sig.parameters, "El aprovisionador debe recibir fotmob_league_id"
    assert "session" in sig.parameters or "gateway" in sig.parameters, "El aprovisionador debe aceptar sesión o gateway de DB"


# ---------------------------------------------------------------------------
# 5. PRUEBA DE LOS DTOs LEGISLADOS DE CAPA 2 (SECCIÓN 5 DEL DECRETO)
# ---------------------------------------------------------------------------
def test_sprint2_legislated_dtos_structure():
    """Audita la materialización y estructura Pydantic de los DTOs legislados de Capa 2."""
    try:
        from src.ingestion.schemas import CategorizedEntityDTO, DisambiguatedMatchDTO
    except ImportError as e:
        pytest.fail(f"❌ [LN-QBE-094/095] Faltan los DTOs legislados en src/ingestion/schemas.py: {e}")

    from pydantic import BaseModel

    assert issubclass(DisambiguatedMatchDTO, BaseModel), "DisambiguatedMatchDTO debe ser un contrato Pydantic V2"
    assert issubclass(CategorizedEntityDTO, BaseModel), "CategorizedEntityDTO debe ser un contrato Pydantic V2"

    campos_desambiguacion = {"match_id", "competition_id", "kickoff_utc", "is_ambiguous"}
    campos_categoria = {"canonical_name", "canonical_slug", "category"}

    assert campos_desambiguacion <= set(DisambiguatedMatchDTO.model_fields), \
        f"❌ [LN-QBE-094] DisambiguatedMatchDTO incompleto: faltan {campos_desambiguacion - set(DisambiguatedMatchDTO.model_fields)}"
    assert campos_categoria <= set(CategorizedEntityDTO.model_fields), \
        f"❌ [LN-QBE-095] CategorizedEntityDTO incompleto: faltan {campos_categoria - set(CategorizedEntityDTO.model_fields)}"

