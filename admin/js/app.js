// ============================================================
// GeoFace Admin Panel — Application Logic
// ============================================================

let todayChart = null;
let failureChart = null;
let trendChart = null;



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

  if (page !== 'alerts') {
    updateGlobalAlertBadge();
  }

  // Populate navbar profile from sessionStorage cache immediately
  const adminStr = sessionStorage.getItem('geoface_admin_data');
  if (adminStr) {
    try {
      const adminData = JSON.parse(adminStr);
      updateNavbarProfileUI(adminData);
    } catch (e) { console.error('Error parsing admin data', e); }
  }

  // Asynchronously sync fresh admin data from backend /admin/me
  syncAdminData();

  // Initialize click-based profile dropdown
  initProfileDropdown();
}

function updateNavbarProfileUI(adminData) {
  const nameEl = document.getElementById('nav-profile-name');
  const roleEl = document.getElementById('nav-profile-role');
  const picEl = document.getElementById('nav-profile-pic');
  const manageAdminsEl = document.getElementById('nav-manage-admins');
  const manageAdminsDiv = document.getElementById('nav-manage-admins-divider');
  
  if (nameEl) nameEl.textContent = adminData.name;
  if (roleEl) roleEl.textContent = adminData.is_head_admin ? 'Head Admin' : 'Administrator';
  if (picEl) {
    if (adminData.profile_pic) {
      picEl.src = adminData.profile_pic.startsWith('data:') ? adminData.profile_pic : 'data:image/jpeg;base64,' + adminData.profile_pic;
    } else {
      picEl.src = 'images/default-avatar.svg';
    }
  }
  
  if (manageAdminsEl && manageAdminsDiv) {
    if (adminData.is_head_admin) {
      manageAdminsEl.style.display = 'flex';
      manageAdminsDiv.style.display = 'block';
    } else {
      manageAdminsEl.style.display = 'none';
      manageAdminsDiv.style.display = 'none';
    }
  }
}

async function syncAdminData() {
  try {
    const freshData = await api('/admin/me');
    if (freshData && freshData.id) {
      sessionStorage.setItem('geoface_admin_data', JSON.stringify(freshData));
      updateNavbarProfileUI(freshData);
    }
  } catch (e) {
    console.error('Failed to sync admin data from backend', e);
  }
}

function initProfileDropdown() {
  const profileContainer = document.querySelector('.nav-profile');
  if (!profileContainer) return;

  if (profileContainer.dataset.dropdownInitialized) return;
  profileContainer.dataset.dropdownInitialized = "true";

  profileContainer.addEventListener('click', (e) => {
    e.stopPropagation();
    profileContainer.classList.toggle('open');
  });

  // Close when clicking anywhere else
  document.addEventListener('click', (e) => {
    if (!profileContainer.contains(e.target)) {
      profileContainer.classList.remove('open');
    }
  });
}

async function updateGlobalAlertBadge() {
  const data = await api('/admin/alerts');
  if (data && data.alerts) {
    const count = data.alerts.length;
    const badge = document.getElementById('navbar-alert-badge');
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    }
  }
}

// ── Dashboard ──────────────────────────────────────────────

function renderSparkline(elementId, dataArray, color) {
  const el = document.getElementById(elementId);
  if (!el || !dataArray || dataArray.length === 0) return;
  
  const width = 60;
  const height = 24;
  const max = Math.max(...dataArray, 1);
  const min = 0;
  
  const points = dataArray.map((val, i) => {
    const x = (i / (dataArray.length - 1)) * width;
    const y = height - ((val - min) / (max - min)) * height;
    return `${x},${y}`;
  }).join(' ');

  el.innerHTML = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" fill="none" xmlns="http://www.w3.org/2000/svg">
    <polyline points="${points}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>`;
}

function renderStatChange(elementId, todayVal, yesterdayVal, isRate = false) {
  const el = document.getElementById(elementId);
  if (!el) return;
  
  if (yesterdayVal === undefined) {
    el.innerHTML = '<span style="color:var(--text-muted)">No previous data</span>';
    return;
  }
  
  const diff = todayVal - yesterdayVal;
  if (diff === 0) {
    el.innerHTML = '<span style="color:var(--text-muted)">0% from yesterday</span>';
    return;
  }
  
  let percentage = 0;
  if (yesterdayVal > 0) {
    percentage = ((diff / yesterdayVal) * 100).toFixed(1);
  } else {
    percentage = 100; // If yesterday was 0 and today > 0
  }
  
  // For rate it's just the absolute difference
  if (isRate) {
    percentage = diff.toFixed(1);
  }
  
  const color = diff > 0 ? (elementId.includes('failure') ? 'var(--error)' : 'var(--success)') : (elementId.includes('failure') ? 'var(--success)' : 'var(--error)');
  const sign = diff > 0 ? '+' : '';
  const text = isRate ? `${sign}${percentage}% from yesterday` : `${sign}${diff} from yesterday`;
  
  el.innerHTML = `<span style="color:${color}">${text}</span>`;
}

async function loadDashboard() {
  const data = await api('/admin/stats');
  if (!data) return;

  // Stat cards
  const valTeachers = document.getElementById('val-teachers');
  const valSuccess = document.getElementById('val-success');
  const valFailure = document.getElementById('val-failure');
  const valRate = document.getElementById('val-rate');
  const rateLifetimeSub = document.getElementById('rate-lifetime-sub');

  if (valTeachers) valTeachers.textContent = data.total_teachers ?? '—';
  if (valSuccess) valSuccess.textContent = data.today_success ?? '—';
  if (valFailure) valFailure.textContent = data.today_failure ?? '—';
  if (valRate) valRate.textContent = data.overall_success_rate != null ? data.overall_success_rate + '%' : '—';
  if (rateLifetimeSub) {
    rateLifetimeSub.textContent = 'Lifetime Scans: ' + (data.total_logs != null ? data.total_logs.toLocaleString() : '—');
  }
    
  if (data.yesterday_success !== undefined) {
    const changeTeachers = document.getElementById('change-teachers');
    if (changeTeachers) {
      changeTeachers.innerHTML = '<span style="color:var(--text-muted)">All systems operational</span>';
    }
    renderStatChange('change-success', data.today_success, data.yesterday_success);
    renderStatChange('change-failure', data.today_failure, data.yesterday_failure);
    renderStatChange('change-rate', data.overall_success_rate, data.yesterday_rate, true);
    
    // Sparklines (using success_trend or failure_trend for others if they exist, or dummy for teachers)
    renderSparkline('spark-teachers', [4, 4, 4, 4, 4, 4, 4], '#8b5cf6');
    renderSparkline('spark-success', data.success_trend, '#10b981');
    renderSparkline('spark-failure', data.failure_trend, '#ef4444');
    
    // Compute precise daily success rates for overall rate sparkline
    const successTrend = data.success_trend || [];
    const failureTrend = data.failure_trend || [];
    const rateTrend = successTrend.map((succ, i) => {
      const fail = failureTrend[i] || 0;
      const tot = succ + fail;
      return tot > 0 ? (succ / tot) * 100 : 0;
    });
    renderSparkline('spark-rate', rateTrend, '#8b5cf6');

    // Render 7-Day Authentication Trend Area-Line Chart
    renderTrendChart(successTrend, failureTrend);
  }

  // Today's attendance chart
  renderTodayChart(data.today_success || 0, data.today_failure || 0);

  // Failure breakdown chart
  const stages = data.failure_by_stage || {};
  renderFailureChart(stages);

  // Recent logs
  loadRecentLogs();
}

function renderTrendChart(successTrend, failureTrend) {
  const canvas = document.getElementById('trendChart');
  if (!canvas) return;
  if (trendChart) trendChart.destroy();

  const ctx = canvas.getContext('2d');

  // Dynamic past 7 days labels
  const labels = [];
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    labels.push(i === 0 ? 'Today' : (i === 1 ? 'Yesterday' : days[d.getDay()]));
  }

  // Linear Area Gradients
  const succGrad = ctx.createLinearGradient(0, 0, 0, 280);
  succGrad.addColorStop(0, 'rgba(16, 185, 129, 0.25)');
  succGrad.addColorStop(1, 'rgba(16, 185, 129, 0)');

  const failGrad = ctx.createLinearGradient(0, 0, 0, 280);
  failGrad.addColorStop(0, 'rgba(239, 68, 68, 0.25)');
  failGrad.addColorStop(1, 'rgba(239, 68, 68, 0)');

  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Successful',
          data: successTrend,
          borderColor: '#10b981',
          borderWidth: 2.5,
          backgroundColor: succGrad,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#10b981',
          pointBorderColor: '#111118',
          pointBorderWidth: 1.5,
          pointRadius: 4,
          pointHoverRadius: 6,
        },
        {
          label: 'Failed',
          data: failureTrend,
          borderColor: '#ef4444',
          borderWidth: 2.5,
          backgroundColor: failGrad,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#ef4444',
          pointBorderColor: '#111118',
          pointBorderWidth: 1.5,
          pointRadius: 4,
          pointHoverRadius: 6,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#111118',
          titleColor: '#e2e8f0',
          bodyColor: '#94a3b8',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8,
          titleFont: { family: 'Inter', size: 12, weight: 'bold' },
          bodyFont: { family: 'Inter', size: 12 },
        }
      },
      scales: {
        x: {
          ticks: { color: '#94a3b8', font: { family: 'Inter', size: 11 } },
          grid: { display: false },
        },
        y: {
          ticks: { color: '#94a3b8', font: { family: 'Inter', size: 11 }, precision: 0 },
          grid: { color: 'rgba(255,255,255,0.05)' },
          beginAtZero: true,
        }
      }
    }
  });
}

function renderTodayChart(success, failure) {
  const ctx = document.getElementById('todayChart');
  if (!ctx) return;
  if (todayChart) todayChart.destroy();

  const total = success + failure;
  const pct = total > 0 ? Math.round((success / total) * 100) : 0;

  const pctEl = document.getElementById('today-success-percent');
  const succEl = document.getElementById('today-success-count');
  const failEl = document.getElementById('today-failure-count');

  if (pctEl) pctEl.textContent = `${pct}%`;
  if (succEl) succEl.textContent = success.toLocaleString();
  if (failEl) failEl.textContent = failure.toLocaleString();

  const hasData = success > 0 || failure > 0;

  todayChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: hasData ? ['Successful', 'Failed'] : ['No Data'],
      datasets: [{
        data: hasData ? [success, failure] : [1],
        backgroundColor: hasData ? ['#10b981', '#ef4444'] : ['rgba(255,255,255,0.05)'],
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '75%',
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: hasData,
          backgroundColor: '#111118',
          titleColor: '#e2e8f0',
          bodyColor: '#94a3b8',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: (c) => ` ${c.label}: ${c.parsed}`
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
    'attempt_limit': 'Attempt Limit',
    'auto_absent': 'Auto Absent'
  };

  const rawLabels = Object.keys(stages);
  const filteredStages = rawLabels.reduce((acc, key) => {
    if (stages[key] > 0) acc[key] = stages[key];
    return acc;
  }, {});

  const finalLabels = Object.keys(filteredStages).length > 0 ? Object.keys(filteredStages) : ['No Failures'];
  const values = Object.keys(filteredStages).length > 0 ? Object.values(filteredStages) : [0];

  const labels = finalLabels.map(s => labelMap[s] || s || 'Unknown');
  const colors = ['#ef4444', '#f59e0b', '#c084fc', '#3b82f6', '#14b8a6', '#f97316'];

  failureChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Count',
        data: values,
        backgroundColor: colors.slice(0, labels.length),
        borderRadius: 4,
        barThickness: 8,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#111118',
          titleColor: '#e2e8f0',
          bodyColor: '#94a3b8',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8,
        }
      },
      scales: {
        x: {
          ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 }, precision: 0 },
          grid: { color: 'rgba(255,255,255,0.05)' },
          beginAtZero: true,
        },
        y: {
          ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 } },
          grid: { display: false },
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

  const validLogs = data.logs.filter(log => !log.reason || (!log.reason.includes('Demo Mode') && !log.reason.includes('Auto-marked absent')));

  if (!validLogs.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="td-loading">No recent activity detected</td></tr>';
    return;
  }

  tbody.innerHTML = validLogs.map(log => {
    // 1. Premium Avatar Layout with dynamic fallback initials
    const initials = (log.teacher_name || 'T').charAt(0).toUpperCase();
    const hasAvatar = !!log.profile_pic;
    const avatarUrl = hasAvatar ? (log.profile_pic.startsWith('data:') ? log.profile_pic : 'data:image/jpeg;base64,' + log.profile_pic) : '';
    
    const avatarHTML = hasAvatar
      ? `<div style="position:relative; width:32px; height:32px; flex-shrink:0;">
           <img src="${avatarUrl}" alt="${escHtml(log.teacher_name)}" style="width:32px; height:32px; border-radius:50%; object-fit:cover; border:1.5px solid rgba(124, 58, 237, 0.3); box-shadow: 0 2px 8px rgba(0,0,0,0.2);" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
           <div style="display:none; width:32px; height:32px; border-radius:50%; background:linear-gradient(135deg, #c084fc 0%, #6366f1 100%); color:#fff; font-weight:600; font-size:12px; align-items:center; justify-content:center; border:1.5px solid rgba(124, 58, 237, 0.35); box-shadow:0 2px 8px rgba(0,0,0,0.2);">${initials}</div>
         </div>`
      : `<div style="width:32px; height:32px; border-radius:50%; background:linear-gradient(135deg, #c084fc 0%, #6366f1 100%); color:#fff; font-weight:600; font-size:12px; display:flex; align-items:center; justify-content:center; border:1.5px solid rgba(124, 58, 237, 0.35); box-shadow:0 2px 8px rgba(0,0,0,0.2); flex-shrink:0;">${initials}</div>`;

    const nameDisplay = `
      <div style="display:flex; align-items:center; gap:12px;">
        ${avatarHTML}
        <div style="display:flex; flex-direction:column; gap:2px;">
          <span style="font-weight:600; color:var(--text); font-size:13.5px;">${escHtml(log.teacher_name || '—')}</span>
          <span class="reg-badge">${escHtml(log.reg_no || '—')}</span>
        </div>
      </div>
    `;

    // 2. Styled Split Time Layout
    const dtParts = formatDt(log.timestamp).split(', ');
    const dateStr = dtParts[0] || '—';
    const timeStr = dtParts[1] || '';
    
    const timeDisplay = `
      <div style="display:flex; flex-direction:column; gap:2px;">
        <span style="font-size:13px; color:var(--text); font-weight:500;">${dateStr}</span>
        <span style="font-size:11px; color:var(--text-muted); display:flex; align-items:center; gap:4px;">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:12px; height:12px; color:var(--text-muted);"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          ${timeStr}
        </span>
      </div>
    `;

    // 3. Unified Pill Badges
    const statusRaw = (log.status_display || log.status || '').toUpperCase();
    let statusClass = 'neutral';
    if (statusRaw.includes('SUCCESS') || statusRaw.includes('FULL') || statusRaw.includes('SUCCESSFUL')) {
      statusClass = 'success';
    } else if (statusRaw.includes('FAIL') || statusRaw.includes('ABSENT') || statusRaw.includes('ERROR')) {
      statusClass = 'failure';
    } else if (statusRaw.includes('HALF') || statusRaw.includes('LEAVE') || statusRaw.includes('FLAGGED') || statusRaw.includes('WARN')) {
      statusClass = 'warning';
    }
    const statusBadge = `<span class="badge-pill badge-pill--${statusClass}">${statusRaw}</span>`;

    // 4. Smart Callouts for Reasons
    let reasonClass = 'success';
    let reasonIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:13px; height:13px; flex-shrink: 0;"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
    
    const isSuccess = log.status === 'success';
    if (!isSuccess) {
      const reasonLower = (log.reason || '').toLowerCase();
      if (reasonLower.includes('geofence') || reasonLower.includes('premises') || reasonLower.includes('location') || reasonLower.includes('zone')) {
        reasonClass = 'warning';
        reasonIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:13px; height:13px; flex-shrink: 0;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>`;
      } else {
        reasonClass = 'failure';
        reasonIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:13px; height:13px; flex-shrink: 0;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
      }
    }

    return `
      <tr>
        <td>${nameDisplay}</td>
        <td>${timeDisplay}</td>
        <td>${statusBadge}</td>
        <td>
          <div class="reason-callout reason-callout--${reasonClass}" title="${escHtml(log.reason || '—')}">
            ${reasonIcon}
            <span class="reason-text">${escHtml(log.reason || 'Verification successful')}</span>
          </div>
        </td>
      </tr>
    `;
  }).join('');
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


// --- Uiverse Custom Dropdown Logic ---
function initUiverseSelects() {
  document.querySelectorAll('.uiverse-select').forEach(selectEl => {
    // Prevent double initialization
    if (selectEl.dataset.initialized) return;
    selectEl.dataset.initialized = "true";

    const selectedTextSpan = selectEl.querySelector('.uiverse-selected-text');
    const radios = selectEl.querySelectorAll('input[type="radio"]');

    // On load, set the text to the checked radio (if any)
    const checkedRadio = selectEl.querySelector('input[type="radio"]:checked');
    if (checkedRadio && checkedRadio.id) {
      const label = selectEl.querySelector(`label[for="${checkedRadio.id}"]`);
      if (label) selectedTextSpan.textContent = label.getAttribute('data-txt') || label.textContent;
    }

    const selectedDiv = selectEl.querySelector('.uiverse-selected');
    if (selectedDiv) {
      selectedDiv.addEventListener('click', (e) => {
        e.stopPropagation();
        // Close other open selects
        document.querySelectorAll('.uiverse-select').forEach(el => {
          if (el !== selectEl) el.classList.remove('open');
        });
        selectEl.classList.toggle('open');
      });
    }

    radios.forEach(radio => {
      radio.addEventListener('change', (e) => {
        if (e.target.checked && e.target.id) {
          const label = selectEl.querySelector(`label[for="${e.target.id}"]`);
          if (label) {
            selectedTextSpan.textContent = label.getAttribute('data-txt') || label.textContent;
          }
          selectEl.classList.remove('open');
          // Dispatch a custom change event on the main select container for external listeners
          selectEl.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });
    });
  });

  // Close selects when clicking outside
  document.addEventListener('click', () => {
    document.querySelectorAll('.uiverse-select.open').forEach(el => el.classList.remove('open'));
  });
}

// Helper to get value
function getUiverseSelectValue(selectId) {
  const container = document.getElementById(selectId);
  if (!container) return null;
  const checked = container.querySelector('input[type="radio"]:checked');
  return checked ? checked.value : null;
}

// Helper to set value
function setUiverseSelectValue(selectId, value) {
  const container = document.getElementById(selectId);
  if (!container) return;
  const radios = container.querySelectorAll('input[type="radio"]');
  let matched = false;
  radios.forEach(r => {
    if (r.value === value || r.id === value) {
      r.checked = true;
      r.dispatchEvent(new Event('change'));
      matched = true;
    }
  });
  // If not matched, select the first option
  if (!matched && radios.length > 0) {
    radios[0].checked = true;
    radios[0].dispatchEvent(new Event('change'));
  }
}

// Auto-init on DOMContentLoaded
document.addEventListener('DOMContentLoaded', initUiverseSelects);
