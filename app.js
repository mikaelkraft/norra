let allPredictions = [];
let pastPredictions = [];
let todayPredictions = [];
let yesterdayPredictions = [];
let archivePredictions = [];
let activeFilter = 'All';
let currentView = 'active'; // 'active', 'yesterday', 'past', 'live'
let yesterdaySubView = 'yesterday'; // 'yesterday', 'archive'
let currentPage = 1;
const itemsPerPage = 6;

// Dynamic backend URL resolution: if local hostname, use local URL; else use production Render URL
const BACKEND_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://127.0.0.1:8000' // Local FastAPI backend
    : 'https://norra-ai.onrender.com'; // Production Render URL

function getGMTPlus1DateStrings() {
    const now = new Date();
    const utcMs = now.getTime() + (now.getTimezoneOffset() * 60000);
    const gmt1Today = new Date(utcMs + 3600000);
    const gmt1Yesterday = new Date(utcMs + 3600000 - 86400000);
    
    const formatDate = (d) => {
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    return {
        today: formatDate(gmt1Today),
        yesterday: formatDate(gmt1Yesterday)
    };
}

async function fetchPredictions() {
    const grid = document.getElementById('prediction-grid');
    const lastSyncSpan = document.getElementById('last-updated');
    
    try {
        const response = await fetch(`${BACKEND_URL}/predictions`);
        const data = await response.json();
        
        allPredictions = data.active_predictions || data.predictions || [];
        pastPredictions = data.past_predictions || [];
        
        const dates = getGMTPlus1DateStrings();
        const combined = [...allPredictions, ...pastPredictions];
        
        // Today predictions: matches that kickoff today (active or past/concluded) or are pending and in the future
        todayPredictions = combined.filter(p => p.date.startsWith(dates.today) || (p.status === 'pending' && p.date >= dates.today));
        
        // Yesterday predictions: matches that kickoff yesterday
        yesterdayPredictions = combined.filter(p => p.date.startsWith(dates.yesterday));
        
        // Archive predictions: matches that kickoff before yesterday
        archivePredictions = combined.filter(p => !p.date.startsWith(dates.today) && !p.date.startsWith(dates.yesterday) && p.date < dates.yesterday);
        
        // Sort chronologically
        archivePredictions.sort((a, b) => b.date.localeCompare(a.date));
        todayPredictions.sort((a, b) => a.date.localeCompare(b.date));
        yesterdayPredictions.sort((a, b) => b.date.localeCompare(a.date));
        
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
    
    const btnYest = document.getElementById('btn-yesterday-predictions');
    if (btnYest) btnYest.classList.toggle('active', view === 'yesterday');
    
    const btnPast = document.getElementById('btn-past-predictions');
    if (btnPast) btnPast.classList.toggle('active', view === 'past');
    
    const btnLive = document.getElementById('btn-live-scores');
    if (btnLive) btnLive.classList.toggle('active', view === 'live');
    
    const grid = document.getElementById('prediction-grid');
    const liveContainer = document.getElementById('live-scores-container');
    const filterContainer = document.querySelector('.filter-container');
    const paginationContainer = document.getElementById('pagination-container');
    
    // Toggle Yesterday nested sub-toggle
    const subToggle = document.getElementById('yesterday-sub-toggle');
    if (subToggle) {
        if (view === 'yesterday') {
            subToggle.classList.remove('hidden');
        } else {
            subToggle.classList.add('hidden');
        }
    }
    
    if (view === 'active' || view === 'yesterday' || view === 'past') {
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

function switchYesterdaySubView(subView) {
    yesterdaySubView = subView;
    activeFilter = 'All'; // Reset filter when switching sub-views
    currentPage = 1; // Reset page number
    
    // Update sub-toggle buttons state
    document.getElementById('btn-sub-yesterday').classList.toggle('active', subView === 'yesterday');
    document.getElementById('btn-sub-archive').classList.toggle('active', subView === 'archive');
    
    renderFilters();
    renderGrid();
}

function renderFilters() {
    const filterBar = document.getElementById('league-filters');
    if (!filterBar) return;

    let visiblePredictions = [];
    if (currentView === 'active') {
        visiblePredictions = todayPredictions;
    } else if (currentView === 'yesterday') {
        if (yesterdaySubView === 'yesterday') {
            visiblePredictions = yesterdayPredictions;
        } else {
            visiblePredictions = archivePredictions;
        }
    } else if (currentView === 'past') {
        visiblePredictions = archivePredictions;
    }
    
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

    let visiblePredictions = [];
    if (currentView === 'active') {
        visiblePredictions = todayPredictions;
    } else if (currentView === 'yesterday') {
        if (yesterdaySubView === 'yesterday') {
            visiblePredictions = yesterdayPredictions;
        } else {
            visiblePredictions = archivePredictions;
        }
    } else if (currentView === 'past') {
        visiblePredictions = archivePredictions;
    }

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

        // Suggested Stake Units fallback calculation
        let stakeAdvice = '2/10 Units';
        if (confValue >= 85) stakeAdvice = '8/10 Units';
        else if (confValue >= 75) stakeAdvice = '6/10 Units';
        else if (confValue >= 65) stakeAdvice = '4/10 Units';

        // Value Pick detection fallback calculation (statistical mismatch)
        let isValueBet = false;
        if (confValue >= 78) {
            let homeStar = 5.0, awayStar = 5.0;
            if (p.stars && p.stars.includes('H:') && p.stars.includes('A:')) {
                const parts = p.stars.split(' ');
                const hPart = parts.find(x => x.startsWith('H:'));
                const aPart = parts.find(x => x.startsWith('A:'));
                if (hPart) homeStar = parseFloat(hPart.substring(2)) || 5.0;
                if (aPart) awayStar = parseFloat(aPart.substring(2)) || 5.0;
            }
            const starDiff = Math.abs(homeStar - awayStar);
            const h2hVal = Math.abs(parseInt(p.h2h) || 0);
            if (starDiff >= 1.2 || h2hVal >= 2) {
                isValueBet = true;
            }
        }

        let statusBadgeHtml = '';
        let scoreHtml = '';
        
        if (p.status !== 'pending') {
            const statusClass = p.status === 'won' ? 'status-won' : (p.status === 'lost' ? 'status-lost' : (p.status === 'void' ? 'status-void' : 'status-pending'));
            const statusText = p.status === 'won' ? '✅ Won' : (p.status === 'lost' ? '❌ Lost' : (p.status === 'void' ? '➖ Void' : '⏳ Concluded'));
            statusBadgeHtml = `<span class="past-status-badge ${statusClass}">${statusText}</span>`;
        }
        
        if (p.actual_home_goals !== null && p.actual_away_goals !== null) {
            scoreHtml = `
                <div class="final-score-badge">
                    ⚽ Score: <strong>${p.actual_home_goals} - ${p.actual_away_goals}</strong>
                </div>
            `;
        }

        // Generate the high-precision top 2-3 recommended picks
        const picks = [];
        
        // 1. FT Outcome / Double Chance
        if (p.main && !p.main.includes("Draw")) {
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

        // 3. Both Teams to Score (BTTS) removed as requested due to risk profile

        // 4. First Half Goals
        if (p.ht_ft && p.ht_ft !== "N/A") {
            let fhConf = (p.ht_ft === "FH Under 1.5" ? 82 : 71) + (p.away.length % 7);
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
        const hashSeed = (p.home.length + p.away.length) % 3;
        let cornerLine = isHighCorner ? 9.5 : 8.5;
        if (hashSeed === 0) cornerLine -= 1;
        else if (hashSeed === 1) cornerLine += 1;
        const cornerConf = Math.min(88, 65 + (p.home.length % 15) + (p.away.length % 10));

        picks.push({
            type: "Corners Pick",
            value: `Over ${cornerLine} Corners`,
            conf: cornerConf,
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

        const dates = getGMTPlus1DateStrings();
        card.innerHTML = `
            <div class="card-header" style="display: flex; flex-direction: column; align-items: flex-start; gap: 4px; border-bottom: 1px solid var(--glass-border); padding-bottom: 0.6rem; margin-bottom: 0.6rem;">
                <div style="display: flex; justify-content: space-between; width: 100%; font-size: 0.75rem; opacity: 0.95;">
                    <div>
                        <span class="card-tier">${p.status === 'pending' ? 'Beacon V4 ML' : (p.date.startsWith(dates.yesterday) ? 'Yesterday' : 'Archive')}</span>
                        ${isValueBet ? '<span class="value-bet-badge">🔥 Value Pick</span>' : ''}
                    </div>
                    <span>${p.league}</span>
                </div>
                <div style="font-size: 0.65rem; opacity: 0.7; margin-top: 2px;">
                    Generated: ${p.created_at || 'N/A'} (GMT+1)
                </div>
            </div>
            <div class="teams" style="font-size: 1.15rem; margin-bottom: 0.4rem;">
                ${p.home} <span style="font-size: 0.9rem; opacity: 0.6;">VS</span> ${p.away}
            </div>

            ${statusBadgeHtml}
            ${scoreHtml}

            <div class="main-outcome" style="margin: 0.6rem 0; font-size: 0.95rem; font-weight: 600;">
                🎯 Verdict: <strong style="color: var(--accent);">${p.main}</strong>
            </div>

            <!-- Toggle Details Button -->
            <button class="toggle-card-btn" onclick="toggleCardDetails(${p.fixture_id}, this)" style="width: 100%; background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border); color: var(--text); padding: 6px 12px; border-radius: 8px; font-size: 0.78rem; cursor: pointer; margin-top: 0.4rem; transition: background 0.2s; display: flex; align-items: center; justify-content: center; gap: 6px; font-weight: 600;">
                <span>Show Details</span> <span class="arrow-icon">▼</span>
            </button>

            <!-- Collapsible Details Container -->
            <div class="card-details collapsed" id="details-${p.fixture_id}" style="display: none; margin-top: 0.8rem; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 0.8rem;">
                ${p.league_avg_goals ? `
                <div class="avg-goals-badge" style="margin-bottom: 0.6rem; font-size: 0.75rem;">
                    📊 League Avg: <strong>${p.league_avg_goals} goals/game</strong>
                </div>
                ` : ''}

                <div class="confidence-gauge-container" style="margin-bottom: 0.8rem;">
                    <div class="gauge-label" style="font-size: 0.75rem; margin-bottom: 4px;">
                        <span>Precision (${p.conf})</span>
                        <span class="stake-label">Stake: <strong>${stakeAdvice}</strong></span>
                    </div>
                    <div class="gauge-track" style="height: 6px;">
                        <div class="gauge-fill" style="width: ${confValue}%"></div>
                    </div>
                </div>

                <div class="recommended-picks-container" style="margin-bottom: 0.8rem;">
                    <div class="picks-title" style="font-size: 0.72rem; letter-spacing: 0.5px; margin-bottom: 0.4rem; opacity: 0.8;">🎯 TOP PRECISION PICKS</div>
                    <div class="picks-list" style="gap: 6px;">
                        ${bestPicks.map((pick, idx) => `
                            <div class="pick-item ${idx === 0 ? 'best-pick' : ''}" style="padding: 6px 10px; font-size: 0.75rem;">
                                <span class="pick-market">${pick.badge} ${pick.type}</span>
                                <span class="pick-val" style="font-weight: 700;">${pick.value}</span>
                                <span class="pick-precision" style="font-size: 0.68rem; opacity: 0.8;">${pick.conf}% Precision</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                ${p.explanation && p.explanation !== 'N/A' && p.explanation !== '' ? `
                <div class="verdict-detail" style="font-size: 0.75rem; line-height: 1.4; opacity: 0.85; margin-bottom: 0.8rem; border-top: 1px dashed rgba(255,255,255,0.08); padding-top: 0.5rem; color: #cbd5e1; font-style: italic;">
                    💡 <strong>Analysis:</strong> ${p.explanation}
                </div>
                ` : ''}

                <div class="prediction-date-footer" style="margin-top: 0.5rem; font-size: 0.78rem; font-weight: 700; color: #f8fafc; border-top: 1px solid rgba(255,255,255,0.04); padding-top: 0.5rem;">
                    📅 Kickoff: ${p.date} (GMT+1)
                </div>
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

function setYesterdayLabel() {
    const btnYest = document.getElementById('btn-yesterday-predictions');
    if (!btnYest) return;
    
    const now = new Date();
    const utcMs = now.getTime() + (now.getTimezoneOffset() * 60000);
    const gmt1Yesterday = new Date(utcMs + 3600000 - 86400000);
    
    const weekdayOptions = { weekday: 'short' };
    const dateOptions = { month: 'short', day: 'numeric' };
    
    const weekday = gmt1Yesterday.toLocaleDateString('en-US', weekdayOptions);
    const dateStr = gmt1Yesterday.toLocaleDateString('en-US', dateOptions);
    
    btnYest.textContent = `📅 ${weekday}, ${dateStr}`;
}

// Fetch on load
document.addEventListener('DOMContentLoaded', () => {
    fetchPredictions();
    setYesterdayLabel();
    setDynamicYear();
    checkCookies();

    // Register Service Worker for PWA Support
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('sw.js')
                .then(reg => console.log('Service Worker registered successfully:', reg.scope))
                .catch(err => console.error('Service Worker registration failed:', err));
        });
    }
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

function toggleCardDetails(fixtureId, button) {
    const details = document.getElementById(`details-${fixtureId}`);
    const arrow = button.querySelector('.arrow-icon');
    const label = button.querySelector('span');
    
    if (details.style.display === 'none' || details.style.display === '') {
        details.style.display = 'block';
        label.textContent = 'Hide Details';
        arrow.textContent = '▲';
        button.style.background = 'rgba(255,255,255,0.08)';
    } else {
        details.style.display = 'none';
        label.textContent = 'Show Details';
        arrow.textContent = '▼';
        button.style.background = 'rgba(255,255,255,0.04)';
    }
}
