// src/web/static/js/app.js
// Q-BE Casino Deportes — Live Board Reactivo SPA (DES-QBE-016 / ARCH-1.6.0 / ARCH-1.6.2)

let currentLiveBoard = null;
let selectedMatchIds = [];

document.addEventListener("DOMContentLoaded", function () {
    initNavigation();
    cargarLigasDesdeBD();
});

function initNavigation() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-tab');
            switchView(target);
        });
    });
}

function switchView(viewId) {
    document.querySelectorAll('.view-section').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));

    const targetView = document.getElementById(viewId);
    if (targetView) targetView.classList.add('active');
    const targetTab = document.querySelector(`.tab-btn[data-tab="${viewId}"]`);
    if (targetTab) targetTab.classList.add('active');
}

function switchTableTab(tabName) {
    document.querySelectorAll('.subtab-btn').forEach(btn => btn.classList.remove('active'));
    const clickedBtn = document.getElementById(`btn-tab-${tabName}`);
    if (clickedBtn) clickedBtn.classList.add('active');

    const colGen = document.querySelectorAll('.col-gen');
    const colForma = document.querySelectorAll('.col-forma');
    const colXg = document.querySelectorAll('.col-xg');

    colGen.forEach(el => el.style.display = (tabName === 'general') ? '' : 'none');
    colForma.forEach(el => el.style.display = (tabName === 'forma') ? '' : 'none');
    colXg.forEach(el => el.style.display = (tabName === 'xg') ? '' : 'none');
}

// 1. Cargar Ligas en Vista 1
async function cargarLigasDesdeBD() {
    try {
        const resp = await fetch("/api/leagues");
        if (!resp.ok) throw new Error("Error al consultar /api/leagues");
        const ligas = await resp.json();

        const grid = document.querySelector(".leagues-grid");
        if (!grid) return;
        grid.innerHTML = "";

        ligas.forEach(l => {
            const card = document.createElement("div");
            card.className = "league-card active";
            card.style.cssText = "background: #1C2541; border: 1px solid #00E676; border-radius: 8px; padding: 14px; cursor: pointer; transition: transform 0.15s ease;";
            const logoHtml = l.flag ? `<img src="${l.flag}" alt="" onerror="this.src='/static/img/favicon.svg'" style="width: 32px; height: 32px; object-fit: contain; margin-bottom: 8px;">` : `<div style="font-size: 14pt; font-weight: 800; color: #38BDF8; margin-bottom: 6px;">MX</div>`;
            card.innerHTML = `
                <div style="margin-bottom: 4px;">${logoHtml}</div>
                <div class="league-info">
                    <h3 style="margin: 0; color: #ffffff; font-size: 1.05rem;">${l.name}</h3>
                    <span style="font-size: 7.5pt; color: #94A3B8;">${l.country}</span>
                    <div style="font-size: 7.2pt; color: #00E676; font-weight: 700; margin-top: 6px;">• 18 Clubes • Tabla y Métricas al Día</div>
                </div>
            `;
            card.onmouseenter = () => card.style.transform = "translateY(-3px)";
            card.onmouseleave = () => card.style.transform = "translateY(0)";
            card.onclick = () => seleccionarLiga(l.fotmob_id);
            grid.appendChild(card);
        });
    } catch (e) {
        console.error("Fallo cargando ligas:", e);
    }
}

// 2. Seleccionar Liga y Cargar Live Board en Vista 2
async function seleccionarLiga(fotmobId, forceRefresh = false) {
    switchView("view-matchday-selection");
    const tbody = document.querySelector(".table-panel-left table tbody");
    if (tbody) tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:20px; color:#38BDF8;">⏳ Sincronizando datos oficiales en tiempo real...</td></tr>';

    try {
        let url = `/api/leagues/${fotmobId}/live-board`;
        if (forceRefresh) url += "?force_refresh=true";
        const resp = await fetch(url);
        if (!resp.ok) throw new Error("Error al obtener Live Board");
        currentLiveBoard = await resp.json();

        const lblTabla = document.getElementById("lbl-nombre-tabla");
        if (lblTabla) lblTabla.textContent = currentLiveBoard.league_name || "Liga MX";
        const lblJornada = document.getElementById("lbl-nombre-jornada");
        if (lblJornada) lblJornada.textContent = currentLiveBoard.jornada || "Jornada Activa";

        renderizarTabla18Clubes(currentLiveBoard.standings);
        renderizarCartelera(currentLiveBoard.fixtures);
    } catch (e) {
        console.error("Error cargando live board:", e);
        if (tbody) tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:#f87171;">❌ Error al conectar: ${e.message}</td></tr>`;
    }
}

async function refrescarCuotasEnVivo() {
    if (!currentLiveBoard) return;
    const btn = document.getElementById("btn-force-refresh");
    if (btn) btn.innerHTML = "⏳ Refrescando...";
    await seleccionarLiga(currentLiveBoard.league_id, true);
    if (btn) btn.innerHTML = "🔄 Refrescar Cuotas";
}
window.refrescarCuotasEnVivo = refrescarCuotasEnVivo;

// 3. Renderizar Tabla de 18 Clubes Completa (Panel Izquierdo)
function renderizarTabla18Clubes(standings) {
    const tbody = document.querySelector(".table-panel-left table tbody");
    if (!tbody || !standings) return;
    tbody.innerHTML = "";

    standings.forEach(t => {
        const tr = document.createElement("tr");
        
        // Renderizado del escudo oficial del club
        const escudoHtml = t.escudo_url ? `<img src="${t.escudo_url}" alt="" style="width: 16px; height: 16px; object-fit: contain; vertical-align: middle; margin-right: 6px;">` : '';

        // Forma con círculos de colores en contenedor horizontal anti-descuadre [DES-QBE-036]
        const formaHtml = `<div class="form-badges-wrapper" style="display: inline-flex; align-items: center; justify-content: center; gap: 3px; white-space: nowrap;">` +
            (t.forma || ["G", "E", "P"]).map(f => {
                const cls = (f === "G" || f === "W") ? "badge-g" : (f === "E" || f === "D") ? "badge-e" : "badge-p";
                const letra = (f === "G" || f === "W") ? "G" : (f === "E" || f === "D") ? "E" : "P";
                return `<span class="form-badge ${cls}" style="display: inline-flex; align-items: center; justify-content: center; width: 14px; height: 14px; border-radius: 50%; font-size: 6pt; font-weight: 800; color: #fff;">${letra}</span>`;
            }).join("") + `</div>`;

        // Renderizado del próximo rival con escudo miniatura [DES-QBE-016]
        const proxEscudoHtml = t.proximo_escudo_url ? `<img src="${t.proximo_escudo_url}" alt="" style="width: 14px; height: 14px; object-fit: contain; vertical-align: middle; margin-right: 4px;">` : '';
        const proximoHtml = `<div style="display: inline-flex; align-items: center; white-space: nowrap; color: #38BDF8; font-weight: 600; font-size: 7.2pt;">${proxEscudoHtml}${t.proximo_rival || "—"}</div>`;

        const difColor = t.dif >= 0 ? "#00E676" : "#f87171";
        const difSign = t.dif > 0 ? "+" : "";

        // Cálculo limpio de diferencia xG sin doble signo (+ -)
        const xgVal = parseFloat(t.xg || 0);
        const xgaVal = parseFloat(t.xga || 0);
        const difXg = xgVal - xgaVal;
        const difXgSign = difXg > 0 ? "+" : "";
        const difXgColor = difXg >= 0 ? "#00E676" : "#f87171";
        const difXgFormatted = `${difXgSign}${difXg.toFixed(1)}`;

        tr.innerHTML = `
            <td style="text-align: center; font-weight: 700;">${t.pos}</td>
            <td style="font-weight: 600; color: #ffffff; white-space: nowrap;">${escudoHtml}${t.equipo}</td>
            <td style="text-align: center; font-weight: 700; color: #00E676;">${t.puntos}</td>
            <!-- General -->
            <td class="col-gen" style="text-align: center;">${t.pj}</td>
            <td class="col-gen" style="text-align: center;">${t.pg}</td>
            <td class="col-gen" style="text-align: center;">${t.pe}</td>
            <td class="col-gen" style="text-align: center;">${t.pp}</td>
            <td class="col-gen" style="text-align: center;">${t.gf}:${t.gc}</td>
            <td class="col-gen" style="text-align: center; font-weight: 700; color: ${difColor};">${difSign}${t.dif}</td>
            <!-- Forma -->
            <td class="col-forma" style="text-align: center; white-space: nowrap !important; display: none;">${formaHtml}</td>
            <td class="col-forma" style="text-align: center; white-space: nowrap !important; display: none;">${proximoHtml}</td>
            <!-- xG Opta -->
            <td class="col-xg" style="text-align: center; color: #38BDF8; font-weight: 600; display: none;">${t.xg || "—"}</td>
            <td class="col-xg" style="text-align: center; color: #f87171; display: none;">${t.xga || "—"}</td>
            <td class="col-xg" style="text-align: center; color: #00E676; font-weight: 700; display: none;">${t.xpts || "—"}</td>
            <td class="col-xg" style="text-align: center; font-weight: 700; color: ${difXgColor}; display: none;">${difXgFormatted}</td>
        `;
        tbody.appendChild(tr);
    });
}

// 4. Renderizar Cartelera en 4 Niveles Visuales [DES-QBE-016-C] [ARCH-1.6.3]
function renderizarCartelera(fixtures) {
    const container = document.querySelector(".fixtures-list");
    if (!container || !fixtures) return;
    container.innerHTML = "";
    selectedMatchIds = [];

    // Separar por estado semántico (Ordenamiento Topológico ya aplicado por el backend)
    const enCurso     = fixtures.filter(f => f.estado === "EN_CURSO");
    const programados = fixtures.filter(f => f.estado === "PROGRAMADO");
    const reprogramados = fixtures.filter(f => f.estado === "REPROGRAMADO");
    const finalizados = fixtures.filter(f => f.estado === "FINALIZADO");

    // ── Nivel 1: EN CURSO ─────────────────────────────────────────────────
    if (enCurso.length > 0) {
        _renderSeccionHeader(container, "🔴 En Juego Ahora", "header-live");
        enCurso.forEach(f => _renderFixtureCard(container, f, false));
    }

    // ── Nivel 2: PROGRAMADOS — agrupados por fecha (con prefijo HOY dinámico) ──
    if (programados.length > 0) {
        const grupos = {};
        programados.forEach(f => {
            const hoy = f.fecha_dt ? _esHoyDinamico(f.fecha_dt) : false;
            const label = hoy ? `HOY — ${f.fecha_bloque}` : f.fecha_bloque;
            if (!grupos[label]) grupos[label] = [];
            grupos[label].push(f);
        });
        Object.keys(grupos).forEach(label => {
            _renderSeccionHeader(container, `📅 ${label}`, "");
            grupos[label].forEach(f => _renderFixtureCard(container, f, false));
        });
    }

    // ── Nivel 3: REPROGRAMADOS ────────────────────────────────────────────
    if (reprogramados.length > 0) {
        _renderSeccionHeader(container, "⏳ Partidos Reprogramados / Fecha Lejana", "header-postponed");
        reprogramados.forEach(f => _renderFixtureCard(container, f, true));
    }

    // ── Nivel 4: FINALIZADOS al fondo ─────────────────────────────────────
    if (finalizados.length > 0) {
        _renderSeccionHeader(container, "🏁 Partidos Concluidos de la Jornada", "header-finished");
        finalizados.forEach(f => _renderFixtureCard(container, f, true));
    }

    actualizarContadorSeleccionados();

    // Habilitar clicabilidad total de tarjeta [DES-QBE-016-C]
    habilitarClicTarjetaCompleta();
}

/** Evalúa dinámicamente si una fecha ISO 8601 corresponde al día de hoy [ARCH-1.6.3] */
function _esHoyDinamico(fechaDtStr) {
    if (!fechaDtStr) return false;
    try {
        const dt = new Date(fechaDtStr);
        const hoy = new Date();
        return dt.getFullYear() === hoy.getFullYear() &&
               dt.getMonth() === hoy.getMonth() &&
               dt.getDate() === hoy.getDate();
    } catch (e) {
        return false;
    }
}

/** Renderiza un encabezado de sección con clase de color opcional */
function _renderSeccionHeader(container, texto, claseAdicional) {
    const div = document.createElement("div");
    div.className = `fixture-section-header ${claseAdicional}`.trim();
    div.textContent = texto;
    container.appendChild(div);
}

/** Renderiza una tarjeta de fixture según su estado semántico [DES-QBE-016-C] */
function _renderFixtureCard(container, f, deshabilitada) {
    const card = document.createElement("div");
    card.className = "fixture-card" + (deshabilitada ? " fixture-disabled" : "");
    card.id = `fixture-card-${f.id_partido}`;
    card.dataset.estado = f.estado || "PROGRAMADO";
    card.dataset.matchId = f.id_partido;

    const estado = f.estado || "PROGRAMADO";
    const esSeleccionable = !deshabilitada && estado === "PROGRAMADO" && f.disponible_para_seleccion !== false;

    // Estilo base de la tarjeta según estado
    if (estado === "EN_CURSO") {
        card.style.cssText = "background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.4); border-radius: 6px; padding: 10px; margin-bottom: 6px;";
    } else if (estado === "FINALIZADO") {
        card.style.cssText = "background: rgba(255,255,255,0.015); border: 1px dashed #475569; border-radius: 6px; padding: 10px; margin-bottom: 6px;";
    } else if (estado === "REPROGRAMADO") {
        card.style.cssText = "background: rgba(255,255,255,0.01); border: 1px dashed #334155; border-radius: 6px; padding: 10px; margin-bottom: 6px;";
    } else {
        // PROGRAMADO — operable
        card.style.cssText = "background: rgba(0,230,118,0.04); border: 1px solid #334155; border-radius: 6px; padding: 10px; margin-bottom: 6px;";
        if (esSeleccionable) {
            selectedMatchIds.push(f.id_partido);
        }
    }

    // Badge de estado
    let badgeHtml = "";
    if (estado === "EN_CURSO") {
        const minuto = f.minuto_juego || "En Juego";
        badgeHtml = `<span class="badge-status-live"><span class="badge-pulse"></span>${minuto}</span>`;
    } else if (estado === "FINALIZADO") {
        badgeHtml = `<span class="badge-status-finished">🏁 FINALIZADO</span>`;
    } else if (estado === "REPROGRAMADO") {
        badgeHtml = `<span class="badge-status-postponed">⏳ Fecha Lejana</span>`;
    }

    // Checkbox — solo visible y habilitado si es PROGRAMADO
    const checkboxHtml = esSeleccionable
        ? `<input type="checkbox" checked
               style="accent-color: #38BDF8; cursor: pointer; width: 15px; height: 15px;"
               value="${f.id_partido}"
               class="fixture-checkbox"
               onchange="toggleFixtureCheckbox(this, '${f.id_partido}')">`
        : `<input type="checkbox" disabled
               style="cursor: not-allowed; opacity: 0.25; width: 15px; height: 15px;"
               value="${f.id_partido}"
               class="fixture-checkbox">`;

    // Marcador (EN_CURSO o FINALIZADO con números reales)
    let marcadorHtml = "";
    if (f.marcador_actual) {
        const cls = estado === "EN_CURSO" ? "score-live" : "score-final";
        const textoMarcador = (f.marcador_actual === "MARCADOR_PENDIENTE") ? "Finalizado" : f.marcador_actual;
        marcadorHtml = `<span class="${cls}" style="font-weight: 800; font-size: 8.5pt; color: ${estado === 'EN_CURSO' ? '#EF4444' : '#38BDF8'}; margin-left: 6px;">${textoMarcador}</span>`;
    }

    // Escudos de ambos equipos
    const localEscudo = f.local_escudo_url
        ? `<img src="${f.local_escudo_url}" alt="" style="width:16px;height:16px;object-fit:contain;vertical-align:middle;margin-right:4px;">`
        : "";
    const visEscudo = f.visitante_escudo_url
        ? `<img src="${f.visitante_escudo_url}" alt="" style="width:16px;height:16px;object-fit:contain;vertical-align:middle;margin-right:4px;">`
        : "";

    // Nombre del partido con escudos
    const partidoHtml = `
        <span style="display:inline-flex;align-items:center;gap:4px;">
            ${localEscudo}<span style="color:#FFFFFF;font-weight:700;">${f.local}</span>
        </span>
        <span style="color:#64748B;font-size:8pt;margin:0 4px;">vs</span>
        <span style="display:inline-flex;align-items:center;gap:4px;">
            ${visEscudo}<span style="color:#FFFFFF;font-weight:700;">${f.visitante}</span>
        </span>
    `;

    // Cuotas 1X2 (solo para operables o como referencia en finalizados)
    let cuotasHtml = "";
    if (f.momios && f.momios.L) {
        const paBadge = f.momios.pago_anticipado
            ? `<span style="color:#00E676;font-weight:700;font-size:6.8pt;margin-left:4px;">🏷️ PA</span>` : "";
        const cuotaColor = estado === "FINALIZADO" ? "#64748B" : "#38BDF8";
        cuotasHtml = `
            <span>L <strong style="color:${cuotaColor};">${Number(f.momios.L).toFixed(2)}</strong></span>
            <span>E <strong style="color:#94A3B8;">${Number(f.momios.E).toFixed(2)}</strong></span>
            <span>V <strong style="color:#94A3B8;">${Number(f.momios.V).toFixed(2)}</strong></span>
            ${paBadge}
        `;
    } else if (estado === "PROGRAMADO") {
        cuotasHtml = `<span style="color:#94A3B8;font-size:6.8pt;font-style:italic;">⏳ Cuotas Pendientes</span>`;
    }

    card.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
            <div style="display:flex;align-items:center;gap:6px;">
                <span style="font-size:7pt;color:#94A3B8;">⏰ ${f.horario}</span>
                ${badgeHtml}
                ${marcadorHtml}
            </div>
            ${checkboxHtml}
        </div>
        <div style="font-size:9.2pt;font-weight:700;margin-bottom:4px;display:flex;align-items:center;flex-wrap:wrap;gap:4px;">
            ${partidoHtml}
        </div>
        <div style="font-size:7pt;color:#cbd5e1;display:flex;gap:8px;align-items:center;">
            ${cuotasHtml}
        </div>
    `;

    container.appendChild(card);
}

// [DES-QBE-016-C] Clicabilidad Total de Tarjeta (Card-Level Clickability)
function habilitarClicTarjetaCompleta() {
    document.querySelectorAll('.fixture-card').forEach(card => {
        // Evitar doble registro de listeners
        if (card.dataset.listenerBound) return;
        card.dataset.listenerBound = "true";

        card.addEventListener("click", (e) => {
            const estado = card.dataset.estado;

            // Bloquear interacción en tarjetas deshabilitadas
            if (card.classList.contains("fixture-disabled") ||
                estado === "FINALIZADO" || estado === "REPROGRAMADO") {
                return;
            }

            const checkbox = card.querySelector("input[type='checkbox']");
            if (!checkbox || checkbox.disabled) return;

            // Clic en área de tarjeta (no directamente en el checkbox): alternar manualmente
            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
            }

            // Actualizar estilo visual de selección
            const matchId = card.dataset.matchId;
            if (checkbox.checked) {
                card.classList.add("selected");
                card.style.borderColor = "#38BDF8";
                if (matchId && !selectedMatchIds.includes(matchId)) {
                    selectedMatchIds.push(matchId);
                }
            } else {
                card.classList.remove("selected");
                card.style.borderColor = "#334155";
                if (matchId) {
                    selectedMatchIds = selectedMatchIds.filter(id => id !== matchId);
                }
            }

            // Actualizar contador (sin disparar change para evitar doble-toggle)
            actualizarContadorSeleccionados();
        });
    });
}

// [DES-QBE-016] Selector único: feedback visual por borde cian (manejador de evento nativo)
function toggleFixtureCheckbox(checkbox, matchId) {
    const card = document.getElementById(`fixture-card-${matchId}`);
    if (checkbox.checked) {
        if (!selectedMatchIds.includes(matchId)) selectedMatchIds.push(matchId);
        if (card) {
            card.classList.add("selected");
            card.style.borderColor = "#38BDF8";
            card.style.backgroundColor = "rgba(56, 189, 248, 0.05)";
        }
    } else {
        selectedMatchIds = selectedMatchIds.filter(id => id !== matchId);
        if (card) {
            card.classList.remove("selected");
            card.style.borderColor = "#334155";
            card.style.backgroundColor = "rgba(0,230,118,0.04)";
        }
    }
    actualizarContadorSeleccionados();
}

function actualizarContadorSeleccionados() {
    const lbl = document.getElementById("lbl-partidos-seleccionados");
    if (lbl) lbl.textContent = `${selectedMatchIds.length} partido${selectedMatchIds.length !== 1 ? 's' : ''} seleccionado${selectedMatchIds.length !== 1 ? 's' : ''}`;
}

async function ejecutarDespachoPortafolio() {
    if (!currentLiveBoard) {
        alert("Por favor seleccione primero una liga en el Hub.");
        return;
    }
    if (selectedMatchIds.length === 0) {
        alert("Debe seleccionar al menos 1 partido en la cartelera.");
        return;
    }

    const bankrollInput = document.getElementById('bankroll-input');
    const bankroll = bankrollInput ? parseFloat(bankrollInput.value) : 200.0;

    switchView("tab-portfolio");
    const tbody = document.getElementById("cuerpo-tabla-ordenes") || document.querySelector("#tabla-ordenes-inversion tbody");
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #38BDF8; padding: 25px;">⏳ Ejecutando motor cuantitativo (Poisson 6x6, Kelly & Dutching V=0)...</td></tr>';
    }

    try {
        const resp = await fetch('/api/portfolio/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                league_id: currentLiveBoard.league_id || 262,
                selected_match_ids: selectedMatchIds,
                bankroll: bankroll,
                mode: "BANKROLL"
            })
        });

        if (!resp.ok) {
            const errData = await resp.json().catch(() => ({}));
            throw new Error(errData.detail || "Error en cálculo de portafolio");
        }
        const data = await resp.json();
        renderizarResultadosPortafolio(data);
    } catch (e) {
        console.error("Error generando portafolio:", e);
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #ef4444; padding: 25px;">❌ Error en motor: ${e.message}</td></tr>`;
        }
    }
}
window.ejecutarDespachoPortafolio = ejecutarDespachoPortafolio;

function renderizarResultadosPortafolio(data) {
    const tbody = document.getElementById("cuerpo-tabla-ordenes") || document.querySelector("#tabla-ordenes-inversion tbody");
    if (!tbody) return;
    tbody.innerHTML = '';

    const orders = data.ordenes || [];
    const balance = data.balance || {};

    // Actualizar Macro KPIs
    const lblInv = document.getElementById("kpi-inversion-total");
    if (lblInv) lblInv.textContent = `$${(balance.capital_total_comprometido_mxn || 0).toFixed(2)} MXN`;
    const lblEv = document.getElementById("kpi-ganancia-esperada");
    if (lblEv) lblEv.textContent = `+$${(balance.ganancia_neta_esperada_jornada_mxn || 0).toFixed(2)} MXN`;
    const lblRoi = document.getElementById("kpi-roi-global");
    if (lblRoi) lblRoi.textContent = `+${(balance.roi_global_esperado_porcentaje || 0).toFixed(1)}%`;

    if (orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #94A3B8; padding: 25px;">🛡️ Capital protegido al 100% ($0.00 en riesgo). Ningún partido superó el umbral de ventaja matemática (+EV).</td></tr>';
        return;
    }

    orders.forEach(ord => {
        const tr = document.createElement('tr');
        const b1 = ord.boletos?.boleto_1_seguro;
        const b2 = ord.boletos?.boleto_2_ganancia;
        const seguroTexto = (b1 && b1.monto_mxn > 0) ? `Empate ($${b1.monto_mxn.toFixed(2)} @${b1.momio.toFixed(2)})` : 'Directo (Sin Cobertura)';
        const gananciaTexto = (b2) ? `${b2.seleccion} ($${b2.monto_mxn.toFixed(2)} a @${b2.momio.toFixed(2)})` : '—';
        const invTotal = ord.boletos?.inversion_partido_A_i ?? 0;
        const estCod = ord.estrategia_seleccionada?.codigo || "QBE-D1";

        tr.innerHTML = `
            <td style="font-weight: 600; color: #fff;">${ord.partido}</td>
            <td><span class="badge-estrategia" style="background: rgba(56,189,248,0.15); color: #38BDF8; padding: 2px 6px; border-radius: 4px; font-size: 8pt; font-weight: 700;">${estCod}</span></td>
            <td style="color: #94A3B8;">${seguroTexto}</td>
            <td style="color: #00E676; font-weight: 600;">${gananciaTexto}</td>
            <td style="text-align: right; font-weight: 700; color: #fff;">$${Number(invTotal).toFixed(2)} MXN</td>
        `;
        tbody.appendChild(tr);
    });
}

// ─── Funciones del Panel de Curación Agéntica HITL [ARCH-1.5.2] ─────────────
async function abrirModalCurador(leagueId = 262) {
    document.getElementById("modal-curador-hitl").style.display = "block";
    const grid = document.getElementById("grid-curacion-clubes");
    grid.innerHTML = '<div style="color:#38BDF8; padding:20px;">🔍 Cargando candidatos prospectados...</div>';
    
    try {
        const resp = await fetch(`/api/admin/catalogs/staging?league_id=${leagueId}`);
        const teams = await resp.json();
        grid.innerHTML = "";
        
        teams.forEach(t => {
            const card = document.createElement("div");
            card.style.cssText = "background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 12px;";
            
            // Priorizar ruta local soberana con fallback a candidate_url
            const imgSrc = t.crest_url || t.crest_candidate_url;

            card.innerHTML = `
                <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 8px;">
                    <img src="${imgSrc}" onerror="this.src='${t.crest_candidate_url}'" referrerpolicy="no-referrer" alt="" style="width: 36px; height: 36px; object-fit: contain;">
                    <div>
                        <strong style="color: #fff; font-size: 9pt;">${t.name}</strong>
                        <div style="color: #94A3B8; font-size: 7.2pt;">Estadio: ${t.stadium} (${t.city})</div>
                    </div>
                </div>
                <div style="font-size: 6.8pt; color: #38BDF8; margin-bottom: 8px;">Aliases: ${(t.aliases || []).join(", ")}</div>
                <div style="display: flex; justify-content: flex-end;">
                    <span style="color: #00E676; font-size: 7.2pt; font-weight: 700;">✅ Validado</span>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (e) {
        grid.innerHTML = `<div style="color:#f87171;">Error: ${e.message}</div>`;
    }
}

function cerrarModalCurador() {
    document.getElementById("modal-curador-hitl").style.display = "none";
}

async function sellarCatalogoCompleto(leagueId = 262) {
    try {
        const stagedResp = await fetch(`/api/admin/catalogs/staging?league_id=${leagueId}`);
        const teams = await stagedResp.json();
        
        const commitResp = await fetch("/api/admin/catalogs/commit", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({league_id: leagueId, approved_teams: teams})
        });
        const res = await commitResp.json();
        alert(`✅ Catálogo sellado con éxito: ${res.teams_committed} clubes guardados en SQLite.`);
        cerrarModalCurador();
        location.reload();
    } catch (e) {
        alert(`❌ Error al sellar: ${e.message}`);
    }
}

// [FAST-TRACK FIX]: Exponer funciones del Modal Curador al ámbito global
window.abrirModalCurador = typeof abrirModalCurador !== 'undefined' ? abrirModalCurador : function() {
    const modal = document.getElementById('modalCurador') || document.getElementById('modal-curador');
    if (modal) modal.style.display = 'flex';
};

window.cerrarModalCurador = typeof cerrarModalCurador !== 'undefined' ? cerrarModalCurador : function() {
    const modal = document.getElementById('modalCurador') || document.getElementById('modal-curador');
    if (modal) modal.style.display = 'none';
};

window.sellarCatalogoCompleto = typeof sellarCatalogoCompleto !== 'undefined' ? sellarCatalogoCompleto : function() {
    console.log("Sellando catálogo...");
};

// Funciones globales para control masivo de selección en cartelera
function seleccionarTodosPartidos() {
    selectedMatchIds = [];
    document.querySelectorAll('.fixture-card:not(.fixture-disabled)').forEach(card => {
        const checkbox = card.querySelector("input[type='checkbox']");
        const matchId = card.dataset.matchId;
        if (checkbox && !checkbox.disabled) {
            checkbox.checked = true;
            card.classList.add("selected");
            card.style.borderColor = "#38BDF8";
            if (matchId) selectedMatchIds.push(matchId);
        }
    });
    actualizarContadorSeleccionados();
}

function deseleccionarTodosPartidos() {
    selectedMatchIds = [];
    document.querySelectorAll('.fixture-card').forEach(card => {
        const checkbox = card.querySelector("input[type='checkbox']");
        if (checkbox) {
            checkbox.checked = false;
        }
        card.classList.remove("selected");
        card.style.borderColor = "#334155";
    });
    actualizarContadorSeleccionados();
}

// Exponer al ámbito global
window.seleccionarTodosPartidos = seleccionarTodosPartidos;
window.deseleccionarTodosPartidos = deseleccionarTodosPartidos;
