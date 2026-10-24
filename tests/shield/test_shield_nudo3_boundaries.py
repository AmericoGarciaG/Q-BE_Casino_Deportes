# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DEL NUDO 3 (FRONTERA src/ ↔ scripts/)
[ARCH-1.6.4 · Enmienda Nudo 3] · [ARCH-1.3.5 · Enmienda Nudo 3] · [LN-QBE-107 · Enmienda Nudo 3]
Régimen: [DIRGEN-STRICT]

Invariantes certificadas:
1. `src/web/routes/markets.py` no importa NADA desde `scripts/`.
2. `src/ingestion/providers/h2h_provider.py` no importa NADA desde `scripts/`.
3. El endpoint legacy `POST /generate` de `src/web/routes/portfolio.py` está físicamente
   eliminado (decorador y función).

En Fase 2 este juez debe estar en ROJO. En Fase 3 (materialización) debe pasar sin
una sola concesión.

Nota de alcance declarada: existe un cuarto cruce de frontera no cubierto por este
juez —`src/web/routes/admin_status.py` importa `scripts.auditoria.auditar_coherencia_cartelera`—
que la Enmienda Nudo 3 también prohíbe y que debe incorporarse al alcance de la
materialización.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MARKETS = RAIZ / "src" / "web" / "routes" / "markets.py"
PORTFOLIO = RAIZ / "src" / "web" / "routes" / "portfolio.py"
ADMIN_STATUS = RAIZ / "src" / "web" / "routes" / "admin_status.py"
H2H_PROVIDER_CANDIDATOS = (
    # El proveedor reside en el paquete soberano; se admite la ruta nominal de la
    # Directiva por si la materialización lo reubica en `src/ingestion/providers/`.
    RAIZ / "src" / "core" / "sovereign" / "h2h_provider.py",
    RAIZ / "src" / "ingestion" / "providers" / "h2h_provider.py",
)


def _texto(ruta: Path) -> str:
    assert ruta.exists(), f"Archivo requerido no encontrado: {ruta.relative_to(RAIZ)}"
    return ruta.read_text(encoding="utf-8")


def _texto_proveedor_h2h() -> str:
    for ruta in H2H_PROVIDER_CANDIDATOS:
        if ruta.exists():
            return ruta.read_text(encoding="utf-8")
    ubicaciones = " ni ".join(str(r.relative_to(RAIZ)) for r in H2H_PROVIDER_CANDIDATOS)
    raise AssertionError(f"Archivo requerido no encontrado: {ubicaciones}")


class TestNudo3FronteraSrcScripts:
    """[NUDO 3] Pureza de la frontera: producción no depende de `scripts/`."""

    def test_markets_no_importa_scripts(self):
        """[ARCH-1.6.4 · Enmienda Nudo 3] El endpoint de simulación no importa el sandbox."""
        contenido = _texto(MARKETS)
        assert "from scripts.laboratorio.sandbox_rentabilidad_pipeline import" not in contenido, (
            "🚨 VIOLACIÓN [ARCH-1.6.4 · Enmienda Nudo 3]: `markets.py` importa el sandbox "
            "`scripts.laboratorio.sandbox_rentabilidad_pipeline`. El motor de simulación debe "
            "residir en `src/core/` y el script debe ser su consumidor, no su proveedor."
        )
        assert "from scripts." not in contenido, (
            "🚨 VIOLACIÓN [ARCH-1.6.4 · Enmienda Nudo 3]: `markets.py` conserva una "
            "importación desde el directorio `scripts/`."
        )

    def test_h2h_provider_no_importa_scripts(self):
        """[ARCH-1.6.4 · Enmienda Nudo 3] El proveedor H2H no importa utilidades de scripts."""
        contenido = _texto_proveedor_h2h()
        assert "from scripts.utilidades.poblar_temporada_completa_backtesting import" not in contenido, (
            "🚨 VIOLACIÓN [ARCH-1.6.4 · Enmienda Nudo 3]: `h2h_provider.py` importa utilidades "
            "de `scripts/utilidades/`. La lógica debe migrarse a `src/core/` o `src/services/`."
        )
        assert "from scripts." not in contenido, (
            "🚨 VIOLACIÓN [ARCH-1.6.4 · Enmienda Nudo 3]: `h2h_provider.py` conserva una "
            "importación desde el directorio `scripts/`."
        )

    def test_portfolio_legacy_generate_eliminado(self):
        """[ARCH-1.3.5 · Enmienda Nudo 3] La ruta legacy `/generate` está eliminada."""
        contenido = _texto(PORTFOLIO)
        assert '@router.post("/generate")' not in contenido, (
            "🚨 VIOLACIÓN [ARCH-1.3.5 · Enmienda Nudo 3]: `portfolio.py` conserva el decorador "
            '`@router.post("/generate")`. La ruta legacy duplica `markets.py` y debe ser '
            "físicamente eliminada."
        )
        assert "def generate_portfolio(" not in contenido, (
            "🚨 VIOLACIÓN [ARCH-1.3.5 · Enmienda Nudo 3]: la función `generate_portfolio` "
            "sigue existiendo en `portfolio.py`."
        )

    def test_admin_status_no_importa_scripts(self):
        """[ARCH-1.6.4 · Enmienda Nudo 3] El semáforo de deriva no importa el auditor de scripts."""
        contenido = _texto(ADMIN_STATUS)
        assert "from scripts." not in contenido, (
            "🚨 VIOLACIÓN [ARCH-1.6.4 · Enmienda Nudo 3]: `admin_status.py` importa desde el "
            "directorio `scripts/` (auditor de coherencia). La lógica debe residir en "
            "`src/core/coherence_auditor.py`."
        )
