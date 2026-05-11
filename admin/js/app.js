// ============================================================
// GeoFace Admin Panel — Application Logic
// ============================================================

let todayChart = null;
let failureChart = null;



/**
 * Initialize the admin app.
 * Checks for a stored token; shows login modal if not found.
 */
function initApp(page, onReady) {
  const isIndex = window.location.pathname.endsWith('index.html') ||
                  window.location.pathname.endsWith('/admin/') ||
                  window.location.pathname === '/admin';

  if (!getToken()) {
    if (isIndex) {
      showLoginModal();
    } else {
      window.location.href = 'index.html';
    }
    return;
  }

  hideLoginModal();

  if (page === 'dashboard') {
    loadDashboard();
  }

  if (typeof onReady === 'function') {
    onReady();
  }

  // Update alert badge globally
  if (page !== 'alerts') {
    updateGlobalAlertBadge();
  }
}

async function updateGlobalAlertBadge() {
  const data = await api('/admin/alerts');
  if (data && data.alerts) {
    const count = data.alerts.length;
    const badge = document.getElementById('sidebar-alert-badge');
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    }
  }
}

// ── Dashboard ──────────────────────────────────────────────

async function loadDashboard() {
  const data = await api('/admin/stats');
  if (!data) return;

  // Stat cards
  document.getElementById('val-teachers').textContent = data.total_teachers ?? '—';
  document.getElementById('val-success').textContent = data.today_success ?? '—';
  document.getElementById('val-failure').textContent = data.today_failure ?? '—';
  document.getElementById('val-rate').textContent =
    data.overall_success_rate != null ? data.overall_success_rate + '%' : '—';

  // Today's attendance chart
  const todayTotal = (data.today_success || 0) + (data.today_failure || 0);
  renderTodayChart(data.today_success || 0, data.today_failure || 0);

  // Failure breakdown chart
  const stages = data.failure_by_stage || {};
  renderFailureChart(stages);

  // Recent logs
  loadRecentLogs();
}

function renderTodayChart(success, failure) {
  const ctx = document.getElementById('todayChart');
  if (!ctx) return;
  if (todayChart) todayChart.destroy();

  const hasData = success > 0 || failure > 0;

  todayChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: hasData ? ['Successful', 'Failed'] : ['No Data'],
      datasets: [{
        data: hasData ? [success, failure] : [1],
        backgroundColor: hasData ? ['rgba(124,58,237,0.8)', 'rgba(239,68,68,0.8)'] : ['rgba(255,255,255,0.05)'],
        borderColor: hasData ? ['#7C3AED', '#ef4444'] : ['rgba(255,255,255,0.1)'],
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 12 } } },
        tooltip: { 
          callbacks: { 
            label: (c) => c.label === 'No Data' ? ' No Data for today' : ` ${c.label}: ${c.parsed}` 
          } 
        },
      },
    },
  });
}

function renderFailureChart(stages) {
  const ctx = document.getElementById('failureChart');
  if (!ctx) return;
  if (failureChart) failureChart.destroy();

  const labelMap = {
    'face_detection': 'Face Detection',
    'face_recognition': 'Face Recognition',
    'geofence': 'Geofencing',
    'liveness': 'Liveness Check',
    'frame_decode': 'Frame Decode',
    'buffer_zone': 'Buffer Zone',
    'attempt_limit': 'Attempt Limit'
  };
  const labels = Object.keys(stages).map(s => labelMap[s] || s || 'Unknown');
  const values = Object.values(stages);
  const colors = ['#ef4444','#f59e0b','#8b5cf6','#3b82f6','#14b8a6','#f97316'];

  failureChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Count',
        data: values,
        backgroundColor: colors.slice(0, labels.length),
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          ticks: { color: '#94a3b8', font: { size: 11 } },
          grid: { color: 'rgba(255,255,255,0.05)' },
        },
        y: {
          ticks: { color: '#94a3b8', stepSize: 1 },
          grid: { color: 'rgba(255,255,255,0.05)' },
          beginAtZero: true,
        },
      },
    },
  });
}

async function loadRecentLogs() {
  const data = await api('/admin/attendance?per_page=8');
  if (!data) return;

  const tbody = document.getElementById('recent-tbody');
  if (!tbody) return;

  if (!data.logs.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="td-loading"><div class="spinner"></div></td></tr>';
    return;
  }

  tbody.innerHTML = data.logs.map(log => `
    <tr>
      <td><strong>${escHtml(log.teacher_name || '—')}</strong></td>
      <td style="color:var(--text-muted);font-size:12px">${formatDt(log.timestamp)}</td>
      <td><span class="badge badge--${log.status}">${log.status_display || log.status}</span></td>
      <td style="color:var(--text-muted);font-size:12px;max-width:200px;
                 overflow:hidden;text-overflow:ellipsis;white-space:nowrap" 
          title="${escHtml(log.reason)}">
        ${escHtml(log.reason)}
      </td>
    </tr>
  `).join('');
}

// ── Custom Dialog Helpers (replaces browser confirm/alert) ──────────────────

/**
 * Show a styled in-app confirm dialog.
 * Returns a Promise<boolean> — true if confirmed, false if cancelled.
 */
function uiConfirm(message, { danger = false } = {}) {
  return new Promise(resolve => {
    // Remove any existing dialog
    const existing = document.getElementById('ui-confirm-overlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'ui-confirm-overlay';
    overlay.style.cssText = `
      position:fixed;inset:0;background:rgba(0,0,0,0.65);backdrop-filter:blur(4px);
      display:flex;align-items:center;justify-content:center;z-index:99999;
    `;

    const confirmBtnColor = danger ? '#ef4444' : 'var(--primary, #7c3aed)';

    overlay.innerHTML = `
      <div style="
        background:var(--surface-1,#111118);border:1px solid var(--border,rgba(255,255,255,0.08));
        border-radius:16px;padding:28px 28px 24px;max-width:360px;width:90%;
        box-shadow:0 24px 48px rgba(0,0,0,0.5);text-align:center;
      ">
        <div style="width:44px;height:44px;border-radius:50%;background:rgba(239,68,68,0.12);
                    display:flex;align-items:center;justify-content:center;margin:0 auto 16px;">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="${danger ? '#ef4444' : 'var(--primary,#7c3aed)'}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <p style="color:var(--text,#e2e8f0);font-size:14px;line-height:1.6;margin-bottom:24px;font-weight:500;">${message}</p>
        <div style="display:flex;gap:10px;">
          <button id="ui-confirm-cancel" style="
            flex:1;padding:11px;border-radius:10px;border:1px solid var(--border,rgba(255,255,255,0.08));
            background:var(--surface-2,#1e1e2d);color:var(--text,#e2e8f0);font-size:14px;
            font-weight:600;cursor:pointer;transition:background 0.15s;
          ">Cancel</button>
          <button id="ui-confirm-ok" style="
            flex:1;padding:11px;border-radius:10px;border:none;
            background:${confirmBtnColor};color:#fff;font-size:14px;
            font-weight:600;cursor:pointer;transition:opacity 0.15s;
          ">Confirm</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    document.getElementById('ui-confirm-ok').onclick = () => { overlay.remove(); resolve(true); };
    document.getElementById('ui-confirm-cancel').onclick = () => { overlay.remove(); resolve(false); };
    overlay.addEventListener('click', e => { if (e.target === overlay) { overlay.remove(); resolve(false); } });
  });
}

/**
 * Show a styled in-app alert (info/error notice).
 * Returns a Promise that resolves when dismissed.
 */
function uiAlert(message, { type = 'info' } = {}) {
  return new Promise(resolve => {
    const existing = document.getElementById('ui-alert-overlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'ui-alert-overlay';
    overlay.style.cssText = `
      position:fixed;inset:0;background:rgba(0,0,0,0.65);backdrop-filter:blur(4px);
      display:flex;align-items:center;justify-content:center;z-index:99999;
    `;

    const color = type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : 'var(--primary,#7c3aed)';

    overlay.innerHTML = `
      <div style="
        background:var(--surface-1,#111118);border:1px solid var(--border,rgba(255,255,255,0.08));
        border-radius:16px;padding:28px 28px 24px;max-width:340px;width:90%;
        box-shadow:0 24px 48px rgba(0,0,0,0.5);text-align:center;
      ">
        <p style="color:var(--text,#e2e8f0);font-size:14px;line-height:1.6;margin-bottom:22px;font-weight:500;">${message}</p>
        <button id="ui-alert-ok" style="
          width:100%;padding:11px;border-radius:10px;border:none;
          background:${color};color:#fff;font-size:14px;font-weight:600;cursor:pointer;
        ">OK</button>
      </div>
    `;

    document.body.appendChild(overlay);
    document.getElementById('ui-alert-ok').onclick = () => { overlay.remove(); resolve(); };
    overlay.addEventListener('click', e => { if (e.target === overlay) { overlay.remove(); resolve(); } });
  });
}

