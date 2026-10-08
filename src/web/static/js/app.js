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
        if (lblJornada) {
            // [DES-QBE-056 / ARCH-1.6.15-C] Etiqueta derivada del payload: cero celdas quemadas.
            const vigenteLbl = (currentLiveBoard.jornada_actual !== null && currentLiveBoard.jornada_actual !== undefined)
                ? currentLiveBoard.jornada_actual : currentLiveBoard.jornada_mostrada;
            lblJornada.textContent = currentLiveBoard.jornada ||
                (Number.isInteger(vigenteLbl) ? `Jornada ${vigenteLbl}` : "Jornada —");
        }
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

// [DES-QBE-056] Apertura determinista en la jornada VIGENTE: la píldora activa emana del estado
// fáctico de la bóveda (`jornada_actual` → primer partido PROGRAMADO), jamás de una celda fija.
// Cero invención: si la bóveda no dicta jornada, no se fabrica ninguna.
function resolverJornadaVigenteLiveBoard(liveBoard) {
    if (!liveBoard) return null;
    if (Number.isInteger(liveBoard.jornada_actual)) return liveBoard.jornada_actual;
    const fixtures = Array.isArray(liveBoard.fixtures) ? liveBoard.fixtures : [];
    const jornadaDe = (f) => {
        if (!f) return null;
        if (Number.isInteger(f.jornada)) return f.jornada;
        if (Number.isInteger(f.matchday)) return f.matchday;
        return null;
    };
    const pendientes = fixtures
        .filter(f => f && String(f.estado || "").toUpperCase() === "PROGRAMADO")
        .map(jornadaDe).filter(j => j !== null);
    if (pendientes.length > 0) return Math.min.apply(null, pendientes);
    const ledgeradas = fixtures.map(jornadaDe).filter(j => j !== null);
    if (ledgeradas.length > 0) return Math.max.apply(null, ledgeradas);
    return null;
}

// [DES-QBE-037] Carrusel Ventanizado Determinista (Máximo 3 píldoras en pantalla)
function renderizarPildorasJornada(liveBoard) {
    const container = document.getElementById("matchday-pill-selector");
    if (!container) return;
    container.innerHTML = "";

    const disponibles = liveBoard.jornadas_disponibles || [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17];
    const actual = resolverJornadaVigenteLiveBoard(liveBoard);
    if (!Number.isInteger(actual)) {
        container.innerHTML = '<span style="font-size:7.5pt; color:#94A3B8;">ℹ️ Sin jornadas ledgeradas en la bóveda: ejecute la ingesta en el Centro de Control.</span>';
        return;
    }
    const mostrada = Number.isInteger(liveBoard.jornada_mostrada) ? liveBoard.jornada_mostrada : actual;

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
    // [DES-QBE-056] La navegación parte de la jornada vigente derivada, nunca de una celda fija.
    const vigenteCarrusel = resolverJornadaVigenteLiveBoard(currentLiveBoard);
    const mostrada = Number.isInteger(currentLiveBoard.jornada_mostrada)
        ? currentLiveBoard.jornada_mostrada
        : vigenteCarrusel;
    if (!Number.isInteger(mostrada)) return;
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
    currentCasinoOperador = operador;

    const certaintySlider = document.getElementById('slider-risk-certainty');
    const certeza = certaintySlider ? parseFloat(certaintySlider.value) / 100.0 : 0.80;

    // [ARCH-1.4.30] Masa Γ de Capa 0 seleccionada en la barra de configuración (67% | 70% | 75%).
    const gammaSeleccionada = parseFloat(document.querySelector('input[name="opcion_gamma"]:checked')?.value || "0.67");

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
                operador: operador,
                gamma_slider: gammaSeleccionada
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
let currentCasinoOperador = "caliente";

// ─── [DES-QBE-055 / ARCH-1.5.10-B] Rótulo de Casa Patrocinadora por Boleto ─────
// El emblema viaja desde la bóveda LOCAL de activos (`/static/img/bookmakers/{slug}.png`,
// anclada por `scripts/utilidades/sincronizar_boveda_activos.py`). Cero hotlinking a
// servidores de terceros ([ARCH-1.5.10-B]). Si el plan no expone operador (modalidad
// mono-casa heredada), se conserva el rótulo genérico de ventanilla: degradación
// declarada, jamás una casa inventada ([GOVERNANCE-01]).
// [DES-QBE-055] Pie de boleto split sobrio: rótulo + emblema de la bóveda local, SIN el nombre
// textual del casino (deroga el sufijo `{NOMBRE_CASINO}` de [DES-QBE-053]). El operador se
// identifica por el logo y por su tooltip fiduciario; jamás se duplica el texto en el boleto.
function _rotuloCasaApostar(slugOperador) {
    const etiqueta = `<span class="ticket-action-label" style="font-size:7pt; color:#94A3B8; font-weight:700;">APOSTAR EN:</span>`;
    if (!slugOperador) return `${etiqueta} <span style="font-size:7pt; color:#94A3B8;">VENTANILLA</span>`;
    const slug = String(slugOperador).toLowerCase();
    // Bóveda local ([ARCH-1.5.10-B]): PNG oficial si está anclado; si no, respaldo SVG local;
    // en última instancia el emblema se oculta (degradación declarada, cero hotlink).
    const onerror = "if(!this.dataset.fb){this.dataset.fb='1';this.src='/static/img/bookmakers/" +
        slug + ".svg';}else{this.style.display='none';}";
    return `${etiqueta} <img src="/static/img/bookmakers/${slug}.png" class="bookmaker-logo-inline" alt="${slug}" title="Operador: ${slug.toUpperCase()}" style="height:18px; vertical-align:middle; margin-left:4px;" onerror="${onerror}">`;
}

// ─── [ARCH-1.4.15] Disponibilidad Dinámica de Operadores en Ventanilla ───────
// El backend declara la captura fáctica por casa. Una casa con `disponible: false` no
// puede simular cuotas ajenas: se inhabilita y se rotula explícitamente.
function _aplicarDisponibilidadOperadores(mapaOperadores) {
    const sel = document.getElementById("casino-operator-select");
    if (!sel || !mapaOperadores || Object.keys(mapaOperadores).length === 0) return;

    const etiquetaBase = {};
    Array.from(sel.options).forEach(op => {
        etiquetaBase[op.value] = (op.textContent || "").replace(/\s*\(Sin cuotas disponibles\)\s*$/, "").trim();
    });

    Array.from(sel.options).forEach(op => {
        const info = mapaOperadores[op.value];
        if (!info || info.disponible === undefined) return;
        const disponible = info.disponible !== false;
        op.disabled = !disponible;
        op.textContent = disponible ? etiquetaBase[op.value] : `${etiquetaBase[op.value]} (Sin cuotas disponibles)`;
    });

    const actual = sel.options[sel.selectedIndex];
    if (actual && actual.disabled) {
        const primera = Array.from(sel.options).find(op => !op.disabled);
        if (primera) sel.value = primera.value;
    }
}

function renderizarResultadosPortafolio(data) {
    currentPortfolioData = data;
    // [DES-QBE-045] Consumo de las claves canónicas 3NF emitidas por markets.py (con fallback declarado).
    const orders = data.ordenes_ejecucion_partidos || data.ordenes || [];
    const control = data.control_portafolio || data.control || {};
    const balance = data.balance_global_portafolio || data.balance || {};
    const meta = data.metadata || {};

    // [ARCH-1.4.15] Contrato de disponibilidad: una casa sin cuotas capturadas en la jornada
    // activa se rotula `(Sin cuotas disponibles)` y queda inhabilitada en el selector.
    _aplicarDisponibilidadOperadores(data.operadores_disponibles || {});

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
    // [ARCH-1.4.14 / DES-QBE-054] Denominador fáctico de cartelera: el KPI se lee K / 9 (jornada
    // oficial), nunca K / K. `total_partidos_jornada` es el campo legislado; se conserva el
    // fallback declarado a `total_partidos_escaneados` y al tamaño de la cartera entregada.
    const totalJornada = control.total_partidos_jornada || control.total_partidos_escaneados || orders.length;

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
    if (elCore) elCore.textContent = `${kAprobados} / ${totalJornada}`;

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
            // [LN-QBE-083-B] [ARCH-1.4.16-B] Tramo 4: las familias DIRECTAS (QBE-D1 y QBE-D2) carecen de
            // pierna de cobertura en tablas ⇒ comparten el rótulo único de riesgo directo. El literal
            // genérico "Recuperas $X MXN ($0.00 pérdida)" queda erradicado para ellas: es fiduciariamente
            // falso al no existir recuperación alguna ([GOVERNANCE-01]).
            if (cod.startsWith("QBE-D1") || cod.startsWith("QBE-D2")) {
                coberturaHtml = `<span style="color:#f87171; font-weight:600;">Sin cobertura (Riesgo Directo: -$${inv.toFixed(2)})</span>`;
            } else if (cod === "QBE-R2") {
                coberturaHtml = `<span style="color:#00E676; font-weight:600;">Ambos boletos ganan (+${roi.toFixed(1)}% ROI)</span>`;
            } else if (cod.startsWith("QBE-H1") || cod.startsWith("QBE-H2") || cod.startsWith("QBE-R1")) {
                coberturaHtml = `<span style="color:#38BDF8;">Recuperas $${tablas.toFixed(2)} MXN ($0.00 pérdida)</span>`;
            }

            // [ARCH-1.4.16-B] Tramo 3: el horario fáctico del encuentro se publica como línea secundaria
            // dentro de la columna PARTIDO (`horario_evento` es contrato sellado por [ARCH-1.4.16] y lo
            // emite src/web/routes/markets.py). Sin horario declarado no se inventa placeholder:
            // la fila se emite sin línea secundaria ([GOVERNANCE-01]).
            const horarioHtml = ord.horario_evento
                ? `<small style="display:block; font-weight:400; color:var(--text-muted); font-size:7.6pt;">⏰ ${ord.horario_evento}</small>`
                : "";

            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td style="font-weight:700; color:#fff;">${ord.partido}${horarioHtml}</td>
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
            const opSlugB1 = (b1.operador || currentCasinoOperador || "caliente");
            const opSlugB2 = (b2.operador || currentCasinoOperador || "caliente");
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

            // [DES-QBE-061] Formato Dual de la cuota: probabilidad implícita del casino + decimal.
            // prob_implicita = 100.0 / O_casino (1 decimal, [DES-QBE-061]). Cero conversión en el
            // cliente: los momios ya viajan canónicos desde el motor ([GOVERNANCE-01] paridad).
            const _momioDual = (momio) => {
                const m = Number(momio);
                return (m > 1.0) ? `${(100.0 / m).toFixed(1)}% (@${m.toFixed(2)})` : '—';
            };
            const momioDualB1 = _momioDual(b2.momio);   // BOLETO 1 exhibido: GANANCIA (ataque)
            const momioDualB2 = _momioDual(b1.momio);   // BOLETO 2 exhibido: SEGURO (recuperación)
            // [DES-QBE-062] El renglón de Doble Cobro se gobierna por la bandera PA
            // ([DES-QBE-045]: por bandera booleana, jamás por proxies de proyección heredados).
            const paActivo = (ord.pa_activo === true) || Boolean(est.linea_promocional);

            // [DES-QBE-062] Tetralogía de Escenarios en orden estricto y estilo sobrio (CERO balazos)
            let escenariosHtml = `
                <div style="font-size: 7.8pt; line-height: 1.6; color: #94A3B8; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 8px;">
                    <div>• <strong style="color: #e2e8f0;">Ganancia Principal:</strong> Cobro de $${cobroPrincipal} MXN (+$${proy.ganancia_neta_principal_mxn?.toFixed(2)} MXN netos, +${proy.roi_principal_porcentaje?.toFixed(1)}% ROI).</div>
            `;

            if (b1Monto > 0) {
                // [INVARIANTE VIII-11] Tras la Resolución Definitiva de VARIANZA-H2, la pierna de
                // recuperación (`boleto_1_seguro`) es SIEMPRE el Empate en toda la Familia H
                // (H1/H2). El renglón exhibe el capital recuperado CERTIFICADO POR EL MOTOR
                // (`inv`, con V=0 garantizado por `calcular_dutching_v0`), sin re-derivaciones
                // del cliente ([GOVERNANCE-01] paridad estricta backend↔pantalla).
                escenariosHtml += `
                    <div>• <strong style="color: #e2e8f0;">Cobertura en Empate:</strong> Recuperación de $${inv.toFixed(2)} MXN ($0.00 pérdida de capital).</div>
                `;
            }

            // Renglón 3: Pago Anticipado con Empate (Doble Cobro) si pa_activo es True y existe seguro
            if (paActivo && b1Monto > 0) {
                const dobleCobroTot = (Number(cobroPrincipal) + Number(retornoTablas)).toFixed(2);
                const dobleCobroNeto = Number(cobroPrincipal).toFixed(2);
                const dobleRoi = ((Number(dobleCobroNeto) / Math.max(0.01, inv)) * 100).toFixed(1);
                escenariosHtml += `
                    <div>• <strong style="color: #00E676;">Pago Anticipado con Empate:</strong> Cobro de AMBOS boletos por $${dobleCobroTot} MXN (+$${dobleCobroNeto} netos, +${dobleRoi}% ROI) si el favorito toma ventaja de 2 goles y el juego concluye empatado.</div>
                `;
            }

            // Renglón 4: Salida de Emergencia (Rompe-Quinielas)
            if (b1Monto > 0) {
                escenariosHtml += `
                    <div>• <strong style="color: #F59E0B;">Salida de Emergencia:</strong> Si el rival anota primero, ejecutar CashOut al empatar en el 2T en cuanto ofrezca Tablas ($${inv.toFixed(2)} MXN) para recuperar el 100% del capital.</div>
                `;
            }
            escenariosHtml += `</div>`;

            // [DES-QBE-060] Anatomía enriquecida del boleto: P' fiduciario por pierna y bloque de
            // transparencia 360°. El cliente NO calcula probabilidades: consume el contrato
            // hidratado por `PortfolioEngine.build_plan()` ([GOVERNANCE-01] paridad fáctica).
            const probB1Txt = (b2.prob_qbe === null || b2.prob_qbe === undefined) ? '—' : `${Number(b2.prob_qbe).toFixed(1)}%`;
            const probB2Txt = (b1.prob_qbe === null || b1.prob_qbe === undefined) ? '—' : `${Number(b1.prob_qbe).toFixed(1)}%`;
            const unbet = ord.opcion_no_jugada || {};
            const unbetNombre = unbet.nombre || 'Rival Descartado';
            const momioDualUnbet = _momioDual(unbet.momio);
            const unbetProb = (unbet.prob_qbe === null || unbet.prob_qbe === undefined) ? '—' : `${Number(unbet.prob_qbe).toFixed(1)}%`;
            // Cero jerga técnica y cero títulos ruidosos en este bloque ([DES-QBE-060]).
            const opcionNoJugadaHtml = `
                <div style="margin-top:8px; padding-top:6px; border-top:1px solid rgba(51,65,85,0.4); font-size:7.5pt; color:#94A3B8; font-family:monospace;">
                    • Opción No Jugada: <span style="color:#cbd5e1; font-weight:700;">${unbetNombre}</span> ──► Momio Casino: <strong style="color:#fff;">${momioDualUnbet}</strong> | Predicción Q-BE con P': <strong style="color:#38BDF8;">${unbetProb}</strong>
                </div>
            `;

            // [DES-QBE-069] Acciones de tarjeta: compra congelada en el Ledger + copia de ticket.
            const yaComprado = _verificarBoletoComprado(ord.id_partido);
            const btnComprarHtml = yaComprado
                ? `<button class="btn btn-sm" style="background:#1e293b; color:#00E676; border:1px solid #00E676; padding:6px 14px; border-radius:4px; font-size:7.8pt; font-weight:800; cursor:default;" disabled>✔ Boleto Registrado</button>`
                : `<button id="btn-comprar-${ord.id_partido}" onclick="comprarBoleto('${ord.id_partido}')" style="background:linear-gradient(135deg, #00E676 0%, #059669 100%); border:none; color:#0b1120; padding:6px 16px; border-radius:4px; font-size:8pt; font-weight:800; cursor:pointer; box-shadow:0 0 10px rgba(0,230,118,0.3);">🎟️ Comprar Boleto</button>`;

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
                        <div style="font-size:7.5pt; color:#94A3B8; margin-top:2px;">Momio Casino: <strong style="color:#fff;">${momioDualB1}</strong></div>
                        <div style="font-size:7.5pt; color:#94A3B8;">Predicción Q-BE con P': <strong style="color:#38BDF8;">${probB1Txt}</strong></div>
                        <div style="margin-top:6px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.05); display:flex; justify-content:space-between; align-items:flex-end;">
                            <span>${_rotuloCasaApostar(opSlugB2)}</span>
                            <span style="font-size:1.35rem; font-weight:900; color:#00E676;">$${(b2.monto_mxn || 0).toFixed(2)} MXN</span>
                        </div>
                    </div>

                    <!-- BOLETO SEGURO / RECUPERACIÓN (DERECHA - AZUL) -->
                    <div style="background:#0f172a; border:1px solid rgba(56,189,248,0.3); border-radius:6px; padding:12px;">
                        <span style="font-size:7.2pt; color:#38BDF8; font-weight:800;">🛡️ BOLETO 2: SEGURO (RECUPERACIÓN)</span>
                        <div style="font-size:1rem; font-weight:700; color:#fff; margin-top:3px;">${b1.seleccion || 'N/A ($0.00)'}</div>
                        <div style="font-size:7.5pt; color:#94A3B8; margin-top:2px;">Momio Casino: <strong style="color:#fff;">${momioDualB2}</strong></div>
                        <div style="font-size:7.5pt; color:#94A3B8;">Predicción Q-BE con P': <strong style="color:#38BDF8;">${probB2Txt}</strong></div>
                        <div style="margin-top:6px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.05); display:flex; justify-content:space-between; align-items:flex-end;">
                            <span>${_rotuloCasaApostar(opSlugB1)}</span>
                            <span style="font-size:1.35rem; font-weight:900; color:#38BDF8;">$${(b1.monto_mxn || 0).toFixed(2)} MXN</span>
                        </div>
                    </div>
                </div>

                <!-- Escenarios Desglosados Sobrios -->
                <div style="background:rgba(0,0,0,0.25); border-radius:6px; padding:10px 14px; margin-bottom:12px;">
                    ${escenariosHtml}
                </div>

                <!-- [DES-QBE-060] Bloque de Transparencia 360° al Pie de Tarjeta -->
                <div style="background:rgba(0,0,0,0.25); border-radius:6px; padding:8px 14px; margin-bottom:12px;">
                    ${opcionNoJugadaHtml}
                </div>

                <!-- [DES-QBE-069] Barra de dos extremos: Análisis (izq.) · Copiar + Comprar (der.) -->
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.06);">
                    <button onclick="abrirRadiografiaForense('${ord.id_partido}')" style="background:transparent; border:1px solid #38BDF8; color:#38BDF8; padding:6px 14px; border-radius:4px; font-size:7.8pt; font-weight:700; cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
                        🔬 Ver Análisis Cuantitativo
                    </button>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <button onclick="copiarTicketPortapapeles('${ord.id_partido}')" style="background:rgba(255,255,255,0.04); border:1px solid #334155; color:#94A3B8; padding:6px 12px; border-radius:4px; font-size:7.8pt; cursor:pointer;" title="Copiar resumen para WhatsApp o terminal">
                            📋 Copiar Ticket
                        </button>
                        ${btnComprarHtml}
                    </div>
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
                const m = d.metricas || {};
                const cifrasHtml = m.alpha_max !== undefined ?
                    `<div style="font-family: monospace; font-size: 7.2pt; color: #94A3B8; margin-top: 4px;">
                        Fav: ${(m.p_fav * 100).toFixed(0)}% (@${m.cuota_fav}) · Emp: @${m.cuota_empate} · α_max: <span style="color:#ef4444;">${(m.alpha_max * 100).toFixed(1)}% (-EV)</span> · θ*: ${m.theta_estrella}
                    </div>` : '';
                const item = document.createElement("div");
                item.style.cssText = "background:rgba(239,68,68,0.06); border:1px solid rgba(239,68,68,0.3); border-radius:6px; padding:10px 14px;";
                item.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <strong style="color:#fff; font-size:9pt;">❌ ${d.partido}</strong>
                        <span style="background:rgba(239,68,68,0.2); color:#ef4444; border:1px solid #ef4444; padding:2px 6px; border-radius:4px; font-size:7pt; font-weight:800;">VETO: ${d.motivo_codigo || 'QBE-00'}</span>
                    </div>
                    <div style="color:#cbd5e1; font-size:7.8pt;">${d.explicacion_didactica || d.motivo}</div>
                    ${cifrasHtml}
                `;
                contDescartes.appendChild(item);
            });
        }
    }
}

// ─── Modal de Radiografía Forense REBORN [LN-QBE-098 / ARCH-1.4.31 / DES-QBE-063] ──
// Cero red y cero LLM: toda la hidratación es determinista en O(1) sobre el payload
// soberano ya presente en memoria ([GOVERNANCE-01] paridad backend↔pantalla).

/** Densidad Poisson P(X=k) = λ^k · e^(-λ) / k!. Cálculo local determinista. */
function _calcularPoissonP(lambda, k) {
    let fact = 1;
    for (let i = 2; i <= k; i++) fact *= i;
    return (Math.pow(lambda, k) * Math.exp(-lambda)) / fact;
}

/** [DES-QBE-063] Radar Factual de 3 Factores y Top-4 de marcadores Poisson.
 *  Reemplaza la prosa generativa de Gemini por una síntesis local en O(1). */
function _hidratarRadarYMarcadores(p) {
    const lamH = Number(p.lambda_local ?? p.lambda_home ?? p.xg_local ?? 1.5);
    const lamA = Number(p.mu_visita ?? p.lambda_away ?? p.xg_visita ?? 1.1);
    // Nombres de los contendientes para humanizar las etiquetas del radar.
    const localNom = (String(p.partido || "Local vs Visita").split(" vs ")[0] || "Local").trim();
    const visitaNom = (String(p.partido || "Local vs Visita").split(" vs ")[1] || "Visita").trim();

    // 1. Peligro Ofensivo Esperado: diferencial de goles esperados (λ_H − λ_A).
    const diffXg = lamH - lamA;
    const facOfEl = document.getElementById("rad-fac-ofensiva");
    const barOfEl = document.getElementById("rad-bar-ofensiva");
    if (facOfEl && barOfEl) {
        const liderNom = diffXg >= 0 ? localNom : visitaNom;
        facOfEl.textContent = `${liderNom} genera +${Math.abs(diffXg).toFixed(2)} goles esperados de peligro`;
        barOfEl.style.width = `${Math.min(100, Math.max(10, 50 + diffXg * 25))}%`;
    }

    // 2. Vulnerabilidad del Rival / Contención: anclada al SoTA promedio de la tabla 10P
    //    (menor exposición ⇒ mayor contención). Sin 10P, degrada al diferencial implícito en λ.
    const t10 = Array.isArray(p.tabla_10p) ? p.tabla_10p : [];
    let solidezEdge = (t10.length >= 2 && t10[0].sota !== undefined && t10[1].sota !== undefined)
        ? Number(t10[1].sota) - Number(t10[0].sota)
        : (lamA - lamH);
    const facDefEl = document.getElementById("rad-fac-defensa");
    const barDefEl = document.getElementById("rad-bar-defensa");
    if (facDefEl && barDefEl) {
        const etiqueta = solidezEdge >= 0
            ? `${visitaNom} concede más tiros a puerta`
            : `${localNom} muestra mayor exposición`;
        facDefEl.textContent = `${etiqueta} (${solidezEdge >= 0 ? "+" : ""}${solidezEdge.toFixed(2)} ΔSoTA)`;
        barDefEl.style.width = `${Math.min(95, Math.max(10, 50 + solidezEdge * 6))}%`;
    }

    // 3. Factor Estadio / Territorio: log-boost territorial ln(λ_H / λ_A).
    const facLocEl = document.getElementById("rad-fac-localia");
    const barLocEl = document.getElementById("rad-bar-localia");
    if (facLocEl && barLocEl && lamA > 0) {
        const logBoost = Math.log(lamH / lamA);
        const boostPct = Math.round(Math.abs(logBoost) * 100);
        facLocEl.textContent = `La localía en casa de ${localNom} inclina el juego (+${boostPct}% impulso)`;
        barLocEl.style.width = `${Math.min(95, Math.max(10, 50 + logBoost * 40))}%`;
    }

    // 4. Top-4 marcadores más probables a partir de la rejilla Poisson 0..3.
    const scores = [];
    for (let x = 0; x <= 3; x++) {
        for (let y = 0; y <= 3; y++) {
            scores.push({ marcador: `${x} - ${y}`, prob: _calcularPoissonP(lamH, x) * _calcularPoissonP(lamA, y) });
        }
    }
    scores.sort((a, b) => b.prob - a.prob);
    const topContainer = document.getElementById("rad-top-marcadores");
    if (topContainer) {
        topContainer.innerHTML = scores.slice(0, 4).map(s => `
            <div style="background: #1e293b; padding: 6px 10px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #f8fafc; font-size: 0.85rem;">${s.marcador}</strong>
                <span style="color: #38bdf8; font-size: 0.78rem; font-weight: 600;">${(s.prob * 100).toFixed(1)}%</span>
            </div>
        `).join("");
    }
}

/** [LN-QBE-098] Comparador de 6 columnas de probabilidad (cero momios).
 *  Colorimetría de boletos: Verde #00E676 = Ataque (Boleto 1), Azul #38BDF8 = Cobertura (Boleto 2). */
function _hidratarTablasRadiografia(p) {
    const COLOR_ATAQUE = "#00E676";
    const COLOR_COBERTURA = "#38BDF8";
    const COLOR_NEUTRO = "#94A3B8";
    const ord = p.orden || (Array.isArray(p.ordenes) ? p.ordenes[0] : null);

    // P' certificado (prob_qbe) por pierna + operador asignado, desde la orden soberana.
    const boletos = (ord && ord.boletos) || {};
    const legAtaque = boletos.boleto_2_ganancia || {};
    const legCobertura = boletos.boleto_1_seguro || {};
    const opNoJugada = (ord && ord.opcion_no_jugada) || {};

    const filas = Array.isArray(p.probabilidades_3vias) ? p.probabilidades_3vias : [];

    // Favorito: por bandera, por nombre o por máxima probabilidad deportiva.
    let idxFav = null;
    if (p.is_fav_local === true) idxFav = 0;
    else if (p.is_fav_local === false) idxFav = filas.length - 1;
    else {
        let best = -1;
        filas.forEach((pv, i) => {
            if (/empate/i.test(String(pv.resultado || ""))) return;
            const pr = Number(pv.prob_real) || 0;
            if (pr > best) { best = pr; idxFav = i; }
        });
    }

    const consenso = p.consenso_mercado || null;
    const consensoSeq = consenso ? [consenso.p_L_mercado, consenso.p_E_mercado, consenso.p_V_mercado] : [];
    const fmtPct = (v) => (v === null || v === undefined || isNaN(Number(v))) ? "—" : `${Number(v).toFixed(1)}%`;

    const tbodyPron = document.getElementById("rad-cuerpo-pronostico");
    if (tbodyPron && filas.length) {
        tbodyPron.innerHTML = filas.map((pv, i) => {
            const esEmpate = /empate/i.test(String(pv.resultado || ""));
            const esAtaque = (!esEmpate && idxFav === i);
            const rol = esEmpate ? "cobertura" : (esAtaque ? "ataque" : "none");
            const colorRes = esAtaque ? COLOR_ATAQUE : (esEmpate ? COLOR_COBERTURA : COLOR_NEUTRO);

            // P' fiduciaria CERTIFICADA por el motor, tomada de la pierna correspondiente.
            let pPrima = null, operador = null;
            if (rol === "ataque") { pPrima = legAtaque.prob_qbe; operador = legAtaque.operador; }
            else if (rol === "cobertura") { pPrima = legCobertura.prob_qbe; operador = legCobertura.operador; }
            else { pPrima = opNoJugada.prob_qbe; operador = opNoJugada.operador; }
            if (pPrima === null || pPrima === undefined) pPrima = pv.prob_real;

            // [DES-QBE-063] Columna CASINO SELECCIONADO: operador ESPECÍFICO de CADA pierna.
            // Se descarta el rótulo residual de la modalidad cross-market ('mejor_combinacion'):
            // sólo se exhibe una casa real que publica cuota de ESTE desenlace, jamás el
            // selector global. Sin operador asignado ⇒ '—' (cero cifras inventadas).
            const slugOp = (operador && String(operador).toLowerCase() !== "mejor_combinacion")
                ? String(operador).toLowerCase()
                : null;
            const nombreCap = slugOp ? slugOp.charAt(0).toUpperCase() + slugOp.slice(1) : null;
            const casinoTxt = slugOp
                ? ((esAtaque || esEmpate)
                    ? `<span style="color: ${colorRes}; font-weight: 700;">⭐ ${nombreCap}</span>`
                    : `<span style="color: #64748b;">${nombreCap}</span>`)
                : "—";

            // P̂ deportiva soberana (física de goles) certificada por el motor.
            const pDeportiva = pv.prob_real;

            // Consenso de mercado des-marginado (vig-free) si el fixture lo expone.
            const cRaw = consensoSeq[i];
            const pConsenso = (cRaw === null || cRaw === undefined) ? null : Number(cRaw) * 100.0;

            // Ventaja matemática neta sobre la casa: α = p·O − 1.0 ([LN-QBE-098]).
            const momio = Number(pv.momio);
            const alpha = (Number(pv.prob_real) > 0 && momio > 1.0)
                ? (Number(pv.prob_real) / 100.0) * momio - 1.0
                : null;
            const alphaColor = (alpha !== null && alpha > 0) ? COLOR_ATAQUE : "#EF4444";
            const alphaTxt = (alpha === null) ? "—" : `${alpha >= 0 ? "+" : ""}${(alpha * 100).toFixed(2)}%`;

            return `
                <tr style="border-top: 1px solid #1e293b;">
                    <td style="padding: 9px 14px; font-weight: 700; color: ${colorRes};">${pv.resultado}</td>
                    <td style="padding: 9px 10px; text-align: center; font-family: monospace; color: ${colorRes};">${fmtPct(pPrima)}</td>
                    <td style="padding: 9px 10px; text-align: center; font-family: monospace; color: #cbd5e1;">${fmtPct(pDeportiva)}</td>
                    <td style="padding: 9px 10px; text-align: center; font-family: monospace; color: #cbd5e1;">${fmtPct(pConsenso)}</td>
                    <td style="padding: 9px 10px; text-align: center; font-family: monospace; color: #94a3b8;">${fmtPct(pv.prob_casino)}</td>
                    <td style="padding: 9px 10px; text-align: center; color: #e2e8f0; font-weight: 600;">${casinoTxt}</td>
                    <td style="padding: 9px 14px; text-align: right; font-weight: 800; color: ${alphaColor};">${alphaTxt}</td>
                </tr>
            `;
        }).join("");
    }

    // Margen comercial implícito del operador (Σ probabilidades implícitas − 100%).
    const footerCom = document.getElementById("rad-footer-comisiones");
    if (footerCom && filas.length) {
        const suma = filas.reduce((acc, pv) => acc + (Number(pv.prob_casino) || 0), 0);
        footerCom.textContent = (suma > 0)
            ? `Margen comercial implícito del operador: ${(suma - 100).toFixed(1)}% · Comparación pura de probabilidades (sin cuota decimal).`
            : "";
    }

    // KPI Tiles: intensidades de gol y pago anticipado.
    const kLambda = document.getElementById("rad-kpi-lambda");
    const kMu = document.getElementById("rad-kpi-mu");
    const kTot = document.getElementById("rad-kpi-totales");
    const kPa = document.getElementById("rad-kpi-pa");
    if (kLambda) kLambda.textContent = (p.lambda_local !== undefined && p.lambda_local !== null) ? Number(p.lambda_local).toFixed(2) : "--";
    if (kMu) kMu.textContent = (p.mu_visita !== undefined && p.mu_visita !== null) ? Number(p.mu_visita).toFixed(2) : "--";
    if (kTot) kTot.textContent = (p.xg_total !== undefined && p.xg_total !== null) ? Number(p.xg_total).toFixed(2) : "--";
    if (kPa) kPa.textContent = (p.phi_lead2_pct !== undefined && p.phi_lead2_pct !== null) ? `${Number(p.phi_lead2_pct).toFixed(1)}%` : "--";

    // Tabla de desempeño y control de cancha (10P).
    const tbodyEq = document.getElementById("rad-cuerpo-equipos");
    if (tbodyEq && p.tabla_10p) {
        tbodyEq.innerHTML = p.tabla_10p.map(row => `
            <tr style="border-top: 1px solid #1e293b;">
                <td style="padding: 7px 14px; font-weight: 700; color: #f8fafc;">${row.equipo}</td>
                <td style="padding: 7px 10px; text-align: center;">#${row.puesto}</td>
                <td style="padding: 7px 10px; text-align: center; font-weight: 700; color: #00E676;">${row.pts}</td>
                <td style="padding: 7px 10px; text-align: center;">${row.gf_gc}</td>
                <td style="padding: 7px 10px; text-align: center;">${(row.pts_pj ?? 0).toFixed(2)}</td>
                <td style="padding: 7px 10px; text-align: center;">${(row.sot ?? 0).toFixed(1)}</td>
                <td style="padding: 7px 10px; text-align: center;">${(row.sota ?? 0).toFixed(1)}</td>
                <td style="padding: 7px 10px; text-align: center;">${(row.posesion ?? 0).toFixed(1)}%</td>
                <td style="padding: 7px 10px; text-align: center; font-weight: 700; color: #38BDF8;">${(row.qmod ?? 0).toFixed(2)}</td>
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
    // Orden soberana asociada (P' fiduciaria por pierna y operador) — clave canónica 3NF
    // `ordenes_ejecucion_partidos` con fallback declarado a `ordenes` ([DES-QBE-045]).
    const allOrders = currentPortfolioData?.ordenes_ejecucion_partidos
        || currentPortfolioData?.ordenes
        || [];
    p.orden = allOrders.find(x => x.id_partido === matchId) || p.orden || null;

    document.getElementById("modal-radiografia-forense").style.display = "block";

    // [DES-QBE-063] Cabecera: píldora de estrategia REAL (familia canónica QBE-H/D/R/C)
    // resuelta desde la orden soberana; jamás el residuo genérico 'QBE-00' por omisión.
    const badgeEl = document.getElementById("rad-estrategia-badge");
    if (badgeEl) {
        const ordBadge = p.orden || {};
        const stratCode = (ordBadge.estrategia_seleccionada && ordBadge.estrategia_seleccionada.codigo)
            || ordBadge.estrategia_codigo
            || p.estrategia_codigo
            || p.strategy_code
            || "QBE-00";
        const pal = _paletaEstrategia(stratCode);
        badgeEl.textContent = stratCode;
        badgeEl.style.color = pal.fg;
        badgeEl.style.borderColor = pal.borde;
        badgeEl.style.background = pal.bg;
    }
    const tituloEl = document.getElementById("rad-titulo-partido");
    if (tituloEl) tituloEl.textContent = p.partido || p.partido_nombre || "Partido";
    const horarioEl = document.getElementById("rad-horario");
    if (horarioEl) horarioEl.textContent = String(p.horario || "").replace(/\n/g, " ");

    // [LN-QBE-098] Hidratación 100% local y determinista: Gemini permanece en reposo total (cero red).
    _hidratarRadarYMarcadores(p);
    _hidratarTablasRadiografia(p);
}

function cerrarRadiografiaForense() {
    document.getElementById("modal-radiografia-forense").style.display = "none";
}
window.abrirRadiografiaForense = abrirRadiografiaForense;
window.cerrarRadiografiaForense = cerrarRadiografiaForense;

// ─── [DES-QBE-069] SISTEMA DE CONGELAMIENTO "COMPRAR BOLETO" (LEDGER INMUTABLE) ──
// El estado del boleto se congela al momento de la compra para auditoría post-partido:
// cuotas, importes y proyecciones quedan inmutables en localStorage. Cero red y cero
// LLM ([GOVERNANCE-01]): la UI sólo persiste el contrato ya hidratado por el motor.

/** ¿El boleto de este partido ya fue congelado en el Ledger local? */
function _verificarBoletoComprado(matchId) {
    try {
        const ledger = JSON.parse(localStorage.getItem("qbe_boletos_comprados") || "[]");
        return ledger.some(t => t.id_partido === matchId);
    } catch (e) {
        return false;
    }
}

/** [MEJORA 1] Refresca el contador de boletos comprados en la barra superior. */
function _actualizarContadorBoletosComprados() {
    let ledger = [];
    try {
        ledger = JSON.parse(localStorage.getItem("qbe_boletos_comprados") || "[]");
    } catch (e) {
        ledger = [];
    }
    const count = ledger.length;
    const totalComprometido = ledger.reduce((acc, t) => acc + (Number(t.inversion_total_mxn) || 0), 0);
    const badge = document.getElementById("badge-boletos-comprados");
    if (badge) {
        badge.textContent = `🎟️ Comprados: ${count} ($${totalComprometido.toFixed(2)} MXN)`;
    }
}

/** [CONGELAMIENTO] Almacena el estado INMUTABLE del boleto en el momento de la compra. */
function comprarBoleto(matchId) {
    const allOrders = currentPortfolioData?.ordenes_ejecucion_partidos
        || currentPortfolioData?.ordenes
        || [];
    const ord = allOrders.find(x => x.id_partido === matchId);
    if (!ord) return;

    const b1 = ord.boletos?.boleto_1_seguro || {};
    const b2 = ord.boletos?.boleto_2_ganancia || {};

    const ticketCongelado = {
        id_partido: ord.id_partido,
        partido: ord.partido,
        horario_evento: ord.horario_evento,
        estrategia: ord.estrategia_seleccionada?.codigo || ord.estrategia_codigo,
        inversion_total_mxn: ord.boletos?.inversion_partido_A_i || 0,
        pierna_ataque: {
            seleccion: b2.seleccion,
            monto_mxn: b2.monto_mxn,
            momio_congelado: b2.momio,
            operador: b2.operador,
            prob_p_prime: b2.prob_qbe
        },
        pierna_seguro: {
            seleccion: b1.seleccion,
            monto_mxn: b1.monto_mxn,
            momio_congelado: b1.momio,
            operador: b1.operador,
            prob_p_prime: b1.prob_qbe
        },
        proyecciones: ord.proyecciones,
        timestamp_compra_utc: new Date().toISOString(),
        estado_auditoria: "PENDIENTE_RESULTADO"
    };

    let ledger = [];
    try {
        ledger = JSON.parse(localStorage.getItem("qbe_boletos_comprados") || "[]");
    } catch (e) {
        ledger = [];
    }
    ledger = ledger.filter(t => t.id_partido !== matchId);
    ledger.push(ticketCongelado);
    localStorage.setItem("qbe_boletos_comprados", JSON.stringify(ledger));

    // Feedback visual inmediato en el botón de compra de la tarjeta.
    const btn = document.getElementById(`btn-comprar-${matchId}`);
    if (btn) {
        btn.style.background = "#1e293b";
        btn.style.color = "#00E676";
        btn.style.border = "1px solid #00E676";
        btn.style.boxShadow = "none";
        btn.style.cursor = "default";
        btn.innerHTML = "✔ Boleto Registrado";
        btn.disabled = true;
    }

    _actualizarContadorBoletosComprados();
    alert(`🎟️ Boleto congelado exitosamente para ${ord.partido}.\nLas cuotas e importes se han registrado para auditoría post-partido.`);
}

/** [MEJORA 2] Copia al portapapeles el ticket en formato limpio para ventanilla / WhatsApp. */
function copiarTicketPortapapeles(matchId) {
    const allOrders = currentPortfolioData?.ordenes_ejecucion_partidos
        || currentPortfolioData?.ordenes
        || [];
    const ord = allOrders.find(x => x.id_partido === matchId);
    if (!ord) return;

    const b1 = ord.boletos?.boleto_1_seguro || {};
    const b2 = ord.boletos?.boleto_2_ganancia || {};
    const inv = ord.boletos?.inversion_partido_A_i || 0;

    let texto = `🏛️ TICKET Q-BE · ${ord.partido}\n`;
    texto += `⏰ ${ord.horario_evento} | Inversión: $${Number(inv).toFixed(2)} MXN\n`;
    texto += `• Boleto 1 (Ataque): ${b2.seleccion} @${b2.momio} (${String(b2.operador || "").toUpperCase()}) ➔ $${Number(b2.monto_mxn || 0).toFixed(2)} MXN\n`;
    if (Number(b1.monto_mxn || 0) > 0) {
        texto += `• Boleto 2 (Seguro): ${b1.seleccion} @${b1.momio} (${String(b1.operador || "").toUpperCase()}) ➔ $${Number(b1.monto_mxn || 0).toFixed(2)} MXN (Tablas V=0)\n`;
    }
    texto += `🎯 Ganancia Neta: +$${Number(ord.proyecciones?.ganancia_neta_principal_mxn || 0).toFixed(2)} MXN`;

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(texto)
            .then(() => alert("📋 Ticket copiado al portapapeles."))
            .catch(() => prompt("Copie manualmente el ticket:", texto));
    } else {
        prompt("Copie manualmente el ticket:", texto);
    }
}

window.comprarBoleto = comprarBoleto;
window.copiarTicketPortapapeles = copiarTicketPortapapeles;

// El contador de boletos comprados se hidrata al cargar la SPA.
document.addEventListener("DOMContentLoaded", _actualizarContadorBoletosComprados);

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

    // [ARCH-1.4.20 / VAULT-CORE-084-PROGOL-P-PRIME] Bloque aditivo del motor soberano de masa
    // acumulada P': despliega las boletas priorizadas por maximización de C(M) y su garantía
    // fiduciaria declarada por el backend. Sólo formatea claves ya calculadas por el motor.
    const boletasP = data.boletas || [];
    const bloqueMotorSoberano = boletasP.length === 0 ? "" : `
        <div style="margin-top: 12px; border-top: 1px solid #1E293B; padding-top: 10px;">
            <span style="font-size: 7.2pt; color: #00E676; text-transform: uppercase; font-weight: 800;">Motor de Masa Acumulada P' · ${data.motor || "PROGOL_P_PRIME_MASS"}</span>
            <div style="font-size: 8pt; color: #CBD5E1; margin: 4px 0 6px 0;">
                Garantía fiduciaria: <b style="color:#fff;">${data.garantia_fiduciaria || "—"}</b> ·
                Masa acumulada capturada: <b style="color:#fff;">${Number(data.masa_acumulada_capturada || 0).toExponential(3)}</b>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                ${boletasP.map(b => `<span style="font-family: monospace; font-size: 7.5pt; color: #38BDF8; background: rgba(56,189,248,0.08); border: 1px solid #1E293B; border-radius: 4px; padding: 2px 6px;" title="Boleta #${b.boleta_id} · P' = ${Number(b.prob_conjunta || 0).toExponential(3)}">#${b.boleta_id} ${(b.combinacion || []).join("")}</span>`).join("")}
            </div>
        </div>`;

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
        </table>${bloqueMotorSoberano}`;
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

    // [LN-QBE-098] Passthrough soberano para el comparador de 6 columnas del modal:
    // favorito, consenso des-marginado y localía, ya presentes en el Live Board.
    p.fav_name = f.fav_name || null;
    p.horario = f.horario || null;
    if (typeof f.is_fav_local === "boolean") p.is_fav_local = f.is_fav_local;
    if (f.consenso_mercado) p.consenso_mercado = f.consenso_mercado;
    if (f.estrategia_codigo) p.estrategia_codigo = f.estrategia_codigo;
    if (f.strategy_code) p.strategy_code = f.strategy_code;

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

