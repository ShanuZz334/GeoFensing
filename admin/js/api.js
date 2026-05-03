// ============================================================
// GeoFace Admin Panel — API Service
// ============================================================

const API_BASE = '/api'; // Production-ready (proxied via Nginx)

const TOKEN_KEY = 'geoface_admin_token';

function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

function setToken(t) {
  sessionStorage.setItem(TOKEN_KEY, t);
}

function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

/**
 * Central fetch wrapper. Automatically attaches Authorization header.
 * Returns parsed JSON on success, null on error (shows error in console).
 */
async function api(path, method = 'GET', body = null) {
  let token = getToken();
  if (!token) {
    const loginRes = await fetch(`${API_BASE}/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'admin@college.edu', password: 'Admin@1234' })
    }).catch(() => null);
    if (loginRes && loginRes.ok) {
      const data = await loginRes.json();
      setToken(data.token);
      token = data.token;
    }
  }
  const opts = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  };
  if (body) opts.body = JSON.stringify(body);

  try {
    const res = await fetch(`${API_BASE}${path}`, opts);
    const json = await res.json().catch(() => ({}));

    if (res.status === 401) {
      clearToken();
      if (typeof showLoginModal === 'function') {
        showLoginModal();
      }
      return null;
    }
    if (!res.ok) {
      console.error('API error', res.status, json);
      showToast(json.error || json.reason || `Error ${res.status}`, 'error');
      return null;
    }
    return json;
  } catch (err) {
    console.error('Network error:', err);
    showToast('Network error — is the backend running?', 'error');
    return null;
  }
}

async function adminLogin() {
  const email = document.getElementById('admin-email').value.trim();
  const password = document.getElementById('admin-password').value;
  const errEl = document.getElementById('login-error');
  errEl.style.display = 'none';

  const btn = document.getElementById('btn-login');
  btn.disabled = true;
  btn.textContent = 'Signing in…';

  const res = await fetch(`${API_BASE}/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  }).catch(() => null);

  btn.disabled = false;
  btn.textContent = 'Sign In';

  if (!res || !res.ok) {
    errEl.textContent = 'Invalid admin credentials';
    errEl.style.display = 'block';
    return;
  }
  const data = await res.json();
  setToken(data.token);
  hideLoginModal();
  window.location.reload();
}

function adminSignOut() {
  clearToken();
  showLoginModal();
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
