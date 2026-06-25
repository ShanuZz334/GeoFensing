// ============================================================
// GeoFace Admin Panel — API Service
// ============================================================

const API_BASE = '/api'; // Production-ready (proxied via Nginx)

const TOKEN_KEY = 'geoface_admin_token';
const ADMIN_DATA_KEY = 'geoface_admin_data';

function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

function setToken(t) {
  sessionStorage.setItem(TOKEN_KEY, t);
}

function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(ADMIN_DATA_KEY);
}

function getAdminData() {
  try { return JSON.parse(sessionStorage.getItem(ADMIN_DATA_KEY) || 'null'); } catch { return null; }
}

function isCurrentAdminHeadAdmin() {
  const admin = getAdminData();
  return admin && admin.is_head_admin === true;
}

/**
 * Central fetch wrapper. (MOCKED FOR DUMMY VERCEL DEPLOYMENT)
 */
async function api(path, method = 'GET', body = null) {
  let token = getToken();
  if (!token) {
    if (window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('/admin/')) {
      if (typeof showLoginModal === 'function') showLoginModal();
    } else {
      window.location.href = 'index.html';
    }
    return null;
  }
  
  // MOCK DELAY
  await new Promise(r => setTimeout(r, 200));

  // MOCK RESPONSES
  if (path.startsWith('/admin/me')) {
    return getAdminData() || { reg_no: 'dummy_admin', is_head_admin: true };
  }
  if (path.startsWith('/admin/stats')) {
    return {
      teacher_count: 42,
      active_count: 38,
      today_present: 30,
      today_absent: 8,
      alert_count: 2
    };
  }
  if (path.startsWith('/admin/alerts')) {
    if (method === 'POST') return { success: true };
    return [];
  }
  if (path.startsWith('/admin/attendance')) {
    return { records: [], total: 0 };
  }
  if (path.startsWith('/admin/geofence')) {
    if (method === 'PUT') return { success: true };
    return { center_lat: 12.9716, center_lng: 77.5946, radius_meters: 100, is_enabled: true };
  }
  if (path.startsWith('/admin/settings')) {
    if (method === 'PATCH') return { success: true };
    return {
      capture_interval_mins: 15,
      offline_sync_hours: 24,
      allow_fake_location: false,
      enable_liveness: true
    };
  }
  if (path.startsWith('/admin/admins')) {
    if (method === 'POST') return { success: true };
    return [{ id: 1, reg_no: 'admin', is_head_admin: true, created_at: new Date().toISOString() }];
  }
  if (path.startsWith('/admin/teachers')) {
    if (method !== 'GET') return { success: true };
    return [{ id: 1, reg_no: 'T001', name: 'Dummy Teacher', is_active: true, face_registered: true, has_device_id: true, last_active: new Date().toISOString() }];
  }
  if (path.startsWith('/admin/logs')) {
    return [];
  }
  
  // Fallback
  return { success: true, message: 'Mock response' };
}

async function adminLogin() {
  const reg_no = document.getElementById('admin-reg-no').value.trim();
  const password = document.getElementById('admin-password').value;
  const errEl = document.getElementById('login-error');
  errEl.style.display = 'none';

  const btn = document.getElementById('btn-login');
  btn.disabled = true;
  btn.textContent = 'Signing in…';

  // Mock delay
  await new Promise(r => setTimeout(r, 500));

  btn.disabled = false;
  btn.textContent = 'Login';

  if (!reg_no || !password) {
    errEl.textContent = 'Please enter any credentials';
    errEl.style.display = 'block';
    return;
  }

  setToken('dummy_token_123');
  sessionStorage.setItem(ADMIN_DATA_KEY, JSON.stringify({
    reg_no: reg_no,
    is_head_admin: true
  }));
  hideLoginModal();
  window.location.reload();
}

function adminSignOut() {
  clearToken();
  if (window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('/admin/')) {
    window.location.reload();
  } else {
    window.location.href = 'index.html';
  }
}

function showLoginModal() {
  const m = document.getElementById('login-modal');
  if (m) m.style.display = 'flex';
}
function hideLoginModal() {
  const m = document.getElementById('login-modal');
  if (m) m.style.display = 'none';
}

// ── Utilities ─────────────────────────────────────────────
function escHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function formatDt(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: true,
  });
}

function showToast(msg, type = 'info') {
  const toast = document.createElement('div');
  toast.textContent = msg;
  toast.style.cssText = `
    position:fixed;bottom:20px;right:20px;z-index:9999;
    background:${type === 'error' ? '#7f1d1d' : '#1e293b'};
    color:${type === 'error' ? '#fca5a5' : '#f1f5f9'};
    border:1px solid ${type === 'error' ? '#ef4444' : '#334155'};
    padding:12px 20px;border-radius:10px;font-size:13px;
    box-shadow:0 8px 24px rgba(0,0,0,0.4);
    animation:slideIn 0.25s ease;
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ── Custom UI Modals ──────────────────────────────────────
window.uiAlert = function(title, message = '') {
  return new Promise(resolve => {
    const modalHtml = `
      <div id="custom-alert-modal" class="modal-overlay" style="display:flex; z-index: 99999;">
        <div class="modal-card" style="max-width: 400px; text-align: center;">
          <h3 style="margin-bottom: 10px; color: var(--text);">${escHtml(title)}</h3>
          <p style="margin-bottom: 24px; color: var(--text-muted);">${escHtml(message)}</p>
          <button id="alert-ok-btn" class="btn btn-primary" style="width: 100%; justify-content: center;">OK</button>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.getElementById('alert-ok-btn').onclick = () => {
      document.getElementById('custom-alert-modal').remove();
      resolve();
    };
  });
};

window.uiConfirm = function(title, message = '') {
  return new Promise(resolve => {
    const modalHtml = `
      <div id="custom-confirm-modal" class="modal-overlay" style="display:flex; z-index: 99999;">
        <div class="modal-card" style="max-width: 400px;">
          <h3 style="margin-bottom: 10px; color: var(--text);">${escHtml(title)}</h3>
          <p style="margin-bottom: 24px; color: var(--text-muted); line-height: 1.5;">${escHtml(message)}</p>
          <div style="display: flex; justify-content: flex-end; gap: 12px;">
            <button id="confirm-cancel-btn" class="btn-secondary">Cancel</button>
            <button id="confirm-ok-btn" class="btn-primary">Confirm</button>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.getElementById('confirm-cancel-btn').onclick = () => {
      document.getElementById('custom-confirm-modal').remove();
      resolve(false);
    };
    document.getElementById('confirm-ok-btn').onclick = () => {
      document.getElementById('custom-confirm-modal').remove();
      resolve(true);
    };
  });
};
