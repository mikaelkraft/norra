let allPredictions = [];
let activeFilter = 'All';

// Dynamic backend URL resolution: if on GitHub Pages, use Render API URL; else use relative URL
const BACKEND_URL = window.location.hostname.includes('github.io')
    ? 'https://norra-ai.onrender.com' // ctual Render URL in production
    : ''; // Relative URL for local development or self-hosted deployment

async function fetchPredictions() {
    const grid = document.getElementById('prediction-grid');
    const lastSyncSpan = document.getElementById('last-updated');
    
    try {
        const response = await fetch(`${BACKEND_URL}/predictions`);
        const data = await response.json();
        
        allPredictions = data.predictions || [];
        if (lastSyncSpan) lastSyncSpan.textContent = data.last_updated || 'Unknown';

        renderFilters();
        renderGrid();

    } catch (err) {
        console.error('Beacon fetch error:', err);
        grid.innerHTML = '<div class="loading">Failed to sync with Beacon backend.</div>';
    }
}

function renderFilters() {
    const filterBar = document.getElementById('league-filters');
    if (!filterBar) return;

    const leagues = ['All', ...new Set(allPredictions.map(p => p.league))];
    filterBar.innerHTML = '';
    
    leagues.forEach(league => {
        const btn = document.createElement('button');
        btn.className = `filter-btn ${activeFilter === league ? 'active' : ''}`;
        btn.textContent = league;
        btn.onclick = () => {
            activeFilter = league;
            renderFilters();
            renderGrid();
        };
        filterBar.appendChild(btn);
    });
}

function renderGrid() {
    const grid = document.getElementById('prediction-grid');
    grid.innerHTML = '';

    const filtered = activeFilter === 'All' 
        ? allPredictions 
        : allPredictions.filter(p => p.league === activeFilter);

    if (filtered.length === 0) {
        grid.innerHTML = '<div class="loading">No active beacons for this sector.</div>';
        return;
    }

    filtered.forEach((p, index) => {
        const card = document.createElement('div');
        card.className = 'prediction-card';
        card.style.animationDelay = `${index * 0.1}s`;
        
        const confValue = parseInt(p.conf) || 50;

        card.innerHTML = `
            <div class="card-header">
                <span class="card-tier">Beacon V4 ML</span>
                <span>${p.league}</span>
            </div>
            <div class="teams">
                ${p.home} <span>VS</span> ${p.away}
            </div>

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

            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-label">Double Chance</span>
                    <span class="stat-value">${p.dc || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">BTTS (GG/NG)</span>
                    <span class="stat-value">${p.btts || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Draw No Bet</span>
                    <span class="stat-value">${p.dnb || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Multi-Goals</span>
                    <span class="stat-value">${p.multi_goals || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">HT/FT Market</span>
                    <span class="stat-value">${p.ht_ft || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Goal Forecast</span>
                    <span class="stat-value">${p.ou_refined || 'N/A'}</span>
                </div>
            </div>
            
            <div class="combo-bet-container">
                <span class="stat-label">⚡ Combo Value Pick</span>
                <div class="combo-badge">${p.combos || 'N/A'}</div>
            </div>

            <div class="main-outcome">
                🎯 FT Outcome: ${p.main}
            </div>
        `;
        grid.appendChild(card);
    });
}

async function fetchTimeline() {
    const timelineContainer = document.getElementById('timeline-container');
    if (!timelineContainer) return;
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/timeline`);
        const data = await response.json();
        
        if (data.length === 0) {
            timelineContainer.innerHTML = '<div class="loading">No broadcast signals captured in this sector yet.</div>';
            return;
        }
        
        timelineContainer.innerHTML = '';
        
        data.forEach(post => {
            const card = document.createElement('div');
            card.className = 'timeline-card';
            
            // Random-ish initial likes to simulate active user reactions
            const agreeCount = Math.floor(Math.random() * 24) + 12;
            const valueCount = Math.floor(Math.random() * 15) + 6;
            
            card.innerHTML = `
                <div class="timeline-header">
                    <span class="platform-badge platform-${post.platform.toLowerCase()}">
                        ${post.platform === 'X' ? '🐦 X (Twitter)' : '📢 Telegram'}
                    </span>
                    <span class="timeline-date">${post.date}</span>
                </div>
                <div class="timeline-body">${post.content.replace(/\n/g, '<br>')}</div>
                ${post.link ? `<a href="${post.link}" target="_blank" class="timeline-link">View Original Post &rarr;</a>` : ''}
                <div class="reaction-bar">
                    <button class="reaction-btn" onclick="reactToPost(this)">
                        🔥 Agree <span class="react-count">${agreeCount}</span>
                    </button>
                    <button class="reaction-btn" onclick="reactToPost(this)">
                        📈 Value Pick <span class="react-count">${valueCount}</span>
                    </button>
                </div>
            `;
            timelineContainer.appendChild(card);
        });
    } catch (err) {
        console.error('Timeline fetch error:', err);
        timelineContainer.innerHTML = '<div class="loading">Failed to load timeline feed.</div>';
    }
}

function reactToPost(btn) {
    const countSpan = btn.querySelector('.react-count');
    if (!btn.classList.contains('reacted')) {
        btn.classList.add('reacted');
        countSpan.textContent = parseInt(countSpan.textContent) + 1;
        btn.style.borderColor = 'var(--accent)';
    } else {
        btn.classList.remove('reacted');
        countSpan.textContent = parseInt(countSpan.textContent) - 1;
        btn.style.borderColor = 'var(--glass-border)';
    }
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
    fetchTimeline();
    setDynamicYear();
    checkCookies();
});

// Refresh every 5 minutes
setInterval(() => {
    fetchPredictions();
    fetchTimeline();
}, 300000);
