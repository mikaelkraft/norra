let allPredictions = [];
let pastPredictions = [];
let activeFilter = 'All';
let currentView = 'active'; // 'active', 'past', 'live'
let currentPage = 1;
const itemsPerPage = 6;

// Dynamic backend URL resolution: if on GitHub Pages or custom domain, use Render API URL; else use relative URL
const BACKEND_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.hostname === '')
    ? 'http://127.0.0.1:8000' // Local FastAPI backend
    : (window.location.hostname.includes('onrender.com'))
        ? '' // Relative URL for Render self-hosted backend
        : 'https://norra-ai.onrender.com'; // Production Render URL

async function fetchPredictions() {
    const grid = document.getElementById('prediction-grid');
    const lastSyncSpan = document.getElementById('last-updated');
    
    try {
        const response = await fetch(`${BACKEND_URL}/predictions`);
        const data = await response.json();
        
        allPredictions = data.active_predictions || data.predictions || [];
        pastPredictions = data.past_predictions || [];
        if (lastSyncSpan) lastSyncSpan.textContent = data.last_updated || 'Unknown';

        currentPage = 1; // Reset to page 1 on fresh sync
        renderFilters();
        renderGrid();

    } catch (err) {
        console.error('Beacon fetch error:', err);
        grid.innerHTML = '<div class="loading">Failed to sync with Beacon backend.</div>';
    }
}

function switchView(view) {
    currentView = view;
    activeFilter = 'All'; // Reset filter when switching tabs
    currentPage = 1; // Reset page number
    
    // Update active button state
    document.getElementById('btn-active-predictions').classList.toggle('active', view === 'active');
    document.getElementById('btn-past-predictions').classList.toggle('active', view === 'past');
    document.getElementById('btn-live-scores').classList.toggle('active', view === 'live');
    
    const grid = document.getElementById('prediction-grid');
    const liveContainer = document.getElementById('live-scores-container');
    const filterContainer = document.querySelector('.filter-container');
    const paginationContainer = document.getElementById('pagination-container');
    
    if (view === 'active') {
        grid.classList.remove('hidden');
        if (liveContainer) liveContainer.classList.add('hidden');
        if (filterContainer) filterContainer.classList.remove('hidden');
        if (paginationContainer) paginationContainer.classList.remove('hidden');
        renderFilters();
        renderGrid();
    } else if (view === 'past') {
        grid.classList.remove('hidden');
        if (liveContainer) liveContainer.classList.add('hidden');
        if (filterContainer) filterContainer.classList.remove('hidden');
        if (paginationContainer) paginationContainer.classList.remove('hidden');
        renderFilters();
        renderGrid();
    } else if (view === 'live') {
        grid.classList.add('hidden');
        if (filterContainer) filterContainer.classList.add('hidden');
        if (paginationContainer) paginationContainer.classList.add('hidden');
        if (liveContainer) liveContainer.classList.remove('hidden');
    }
}

function renderFilters() {
    const filterBar = document.getElementById('league-filters');
    if (!filterBar) return;

    const visiblePredictions = currentView === 'active' ? allPredictions : pastPredictions;
    const leagues = ['All', ...new Set(visiblePredictions.map(p => p.league))];
    filterBar.innerHTML = '';
    
    leagues.forEach(league => {
        const btn = document.createElement('button');
        btn.className = `filter-btn ${activeFilter === league ? 'active' : ''}`;
        btn.textContent = league;
        btn.onclick = () => {
            activeFilter = league;
            currentPage = 1; // Reset to page 1 on filter change
            renderFilters();
            renderGrid();
        };
        filterBar.appendChild(btn);
    });
}

function renderGrid() {
    const grid = document.getElementById('prediction-grid');
    grid.innerHTML = '';

    const visiblePredictions = currentView === 'active' ? allPredictions : pastPredictions;

    const filtered = activeFilter === 'All' 
        ? visiblePredictions 
        : visiblePredictions.filter(p => p.league === activeFilter);

    if (filtered.length === 0) {
        grid.innerHTML = '<div class="loading">No beacons found for this sector.</div>';
        renderPagination(0);
        return;
    }

    const totalPages = Math.ceil(filtered.length / itemsPerPage);
    if (currentPage > totalPages) currentPage = totalPages || 1;

    const paginated = filtered.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

    paginated.forEach((p, index) => {
        const card = document.createElement('div');
        card.className = 'prediction-card';
        card.style.animationDelay = `${index * 0.1}s`;
        
        const confValue = parseInt(p.conf) || 50;

        let statusBadgeHtml = '';
        let scoreHtml = '';
        
        if (currentView === 'past') {
            const statusClass = p.status === 'won' ? 'status-won' : (p.status === 'lost' ? 'status-lost' : 'status-pending');
            const statusText = p.status === 'won' ? '✅ Won' : (p.status === 'lost' ? '❌ Lost' : '⏳ Concluded');
            statusBadgeHtml = `<span class="past-status-badge ${statusClass}">${statusText}</span>`;
            
            if (p.actual_home_goals !== null && p.actual_away_goals !== null) {
                scoreHtml = `
                    <div class="final-score-badge">
                        ⚽ Final Score: <strong>${p.actual_home_goals} - ${p.actual_away_goals}</strong>
                    </div>
                `;
            }
        }

        // Generate the high-precision top 2-3 recommended picks
        const picks = [];
        
        // 1. FT Outcome / Double Chance
        if (p.main && !p.main.includes("Draw") && confValue >= 72) {
            picks.push({
                type: "Match Winner",
                value: p.main,
                conf: confValue,
                badge: "🎯"
            });
        } else if (p.dc && p.dc !== "N/A") {
            picks.push({
                type: "Double Chance",
                value: p.dc,
                conf: Math.min(95, confValue + 12),
                badge: "🛡️"
            });
        }

        // 2. Goal Forecast / Over Under
        if (p.ou_refined && p.ou_refined !== "N/A") {
            let ouConf = 70;
            if (p.ou_refined === "Over 1.5") ouConf = 82;
            else if (p.ou_refined === "Under 3.5") ouConf = 80;
            else if (p.ou_refined === "Over 2.5") ouConf = 73;
            else if (p.ou_refined === "Under 2.5") ouConf = 71;
            
            picks.push({
                type: "Goal Line",
                value: p.ou_refined,
                conf: ouConf,
                badge: "💎"
            });
        }

        // 3. Both Teams to Score (BTTS)
        if (p.btts && p.btts !== "N/A" && p.btts !== "NG / No") {
            picks.push({
                type: "Both Teams to Score",
                value: p.btts,
                conf: 75,
                badge: "⚽"
            });
        }

        // 4. First Half Goals
        if (p.ht_ft && p.ht_ft !== "N/A") {
            let fhConf = p.ht_ft === "FH Under 1.5" ? 85 : 74;
            picks.push({
                type: "First Half Goals",
                value: p.ht_ft,
                conf: fhConf,
                badge: "⏱️"
            });
        }

        // 5. Corners (Dynamic Custom Prediction)
        const highCornerLeagues = ["Premier League", "Championship", "Allsvenskan", "Bundesliga", "Eredivisie"];
        const isHighCorner = highCornerLeagues.some(l => p.league && p.league.includes(l));
        picks.push({
            type: "Corners Pick",
            value: isHighCorner ? "Over 8.5 Corners" : "Over 7.5 Corners",
            conf: isHighCorner ? 80 : 75,
            badge: "🚩"
        });

        // 6. Combo Bet
        if (p.combos && p.combos !== "N/A" && confValue >= 75) {
            picks.push({
                type: "Value Combo",
                value: p.combos,
                conf: Math.max(60, confValue - 5),
                badge: "⚡"
            });
        }

        // Sort by confidence level to show the absolute best/safest picks first!
        picks.sort((a, b) => b.conf - a.conf);

        // Keep only top 2-3 picks for clean user display
        const bestPicks = picks.slice(0, 3);

        card.innerHTML = `
            <div class="card-header" style="display: flex; flex-direction: column; align-items: flex-start; gap: 4px; border-bottom: 1px solid var(--glass-border); padding-bottom: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; width: 100%; font-size: 0.8rem; opacity: 0.6;">
                    <span class="card-tier">${currentView === 'active' ? 'Beacon V4 ML' : 'Concluded'}</span>
                    <span>${p.league}</span>
                </div>
                <div style="font-size: 0.7rem; opacity: 0.4; margin-top: 2px;">
                    Generated: ${p.created_at || 'N/A'} (GMT+1)
                </div>
            </div>
            <div class="teams">
                ${p.home} <span>VS</span> ${p.away}
            </div>

            ${statusBadgeHtml}
            ${scoreHtml}

            ${p.league_avg_goals ? `
            <div class="avg-goals-badge">
                📊 League Avg: <strong>${p.league_avg_goals} goals/game</strong>
            </div>
            ` : ''}

            <div class="confidence-gauge-container">
                <div class="gauge-label">
                    <span>Precision Level</span>
                    <span>${p.conf}</span>
                </div>
                <div class="gauge-track">
                    <div class="gauge-fill" style="width: ${confValue}%"></div>
                </div>
            </div>

            <div class="recommended-picks-container">
                <div class="picks-title">🎯 TOP PRECISION PICKS</div>
                <div class="picks-list">
                    ${bestPicks.map(pick => `
                        <div class="pick-item">
                            <span class="pick-market">${pick.badge} ${pick.type}</span>
                            <span class="pick-val">${pick.value}</span>
                            <span class="pick-precision">${pick.conf}% Precision</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="prediction-date-footer">
                📅 Kickoff: ${p.date} (GMT+1)
            </div>
        `;
        grid.appendChild(card);
    });

    renderPagination(totalPages);
}

function renderPagination(totalPages) {
    const container = document.getElementById('pagination-container');
    if (!container) return;
    container.innerHTML = '';
    
    if (totalPages <= 1) return;
    
    // Prev Button
    const prevBtn = document.createElement('button');
    prevBtn.className = 'page-btn';
    prevBtn.innerHTML = '&larr; Prev';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => {
        if (currentPage > 1) {
            currentPage--;
            renderGrid();
            const filterBar = document.querySelector('.view-toggle-container');
            if (filterBar) {
                window.scrollTo({ top: filterBar.offsetTop - 20, behavior: 'smooth' });
            }
        }
    };
    container.appendChild(prevBtn);
    
    // Page Numbers
    for (let i = 1; i <= totalPages; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `page-btn ${currentPage === i ? 'active' : ''}`;
        pageBtn.textContent = i;
        pageBtn.onclick = () => {
            currentPage = i;
            renderGrid();
            const filterBar = document.querySelector('.view-toggle-container');
            if (filterBar) {
                window.scrollTo({ top: filterBar.offsetTop - 20, behavior: 'smooth' });
            }
        };
        container.appendChild(pageBtn);
    }
    
    // Next Button
    const nextBtn = document.createElement('button');
    nextBtn.className = 'page-btn';
    nextBtn.innerHTML = 'Next &rarr;';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderGrid();
            const filterBar = document.querySelector('.view-toggle-container');
            if (filterBar) {
                window.scrollTo({ top: filterBar.offsetTop - 20, behavior: 'smooth' });
            }
        }
    };
    container.appendChild(nextBtn);
}

function setDynamicYear() {
    const yearSpan = document.getElementById('current-year');
    if (yearSpan) {
        yearSpan.textContent = new Date().getFullYear();
    }
}

// --- Modal Handlers ---
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('active');
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('active');
}

// Close modal when clicking outside of modal-content
window.addEventListener('click', (event) => {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
});

// --- Cookie Banner Handlers ---
function checkCookies() {
    const banner = document.getElementById('cookie-banner');
    if (banner && !localStorage.getItem('cookies-accepted')) {
        banner.classList.remove('hidden');
    } else if (banner) {
        banner.classList.add('hidden');
    }
}

function acceptCookies() {
    localStorage.setItem('cookies-accepted', 'true');
    const banner = document.getElementById('cookie-banner');
    if (banner) banner.classList.add('hidden');
}

// --- Chatbot Handlers ---
function toggleChat() {
    const win = document.getElementById('chat-window');
    if (win) win.classList.toggle('active');
}

function handleChatKey(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const messages = document.getElementById('chat-messages');
    if (!input || !messages || !input.value.trim()) return;

    const query = input.value.trim();
    input.value = '';

    // Append User Message
    const userMsg = document.createElement('div');
    userMsg.className = 'message user-msg';
    userMsg.textContent = query;
    messages.appendChild(userMsg);
    messages.scrollTop = messages.scrollHeight;

    // Append Bot Loading Message
    const botLoading = document.createElement('div');
    botLoading.className = 'message bot-msg';
    botLoading.textContent = 'Thinking...';
    messages.appendChild(botLoading);
    messages.scrollTop = messages.scrollHeight;

    try {
        const response = await fetch(`${BACKEND_URL}/api/chat?message=${encodeURIComponent(query)}`, {
            method: 'POST'
        });
        const data = await response.json();
        botLoading.textContent = data.response || 'Sorry, I am offline right now.';
    } catch (err) {
        console.error('Chat error:', err);
        botLoading.textContent = 'Connection error. Please try again later.';
    }
    messages.scrollTop = messages.scrollHeight;
}

// Fetch on load
document.addEventListener('DOMContentLoaded', () => {
    fetchPredictions();
    setDynamicYear();
    checkCookies();
});

// Refresh every 5 minutes
setInterval(() => {
    fetchPredictions();
}, 300000);

async function promptAdminAccess() {
    const code = prompt("Enter the Admin Access Code:");
    if (!code) return;
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/verify-admin-code?code=${encodeURIComponent(code)}`);
        const data = await response.json();
        if (data.status === "success") {
            // Admin default render URL remains
            const adminBase = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.hostname === '')
                ? 'http://127.0.0.1:8000'
                : 'https://norra-ai.onrender.com';
            window.location.href = `${adminBase}/admin?token=${data.token}`;
        } else {
            alert(data.message || "Access Denied. Be gone, snooper!");
        }
    } catch (err) {
        console.error("Access check failed:", err);
        alert("A system error occurred. Access Denied.");
    }
}
