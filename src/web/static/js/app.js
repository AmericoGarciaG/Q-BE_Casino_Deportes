document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadLiveBoard(1); // Liga MX por defecto
});

function initNavigation() {
    const tabs = document.querySelectorAll('.tab-btn');
    const views = document.querySelectorAll('.view-section');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            views.forEach(v => v.classList.remove('active'));

            tab.classList.add('active');
            const target = tab.getAttribute('data-tab');
            document.getElementById(target).classList.add('active');
        });
    });
}

async function loadLiveBoard(leagueId) {
    try {
        const res = await fetch(`/api/leagues/${leagueId}/live-board`);
        if (!res.ok) return;
        const data = await res.json();

        renderStandings(data.standings);
        renderFixtures(data.fixtures);
    } catch (err) {
        console.error("Error cargando live board:", err);
    }
}

function renderStandings(standings) {
    const tbody = document.getElementById('standings-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    standings.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="numeric">${row.rank}</td>
            <td><strong>${row.name}</strong></td>
            <td class="numeric">${row.played}</td>
            <td class="numeric">${row.win}</td>
            <td class="numeric">${row.draw}</td>
            <td class="numeric">${row.loss}</td>
            <td class="numeric">${row.goalsFor}:${row.goalsAgainst}</td>
            <td class="numeric" style="color: var(--accent-amber); font-weight: bold;">${row.pts}</td>
            <td class="numeric" style="color: var(--accent-green);">${row.xg}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderFixtures(fixtures) {
    const container = document.getElementById('fixtures-container');
    if (!container) return;
    container.innerHTML = '';

    fixtures.forEach(match => {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.marginBottom = '1rem';
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>${match.home}</strong> vs <strong>${match.away}</strong>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">${match.date} | ${match.time}</div>
                </div>
                <div style="display: flex; gap: 0.5rem;" class="numeric">
                    <span style="background: rgba(255,255,255,0.05); padding: 4px 8px; border-radius: 4px;">1: ${match.home_odd}</span>
                    <span style="background: rgba(255,255,255,0.05); padding: 4px 8px; border-radius: 4px;">X: ${match.draw_odd}</span>
                    <span style="background: rgba(255,255,255,0.05); padding: 4px 8px; border-radius: 4px;">2: ${match.away_odd}</span>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

async function generatePortfolio() {
    try {
        const bankrollInput = document.getElementById('bankroll-input');
        const bankroll = bankrollInput ? parseFloat(bankrollInput.value) : 10000;

        const res = await fetch('/api/portfolio/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({league_id: 1, bankroll: bankroll, matchday: 7})
        });

        if (!res.ok) return;
        const data = await res.json();
        
        renderPortfolioResults(data);
    } catch (err) {
        console.error("Error generando cartera:", err);
    }
}

function renderPortfolioResults(data) {
    const ordersBody = document.getElementById('portfolio-orders-body');
    if (!ordersBody) return;
    ordersBody.innerHTML = '';

    data.orders.forEach(ord => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${ord.home_team} vs ${ord.away_team}</td>
            <td><strong style="color: var(--accent-amber);">${ord.recommended_selection}</strong></td>
            <td class="numeric">${ord.odd}</td>
            <td class="numeric">${ord.breakeven_odd}</td>
            <td class="numeric" style="color: var(--accent-green);">+${(ord.ev * 100).toFixed(1)}%</td>
            <td class="numeric" style="font-weight: bold; color: var(--accent-gold);">$${ord.stake}</td>
        `;
        ordersBody.appendChild(tr);
    });

    if (data.portfolio_id) {
        const exportBtn = document.getElementById('export-pdf-btn');
        if (exportBtn) {
            exportBtn.onclick = () => window.open(`/api/portfolio/${data.portfolio_id}/pdf`, '_blank');
        }
    }
}
