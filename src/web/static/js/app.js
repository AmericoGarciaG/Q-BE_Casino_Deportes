// src/web/static/js/app.js
// Q-BE Casino Deportes — Live Board Reactivo SPA (DES-QBE-016 / ARCH-1.6.0)

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

// 1. Cargar Ligas en Vista 1 desde SQLite
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
                    <div style="font-size: 7.2pt; color: #00E676; font-weight: 700; margin-top: 6px;">● Sincronizado en BD (18 Clubes)</div>
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
        
        // Forma con círculos de colores
        const formaHtml = (t.forma || ["G", "E", "P"]).map(f => {
            const cls = (f === "G" || f === "W") ? "badge-g" : (f === "E" || f === "D") ? "badge-e" : "badge-p";
            const letra = (f === "G" || f === "W") ? "G" : (f === "E" || f === "D") ? "E" : "P";
            return `<span class="form-badge ${cls}">${letra}</span>`;
        }).join("");

        const difColor = t.dif >= 0 ? "#00E676" : "#f87171";
        const difSign = t.dif > 0 ? "+" : "";

        tr.innerHTML = `
            <td style="text-align: center; font-weight: 700;">${t.pos}</td>
            <td style="font-weight: 600; color: #ffffff;">🛡️ ${t.equipo}</td>
            <td style="text-align: center; font-weight: 700; color: #00E676;">${t.puntos}</td>
            <!-- General -->
            <td class="col-gen" style="text-align: center;">${t.pj}</td>
            <td class="col-gen" style="text-align: center;">${t.pg}</td>
            <td class="col-gen" style="text-align: center;">${t.pe}</td>
            <td class="col-gen" style="text-align: center;">${t.pp}</td>
            <td class="col-gen" style="text-align: center;">${t.gf}:${t.gc}</td>
            <td class="col-gen" style="text-align: center; font-weight: 700; color: ${difColor};">${difSign}${t.dif}</td>
            <!-- Forma -->
            <td class="col-forma" style="text-align: center; display: none;">${formaHtml}</td>
            <td class="col-forma" style="text-align: center; color: #38BDF8; font-weight: 600; display: none;">${t.proximo_rival || "vs Rival"}</td>
            <!-- xG Opta -->
            <td class="col-xg" style="text-align: center; color: #38BDF8; font-weight: 600; display: none;">${t.xg || "—"}</td>
            <td class="col-xg" style="text-align: center; color: #f87171; display: none;">${t.xga || "—"}</td>
            <td class="col-xg" style="text-align: center; color: #00E676; font-weight: 700; display: none;">${t.xpts || "—"}</td>
            <td class="col-xg" style="text-align: center; font-weight: 700; color: #00E676; display: none;">+${(t.xg - t.xga).toFixed(1)}</td>
        `;
        tbody.appendChild(tr);
    });
}

// 4. Renderizar Cartelera Dinámica con Checkboxes (Panel Derecho)
function renderizarCartelera(fixtures) {
    const list = document.querySelector(".fixtures-list");
    if (!list || !fixtures) return;
    list.innerHTML = "";
    selectedMatchIds = [];

    fixtures.forEach((f, idx) => {
        const card = document.createElement("div");
        card.className = "fixture-card";
        card.id = `fixture-card-${idx}`;
        card.style.cssText = "background: rgba(0,230,118,0.04); border: 1px solid #00E676; border-radius: 6px; padding: 10px; margin-bottom: 8px;";
        
        selectedMatchIds.push(f.id_partido); // Marcado por defecto

        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 7.5pt; color: #94A3B8;">📅 ${f.horario}</span>
                <label style="display: flex; align-items: center; gap: 4px; cursor: pointer;">
                    <input type="checkbox" checked value="${f.id_partido}" style="accent-color: #00E676; cursor: pointer;" onchange="toggleFixtureCheckbox(this, '${f.id_partido}')">
                    <span style="font-size: 7pt; font-weight: 700; color: #00E676;">✅ Seleccionado</span>
                </label>
            </div>
            <div style="font-size: 9.5pt; font-weight: 700; color: #ffffff; margin-bottom: 4px;">${f.local} vs ${f.visitante}</div>
            <div style="font-size: 7.5pt; color: #cbd5e1; display: flex; gap: 8px;">
                <span>L <strong style="color: #38BDF8;">${f.momios.L.toFixed(2)}</strong></span>
                <span>E <strong style="color: #fbbf24;">${f.momios.E.toFixed(2)}</strong></span>
                <span>V <strong style="color: #f87171;">${f.momios.V.toFixed(2)}</strong></span>
                ${f.momios.pago_anticipado ? '<span style="color: #00E676; font-weight: 700;">🏷️ PA Activo</span>' : ''}
            </div>
        `;
        list.appendChild(card);
    });

    actualizarContadorSeleccionados();
}

function toggleFixtureCheckbox(checkbox, matchId) {
    if (checkbox.checked) {
        if (!selectedMatchIds.includes(matchId)) selectedMatchIds.push(matchId);
    } else {
        selectedMatchIds = selectedMatchIds.filter(id => id !== matchId);
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
            <td style="color: var(--accent-amber); font-weight: 700;">${ord.estrategia_codigo || ord.estrategia || "QBE-D1"}</td>
            <td class="numeric">${ord.momio || "2.10"}</td>
            <td style="color: #00E676;">${ord.seguro || "Cubierto"}</td>
            <td class="numeric" style="font-weight: 700; color: var(--accent-gold);">$${ord.inversion || ord.stake || "50.00"}</td>
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
