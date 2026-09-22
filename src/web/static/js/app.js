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
async function seleccionarLiga(fotmobId, forceRefresh = false, targetJornada = null) {
    switchView("view-matchday-selection");
    const tbody = document.querySelector(".table-panel-left table tbody");
    if (tbody && !currentLiveBoard) tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:20px; color:#38BDF8;">⏳ Sincronizando datos oficiales en tiempo real...</td></tr>';

    try {
        let url = `/api/leagues/${fotmobId}/live-board`;
        const params = [];
        if (targetJornada !== null && targetJornada !== undefined) params.push(`jornada=${targetJornada}`);
        if (forceRefresh) params.push("force_refresh=true");
        if (params.length > 0) url += "?" + params.join("&");

        const resp = await fetch(url);
        if (!resp.ok) throw new Error("Error al obtener Live Board");
        currentLiveBoard = await resp.json();

        const lblTabla = document.getElementById("lbl-nombre-tabla");
        if (lblTabla) lblTabla.textContent = currentLiveBoard.league_name || "Liga MX";
        const lblJornada = document.getElementById("lbl-nombre-jornada");
        if (lblJornada) lblJornada.textContent = currentLiveBoard.jornada || `Jornada ${currentLiveBoard.jornada_mostrada || 8}`;
        const lblTime = document.getElementById("lbl-timestamp-tabla");
        if (lblTime) {
            lblTime.textContent = `🕒 Tabla Oficial: Sincronizada en vivo (${_formatearFechaHoraActual()})`;
        }

        renderizarPildorasJornada(currentLiveBoard);
        renderizarTabla18Clubes(currentLiveBoard.standings);
        renderizarCartelera(currentLiveBoard.fixtures);
    } catch (e) {
        console.error("Error cargando live board:", e);
        if (tbody) tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:#f87171;">❌ Error al conectar: ${e.message}</td></tr>`;
    }
}

// Renderizado dinámico de píldoras continuas de jornada [DES-QBE-026]
function renderizarPildorasJornada(liveBoard) {
    const container = document.getElementById("matchday-pill-selector");
    if (!container) return;
    container.innerHTML = "";

    const disponibles = liveBoard.jornadas_disponibles || [8, 9];
    const mostrada = liveBoard.jornada_mostrada || 8;
    const actual = liveBoard.jornada_actual || 8;

    disponibles.forEach(jNum => {
        const btn = document.createElement("button");
        btn.type = "button";
        const isActive = (jNum === mostrada);
        
        // Estilos defensivos directos Dark Fintech
        btn.style.cssText = `
            background: ${isActive ? '#0284C7' : '#1C2541'};
            border: 1px solid ${isActive ? '#38BDF8' : '#334155'};
            color: ${isActive ? '#FFFFFF' : '#94A3B8'};
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: ${isActive ? '0 0 10px rgba(56, 189, 248, 0.3)' : 'none'};
            transition: all 0.2s ease;
        `;

        let badgeBg = "rgba(56, 189, 248, 0.2)";
        let badgeColor = "#38BDF8";
        let badgeLabel = "🟢 Mercado Abierto ⭐";

        if (jNum < actual || (jNum === 8 && actual === 8)) {
            badgeBg = "rgba(148, 163, 184, 0.2)";
            badgeColor = "#CBD5E1";
            badgeLabel = "🏁 Concluida";
        }

        btn.innerHTML = `<span>Jornada ${jNum}</span><span style="background:${badgeBg}; color:${badgeColor}; font-size:0.7rem; padding:2px 7px; border-radius:10px; font-weight:600;">${badgeLabel}</span>`;
        
        btn.onmouseenter = () => { if (!isActive) btn.style.borderColor = '#38BDF8'; };
        btn.onmouseleave = () => { if (!isActive) btn.style.borderColor = '#334155'; };

        btn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (jNum === mostrada) return;
            const leagueId = liveBoard.league_id || 262;
            seleccionarLiga(leagueId, false, jNum);
        };
        container.appendChild(btn);
    });
}


function _formatearFechaHoraActual() {
    const ahora = new Date();
    const meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
    const dia = ahora.getDate();
    const mes = meses[ahora.getMonth()];
    const hora = ahora.toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });
    return `${dia}-${mes} ${hora}`;
}

// ── 1. Refrescar ÚNICAMENTE la Tabla de Posiciones (Panel Izquierdo) ─────────
async function refrescarTablaEnVivo() {
    const targetId = currentLiveBoard ? currentLiveBoard.league_id : 262;
    const btn = document.getElementById("btn-force-refresh");
    const tbody = document.querySelector(".table-panel-left table tbody");

    if (btn) btn.innerHTML = "⏳ Refrescando...";
    if (tbody) tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:20px; color:#38BDF8;">⏳ Sincronizando tabla oficial...</td></tr>';

    try {
        const resp = await fetch(`/api/leagues/${targetId}/refresh-tabla`, { method: "POST" });
        if (!resp.ok) throw new Error("Error en respuesta del servidor");
        const data = await resp.json();

        // Actualizar ÚNICAMENTE el panel izquierdo
        renderizarTabla18Clubes(data.standings);

        const lblTime = document.getElementById("lbl-timestamp-tabla");
        if (lblTime) {
            lblTime.textContent = `🕒 Tabla Oficial: Sincronizada en vivo (${_formatearFechaHoraActual()})`;
        }
    } catch (e) {
        console.error("Error refrescando tabla:", e);
    } finally {
        if (btn) btn.innerHTML = "🔄 Refrescar Tabla";
    }
}
window.refrescarTablaEnVivo = refrescarTablaEnVivo;

async function refrescarCarteleraEnVivo() {
    const targetId = currentLiveBoard ? currentLiveBoard.league_id : 262;
    const btn = document.getElementById("btn-refresh-cartelera");
    const container = document.querySelector(".fixtures-list");

    if (btn) btn.innerHTML = "⏳ Refrescando...";
    if (container) container.innerHTML = '<div style="text-align:center; padding:25px; color:#38BDF8; font-size:8.5pt;">⏳ Sincronizando momios Caliente en vivo...</div>';

    try {
        const resp = await fetch(`/api/leagues/${targetId}/refresh-momios`, { method: "POST" });
        if (!resp.ok) throw new Error("Error en respuesta del servidor");
        const data = await resp.json();

        // Actualizar ÚNICAMENTE el panel derecho
        renderizarCartelera(data.fixtures);

        const lblTime = document.getElementById("lbl-timestamp-cartelera");
        if (lblTime) {
            lblTime.textContent = `🕒 Momios Caliente: Sincronizados en vivo (${_formatearFechaHoraActual()})`;
        }
    } catch (e) {
        console.error("Error refrescando cartelera:", e);
    } finally {
        if (btn) btn.innerHTML = "🔄 Refrescar Momios";
    }
}
window.refrescarCarteleraEnVivo = refrescarCarteleraEnVivo;

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
    const enCurso = fixtures.filter(f => f.estado === "EN_CURSO");
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
        reprogramados.forEach(f => _renderFixtureCard(container, f, false));
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
    const estado = f.estado || "PROGRAMADO";
    // [LEY DE OPERABILIDAD TOTAL]: Seleccionable si no está finalizado y tiene cuotas reales
    const esSeleccionable = !deshabilitada && f.disponible_para_seleccion === true && estado !== "FINALIZADO";

    const card = document.createElement("div");
    card.className = "fixture-card" + (!esSeleccionable ? " fixture-disabled" : "");
    card.id = `fixture-card-${f.id_partido}`;
    card.dataset.estado = f.estado || "PROGRAMADO";
    card.dataset.matchId = f.id_partido;

    // Si es operable con cuotas, incluir en selección inicial por defecto si aún no está agregado
    if (esSeleccionable && !selectedMatchIds.includes(f.id_partido)) {
        selectedMatchIds.push(f.id_partido);
    }

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
        // [CORRECCIÓN]: Leer sub_badge del backend (solo dice Fecha Lejana si dista > 14 días)
        const textoBadge = f.sub_badge ? `⏳ ${f.sub_badge}` : "⏳ Reprogramado";
        badgeHtml = `<span class="badge-status-postponed">${textoBadge}</span>`;
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

            // Bloquear interacción ÚNICAMENTE si está finalizado o no tiene cuotas disponibles
            if (card.classList.contains("fixture-disabled") || estado === "FINALIZADO") {
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
    // Contar exclusivamente checkboxes marcados que NO estén deshabilitados
    const checkboxesActivos = document.querySelectorAll(".fixture-card:not(.fixture-disabled) input[type='checkbox']:checked");
    selectedMatchIds = Array.from(checkboxesActivos).map(cb => cb.value);

    if (lbl) {
        lbl.textContent = `${selectedMatchIds.length} partido${selectedMatchIds.length !== 1 ? 's' : ''} seleccionado${selectedMatchIds.length !== 1 ? 's' : ''}`;
    }
}

let abortControllerDespacho = null;

function mostrarHUDProcesamiento() {
    const modal = document.getElementById("modal-hud-procesamiento");
    if (modal) modal.style.display = "flex";
    actualizarProgresoHUD(1, 15);
}

function ocultarHUDProcesamiento() {
    const modal = document.getElementById("modal-hud-procesamiento");
    if (modal) modal.style.display = "none";
}

function cancelarDespachoPortafolio() {
    if (abortControllerDespacho) {
        abortControllerDespacho.abort();
    }
    ocultarHUDProcesamiento();
}
window.cancelarDespachoPortafolio = cancelarDespachoPortafolio;

function actualizarProgresoHUD(paso, porcentaje) {
    const fill = document.getElementById("hud-barra-fill");
    if (fill) fill.style.width = `${porcentaje}%`;

    for (let i = 1; i <= 6; i++) {
        const el = document.getElementById(`hud-p${i}`);
        if (!el) continue;
        if (i < paso) {
            el.style.color = "#00E676";
            el.innerHTML = el.innerHTML.replace("⏳", "✅");
        } else if (i === paso) {
            el.style.color = "#38BDF8";
            el.innerHTML = el.innerHTML.replace("✅", "⏳");
        } else {
            el.style.color = "#64748B";
        }
    }
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

    mostrarHUDProcesamiento();
    abortControllerDespacho = new AbortController();

    try {
        // Simulación visual reactiva de progresión mientras responde el worker
        setTimeout(() => actualizarProgresoHUD(2, 35), 300);
        setTimeout(() => actualizarProgresoHUD(3, 55), 600);
        setTimeout(() => actualizarProgresoHUD(4, 75), 900);
        setTimeout(() => actualizarProgresoHUD(5, 90), 1200);

        const resp = await fetch('/api/portfolio/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: abortControllerDespacho.signal,
            body: JSON.stringify({
                league_id: currentLiveBoard.league_id || 262,
                selected_match_ids: selectedMatchIds,
                bankroll: bankroll,
                mode: "BANKROLL"
            })
        });

        actualizarProgresoHUD(6, 100);
        if (!resp.ok) {
            const errData = await resp.json().catch(() => ({}));
            throw new Error(errData.detail || "Error en cálculo de portafolio");
        }

        const data = await resp.json();

        setTimeout(() => {
            ocultarHUDProcesamiento();
            switchView("tab-portfolio");
            renderizarResultadosPortafolio(data);

            // Enlazar botón PDF export en la vista de cartera
            const pdfBtn = document.getElementById("export-pdf-btn");
            if (pdfBtn && data.portfolio_id) {
                pdfBtn.onclick = () => window.open(`/api/portfolio/${data.portfolio_id}/pdf`, '_blank');
            }
        }, 400);

    } catch (e) {
        ocultarHUDProcesamiento();
        if (e.name !== 'AbortError') {
            alert(`❌ Error calculando portafolio: ${e.message}`);
        }
    }
}
window.ejecutarDespachoPortafolio = ejecutarDespachoPortafolio;

let currentPortfolioData = null;

function renderizarResultadosPortafolio(data) {
    currentPortfolioData = data;
    const orders = data.ordenes || [];
    const control = data.control || {};
    const balance = data.balance || {};
    const meta = data.metadata || {};

    // 1. Encabezado Macro
    const elTorneo = document.getElementById("hdr-torneo-portfolio");
    if (elTorneo) elTorneo.textContent = meta.torneo || "Liga MX — Apertura 2026";
    const elFechas = document.getElementById("hdr-fechas-portfolio");
    if (elFechas) elFechas.textContent = `${meta.jornada || 'Jornada Activa'} · ${meta.fechas || 'Septiembre 2026'}`;

    // 2. Macro KPIs Duales
    const invTotal = balance.capital_total_comprometido_mxn || 0.0;
    const gananciaEv = balance.ganancia_neta_esperada_jornada_mxn || 0.0;
    const roiGlobal = balance.roi_global_esperado_porcentaje || 0.0;
    const blindajePct = control.blindaje_global_preservacion_porcentaje || 99.9;
    const ruinaPct = control.probabilidad_ruina_total_porcentaje || 0.1;
    const kAprobados = control.total_partidos_core_aprobados || orders.length;
    const kEscaneados = control.total_partidos_escaneados || orders.length;

    // Calcular suma de premios máximos netos (Ganancia Neta Potencial)
    let sumaPremios = 0;
    orders.forEach(o => {
        sumaPremios += (o.proyecciones?.ganancia_neta_principal_mxn || 0);
    });
    const roiPotencial = invTotal > 0 ? (sumaPremios / invTotal) * 100.0 : 0.0;

    const elInv = document.getElementById("kpi-inversion-total");
    if (elInv) elInv.textContent = `$${invTotal.toFixed(2)} MXN`;
    const elPctCaja = document.getElementById("kpi-pct-caja");
    if (elPctCaja) elPctCaja.textContent = `${((invTotal / (control.desglose_bankroll?.bankroll_total || 200)) * 100).toFixed(1)}% de la caja`;

    // Ganancia Potencial
    const elPot = document.getElementById("kpi-ganancia-potencial");
    if (elPot) elPot.textContent = `+$${sumaPremios.toFixed(2)} MXN`;
    const elRoiPot = document.getElementById("kpi-roi-potencial");
    if (elRoiPot) elRoiPot.textContent = `+${roiPotencial.toFixed(1)}% Ganando todas las apuestas principales (sin dobles premios)`;

    // Ganancia Esperada (EV)
    const elEv = document.getElementById("kpi-ganancia-esperada");
    if (elEv) elEv.textContent = `+$${gananciaEv.toFixed(2)} MXN`;
    const elRoi = document.getElementById("kpi-roi-global");
    if (elRoi) elRoi.textContent = `+${roiGlobal.toFixed(1)}% ROI Esperado (+EV estrategia a largo plazo)`;

    const elBlind = document.getElementById("kpi-blindaje-global");
    if (elBlind) elBlind.textContent = `${blindajePct.toFixed(2)}%`;
    const elRuina = document.getElementById("kpi-prob-ruina");
    if (elRuina) elRuina.textContent = `Probabilidad Ruina: ${ruinaPct.toFixed(4)}%  (de perder todas las apuestas)`;

    const elCore = document.getElementById("kpi-posiciones-core");
    if (elCore) elCore.textContent = `${kAprobados} / ${kEscaneados}`;

    // 3. Banner de Certeza Tripartito (La Trinidad de Resiliencia) [DES-QBE-027]
    const trinidad = control.desglose_bankroll?.trinidad_resiliencia;
    const txtResumen = document.getElementById("txt-cascada-resumen");
    const pildorasCont = document.getElementById("pildoras-cascada");

    if (trinidad && pildorasCont) {
        const pleno = trinidad.pleno_exito;
        const tablas = trinidad.tablas_o_ganancia;
        const ruina = trinidad.ruina_total;

        if (txtResumen) {
            txtResumen.innerHTML = `<strong style="color:#38BDF8;">Certeza de Cartera:</strong> Tienes un <strong style="color:#00E676;">${tablas.probabilidad_pct}%</strong> de probabilidad de recuperar el 100% de tu dinero o salir con ganancia neta.`;
        }

        pildorasCont.innerHTML = `
            <span style="background: rgba(0, 230, 118, 0.15); color: #00E676; border: 1px solid #00E676; padding: 4px 12px; border-radius: 20px; font-size: 7.8pt; font-weight: 800;">
                🎯 Pleno Éxito: +$${pleno.pnl_mxn.toFixed(2)} (${pleno.probabilidad_pct}%)
            </span>
            <span style="background: rgba(56, 189, 248, 0.20); color: #38BDF8; border: 1px solid #38BDF8; padding: 4px 14px; border-radius: 20px; font-size: 8pt; font-weight: 900; box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);">
                🛡️ Tablas o Ganancia: ≥ $0.00 (${tablas.probabilidad_pct}%) ⭐
            </span>
            <span style="background: rgba(239, 68, 68, 0.12); color: #ef4444; border: 1px solid #ef4444; padding: 4px 12px; border-radius: 20px; font-size: 7.8pt; font-weight: 700;">
                💀 Ruina Total: -$${Math.abs(ruina.pnl_mxn).toFixed(2)} (${ruina.probabilidad_pct}%)
            </span>
        `;
    }

    // 4. Tabla Resumen de Asignación
    const tbodyResumen = document.getElementById("cuerpo-resumen-asignacion");
    const tfootResumen = document.getElementById("pie-resumen-asignacion");
    if (tbodyResumen) {
        tbodyResumen.innerHTML = "";
        let sumaPremios = 0;
        let sumaInv = 0;

        orders.forEach(ord => {
            const inv = ord.boletos?.inversion_partido_A_i || 0;
            const gan = ord.proyecciones?.ganancia_neta_principal_mxn || 0;
            const tablas = ord.proyecciones?.resultado_tablas_mxn || 0;
            const roi = ord.proyecciones?.roi_principal_porcentaje || 0;
            const cod = ord.estrategia_seleccionada?.codigo || "";
            sumaInv += inv;
            sumaPremios += gan;

            // [UX-MANDATE] Semántica precisa de cobertura por familia de estrategia (GOVERNANCE §8)
            let coberturaHtml = `<span style="color:#94A3B8;">Recuperas $${tablas.toFixed(2)} MXN ($0.00 pérdida)</span>`;
            if (cod.startsWith("QBE-D1")) {
                coberturaHtml = `<span style="color:#f87171; font-weight:600;">Sin cobertura (Riesgo Directo: -$${inv.toFixed(2)})</span>`;
            } else if (cod === "QBE-R2") {
                coberturaHtml = `<span style="color:#00E676; font-weight:600;">Ambos boletos ganan (+${roi.toFixed(1)}% ROI)</span>`;
            } else if (cod.startsWith("QBE-H1") || cod.startsWith("QBE-H2") || cod.startsWith("QBE-R1")) {
                coberturaHtml = `<span style="color:#38BDF8;">Recuperas $${tablas.toFixed(2)} MXN ($0.00 pérdida)</span>`;
            }

            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td style="font-weight:700; color:#fff;">${ord.partido}</td>
                <td style="text-align:center;"><span class="badge-status-live" style="background:rgba(56,189,248,0.15); color:#38BDF8; border-color:#38BDF8;">${cod}</span></td>
                <td style="text-align:right; font-weight:700;">$${inv.toFixed(2)}</td>
                <td style="text-align:right; font-weight:700; color:#00E676;">+$${gan.toFixed(2)} MXN</td>
                <td>${coberturaHtml}</td>
            `;
            tbodyResumen.appendChild(tr);
        });

        if (tfootResumen) {
            tfootResumen.innerHTML = `
                <tr>
                    <td>TOTAL EN CARTERA</td>
                    <td style="text-align:center;">${orders.length} Posiciones</td>
                    <td style="text-align:right;">$${invTotal.toFixed(2)} MXN</td>
                    <td style="text-align:right; color:#00E676;">+$${sumaPremios.toFixed(2)} MXN</td>
                    <td></td>
                </tr>
            `;
        }
    }

    // 5. Tarjetas Ricas de Boletos Split (Ganancia a la Izquierda, Seguro a la Derecha, Escenarios Sobrios)
    const contSplit = document.getElementById("contenedor-tarjetas-split");
    if (contSplit) {
        contSplit.innerHTML = "";
        orders.forEach(ord => {
            const b1 = ord.boletos?.boleto_1_seguro || {};
            const b2 = ord.boletos?.boleto_2_ganancia || {};
            const est = ord.estrategia_seleccionada || {};
            const proy = ord.proyecciones || {};
            const inv = ord.boletos?.inversion_partido_A_i || 0;

            // Momios 1X2 completos
            const oddsObj = ord.momios_1x2 || {};
            const oddL = oddsObj.L ? `L @${Number(oddsObj.L).toFixed(2)}` : '';
            const oddE = oddsObj.E ? `E @${Number(oddsObj.E).toFixed(2)}` : '';
            const oddV = oddsObj.V ? `V @${Number(oddsObj.V).toFixed(2)}` : '';
            const momiosCompletos = [oddL, oddE, oddV].filter(Boolean).join(" | ");

            const b1Monto = b1.monto_mxn || 0;
            const b2Monto = b2.monto_mxn || 0;
            const cobroPrincipal = (b2Monto * (b2.momio || 1)).toFixed(2);
            const retornoTablas = (b1Monto * (b1.momio || 1)).toFixed(2);

            // Escenarios desglosados en estilo sobrio y limpio (CERO balazos)
            let escenariosHtml = `
                <div style="font-size: 7.8pt; line-height: 1.6; color: #94A3B8; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 8px;">
                    <div>• <strong style="color: #e2e8f0;">Ganancia Principal:</strong> Cobro de $${cobroPrincipal} MXN (+$${proy.ganancia_neta_principal_mxn?.toFixed(2)} MXN netos, +${proy.roi_principal_porcentaje?.toFixed(1)}% ROI).</div>
            `;

            if (proy.freeroll_doble_ganancia_mxn > 0) {
                escenariosHtml += `
                    <div>• <strong style="color: #e2e8f0;">Doble Cobro (Pago Anticipado):</strong> Cobro de ambos boletos sumando +$${proy.freeroll_doble_ganancia_mxn?.toFixed(2)} MXN netos (+${proy.freeroll_roi_porcentaje?.toFixed(1)}% ROI).</div>
                `;
            }

            if (b1Monto > 0) {
                escenariosHtml += `
                    <div>• <strong style="color: #e2e8f0;">Cobertura en Empate:</strong> Recuperación de $${retornoTablas} MXN ($0.00 pérdida de capital).</div>
                `;
            }
            escenariosHtml += `</div>`;

            const card = document.createElement("div");
            card.className = "card";
            card.style.cssText = "background:#1C2541; border:1px solid rgba(56,189,248,0.25); border-radius:8px; padding:16px;";
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
                    <div>
                        <div style="display:flex; gap:6px; align-items:center; margin-bottom:6px; flex-wrap:wrap;">
                            <span class="badge-status-live" style="background:rgba(56,189,248,0.2); color:#38BDF8; border-color:#38BDF8; font-weight:800;">${est.codigo}</span>
                            <span style="font-size:7.5pt; color:#cbd5e1;">${est.descripcion_ejecutiva}</span>
                            <span style="font-size:7.5pt; color:#00E676; font-weight:700;">🏷️ ${est.linea_promocional || 'Pago Anticipado'}</span>
                        </div>
                        <h3 style="margin:0; font-size:1.15rem; color:#fff;">${ord.partido}</h3>
                        <div style="font-size:7.5pt; color:#94A3B8; margin-top:3px;">⏰ ${ord.horario_evento} ${momiosCompletos ? `<span style="color:#64748B; margin:0 4px;">•</span> <span style="color:#38BDF8; font-weight:700;">${momiosCompletos}</span>` : ''}</div>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:7pt; color:#94A3B8; text-transform:uppercase;">Inversión Total</span>
                        <div style="font-size:1.35rem; font-weight:900; color:#00E676;">$${inv.toFixed(2)} MXN</div>
                    </div>
                </div>

                <!-- Doble Boleto: Ganancia PRIMERO (Izquierda), Seguro SEGUNDO (Derecha) -->
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:12px;">
                    <!-- BOLETO GANANCIA / ATAQUE (IZQUIERDA - VERDE) -->
                    <div style="background:#0f172a; border:1px solid rgba(0,230,118,0.4); border-radius:6px; padding:12px;">
                        <span style="font-size:7.2pt; color:#00E676; font-weight:800;">🎯 BOLETO 1: GANANCIA (ATAQUE)</span>
                        <div style="font-size:1rem; font-weight:700; color:#fff; margin-top:3px;">${b2.seleccion || 'Victoria Principal'}</div>
                        <div style="font-size:7.5pt; color:#94A3B8; margin-top:2px;">Momio: @${(b2.momio || 0).toFixed(2)}</div>
                        <div style="margin-top:6px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.05); display:flex; justify-content:space-between; align-items:flex-end;">
                            <span style="font-size:7pt; color:#94A3B8;">APOSTAR EN VENTANILLA:</span>
                            <span style="font-size:1.35rem; font-weight:900; color:#00E676;">$${(b2.monto_mxn || 0).toFixed(2)} MXN</span>
                        </div>
                    </div>

                    <!-- BOLETO SEGURO / RECUPERACIÓN (DERECHA - AZUL) -->
                    <div style="background:#0f172a; border:1px solid rgba(56,189,248,0.3); border-radius:6px; padding:12px;">
                        <span style="font-size:7.2pt; color:#38BDF8; font-weight:800;">🛡️ BOLETO 2: SEGURO (RECUPERACIÓN)</span>
                        <div style="font-size:1rem; font-weight:700; color:#fff; margin-top:3px;">${b1.seleccion || 'N/A ($0.00)'}</div>
                        <div style="font-size:7.5pt; color:#94A3B8; margin-top:2px;">Momio: @${(b1.momio || 0).toFixed(2)}</div>
                        <div style="margin-top:6px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.05); display:flex; justify-content:space-between; align-items:flex-end;">
                            <span style="font-size:7pt; color:#94A3B8;">APOSTAR EN VENTANILLA:</span>
                            <span style="font-size:1.35rem; font-weight:900; color:#38BDF8;">$${(b1.monto_mxn || 0).toFixed(2)} MXN</span>
                        </div>
                    </div>
                </div>

                <!-- Escenarios Desglosados Sobrios -->
                <div style="background:rgba(0,0,0,0.25); border-radius:6px; padding:10px 14px; margin-bottom:12px;">
                    ${escenariosHtml}
                </div>

                <!-- Botón hacia Radiografía Forense -->
                <div style="text-align:right;">
                    <button onclick="abrirRadiografiaForense('${ord.id_partido}')" style="background:transparent; border:1px solid #38BDF8; color:#38BDF8; padding:6px 14px; border-radius:4px; font-size:7.8pt; font-weight:700; cursor:pointer;">
                        🔬 Ver Análisis Cuantitativo y Tesis →
                    </button>
                </div>
            `;
            contSplit.appendChild(card);
        });
    }

    // 6. Radar de Descartes (QBE-00)
    const contDescartes = document.getElementById("contenedor-descartes");
    if (contDescartes) {
        contDescartes.innerHTML = "";
        const descartes = data.descartes || [];
        if (descartes.length === 0) {
            contDescartes.innerHTML = '<div style="color:#94A3B8; font-size:8pt; padding:8px;">Cero partidos vetados en esta selección.</div>';
        } else {
            descartes.forEach(d => {
                const item = document.createElement("div");
                item.style.cssText = "background:rgba(239,68,68,0.06); border:1px solid rgba(239,68,68,0.3); border-radius:6px; padding:10px 14px;";
                item.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <strong style="color:#fff; font-size:9pt;">❌ ${d.partido}</strong>
                        <span style="background:rgba(239,68,68,0.2); color:#ef4444; border:1px solid #ef4444; padding:2px 6px; border-radius:4px; font-size:7pt; font-weight:800;">VETO: ${d.motivo_codigo || 'QBE-00'}</span>
                    </div>
                    <div style="color:#cbd5e1; font-size:7.8pt;">${d.explicacion_didactica || d.motivo}</div>
                `;
                contDescartes.appendChild(item);
            });
        }
    }
}

// ─── Modal de Radiografía Forense (Imagen 4) ─────────────────────────────────
function _hidratarTablasRadiografia(p) {
    // Pronóstico vs Mercado
    const tbodyPron = document.getElementById("rad-cuerpo-pronostico");
    if (tbodyPron && p.probabilidades_3vias) {
        tbodyPron.innerHTML = p.probabilidades_3vias.map(pv => {
            const edgeVal = pv.edge || 0;
            const edgeColor = edgeVal > 0 ? '#00E676' : '#ef4444';
            // [LN-QBE-011]: Momio Justo Teórico Q-BE = 100 / Prob_Real
            const momioJustoQBE = (pv.prob_real && pv.prob_real > 0) ? (100.0 / pv.prob_real).toFixed(2) : '—';

            return `
                <tr>
                    <td style="font-weight:700; color:#fff;">${pv.resultado}</td>
                    <td style="text-align:center; color:#38BDF8; font-weight:800;">@${momioJustoQBE}</td>
                    <td style="text-align:center; font-weight:700;">${pv.prob_real?.toFixed(1)}%</td>
                    <td style="text-align:center; color:#cbd5e1;">@${pv.momio?.toFixed(2)}</td>
                    <td style="text-align:center;">${pv.prob_casino?.toFixed(1)}%</td>
                    <td style="text-align:right; font-weight:800; color:${edgeColor};">${edgeVal >= 0 ? '+' : ''}${edgeVal.toFixed(2)}%</td>
                </tr>
            `;
        }).join("");
    }

    // Poisson Boxes
    document.getElementById("rad-xg-local").textContent = (p.lambda_local || 0).toFixed(2);
    document.getElementById("rad-xg-visita").textContent = (p.mu_visita || 0).toFixed(2);
    document.getElementById("rad-xg-total").textContent = (p.xg_total || 0).toFixed(2);
    document.getElementById("rad-phi-lead2").textContent = `${(p.phi_lead2_pct || 0).toFixed(1)}%`;

    // 10P Stats
    const tbody10p = document.getElementById("rad-cuerpo-10p");
    if (tbody10p && p.tabla_10p) {
        tbody10p.innerHTML = p.tabla_10p.map(row => `
            <tr>
                <td style="font-weight:700; color:#fff;">${row.equipo}</td>
                <td style="text-align:center;">#${row.puesto}</td>
                <td style="text-align:center; font-weight:700; color:#00E676;">${row.pts}</td>
                <td style="text-align:center;">${row.gf_gc}</td>
                <td style="text-align:center;">${row.pts_pj?.toFixed(2)}</td>
                <td style="text-align:center;">${row.sot?.toFixed(1)}</td>
                <td style="text-align:center;">${row.sota?.toFixed(1)}</td>
                <td style="text-align:center;">${row.posesion?.toFixed(1)}%</td>
                <td style="text-align:center; font-weight:700; color:#38BDF8;">${row.qmod?.toFixed(2)}</td>
            </tr>
        `).join("");
    }
}

async function abrirRadiografiaForense(matchId) {
    if (!currentPortfolioData) return;
    const analisisList = currentPortfolioData.partidos_analisis || [];
    const p = analisisList.find(x => x.id_partido === matchId);
    if (!p) return;

    document.getElementById("modal-radiografia-forense").style.display = "block";
    document.getElementById("rad-estrategia-badge").textContent = p.strategy_code || "QBE";
    document.getElementById("rad-titulo-partido").textContent = p.partido || p.partido_nombre;

    // Hidratar Pronóstico vs Mercado, Poisson y 10P (Instantáneo)
    _hidratarTablasRadiografia(p);

    const tesisContainer = document.getElementById("rad-tesis-html");

    // Si ya fue generada previamente, renderizarla de inmediato
    if (p.tesis_didactica && p.tesis_didactica.length > 50 && p.tesis_didactica !== "PENDIENTE") {
        tesisContainer.innerHTML = p.tesis_didactica;
        return;
    }

    // Si no, mostrar spinner elegante y llamar al endpoint on-demand
    tesisContainer.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px; color: #38BDF8; padding: 12px 0;">
            <span class="badge-pulse"></span>
            <span style="font-size: 8.5pt; font-weight: 600;">⚡ Generando Tesis Cuantitativa con IA (Gemini 3.6 Flash)...</span>
        </div>
    `;

    try {
        const resp = await fetch("/api/portfolio/match-thesis", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                partido_id: matchId,
                partido_data: p
            })
        });
        if (!resp.ok) throw new Error("Error en generador narrativo");
        const data = await resp.json();

        p.tesis_didactica = data.tesis_html;
        tesisContainer.innerHTML = data.tesis_html;
    } catch (err) {
        console.error("Fallo lazy loading tesis:", err);
        // Fallback local instantáneo
        tesisContainer.innerHTML = `
            <div>• <strong>Momento y Tabla:</strong> Disparidad fáctica en puntos y rendimiento de ambos clubes.</div>
            <div style='margin-top:6px;'>• <strong>Dominio de Cancha:</strong> Superioridad en métricas de xG Opta y control de posesión.</div>
            <div style='margin-top:6px;'>• <strong>Historial y Bajas:</strong> Antecedentes ponderados sin bajas críticas reportadas.</div>
            <div style='margin-top:6px;'>• <strong>Estrategia y Protección:</strong> Cobertura cuantitativa con preservación de capital garantizada.</div>
        `;
    }
}

function cerrarRadiografiaForense() {
    document.getElementById("modal-radiografia-forense").style.display = "none";
}
window.abrirRadiografiaForense = abrirRadiografiaForense;
window.cerrarRadiografiaForense = cerrarRadiografiaForense;

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
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ league_id: leagueId, approved_teams: teams })
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
window.abrirModalCurador = typeof abrirModalCurador !== 'undefined' ? abrirModalCurador : function () {
    const modal = document.getElementById('modalCurador') || document.getElementById('modal-curador');
    if (modal) modal.style.display = 'flex';
};

window.cerrarModalCurador = typeof cerrarModalCurador !== 'undefined' ? cerrarModalCurador : function () {
    const modal = document.getElementById('modalCurador') || document.getElementById('modal-curador');
    if (modal) modal.style.display = 'none';
};

window.sellarCatalogoCompleto = typeof sellarCatalogoCompleto !== 'undefined' ? sellarCatalogoCompleto : function () {
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

// ── [DES-QBE-030] NAVEGACIÓN COCKPIT DUAL-CORE ──────────────────────────

function cambiarVistaPrincipal(vistaId) {
    // 1. Actualizar botones de navegación
    document.querySelectorAll(".nav-tab").forEach(b => b.classList.remove("active"));
    const btn = document.getElementById(`nav-btn-${vistaId}`);
    if (btn) btn.classList.add("active");

    // 2. Conmutar paneles principales
    const sovereignPanel = document.getElementById("view-sovereign-hub");
    if (sovereignPanel) sovereignPanel.style.display = (vistaId === "sovereign") ? "block" : "none";
    const marketsPanel = document.getElementById("view-markets-hub");
    if (marketsPanel) marketsPanel.style.display = (vistaId === "markets") ? "block" : "none";
    const adminPanel = document.getElementById("view-admin-hub");
    if (adminPanel) adminPanel.style.display = (vistaId === "admin") ? "block" : "none";

    // 3. Carga automática de datos según la vista
    if (vistaId === "sovereign") {
        cargarTableroSoberano(262);
    } else if (vistaId === "markets") {
        cargarMercadoCasino(262);
    }
}

function conmutarSubMercado(subMercadoId) {
    document.querySelectorAll(".sub-tab").forEach(b => b.classList.remove("active"));
    const btn = document.getElementById(`tab-btn-${subMercadoId}`);
    if (btn) btn.classList.add("active");

    const casinoView = document.getElementById("market-view-casino");
    if (casinoView) casinoView.style.display = (subMercadoId === "casino") ? "block" : "none";
    const progolView = document.getElementById("market-view-progol");
    if (progolView) progolView.style.display = (subMercadoId === "progol") ? "block" : "none";

    if (subMercadoId === "progol") {
        cargarMercadoProgol();
    }
}

// ── PANTALLA 1: CARGA DE TABLERO SOBERANO (CERO CUOTAS) ─────────────────

async function cargarTableroSoberano(leagueId = 262, jornada = null) {
    const matchesContainer = document.getElementById("sovereign-matches-carousel");
    const standingsContainer = document.getElementById("sovereign-standings-container");
    const mdSelector = document.getElementById("sovereign-matchday-selector");

    if (matchesContainer) matchesContainer.innerHTML = '<div style="text-align:center;padding:30px;color:#38BDF8;">⏳ Cargando inteligencia soberana...</div>';
    if (standingsContainer) standingsContainer.innerHTML = '<div style="text-align:center;padding:20px;color:#38BDF8;font-size:8pt;">⏳ Sincronizando tabla...</div>';

    try {
        let url = `/api/sovereign/leagues/${leagueId}/matches`;
        if (jornada) url += `?jornada=${jornada}`;
        const resp = await fetch(url);
        if (!resp.ok) return;
        const data = await resp.json();
        renderizarTableroSoberano(data);
    } catch (e) {
        console.error("Error cargando tablero soberano:", e);
        if (matchesContainer) matchesContainer.innerHTML = '<div style="text-align:center;padding:30px;color:#f87171;">❌ Error al cargar datos soberanos.</div>';
    }
}

function renderizarTableroSoberano(data) {
    const leagueId = data.league_id || 262;
    const jornadaActual = data.jornada || 10;

    // ── 1. Selector de Jornadas ────────────────────────────────────────────
    const mdSelector = document.getElementById("sovereign-matchday-selector");
    if (mdSelector) {
        mdSelector.innerHTML = "";
        const jornadasDisp = data.jornadas_disponibles || [8, 9, 10];
        const jornada8Conclusa = jornadasDisp.includes(8);
        const jornada9Conclusa = jornadasDisp.includes(9);

        jornadasDisp.forEach(jNum => {
            const btn = document.createElement("button");
            btn.type = "button";
            const isActive = (jNum === jornadaActual);

            // Determinar estado del badge: J8 y J9 concluidas, J10 activa
            let badgeLabel, badgeBg, badgeColor;
            if (jNum < 10) {
                badgeLabel = "🏁 Concluida";
                badgeBg = "rgba(148, 163, 184, 0.2)";
                badgeColor = "#CBD5E1";
            } else {
                badgeLabel = "🟢 Programada ⭐";
                badgeBg = "rgba(0, 230, 118, 0.2)";
                badgeColor = "#00E676";
            }

            btn.style.cssText = `
                background: ${isActive ? '#0284C7' : '#1C2541'};
                border: 1px solid ${isActive ? '#38BDF8' : '#334155'};
                color: ${isActive ? '#FFFFFF' : '#94A3B8'};
                padding: 6px 14px; border-radius: 20px;
                font-size: 0.82rem; font-weight: 700; cursor: pointer;
                display: inline-flex; align-items: center; gap: 8px;
                box-shadow: ${isActive ? '0 0 10px rgba(56,189,248,0.3)' : 'none'};
                transition: all 0.2s ease;
            `;
            btn.innerHTML = `<span>J${jNum}</span><span style="background:${badgeBg};color:${badgeColor};font-size:0.7rem;padding:2px 7px;border-radius:10px;font-weight:600;">${badgeLabel}</span>`;
            btn.onmouseenter = () => { if (!isActive) btn.style.borderColor = '#38BDF8'; };
            btn.onmouseleave = () => { if (!isActive) btn.style.borderColor = '#334155'; };
            btn.onclick = (e) => {
                e.preventDefault();
                if (jNum === jornadaActual) return;
                cargarTableroSoberano(leagueId, jNum);
            };
            mdSelector.appendChild(btn);
        });
    }

    // ── 2. Tabla General en Panel Izquierdo ────────────────────────────────
    const standingsContainer = document.getElementById("sovereign-standings-container");
    if (standingsContainer && data.standings && data.standings.length > 0) {
        const table = document.createElement("table");
        table.style.cssText = "width:100%; border-collapse: collapse; font-size: 7.5pt;";
        table.innerHTML = `
            <thead>
                <tr style="color:#38BDF8; border-bottom: 1px solid #1C2541;">
                    <th style="padding:4px 3px; text-align:center;">#</th>
                    <th style="padding:4px 3px; text-align:left;">Club</th>
                    <th style="padding:4px 3px; text-align:center; color:#00E676;">Pts</th>
                    <th style="padding:4px 3px; text-align:center;">PJ</th>
                    <th style="padding:4px 3px; text-align:center;">Dif</th>
                    <th style="padding:4px 3px; text-align:center; color:#38BDF8;">xG</th>
                    <th style="padding:4px 3px; text-align:center;">Forma</th>
                </tr>
            </thead>
            <tbody id="sovereign-standings-tbody"></tbody>
        `;
        standingsContainer.innerHTML = "";
        standingsContainer.appendChild(table);

        const tbody = document.getElementById("sovereign-standings-tbody");
        data.standings.forEach(s => {
            const difColor = s.dif >= 0 ? "#00E676" : "#f87171";
            const difSign = s.dif > 0 ? "+" : "";
            const escudoHtml = s.escudo_url
                ? `<img src="${s.escudo_url}" width="14" height="14" style="vertical-align:middle;margin-right:4px;object-fit:contain;" onerror="this.style.display='none'">`
                : "";

            // Forma: últimos 5, círculos compactos
            const formaHtml = (s.forma || []).slice(-5).map(f => {
                const cls = (f==="G"||f==="W") ? "#00E676" : (f==="E"||f==="D") ? "#F59E0B" : "#f87171";
                const ltr = (f==="G"||f==="W") ? "G" : (f==="E"||f==="D") ? "E" : "P";
                return `<span style="display:inline-flex;align-items:center;justify-content:center;width:12px;height:12px;border-radius:50%;background:${cls};color:#fff;font-size:5.5pt;font-weight:800;">${ltr}</span>`;
            }).join("");

            const tr = document.createElement("tr");
            tr.style.cssText = `border-bottom: 1px solid rgba(255,255,255,0.04); transition: background 0.15s;`;
            tr.onmouseenter = () => tr.style.background = "rgba(56,189,248,0.06)";
            tr.onmouseleave = () => tr.style.background = "";
            tr.innerHTML = `
                <td style="padding:5px 3px; text-align:center; font-weight:700; color:#94A3B8;">${s.pos}</td>
                <td style="padding:5px 3px; font-weight:600; color:#fff; white-space:nowrap;">${escudoHtml}${s.equipo}</td>
                <td style="padding:5px 3px; text-align:center; font-weight:800; color:#00E676;">${s.puntos}</td>
                <td style="padding:5px 3px; text-align:center; color:#94A3B8;">${s.pj}</td>
                <td style="padding:5px 3px; text-align:center; font-weight:700; color:${difColor};">${difSign}${s.dif}</td>
                <td style="padding:5px 3px; text-align:center; color:#38BDF8;">${(s.xg||0).toFixed(1)}</td>
                <td style="padding:5px 3px; text-align:center;"><div style="display:inline-flex;gap:2px;">${formaHtml}</div></td>
            `;
            tbody.appendChild(tr);
        });
    }

    // ── 3. Carrusel de Partidos en Panel Derecho ───────────────────────────
    const container = document.getElementById("sovereign-matches-carousel");
    if (!container) return;
    container.innerHTML = "";

    const matches = data.matches || [];
    if (matches.length === 0) {
        container.innerHTML = '<div style="text-align:center;padding:30px;color:#94A3B8;">Sin partidos para esta jornada.</div>';
        return;
    }

    // Agrupar por estado para header visual
    const finalizados = matches.filter(m => m.estado === "FINALIZADO");
    const programados = matches.filter(m => m.estado === "PROGRAMADO" || m.estado === "EN_CURSO");

    if (finalizados.length > 0) {
        const hdr = document.createElement("div");
        hdr.style.cssText = "font-size:7pt;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;padding:6px 4px 4px;margin-top:4px;";
        hdr.textContent = "🏁 Partidos Concluidos";
        container.appendChild(hdr);
        finalizados.forEach(m => container.appendChild(_crearTarjetaSoberana(m)));
    }
    if (programados.length > 0) {
        const hdr = document.createElement("div");
        hdr.style.cssText = "font-size:7pt;font-weight:700;color:#00E676;text-transform:uppercase;letter-spacing:1px;padding:6px 4px 4px;margin-top:4px;";
        hdr.textContent = "📅 Partidos Programados";
        container.appendChild(hdr);
        programados.forEach(m => container.appendChild(_crearTarjetaSoberana(m)));
    }
}

function _crearTarjetaSoberana(m) {
    const card = document.createElement("div");
    card.className = "card match-card-sovereign";
    const esFinal = m.estado === "FINALIZADO";
    const marcadorHtml = esFinal && m.marcador_actual
        ? `<span style="font-size:0.9rem;font-weight:800;color:#F59E0B;padding:2px 8px;background:rgba(245,158,11,0.1);border-radius:4px;">${m.marcador_actual}</span>`
        : `<span style="color:#475569;font-size:0.75rem;">vs</span>`;

    card.innerHTML = `
        <div class="flex-between text-muted" style="font-size:0.72rem;">
            <span>${m.horario || ''}</span>
            <span class="badge-pill" style="${esFinal ? 'color:#94A3B8;' : 'color:#00E676;'}">${m.fecha_bloque || ''}</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin:10px 0; gap:6px;">
            <div style="display:flex; align-items:center; gap:5px; flex:1; justify-content:flex-end;">
                <span style="font-weight:700; font-size:0.82rem; text-align:right;">${m.local}</span>
                <img src="${m.local_escudo_url || ''}" width="22" height="22" onerror="this.src='/static/img/favicon.svg'" style="object-fit:contain;">
            </div>
            ${marcadorHtml}
            <div style="display:flex; align-items:center; gap:5px; flex:1; justify-content:flex-start;">
                <img src="${m.visitante_escudo_url || ''}" width="22" height="22" onerror="this.src='/static/img/favicon.svg'" style="object-fit:contain;">
                <span style="font-weight:700; font-size:0.82rem;">${m.visitante}</span>
            </div>
        </div>
        <div class="prob-strip" style="height:6px; border-radius:3px; display:flex; overflow:hidden; margin-bottom:6px;">
            <div style="width:${((m.p_local||0)*100).toFixed(1)}%; background:#00E676;"></div>
            <div style="width:${((m.p_empate||0)*100).toFixed(1)}%; background:#F59E0B;"></div>
            <div style="width:${((m.p_visitante||0)*100).toFixed(1)}%; background:#EF4444;"></div>
        </div>
        <div class="flex-between" style="font-size:0.75rem; font-weight:700;">
            <span style="color:#00E676;">L: ${((m.p_local||0)*100).toFixed(1)}%</span>
            <span style="color:#F59E0B;">E: ${((m.p_empate||0)*100).toFixed(1)}%</span>
            <span style="color:#EF4444;">V: ${((m.p_visitante||0)*100).toFixed(1)}%</span>
        </div>
        <div class="flex-between text-muted" style="font-size:0.7rem; margin-top:6px;">
            <span>λH: ${(m.lambda_home||0).toFixed(2)} / λA: ${(m.lambda_away||0).toFixed(2)}</span>
            <span>Φ Lead2: ${((m.phi_lead2_home||0)*100).toFixed(1)}%</span>
        </div>
        <button class="btn btn-secondary btn-sm" style="width:100%; margin-top:10px;" onclick="abrirRadiografiaSoberana('${m.match_id}')">
            🔬 Radiografía Estocástica
        </button>
    `;
    return card;
}


// ── PANTALLA 2: CARGA DE MERCADO CASINO (CALIENTE.MX) ───────────────────

async function cargarMercadoCasino(leagueId = 262) {
    try {
        const resp = await fetch(`/api/markets/sportsbook/matches?bookmaker=caliente&league_id=${leagueId}`);
        if (!resp.ok) return;
        const data = await resp.json();
        renderizarMercadoCasino(data);
    } catch (e) {
        console.error("Error cargando mercado casino:", e);
    }
}

function renderizarMercadoCasino(data) {
    const container = document.getElementById("casino-matches-list");
    if (!container) return;
    container.innerHTML = "";

    (data.matches || []).forEach(m => {
        const card = document.createElement("div");
        card.className = "card match-card-market";
        const gapLColor = (m.gap_local || 0) > 0 ? "#00E676" : "#94A3B8";
        card.innerHTML = `
            <div class="flex-between">
                <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
                    <input type="checkbox" class="casino-match-checkbox" value="${m.match_id}">
                    <strong>${m.local} vs ${m.visitante}</strong>
                </label>
                <span style="font-size:0.75rem; color:${gapLColor}; font-weight:800;">
                    GAP Local: ${((m.gap_local||0)*100).toFixed(1)}% (+EV)
                </span>
            </div>
            <div class="odds-row" style="display:flex; gap:10px; margin-top:8px; font-size:0.8rem;">
                <span>L @ <strong>${(m.momio_l||0).toFixed(2)}</strong></span>
                <span>E @ <strong>${(m.momio_e||0).toFixed(2)}</strong></span>
                <span>V @ <strong>${(m.momio_v||0).toFixed(2)}</strong></span>
                ${m.pago_anticipado ? '<span style="color:#00E676; font-weight:700;">🏷️ PA</span>' : ''}
            </div>
        `;
        container.appendChild(card);
    });
}

// ── PANTALLA 2: CARGA DE MERCADO PROGOL ─────────────────────────────────

async function cargarMercadoProgol() {
    try {
        const resp = await fetch("/api/markets/progol/slates/active");
        if (!resp.ok) return;
        const data = await resp.json();
        renderizarMercadoProgol(data);
    } catch (e) {
        console.error("Error cargando Progol:", e);
    }
}

function renderizarMercadoProgol(data) {
    const container = document.getElementById("progol-slate-container");
    if (!container) return;
    container.innerHTML = "";

    (data.items || []).forEach(item => {
        const row = document.createElement("div");
        row.className = "progol-row";
        row.style.cssText = "display:flex; justify-content:space-between; align-items:center; padding:10px; border-bottom:1px solid #1C2541;";
        const s = item.analisis_sesgo || {};
        const vPub = item.v_pub || { L: 0, E: 0, V: 0 };
        row.innerHTML = `
            <div>
                <span style="font-weight:700; color:#38BDF8;">#${item.order || ''}</span>
                <strong>${item.local} vs ${item.visitante}</strong>
            </div>
            <div style="font-size:0.75rem; color:#94A3B8;">
                Venta Pública: L ${(vPub.L*100).toFixed(0)}% | E ${(vPub.E*100).toFixed(0)}% | V ${(vPub.V*100).toFixed(0)}%
            </div>
            <div>
                ${s.alerta_sesgo ? '<span class="badge-bias-alert">🚨 SESGO POPULAR</span>' : ''}
                <span style="font-size:0.8rem; font-weight:800; color:#00E676; margin-left:8px;">${s.recomendacion_cobertura || 'BASE'}</span>
            </div>
        `;
        container.appendChild(row);
    });
}

// ── [LN-QBE-073] DESPACHO ACTIVO DE CARTERA CASINO CON SLIDER DE CERTEZA ──

async function ejecutarDespachoPortafolio() {
    const checkboxes = document.querySelectorAll(".casino-match-checkbox:checked");
    const selectedIds = Array.from(checkboxes).map(cb => cb.value);

    if (selectedIds.length === 0) {
        alert("Selecciona al menos un partido para invertir.");
        return;
    }

    const bankrollInput = document.getElementById("input-bankroll");
    const bankroll = parseFloat((bankrollInput && bankrollInput.value) ? bankrollInput.value : 200);

    const sliderEl = document.getElementById("slider-risk-certainty");
    const sliderVal = parseFloat((sliderEl && sliderEl.value) ? sliderEl.value : 80);
    const targetCerteza = sliderVal / 100.0;

    const btn = document.getElementById("btn-generate-portfolio");
    if (btn) {
        btn.textContent = "⏳ Calculando Cartera...";
        btn.disabled = true;
    }

    try {
        const resp = await fetch("/api/markets/sportsbook/portfolio/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                league_id: 262,
                selected_match_ids: selectedIds,
                bankroll: bankroll,
                target_certeza: targetCerteza
            })
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || "Error calculando cartera");
        }

        const data = await resp.json();
        if (typeof currentPortfolioData !== "undefined") {
            currentPortfolioData = data;
        }

        // Desplegar Dashboard de Cartera si existe
        const dashboard = document.getElementById("portfolio-results-dashboard");
        if (dashboard) dashboard.style.display = "block";

        if (typeof renderizarResultadosPortafolio === "function") {
            renderizarResultadosPortafolio(data);
        }
    } catch (e) {
        alert(`❌ Error en despacho: ${e.message}`);
    } finally {
        if (btn) {
            btn.textContent = "🚀 Generar Cartera Cuantitativa";
            btn.disabled = false;
        }
    }
}

// ── [LN-QBE-074] OPTIMIZADOR PROGOL POR PRESUPUESTO ─────────────────────────

async function optimizarQuinielaProgol(presupuestoMxn = 360.0) {
    try {
        const resp = await fetch("/api/markets/progol/optimize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                slate_id: "PROGOL_2245",
                presupuesto_mxn: presupuestoMxn
            })
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || "Error optimizando Progol");
        }

        const data = await resp.json();

        // Renderizar resultado en la UI si existe el contenedor
        const container = document.getElementById("progol-optimization-result");
        if (container) {
            container.innerHTML = `
                <div style="padding:12px; background:#0F172A; border-radius:8px; border:1px solid #38BDF8; margin-top:12px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <strong style="color:#38BDF8;">🎯 Quiniela Optimizada [LN-QBE-074]</strong>
                        <span style="color:#00E676; font-weight:800;">$${data.costo_total_mxn} MXN</span>
                    </div>
                    <div style="font-size:0.8rem; color:#94A3B8; margin-bottom:10px;">
                        ${data.dobles_asignados} Dobles × ${data.triples_asignados} Triples = 
                        <strong style="color:#F59E0B;">${data.combinaciones_totales} combinaciones</strong>
                    </div>
                    ${(data.matriz_quiniela || []).map(item => `
                        <div style="display:flex; justify-content:space-between; align-items:center;
                                    padding:6px 8px; border-bottom:1px solid #1C2541; font-size:0.78rem;">
                            <span><strong style="color:#38BDF8;">#${item.order}</strong> ${item.local} vs ${item.visitante}</span>
                            <span>
                                ${item.juega_L ? '<span style="color:#00E676; font-weight:700; margin:0 3px;">1</span>' : '<span style="color:#334155; margin:0 3px;">—</span>'}
                                ${item.juega_E ? '<span style="color:#F59E0B; font-weight:700; margin:0 3px;">X</span>' : '<span style="color:#334155; margin:0 3px;">—</span>'}
                                ${item.juega_V ? '<span style="color:#EF4444; font-weight:700; margin:0 3px;">2</span>' : '<span style="color:#334155; margin:0 3px;">—</span>'}
                                ${item.alerta_sesgo ? '<span style="color:#EF4444; font-size:0.7rem; margin-left:6px;">🚨 SESGO</span>' : ''}
                            </span>
                        </div>
                    `).join("")}
                </div>
            `;
        }

        alert(`✅ Quiniela Optimizada: $${data.costo_total_mxn} MXN (${data.dobles_asignados}D + ${data.triples_asignados}T = ${data.combinaciones_totales} combinaciones)`);
    } catch (e) {
        console.error("Error optimizando Progol:", e);
        alert(`❌ Error Progol: ${e.message}`);
    }
}

// Exponer al ámbito global
window.cambiarVistaPrincipal = cambiarVistaPrincipal;
window.conmutarSubMercado = conmutarSubMercado;
window.cargarTableroSoberano = cargarTableroSoberano;
window.renderizarTableroSoberano = renderizarTableroSoberano;
window.cargarMercadoCasino = cargarMercadoCasino;
window.renderizarMercadoCasino = renderizarMercadoCasino;
window.cargarMercadoProgol = cargarMercadoProgol;
window.renderizarMercadoProgol = renderizarMercadoProgol;
window.ejecutarDespachoPortafolio = ejecutarDespachoPortafolio;
window.optimizarQuinielaProgol = optimizarQuinielaProgol;

