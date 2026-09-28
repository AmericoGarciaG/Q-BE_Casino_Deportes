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
                    <div style="font-size: 7.2pt; color: #00E676; font-weight: 700; margin-top: 6px;">• 18 Clubes</div>
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

        // [DES-QBE-051] Guarda de bóveda vacía: banner didáctico, jamás excepción roja
        if (!currentLiveBoard.standings || currentLiveBoard.standings.length === 0) {
            if (tbody) tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:30px; color:#94A3B8;">
                ℹ️ Base de datos en reposo / vacía.<br>
                <span style="font-size:8pt; color:#38BDF8;">Vaya a <strong>[ ⚙️ Centro de Control ]</strong> y presione <em>"⚡ Ejecutar Cadena de Ingesta Total"</em> para sincronizar la liga en vivo.</span>
            </td></tr>`;
        } else {
            renderizarTabla18Clubes(currentLiveBoard.standings);
        }

        renderizarCartelera(currentLiveBoard.fixtures);
    } catch (e) {
        console.error("Error cargando live board:", e);
        if (tbody) tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:#f87171;">❌ Error al conectar: ${e.message}</td></tr>`;
    }
}

// [DES-QBE-037] Carrusel Ventanizado Determinista (Máximo 3 píldoras en pantalla)
function renderizarPildorasJornada(liveBoard) {
    const container = document.getElementById("matchday-pill-selector");
    if (!container) return;
    container.innerHTML = "";

    const disponibles = liveBoard.jornadas_disponibles || [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17];
    const mostrada = liveBoard.jornada_mostrada || 10;
    const actual = liveBoard.jornada_actual || 10;

    // 1. Calcular la ventana de 3 jornadas visibles [mostrada - 1, mostrada, mostrada + 1]
    let ventana = [mostrada - 1, mostrada, mostrada + 1];
    if (mostrada === 1) ventana = [1, 2, 3];
    if (mostrada === 17) ventana = [15, 16, 17];

    // Filtrar para que solo existan jornadas dentro del rango 1 a 17
    ventana = ventana.filter(j => j >= 1 && j <= 17);

    // 2. Controlar estado de flechas ◄ y ►
    const btnPrev = document.getElementById("btn-carousel-prev");
    const btnNext = document.getElementById("btn-carousel-next");
    if (btnPrev) btnPrev.disabled = (mostrada <= 1);
    if (btnNext) btnNext.disabled = (mostrada >= 17);

    // 3. Renderizar ÚNICAMENTE las 3 píldoras visibles
    ventana.forEach(jNum => {
        const btn = document.createElement("button");
        btn.type = "button";
        const isActive = (jNum === mostrada);
        btn.className = "pill-tab" + (isActive ? " active" : "");
        
        btn.style.cssText = `
            background: ${isActive ? '#0284C7' : '#1C2541'};
            border: 1px solid ${isActive ? '#38BDF8' : '#334155'};
            color: ${isActive ? '#FFFFFF' : '#94A3B8'};
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            white-space: nowrap;
            box-shadow: ${isActive ? '0 0 8px rgba(56, 189, 248, 0.35)' : 'none'};
        `;

        let badgeLabel = "";
        if (jNum < actual) {
            badgeLabel = "🏁";
        } else if (jNum === actual) {
            badgeLabel = "⚡ Activa";
        } else {
            badgeLabel = "📅";
        }

        btn.innerHTML = `<span>Jornada ${jNum}</span><span style="font-size:0.68rem; opacity:0.8;">${badgeLabel}</span>`;
        
        btn.onclick = (e) => {
            e.preventDefault();
            if (jNum === mostrada) return;
            const leagueId = liveBoard.league_id || 262;
            seleccionarLiga(leagueId, false, jNum);
        };
        container.appendChild(btn);
    });
}

function navegarCarruselTemporal(delta) {
    if (!currentLiveBoard) return;
    const mostrada = currentLiveBoard.jornada_mostrada || 10;
    const targetJornada = mostrada + delta;
    if (targetJornada >= 1 && targetJornada <= 17) {
        const leagueId = currentLiveBoard.league_id || 262;
        seleccionarLiga(leagueId, false, targetJornada);
    }
}
window.navegarCarruselTemporal = navegarCarruselTemporal;
window.renderizarCarruselTemporadaCompleta = renderizarPildorasJornada;



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
    const container = document.getElementById("fixtures-container") || document.querySelector(".fixtures-scroll-container");
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
    const card = document.createElement("div");
    card.className = "card match-card-clean";
    card.id = `fixture-card-${f.id_partido}`;
    card.setAttribute("onclick", `abrirRadiografiaForense('${f.id_partido}')`);

    const localEscudo = f.local_escudo_url ? `<img src="${f.local_escudo_url}" class="match-crest-mini">` : "";
    const visEscudo = f.visitante_escudo_url ? `<img src="${f.visitante_escudo_url}" class="match-crest-mini">` : "";

    // Contenido del centro: reemplaza el 'vs' flotante por el resultado o estado discreto
    let centroHtml = "";
    if (estado === "FINALIZADO") {
        const marcador = f.marcador_actual || "Final";
        centroHtml = `
            <span class="match-time-muted">${f.horario}</span>
            <span class="score-center-badge">${marcador}</span>
        `;
    } else if (estado === "REPROGRAMADO") {
        centroHtml = `
            <span class="match-time-muted">${f.horario}</span>
            <span class="status-center-subtle">⏳ Reprogramado</span>
        `;
    } else {
        // PROGRAMADO (JORNADA ACTIVA J10)
        const pL = f.p_local ? (f.p_local * 100).toFixed(0) + "%" : "—";
        const pE = f.p_empate ? (f.p_empate * 100).toFixed(0) + "%" : "—";
        const pV = f.p_visitante ? (f.p_visitante * 100).toFixed(0) + "%" : "—";

        const wL = f.p_local ? (f.p_local * 100).toFixed(1) : 33.3;
        const wE = f.p_empate ? (f.p_empate * 100).toFixed(1) : 33.3;
        const wV = f.p_visitante ? (f.p_visitante * 100).toFixed(1) : 33.4;

        // [DES-QBE-039-B] Micro-Malla de Consenso y Diferencial Alineada
        let consensoHtml = '';
        if (f.consenso_mercado && f.consenso_mercado.p_L_mercado > 0) {
            const qL = (f.consenso_mercado.p_L_mercado * 100).toFixed(0);
            const qE = (f.consenso_mercado.p_E_mercado * 100).toFixed(0);
            const qV = (f.consenso_mercado.p_V_mercado * 100).toFixed(0);

            const dL = (f.consenso_mercado.delta_L * 100);
            const dE = (f.consenso_mercado.delta_E * 100);
            const dV = (f.consenso_mercado.delta_V * 100);

            const fmtDiff = (v) => (v >= 0 ? `+${v.toFixed(1)}%` : `${v.toFixed(1)}%`);

            consensoHtml = `
                <div class="market-benchmark-grid" title="Comparativo: Consenso de Mercado vs Modelo Q-BE">
                    <!-- Fila 1: Promedio de Mercado sin comisión -->
                    <span class="mkt-cell-lbl">Mkt</span>
                    <span class="mkt-cell-val">${qL}%</span>
                    <span class="mkt-cell-val">${qE}%</span>
                    <span class="mkt-cell-val">${qV}%</span>

                    <!-- Fila 2: Diferencial aritmético con signo -->
                    <span class="mkt-cell-lbl">Δ</span>
                    <span class="mkt-cell-diff">${fmtDiff(dL)}</span>
                    <span class="mkt-cell-diff">${fmtDiff(dE)}</span>
                    <span class="mkt-cell-diff">${fmtDiff(dV)}</span>
                </div>
            `;
        }


        centroHtml = `
            <span class="match-time-muted">${f.horario}</span>
            <div class="distribution-center-badge" title="Probabilidad Soberana Q-BE: Local · Empate · Visita">
                <span style="color:#00E676; font-weight:800;">${pL}</span>
                <span style="color:#64748B; margin: 0 3px;">·</span>
                <span style="color:#94A3B8; font-weight:700;">${pE}</span>
                <span style="color:#64748B; margin: 0 3px;">·</span>
                <span style="color:#EF4444; font-weight:800;">${pV}</span>
            </div>
            <div class="prob-strip-mini prob-strip" style="display:flex; width:75px; height:4px; border-radius:2px; overflow:hidden; margin-top:3px;">
                <div style="background:#00E676; width:${wL}%;"></div>
                <div style="background:#64748B; width:${wE}%;"></div>
                <div style="background:#EF4444; width:${wV}%;"></div>
            </div>
            ${consensoHtml}
        `;

    }

    card.innerHTML = `
        <div class="match-grid-3col">
            <div class="team-home-cell">
                <span>${f.local}</span>
                ${localEscudo}
            </div>
            <div class="match-center-cell">
                ${centroHtml}
            </div>
            <div class="team-away-cell">
                ${visEscudo}
                <span>${f.visitante}</span>
            </div>
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
    const bankrollInput = document.getElementById('input-bankroll') || document.getElementById('bankroll-input');
    const bankroll = bankrollInput ? parseFloat(bankrollInput.value) : 200.0;

    const operatorSelect = document.getElementById('casino-operator-select');
    const operador = operatorSelect ? operatorSelect.value : "caliente";

    const certaintySlider = document.getElementById('slider-risk-certainty');
    const certeza = certaintySlider ? parseFloat(certaintySlider.value) / 100.0 : 0.80;

    const leagueId = (currentLiveBoard && currentLiveBoard.league_id) ? currentLiveBoard.league_id : 262;

    mostrarHUDProcesamiento();
    abortControllerDespacho = new AbortController();

    try {
        // Simulación visual reactiva de progresión mientras responde el worker
        setTimeout(() => actualizarProgresoHUD(2, 35), 300);
        setTimeout(() => actualizarProgresoHUD(3, 55), 600);
        setTimeout(() => actualizarProgresoHUD(4, 75), 900);
        setTimeout(() => actualizarProgresoHUD(5, 90), 1200);

        const resp = await fetch('/api/markets/sportsbook/portfolio/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: abortControllerDespacho.signal,
            body: JSON.stringify({
                league_id: leagueId,
                selected_match_ids: [],
                bankroll: bankroll,
                target_certeza: certeza,
                operador: operador
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
window.ejecutarDespachoMesaApuestas = ejecutarDespachoPortafolio;

let currentPortfolioData = null;

function renderizarResultadosPortafolio(data) {
    currentPortfolioData = data;
    // [DES-QBE-045] Consumo de las claves canónicas 3NF emitidas por markets.py (con fallback declarado).
    const orders = data.ordenes_ejecucion_partidos || data.ordenes || [];
    const control = data.control_portafolio || data.control || {};
    const balance = data.balance_global_portafolio || data.balance || {};
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
            // [DES-QBE-045] Paleta canónica de las 9 familias estratégicas Q-BE.
            const pal = _paletaEstrategia(cod);
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
                <td style="text-align:center;"><span class="badge-status-live" style="background:${pal.bg}; color:${pal.fg}; border-color:${pal.borde};">${cod}</span></td>
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
            // [DES-QBE-045] Paleta canónica de familia + distintivo de Pago Anticipado gobernado por bandera.
            const pal = _paletaEstrategia(est.codigo || "");
            const paBadgeHtml = _badgePagoAnticipado(ord, est);
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
                            <span class="badge-status-live" style="background:${pal.bg}; color:${pal.fg}; border-color:${pal.borde}; font-weight:800;">${est.codigo}</span>
                            <span style="font-size:7.5pt; color:#cbd5e1;">${est.descripcion_ejecutiva}</span>
                            ${paBadgeHtml}
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
    // [DES-QBE-045 cláusula 4] Autarquía de la Radiografía Forense: no exige cálculo de cartera previo.
    // Fuente 1: análisis soberano de la cartera. Fuente 2: datos soberanos del Live Board (fixtures).
    let p = (currentPortfolioData?.partidos_analisis || []).find(x => x.id_partido === matchId);
    if (!p) {
        const fixture = (currentLiveBoard?.fixtures || []).find(x => x.id_partido === matchId);
        if (!fixture) return;
        p = _adaptarFixtureARadiografia(fixture);
    }

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

// [DES-QBE-040] Alternador de Modo Enfoque (Ocultar/Mostrar Tabla de Posiciones)
function toggleTablaPosiciones() {
    // Localizar el contenedor split-view padre de Pantalla 1
    const splitContainer = document.querySelector('.split-view-container') || 
                           document.querySelector('.split-view') ||
                           document.getElementById('sovereign-split-container') ||
                           document.querySelector('#view-sovereign-hub .content-grid');

    const btnTxt = document.getElementById('btn-toggle-txt');
    const btnIcon = document.getElementById('btn-toggle-icon');
    const btn = document.getElementById('btn-toggle-standings');

    if (!splitContainer) {
        console.warn("No se encontró el contenedor split-view para alternar.");
        return;
    }

    const estaOculta = splitContainer.classList.toggle('standings-hidden');

    if (btnTxt && btnIcon) {
        if (estaOculta) {
            btnIcon.textContent = '◧';
            btnTxt.textContent = 'Ver Tabla';
            if (btn) btn.classList.add('active-focus');
            localStorage.setItem('qbe_standings_hidden', 'true');
        } else {
            btnIcon.textContent = '◨';
            btnTxt.textContent = 'Ocultar Tabla';
            if (btn) btn.classList.remove('active-focus');
            localStorage.setItem('qbe_standings_hidden', 'false');
        }
    }
}
window.toggleTablaPosiciones = toggleTablaPosiciones;

// Al inicializar la app, verificar si el usuario tenía la tabla oculta previamente
document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('qbe_standings_hidden') === 'true') {
        const splitContainer = document.querySelector('.split-view-container') || 
                               document.querySelector('.split-view') ||
                               document.getElementById('sovereign-split-container') ||
                               document.querySelector('#view-sovereign-hub .content-grid');
        if (splitContainer) {
            splitContainer.classList.add('standings-hidden');
            const btnTxt = document.getElementById('btn-toggle-txt');
            const btnIcon = document.getElementById('btn-toggle-icon');
            const btn = document.getElementById('btn-toggle-standings');
        }
    }
});

// ═══════════════════════════════════════════════════════════════════════════════
// [DES-QBE-045] PALETA CANÓNICA DE LAS 9 ESTRATEGIAS Q-BE Y PAGO ANTICIPADO
// Familias: D1/D2 (cian) · H1/H2 (verde) · R1/R2 (ámbar) · C1/C2 (violeta) · 00 (coral)
// ═══════════════════════════════════════════════════════════════════════════════

/** Paleta soberana por familia estratégica (LOGIC.md [LN-QBE-060-B], DESIGN.md [DES-QBE-045]). */
const PALETA_ESTRATEGIAS_QBE = {
    "QBE-D": { bg: "rgba(56,189,248,0.18)", fg: "#38BDF8", borde: "#38BDF8" },
    "QBE-H": { bg: "rgba(0,230,118,0.18)", fg: "#00E676", borde: "#00E676" },
    "QBE-R": { bg: "rgba(245,158,11,0.18)", fg: "#F59E0B", borde: "#F59E0B" },
    "QBE-C": { bg: "rgba(168,85,247,0.18)", fg: "#A855F7", borde: "#A855F7" },
    "QBE-00": { bg: "rgba(239,68,68,0.18)", fg: "#EF4444", borde: "#EF4444" }
};

/** Resuelve la familia canónica de un código; degrada a gris neutro si el código no está declarado. */
function _paletaEstrategia(codigo) {
    const cod = String(codigo || "").toUpperCase();
    const familia = Object.keys(PALETA_ESTRATEGIAS_QBE).find(k => cod.startsWith(k));
    return familia
        ? PALETA_ESTRATEGIAS_QBE[familia]
        : { bg: "rgba(148,163,184,0.15)", fg: "#94A3B8", borde: "#64748B" };
}

/** [DES-QBE-045] El distintivo (+PA) se gobierna por bandera booleana, nunca por el sufijo '+' heredado. */
function _badgePagoAnticipado(ord, est) {
    const activo = (ord && ord.pa_activo === true) || Boolean(est && est.linea_promocional);
    if (!activo) return "";
    const etiqueta = String((est && est.linea_promocional) || "Pago Anticipado").replace(/\+PA/gi, "").trim();
    return `<span class="badge-status-live" style="background:rgba(0,230,118,0.12); color:#00E676; border-color:#00E676; font-size:7.5pt; font-weight:700;">🏷️ ${etiqueta} (+PA)</span>`;
}

// ═══════════════════════════════════════════════════════════════════════════════
// [DES-QBE-046] SUB-VISTA QUINIELAS PROGOL — CONTRATO FÁCTICO CONSUMIDO
//   GET  /api/markets/progol/slates/active  -> markets.py:497-509
//   POST /api/markets/progol/optimize       -> progol_math.py:156-162
// Cero mapeo a claves hipotéticas: la UI sirve al contrato real (desviación D-3 autorizada).
// ═══════════════════════════════════════════════════════════════════════════════

let currentProgolSlate = null;

/** Conmuta la Mesa de Apuestas entre la sub-vista Sportsbook y la sub-vista Progol. */
function conmutarSubvistaMercados(vista) {
    const esProgol = vista === "progol";
    const contSportsbook = document.getElementById("contenedor-sportsbook");
    const contProgol = document.getElementById("contenedor-progol");
    const btnSportsbook = document.getElementById("btn-subtab-sportsbook");
    const btnProgol = document.getElementById("btn-subtab-progol");

    if (contSportsbook) contSportsbook.style.display = esProgol ? "none" : "";
    if (contProgol) contProgol.style.display = esProgol ? "" : "none";
    if (btnSportsbook) btnSportsbook.classList.toggle("active", !esProgol);
    if (btnProgol) btnProgol.classList.toggle("active", esProgol);

    if (esProgol && !currentProgolSlate) cargarSlateProgolActivo();
}

/** Hidrata el encabezado y el retículo del concurso vigente desde la bóveda 3NF. */
async function cargarSlateProgolActivo() {
    const cont = document.getElementById("progol-reticulo-container");
    if (!cont) return;
    cont.innerHTML = '<div style="font-size: 8.5pt; color: #94A3B8;">Consultando bóveda 3NF…</div>';
    try {
        const resp = await fetch("/api/markets/progol/slates/active");
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const slate = await resp.json();
        currentProgolSlate = slate;
        _renderEncabezadoProgol(slate);
        _renderReticuloProgol(slate);
    } catch (e) {
        console.error("Fallo hidratando el concurso Progol:", e);
        currentProgolSlate = null;
        cont.innerHTML = `<div style="font-size: 8.5pt; color: #F87171;">⚠️ No fue posible leer la bóveda 3NF del concurso Progol (${e.message}). Cero cifras se muestran sin respaldo.</div>`;
    }
}

/** [GOVERNANCE-01] Encabezado honesto: si la bóveda no declara un dato, se rotula con '—'. */
function _renderEncabezadoProgol(slate) {
    const elNombre = document.getElementById("progol-slate-nombre");
    const elCasillas = document.getElementById("progol-slate-casillas");
    const elBolsa = document.getElementById("progol-slate-bolsa");
    const elCierre = document.getElementById("progol-slate-cierre");
    const elFuente = document.getElementById("progol-sesgo-fuente");

    const sinConcurso = !slate || !slate.slate_id;
    if (elNombre) {
        elNombre.textContent = sinConcurso
            ? "Sin concurso Progol OPEN en la bóveda 3NF"
            : (slate.name || "Concurso Progol");
    }
    if (elCasillas) {
        elCasillas.textContent = sinConcurso
            ? "—"
            : `${slate.items_total} casillas · ${slate.soberanos} soberanas (3NF) · ${slate.priors} con Prior Base (1/3)`;
    }
    if (elBolsa) {
        const bolsa = slate ? slate.bolsa_garantizada_mxn : null;
        elBolsa.textContent = (bolsa === null || bolsa === undefined)
            ? "—"
            : `$${Number(bolsa).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} MXN`;
    }
    if (elCierre) {
        elCierre.textContent = `Tiempo límite: ${(slate && slate.fecha_cierre) ? slate.fecha_cierre : "—"}`;
    }
    if (elFuente) {
        const fuente = slate ? slate.sesgo_fuente : null;
        elFuente.textContent = (fuente === "MOMIOS_DE_CASINO")
            ? "📡 Contraste con venta pública: momios de casino de la jornada"
            : `📡 Contraste con venta pública: no disponible (${fuente || "SIN_BOVEDA"})`;
    }
}

/** Retículo de casillas del concurso (14 PROGOL REGULAR + 7 REVANCHA) leído de la bóveda 3NF. */
function _renderReticuloProgol(slate) {
    const cont = document.getElementById("progol-reticulo-container");
    if (!cont) return;
    const items = (slate && slate.items) || [];
    if (items.length === 0) {
        cont.textContent = "";
        const aviso = document.createElement("div");
        aviso.style.cssText = "font-size: 8.5pt; color: #94A3B8;";
        aviso.textContent = `⚠️ La bóveda 3NF no declara casillas para el concurso activo (fuente: ${(slate && slate.sesgo_fuente) || "SIN_BOVEDA"}). No se fabrican casillas ni probabilidades.`;
        cont.appendChild(aviso);
        return;
    }

    const fmtP = (v) => (v === null || v === undefined) ? "—" : `${(Number(v) * 100).toFixed(1)}%`;

    const filas = items.map(it => {
        const p = it.p_qbe || {};
        const badge = it.es_prior_ignorancia
            ? '<span class="badge-status-live" style="background:rgba(148,163,184,0.15); color:#cbd5e1; border-color:#64748B;">Prior Base (1/3)</span>'
            : '<span class="badge-status-live" style="background:rgba(0,230,118,0.15); color:#00E676; border-color:#00E676;">Soberano 3NF</span>';
        return `
            <tr>
                <td style="text-align:center; font-weight:800; color:#38BDF8;">${it.order}</td>
                <td style="text-align:center; font-size:7.5pt; color:#94A3B8;">${it.tipo_concurso || "—"}</td>
                <td style="font-weight:700; color:#fff;">${it.local || "—"}</td>
                <td style="font-weight:700; color:#fff;">${it.visitante || "—"}</td>
                <td style="text-align:center;">${fmtP(p.L)}</td>
                <td style="text-align:center;">${fmtP(p.E)}</td>
                <td style="text-align:center;">${fmtP(p.V)}</td>
                <td style="text-align:center;">${badge}</td>
                <td style="text-align:center;">${_badgeSesgoProgol(it)}</td>
            </tr>`;
    }).join("");

    cont.innerHTML = `
        <table class="fintech-table" style="width: 100%; font-size: 8.5pt;">
            <thead>
                <tr>
                    <th>#</th><th>Bloque</th><th>Local</th><th>Visitante</th>
                    <th>P(1)</th><th>P(X)</th><th>P(2)</th><th>Origen</th><th>Sesgo público</th>
                </tr>
            </thead>
            <tbody>${filas}</tbody>
        </table>`;
}

/** [GOVERNANCE-01] El sesgo sólo se declara con captura fáctica de momios públicos de la jornada. */
function _badgeSesgoProgol(it) {
    const motivo = it.sesgo_motivo || "";
    if (!it.sesgo_disponible) {
        return `<span style="font-size:7.2pt; color:#64748B;" title="${motivo}">Venta pública no ingesta</span>`;
    }
    const s = it.analisis_sesgo || {};
    const pct = (v) => `${(Number(v || 0) * 100).toFixed(1)}%`;
    const detalle = `Sesgo L ${pct(s.sesgo_local)} · X ${pct(s.sesgo_empate)} · V ${pct(s.sesgo_visitante)}`;
    if (s.alerta_sesgo) {
        return `<span class="badge-status-live" style="background:rgba(245,158,11,0.15); color:#F59E0B; border-color:#F59E0B;" title="${detalle}">⚠️ ${s.recomendacion_cobertura || "Sesgo popular"}</span>`;
    }
    return `<span style="font-size:7.2pt; color:#00E676;" title="${detalle}">${s.recomendacion_cobertura || "Sin sesgo explotable"}</span>`;
}

/** Ejecuta el optimizador combinatorio del backend (Costo = 15.00 × 2^D × 3^T ≤ presupuesto). */
async function ejecutarOptimizadorProgol() {
    const cont = document.getElementById("progol-resultado-optimizador");
    const input = document.getElementById("input-progol-presupuesto");
    if (!cont) return;

    const presupuesto = parseFloat(input ? input.value : "");
    if (!Number.isFinite(presupuesto) || presupuesto < 15.0) {
        cont.style.display = "block";
        cont.textContent = "";
        const aviso = document.createElement("div");
        aviso.style.cssText = "font-size: 8.5pt; color: #F87171;";
        aviso.textContent = "⚠️ El presupuesto mínimo aceptado es $15.00 MXN (invariante del request schema ProgolOptimizeRequest).";
        cont.appendChild(aviso);
        return;
    }

    cont.style.display = "block";
    cont.textContent = "";
    const carga = document.createElement("div");
    carga.style.cssText = "font-size: 8.5pt; color: #38BDF8;";
    carga.textContent = "⚡ Optimizando cobertura 2^D × 3^T sobre la bóveda 3NF…";
    cont.appendChild(carga);

    try {
        const resp = await fetch("/api/markets/progol/optimize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                slate_id: currentProgolSlate ? currentProgolSlate.slate_id : null,
                presupuesto_mxn: presupuesto
            })
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        _renderResultadoOptimizadorProgol(await resp.json());
    } catch (e) {
        console.error("Fallo optimizando Progol:", e);
        cont.textContent = "";
        const error = document.createElement("div");
        error.style.cssText = "font-size: 8.5pt; color: #F87171;";
        error.textContent = `⚠️ Sin concurso optimizable en la bóveda 3NF (${e.message}). Cero matrices se muestran sin respaldo.`;
        cont.appendChild(error);
    }
}

/** [D-3] Renderiza la matriz con las claves FÁCTICAS del plano (progol_math.py:156-162). */
function _renderResultadoOptimizadorProgol(data) {
    const cont = document.getElementById("progol-resultado-optimizador");
    if (!cont || !data) return;

    const matriz = data.matriz_quiniela || [];
    const casilla = (jugada, etiqueta) => jugada
        ? `<span style="color:#38BDF8; font-weight:900;" title="Se juega ${etiqueta}">●</span>`
        : '<span style="color:#334155;">·</span>';

    if (matriz.length === 0) {
        cont.textContent = "";
        const aviso = document.createElement("div");
        aviso.style.cssText = "font-size: 8.5pt; color: #94A3B8;";
        aviso.textContent = "⚠️ El optimizador no devolvió matriz de casillas: la bóveda 3NF no expone el bloque REGULAR del concurso.";
        cont.appendChild(aviso);
        return;
    }

    const filas = matriz.map(row => `
        <tr>
            <td style="text-align:center; font-weight:800; color:#38BDF8;">${row.order}</td>
            <td style="font-weight:700; color:#fff;">${row.local || "—"} vs ${row.visitante || "—"}</td>
            <td style="text-align:center;">${casilla(row.juega_L, "1")}</td>
            <td style="text-align:center;">${casilla(row.juega_E, "X")}</td>
            <td style="text-align:center;">${casilla(row.juega_V, "2")}</td>
            <td style="font-size:7.5pt; color:#cbd5e1;">${row.recomendacion || "—"}</td>
            <td style="text-align:center;">${row.alerta_sesgo ? "⚠️" : "—"}</td>
        </tr>`).join("");

    cont.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;">
            <div>
                <span style="font-size: 7.2pt; color: #38BDF8; text-transform: uppercase; font-weight: 800;">Matriz de Quiniela Optimizada</span>
                <h3 style="margin: 2px 0 0 0; font-size: 1.05rem; color: #fff;">${data.combinaciones_totales} combinaciones · ${data.dobles_asignados} dobles · ${data.triples_asignados} triples</h3>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 7pt; color: #94A3B8; text-transform: uppercase;">Costo real del boleto</span>
                <div style="font-size: 1.15rem; font-weight: 900; color: #00E676;">$${Number(data.costo_total_mxn || 0).toFixed(2)} MXN</div>
            </div>
        </div>
        <table class="fintech-table" style="width: 100%; font-size: 8.5pt;">
            <thead>
                <tr><th>#</th><th>Partido</th><th>1</th><th>X</th><th>2</th><th>Recomendación</th><th>Sesgo</th></tr>
            </thead>
            <tbody>${filas}</tbody>
        </table>`;
}

// ═══════════════════════════════════════════════════════════════════════════════
// [DES-QBE-045 cláusula 4] ADAPTADOR AUTÁRQUICO DEL LIVE BOARD HACIA LA RADIOGRAFÍA
// Sólo se escriben claves sobre hechos presentes en el fixture (SovereignDistribution +
// momios 1X2). Si un dato no existe, la clave no se crea: cero cifras inventadas.
// ═══════════════════════════════════════════════════════════════════════════════

function _adaptarFixtureARadiografia(f) {
    const num = (v) => (v === null || v === undefined || v === "") ? null : Number(v);
    const etiqueta = `${f.local || "—"} vs ${f.visitante || "—"}`;
    const momios = f.momios || {};

    const p = {
        id_partido: f.id_partido,
        partido: etiqueta,
        partido_nombre: etiqueta,
        origen_datos: "LIVE_BOARD_SOBERANO"
    };

    // Tabla Pronóstico vs Mercado: soberana persistida contra el momio 1X2 del fixture.
    const claves = [
        { clave: "L", resultado: f.local || "Local", soberana: num(f.p_local) },
        { clave: "E", resultado: "Empate", soberana: num(f.p_empate) },
        { clave: "V", resultado: f.visitante || "Visitante", soberana: num(f.p_visitante) }
    ];
    const filas = [];
    claves.forEach(({ clave, resultado, soberana }) => {
        if (soberana === null) return;
        const momio = num(momios[clave]);
        const probCasino = (momio !== null && momio > 0) ? (1.0 / momio) * 100.0 : null;
        const probReal = soberana * 100.0;
        filas.push({
            resultado: resultado,
            prob_real: probReal,
            momio: momio,
            prob_casino: probCasino,
            edge: (probCasino === null) ? 0.0 : probReal - probCasino
        });
    });
    if (filas.length > 0) p.probabilidades_3vias = filas;

    // Poisson Boxes: lambdas persistidos; el total es la suma aritmética y sólo si ambos existen.
    const lambdaLocal = num(f.lambda_home);
    const lambdaVisita = num(f.lambda_away);
    if (lambdaLocal !== null) p.lambda_local = lambdaLocal;
    if (lambdaVisita !== null) p.mu_visita = lambdaVisita;
    if (lambdaLocal !== null && lambdaVisita !== null) p.xg_total = lambdaLocal + lambdaVisita;
    const phiLead2 = num(f.phi_lead2_home);
    if (phiLead2 !== null) p.phi_lead2_pct = phiLead2 * 100.0;

    return p;
}

// ══════════════════════════════════════════════════════════════════════════════
// [DES-QBE-048 / ARCH-1.4.12] CENTRO DE CONTROL — DESPACHO GOBERNADO DE TAREAS
// El cliente SÓLO transmite el identificador certificado: el servidor resuelve la
// whitelist estricta y materializa el comando (cero texto libre, cero inyección).
// ══════════════════════════════════════════════════════════════════════════════

function bloquearBotonesAdmin(congelado) {
    document.querySelectorAll('.cc-task-btn, .cc-btn-master').forEach(btn => {
        btn.disabled = !!congelado;
    });
}

async function ejecutarTareaAdmin(taskId) {
    const identificador = String(taskId || '').trim();
    if (!identificador) return;

    const consola = document.getElementById('terminal-stream-output');
    const meta = document.getElementById('cc-terminal-meta');
    const badge = document.getElementById('cc-estado');

    bloquearBotonesAdmin(true);
    if (badge) {
        badge.className = 'cc-badge cc-badge-running';
        badge.textContent = `● En ejecución: ${identificador}`;
    }
    if (meta) meta.textContent = `tarea: ${identificador} · exit: en curso · duración: —`;
    if (consola) consola.textContent = `[SISTEMA] Despachando tarea '${identificador}'...\n`;

    try {
        const resp = await fetch('/api/admin/tasks/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: identificador })
        });

        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status} — ${await resp.text()}`);
        }

        const data = await resp.json();
        const salidaTexto = (data.output && data.output.length) ? data.output : '[SISTEMA] La tarea no emitió salida estándar.';

        // [GOVERNANCE-01] La salida se pinta como TEXTO PLANO: la consola nunca interpreta HTML.
        if (consola) {
            consola.textContent = salidaTexto;
            consola.scrollTop = consola.scrollHeight;
        }

        const exito = Number(data.exit_code) === 0;
        if (badge) {
            badge.className = `cc-badge ${exito ? 'cc-badge-ok' : 'cc-badge-fail'}`;
            badge.textContent = `${exito ? '✔ Completada' : '✖ Fallida'}: ${identificador}`;
        }
        if (meta) meta.textContent = `tarea: ${identificador} · exit: ${data.exit_code} · duración: ${data.duration_s}s`;
    } catch (e) {
        console.error('Fallo despachando tarea administrativa:', e);
        if (badge) {
            badge.className = 'cc-badge cc-badge-fail';
            badge.textContent = `✖ Error de despacho: ${identificador}`;
        }
        if (meta) meta.textContent = `tarea: ${identificador} · exit: — · duración: —`;
        if (consola) consola.textContent = `[ERROR] Despacho fallido: ${e.message}`;
    } finally {
        bloquearBotonesAdmin(false);
    }
}

window.ejecutarTareaAdmin = ejecutarTareaAdmin;
window.bloquearBotonesAdmin = bloquearBotonesAdmin;

window.conmutarSubvistaMercados = conmutarSubvistaMercados;
window.cargarSlateProgolActivo = cargarSlateProgolActivo;
window.ejecutarOptimizadorProgol = ejecutarOptimizadorProgol;

// Arranque de la SPA: se hidrata el concurso Progol vigente sin bloquear el render del Live Board.
document.addEventListener("DOMContentLoaded", function () {
    cargarSlateProgolActivo();
});

