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
            card.innerHTML = `
                <div style="font-size: 20pt; margin-bottom: 6px;">${l.flag}</div>
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
async function seleccionarLiga(fotmobId) {
    switchView("view-matchday-selection");
    const tbody = document.querySelector(".table-panel-left table tbody");
    if (tbody) tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:20px; color:#38BDF8;">⏳ Sincronizando los 18 clubes con FotMob...</td></tr>';

    try {
        const resp = await fetch(`/api/leagues/${fotmobId}/live-board`);
        if (!resp.ok) throw new Error("Error al obtener Live Board");
        currentLiveBoard = await resp.json();

        const lblTabla = document.getElementById("lbl-nombre-tabla");
        if (lblTabla) lblTabla.textContent = currentLiveBoard.league_name || "Liga MX";
        const lblJornada = document.getElementById("lbl-nombre-jornada");
        if (lblJornada) lblJornada.textContent = currentLiveBoard.jornada || "Jornada 7";

        renderizarTabla18Clubes(currentLiveBoard.standings);
        renderizarCartelera(currentLiveBoard.fixtures);
    } catch (e) {
        console.error("Error cargando live board:", e);
        if (tbody) tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:#f87171;">❌ Error al conectar: ${e.message}</td></tr>`;
    }
}

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

// 4. Renderizar Cartelera Agrupada por Bloques de Fecha con Checkbox Único (Panel Derecho)
function renderizarCartelera(fixtures) {
    const container = document.querySelector(".fixtures-list");
    if (!container || !fixtures) return;
    container.innerHTML = "";
    selectedMatchIds = [];

    // 1. Agrupar fixtures por bloque de fecha
    const gruposFecha = {};
    fixtures.forEach(f => {
        const fechaLabel = f.fecha_bloque || f.horario_bloque || "Jornada 7";
        if (!gruposFecha[fechaLabel]) gruposFecha[fechaLabel] = [];
        gruposFecha[fechaLabel].push(f);
    });

    // 2. Renderizar bloques con encabezados claros
    Object.keys(gruposFecha).forEach(fechaHeader => {
        const headerDiv = document.createElement("div");
        headerDiv.className = "date-group-header";
        headerDiv.style.cssText = "font-size: 7.8pt; font-weight: 800; color: #38BDF8; margin: 8px 0 4px 0; text-transform: uppercase; letter-spacing: 0.04em;";
        headerDiv.innerHTML = `📅 ${fechaHeader}`;
        container.appendChild(headerDiv);

        gruposFecha[fechaHeader].forEach((f) => {
            const card = document.createElement("div");
            card.className = "fixture-card";
            card.id = `fixture-card-${f.id_partido}`;
            
            const esOperable = f.es_operable !== false && f.momios !== null;
            
            if (esOperable) {
                card.style.cssText = "background: rgba(0,230,118,0.04); border: 1px solid #00E676; border-radius: 6px; padding: 10px; margin-bottom: 6px;";
                selectedMatchIds.push(f.id_partido);
            } else {
                card.style.cssText = "background: rgba(255,255,255,0.02); border: 1px dashed #475569; border-radius: 6px; padding: 10px; margin-bottom: 6px; opacity: 0.7;";
            }

            const checkboxAttr = esOperable
                ? 'checked style="accent-color: #38BDF8; cursor: pointer; width: 15px; height: 15px;"'
                : 'disabled style="cursor: not-allowed; opacity: 0.4; width: 15px; height: 15px;" title="Caliente.mx aún no publica cuotas para este encuentro."';

            let cuotasHtml = '';
            if (f.momios && f.momios.L) {
                const paBadge = f.momios.pago_anticipado ? '<span style="color: #00E676; font-weight: 700; font-size: 6.8pt; margin-left: 4px;">🏷️ PA Activo</span>' : '';
                cuotasHtml = `
                    <span>L <strong style="color: #38BDF8;">${Number(f.momios.L).toFixed(2)}</strong></span>
                    <span>E <strong style="color: #94A3B8;">${Number(f.momios.E).toFixed(2)}</strong></span>
                    <span>V <strong style="color: #94A3B8;">${Number(f.momios.V).toFixed(2)}</strong></span>
                    ${paBadge}
                `;
            } else {
                cuotasHtml = `<span style="color: #94A3B8; font-size: 6.8pt; font-style: italic;">L — | E — | V — &nbsp;<span class="badge-pending" style="color: #94A3B8; font-weight: 600;">⏳ Momios Pendientes</span></span>`;
            }

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="font-size: 7pt; color: #94A3B8;">⏰ ${f.horario}</span>
                    <input type="checkbox" ${checkboxAttr} value="${f.id_partido}"
                           class="fixture-checkbox"
                           onchange="toggleFixtureCheckbox(this, '${f.id_partido}')">
                </div>
                <div style="font-size: 9.2pt; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;">${f.local} vs ${f.visitante}</div>
                <div style="font-size: 7pt; color: #cbd5e1; display: flex; gap: 8px; align-items: center;">
                    ${cuotasHtml}
                </div>
            `;
            container.appendChild(card);
        });
    });

    actualizarContadorSeleccionados();
}


// [DES-QBE-016] Selector único: feedback visual por borde cian, sin texto redundante
function toggleFixtureCheckbox(checkbox, matchId) {
    const card = document.getElementById(`fixture-card-${matchId}`);
    if (checkbox.checked) {
        if (!selectedMatchIds.includes(matchId)) selectedMatchIds.push(matchId);
        if (card) {
            card.style.borderColor = "#38BDF8";
            card.style.background = "rgba(56, 189, 248, 0.05)";
        }
    } else {
        selectedMatchIds = selectedMatchIds.filter(id => id !== matchId);
        if (card) {
            card.style.borderColor = "rgba(255, 255, 255, 0.08)";
            card.style.background = "#0f172a";
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
    const tbody = document.getElementById('portfolio-orders-body');
    if (tbody) tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #38BDF8;">⏳ Ejecutando motor cuantitativo (Poisson 6x6, Kelly & Dutching)...</td></tr>';

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

        if (!resp.ok) throw new Error("Error en cálculo de portafolio");
        const data = await resp.json();
        renderizarResultadosPortafolio(data);
    } catch (e) {
        console.error("Error generando portafolio:", e);
        if (tbody) tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #ef4444;">❌ Error: ${e.message}</td></tr>`;
    }
}

function renderizarResultadosPortafolio(data) {
    const tbody = document.getElementById('portfolio-orders-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    const orders = data.ordenes || data.orders || [];
    if (orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No se generaron órdenes de inversión.</td></tr>';
        return;
    }

    orders.forEach(ord => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${ord.partido || (ord.local + ' vs ' + ord.visitante)}</strong></td>
            <td style="color: var(--accent-cyan); font-weight: 700;">${ord.estrategia_codigo || ord.estrategia || "QBE-D1"}</td>
            <td class="numeric">${ord.momio || "2.10"}</td>
            <td style="color: #00E676;">${ord.seguro || "Cubierto"}</td>
            <td class="numeric" style="font-weight: 700; color: var(--accent-cyan-deep);">$${ord.inversion || ord.stake || "50.00"}</td>
        `;
        tbody.appendChild(tr);
    });

    if (data.portfolio_id) {
        const exportBtn = document.getElementById('export-pdf-btn');
        if (exportBtn) {
            exportBtn.onclick = () => window.open(`/api/portfolio/${data.portfolio_id}/pdf`, '_blank');
        }
    }
}
