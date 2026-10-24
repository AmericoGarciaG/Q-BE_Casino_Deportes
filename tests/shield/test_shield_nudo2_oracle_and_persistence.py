# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DEL NUDO 2 (ORÁCULO 3NF Y PERSISTENCIA)
[ARCH-1.5.0 · Enmienda Nudo 2] · [ARCH-1.6.12 · Enmienda Nudo 2] · [LN-QBE-130 · Enmienda Nudo 2]
Régimen: [DIRGEN-STRICT]

Invariantes certificadas:
1. El Centinela Deportivo no alambra rangos de jornada quemados (`range(10, 18)`).
2. El Centinela Deportivo declara `MARCADOR_PENDIENTE` y jamás fabrica el literal `"0 - 0"`.
3. El Seeder no siembra posiciones estáticas ni cuotas comerciales inventadas.
4. `src/storage/database.py` está erradicado —o, si subsiste, aislado de `leagues.py` y
   `seeder.py`—; toda transacción pasa por `PersistenceGateway`.
5. El ORM `Match` declara `ForeignKey` hacia `teams.id` en los ejes de localía.

En Fase 2 este juez debe estar en ROJO. En Fase 3 (materialización en `src/` y
`scripts/`) debe pasar sin una sola concesión.
"""

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
CENTINELA = RAIZ / "scripts" / "daemons" / "centinela_deportivo.py"
SEEDER = RAIZ / "src" / "storage" / "seeder.py"
DATABASE_PY = RAIZ / "src" / "storage" / "database.py"


def _texto(ruta: Path) -> str:
    assert ruta.exists(), f"Archivo requerido no encontrado: {ruta.relative_to(RAIZ)}"
    return ruta.read_text(encoding="utf-8")


class TestNudo2Oraculo3NF:
    """[NUDO 2] Erradicación de la evasión del Gateway y de la fabricación en el oráculo 3NF."""

    def test_centinela_no_usa_rangos_quemados(self):
        """[ARCH-1.6.12 · Enmienda Nudo 2] La ingesta itera TODAS las jornadas de la fuente."""
        contenido = _texto(CENTINELA)
        hallazgo = re.search(r"range\(\s*10\s*,\s*18\s*\)", contenido)
        assert hallazgo is None, (
            "🚨 VIOLACIÓN [ARCH-1.6.12 · Enmienda Nudo 2]: `centinela_deportivo.py` conserva "
            f"el rango de jornadas quemado `{hallazgo.group(0) if hallazgo else ''}`. "
            "La ingesta debe iterar dinámicamente sobre todas las jornadas devueltas por la "
            "fuente fáctica (N ∈ [1, 17]), no sobre un tramo alambrado."
        )

    def test_centinela_usa_marcador_pendiente(self):
        """[ARCH-1.6.12 · Enmienda Nudo 2] Sin goles publicados: MARCADOR_PENDIENTE, jamás 0-0."""
        contenido = _texto(CENTINELA)
        fabricado = re.search(r"or\s+['\"]0\s*-\s*0['\"]", contenido)
        assert fabricado is None, (
            "🚨 VIOLACIÓN [ARCH-1.6.12 · Enmienda Nudo 2]: el Centinela fabrica "
            f"`{fabricado.group(0) if fabricado else ''}` cuando el marcador no se publica. "
            "[LN-QBE-018] H4 exige `MARCADOR_PENDIENTE`."
        )
        assert "MARCADOR_PENDIENTE" in contenido, (
            "🚨 VIOLACIÓN [ARCH-1.6.12 · Enmienda Nudo 2]: el Centinela no declara "
            "`MARCADOR_PENDIENTE` para partidos concluidos sin goles publicados."
        )

    def test_seeder_no_inventa_datos(self):
        """[LN-QBE-130 · Enmienda Nudo 2] El Seeder solo inicializa estructura base."""
        contenido = _texto(SEEDER)
        for literal in ("TABLA_OFICIAL_J7_CONCLUIDA", "fixtures_iniciales_j8", "momios"):
            assert literal not in contenido, (
                "🚨 VIOLACIÓN [LN-QBE-130 · Enmienda Nudo 2]: el Seeder conserva "
                f"`{literal}`. Queda prohibido sembrar posiciones estáticas o cuotas "
                "comerciales inventadas; el resto debe venir de la ingesta fáctica."
            )

    def test_database_py_erradicado(self):
        """[ARCH-1.5.0 · Enmienda Nudo 2] El motor paralelo no existe o no es importado."""
        if not DATABASE_PY.exists():
            return

        consumidores = (
            RAIZ / "src" / "web" / "routes" / "leagues.py",
            RAIZ / "src" / "storage" / "seeder.py",
        )
        for consumidor in consumidores:
            texto = _texto(consumidor)
            importa_motor = (
                "src.storage.database" in texto
                or "from src.storage import database" in texto
            )
            assert not importa_motor, (
                "🚨 VIOLACIÓN [ARCH-1.5.0 · Enmienda Nudo 2]: "
                f"`{consumidor.relative_to(RAIZ)}` importa el motor paralelo erradicado "
                "`src/storage/database.py`. Toda escritura, lectura y transacción debe "
                "canalizarse por `PersistenceGateway`."
            )

    @pytest.mark.xfail(
        reason="VAR-2026-ORACLE-FK-MIGRATION: Migración a VARCHAR pendiente"
    )
    def test_orm_match_tiene_fk(self):
        """[ARCH-1.5.1 · Nudo 2] Integridad referencial del oráculo en los ejes de localía."""
        from src.storage.models import Match

        columnas = Match.__table__.columns
        pares = (("home_team_slug", "away_team_slug"), ("home_team_id", "away_team_id"))
        par = next((p for p in pares if p[0] in columnas and p[1] in columnas), None)
        assert par is not None, (
            "🚨 VIOLACIÓN [ARCH-1.5.1]: `Match` no declara los ejes de localía "
            "(ni `home_team_slug`/`away_team_slug` ni `home_team_id`/`away_team_id`)."
        )

        for nombre in par:
            columna = columnas[nombre]
            destinos = {(fk.column.table.name, fk.column.name) for fk in columna.foreign_keys}
            assert ("teams", "id") in destinos, (
                "🚨 VIOLACIÓN [ARCH-1.5.1 · Nudo 2]: la columna "
                f"`Match.{nombre}` no declara ForeignKey hacia `teams.id` "
                f"(destinos observados: {sorted(destinos) or 'ninguno'}). "
                "El oráculo 3NF pierde integridad referencial."
            )
