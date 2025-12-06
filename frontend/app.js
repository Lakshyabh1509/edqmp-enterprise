/**
 * EDQMP Frontend Application
 * Enterprise Data Quality & Monitoring Platform
 * With Real Supabase Authentication
 */

// =============================================================================
// Configuration
// =============================================================================

const CONFIG = {
    API_URL: 'https://edqmp-enterprise.vercel.app/api/v1',
    SUPABASE_URL: 'https://rlvblrpfsfbnetdgnaqh.supabase.co',
    SUPABASE_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdmJscnBmc2ZibmV0ZGduYXFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ5Njc5MjYsImV4cCI6MjA4MDU0MzkyNn0.d4D5pTVgu9Jg36T2kXb3ZnC8OgcoPtzR_uqhme3qDHo'
};

// =============================================================================
// Supabase Client Initialization
// =============================================================================

let supabaseClient = null;

function initSupabase() {
    try {
        // Use global supabase from CDN
        if (typeof supabase !== 'undefined' && supabase.createClient) {
            supabaseClient = supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_KEY);
            console.log('✅ Supabase initialized successfully');
            return true;
        } else {
            console.error('❌ Supabase SDK not loaded');
            return false;
        }
    } catch (error) {
        console.error('❌ Failed to initialize Supabase:', error);
        return false;
    }
}

// =============================================================================
// State Management
// =============================================================================

const state = {
    isAuthenticated: false,
    isDemo: false,
    user: null,
    currentPage: 'dashboard',
    uploadedFile: null,
    chart: null,
    pendingVerification: false,
    pendingEmail: null
};

// =============================================================================
// Demo Data
// =============================================================================

const DEMO_DATA = {
    metrics: {
        riskExposure: '$142,500',
        riskDelta: '12%',
        qualityScore: '98.2%',
        qualityDelta: '+0.4%',
        incidents: '2',
        incidentsDelta: '-1',
        slaCompliance: '99.9%',
        slaDelta: 'Stable'
    },
    threats: [
        { severity: 'critical', title: 'CRITICAL: Trade Settlement Break', meta: 'Detected 15 mins ago • Potential Loss: $85k' },
        { severity: 'warning', title: 'WARNING: KYC Data Lag', meta: 'Feed delayed by 45s • Compliance Risk' }
    ],
    rules: [
        { name: 'trade_completeness', type: 'Completeness', target: 'trade_id', severity: 'Critical', status: 'Active' },
        { name: 'account_format', type: 'Accuracy', target: 'account_no', severity: 'Critical', status: 'Active' },
        { name: 'price_anomaly', type: 'Anomaly', target: 'price', severity: 'Warning', status: 'Active' }
    ],
    sources: [
        { name: 'Production DB (Read-Replica)', type: 'PostgreSQL', status: 'Connected' },
        { name: 'Snowflake Warehouse', type: 'Snowflake', status: 'Connected' },
        { name: 'S3 Data Lake', type: 'AWS S3', status: 'Syncing...' }
    ],
    pipelines: [
        { name: 'Trade Settlement', status: 'healthy', lastRun: '2 min ago', latency: '1.2s', successRate: '100%' },
        { name: 'KYC Processing', status: 'healthy', lastRun: '5 min ago', latency: '3.4s', successRate: '99.5%' },
        { name: 'FX Rates', status: 'warning', lastRun: '1 min ago', latency: '5.1s', successRate: '97.2%' },
        { name: 'Market Data', status: 'healthy', lastRun: '30 sec ago', latency: '0.8s', successRate: '100%' },
        { name: 'Risk Calc', status: 'healthy', lastRun: '10 min ago', latency: '8.2s', successRate: '99.8%' }
    ],
    alerts: [
        { severity: 'critical', source: 'Market Data Feed', rule: 'Anomaly Detection', message: 'Price spike detected: 3.2σ deviation', time: '10 min ago' },
        { severity: 'warning', source: 'KYC API', rule: 'Freshness Check', message: 'Data not refreshed in 2+ hours', time: '25 min ago' },
        { severity: 'warning', source: 'Trade Settlement', rule: 'Completeness', message: '5% missing values in account_id', time: '1 hour ago' }
    ]
};

// =============================================================================
// DOM Elements
// =============================================================================

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// =============================================================================
// Initialization
// =============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    showLoading(true);

    // Initialize Supabase
    await initSupabase();

    initTabs();
    initNavigation();
    initForms();
    initFileUpload();

    // Check for auth state
    await checkAuth();

    showLoading(false);
});

function showLoading(show) {
    // Could add a loading spinner here
}

// =============================================================================
// Authentication
// =============================================================================

async function checkAuth() {
    // First check if there's a Supabase session
    if (supabaseClient) {
        try {
            const { data: { session }, error } = await supabaseClient.auth.getSession();

            if (session && session.user) {
                state.user = {
                    id: session.user.id,
                    email: session.user.email,
                    name: session.user.user_metadata?.full_name || session.user.email.split('@')[0],
                    role: 'user',
                    isDemo: false,
                    emailVerified: session.user.email_confirmed_at !== null
                };
                state.isAuthenticated = true;
                state.isDemo = false;
                showApp();
                return;
            }
        } catch (error) {
            console.error('Session check error:', error);
        }
    }

    // Fall back to local storage
    const savedUser = localStorage.getItem('edqmp_user');
    if (savedUser) {
        state.user = JSON.parse(savedUser);
        state.isAuthenticated = true;
        state.isDemo = state.user.isDemo || false;
        showApp();
    } else {
        showLogin();
    }

    // Listen for auth state changes
    if (supabaseClient) {
        supabaseClient.auth.onAuthStateChange((event, session) => {
            console.log('Auth state changed:', event);
            if (event === 'SIGNED_IN' && session) {
                state.user = {
                    id: session.user.id,
                    email: session.user.email,
                    name: session.user.user_metadata?.full_name || session.user.email.split('@')[0],
                    role: 'user',
                    isDemo: false,
                    emailVerified: session.user.email_confirmed_at !== null
                };
                state.isAuthenticated = true;
                state.isDemo = false;
                showApp();
            } else if (event === 'SIGNED_OUT') {
                state.user = null;
                state.isAuthenticated = false;
                showLogin();
            }
        });
    }
}

function showLogin() {
    $('#loginModal').classList.remove('hidden');
    $('#app').classList.add('hidden');
    hideVerificationScreen();
}

function showVerificationScreen(email) {
    state.pendingVerification = true;
    state.pendingEmail = email;

    $('#loginTab').innerHTML = `
        <div class="verification-box">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📧</div>
            <h2 style="margin-bottom: 0.5rem;">Verify Your Email</h2>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                We've sent a verification link to<br>
                <strong style="color: var(--accent-primary);">${email}</strong>
            </p>
            <p style="color: var(--text-muted); font-size: 0.9rem;">
                Click the link in your email to activate your account.
                <br>Check your spam folder if you don't see it.
            </p>
        </div>
        <div style="display: flex; gap: 0.5rem; margin-top: 1.5rem;">
            <button class="btn btn-secondary" style="flex: 1;" onclick="resendVerification()">📤 Resend Email</button>
            <button class="btn btn-secondary" style="flex: 1;" onclick="backToLogin()">← Back</button>
        </div>
        <div style="margin-top: 1rem;">
            <button class="btn btn-primary btn-full" onclick="tryLoginAfterVerification()">🔐 I've Verified - Log In</button>
        </div>
    `;
}

function hideVerificationScreen() {
    state.pendingVerification = false;
    state.pendingEmail = null;
}

function backToLogin() {
    location.reload();
}

async function resendVerification() {
    if (!supabaseClient || !state.pendingEmail) {
        showToast('Cannot resend verification email', 'error');
        return;
    }

    try {
        const { error } = await supabaseClient.auth.resend({
            type: 'signup',
            email: state.pendingEmail
        });

        if (error) throw error;
        showToast('Verification email sent! Check your inbox.', 'success');
    } catch (error) {
        showToast('Failed to resend: ' + error.message, 'error');
    }
}

async function tryLoginAfterVerification() {
    showToast('Please enter your password to log in', 'info');
    location.reload();
}

function showApp() {
    $('#loginModal').classList.add('hidden');
    $('#app').classList.remove('hidden');

    updateUserInfo();

    if (state.isDemo) {
        $('#demoBanner').classList.remove('hidden');
        loadDemoData();
    } else {
        $('#demoBanner').classList.add('hidden');
        loadEmptyState();
    }

    navigateTo('dashboard');
}

async function login(email, password) {
    if (!email || !password) {
        showToast('Please enter email and password', 'error');
        return;
    }

    // Try Supabase auth first
    if (supabaseClient) {
        try {
            showToast('Signing in...', 'info');

            const { data, error } = await supabaseClient.auth.signInWithPassword({
                email: email,
                password: password
            });

            if (error) {
                if (error.message.includes('Email not confirmed')) {
                    showToast('Please verify your email first. Check your inbox.', 'warning');
                    showVerificationScreen(email);
                    return;
                }
                throw error;
            }

            if (data.user) {
                state.user = {
                    id: data.user.id,
                    email: data.user.email,
                    name: data.user.user_metadata?.full_name || data.user.email.split('@')[0],
                    role: 'user',
                    isDemo: false,
                    emailVerified: data.user.email_confirmed_at !== null
                };
                state.isAuthenticated = true;
                state.isDemo = false;

                localStorage.setItem('edqmp_user', JSON.stringify(state.user));
                showToast('Login successful!', 'success');
                showApp();
                return;
            }
        } catch (error) {
            console.error('Supabase login error:', error);
            showToast(error.message || 'Login failed. Please check your credentials.', 'error');
            return;
        }
    } else {
        // Fallback: Local auth for demo
        state.user = {
            email: email,
            name: email.split('@')[0],
            role: 'user',
            isDemo: false
        };
        state.isAuthenticated = true;
        state.isDemo = false;

        localStorage.setItem('edqmp_user', JSON.stringify(state.user));
        showToast('Login successful! (Demo mode)', 'success');
        showApp();
    }
}

async function signup(email, name, password) {
    if (!email || !name || !password) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    if (password.length < 6) {
        showToast('Password must be at least 6 characters', 'error');
        return;
    }

    // Try Supabase signup
    if (supabaseClient) {
        try {
            showToast('Creating account...', 'info');

            const { data, error } = await supabaseClient.auth.signUp({
                email: email,
                password: password,
                options: {
                    data: {
                        full_name: name
                    }
                }
            });

            if (error) throw error;

            if (data.user) {
                // Check if email verification is required
                if (data.user.email_confirmed_at === null) {
                    showToast('Account created! Please check your email to verify.', 'success');
                    showVerificationScreen(email);
                    return;
                } else {
                    // Email already confirmed (auto-confirm enabled)
                    state.user = {
                        id: data.user.id,
                        email: data.user.email,
                        name: name,
                        role: 'user',
                        isDemo: false
                    };
                    state.isAuthenticated = true;
                    state.isDemo = false;

                    localStorage.setItem('edqmp_user', JSON.stringify(state.user));
                    showToast('Account created successfully!', 'success');
                    showApp();
                    return;
                }
            }
        } catch (error) {
            console.error('Supabase signup error:', error);
            if (error.message.includes('already registered')) {
                showToast('An account with this email already exists. Please login.', 'error');
            } else {
                showToast(error.message || 'Signup failed. Please try again.', 'error');
            }
            return;
        }
    } else {
        // Fallback: Local signup for demo
        state.user = {
            email: email,
            name: name,
            role: 'user',
            isDemo: false
        };
        state.isAuthenticated = true;
        state.isDemo = false;

        localStorage.setItem('edqmp_user', JSON.stringify(state.user));
        showToast('Account created! (Demo mode - no email verification)', 'success');
        showApp();
    }
}

function loginDemo() {
    state.user = {
        email: 'demo@edqmp.com',
        name: 'Demo User',
        role: 'viewer',
        isDemo: true
    };
    state.isAuthenticated = true;
    state.isDemo = true;

    localStorage.setItem('edqmp_user', JSON.stringify(state.user));
    showToast('Welcome to the Demo!', 'success');
    showApp();
}

async function logout() {
    // Sign out from Supabase
    if (supabaseClient) {
        try {
            await supabaseClient.auth.signOut();
        } catch (error) {
            console.error('Logout error:', error);
        }
    }

    state.user = null;
    state.isAuthenticated = false;
    state.isDemo = false;
    localStorage.removeItem('edqmp_user');
    showLogin();
    showToast('Logged out successfully', 'success');
}

function updateUserInfo() {
    if (state.user) {
        $('#userName').textContent = state.user.name || state.user.email.split('@')[0];
        $('#userRole').textContent = state.user.role || 'User';
        $('#userAvatar').textContent = (state.user.name || state.user.email)[0].toUpperCase();
    }
}

// =============================================================================
// Navigation
// =============================================================================

function initNavigation() {
    $$('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            navigateTo(page);
        });
    });

    $('#logoutBtn').addEventListener('click', logout);
}

function navigateTo(page) {
    state.currentPage = page;

    // Update nav links
    $$('.nav-link').forEach(link => {
        link.classList.toggle('active', link.dataset.page === page);
    });

    // Update pages
    $$('.page').forEach(p => {
        p.classList.toggle('active', p.id === `${page}Page`);
    });

    // Load page-specific data
    if (state.isDemo) {
        switch (page) {
            case 'dashboard': loadDashboardData(); break;
            case 'quality': loadQualityData(); break;
            case 'pipelines': loadPipelinesData(); break;
            case 'alerts': loadAlertsData(); break;
            case 'reports': break;
        }
    }
}

// =============================================================================
// Tabs
// =============================================================================

function initTabs() {
    // Login/Signup tabs
    $$('.tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;

            // Update buttons
            btn.parentElement.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update content
            if (tab === 'login') {
                $('#loginTab').classList.add('active');
                $('#signupTab').classList.remove('active');
            } else {
                $('#loginTab').classList.remove('active');
                $('#signupTab').classList.add('active');
            }
        });
    });

    // Quality page tabs
    $$('[data-quality-tab]').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.qualityTab;

            $$('[data-quality-tab]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            $$('.quality-tab').forEach(t => t.classList.remove('active'));
            $(`#${tab}Tab`).classList.add('active');
        });
    });
}

// =============================================================================
// Forms
// =============================================================================

function initForms() {
    $('#loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = $('#loginEmail').value.trim();
        const password = $('#loginPassword').value;

        await login(email, password);
    });

    $('#signupForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = $('#signupEmail').value.trim();
        const name = $('#signupName').value.trim();
        const password = $('#signupPassword').value;
        const confirm = $('#signupConfirm').value;

        if (password !== confirm) {
            showToast('Passwords do not match', 'error');
            return;
        }

        await signup(email, name, password);
    });

    $('#demoBtn').addEventListener('click', loginDemo);

    $('#ruleForm').addEventListener('submit', (e) => {
        e.preventDefault();
        if (state.isDemo) {
            showToast('Cannot save rules in demo mode', 'warning');
        } else {
            showToast('Rule created successfully!', 'success');
        }
    });
}

// =============================================================================
// File Upload
// =============================================================================

function initFileUpload() {
    const uploadArea = $('#uploadArea');
    const fileInput = $('#fileInput');

    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--accent-primary)';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '';

        const file = e.dataTransfer.files[0];
        if (file) handleFileUpload(file);
    });

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file) handleFileUpload(file);
    });

    $('#runValidation').addEventListener('click', runValidation);
}

function handleFileUpload(file) {
    if (!file.name.endsWith('.csv') && !file.name.endsWith('.json')) {
        showToast('Please upload a CSV or JSON file', 'error');
        return;
    }

    state.uploadedFile = file;
    $('#fileInfo').classList.remove('hidden');
    $('#fileInfo').innerHTML = `✅ Loaded: ${file.name} (${formatFileSize(file.size)})`;
    $('#runValidation').disabled = false;

    showToast('File uploaded successfully!', 'success');
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function runValidation() {
    if (!state.uploadedFile) {
        showToast('Please upload a file first', 'error');
        return;
    }

    $('#runValidation').disabled = true;
    $('#runValidation').textContent = 'Running...';

    // Simulate validation
    setTimeout(() => {
        showValidationResults();
        $('#runValidation').disabled = false;
        $('#runValidation').textContent = '🚀 Execute Validation Engine';
    }, 1500);
}

function showValidationResults() {
    const resultsHtml = `
        <div class="card">
            <h3>🔍 Validation Results</h3>
            <div class="results-metrics">
                <div class="result-metric">
                    <div class="value" style="color: var(--success)">94.2%</div>
                    <div class="label">Quality Score</div>
                </div>
                <div class="result-metric">
                    <div class="value">1,245</div>
                    <div class="label">Rows Processed</div>
                </div>
                <div class="result-metric">
                    <div class="value" style="color: var(--danger)">72</div>
                    <div class="label">Failed Records</div>
                </div>
            </div>
            <div class="threat-item warning" style="margin-top: 1rem;">
                <div class="threat-title">⚠️ 72 records failed validation</div>
                <div class="threat-meta">Estimated Operational Risk: $32,400</div>
            </div>
        </div>
    `;

    $('#validationResults').innerHTML = resultsHtml;
    $('#validationResults').classList.remove('hidden');
    showToast('Validation complete!', 'success');
}

// =============================================================================
// Data Loading
// =============================================================================

function loadDemoData() {
    loadDashboardData();
}

function loadEmptyState() {
    // Show empty state on dashboard
    $('#emptyState').classList.remove('hidden');

    // Reset metrics to zero
    $('#riskExposure').textContent = '$0';
    $('#qualityScore').textContent = '0%';
    $('#incidents').textContent = '0';
    $('#slaCompliance').textContent = '—';

    $('#riskDelta').textContent = '0%';
    $('#qualityDelta').textContent = '0%';
    $('#incidentsDelta').textContent = '0';
    $('#slaDelta').textContent = 'N/A';
}

function loadDashboardData() {
    if (!state.isDemo) return;

    $('#emptyState').classList.add('hidden');

    // Load metrics
    const m = DEMO_DATA.metrics;
    $('#riskExposure').textContent = m.riskExposure;
    $('#qualityScore').textContent = m.qualityScore;
    $('#incidents').textContent = m.incidents;
    $('#slaCompliance').textContent = m.slaCompliance;

    $('#riskDelta').textContent = m.riskDelta;
    $('#qualityDelta').textContent = m.qualityDelta;
    $('#incidentsDelta').textContent = m.incidentsDelta;
    $('#slaDelta').textContent = m.slaDelta;

    // Load threats
    const threatsHtml = DEMO_DATA.threats.map(t => `
        <div class="threat-item ${t.severity}">
            <div class="threat-title">${t.title}</div>
            <div class="threat-meta">${t.meta}</div>
        </div>
    `).join('');
    $('#threatsList').innerHTML = threatsHtml;

    // Load chart
    loadRiskChart();
}

function loadRiskChart() {
    const ctx = $('#riskChart');
    if (!ctx) return;

    if (state.chart) {
        state.chart.destroy();
    }

    const labels = [];
    const data = [];
    const now = new Date();

    for (let i = 29; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        data.push(Math.floor(Math.random() * 150000) + 50000);
    }

    state.chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Risk Exposure ($)',
                data: data,
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

function loadQualityData() {
    if (!state.isDemo) return;

    // Load rules
    const rulesHtml = DEMO_DATA.rules.map(r => `
        <tr>
            <td>${r.name}</td>
            <td>${r.type}</td>
            <td>${r.target}</td>
            <td><span class="status-badge ${r.severity.toLowerCase()}">${r.severity}</span></td>
            <td><span class="status-badge healthy">${r.status}</span></td>
        </tr>
    `).join('');
    $('#rulesTableBody').innerHTML = rulesHtml;

    // Load sources
    const sourcesHtml = DEMO_DATA.sources.map(s => `
        <tr>
            <td>${s.name}</td>
            <td>${s.type}</td>
            <td><span class="status-badge ${s.status === 'Connected' ? 'healthy' : 'warning'}">${s.status}</span></td>
        </tr>
    `).join('');
    $('#sourcesTableBody').innerHTML = sourcesHtml;
}

function loadPipelinesData() {
    if (!state.isDemo) {
        $('#activePipelines').textContent = '0';
        $('#successRate').textContent = '—';
        $('#avgLatency').textContent = '—';
        $('#pipelineSla').textContent = '—';
        return;
    }

    $('#activePipelines').textContent = '24';
    $('#successRate').textContent = '99.2%';
    $('#avgLatency').textContent = '2.3s';
    $('#pipelineSla').textContent = '99.9%';

    const pipelinesHtml = DEMO_DATA.pipelines.map(p => `
        <tr>
            <td>${p.name}</td>
            <td><span class="status-badge ${p.status}">${p.status === 'healthy' ? '🟢 Healthy' : '🟡 Warning'}</span></td>
            <td>${p.lastRun}</td>
            <td>${p.latency}</td>
            <td>${p.successRate}</td>
        </tr>
    `).join('');
    $('#pipelinesTableBody').innerHTML = pipelinesHtml;
}

function loadAlertsData() {
    if (!state.isDemo) {
        $('#openAlerts').textContent = '0';
        $('#criticalAlerts').textContent = '0';
        $('#warningAlerts').textContent = '0';
        $('#resolvedAlerts').textContent = '0';
        $('#alertsList').innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;">No alerts configured yet</p>';
        return;
    }

    $('#openAlerts').textContent = '3';
    $('#criticalAlerts').textContent = '1';
    $('#warningAlerts').textContent = '2';
    $('#resolvedAlerts').textContent = '8';

    const alertsHtml = DEMO_DATA.alerts.map((a, i) => `
        <div class="alert-item ${a.severity}">
            <div class="alert-content">
                <div class="alert-header">${a.severity === 'critical' ? '🔴' : '🟡'} ${a.source} - ${a.rule}</div>
                <div class="alert-message">${a.message} • ${a.time}</div>
            </div>
            <div class="alert-actions">
                <button class="btn btn-secondary" onclick="acknowledgeAlert(${i})">Acknowledge</button>
                <button class="btn btn-primary" onclick="resolveAlert(${i})">Resolve</button>
            </div>
        </div>
    `).join('');
    $('#alertsList').innerHTML = alertsHtml;
}

function acknowledgeAlert(index) {
    showToast('Alert acknowledged (demo)', 'success');
}

function resolveAlert(index) {
    showToast('Alert resolved (demo)', 'success');
}

// =============================================================================
// Toast Notifications
// =============================================================================

function showToast(message, type = 'info') {
    const container = $('#toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// =============================================================================
// Global Functions
// =============================================================================

window.navigateTo = navigateTo;
window.acknowledgeAlert = acknowledgeAlert;
window.resolveAlert = resolveAlert;
window.resendVerification = resendVerification;
window.backToLogin = backToLogin;
window.tryLoginAfterVerification = tryLoginAfterVerification;
