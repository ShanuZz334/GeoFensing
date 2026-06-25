// ============================================================
// GeoFace Admin Panel — API Service (DEMO MODE — No Backend)
// ============================================================

const API_BASE = '/api';
const TOKEN_KEY = 'geoface_admin_token';
const ADMIN_DATA_KEY = 'geoface_admin_data';

function getToken() { return sessionStorage.getItem(TOKEN_KEY); }
function setToken(t) { sessionStorage.setItem(TOKEN_KEY, t); }
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

// ── Rich Mock Data ──────────────────────────────────────────

const MOCK_TEACHERS = [
  {
    id: 1, teacher_id: 1, reg_no: 'TCH001', name: 'Dr. Priya Sharma', full_name: 'Dr. Priya Sharma',
    department: 'Computer Science', email: 'priya.sharma@college.edu',
    phone: '+91 98765 43210', is_active: true,
    has_face_encoding: true, face_registered: true, has_device_id: true,
    profile_pic: null, profile_pic_url: 'https://i.pravatar.cc/150?img=47',
    last_active: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    created_at: '2024-08-01T09:00:00Z',
  },
  {
    id: 2, teacher_id: 2, reg_no: 'TCH002', name: 'Prof. Arjun Mehta', full_name: 'Prof. Arjun Mehta',
    department: 'Electronics & Comm.', email: 'arjun.mehta@college.edu',
    phone: '+91 91234 56789', is_active: true,
    has_face_encoding: true, face_registered: true, has_device_id: true,
    profile_pic: null, profile_pic_url: 'https://i.pravatar.cc/150?img=12',
    last_active: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    created_at: '2024-08-01T09:00:00Z',
  },
  {
    id: 3, teacher_id: 3, reg_no: 'TCH003', name: 'Ms. Divya Nair', full_name: 'Ms. Divya Nair',
    department: 'Mathematics', email: 'divya.nair@college.edu',
    phone: '+91 99887 76655', is_active: true,
    has_face_encoding: true, face_registered: true, has_device_id: true,
    profile_pic: null, profile_pic_url: 'https://i.pravatar.cc/150?img=23',
    last_active: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    created_at: '2024-08-15T10:30:00Z',
  },
  {
    id: 4, teacher_id: 4, reg_no: 'TCH004', name: 'Mr. Karan Patel', full_name: 'Mr. Karan Patel',
    department: 'Mechanical Engg.', email: 'karan.patel@college.edu',
    phone: '+91 88776 65544', is_active: true,
    has_face_encoding: true, face_registered: true, has_device_id: false,
    profile_pic: null, profile_pic_url: 'https://i.pravatar.cc/150?img=65',
    last_active: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
    created_at: '2024-09-01T08:00:00Z',
  },
  {
    id: 5, teacher_id: 5, reg_no: 'TCH005', name: 'Dr. Sneha Kulkarni', full_name: 'Dr. Sneha Kulkarni',
    department: 'Physics', email: 'sneha.kulkarni@college.edu',
    phone: '+91 77665 54433', is_active: true,
    has_face_encoding: false, face_registered: false, has_device_id: true,
    profile_pic: null, profile_pic_url: 'https://i.pravatar.cc/150?img=32',
    last_active: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(),
    created_at: '2024-09-10T09:00:00Z',
  },
  {
    id: 6, teacher_id: 6, reg_no: 'TCH006', name: 'Mr. Rahul Gupta', full_name: 'Mr. Rahul Gupta',
    department: 'Civil Engg.', email: 'rahul.gupta@college.edu',
    phone: '+91 66554 43322', is_active: false,
    has_face_encoding: true, face_registered: true, has_device_id: true,
    profile_pic: null, profile_pic_url: 'https://i.pravatar.cc/150?img=52',
    last_active: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
    created_at: '2024-07-20T11:00:00Z',
  },
  {
    id: 7, teacher_id: 7, reg_no: 'TCH007', name: 'Prof. Lakshmi Iyer', full_name: 'Prof. Lakshmi Iyer',
    department: 'Chemistry', email: 'lakshmi.iyer@college.edu',
    phone: '+91 55443 32211', is_active: true,
    has_face_encoding: true, face_registered: true, has_device_id: true,
    profile_pic: null, profile_pic_url: 'https://i.pravatar.cc/150?img=41',
    last_active: new Date(Date.now() - 1000 * 60 * 20).toISOString(),
    created_at: '2024-08-05T10:00:00Z',
  },
  {
    id: 8, teacher_id: 8, reg_no: 'TCH008', name: 'Dr. Vikram Reddy', full_name: 'Dr. Vikram Reddy',
    department: 'Computer Science', email: 'vikram.reddy@college.edu',
    phone: '+91 44332 21100', is_active: true,
    has_face_encoding: true, face_registered: true, has_device_id: true,
    profile_pic: null, profile_pic_url: 'https://i.pravatar.cc/150?img=7',
    last_active: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
    created_at: '2024-08-20T08:30:00Z',
  },
];

function makeTrend(base, variance = 3, days = 30) {
  return Array.from({ length: days }, () => Math.max(0, base + Math.floor((Math.random() - 0.4) * variance * 2)));
}

const today = new Date();
const monthName = today.toLocaleString('en-IN', { month: 'long', year: 'numeric' });

const successTrend = makeTrend(28, 6, 30);
const failureTrend = makeTrend(5, 3, 30);
const todaySuccess = 31;
const todayFailure = 4;
const totalTeachers = 8;
const inactiveTeachers = 1;

// Campus centre + slight scatter for map pins
const CAMPUS_CENTER_LAT = 31.2536;
const CAMPUS_CENTER_LNG = 75.7037;

function randOffset(range) { return (Math.random() - 0.5) * range; }

// Recent attendance logs — enriched with GPS, action_type, frames
function makeLogs(count) {
  const teachers = MOCK_TEACHERS.filter(t => t.is_active);
  const results = [];
  const scenarios = [
    { status: 'success', reason: 'Verification successful', action_type: 'check_in', attendance_mark: 'present' },
    { status: 'success', reason: 'Verification successful', action_type: 'check_in', attendance_mark: 'present' },
    { status: 'success', reason: 'Verification successful', action_type: 'check_out', attendance_mark: 'present' },
    { status: 'success', reason: 'Verification successful', action_type: 'check_in', attendance_mark: 'present' },
    { status: 'failure', reason: 'Liveness check failed', action_type: 'check_in', attendance_mark: null },
    { status: 'failure', reason: 'Outside geofence boundary', action_type: 'check_in', attendance_mark: null },
    { status: 'failure', reason: 'Face match confidence too low (0.61 < 0.72)', action_type: 'check_in', attendance_mark: null },
  ];
  for (let i = 0; i < count; i++) {
    const t = teachers[i % teachers.length];
    const s = scenarios[i % scenarios.length];
    // Success scans within campus, failure scans slightly outside
    const isSuccess = s.status === 'success';
    const latOff = isSuccess ? randOffset(0.002) : randOffset(0.006);
    const lngOff = isSuccess ? randOffset(0.002) : randOffset(0.006);
    results.push({
      id: 100 + i,
      teacher_id: t.id,
      teacher_name: t.full_name,
      reg_no: t.reg_no,
      profile_pic: null,
      profile_pic_url: t.profile_pic_url,
      timestamp: new Date(Date.now() - 1000 * 60 * (i * 17 + 3)).toISOString(),
      status: s.status,
      reason: s.reason,
      action_type: s.action_type,
      attendance_mark: s.attendance_mark,
      latitude: parseFloat((CAMPUS_CENTER_LAT + latOff).toFixed(6)),
      longitude: parseFloat((CAMPUS_CENTER_LNG + lngOff).toFixed(6)),
      frames_count: isSuccess ? Math.floor(Math.random() * 8 + 3) : Math.floor(Math.random() * 3 + 1),
    });
  }
  return results;
}

const MOCK_LOGS_ALL = makeLogs(80);

// Campus polygon — NIT Jalandhar main campus rough boundary
const CAMPUS_POLYGON = [
  [31.2558, 75.7012],
  [31.2575, 75.7055],
  [31.2563, 75.7098],
  [31.2530, 75.7105],
  [31.2510, 75.7060],
  [31.2522, 75.7018],
  [31.2558, 75.7012],
];

const MOCK_ALERTS = [
  {
    id: 1,
    type: 'flagged_log',
    log_id: 'LOG201',
    teacher_id: 'TCH004',
    teacher_name: 'Mr. Karan Patel',
    reg_no: 'TCH004',
    profile_pic: null,
    profile_pic_url: 'https://i.pravatar.cc/150?img=65',
    title: 'Flagged Scan',
    description: 'Attendance scan flagged — location was outside the permitted geofence boundary by 47 metres.',
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
  },
  {
    id: 2,
    type: 'failed_log',
    log_id: 'LOG202',
    teacher_id: 'TCH003',
    teacher_name: 'Ms. Divya Nair',
    reg_no: 'TCH003',
    profile_pic: null,
    profile_pic_url: 'https://i.pravatar.cc/150?img=23',
    title: 'Failed Scan',
    description: 'Liveness detection failed 3 consecutive times within a 5-minute window. Possible spoof attempt.',
    timestamp: new Date(Date.now() - 1000 * 60 * 95).toISOString(),
  },
  {
    id: 3,
    type: 'spoof_detected',
    log_id: 'LOG203',
    teacher_id: 'TCH001',
    teacher_name: 'Dr. Priya Sharma',
    reg_no: 'TCH001',
    profile_pic: null,
    profile_pic_url: 'https://i.pravatar.cc/150?img=47',
    title: 'Spoof Detected',
    description: 'Sign-in attempted from an unregistered device. Device fingerprint did not match stored record.',
    timestamp: new Date(Date.now() - 1000 * 60 * 210).toISOString(),
  },
  {
    id: 4,
    type: 'unusual_activity',
    log_id: null,
    teacher_id: 'TCH008',
    teacher_name: 'Dr. Vikram Reddy',
    reg_no: 'TCH008',
    profile_pic: null,
    profile_pic_url: 'https://i.pravatar.cc/150?img=7',
    title: 'Unusual Activity',
    description: '5 failed scan attempts in 10 minutes. Account temporarily flagged for review.',
    timestamp: new Date(Date.now() - 1000 * 60 * 150).toISOString(),
  },
  {
    id: 5,
    type: 'abandoned_checkin',
    log_id: 'LOG205',
    teacher_id: 'TCH007',
    teacher_name: 'Prof. Lakshmi Iyer',
    reg_no: 'TCH007',
    profile_pic: null,
    profile_pic_url: 'https://i.pravatar.cc/150?img=41',
    title: 'Abandoned Check-In',
    description: 'Teacher checked in but did not check out within expected timeframe (8 hours). Session may be abandoned.',
    timestamp: new Date(Date.now() - 1000 * 60 * 480).toISOString(),
  },
];

const MOCK_AUDIT_LOGS = [
  { id: 1, admin_reg_no: 'ADM001', action: 'Teacher added', detail: 'Added TCH008 – Dr. Vikram Reddy', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString() },
  { id: 2, admin_reg_no: 'ADM001', action: 'Geofence updated', detail: 'Radius changed from 80m to 100m', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString() },
  { id: 3, admin_reg_no: 'ADM002', action: 'Alert resolved', detail: 'Alert #3 marked as resolved', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 8).toISOString() },
  { id: 4, admin_reg_no: 'ADM001', action: 'Settings changed', detail: 'Capture interval changed to 15 mins', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString() },
  { id: 5, admin_reg_no: 'ADM001', action: 'Teacher deactivated', detail: 'TCH006 – Mr. Rahul Gupta deactivated', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString() },
];

// ── API Mock Function ───────────────────────────────────────

/**
 * Central fetch wrapper — fully mocked for Vercel demo deployment.
 * No backend required. All data is realistic dummy data.
 */
async function api(path, method = 'GET', body = null) {
  let token = getToken();
  if (!token) {
    if (window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('/admin/') || window.location.pathname === '/') {
      if (typeof showLoginModal === 'function') showLoginModal();
    } else {
      window.location.href = 'index.html';
    }
    return null;
  }

  // Simulate network delay
  await new Promise(r => setTimeout(r, 180 + Math.random() * 120));

  // ── /admin/me ──────────────────────────────────────────────
  if (path.startsWith('/admin/me')) {
    const stored = getAdminData();
    return {
      id: 1,
      reg_no: stored?.reg_no || 'ADM001',
      name: stored?.name || 'Head Admin',
      is_head_admin: true,
      profile_pic: null,
      created_at: '2024-07-01T00:00:00Z',
    };
  }

  // ── /admin/stats ───────────────────────────────────────────
  if (path.startsWith('/admin/stats')) {
    return {
      total_teachers: totalTeachers,
      inactive_teachers: inactiveTeachers,
      today_success: todaySuccess,
      today_failure: todayFailure,
      yesterday_success: 27,
      yesterday_failure: 6,
      overall_success_rate: 88.6,
      total_logs: 1842,
      success_trend: successTrend,
      failure_trend: failureTrend,
      trend_month: monthName,
      trend_days: 30,
      failure_by_stage: {
        'Liveness': 8,
        'Geofence': 5,
        'Face Match': 6,
        'Network': 2,
      },
    };
  }

  // ── /admin/alerts ──────────────────────────────────────────
  if (path.startsWith('/admin/alerts/resolve') && method === 'POST') {
    return { success: true };
  }
  if (path.startsWith('/admin/alerts')) {
    if (method === 'POST') return { success: true };
    return { alerts: MOCK_ALERTS };
  }

  // ── /admin/attendance ──────────────────────────────────────
  if (path.startsWith('/admin/attendance')) {
    const urlParams = new URLSearchParams(path.split('?')[1] || '');
    const perPage = parseInt(urlParams.get('per_page')) || 20;
    const page = parseInt(urlParams.get('page')) || 1;
    const logs = MOCK_LOGS_ALL.slice((page - 1) * perPage, page * perPage);
    return {
      logs,
      total: MOCK_LOGS_ALL.length,
      page,
      per_page: perPage,
      pages: Math.ceil(MOCK_LOGS_ALL.length / perPage),
    };
  }

  // ── /admin/geofence ────────────────────────────────────────
  if (path.startsWith('/admin/geofence')) {
    if (method === 'PUT') return { success: true };
    return {
      center_lat: CAMPUS_CENTER_LAT,
      center_lng: CAMPUS_CENTER_LNG,
      radius_meters: 200,
      is_enabled: true,
      campus_name: 'NIT Jalandhar — Main Campus',
      polygon: CAMPUS_POLYGON,
      geofence_config: {
        mode: 2,
        main_polygon: CAMPUS_POLYGON,
        sub_polygons: [
          {
            polygon: [
              [31.2545, 75.7020],
              [31.2555, 75.7040],
              [31.2545, 75.7055],
              [31.2535, 75.7040],
            ],
            departments: ['Computer Science', 'Electronics'],
            color: '#7c3aed',
          },
          {
            polygon: [
              [31.2530, 75.7060],
              [31.2545, 75.7075],
              [31.2535, 75.7090],
              [31.2520, 75.7075],
            ],
            departments: ['Mechanical', 'Civil'],
            color: '#ef4444',
          },
        ],
        checkpoints: [
          { lat: 31.2558, lng: 75.7012, radius: 30, label: 'Main Gate' },
          { lat: 31.2536, lng: 75.7037, radius: 25, label: 'Admin Block' },
          { lat: 31.2520, lng: 75.7060, radius: 20, label: 'Library' },
        ],
      },
    };
  }

  // ── /admin/settings ────────────────────────────────────────
  if (path.startsWith('/admin/settings')) {
    if (method === 'PATCH') return { success: true };
    return {
      capture_interval_mins: 15,
      offline_sync_hours: 24,
      allow_fake_location: false,
      enable_liveness: true,
      liveness_confidence_threshold: 0.85,
      face_match_threshold: 0.72,
      max_login_attempts: 5,
      session_timeout_mins: 60,
      timezone: 'Asia/Kolkata',
      institute_name: 'GeoFace Institute of Technology',
      academic_year: '2025–2026',
    };
  }

  // ── /admin/admins ──────────────────────────────────────────
  if (path.startsWith('/admin/admins')) {
    if (method === 'POST' || method === 'DELETE' || method === 'PATCH') return { success: true };
    return {
      admins: [
        { id: 1, reg_no: 'ADM001', name: 'Head Admin', is_head_admin: true, created_at: '2024-07-01T00:00:00Z' },
        { id: 2, reg_no: 'ADM002', name: 'Rohan Das', is_head_admin: false, created_at: '2024-08-10T10:00:00Z' },
      ],
    };
  }

  // ── /admin/teachers/:id/reset-device ──────────────────────
  if (path.includes('/reset-device')) return { success: true };

  // ── /admin/teachers/:id ────────────────────────────────────
  const teacherMatch = path.match(/\/admin\/teachers\/(\d+)$/);
  if (teacherMatch) {
    const id = parseInt(teacherMatch[1]);
    if (method === 'DELETE' || method === 'PATCH') return { success: true };
    const t = MOCK_TEACHERS.find(x => x.id === id);
    return t || null;
  }

  // ── /admin/teachers (list) ────────────────────────────────
  if (path.startsWith('/admin/teachers')) {
    if (method === 'POST') return { success: true, teacher: MOCK_TEACHERS[0] };
    return { teachers: MOCK_TEACHERS };
  }

  // ── /admin/logs (audit) ────────────────────────────────────
  if (path.startsWith('/admin/logs')) {
    return { logs: MOCK_AUDIT_LOGS };
  }

  // ── /admin/encode-face ────────────────────────────────────
  if (path.startsWith('/admin/encode-face')) {
    return { success: true, message: 'Face encoded and registered successfully.' };
  }

  // ── /admin/generate-totp ──────────────────────────────────
  if (path.startsWith('/admin/generate-totp')) {
    return { totp_secret: 'JBSWY3DPEHPK3PXP', qr_url: 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=otpauth://totp/GeoFace:ADM001?secret=JBSWY3DPEHPK3PXP' };
  }

  // ── /admin/devices/reset-all ──────────────────────────────
  if (path.startsWith('/admin/devices/reset-all')) {
    return { success: true };
  }

  // Fallback
  return { success: true };
}

// ── Login / Auth ────────────────────────────────────────────

async function adminLogin() {
  const reg_no = document.getElementById('admin-reg-no').value.trim();
  const password = document.getElementById('admin-password').value;
  const errEl = document.getElementById('login-error');
  errEl.style.display = 'none';

  const btn = document.getElementById('btn-login');
  btn.disabled = true;
  btn.textContent = 'Signing in…';

  await new Promise(r => setTimeout(r, 600));

  btn.disabled = false;
  btn.textContent = 'Login';

  if (!reg_no || !password) {
    errEl.textContent = 'Please enter your credentials';
    errEl.style.display = 'block';
    return;
  }

  setToken('demo_token_geofence_2025');
  sessionStorage.setItem(ADMIN_DATA_KEY, JSON.stringify({
    id: 1,
    reg_no: reg_no,
    name: reg_no === 'ADM001' ? 'Head Admin' : reg_no,
    is_head_admin: true,
  }));
  hideLoginModal();
  window.location.reload();
}

function adminSignOut() {
  clearToken();
  if (window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('/admin/') || window.location.pathname === '/') {
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

// ── Utilities ───────────────────────────────────────────────
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
    background:${type === 'error' ? '#7f1d1d' : type === 'success' ? '#052e16' : '#1e293b'};
    color:${type === 'error' ? '#fca5a5' : type === 'success' ? '#86efac' : '#f1f5f9'};
    border:1px solid ${type === 'error' ? '#ef4444' : type === 'success' ? '#22c55e' : '#334155'};
    padding:12px 20px;border-radius:10px;font-size:13px;
    box-shadow:0 8px 24px rgba(0,0,0,0.4);
    animation:slideIn 0.25s ease;
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ── Custom UI Modals ─────────────────────────────────────────
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
