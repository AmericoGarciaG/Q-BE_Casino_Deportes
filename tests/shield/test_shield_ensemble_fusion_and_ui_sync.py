# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — JUEZ DE LA FUSIÓN CONVEXA DEL SÍMPLEX SOBERANO Y SU SINCRONÍA CON LA CARTELERA
Gobierno: `docs/LOGIC.md` [LN-QBE-104] / `docs/DIRGEN_VAULT.md` [VAULT-CORE-005] /
          `docs/ARCH.md` [ARCH-1.6.22] / `docs/DESIGN.md` [DES-QBE-067]

Régimen declarado (Dual-Track honesto):
* **[DIRGEN-STRICT]** — ley de mezcla `w_H2H = min(0.25, N · 0.05)`, métrica `Δ_epist(∞)` y puente
  de persistencia `src/storage/distribution_sync.py` (`sovereign_distributions.epistemic_delta`).
* **[DBBD-FUNGIBLE]** — cartelera: badge `SIN EVALUAR` del acordeón forense y filtro anti-cuarentena
  `#chk-excluir-vetados` del visor de backtesting.

Cinco defectos legislados que este Juez clausura:
1. **Generador C decorativo:** el kernel H2H se calculaba para `Δ_epist` pero JAMÁS mezclaba el
   símplex publicado — el ensemble era una promesa sin materialización.
2. **`epistemic_delta` maquillado:** la columna 3NF persistía el `ratio` λ_max/λ_min (una magnitud
   de tasas, sin relación con la discrepancia entre generadores) en lugar de `Δ_epist`.
3. **Badge `0/0 evaluadas`:** una dimensión declarada sin una sola variable evaluada exhibía un
   contador que fingía medición en vez de declarar `SIN EVALUAR`.
4. **Cartelera sin filtro anti-cuarentena:** los partidos vetados (EPIST 🔴, `Δ_epist > 0.12`)
   inflaban el acierto de Q-BE con evidencia que la cartera ya había negado.
5. **Universo implícito:** tras filtrar, `#bt-estado` no declaraba qué universo se estaba contando.

[GOV-TEST-01] Aislamiento hermético: cero red, cero navegador, cero base de datos persistente.
La bóveda 3NF se materializa en un motor `sqlite://` en memoria con el metamodelo real.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parents[2]
APP_JS = RAIZ / "src" / "web" / "static" / "js" / "app.js"
INDEX_HTML = RAIZ / "src" / "web" / "templates" / "index.html"
THEME_CSS = RAIZ / "src" / "web" / "static" / "css" / "theme.css"

# ── Fixture fáctica: registro publicable con ventana H2H multianual (cero invención) ────────────
_REGISTRO_BASE = {
    "match_id": "TEST-FUSION-104",
    "competition_id": "MEX_LIGAMX",
    "home_team_slug": "puebla",
    "away_team_slug": "atlante",
    "home_team_stats": {
        "pj": 8, "gf": 14, "gc": 6,
        "xg": 12.8, "xga": 8.0, "sot": 40, "sota": 32, "possession": 53.5,
    },
    "away_team_stats": {
        "pj": 8, "gf": 9, "gc": 12,
        "xg": 8.8, "xga": 12.0, "sot": 24, "sota": 32, "possession": 46.5,
    },
    "home_split_stats": {"pj": 4},
    "away_split_stats": {"pj": 4},
    # Dominio local sostenido: el Generador C publica un símplex materialmente distinto del
    # paramétrico, de modo que la mezcla es OBSERVABLE (Δ(∞) > 0 y w_H2H saturado en N = 4).
    "h2h_matches": [
        {"dias_antiguedad": 120, "goles_local": 3, "goles_visita": 0},
        {"dias_antiguedad": 200, "goles_local": 2, "goles_visita": 0},
        {"dias_antiguedad": 300, "goles_local": 4, "goles_visita": 1},
        {"dias_antiguedad": 420, "goles_local": 2, "goles_visita": 1},
    ],
}


class _GatewayMemoria:
    """Gateway hermético sobre `sqlite://` con el metamodelo REAL (`Base.metadata`)."""

    def __init__(self) -> None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from src.storage.models import Base

        self._engine = create_engine("sqlite://")
        Base.metadata.create_all(self._engine)
        self._sesiones = sessionmaker(bind=self._engine)

    def read_session(self):
        from contextlib import contextmanager

        @contextmanager
        def _ctx():
            sesion = self._sesiones()
            try:
                yield sesion
            finally:
                sesion.close()

        return _ctx()

    def write_transaction(self):
        from contextlib import contextmanager

        @contextmanager
        def _ctx():
            sesion = self._sesiones()
            try:
                yield sesion
                sesion.commit()
            except Exception:
                sesion.rollback()
                raise
            finally:
                sesion.close()

        return _ctx()


def _kernel_sintetico() -> SimpleNamespace:
    """Generador C mínimo con la MISMA superficie que consume la ley de mezcla."""
    return SimpleNamespace(p_local=0.62, p_empate=0.18, p_visita=0.20)



# ── Inversión 1: la ley de mezcla es monótona, acotada y con identidad en N = 0 ─────────────────
def test_ln_qbe_104_ley_de_mezcla_del_peso_h2h():
    """[LN-QBE-104 · VAULT-CORE-005] `w_H2H = min(0.25, N · 0.05)`.

    La ley es monótona no decreciente (cada duelo adicional aporta 0.05), satura en el tope
    fiduciario 0.25 y se anula exactamente en N = 0 (identidad: la mezcla no toca el Generador A).
    Evidencia ilegible NO inventa peso: degrada a 0.0.
    """
    from src.core.sovereign_pipeline import (
        PESO_H2H_POR_DUELO,
        PESO_H2H_TOPE,
        calcular_peso_h2h,
    )

    assert PESO_H2H_POR_DUELO == 0.05
    assert PESO_H2H_TOPE == 0.25
    assert calcular_peso_h2h(0) == 0.0
    assert calcular_peso_h2h(1) == pytest.approx(0.05, abs=1e-12)
    assert calcular_peso_h2h(2) == pytest.approx(0.10, abs=1e-12)
    assert calcular_peso_h2h(5) == pytest.approx(0.25, abs=1e-12)
    # Saturación: el kernel empírico jamás desplaza más de una cuarta parte del símplex.
    for duelos in (6, 9, 40):
        assert calcular_peso_h2h(duelos) == pytest.approx(0.25, abs=1e-12)
    # Monotonía estricta hasta el tope (ley reproducible, cero escalón arbitrario).
    pesos = [calcular_peso_h2h(n) for n in range(0, 7)]
    assert pesos == sorted(pesos)
    # Degradación honesta: entradas ilegibles o negativas se declaran como ausencia de evidencia.
    assert calcular_peso_h2h(-3) == 0.0
    assert calcular_peso_h2h(None) == 0.0
    assert calcular_peso_h2h("no-numerico") == 0.0


# ── Inversión 2: la fusión es convexa, cierra Δ² y Δ(∞) es la norma infinito ───────────────────
def test_ln_qbe_104_fusion_convexa_y_delta_norma_infinito():
    """[LN-QBE-104] `P_hib = w_Liga·P_A + w_H2H·P_C` habita el símplex y `Δ(∞) = max_k|…|`.

    Se certifica: cierre Σ ≡ 1, acotamiento por componente (min ≤ P_hib ≤ max), recuperación
    exacta de los pesos, identidad con `kernel=None` (Ley Zero-H2H) y que la métrica publicada es
    la NORMA INFINITO —no la TVD— acotando a ésta por arriba.
    """
    from src.core.sovereign_pipeline import (
        DELTA_EPISTEMICO_SIN_EVIDENCIA,
        fusionar_simplex_con_h2h,
    )

    poisson = {"p_local": 0.40, "p_empate": 0.30, "p_visitante": 0.30}
    kernel = _kernel_sintetico()
    fusion = fusionar_simplex_con_h2h(poisson, kernel=kernel, n_duelos=4)

    peso_h2h = 0.20  # min(0.25, 4 · 0.05)
    assert fusion["peso_h2h"] == pytest.approx(peso_h2h, abs=1e-12)
    assert fusion["peso_liga"] == pytest.approx(1.0 - peso_h2h, abs=1e-12)

    # 1) Combinación convexa exacta componente a componente + acotamiento entre generadores.
    for clave_hibrida, p_a, p_c in (
        ("p_local", poisson["p_local"], kernel.p_local),
        ("p_empate", poisson["p_empate"], kernel.p_empate),
        ("p_visitante", poisson["p_visitante"], kernel.p_visita),
    ):
        esperado = (1.0 - peso_h2h) * p_a + peso_h2h * p_c
        assert fusion[clave_hibrida] == pytest.approx(esperado, abs=1e-12)
        assert min(p_a, p_c) - 1e-12 <= fusion[clave_hibrida] <= max(p_a, p_c) + 1e-12

    # 2) Cierre del símplex.
    suma = fusion["p_local"] + fusion["p_empate"] + fusion["p_visitante"]
    assert suma == pytest.approx(1.0, abs=1e-12)

    # 3) Δ(∞) = max_k |P_A − P_C| ≥ TVD (la norma infinito acota la variación total).
    delta_infinito = max(
        abs(poisson["p_local"] - kernel.p_local),
        abs(poisson["p_empate"] - kernel.p_empate),
        abs(poisson["p_visitante"] - kernel.p_visita),
    )
    tvd = 0.5 * (
        abs(poisson["p_local"] - kernel.p_local)
        + abs(poisson["p_empate"] - kernel.p_empate)
        + abs(poisson["p_visitante"] - kernel.p_visita)
    )
    assert fusion["delta_epist"] == pytest.approx(delta_infinito, abs=1e-12)
    assert tvd <= delta_infinito + 1e-12
    assert 0.0 < delta_infinito <= 1.0

    # 4) Ley Zero-H2H: sin kernel (o con N = 0) la fusión es la IDENTIDAD y Δ cae al piso R-1.
    identidad = fusionar_simplex_con_h2h(poisson, kernel=None, n_duelos=4)
    assert identidad["p_local"] == poisson["p_local"]
    assert identidad["p_empate"] == poisson["p_empate"]
    assert identidad["p_visitante"] == poisson["p_visitante"]
    assert identidad["peso_h2h"] == 0.0 and identidad["peso_liga"] == 1.0
    assert identidad["delta_epist"] == DELTA_EPISTEMICO_SIN_EVIDENCIA

    sin_duelos = fusionar_simplex_con_h2h(poisson, kernel=kernel, n_duelos=0)
    assert sin_duelos["p_local"] == poisson["p_local"]
    assert sin_duelos["peso_h2h"] == 0.0
    assert sin_duelos["delta_epist"] == DELTA_EPISTEMICO_SIN_EVIDENCIA



# ── Inversión 3: el orquestador PUBLICA el símplex híbrido y la Δ(∞) real ──────────────────────
def test_ln_qbe_104_pipeline_publica_simplex_hibrido_y_delta_real():
    """[LN-QBE-104 · ARCH-1.6.22] El símplex publicado es la mezcla, no el Generador A puro.

    Se reconstruye la ley desde la traza forense (`simplex_poisson` + `kernel_h2h_empirico`) y se
    exige identidad con el contrato de salida: cualquier futura mutación que devuelva el Poisson
    puro a la vitrina rompe este Juez. `intensidades["ratio"]` permanece intacta (evidencia 3NF
    sellada [LN-QBE-102]) y la TVD sigue publicada como `discrepancia_epist`.
    """
    from src.core.sovereign_pipeline import generar_distribucion_soberana

    salida = generar_distribucion_soberana("TEST-FUSION-104", _REGISTRO_BASE)
    traza = salida.audit_trace

    poisson = traza.simplex_poisson
    kernel = traza.kernel_h2h_empirico
    peso_h2h = kernel["peso_h2h"]

    assert peso_h2h == pytest.approx(min(0.25, len(_REGISTRO_BASE["h2h_matches"]) * 0.05), abs=1e-6)
    assert kernel["peso_liga"] == pytest.approx(1.0 - peso_h2h, abs=1e-6)

    # 1) El contrato de salida ES la combinación convexa reconstruida desde la traza.
    pares = (
        (salida.p_local, poisson["p_1"], kernel["p_local"]),
        (salida.p_empate, poisson["p_X"], kernel["p_empate"]),
        (salida.p_visitante, poisson["p_2"], kernel["p_visita"]),
    )
    for publicado, p_a, p_c in pares:
        esperado = (1.0 - peso_h2h) * p_a + peso_h2h * p_c
        assert publicado == pytest.approx(esperado, abs=1e-6)
        assert min(p_a, p_c) - 1e-6 <= publicado <= max(p_a, p_c) + 1e-6

    # 2) La mezcla es OBSERVABLE: el símplex publicado NO es el paramétrico puro.
    assert abs(salida.p_local - poisson["p_1"]) > 1e-4

    # 3) Cierre del símplex publicado.
    assert salida.p_local + salida.p_empate + salida.p_visitante == pytest.approx(1.0, abs=1e-9)

    # 4) Δ(∞) publicada == norma infinito reconstruida, en contrato Y en traza.
    esperado_infinito = max(
        abs(poisson["p_1"] - kernel["p_local"]),
        abs(poisson["p_X"] - kernel["p_empate"]),
        abs(poisson["p_2"] - kernel["p_visita"]),
    )
    assert salida.epistemic_delta == pytest.approx(esperado_infinito, abs=1e-6)
    assert traza.epistemic_delta == pytest.approx(esperado_infinito, abs=1e-6)
    assert 0.0 <= salida.epistemic_delta <= 1.0

    # 5) La TVD sellada [LN-QBE-020-C] sigue publicada y queda acotada por la norma infinito.
    assert traza.discrepancia_epist == pytest.approx(salida.delta_epist, abs=1e-12)
    assert salida.delta_epist <= salida.epistemic_delta + 1e-6

    # 6) Evidencia 3NF intacta: el `ratio` λ_max/λ_min permanece en `intensidades`.
    ratio = traza.intensidades["ratio"]
    assert ratio == pytest.approx(round(salida.lambda_home / salida.lambda_away, 2), abs=1e-12)
    assert abs(ratio - salida.epistemic_delta) > 1e-3, (
        "Δ_epist(∞) jamás puede coincidir con el `ratio` de tasas: son magnitudes distintas."
    )


# ── Inversión 4: la bóveda 3NF persiste la Δ real (y deja de maquillar el ratio) ───────────────
def test_ln_qbe_104_distribution_sync_persiste_delta_real():
    """[VAULT-DATA-002 · LN-QBE-104] `sovereign_distributions.epistemic_delta` = Δ_epist(∞).

    El puente de persistencia lee el valor del contrato → traza → piso R-1, lo acota a [0, 1] y
    JAMÁS cae al `ratio` λ_max/λ_min. Se certifica el ciclo completo sobre el metamodelo real en
    memoria: orquestador → sincronización → fila 3NF.
    """
    from src.storage.distribution_sync import _delta_epistemico_publicado

    # a) Pureza del puente: orden de lectura, acotamiento y piso de ignorancia.
    assert _delta_epistemico_publicado(SimpleNamespace(epistemic_delta=0.37), {}) == pytest.approx(0.37)
    assert _delta_epistemico_publicado(SimpleNamespace(), {"epistemic_delta": 0.44}) == pytest.approx(0.44)
    assert _delta_epistemico_publicado(SimpleNamespace(), {}) == pytest.approx(0.02)
    assert _delta_epistemico_publicado(SimpleNamespace(epistemic_delta=None), {}) == pytest.approx(0.02)
    assert _delta_epistemico_publicado(SimpleNamespace(epistemic_delta=True), {}) == pytest.approx(0.02)
    assert _delta_epistemico_publicado(SimpleNamespace(epistemic_delta=1.73), {}) == pytest.approx(1.0)
    assert _delta_epistemico_publicado(SimpleNamespace(epistemic_delta=-0.5), {}) == pytest.approx(0.0)
    # El contrato de salida gana a la traza (una sola verdad, la del generador).
    assert _delta_epistemico_publicado(
        SimpleNamespace(epistemic_delta=0.11), {"epistemic_delta": 0.90}
    ) == pytest.approx(0.11)

    # b) Ciclo real de persistencia sobre el metamodelo de producción.
    from src.core.sovereign_pipeline import generar_distribucion_soberana
    from src.storage.distribution_sync import sincronizar_distribuciones_soberanas_partidos
    from src.storage.models import Competition, Match, SovereignDistribution

    gw = _GatewayMemoria()
    with gw.write_transaction() as tx:
        tx.add(Competition(
            id="MEX_LIGAMX", name="Liga MX", country="México",
            macro_mu_liga=2.65, macro_gamma_home=0.15,
        ))
        tx.add(Match(
            id="TEST-FUSION-104", competition_id="MEX_LIGAMX", matchday_num=9,
            home_team_slug="puebla", away_team_slug="atlante", status="SCHEDULED",
        ))

    contrato = generar_distribucion_soberana("TEST-FUSION-104", _REGISTRO_BASE)
    resultado = sincronizar_distribuciones_soberanas_partidos([_REGISTRO_BASE], gateway=gw)
    assert resultado["exitosos"] == 1

    with gw.read_session() as sesion:
        fila = sesion.query(SovereignDistribution).filter_by(match_id="TEST-FUSION-104").one()
        persistido = fila.epistemic_delta
        ratio_traza = fila.audit_trace_json["intensidades"]["ratio"]
        delta_traza = fila.audit_trace_json["epistemic_delta"]
        simplex_poisson = fila.audit_trace_json["simplex_poisson"]
        kernel_traza = fila.audit_trace_json["kernel_h2h_empirico"]

    # La columna 3NF espeja el contrato de salida, no una magnitud de tasas.
    assert persistido == pytest.approx(contrato.epistemic_delta, abs=1e-9)
    assert delta_traza == pytest.approx(contrato.epistemic_delta, abs=1e-9)
    assert 0.0 <= persistido <= 1.0
    assert abs(persistido - ratio_traza) > 1e-3, (
        "La columna `epistemic_delta` no puede volver a espejar el `ratio` λ_max/λ_min."
    )
    # Procedencia de la fusión auditable en la bóveda: ambos generadores quedan publicados.
    assert set(simplex_poisson) == {"p_1", "p_X", "p_2"}
    assert kernel_traza["peso_h2h"] > 0.0



# ── Utilidades de lectura estática (la cartelera se certifica sin navegador) ────────────────────
def _fuente_app() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _cuerpo_funcion(fuente: str, nombre: str) -> str:
    """Cuerpo balanceado de `function nombre(...) { … }` (cero expresiones regulares frágiles)."""
    marca = f"function {nombre}("
    assert marca in fuente, f"La función `{nombre}` desapareció de la cartelera."
    apertura = fuente.index("{", fuente.index(marca))
    profundidad = 0
    for posicion in range(apertura, len(fuente)):
        if fuente[posicion] == "{":
            profundidad += 1
        elif fuente[posicion] == "}":
            profundidad -= 1
            if profundidad == 0:
                return fuente[apertura:posicion + 1]
    raise AssertionError(f"La función `{nombre}` no cierra su bloque.")


# ── Inversión 5: filtro anti-cuarentena (presentación pura, jamás muta la bóveda) ──────────────
def test_des_qbe_067_filtro_anti_cuarentena_de_la_cartelera():
    """[DES-QBE-067 · LN-QBE-104] La cartelera excluye los partidos vetados por Cuarentena.

    Vetado ⟺ `atribucion_factorial.semaforos.epist == "ROJO"` ([ARCH-1.4.42]: 🟢 ≤ 0.03,
    🟡 ≤ 0.12, 🔴 > 0.12). El filtro es de PRESENTACIÓN: recomputa los KPI desde los CONTEOS
    ENTEROS del subconjunto, declara el universo efectivo en `#bt-estado` y NUNCA reescribe
    `backtestingReportCache` ([GOVERNANCE-01]: cero cifras maquilladas).
    """
    fuente = _fuente_app()
    html = INDEX_HTML.read_text(encoding="utf-8")
    css = THEME_CSS.read_text(encoding="utf-8")

    # a) El conmutador existe, está rotulado y declara su criterio fáctico.
    assert 'id="chk-excluir-vetados"' in html
    assert 'for="chk-excluir-vetados"' in html
    assert 'class="bt-filtro-vetados"' in html
    assert "EPIST" in html and "0.12" in html
    assert "PRESENTACI" in html, "El rótulo debe declarar que el filtro NO reescribe la bóveda."
    assert ".bt-filtro-vetados" in css

    # b) La semántica del veto es la del semáforo EPIST publicado, no una heurística local.
    assert 'const SEMAFORO_EPIST_VETO = "ROJO";' in fuente
    cuerpo_veto = _cuerpo_funcion(fuente, "_partidoVetadoBacktesting")
    assert "atribucion_factorial" in cuerpo_veto and "semaforos" in cuerpo_veto
    assert "epist" in cuerpo_veto and "SEMAFORO_EPIST_VETO" in cuerpo_veto

    # c) El conmutador está cableado al re-pintado sin refetch.
    cuerpo_init = fuente[fuente.index("function initVisorBacktesting("):]
    cuerpo_init = cuerpo_init[:cuerpo_init.index("function cargarVisorBacktesting(")]
    assert "chk-excluir-vetados" in cuerpo_init
    assert "addEventListener(\"change\"" in cuerpo_init or "addEventListener('change'" in cuerpo_init
    assert "_pintarVisorBacktesting" in cuerpo_init

    # d) Universo efectivo: filtra por jornada y JAMÁS muta la caché certificada.
    cuerpo_universo = _cuerpo_funcion(fuente, "_universoCalibracion")
    assert "backtestingReportCache" in cuerpo_universo
    assert "filter(" in cuerpo_universo and "_partidoVetadoBacktesting" in cuerpo_universo
    assert "_agregadoTriadaBacktesting" in cuerpo_universo
    assert "backtestingReportCache =" not in cuerpo_universo, "El filtro no puede reescribir la bóveda."
    assert "filtroInerte" in cuerpo_universo, "0 vetados ⇒ agregado servido tal cual (idempotencia)."

    # e) El estado declara el universo leído y los KPI se recomputan desde el subconjunto.
    cuerpo_estado = _cuerpo_funcion(fuente, "_estadoLecturaBacktesting")
    assert "Filtro anti-cuarentena" in cuerpo_estado
    assert "universo efectivo" in cuerpo_estado
    assert "excluidos" in cuerpo_estado
    cuerpo_pintar = _cuerpo_funcion(fuente, "_pintarVisorBacktesting")
    assert "pintarResumenBacktesting(universo.resumen)" in cuerpo_pintar
    assert "pintarMesoBacktesting(universo.jornadas" in cuerpo_pintar
    assert 'getElementById("bt-estado")' in cuerpo_pintar

    # f) La parrilla micro y la jornada expandida consumen el universo EFECTIVO.
    cuerpo_micro = _cuerpo_funcion(fuente, "mostrarMicroJornadaBacktesting")
    assert "backtestingUniversoActual" in cuerpo_micro
    # g) El agregado de la triada se re-deriva de conteos ENTEROS (nada de promedios heredados).
    cuerpo_agregado = _cuerpo_funcion(fuente, "_agregadoTriadaBacktesting")
    assert "_conteosTriadaBacktesting" in cuerpo_agregado
    assert "_brierBacktesting" in cuerpo_agregado and "_alphaBacktesting" in cuerpo_agregado
    for clave in ("total_p_max", "total_p_mid", "total_p_low", "masa_cobertura_pct"):
        assert clave in cuerpo_agregado, f"El agregado exhibido carece de `{clave}`."



# ── Inversión 6: el badge declara `SIN EVALUAR` en vez de fingir «0/0 evaluadas» ───────────────
def test_des_qbe_067_badge_sin_evaluar_sin_maquillaje():
    """[DES-QBE-067 · GOVERNANCE-01] Una dimensión sin evidencia evaluada NO finge medición.

    `tiene_datos` por sí solo no basta: se exige coherencia aritmética (total > 0, evaluadas > 0,
    evaluadas ≤ total). El badge se construye con `createElement`/`textContent` (cero hidratación
    por marcado crudo) y la etiqueta de ausencia es exactamente `SIN EVALUAR`.
    """
    fuente = _fuente_app()
    cuerpo = _cuerpo_funcion(fuente, "_badgeDimension44")

    assert "createElement(\"span\")" in cuerpo or "createElement('span')" in cuerpo
    assert "textContent" in cuerpo
    assert "innerHTML" not in cuerpo, "El badge jamás se hidrata por marcado crudo."
    assert '"SIN EVALUAR"' in cuerpo

    # Guarda de coherencia aritmética: las tres condiciones, no una.
    assert "total > 0" in cuerpo
    assert "evaluadas > 0" in cuerpo
    assert "evaluadas <= total" in cuerpo
    assert "Number.isFinite(evaluadas)" in cuerpo and "Number.isFinite(total)" in cuerpo
    # La etiqueta «evaluadas» SOLO se emite bajo la guarda `conDatos`.
    assert "conDatos ?" in cuerpo
    # Bicolor: clase de evaluada y clase de fase 6 (no evaluada).
    assert "badge-dim-evaluada" in cuerpo and "badge-dim-fase6" in cuerpo
