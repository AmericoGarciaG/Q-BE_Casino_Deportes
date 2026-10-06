# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ INMUTABLE DE LA SIMETRÍA CANÓNICA H1/H2 (INVARIANTE VIII-11)
[INVARIANTE VIII-11] / [LN-QBE-083] / [VAULT-CORE-070-DUTCHING] / [LN-QBE-071] /
[LN-QBE-060-B] / [ARCH-1.4.9]

Resolución Definitiva de VARIANZA-H2 (Dictamen del Director Humano, 2026-10): queda DEROGADO el
Diseño B del commit génesis `0f4b340` ("Empate de Valor con Seguro Fav") y se restituye el
Diseño A — la Familia H COMPLETA (`QBE-H1` y `QBE-H2`) ataca al FAVORITO (α > 0) y recupera el
100% del capital en TABLAS con el EMPATE (V = 0).

Auditoría (aritmética viva del motor, jamás re-implementada por el Juez):
- `QBE-H2`: pierna 2 = ataque al favorito VISITANTE (@O_V); pierna 1 = seguro en Empate
  (@O_X) con reintegro exacto del capital (V = 0).
- Simetría estricta H1/H2: ante momios idénticos, la estructura de capital de ambas familias es
  la MISMA (doctrina de cobertura única).
- Piso de ventanilla [LN-QBE-071]: el clamping re-deriva `A_i = $2.00 · O_Empate` (jamás `O_fav`).
- [LN-QBE-083]: el Doble Cobro del Pago Anticipado obedece
  `Ganancia Neta = B_prio · O_fav` ⟹ `ROI_doble = (1 − 1/O_emp) · O_fav`.
- Ley del Vault conectada: `calcular_dutching_v0` ([VAULT-CORE-070-DUTCHING]) deja de ser ley
  huérfana (V-1) y gobierna la asignación de importes de la Familia H.

Régimen: [HÍBRIDO DUAL-TRACK] — aritmética sellada (portfolio.py) + contrato Pydantic inmutable.
Hermeticidad [GOV-TEST-01]: cero red, cero DB, cero mocks en producción (DTOs evaluados en memoria).
"""

import ast
from abc import ABC, abstractmethod
from pathlib import Path

PORTFOLIO_PY = Path("src/core/portfolio.py")
APP_JS = Path("src/web/static/js/app.js")
AUDITOR_SH = Path("scripts/auditoria/1_auditar_cartera_shield.py")
LOGIC_MD = Path("docs/LOGIC.md")
ARCH_MD = Path("docs/ARCH.md")
REGISTRY_MD = Path("docs/ID_REGISTRY.md")

O_FAV_VISITA = 2.35      # Deportivo Toluca (favorito visitante — caso de fuego fáctico)
O_EMPATE = 3.60
O_UND_LOCAL = 2.90       # Tigres UANL


def _fuente(archivo: Path) -> str:
    """Lectura verbatim del artefacto auditado (fail-loud si no existe)."""
    assert archivo.exists(), f"Artefacto ausente para auditoría: {archivo}"
    return archivo.read_text(encoding="utf-8")


def _candidato(strategy_code: str) -> dict:
    """Fixture fáctico del caso de fuego: Tigres UANL vs Deportivo Toluca (favorito foráneo)."""
    return {
        "id_partido": "TEST-TIGRES-TOLUCA",
        "partido_nombre": "Tigres UANL vs Deportivo Toluca",
        "horario": "Viernes 21:00",
        "strategy_code": strategy_code,
        "strategy_nombre": "Favorito Visitante con Cobertura en Tablas",
        "ev_neto_roi": 0.314,
        "psi_downside": 0.05,
        "delta_epist": 0.03,
        "psi_epist": 0.97,
        "phi_lead2": 0.42,
        "odd_fav": O_FAV_VISITA,
        "odd_emp": O_EMPATE,
        "odd_und": O_UND_LOCAL,
        "fav_name": "Deportivo Toluca",
        "und_name": "Tigres UANL",
        "prob_fav": 55.9,
        "prob_emp": 23.2,
        "prob_und": 20.9,
        "pago_anticipado": True,
        "alpha": 0.314,
    }


def _orden(strategy_code: str, bankroll: float = 200.0):
    """Despacha UNA orden por el motor real (`PortfolioEngine.build_plan`)."""
    from src.core.portfolio import PortfolioEngine

    plan = PortfolioEngine.build_plan(
        [_candidato(strategy_code)], bankroll=bankroll, mode="BANKROLL", total_jornada=9
    )
    assert len(plan.ordenes_ejecucion_partidos) == 1
    return plan.ordenes_ejecucion_partidos[0]


class AbstractTestInvarianteVIII11SimetriaH1H2(ABC):
    """Juez Abstracto de la simetría canónica de cobertura en la Familia H."""

    @abstractmethod
    def build_order(self, strategy_code: str, bankroll: float = 200.0):
        """Materializa la orden a auditar (implementación concreta: motor real)."""

    def test_h2_ataque_en_favorito_visitante_y_seguro_en_empate(self):
        """[INVARIANTE VIII-11] H2: ataque = favorito visitante (α_V > 0); seguro = Empate (V=0)."""
        orden = self.build_order("QBE-H2")
        seguro = orden.boletos.boleto_1_seguro
        ataque = orden.boletos.boleto_2_ganancia
        a_i = orden.boletos.inversion_partido_A_i

        assert orden.estrategia_seleccionada.codigo == "QBE-H2", "El código canónico viaja puro"

        # 1. Boleto 1 (SEGURO) = Empate @ O_Empate
        assert "Empate" in seguro.seleccion, f"🚨 Pierna de recuperación invertida: {seguro.seleccion!r}"
        assert seguro.momio == O_EMPATE

        # 2. Boleto 2 (ATAQUE/GANANCIA) = Gana Favorito Visitante @ O_Fav
        assert "Deportivo Toluca" in ataque.seleccion, (
            f"🚨 El ataque no juega al favorito: {ataque.seleccion!r}"
        )
        assert ataque.momio == O_FAV_VISITA

        # 3. V = 0: el seguro reintegra el 100% del capital en tablas (Invarianza 1 del Auditor)
        assert abs(seguro.monto_mxn * seguro.momio - a_i) <= 0.08, (
            f"Violación V=0: {seguro.monto_mxn} × {seguro.momio} != {a_i}"
        )

        # 4. Ganancia principal = cobro del ATAQUE (nunca el del empate)
        assert ataque.monto_mxn == round(a_i - seguro.monto_mxn, 2), "Los boletos no agotan A_i"
        assert orden.proyecciones.ganancia_neta_principal_mxn == round(
            ataque.monto_mxn * ataque.momio - a_i, 2
        )
        assert orden.proyecciones.ganancia_neta_principal_mxn > 0.0, (
            "🚨 El favorito visitante exhibe α_V > 0: la ganancia principal debe ser positiva"
        )
        assert orden.proyecciones.resultado_tablas_mxn == a_i
        assert orden.proyecciones.perdida_maxima_posible_mxn == a_i

    def test_simetria_estricta_h1_h2_misma_estructura_de_capital(self):
        """La cobertura es ÚNICA: ante momios idénticos, H1 y H2 estructuran el capital igual."""
        h2 = self.build_order("QBE-H2")
        h1 = self.build_order("QBE-H1")

        assert h1.boletos.boleto_1_seguro.seleccion == "Empate"
        assert h2.boletos.boleto_1_seguro.seleccion == "Empate"

        for campo in ("momio", "monto_mxn"):
            seg_h1 = getattr(h1.boletos.boleto_1_seguro, campo)
            seg_h2 = getattr(h2.boletos.boleto_1_seguro, campo)
            ata_h1 = getattr(h1.boletos.boleto_2_ganancia, campo)
            ata_h2 = getattr(h2.boletos.boleto_2_ganancia, campo)
            assert seg_h1 == seg_h2, f"Asimetría en el seguro ({campo}): H1={seg_h1} vs H2={seg_h2}"
            assert ata_h1 == ata_h2, f"Asimetría en el ataque ({campo}): H1={ata_h1} vs H2={ata_h2}"

        assert h1.boletos.boleto_2_ganancia.momio == O_FAV_VISITA
        assert h1.boletos.boleto_1_seguro.momio == O_EMPATE
        assert (
            h1.proyecciones.ganancia_neta_principal_mxn
            == h2.proyecciones.ganancia_neta_principal_mxn
        )

    def test_piso_de_ventanilla_se_ancla_al_momio_del_empate(self):
        """[LN-QBE-071] El clamping re-deriva A_i = $2.00 · O_Empate (jamás O_fav)."""
        orden = self.build_order("QBE-H2", bankroll=20.0)
        seguro = orden.boletos.boleto_1_seguro

        assert seguro.monto_mxn == 2.00, "[LN-QBE-071] El seguro debe clavar el piso de $2.00 MXN"
        assert seguro.momio == O_EMPATE
        assert orden.boletos.inversion_partido_A_i == round(2.00 * O_EMPATE, 2), (
            "🚨 El clamping ancló el seguro al momio del FAVORITO (Diseño B derogado)"
        )
        assert abs(seguro.monto_mxn * seguro.momio - orden.boletos.inversion_partido_A_i) <= 0.01

    def test_ln_qbe_083_doble_cobro_es_la_ley_sellada(self):
        """[LN-QBE-083] Doble Cobro: B_prio·O_fav ⟹ ROI_doble = (1 − 1/O_emp)·O_fav."""
        orden = self.build_order("QBE-H2+")
        seguro = orden.boletos.boleto_1_seguro
        ataque = orden.boletos.boleto_2_ganancia

        assert "+ PA" in ataque.seleccion, "La cláusula +PA viaja en la pierna de ATAQUE"
        assert "+ PA" not in seguro.seleccion, "La recuperación no porta Pago Anticipado"
        assert orden.estrategia_seleccionada.linea_promocional == "Pago Anticipado (+2 goles)"

        neta_ley = round(ataque.monto_mxn * ataque.momio, 2)
        assert abs(orden.proyecciones.freeroll_doble_ganancia_mxn - neta_ley) <= 0.05, (
            f"🚨 Doble cobro fuera de ley: {orden.proyecciones.freeroll_doble_ganancia_mxn} vs {neta_ley}"
        )
        roi_ley = (1.0 - 1.0 / seguro.momio) * ataque.momio * 100.0
        assert abs(orden.proyecciones.freeroll_roi_porcentaje - roi_ley) <= 0.15, (
            f"🚨 ROI fuera de ley: {orden.proyecciones.freeroll_roi_porcentaje} vs {roi_ley}"
        )

    def test_ley_del_vault_conectada_y_auditor_sin_hardcode(self):
        """V-1: `calcular_dutching_v0` deja de ser ley huérfana; V-5: el auditor no hardcodea."""
        fuente = _fuente(PORTFOLIO_PY)
        arbol = ast.parse(fuente)

        importados = {
            alias.name for nodo in ast.walk(arbol) if isinstance(nodo, ast.ImportFrom)
            for alias in nodo.names
        }
        assert "calcular_dutching_v0" in importados, (
            "🚨 [VAULT-CORE-070-DUTCHING] no está importada: la ley volvió a quedar huérfana (V-1)"
        )
        invocadas = {
            nodo.func.id for nodo in ast.walk(arbol)
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
        }
        assert "calcular_dutching_v0" in invocadas, (
            "🚨 build_plan no delega la asignación de la Familia H a la ley sellada del Vault"
        )

        inicio = fuente.index('if "H2" in code:')
        fin = fuente.index('elif "H1" in code:', inicio)
        rama_h2 = fuente[inicio:fin]
        assert "b1_momio = o_emp" in rama_h2, "🚨 La rama H2 no ancla el seguro al Empate"
        assert "b2_momio = o_fav" in rama_h2, "🚨 La rama H2 no ancla el ataque al Favorito"
        assert "b1_momio = o_fav" not in rama_h2, "🚨 Inversión de piernas del Diseño B reintroducida"

        auditor = _fuente(AUDITOR_SH)
        assert "b1.get('seleccion'" in auditor, (
            "🚨 El auditor independiente volvió a hardcodear el rótulo de cobertura (V-5)"
        )

    def test_ui_exhibe_el_capital_certificado_por_el_motor(self):
        """[GOVERNANCE-01] Paridad backend↔pantalla: el renglón 2 lee el capital del motor."""
        js = _fuente(APP_JS)
        assert "Cobertura en Empate:</strong> Recuperación de $${inv.toFixed(2)} MXN" in js, (
            "🚨 La ventanilla re-deriva el capital recuperado en el cliente"
        )

    def test_catalogo_canonico_y_doctrina_anclada(self):
        """Tareas 2/4: catálogo coherente + [INVARIANTE VIII-11] anclada en la Base de Gobierno."""
        from src.core.catalog import STRATEGY_CATALOG

        h2 = STRATEGY_CATALOG["QBE-H2"]
        assert h2.familia == "H"
        assert "Favorito Visitante" in h2.nombre_oficial
        assert "P_Visita" in h2.formula_ev
        assert h2.rol_boleto_1.startswith("Seguro en Empate")
        assert h2.rol_boleto_2.startswith("Ganancia en Favorito Visitante")

        logic = _fuente(LOGIC_MD)
        assert "Invariante VIII-11" in logic, "Falta la Invariante VIII-11 en docs/LOGIC.md"
        assert "Ataque: Gana Favorito Visitante" in logic
        assert "Seguro: Empate" in logic

        arch = _fuente(ARCH_MD)
        assert "`calcular_dutching_v0` gobierna la asignación de capital de la Familia H" in arch, (
            "Falta el gobierno de la ley del Vault sobre la Familia H en docs/ARCH.md"
        )
        assert "VAR-H2-SIMETRIA-CANONICA" in _fuente(REGISTRY_MD), (
            "Falta la ficha de cierre VAR-H2-SIMETRIA-CANONICA en docs/ID_REGISTRY.md"
        )


class TestInvarianteVIII11SimetriaH1H2(AbstractTestInvarianteVIII11SimetriaH1H2):
    """Implementación concreta: el motor de producción (`PortfolioEngine.build_plan`)."""

    def build_order(self, strategy_code: str, bankroll: float = 200.0):
        return _orden(strategy_code, bankroll=bankroll)


