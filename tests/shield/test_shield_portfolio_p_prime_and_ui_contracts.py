# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DE CONTRATO P' CONTRAÍDO Y RÓTULOS DE PRESENTACIÓN
Audita:
- [LN-QBE-083-B] Rótulo único de ausencia de cobertura en familias DIRECTAS (QBE-D1 / QBE-D2).
- [ARCH-1.4.16-B] Horario fáctico (`horario_evento`) en el Resumen de Asignación.
- [DES-QBE-060] P' contraído por pierna (`prob_qbe`) y Bloque de Transparencia 360° preservados.
- [GOV-TEST-01] Hermeticidad: cero red, cero DB, cero mocks en producción (lectura de fuente
  + DTOs Pydantic evaluados en memoria).

Gobierno: expediente de varianza `scratch/DIRGEN_VARIANCE_REQUEST_VAR-10.md` (Dictamen
VARIANZA-10 §1.1 ALT-1, §1.2 alcance acotado a Tramos 3–4, §1.3 congelación ALT-5-A).
Régimen: [HÍBRIDO DUAL-TRACK] — contratos Pydantic (inmutables) + presentación (fungible).

Nota de diseño: el rótulo NO se re-implementa en el Juez. El Juez EXTRAE la cadena real de
decisión publicada por el frontend y la evalúa contra los 9 códigos canónicos; si la pantalla y
la legislación divergen, el Juez falla. Cero etiquetas ni cifras inventadas por el test.
"""

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

APP_JS = Path("src/web/static/js/app.js")
PORTFOLIO_PY = Path("src/core/portfolio.py")
MARKETS_PY = Path("src/web/routes/markets.py")
LOGIC_MD = Path("docs/LOGIC.md")
ARCH_MD = Path("docs/ARCH.md")
REGISTRY_MD = Path("docs/ID_REGISTRY.md")

# Las 9 familias estratégicas canónicas del triaje determinista.
CODIGOS_CANONICOS = [
    "QBE-D1", "QBE-D2", "QBE-H1", "QBE-H2", "QBE-R1", "QBE-R2", "QBE-C1", "QBE-C2", "QBE-00"
]


def _fuente(archivo: Path) -> str:
    """Lectura verbatim del artefacto auditado (fail-loud si no existe)."""
    assert archivo.exists(), f"Artefacto ausente para auditoría: {archivo}"
    return archivo.read_text(encoding="utf-8")


def _bloque_cobertura_resumen_asignacion() -> str:
    """Extrae verbatim el bloque que resuelve el rótulo de cobertura del Resumen de Asignación."""
    code = _fuente(APP_JS)
    inicio = code.index("let coberturaHtml =")
    fin = code.index("const horarioHtml", inicio)
    return code[inicio:fin]


_PATRON_RAMA = re.compile(
    r'(?:if|else\s+if)\s*\((.*?)\)\s*\{\s*coberturaHtml\s*=\s*`([^`]*)`;', re.DOTALL
)


def _ramas_de_cobertura() -> list:
    """Devuelve la cadena real `[(condición_js, plantilla_html), ...]` publicada por el frontend."""
    ramas = _PATRON_RAMA.findall(_bloque_cobertura_resumen_asignacion())
    assert len(ramas) == 3, (
        "La cadena de rótulos de cobertura cambió de forma: se esperaban 3 ramas "
        f"(familias directas / R2 / cobertura en tablas) y se hallaron {len(ramas)}."
    )
    return ramas


_PATRON_POR_DEFECTO = re.compile(r'let coberturaHtml = `([^`]*)`;')


def _plantilla_por_defecto() -> str:
    """Rótulo por defecto del Resumen de Asignación: lo conservan las familias sin rama propia."""
    coincidencia = _PATRON_POR_DEFECTO.search(_bloque_cobertura_resumen_asignacion())
    assert coincidencia, "El Resumen de Asignación no declara rótulo por defecto para el resto de familias"
    return coincidencia.group(1)


def _evalua_condicion(condicion: str, codigo: str) -> bool:
    """Evalúa (subconjunto mínimo y fail-loud) una condición de la cadena contra un código."""
    restante = condicion.strip()
    if "||" in restante:
        return any(_evalua_condicion(parte, codigo) for parte in restante.split("||"))
    coincidencia = re.fullmatch(r'cod\.startsWith\("([^"]+)"\)', restante)
    if coincidencia:
        return codigo.startswith(coincidencia.group(1))
    coincidencia = re.fullmatch(r'cod\s*===\s*"([^"]+)"', restante)
    if coincidencia:
        return codigo == coincidencia.group(1)
    raise AssertionError(
        f"[FAIL-LOUD] Condición no soportada por el Juez: {restante!r}. "
        "Reformule la cadena o amplíe el Juez mediante dictamen."
    )


def _texto_plano(html: str) -> str:
    """Rótulo sin marcado: lo que el usuario lee."""
    return re.sub(r"<[^>]+>", "", html).strip()


def _rotulo_de_cobertura(codigo: str, inv: float = 12.0, tablas: float = 0.0, roi: float = 18.0) -> str:
    """Rótulo EXACTO que la pantalla exhibiría para `codigo` (evalúa la cadena real del frontend)."""
    etiqueta = None
    for condicion, plantilla in _ramas_de_cobertura():
        if _evalua_condicion(condicion, codigo):
            etiqueta = plantilla
            break
    if etiqueta is None:
        # Familia sin rama propia: el frontend conserva el rótulo por defecto (QBE-C1 / C2 / 00).
        etiqueta = _plantilla_por_defecto()
    return _texto_plano(
        etiqueta.replace("${tablas.toFixed(2)}", f"{tablas:.2f}")
                .replace("${inv.toFixed(2)}", f"{inv:.2f}")
                .replace("${roi.toFixed(1)}", f"{roi:.1f}")
    )


# ---------------------------------------------------------------------------
# 1. [LN-QBE-083-B] FAMILIAS DIRECTAS: RIESGO DIRECTO DECLARADO SIN CIFRAS FALSAS
# ---------------------------------------------------------------------------
def test_ln_qbe_083_b_familias_directas_declaran_riesgo_directo():
    """QBE-D1 y QBE-D2 carecen de pierna de cobertura ⇒ rótulo único de riesgo directo."""
    for codigo in ("QBE-D1", "QBE-D2"):
        rotulo = _rotulo_de_cobertura(codigo, inv=12.0, tablas=0.0)
        assert rotulo == "Sin cobertura (Riesgo Directo: -$12.00)", f"{codigo} → {rotulo!r}"
        assert "Recuperas" not in rotulo, (
            f"🚨 [LN-QBE-083-B] {codigo} promete recuperación de capital sin pierna de cobertura: {rotulo!r}"
        )
        assert "Recuperas $0.00" not in rotulo, (
            f"🚨 El falso 'Recuperas $0.00 MXN' erradicado en el Tramo 4 revivió en {codigo}: {rotulo!r}"
        )


def test_ln_qbe_083_b_cero_ortografias_divergentes_en_el_resumen():
    """Las 9 familias canónicas resuelven a un vocabulario cerrado de rótulos (sin tercera ortografía)."""
    rotulos = {codigo: _rotulo_de_cobertura(codigo, inv=10.0, tablas=10.0) for codigo in CODIGOS_CANONICOS}

    assert set(rotulos) == set(CODIGOS_CANONICOS), "La cadena debe clasificar los 9 códigos canónicos"
    assert len(set(rotulos.values())) <= 3, (
        f"🚨 Vocabulario de rótulos divergente (más de 3 ortografías): {rotulos}"
    )
    assert rotulos["QBE-D1"] == rotulos["QBE-D2"] == "Sin cobertura (Riesgo Directo: -$10.00)", (
        "Las dos familias directas deben compartir el rótulo unificado ([LN-QBE-083-B])"
    )
    assert rotulos["QBE-R2"] == "Ambos boletos ganan (+18.0% ROI)"


def test_ln_qbe_083_b_familias_con_cobertura_conservan_rotulo_de_recuperacion():
    """Anti-regresión: las ramas selladas por [LN-QBE-083] / [DES-QBE-062] permanecen intactas."""
    for codigo in ("QBE-H1", "QBE-H2", "QBE-R1"):
        rotulo = _rotulo_de_cobertura(codigo, inv=16.0, tablas=16.0)
        assert rotulo == "Recuperas $16.00 MXN ($0.00 pérdida)", f"{codigo} → {rotulo!r}"


# ---------------------------------------------------------------------------
# 2. [ARCH-1.4.16-B] HORARIO FÁCTICO EN EL RESUMEN DE ASIGNACIÓN (TRAMO 3)
# ---------------------------------------------------------------------------
def test_arch_1_4_16_b_horario_factico_en_resumen_de_asignacion():
    """La columna PARTIDO exhibe `horario_evento`; sin dato jamás se inventa un placeholder."""
    code = _fuente(APP_JS)

    coincidencia = re.search(
        r'const horarioHtml = ord\.horario_evento\s*\?\s*`([^`]*)`\s*:\s*"";', code, re.DOTALL
    )
    assert coincidencia, (
        "🚨 [ARCH-1.4.16-B] El Resumen de Asignación no deriva la línea de horario de `horario_evento`"
    )
    plantilla = coincidencia.group(1)
    assert "⏰" in plantilla, "La línea secundaria debe ser reconocible (glifo de reloj)"
    assert "${ord.horario_evento}" in plantilla, "La plantilla debe interpolar el horario fáctico"

    assert coincidencia.group(0).rstrip().endswith(': "";'), (
        "🚨 [GOVERNANCE-01] La rama sin horario debe emitir cadena vacía: cero placeholders inventados"
    )
    assert '<td style="font-weight:700; color:#fff;">${ord.partido}${horarioHtml}</td>' in code, (
        "La línea de horario debe viajar DENTRO de la columna PARTIDO de la fila de asignación"
    )


# ---------------------------------------------------------------------------
# 3. [ARCH-1.4.16-B] EL PAYLOAD DE ÓRDENES PRESERVA EL HORARIO FÁCTICO
# ---------------------------------------------------------------------------
def test_arch_1_4_16_b_payload_de_ordenes_preserva_horario_evento():
    """El contrato de orden transporta `horario_evento` y falla ruidosamente si falta."""
    from src.models.decision import (
        CashoutTargets, KeyMetrics, MatchExecutionOrder, MatchTickets, Projections,
        StrategySelection, TicketOrder,
    )

    assert "horario_evento" in MatchExecutionOrder.model_fields, (
        "🚨 El contrato de orden perdió `horario_evento` ([ARCH-1.4.16])"
    )
    assert MatchExecutionOrder.model_fields["horario_evento"].is_required(), (
        "`horario_evento` debe ser obligatorio (fail-loud): el motor jamás inventa un horario ausente"
    )

    horario_factico = "14/09\n19:00 hr"
    orden = MatchExecutionOrder(
        id_partido="P1",
        partido="Club León vs Atlético San Luis",
        horario_evento=horario_factico,
        estrategia_seleccionada=StrategySelection(
            codigo="QBE-D1",
            nombre_oficial="Favorito Directo Puro",
            descripcion_ejecutiva="Victoria directa del Favorito sin cobertura de tablas",
            linea_promocional="Estándar",
        ),
        metricas_clave=KeyMetrics(
            score_calidad_S_i=0.81,
            peso_portafolio_w_i=0.08,
            phi_lead2_prob_ventaja_2_goles=0.22,
            psi_downside_riesgo=0.05,
            ev_neto_roi_porcentaje=19.86,
        ),
        forma_reciente_auditada={"fav_resumen": "Posición #3, 21 pts | Q_mod: 1.0"},
        boletos=MatchTickets(
            inversion_partido_A_i=16.0,
            boleto_1_seguro=TicketOrder(
                seleccion="N/A ($0.00)", momio=0.0, monto_mxn=0.0, operador="caliente"
            ),
            boleto_2_ganancia=TicketOrder(
                seleccion="Gana Club León + PA", momio=1.79, monto_mxn=16.0,
                operador="caliente", prob_qbe=64.3,
            ),
        ),
        proyecciones=Projections(
            ganancia_neta_principal_mxn=12.64,
            roi_principal_porcentaje=79.0,
            resultado_tablas_mxn=0.0,
            perdida_maxima_posible_mxn=16.0,
        ),
        cashout_targets=CashoutTargets(
            monto_salida_emergencia_tablas_mxn=0.0,
            monto_salida_optima_min85="N/A",
            instruccion_emergencia_rompequinielas="Monitorear en el 2T.",
            instruccion_desarrollo_normal="Sostener la posición hasta el 90'.",
        ),
    )

    payload = orden.model_dump()
    assert payload["horario_evento"] == horario_factico, (
        "El payload de órdenes debe preservar el horario fáctico byte por byte (incluye salto de línea)"
    )

    with pytest.raises(ValidationError):
        MatchExecutionOrder(**{k: v for k, v in payload.items() if k != "horario_evento"})

    assert 'horario_evento=m.get("horario"' in _fuente(PORTFOLIO_PY), (
        "🚨 portfolio.py no hidrata `horario_evento` desde el contrato de partido"
    )
    assert '"horario": fx.get("horario"' in _fuente(MARKETS_PY), (
        "🚨 markets.py no publica el horario del fixture en el contrato de partido"
    )


# ---------------------------------------------------------------------------
# 4. [DES-QBE-060] P' CONTRAÍDO POR PIERNA Y BLOQUE DE TRANSPARENCIA 360°
# ---------------------------------------------------------------------------
def test_des_qbe_060_p_prima_contraido_preservado_en_el_contrato_de_orden():
    """La pierna expone el P' del desenlace que realmente transporta; el descartado también."""
    from src.models.decision import MatchExecutionOrder, TicketOrder

    assert "prob_qbe" in TicketOrder.model_fields, "🚨 La pierna perdió el rótulo P' contraído"
    assert TicketOrder.model_fields["prob_qbe"].default is None, (
        "P' es opcional para no romper payloads históricos ([DES-QBE-060])"
    )

    pierna = TicketOrder(
        seleccion="Gana Rayados de Monterrey + PA", momio=1.98, monto_mxn=12.0,
        operador="novibet", prob_qbe=42.7,
    )
    assert pierna.model_dump()["prob_qbe"] == 42.7
    assert "opcion_no_jugada" in MatchExecutionOrder.model_fields, (
        "Falta el Bloque de Transparencia 360° ([DES-QBE-060])"
    )

    fuente = _fuente(PORTFOLIO_PY)
    assert "prob_qbe=prob_b1" in fuente and "prob_qbe=prob_b2" in fuente, (
        "🚨 El motor no rotula P' por pierna (resolución por identidad de la etiqueta)"
    )
    assert '"prob_qbe": round(float(desc_p_c) * 100.0, 1) if desc_p_c is not None else None' in fuente, (
        "🚨 El desenlace descartado del Bloque 360° no expone su P' contraído"
    )


# ---------------------------------------------------------------------------
# 5. ANCLAJE LEGISLATIVO DE LOS NODOS -B EN EL REGISTRO MAESTRO
# ---------------------------------------------------------------------------
def test_nodos_b_publicados_y_anclados_en_el_registro_maestro():
    """Los nodos promulgados por el Dictamen VARIANZA-10 §1.2 existen y están anclados."""
    assert "### ID: [LN-QBE-083-B]" in _fuente(LOGIC_MD), "Falta el nodo [LN-QBE-083-B] en LOGIC.md"
    assert "### [ARCH-1.4.16-B]" in _fuente(ARCH_MD), "Falta el nodo [ARCH-1.4.16-B] en ARCH.md"

    registro = _fuente(REGISTRY_MD)
    assert "[LN-QBE-083-B]" in registro and "[ARCH-1.4.16-B]" in registro, (
        "🚨 Ceguera de colisión: nodo sellado sin fila en docs/ID_REGISTRY.md"
    )


