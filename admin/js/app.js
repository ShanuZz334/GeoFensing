// ============================================================
// GeoFace Admin Panel — Application Logic
// ============================================================

let todayChart = null;
let failureChart = null;

/**
 * Initialize the admin app.
 * Checks for a stored token; shows login modal if not found.
 */
function initApp(page) {
  // if (!getToken()) {
  //   showLoginModal();
  //   return;
  // }
  hideLoginModal();

  if (page === 'dashboard') {
    loadDashboard();
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
    'buffer_zone': 'Buffer Zone'
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
    tbody.innerHTML = '<tr><td colspan="4" class="td-loading">No records yet</td></tr>';
    return;
  }

  tbody.innerHTML = data.logs.map(log => `
    <tr>
      <td><strong>${escHtml(log.teacher_name || '—')}</strong></td>
      <td style="color:var(--text-muted);font-size:12px">${formatDt(log.timestamp)}</td>
      <td><span class="badge badge--${log.status}">${log.status}</span></td>
      <td style="color:var(--text-muted);font-size:12px;max-width:200px;
                 overflow:hidden;text-overflow:ellipsis;white-space:nowrap" 
          title="${escHtml(log.reason)}">
        ${escHtml(log.reason)}
      </td>
    </tr>
  `).join('');
}
