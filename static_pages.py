"""
Norra AI - Static Pages Generator
Renders branded, theme-aware pages for How It Works, Terms of Service, and Privacy Policy.
Reuses the exact header, navbar, logo asset, fonts, and footer from the main application.
"""

def render_master_layout(
    title: str,
    canonical_path: str,
    meta_desc: str,
    active_nav: str,
    header_h1: str,
    header_p: str,
    body_content_html: str
) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="canonical" href="https://mynorra.xyz/{canonical_path}">
    <meta name="description" content="{meta_desc}">
    <link rel="icon" type="image/png" href="assets/norraai.png">
    <link rel="apple-touch-icon" href="assets/norraai.png">
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    
    <!-- Master Stylesheet -->
    <link rel="stylesheet" href="style.css?v=3.2.13">

    <!-- Instant Zero-Flash Theme Initialization -->
    <script>
        (function() {{
            try {{
                const saved = localStorage.getItem('norra_theme');
                if (saved === 'light') {{
                    document.documentElement.classList.add('light-theme');
                    document.body && document.body.classList.add('light-theme');
                }}
            }} catch(e) {{}}
        }})();
    </script>
</head>
<body>
    <div class="background-blob"></div>
    <div class="background-blob-2"></div>

    <!-- Official Norra AI Navigation Bar -->
    <nav>
        <div class="logo">
            <a href="/" title="Norra AI Home" style="display: inline-flex; align-items: center; text-decoration: none; gap: 10px;">
                <img src="assets/norraai.png" alt="Norra AI Logo" class="brand-logo">
                <span class="brand-name-desktop" style="font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 1.15rem; color: var(--text-bright);">Norra <span style="color: var(--accent);">AI</span></span>
            </a>
        </div>
        <div class="nav-actions">
            <a href="/" class="nav-icon-btn" title="Predictions Home" style="text-decoration: none;">
                📡 <span class="nav-btn-text">Predictions</span>
            </a>
            <a href="how-it-works.html" class="nav-icon-btn {'active' if active_nav == 'guide' else ''}" title="How It Works & Quantitative Guide" style="text-decoration: none;">
                📖 <span class="nav-btn-text">Guide</span>
            </a>
            <button onclick="toggleTheme()" class="nav-icon-btn" title="Toggle Light / Dark Theme">
                🌓 <span class="nav-btn-text">Theme</span>
            </button>
        </div>
    </nav>

    <!-- Master Header -->
    <header>
        <h1>{header_h1}</h1>
        <p>{header_p}</p>
    </header>

    <!-- Main Page Content -->
    <main class="guide-main-container">
        {body_content_html}
    </main>

    <!-- Decorative Theme-Aware Wavy SVG Divider -->
    <div class="footer-wave-container" aria-hidden="true">
        <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
            <path class="footer-wave-back" d="M0,0 C150,90 350,-40 500,45 C650,130 900,10 1200,50 L1200,120 L0,120 Z"></path>
            <path class="footer-wave-front" d="M0,40 C180,110 380,20 600,70 C820,120 1020,30 1200,65 L1200,120 L0,120 Z"></path>
        </svg>
    </div>

    <!-- Master Footer -->
    <footer>
        <div class="responsible-gambling-badges">
            <a href="https://www.begambleaware.org" target="_blank" rel="noopener noreferrer" title="BeGambleAware.org - Free confidential gambling help">
                <img src="assets/begambleaware.svg" alt="BeGambleAware.org" class="rg-badge" />
            </a>
            <a href="https://www.gamstop.co.uk" target="_blank" rel="noopener noreferrer" title="GamStop - Free Online Gambling Self-Exclusion">
                <img src="assets/gamstop-logo-white.webp" alt="GamStop" class="rg-badge" />
            </a>
            <a href="https://www.taketimetothink.co.uk" target="_blank" rel="noopener noreferrer" title="Take Time To Think - Stay in Control">
                <img src="assets/tttt-logo.svg" alt="Take Time To Think" class="rg-badge" />
            </a>
        </div>
        <p class="gamble-warning">
            <img src="assets/18-plus.svg" alt="18+" class="rg-inline-18" /> Play Responsibly
        </p>
        <div class="footer-links-container">
            <div class="footer-links-group">
                <div class="footer-links-row">
                    <a href="how-it-works.html" class="footer-nav-link">
                        <span class="footer-moonwalk-slant" aria-hidden="true"></span>
                        <span>How It Works</span>
                    </a>
                    <a href="terms.html" class="footer-nav-link">
                        <span class="footer-moonwalk-slant" aria-hidden="true"></span>
                        <span>Terms of Service</span>
                    </a>
                </div>
                <div class="footer-secondary-link-row">
                    <a href="privacy.html" class="footer-nav-link">
                        <span class="footer-moonwalk-slant" aria-hidden="true"></span>
                        <span>Privacy Policy</span>
                    </a>
                </div>
            </div>
            <div class="footer-email-row">
                <a href="mailto:predict@mynorra.xyz" class="footer-email-chip" title="Contact Norra AI Support">
                    <svg class="footer-mail-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"></rect><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path></svg>
                    <span>predict@mynorra.xyz</span>
                </a>
            </div>
        </div>
        <p class="footer-copyright">&copy; <span id="current-year"></span> Norra AI. All rights mathematical.</p>
        <p style="margin-top: 10px; font-size: 0.75rem; opacity: 0.85;">
            Made with ❤ by <a href="https://github.com/mikaelkraft" target="_blank" rel="noopener" style="color: var(--accent); text-decoration: none; font-weight: 600;">Mikael Kraft</a>
        </p>
        <p style="margin-top: 6px; text-align: center;">
            <a href="/" class="footer-admin-link" title="Home" style="font-size: 0.85rem; text-decoration: none; opacity: 0.75;">⚡ Return to Live Predictions</a>
        </p>
    </footer>

    <!-- Theme & Year Controller -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const yr = document.getElementById('current-year');
            if (yr) yr.textContent = new Date().getFullYear();
            
            const saved = localStorage.getItem('norra_theme');
            if (saved === 'light') {{
                document.body.classList.add('light-theme');
            }}
        }});

        function toggleTheme() {{
            const isLight = document.body.classList.toggle('light-theme');
            document.documentElement.classList.toggle('light-theme', isLight);
            try {{
                localStorage.setItem('norra_theme', isLight ? 'light' : 'dark');
            }} catch (e) {{}}
        }}
    </script>
</body>
</html>"""


def get_how_it_works_html() -> str:
    body = """
    <!-- Section 1: Anatomy of a Match Card -->
    <div class="guide-section-card">
        <div class="guide-section-header">
            <span class="guide-section-icon">🎴</span>
            <h2 class="guide-section-title">Anatomy of a Norra AI Match Card</h2>
        </div>
        <p class="guide-section-desc">
            Every match forecast is rendered as an ultra-compact, high-density analytical card engineered for instant decision-making. Here is how each element delivers mathematical value:
        </p>

        <div class="guide-grid-2col">
            <div class="guide-feature-box">
                <div class="guide-feature-title">🏷️ Meta Bar (League &amp; Time)</div>
                <p class="guide-feature-desc">
                    Located at the very top. Displays the competition name, kickoff time standardized strictly to <strong>GMT+1 (West Africa Time)</strong>, and real-time match state (Scheduled, Live, or Concluded).
                </p>
            </div>
            <div class="guide-feature-box">
                <div class="guide-feature-title">⚡ Analytical Badges (EV+ / Steam)</div>
                <p class="guide-feature-desc">
                    High-contrast pill highlighting quantified edges: <strong>⚡ +EV Edge</strong> indicates mathematical advantage over bookmaker price, while <strong>📉 Steam</strong> flags sharp betting volume moving the market.
                </p>
            </div>
            <div class="guide-feature-box">
                <div class="guide-feature-title">🛡️ Golden Verdict Pill</div>
                <p class="guide-feature-desc">
                    The focal point of each card. Displays the primary algorithmically graded selection (e.g., <strong>1X</strong>, <strong>Ov1.5</strong>, <strong>1 DNB</strong>) along with fair de-vigged market odds. Tap to instantly add to your bet slip.
                </p>
            </div>
            <div class="guide-feature-box">
                <div class="guide-feature-title">📂 Expandable Details Drawer</div>
                <p class="guide-feature-desc">
                    Tap <strong>Details ▼</strong> to unveil secondary betting lines (Goals Line, BTTS, Shield/DNB, Combos), opening vs live line market movements, suggested Kelly stake %, and in-card odds format switcher.
                </p>
            </div>
        </div>
    </div>

    <!-- Section 2: The Quantitative Math -->
    <div class="guide-section-card">
        <div class="guide-section-header">
            <span class="guide-section-icon">🧮</span>
            <h2 class="guide-section-title">The Quantitative Math: How to Beat the Bookies</h2>
        </div>
        <p class="guide-section-desc">
            Bookmakers price markets to guarantee a profit margin (vigorish / overround). Naive bettors lose by trying to guess winners. Norra AI systematically beats the market using a 4-layer quantitative pipeline:
        </p>

        <div class="guide-grid-2col">
            <div class="guide-feature-box">
                <div class="guide-feature-title">1. Shin De-Vigging Method</div>
                <p class="guide-feature-desc">
                    Standard proportional normalization fails because bookmakers load extra margin on longshots. Norra AI solves Shin's implicit non-linear equation to isolate the proportion of informed sharp traders (<span class="math-var">z</span>) and uncover true zero-vig probabilities.
                </p>
            </div>
            <div class="guide-feature-box">
                <div class="guide-feature-title">2. Dixon-Coles Poisson Matrix</div>
                <p class="guide-feature-desc">
                    Computes expected goals (<span class="math-var">&lambda;</span><sub>home</sub>, <span class="math-var">&mu;</span><sub>away</sub>) with low-score correlation adjustments (<span class="math-var">&tau;</span>-factor) to generate full 9 &times; 9 scoreline matrices from which every market probability is mathematically derived.
                </p>
            </div>
            <div class="guide-feature-box">
                <div class="guide-feature-title">3. Verified Expected Value (+EV)</div>
                <div class="math-formula-box">
                    <span class="math-formula-expr"><strong>EV</strong> = (<strong>P</strong><sub>model</sub> &times; <strong>Decimal Odds</strong>) &minus; 1</span>
                </div>
                <p class="guide-feature-desc" style="margin-top: 6px;">
                    We only trigger recommendations when positive expected value exceeds verifiable transaction costs and market friction.
                </p>
            </div>
            <div class="guide-feature-box">
                <div class="guide-feature-title">4. Quarter-Kelly Bankroll Sizing</div>
                <p class="guide-feature-desc">
                    Full Kelly staking is mathematically optimal but emotionally volatile. We enforce conservative Quarter-Kelly (<span class="math-var">f</span><sup>*</sup> / 4, max 2.5% bankroll) to guarantee exponential growth while eliminating bankruptcy risk.
                </p>
            </div>
        </div>
    </div>

    <!-- Section 3: Betting Notation Key & Legend -->
    <div class="guide-section-card">
        <div class="guide-section-header">
            <span class="guide-section-icon">📖</span>
            <h2 class="guide-section-title">Betting Notation Key &amp; Market Legend</h2>
        </div>
        <p class="guide-section-desc">
            A quick reference guide to abbreviations and notations across the Norra AI platform:
        </p>

        <div class="guide-grid-2col">
            <div class="guide-feature-box">
                <div class="guide-feature-title">1 / X / 2</div>
                <p class="guide-feature-desc"><strong>1:</strong> Home Win | <strong>X:</strong> Draw | <strong>2:</strong> Away Win.</p>
            </div>
            <div class="guide-feature-box">
                <div class="guide-feature-title">1X / X2 / 12 (Double Chance)</div>
                <p class="guide-feature-desc"><strong>1X:</strong> Home Win or Draw | <strong>X2:</strong> Draw or Away Win | <strong>12:</strong> Either Team Wins (No Draw).</p>
            </div>
            <div class="guide-feature-box">
                <div class="guide-feature-title">DNB (Draw No Bet / Shield)</div>
                <p class="guide-feature-desc">If your team wins, the bet wins. If the match ends in a draw, your full stake is refunded.</p>
            </div>
            <div class="guide-feature-box">
                <div class="guide-feature-title">Ov1.5 / Ov2.5 / Un3.5 (Goals)</div>
                <p class="guide-feature-desc"><strong>Over 1.5:</strong> 2+ total goals | <strong>Over 2.5:</strong> 3+ total goals | <strong>Under 3.5:</strong> 3 or fewer total goals.</p>
            </div>
            <div class="guide-feature-box">
                <div class="guide-feature-title">BTTS (GG / NG)</div>
                <p class="guide-feature-desc"><strong>GG (Yes):</strong> Both teams score at least 1 goal | <strong>NG (No):</strong> At least one team keeps a clean sheet.</p>
            </div>
            <div class="guide-feature-box">
                <div class="guide-feature-title">⭐ Safe Pick / 🔥 Top Pick</div>
                <p class="guide-feature-desc"><strong>Safe Pick:</strong> Statistical certainty exceeding 80% | <strong>Top Pick:</strong> Model conviction exceeding 70%.</p>
            </div>
        </div>
    </div>

    <!-- Section 4: 4 Golden Strategic Rules -->
    <div class="guide-section-card">
        <div class="guide-section-header">
            <span class="guide-section-icon">🏆</span>
            <h2 class="guide-section-title">The Bettor's Strategic Playbook: 4 Golden Rules</h2>
        </div>
        <div class="legal-section-item">
            <h3>1. Prioritize Win Certainty &amp; Compounding</h3>
            <p>Avoid speculative 10-leg accumulators. True sports betting syndicates build wealth through steady 2-leg to 3-leg slips combining resilient Double Chance (1X/X2) and Over 1.5 Goals selections.</p>
        </div>
        <div class="legal-section-item">
            <h3>2. Strict Bankroll Discipline (Quarter-Kelly)</h3>
            <p>Never risk more than 1% to 2.5% of your total bankroll on any single ticket. When a loss occurs, do not chase. Sticking to mathematical sizing guarantees positive expectancy over hundreds of bets.</p>
        </div>
        <div class="legal-section-item">
            <h3>3. Exploit Draw-Shielded Lines</h3>
            <p>Draws occur in ~26-28% of all football matches worldwide. Straight 1X2 wins fail whenever a match finishes 1-1. Double Chance (1X/X2) and Draw No Bet transform draws into profitable wins or protected stakes.</p>
        </div>
        <div class="legal-section-item">
            <h3>4. Track Closing Line Value (CLV)</h3>
            <p>If you consistently bet lines that are higher than bookmakers' closing prices at kickoff, you have mathematically beaten the bookmaker's margin. In the long run, beating CLV guarantees positive return.</p>
        </div>
    </div>
    """
    return render_master_layout(
        title="How Norra AI Works & How to Play - Quantitative Football Intelligence",
        canonical_path="how-it-works.html",
        meta_desc="Complete guide to understanding Norra AI football predictions, reading match cards, using +EV badges, Quarter-Kelly bankroll sizing, and betting notations.",
        active_nav="guide",
        header_h1="How Norra AI <span>Works</span>",
        header_p="The Complete Playbook: Card Anatomy, Quantitative +EV Badges, Shin De-Vigging & Bankroll Sizing.",
        body_content_html=body
    )


def get_terms_html() -> str:
    body = """
    <div class="legal-article-card">
        <div class="guide-section-header">
            <span class="guide-section-icon">⚖️</span>
            <h2 class="guide-section-title">Terms of Service</h2>
        </div>
        <p class="guide-section-desc">Last Updated: October 2026. Please read these Terms of Service carefully before utilizing the Norra AI platform.</p>

        <div class="legal-section-item">
            <h3>1. Acceptance of Terms</h3>
            <p>By accessing or using Norra AI (available exclusively at <a href="https://mynorra.xyz" target="_blank" rel="noopener" style="color: var(--accent); font-weight: 700;">https://mynorra.xyz</a>, official Telegram channels, and progressive web applications), you acknowledge that you have read, understood, and agreed to be bound by these Terms of Service.</p>
        </div>

        <div class="legal-section-item">
            <h3>2. Mathematical Nature of Forecasts</h3>
            <p>Norra AI is an educational, analytical, and statistical modeling platform. All predictions, probabilities, expected value (+EV) indicators, and suggested stake allocations are mathematical estimations derived from machine learning ensembles, Dixon-Coles Poisson matrices, and historical sports data.</p>
            <p><strong>Past performance does not guarantee future results.</strong> Sports events are inherently subject to randomness, referee variance, injuries, and unexpected outcomes. Norra AI does not guarantee financial profit or bet success.</p>
        </div>

        <div class="legal-section-item">
            <h3>3. Non-Gambling Operator Status</h3>
            <p>Norra AI is <strong>not a bookmaker, sportsbook, or gambling operator</strong>. We do not accept bets, hold player deposits, process wagers, or broker gambling transactions. Any booking codes provided are for convenience with third-party licensed platforms where permitted by local law.</p>
        </div>

        <div class="legal-section-item">
            <h3>4. Responsible Gaming &amp; Age Restriction (18+)</h3>
            <p>You must be at least 18 years of age (or the legal age of majority in your jurisdiction) to use sports analysis and betting information. We strictly promote responsible bankroll management and advise users to bet only what they can afford to lose. If gambling is causing you distress, please contact <a href="https://www.begambleaware.org" target="_blank" rel="noopener" style="color: var(--accent); font-weight: 700;">BeGambleAware.org</a> or your local helpline.</p>
        </div>

        <div class="legal-section-item">
            <h3>5. Intellectual Property</h3>
            <p>All algorithms, predictive models, proprietary feature engineering pipelines, user interface code, brand assets, logos, and written guides are the intellectual property of Norra AI and Mikael Kraft. Unauthorized commercial replication, scraping, or redistribution is strictly prohibited.</p>
        </div>

        <div class="legal-section-item">
            <h3>6. Limitation of Liability</h3>
            <p>To the maximum extent permitted by applicable law, Norra AI, its developers, and affiliates shall not be liable for any direct, indirect, incidental, or consequential financial losses incurred by users placing wagers based on information provided on the platform.</p>
        </div>

        <div class="legal-section-item">
            <h3>7. Contact &amp; Support</h3>
            <p>For questions, support, or inquiries regarding the Norra AI platform, reach our team directly at <a href="mailto:predict@mynorra.xyz" style="color: var(--accent); font-weight: 700;">predict@mynorra.xyz</a>.</p>
        </div>
    </div>
    """
    return render_master_layout(
        title="Terms of Service - Norra AI Mathematical Intelligence",
        canonical_path="terms.html",
        meta_desc="Terms of service and legal agreement for utilizing the Norra AI mathematical prediction platform.",
        active_nav="terms",
        header_h1="Terms of <span>Service</span>",
        header_p="Mathematical Model Transparency, Computational Disclaimer & User Agreement.",
        body_content_html=body
    )


def get_privacy_html() -> str:
    body = """
    <div class="legal-article-card">
        <div class="guide-section-header">
            <span class="guide-section-icon">🛡️</span>
            <h2 class="guide-section-title">Privacy Policy</h2>
        </div>
        <p class="guide-section-desc">Last Updated: October 2026. Norra AI is built on a privacy-first foundation with zero persistent tracking.</p>

        <div class="legal-section-item">
            <h3>1. Information We Do NOT Collect</h3>
            <p>Norra AI does not require user accounts, email registration, passwords, credit card details, or banking information to access football forecasts and analytical tools. We do not collect or store your identity, phone number, or personal demographics.</p>
        </div>

        <div class="legal-section-item">
            <h3>2. Local Device Storage (Client-Side Caching)</h3>
            <p>To provide instant, zero-latency loading and offline resilience, the platform utilizes your browser's local storage (<code>localStorage</code>) to retain:</p>
            <ul>
                <li><strong>Theme Preference:</strong> Dark mode vs Light mode selection.</li>
                <li><strong>Odds Format:</strong> Decimal (DEC), Fractional (FRA), or American (AM).</li>
                <li><strong>Cached Predictions:</strong> Stale-while-revalidate data payloads for instant rendering.</li>
            </ul>
            <p>This data stays 100% on your device and is never transmitted or sold to third parties.</p>
        </div>

        <div class="legal-section-item">
            <h3>3. Anonymous Telemetry &amp; Traffic Metrics</h3>
            <p>We log anonymous, non-personally identifiable visit counts via standard server beacons to monitor network capacity and API response health. These logs contain no personal profile information.</p>
        </div>

        <div class="legal-section-item">
            <h3>4. Third-Party Links &amp; Bookmakers</h3>
            <p>Our platform may display external booking links to third-party sportsbooks. When navigating away from Norra AI, the privacy practices of those external destinations are governed by their respective privacy statements.</p>
        </div>

        <div class="legal-section-item">
            <h3>5. Data Security</h3>
            <p>All communication between your device and the Norra AI server is encrypted using industry-standard Transport Layer Security (TLS/HTTPS). We employ strict security headers to prevent cross-site scripting and unauthorized data tampering.</p>
        </div>

        <div class="legal-section-item">
            <h3>6. Inquiries &amp; Privacy Contact</h3>
            <p>For inquiries, feedback, or data governance questions regarding our mathematical models and privacy practices, our team is directly reachable via official email:</p>
            <div class="legal-contact-card">
                <span class="contact-icon">✉</span>
                <div class="contact-details">
                    <span class="contact-label">Official Data &amp; Privacy Contact</span>
                    <a href="mailto:predict@mynorra.xyz" class="contact-email-link">predict@mynorra.xyz</a>
                </div>
            </div>
        </div>
    </div>
    """
    return render_master_layout(
        title="Privacy Policy - Norra AI Mathematical Intelligence",
        canonical_path="privacy.html",
        meta_desc="Privacy policy detailing zero-tracking commitment, client-side caching, and data protection on Norra AI.",
        active_nav="privacy",
        header_h1="Privacy <span>Policy</span>",
        header_p="Zero-Tracking Commitment, Client-Side Caching & Data Protection.",
        body_content_html=body
    )
