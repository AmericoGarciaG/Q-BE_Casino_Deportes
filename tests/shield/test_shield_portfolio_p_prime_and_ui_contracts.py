# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD: JUEZ INMUTABLE DE CONTRATO P' CONTRAÍDO Y RÓTULOS DE PRESENTACIÓN
Audita:
- [LN-QBE-083-B] Rótulo único de ausencia de cobertura en familias DIRECTAS (QBE-D1 / QBE-D2).
- [ARCH-1.4.16-B] Horario fáctico (`horario_evento`) en el Resumen de Asignación.
- [DES-QBE-060] P' contraído por pierna (`prob_qbe`) y Bloque de Transparencia 360° preservados.
- [V-1 / VAR-2026-LIVE-AUDIT-J11] Vinculación del P' en el modal POR IDENTIDAD de pierna (jamás
  por rol posicional de la fila).
- [V-4 / VAR-2026-LIVE-AUDIT-J11] Rótulo de Doble Cobro de la Familia R2 condicionado a la
  bandera booleana del Pago Anticipado ([DES-QBE-062]).
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


# El grupo de condición excluye llaves (`[^{}]*?`): el cotejo NUNCA cruza el cuerpo de una rama,
# de modo que cada hallazgo queda anclado a su propia condición (extracción biunívoca, sin fugas).
_PATRON_RAMA = re.compile(
    r'(?:if|else\s+if)\s*\(([^{}]*?)\)\s*\{\s*coberturaHtml\s*=\s*`([^`]*)`;', re.DOTALL
)

# [V-4] Rama CONDICIONAL gobernada por bandera: `coberturaHtml = BANDERA ? `...` : `...`;`
# El grupo de condición excluye llaves (`[^{}]*?`) para que el cotejo NUNCA cruce el cuerpo de
# una rama previa: cada hallazgo queda anclado a su propia rama (extracción biunívoca).
_PATRON_RAMA_PA = re.compile(
    r'(?:if|else\s+if)\s*\(([^{}]*?)\)\s*\{\s*coberturaHtml\s*=\s*([A-Za-z_$][\w$]*)\s*'
    r'\?\s*`([^`]*)`\s*:\s*`([^`]*)`;', re.DOTALL
)

# [DES-QBE-062] El Pago Anticipado se gobierna por bandera booleana, jamás por proxies.
_PATRON_BANDERA_PA = re.compile(
    r'const\s+([A-Za-z_$][\w$]*)\s*=\s*\(ord\.pa_activo\s*===\s*true\)\s*\|\|\s*'
    r'Boolean\(ord\.estrategia_seleccionada\?\.linea_promocional\);'
)


def _ramas_de_cobertura() -> list:
    """Cadena real de rótulos publicada por el frontend, en orden de evaluación.

    Cada rama se devuelve como un dict `{"condicion", "plantilla", "bandera",
    "plantilla_pa", "plantilla_sin_pa"}`: las ramas incondicionales portan `plantilla`; la rama
    condicional de la Familia R2 ([V-4]) porta la bandera booleana que la gobierna y sus dos
    plantillas (con y sin Pago Anticipado).
    """
    bloque = _bloque_cobertura_resumen_asignacion()
    hallazgos = []
    for coincidencia in _PATRON_RAMA.finditer(bloque):
        hallazgos.append((coincidencia.start(), {
            "condicion": coincidencia.group(1), "plantilla": coincidencia.group(2),
            "bandera": None, "plantilla_pa": None, "plantilla_sin_pa": None,
        }))
    for coincidencia in _PATRON_RAMA_PA.finditer(bloque):
        hallazgos.append((coincidencia.start(), {
            "condicion": coincidencia.group(1), "plantilla": None,
            "bandera": coincidencia.group(2),
            "plantilla_pa": coincidencia.group(3), "plantilla_sin_pa": coincidencia.group(4),
        }))
    ramas = [rama for _, rama in sorted(hallazgos, key=lambda par: par[0])]
    assert len(ramas) == 3, (
        "La cadena de rótulos de cobertura cambió de forma: se esperaban 3 ramas "
        f"(familias directas / R2 / cobertura en tablas) y se hallaron {len(ramas)}."
    )
    return ramas


def _bandera_pa_del_frontend() -> str:
    """Identificador de la bandera booleana del Pago Anticipado que gobierna el rótulo de R2."""
    coincidencia = _PATRON_BANDERA_PA.search(_fuente(APP_JS))
    assert coincidencia, (
        "🚨 [V-4] El rótulo de Doble Cobro no está gobernado por la bandera booleana "
        "`ord.pa_activo === true` ([DES-QBE-062])."
    )
    return coincidencia.group(1)


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


def _rotulo_de_cobertura(codigo: str, inv: float = 12.0, tablas: float = 0.0, roi: float = 18.0,
                         pa_activo: bool = True) -> str:
    """Rótulo EXACTO que la pantalla exhibiría para `codigo` (evalúa la cadena real del frontend).

    `pa_activo` transporta el estado de la bandera booleana del Pago Anticipado ([DES-QBE-062]);
    sólo la rama condicional de la Familia R2 ([V-4]) lo consume.
    """
    etiqueta = None
    for rama in _ramas_de_cobertura():
        if _evalua_condicion(rama["condicion"], codigo):
            if rama["plantilla"] is not None:
                etiqueta = rama["plantilla"]
            else:
                etiqueta = rama["plantilla_pa"] if pa_activo else rama["plantilla_sin_pa"]
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
    rotulos = {
        codigo: _rotulo_de_cobertura(codigo, inv=10.0, tablas=10.0, pa_activo=False)
        for codigo in CODIGOS_CANONICOS
    }

    assert set(rotulos) == set(CODIGOS_CANONICOS), "La cadena debe clasificar los 9 códigos canónicos"
    assert len(set(rotulos.values())) <= 3, (
        f"🚨 Vocabulario de rótulos divergente (más de 3 ortografías): {rotulos}"
    )
    assert rotulos["QBE-D1"] == rotulos["QBE-D2"] == "Sin cobertura (Riesgo Directo: -$10.00)", (
        "Las dos familias directas deben compartir el rótulo unificado ([LN-QBE-083-B])"
    )
    # [V-4] La Familia R2 sólo declara Doble Cobro con la bandera del Pago Anticipado activa.
    assert rotulos["QBE-R2"] == "Recuperas $10.00 MXN ($0.00 pérdida)", (
        "Sin Pago Anticipado, R2 exhibe la recuperación real en tablas ([LN-QBE-083-B])"
    )
    assert _rotulo_de_cobertura("QBE-R2", inv=10.0, tablas=10.0, pa_activo=True) == \
        "Ambos boletos ganan (+18.0% ROI)"


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


# ---------------------------------------------------------------------------
# 6. [V-4 / VAR-2026-LIVE-AUDIT-J11] RÓTULO DE DOBLE COBRO CONDICIONADO AL PA
# ---------------------------------------------------------------------------
def test_v4_rotulo_de_doble_cobro_condicionado_a_la_bandera_pa():
    """R2 sólo promete 'Ambos boletos ganan' con la bandera booleana del Pago Anticipado activa."""
    rama_r2 = [
        rama for rama in _ramas_de_cobertura() if _evalua_condicion(rama["condicion"], "QBE-R2")
    ]
    assert len(rama_r2) == 1, "🚨 La Familia R2 debe poseer exactamente una rama de rótulo"
    rama = rama_r2[0]

    assert rama["plantilla"] is None, (
        "🚨 [V-4] El rótulo de R2 debe ser CONDICIONAL a la bandera del Pago Anticipado"
    )
    assert rama["bandera"] == _bandera_pa_del_frontend(), (
        "🚨 La condición del rótulo debe consumir la bandera booleana declarada ([DES-QBE-062])"
    )
    assert "Ambos boletos ganan" in rama["plantilla_pa"], (
        "🚨 La rama con Pago Anticipado debe conservar el rótulo sellado de Doble Cobro"
    )
    assert "Ambos boletos ganan" not in rama["plantilla_sin_pa"], (
        "🚨 [GOVERNANCE-01] Sin PA, R2 no puede cobrar ambos boletos: rótulo fiduciariamente falso"
    )
    assert _rotulo_de_cobertura("QBE-R2", inv=16.0, tablas=16.0, roi=18.0, pa_activo=True) == \
        "Ambos boletos ganan (+18.0% ROI)"
    assert _rotulo_de_cobertura("QBE-R2", inv=16.0, tablas=16.0, roi=18.0, pa_activo=False) == \
        "Recuperas $16.00 MXN ($0.00 pérdida)"
    # Las ramas incondicionales NO pueden depender de la bandera (anti-deriva silenciosa).
    for rama_plana in _ramas_de_cobertura():
        if _evalua_condicion(rama_plana["condicion"], "QBE-H2"):
            assert rama_plana["plantilla"] is not None, (
                "🚨 La rama de cobertura en tablas debe permanecer incondicional"
            )


# ---------------------------------------------------------------------------
# 7. [V-1 / VAR-2026-LIVE-AUDIT-J11] VINCULACIÓN DEL P' POR IDENTIDAD DE PIERNA
# ---------------------------------------------------------------------------
def test_v1_modal_vincula_p_prima_por_identidad_de_pierna():
    """El comparador resuelve la pierna por la etiqueta `seleccion`, jamás por rol posicional."""
    code = _fuente(APP_JS)

    assert "const _resolverPiernaDeFila = (resultado) =>" in code, (
        "🚨 [V-1] El modal no declara el resolutor de pierna POR IDENTIDAD de etiqueta"
    )
    assert "const _normSeleccion = (s) => String(s || \"\")" in code, (
        "🚨 [V-1] Falta el normalizador de etiquetas (debe erradicar el sufijo ` + PA`)"
    )
    assert r'.replace(/\s*\+\s*PA\s*/gi, "")' in code, (
        "🚨 [V-1] El normalizador debe erradicar el sufijo del Pago Anticipado antes de comparar"
    )
    assert "for (const leg of [legCobertura, legAtaque, opNoJugada])" in code, (
        "🚨 [V-1] El resolutor debe cotejar las TRES piernas certificadas de la orden"
    )
    assert "const legFila = _resolverPiernaDeFila(pv.resultado);" in code, (
        "🚨 [V-1] La fila del comparador debe resolver su pierna por la identidad de `resultado`"
    )
    assert "let pPrima = legFila ? legFila.prob_qbe : null;" in code, (
        "🚨 [V-1] El P' exhibido debe emanar de la pierna IDENTIFICADA, no del rol posicional"
    )
    assert "const legCuota = legFila" in code, (
        "🚨 [V-1] La cuota/operador exhibidos deben emanar de la misma pierna que el P'"
    )
    # El rol posicional queda EXCLUSIVAMENTE como degradación declarada.
    assert "Sin etiqueta certificada: degrada al rol posicional (cero invención)." in code, (
        "🚨 [V-1] La degradación posicional debe estar declarada explícitamente en la fuente"
    )


# ---------------------------------------------------------------------------
# 8. [ARCH-1.4.32 / P3-9] LEDGER FIDUCIARIO PERSISTIDO EN 3NF
# ---------------------------------------------------------------------------
class TestLedgerFiduciario3NF:
    def test_registro_boleto_persiste_en_3nf(self):
        """POST register-ticket persiste el boleto y bloquea el duplicado (idempotencia)."""
        import uuid
        from fastapi.testclient import TestClient
        from src.web.app import app

        payload = {
            "match_id": f"LIGAMX-P3-9-{uuid.uuid4().hex}",
            "desenlace": "L",
            "cuota_congelada": 1.85,
            "monto": 100.0,
        }
        client = TestClient(app)

        primera = client.post("/api/portfolio/register-ticket", json=payload)
        assert primera.status_code == 200, primera.text
        cuerpo = primera.json()
        assert cuerpo.get("status") == "OK", cuerpo
        assert cuerpo.get("boletos_comprados", 0) >= 1, cuerpo

        from src.storage.gateway import PersistenceGateway
        from src.storage.models import PaperTradingLedger

        with PersistenceGateway().read_session() as db:
            fila = db.query(PaperTradingLedger).filter(
                PaperTradingLedger.match_id == payload["match_id"],
                PaperTradingLedger.desenlace == payload["desenlace"],
                PaperTradingLedger.monto == payload["monto"],
            ).first()
            assert fila is not None, "El boleto no quedó persistido en paper_trading_ledger"

        estado = client.get("/api/portfolio/ledger-status")
        assert estado.status_code == 200, estado.text
        assert payload["match_id"] in estado.json().get("match_ids", []), (
            "El endpoint de hidratación no publica el boleto recién sellado"
        )

        duplicado = client.post("/api/portfolio/register-ticket", json=payload)
        assert duplicado.status_code in (400, 409), (
            "La idempotencia debe rechazar el duplicado con 400/409: "
            f"{duplicado.status_code} {duplicado.text}"
        )

        code = APP_JS.read_text(encoding="utf-8")
        assert "qbe_boletos_comprados" not in code, (
            "🚨 El frontend conserva el ledger en localStorage; debe consumir el endpoint 3NF"
        )
        assert "/api/portfolio/register-ticket" in code, (
            "🚨 El frontend no invoca el endpoint POST /api/portfolio/register-ticket"
        )
        assert "/api/portfolio/ledger-status" in code, (
            "🚨 El frontend no hidrata el badge desde el ledger 3NF"
        )


