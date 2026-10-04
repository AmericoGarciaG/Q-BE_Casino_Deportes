# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: RESOLUCIÓN CRONOLÓGICA DE MERCADO, PURGA ATÓMICA Y TOOLTIPS
[ARCH-1.6.21, ARCH-1.6.15-B, ARCH-1.6.13-B, ARCH-1.6.10-B, ARCH-1.4.13] & [DES-QBE-050]
Régimen: [DIRGEN-STRICT]
Axioma: Cero confusión entre calendario administrativo y ventanilla de casino.
"""

import os
import pytest
from abc import ABC, abstractmethod


# ── [ARCH-1.6.21] FRONTERA DE COMPETENCIA vs PK INTERNA DE `leagues` ────────────────────────
# Defecto latente: `FixtureSnapshot.league_id` es FK hacia `leagues.id`, mientras la frontera de
# competencia se declara con el `fotmob_id` (262). Una bóveda donde Liga MX quedó registrada con
# `leagues.id = 1` (seeder `src/storage/seeder.py`; JIT `src/ingestion/progol_resolver.py`) hacía
# que `cargar_fixtures_por_jornada(262)` devolviera vacío y el sensor abortara con «La bóveda 3NF no
# registra jornadas» pese a registrar la temporada entera.
ID_LIGA_MX_FOTMOB = 262
ID_LIGA_VISITANTE_FOTMOB = 670  # Segunda competencia: aísla la vista multi-liga explícita.


def _boveda_efimera_mercado(monkeypatch):
    """SQLite efímero en memoria inyectado en el singleton del Gateway [GOV-TEST-01].

    Cero red y cero contaminación de la bóveda real: el lector abre su propia sesión desde la
    fábrica del singleton, por lo que `StaticPool` es obligatorio para compartir la MISMA conexión
    que sembró el esquema.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from src.storage import gateway as gw_mod
    from src.storage.database import Base

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(gw_mod.PersistenceGateway(), "SessionFactory", factory)
    return factory()


def _cartelera(jornada: int, estado: str, partidos: int = 9):
    """Cartelera sintética mínima: el resolver sólo lee `estado` y `sub_badge` (Ley de ventanilla)."""
    return [
        {
            "local": f"Local J{jornada}-{i}",
            "visitante": f"Visitante J{jornada}-{i}",
            "estado": estado,
            "sub_badge": None,
        }
        for i in range(partidos)
    ]


def _sembrar_temporada(sesion, pk_liga: int, fotmob_id: int = ID_LIGA_MX_FOTMOB, jornadas=None):
    """Siembra una liga y sus snapshots de jornada en la bóveda efímera."""
    from src.storage.models import FixtureSnapshot, League

    sesion.add(League(
        id=pk_liga,
        name=f"Liga sintética {pk_liga}",
        country="México",
        flag="mx",
        fotmob_id=fotmob_id,
    ))
    sesion.flush()
    for jornada, estado in (jornadas or {10: "FINALIZADO", 11: "PROGRAMADO"}).items():
        sesion.add(FixtureSnapshot(
            league_id=pk_liga,
            matchday=jornada,
            matches_json=_cartelera(jornada, estado),
        ))
    sesion.commit()
    return sesion



class AbstractTestMarketResolutionAndPurge(ABC):
    """Juez Abstracto que audita la cronología de mercado y la higiene de base de datos."""

    def test_resolucion_cronologica_mercado_ignora_reprogramados_lejanos(self):
        """Verifica que el resolver no quede atrapado en J7 por juegos de noviembre."""
        from scripts.daemons.centinela_mercado import resolver_jornada_activa_dinamica

        # Simular base de datos real:
        # J10: Todos FINALIZADO (25-27 sep)
        # J7: 7 FINALIZADO y 2 juegos lejanos de octubre/noviembre
        # J11: 9 juegos PROGRAMADO para el próximo fin de semana (octubre)
        mock_fixtures = {
            7: [
                {"estado": "FINALIZADO"},
                {"estado": "PROGRAMADO", "sub_badge": "Fecha Lejana", "fecha_dt": "2026-10-28T21:00:00"},
                {"estado": "PROGRAMADO", "sub_badge": "Fecha Lejana", "fecha_dt": "2026-11-14T17:00:00"},
            ],
            10: [{"estado": "FINALIZADO"} for _ in range(9)],
            11: [{"estado": "PROGRAMADO", "sub_badge": None, "fecha_dt": "2026-10-09T19:00:00"} for _ in range(9)],
            12: [{"estado": "PROGRAMADO", "sub_badge": None, "fecha_dt": "2026-10-16T19:00:00"} for _ in range(9)]
        }
        jornada = resolver_jornada_activa_dinamica(mock_fixtures)
        assert jornada == 11, f"Fallo cronológico: debía resolver J11 por ser la próxima cartelera regular, resolvió J{jornada}"

    def test_purga_atomica_incluye_tablas_3nf(self):
        """Verifica mediante inspección de código que purgar_base_datos limpie Match y Slate."""
        purga_path = os.path.join("scripts", "utilidades", "purgar_base_datos.py")
        assert os.path.exists(purga_path), "purgar_base_datos.py no encontrado"

        with open(purga_path, "r", encoding="utf-8") as f:
            code = f.read()

        assert "Match" in code, "Violación ARCH-1.6.10-B: purgar_base_datos no limpia la tabla Match"
        assert "SovereignDistribution" in code, "Violación ARCH-1.6.10-B: no limpia SovereignDistribution"
        assert "Slate" in code, "Violación ARCH-1.6.10-B: no limpia Slates"

    def test_tooltips_didacticos_en_index_html(self):
        """Verifica que los botones del Centro de Control contengan el atributo title explicativo."""
        html_path = os.path.join("src", "web", "templates", "index.html")
        assert os.path.exists(html_path), "index.html no encontrado"

        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Acotar la inspección estrictamente al contenedor de la vista
        assert 'id="view-control-center"' in html
        seccion_cc = html.split('id="view-control-center"')[1].split('</section>')[0]

        # Verificar que el botón de purga y los daemons tengan su tooltip fiduciario
        assert 'title=' in seccion_cc, "Violación DES-QBE-050: Los botones en view-control-center no tienen tooltips"
        assert 'purgar_base_datos' in seccion_cc

    def test_erradicacion_duplicados_reprogramados_en_deportivo(self):
        """Verifica que centinela_deportivo no tenga la inyección fija if r == 8."""
        dep_path = os.path.join("scripts", "daemons", "centinela_deportivo.py")
        with open(dep_path, "r", encoding="utf-8") as f:
            code = f.read()

        assert "if r == 8" not in code, \
            "Violación ARCH-1.6.13-B: centinela_deportivo aún inyecta reprogramados con 'if r == 8'"

    def test_frontera_fotmob_262_se_traduce_a_la_pk_interna_de_leagues(self, monkeypatch):
        """[ARCH-1.6.21] `leagues.id = 1` con `fotmob_id = 262`: la frontera 262 lee la temporada."""
        from scripts.daemons.centinela_mercado import (
            cargar_fixtures_por_jornada,
            resolver_jornada_activa_dinamica,
        )

        sesion = _sembrar_temporada(_boveda_efimera_mercado(monkeypatch), pk_liga=1)
        try:
            leidas = cargar_fixtures_por_jornada(ID_LIGA_MX_FOTMOB)
            assert sorted(leidas) == [10, 11], (
                "Violación ARCH-1.6.21: la frontera FotMob 262 no se tradujo a la PK interna de "
                f"`leagues`; jornadas leídas = {sorted(leidas)}"
            )
            resuelta = resolver_jornada_activa_dinamica(leidas)
            assert resuelta == 11, (
                f"Violación de ventanilla: se esperaba J11 (cartelera PROGRAMADA), se obtuvo J{resuelta}"
            )
        finally:
            sesion.close()

    def test_frontera_tolera_la_convencion_pk_igual_al_fotmob_id(self, monkeypatch):
        """Convención histórica `leagues.id = fotmob_id = 262`: lectura idéntica, cero regresión."""
        from scripts.daemons.centinela_mercado import cargar_fixtures_por_jornada

        sesion = _sembrar_temporada(
            _boveda_efimera_mercado(monkeypatch), pk_liga=ID_LIGA_MX_FOTMOB)
        try:
            leidas = cargar_fixtures_por_jornada(ID_LIGA_MX_FOTMOB)
            assert sorted(leidas) == [10, 11], (
                "Regresión ARCH-1.6.21: la convención `leagues.id == fotmob_id` dejó de leerse; "
                f"jornadas leídas = {sorted(leidas)}"
            )
        finally:
            sesion.close()

    def test_vista_multiliga_explicita_permanece_intacta(self, monkeypatch):
        """`league_id=None` conserva la vista multi-liga: la frontera sólo acota la lectura por defecto."""
        from scripts.daemons.centinela_mercado import cargar_fixtures_por_jornada

        sesion = _boveda_efimera_mercado(monkeypatch)
        _sembrar_temporada(sesion, pk_liga=1)
        _sembrar_temporada(
            sesion,
            pk_liga=2,
            fotmob_id=ID_LIGA_VISITANTE_FOTMOB,
            jornadas={8: "PROGRAMADO"},
        )
        try:
            multi = cargar_fixtures_por_jornada(None)
            acotada = cargar_fixtures_por_jornada(ID_LIGA_MX_FOTMOB)
            assert sorted(multi) == [8, 10, 11], (
                f"Vista multi-liga degradada: jornadas = {sorted(multi)}"
            )
            assert sorted(acotada) == [10, 11], (
                f"Frontera de competencia contaminada por otra liga: jornadas = {sorted(acotada)}"
            )
        finally:
            sesion.close()

    def test_remapeo_de_la_frontera_al_identificador_arch_1_6_21(self):
        """[VARIANCE-01] La frontera del sensor se cita como `[ARCH-1.6.21]`; `1.6.15-C` es Live Board."""
        sensor_path = os.path.join("scripts", "daemons", "centinela_mercado.py")
        with open(sensor_path, "r", encoding="utf-8") as f:
            sensor = f.read()

        assert "[ARCH-1.6.21]" in sensor, (
            "Colisión no resuelta: el sensor de mercado no cita su cláusula de frontera [ARCH-1.6.21]"
        )
        assert "[ARCH-1.6.15-C]" not in sensor, (
            "Violación de unicidad (1 ID = 1 Cláusula): el sensor de mercado no puede citar "
            "[ARCH-1.6.15-C], reservado con exclusividad al Live Board (`src/storage/sync_service.py`)"
        )

        # Anclaje del Paso 0: todo nodo publicado debe existir en el Registro Maestro y en su libro.
        with open(os.path.join("docs", "ID_REGISTRY.md"), "r", encoding="utf-8") as f:
            registro = f.read()
        with open(os.path.join("docs", "ARCH.md"), "r", encoding="utf-8") as f:
            libro = f.read()

        assert "[ARCH-1.6.21]" in registro, \
            "Ceguera de colisión: [ARCH-1.6.21] no está anclado en docs/ID_REGISTRY.md"
        assert "### [ARCH-1.6.21]" in libro, "[ARCH-1.6.21] no está promulgado en docs/ARCH.md"

        # El nodo reservado conserva a su consumidor legítimo: cero remapeo del Live Board.
        with open(os.path.join("src", "storage", "sync_service.py"), "r", encoding="utf-8") as f:
            sync_service = f.read()
        assert "[ARCH-1.6.15-C]" in sync_service, (
            "El remapeo no debe tocar el Live Board: sync_service.py conserva [ARCH-1.6.15-C]"
        )

class TestMarketResolutionAndPurge(AbstractTestMarketResolutionAndPurge):
    """Implementación concreta en The Shield."""
    pass
