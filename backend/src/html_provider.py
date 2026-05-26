def get_spa_html() -> str:
    return """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Queue — Система управления очередью</title>
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --bg:        #f5f4ef;
            --surface:   #ffffff;
            --surface2:  #f0ede6;
            --border:    #e2ddd6;
            --border2:   #ccc8c0;
            --text:      #1a1a18;
            --text-2:    #6b6860;
            --text-3:    #9e9b95;
            --accent:    #d97706;
            --accent-bg: #fef3c7;
            --green:     #16a34a;
            --green-bg:  #dcfce7;
            --red:       #dc2626;
            --red-bg:    #fee2e2;
            --blue:      #2563eb;
            --blue-bg:   #dbeafe;
            --shadow:    0 1px 3px rgba(0,0,0,.08), 0 4px 12px rgba(0,0,0,.06);
            --shadow-lg: 0 8px 24px rgba(0,0,0,.10);
            --radius:    12px;
            --radius-sm: 8px;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 0 16px 40px;
            -webkit-font-smoothing: antialiased;
        }

        /* ── Layout ── */
        .page { display: none; }
        .page.active { display: flex; flex-direction: column; align-items: center; min-height: 100vh; }

        .center-wrap {
            width: 100%;
            max-width: 440px;
            padding-top: 60px;
        }

        /* ── Logo / Header ── */
        .logo-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 32px;
        }
        .logo-icon {
            width: 36px; height: 36px;
            background: var(--text);
            border-radius: 9px;
            display: flex; align-items: center; justify-content: center;
            flex-shrink: 0;
        }
        .logo-icon svg { width: 20px; height: 20px; fill: var(--bg); }
        .logo-title { font-size: 1.1rem; font-weight: 600; letter-spacing: -.2px; }
        .logo-sub { font-size: .8rem; color: var(--text-3); margin-top: 1px; }

        .page-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            max-width: 640px;
            padding: 16px 0 0;
            margin-bottom: 24px;
        }
        .page-header .room-label {
            font-size: .85rem;
            color: var(--text-2);
            font-weight: 500;
        }
        .page-header .room-id {
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: .5px;
            font-family: "SF Mono", "Fira Code", monospace;
        }

        /* ── Card ── */
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 24px;
            box-shadow: var(--shadow);
            margin-bottom: 16px;
        }
        .card-title {
            font-size: .7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: .08em;
            color: var(--text-3);
            margin-bottom: 16px;
        }

        /* ── Form ── */
        .field-label {
            font-size: .8rem;
            font-weight: 500;
            color: var(--text-2);
            margin-bottom: 6px;
            display: block;
        }
        input[type="text"] {
            width: 100%;
            padding: 11px 14px;
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            color: var(--text);
            font-size: 1rem;
            font-family: "SF Mono", "Fira Code", monospace;
            font-weight: 600;
            letter-spacing: .1em;
            text-transform: uppercase;
            outline: none;
            transition: border-color .15s, box-shadow .15s;
            margin-bottom: 12px;
        }
        input[type="text"]:focus {
            border-color: var(--border2);
            box-shadow: 0 0 0 3px rgba(0,0,0,.06);
        }
        input[type="text"]::placeholder { text-transform: none; letter-spacing: 0; color: var(--text-3); font-weight: 400; font-family: inherit; }

        /* ── Buttons ── */
        .btn {
            display: flex; align-items: center; justify-content: center; gap: 7px;
            width: 100%; padding: 11px 18px;
            border: 1px solid transparent;
            border-radius: var(--radius-sm);
            font-size: .9rem; font-weight: 600;
            cursor: pointer;
            transition: opacity .15s, transform .08s;
            text-decoration: none;
            margin-bottom: 8px;
        }
        .btn:last-child { margin-bottom: 0; }
        .btn:active { transform: scale(.98); }
        .btn:disabled { opacity: .45; cursor: not-allowed; }

        .btn-primary { background: var(--text); color: var(--bg); border-color: var(--text); }
        .btn-primary:hover:not(:disabled) { opacity: .88; }

        .btn-secondary { background: var(--surface); color: var(--text-2); border-color: var(--border); }
        .btn-secondary:hover:not(:disabled) { background: var(--surface2); }

        .btn-danger { background: var(--red-bg); color: var(--red); border-color: #fca5a5; }
        .btn-danger:hover:not(:disabled) { background: #fecaca; }

        .btn-success { background: var(--green-bg); color: var(--green); border-color: #86efac; }
        .btn-success:hover:not(:disabled) { background: #bbf7d0; }

        .btn-sm { padding: 7px 14px; font-size: .8rem; width: auto; margin-bottom: 0; }

        /* ── Divider ── */
        .divider {
            display: flex; align-items: center; gap: 12px;
            color: var(--text-3); font-size: .75rem;
            margin: 16px 0;
        }
        .divider::before, .divider::after {
            content: ""; flex: 1;
            height: 1px; background: var(--border);
        }

        /* ── Fingerprint badge ── */
        .fp-badge {
            display: flex; align-items: center; gap: 8px;
            padding: 10px 14px;
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            margin-top: 16px;
        }
        .fp-badge .fp-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); flex-shrink: 0; }
        .fp-badge .fp-label { font-size: .72rem; color: var(--text-3); }
        .fp-badge .fp-value { font-size: .75rem; font-family: "SF Mono","Fira Code",monospace; color: var(--text-2); font-weight: 600; word-break: break-all; }

        /* ── Ticket display ── */
        .ticket-hero {
            text-align: center;
            padding: 28px 0 20px;
        }
        .ticket-hero .ticket-label {
            font-size: .7rem; font-weight: 600; text-transform: uppercase;
            letter-spacing: .1em; color: var(--text-3); margin-bottom: 8px;
        }
        .ticket-hero .ticket-num {
            font-size: 3.8rem; font-weight: 800;
            letter-spacing: -2px; line-height: 1;
            color: var(--text);
            font-family: "SF Mono","Fira Code",monospace;
        }
        .ticket-hero .ticket-num.serving { color: var(--green); }

        /* ── Stats rows ── */
        .stat-row {
            display: flex; justify-content: space-between; align-items: center;
            padding: 11px 0;
            border-top: 1px solid var(--border);
            font-size: .875rem;
        }
        .stat-row:first-child { border-top: none; }
        .stat-label { color: var(--text-2); }
        .stat-value { font-weight: 600; }
        .stat-value.green { color: var(--green); }
        .stat-value.accent { color: var(--accent); }
        .stat-value.blue { color: var(--blue); }

        /* ── Badge chip ── */
        .chip {
            display: inline-flex; align-items: center; gap: 5px;
            padding: 3px 10px;
            border-radius: 100px;
            font-size: .72rem; font-weight: 600;
        }
        .chip.serving { background: var(--green-bg); color: var(--green); }
        .chip.waiting { background: var(--surface2); color: var(--text-2); }
        .chip-dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }

        /* ── Timer ── */
        .timer-display {
            font-family: "SF Mono","Fira Code",monospace;
            font-size: 1.6rem; font-weight: 700;
            text-align: center;
            color: var(--text-2);
            letter-spacing: .05em;
            margin: 4px 0 20px;
        }
        .timer-display.active { color: var(--text); }

        /* ── Admin current ticket ── */
        .adm-ticket-big {
            font-size: 2.8rem; font-weight: 800;
            font-family: "SF Mono","Fira Code",monospace;
            text-align: center;
            letter-spacing: -1px;
            color: var(--text);
            margin: 8px 0;
        }

        /* ── Queue line ── */
        .queue-line {
            display: flex; gap: 8px; flex-wrap: wrap;
            min-height: 38px; align-items: center;
            padding: 4px 0;
        }
        .q-chip {
            display: inline-flex; align-items: center;
            padding: 5px 12px;
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: 100px;
            font-size: .8rem; font-weight: 600;
            font-family: "SF Mono","Fira Code",monospace;
            color: var(--text-2);
        }
        .q-chip.first { background: var(--accent-bg); border-color: #fcd34d; color: var(--accent); }
        .queue-empty { font-size: .85rem; color: var(--text-3); font-style: italic; }

        /* ── Toast ── */
        .toast-container {
            position: fixed; top: 16px; right: 16px;
            z-index: 9999; width: 320px;
            display: flex; flex-direction: column; gap: 8px;
        }
        .toast {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            box-shadow: var(--shadow-lg);
            padding: 12px 16px;
            display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;
            animation: toastIn .2s ease-out;
        }
        .toast.error { border-left: 3px solid var(--red); }
        .toast.success { border-left: 3px solid var(--green); }
        .toast.info { border-left: 3px solid var(--blue); }
        .toast-msg { font-size: .85rem; line-height: 1.4; color: var(--text); }
        .toast-close { background: none; border: none; cursor: pointer; color: var(--text-3); font-size: 1rem; padding: 0; line-height: 1; flex-shrink: 0; margin: 0; width: auto; }
        .toast-close:hover { color: var(--text); }
        @keyframes toastIn { from { opacity: 0; transform: translateX(8px); } to { opacity: 1; transform: none; } }

        /* ── Error inline ── */
        .inline-error {
            background: var(--red-bg);
            border: 1px solid #fca5a5;
            border-radius: var(--radius-sm);
            color: var(--red);
            padding: 10px 14px;
            font-size: .85rem;
            font-weight: 500;
            margin-bottom: 12px;
            display: none;
        }

        /* ── Spinner ── */
        .spinner {
            width: 16px; height: 16px;
            border: 2px solid currentColor;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin .6s linear infinite;
            display: inline-block;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* ── WS indicator ── */
        .ws-dot {
            width: 7px; height: 7px; border-radius: 50%;
            background: var(--text-3);
            display: inline-block;
            transition: background .3s;
        }
        .ws-dot.connected { background: var(--green); }

        /* ── Responsive ── */
        @media (max-width: 480px) {
            .center-wrap { padding-top: 32px; }
            .ticket-hero .ticket-num { font-size: 3rem; }
            .adm-ticket-big { font-size: 2.2rem; }
            .toast-container { width: calc(100% - 32px); right: 16px; }
        }
    </style>
</head>
<body>

<div class="toast-container" id="toast-box"></div>

<!-- ══════════════════════════════════════════
     PAGE: MAIN (login)
══════════════════════════════════════════ -->
<div id="page-main" class="page active">
  <div class="center-wrap">
    <div class="logo-row">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 6h16M4 10h10M4 14h12M4 18h8"/>
          <path d="M4 6h16M4 10h10M4 14h12M4 18h8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div>
        <div class="logo-title">Queue</div>
        <div class="logo-sub">Система управления очередью</div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">Войти в комнату</div>
      <div id="main-error" class="inline-error"></div>
      <label class="field-label" for="input-room-id">ID комнаты</label>
      <input type="text" id="input-room-id" placeholder="6 символов" maxlength="6" autocomplete="off">
      <button class="btn btn-primary" id="btn-join" onclick="userJoinRoom()">
        Войти в очередь
      </button>
      <div class="divider">или</div>
      <button class="btn btn-secondary" id="btn-create" onclick="adminCreateRoom()">
        Создать комнату (администратор)
      </button>
    </div>

    <div class="fp-badge">
      <div class="fp-dot"></div>
      <div>
        <div class="fp-label">Ваш клиентский ID</div>
        <div class="fp-value" id="display-my-id"></div>
      </div>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════
     PAGE: USER
══════════════════════════════════════════ -->
<div id="page-user" class="page">
  <div class="page-header" style="max-width:440px; width:100%;">
    <div>
      <div class="room-label">Комната</div>
      <div class="room-id" id="user-room-id">——</div>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
      <span class="ws-dot" id="user-ws-dot" title="WebSocket"></span>
      <button class="btn btn-danger btn-sm" onclick="leaveRoom()">Покинуть</button>
    </div>
  </div>
  <div style="width:100%;max-width:440px;">
    <div class="card">
      <div class="ticket-hero">
        <div class="ticket-label">Ваш талон</div>
        <div class="ticket-num" id="user-ticket-num">—</div>
      </div>
      <div class="stat-row">
        <span class="stat-label">Ваша позиция</span>
        <span class="stat-value blue" id="m-position">—</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Статус очереди</span>
        <span id="m-room-status-wrap">
          <span class="chip waiting" id="m-room-status-chip">
            <span class="chip-dot"></span> Ожидание
          </span>
        </span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Время обслуживания</span>
        <span class="stat-value green" id="m-user-timer">—</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Ср. время обслуживания</span>
        <span class="stat-value" id="m-avg-serve">—</span>
      </div>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════
     PAGE: ADMIN
══════════════════════════════════════════ -->
<div id="page-admin" class="page">
  <div class="page-header" style="max-width:440px; width:100%;">
    <div>
      <div class="room-label">Вы — администратор</div>
      <div class="room-id" id="admin-room-id">——</div>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
      <span class="ws-dot" id="admin-ws-dot" title="WebSocket"></span>
      <button class="btn btn-danger btn-sm" onclick="adminCloseRoom()">Закрыть</button>
    </div>
  </div>
  <div style="width:100%;max-width:440px;">
    <div id="adm-queues-container">
      <div class="card">
        <button class="btn btn-secondary" disabled>
          <span class="spinner"></span> Загрузка...
        </button>
      </div>
    </div>
    <div style="margin-bottom:16px;">
      <button class="btn btn-secondary" onclick="adminAddQueue()">+ Добавить очередь</button>
    </div>
    <div class="card">
      <div class="card-title">Статистика сессии</div>
      <div class="stat-row">
        <span class="stat-label">Всего обслужено</span>
        <span class="stat-value" id="stats-completed">—</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Ср. время обслуживания</span>
        <span class="stat-value" id="stats-serve">—</span>
      </div>
    </div>
  </div>
</div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
const MY_ID_KEY   = 'q_client_fp';
const ROOM_KEY    = 'q_room_id';
const ROLE_KEY    = 'q_role';

// fingerprint survives across tabs/sessions — it's not secret, just an identity
let myFp = localStorage.getItem(MY_ID_KEY);
if (!myFp) {
    myFp = 'cli_' + Math.random().toString(36).substring(2, 11).toUpperCase();
    localStorage.setItem(MY_ID_KEY, myFp);
}
document.getElementById('display-my-id').textContent = myFp;

let currentRoomId = '';
let currentRole   = '';
// access token lives only in memory — never written to localStorage/sessionStorage
let accessToken   = '';
let ws            = null;
let uiTimer       = null;
let currentElapsed = 0;
let hadTicket = false;      // becomes true once we see a ticket; enables redirect-on-removal
let leftVoluntarily = false; // set when user clicks "Покинуть" to suppress "served" toast

// ── Token management ───────────────────────────────────────────────────────
async function ensureToken() {
    if (accessToken) return;
    // try refresh cookie first (httpOnly, no JS access — browser sends it automatically)
    const refreshRes = await fetch('/api/v1/auth/refresh', { method: 'POST', credentials: 'include' });
    if (refreshRes.ok) {
        const data = await refreshRes.json();
        accessToken = data.access_token;
        return;
    }
    // no valid refresh cookie — get a new token pair
    const res = await fetch(`/api/v1/auth/token?fingerprint=${encodeURIComponent(myFp)}`, {
        method: 'POST',
        credentials: 'include',
    });
    if (!res.ok) throw new Error('Ошибка получения токена');
    const data = await res.json();
    accessToken = data.access_token;
}

function setToken(token) {
    accessToken = token;
}

function authHeaders() {
    return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${accessToken}` };
}

// ── API helpers ────────────────────────────────────────────────────────────
async function apiFetch(url, options = {}) {
    await ensureToken();
    options.credentials = 'include';
    options.headers = { ...authHeaders(), ...(options.headers || {}) };
    const res = await fetch(url, options);
    if (res.status === 401) {
        // token expired — try refresh once
        const refreshRes = await fetch('/api/v1/auth/refresh', { method: 'POST', credentials: 'include' });
        if (refreshRes.ok) {
            const data = await refreshRes.json();
            accessToken = data.access_token;
            options.headers = { ...authHeaders(), ...(options.headers || {}) };
            return fetch(url, options);
        }
        accessToken = '';
        throw new Error('Сессия истекла. Попробуйте снова.');
    }
    return res;
}

// ── Pages ──────────────────────────────────────────────────────────────────
function showPage(id) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}

function goMain() {
    stopPing();
    if (ws) { ws.close(); ws = null; }
    clearInterval(uiTimer);
    currentRoomId = '';
    currentRole   = '';
    hadTicket        = false;
    leftVoluntarily  = false;
    localStorage.removeItem(ROOM_KEY);
    localStorage.removeItem(ROLE_KEY);
    showPage('page-main');
    document.getElementById('main-error').style.display = 'none';
}

// ── Toast ──────────────────────────────────────────────────────────────────
function toast(msg, type = 'info') {
    const box  = document.getElementById('toast-box');
    const el   = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `<span class="toast-msg">${msg}</span><button class="toast-close" onclick="this.parentElement.remove()">&times;</button>`;
    box.appendChild(el);
    setTimeout(() => el.remove(), 7000);
}

function showMainError(msg) {
    const el = document.getElementById('main-error');
    el.textContent = msg;
    el.style.display = 'block';
}

// ── Actions: Main screen ───────────────────────────────────────────────────
async function userJoinRoom() {
    const rId = document.getElementById('input-room-id').value.trim().toUpperCase();
    if (!rId || rId.length < 4) { showMainError('Введите корректный ID комнаты'); return; }

    const btn = document.getElementById('btn-join');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Подключение...';

    try {
        await ensureToken();
        const res = await apiFetch('/api/v1/queue/ticket', {
            method: 'POST',
            body: JSON.stringify({ room_id: rId }),
        });
        const data = await res.json();
        if (!res.ok) { showMainError(data.detail || 'Комната не найдена'); return; }

        currentRoomId = rId;
        localStorage.setItem(ROOM_KEY, currentRoomId);

        if (data.is_admin) {
            setToken(data.access_token);
            currentRole = 'admin';
            localStorage.setItem(ROLE_KEY, currentRole);
            enterAdminPage();
        } else {
            currentRole = 'user';
            localStorage.setItem(ROLE_KEY, currentRole);
            enterUserPage();
        }
        initWebSocket();
    } catch (e) {
        showMainError(e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Войти в очередь';
    }
}

async function adminCreateRoom() {
    const btn = document.getElementById('btn-create');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Создание...';

    try {
        await ensureToken();
        const res = await apiFetch('/api/v1/rooms', { method: 'POST' });
        const data = await res.json();
        if (!res.ok) { showMainError(data.detail || 'Ошибка создания комнаты'); return; }

        setToken(data.access_token);
        currentRoomId = data.room_id;
        currentRole   = 'admin';
        localStorage.setItem(ROOM_KEY, currentRoomId);
        localStorage.setItem(ROLE_KEY, currentRole);
        enterAdminPage();
        initWebSocket();
    } catch (e) {
        showMainError(e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Создать комнату (администратор)';
    }
}

// ── Enter screens ──────────────────────────────────────────────────────────
function enterUserPage() {
    document.getElementById('user-room-id').textContent = currentRoomId;
    resetUserDOM();
    showPage('page-user');
}

function enterAdminPage() {
    document.getElementById('admin-room-id').textContent = currentRoomId;
    resetAdminDOM();
    showPage('page-admin');
}

function resetUserDOM() {
    document.getElementById('user-ticket-num').textContent = '—';
    document.getElementById('m-position').textContent = '—';
    document.getElementById('m-user-timer').textContent = '—';
    setStatusChip('waiting');
}

function resetAdminDOM() {
    document.getElementById('adm-queues-container').innerHTML =
        '<div class="card"><button class="btn btn-secondary" disabled><span class="spinner"></span> Загрузка...</button></div>';
}

// ── Leave / Close ──────────────────────────────────────────────────────────
async function leaveRoom() {
    leftVoluntarily = true;
    try {
        await apiFetch('/api/v1/queue/leave', {
            method: 'POST',
            body: JSON.stringify({ room_id: currentRoomId }),
        });
    } catch (_) {}
    goMain();
}

async function adminCloseRoom() {
    if (!confirm('Закрыть комнату и завершить приём?')) return;
    try {
        await apiFetch(`/api/v1/rooms/${currentRoomId}`, { method: 'DELETE' });
    } catch (_) {}
    goMain();
}

// ── Admin actions ──────────────────────────────────────────────────────────
async function adminNext(queueLabel) {
    const btn = document.querySelector(`#adm-action-slot-${queueLabel} button`);
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>'; }
    try {
        const res = await apiFetch('/api/v1/admin/next', {
            method: 'POST',
            body: JSON.stringify({ room_id: currentRoomId, queue_label: queueLabel }),
        });
        if (!res.ok) {
            const d = await res.json();
            toast(d.detail || 'Ошибка', 'error');
            if (btn) { btn.disabled = false; btn.textContent = `Вызвать следующего · ${queueLabel}`; }
        }
    } catch (e) { toast(e.message, 'error'); }
}

async function adminComplete(queueLabel) {
    const btn = document.querySelector(`#adm-action-slot-${queueLabel} button`);
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>'; }
    try {
        const res = await apiFetch('/api/v1/admin/complete', {
            method: 'POST',
            body: JSON.stringify({ room_id: currentRoomId, queue_label: queueLabel }),
        });
        if (!res.ok) {
            const d = await res.json();
            toast(d.detail || 'Ошибка', 'error');
            if (btn) { btn.disabled = false; btn.textContent = `Завершить · ${queueLabel}`; }
        }
    } catch (e) { toast(e.message, 'error'); }
}

async function adminAddQueue() {
    try {
        const res = await apiFetch('/api/v1/admin/queue/add', {
            method: 'POST',
            body: JSON.stringify({ room_id: currentRoomId }),
        });
        const d = await res.json();
        if (!res.ok) { toast(d.detail || 'Ошибка', 'error'); return; }
        toast(`Очередь ${d.queue_label} добавлена`, 'success');
        fetchRoomState();
    } catch (e) { toast(e.message, 'error'); }
}

async function adminRemoveQueue(queueLabel) {
    if (!confirm(`Удалить очередь ${queueLabel}?`)) return;
    try {
        const res = await apiFetch('/api/v1/admin/queue/remove', {
            method: 'DELETE',
            body: JSON.stringify({ room_id: currentRoomId, queue_label: queueLabel }),
        });
        const d = await res.json();
        if (!res.ok) { toast(d.detail || 'Ошибка', 'error'); return; }
        toast(`Очередь ${queueLabel} удалена`, 'success');
        fetchRoomState();
    } catch (e) { toast(e.message, 'error'); }
}

async function loadAdminStats() {
    try {
        const res = await apiFetch(`/api/v1/admin/stats/${currentRoomId}`);
        if (!res.ok) return;
        const d = await res.json();
        const fmt = s => s < 60 ? `${s}с` : `${Math.floor(s/60)}м ${s%60}с`;
        document.getElementById('stats-completed').textContent = d.completed ?? '—';
        document.getElementById('stats-serve').textContent = d.avg_serve_seconds ? fmt(d.avg_serve_seconds) : '—';
    } catch (_) {}
}

// ── WebSocket ──────────────────────────────────────────────────────────────
function initWebSocket() {
    if (ws) { ws.close(); ws = null; }
    if (!accessToken) { ensureToken().then(initWebSocket); return; }
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${location.host}/ws/room/${currentRoomId}?token=${encodeURIComponent(accessToken)}`);

    const userDot  = document.getElementById('user-ws-dot');
    const adminDot = document.getElementById('admin-ws-dot');
    const setDot   = (connected) => {
        [userDot, adminDot].forEach(d => { if (d) d.className = 'ws-dot' + (connected ? ' connected' : ''); });
    };

    ws.onopen    = () => { setDot(true); fetchRoomState(); startPing(); };
    ws.onclose   = () => { setDot(false); stopPing(); scheduleReconnect(); };
    ws.onerror   = () => { setDot(false); stopPing(); };

    ws.onmessage = (event) => {
        if (event.data === 'pong') return;
        let msg;
        try { msg = JSON.parse(event.data); } catch { return; }

        if (msg.type === 'welcome' && msg.data) {
            handleState(msg.data);
            return;
        }
        if (msg.type === 'update') {
            if (msg.data && msg.data.room_closed) {
                toast('Комната закрыта администратором', 'info');
                goMain();
                return;
            }
            fetchRoomState();
        }
    };
}

let reconnectTimer = null;
let pingTimer = null;

function scheduleReconnect() {
    if (!currentRoomId) return;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(() => {
        if (currentRoomId && document.visibilityState !== 'hidden') initWebSocket();
    }, 3000);
}

function startPing() {
    if (pingTimer) clearInterval(pingTimer);
    pingTimer = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) ws.send('ping');
    }, 25000);
}

function stopPing() {
    if (pingTimer) { clearInterval(pingTimer); pingTimer = null; }
}

async function fetchRoomState() {
    if (!currentRoomId) return;
    try {
        const res = await apiFetch(`/api/v1/rooms/${currentRoomId}/state?user_id=${encodeURIComponent(myFp)}`);
        if (!res.ok) return;
        const data = await res.json();
        handleState(data);
    } catch (_) {}
}

// ── State rendering ────────────────────────────────────────────────────────
function handleState(data) {
    if (data.room_closed) {
        toast('Комната закрыта', 'info');
        goMain();
        return;
    }
    if (data.room_id && data.room_id !== currentRoomId) return;

    if (currentRole === 'user')  renderUser(data);
    if (currentRole === 'admin') { renderAdmin(data); loadAdminStats(); }
}

function setStatusChip(status) {
    const chip = document.getElementById('m-room-status-chip');
    if (!chip) return;
    if (status === 'serving') {
        chip.className = 'chip serving';
        chip.innerHTML = '<span class="chip-dot"></span> Идёт приём';
    } else {
        chip.className = 'chip waiting';
        chip.innerHTML = '<span class="chip-dot"></span> Ожидание';
    }
}

function renderUser(data) {
    const ctx = data.client_context || {};

    if (ctx.ticket_label && ctx.ticket_label !== '--') hadTicket = true;

    // Redirect only after we've seen a ticket (avoids redirect on first load race)
    if (hadTicket && ctx.should_redirect) {
        if (!leftVoluntarily) toast('Вы были обслужены. Спасибо!', 'success');
        goMain();
        return;
    }

    const ticketEl = document.getElementById('user-ticket-num');
    ticketEl.textContent = ctx.ticket_label || '—';
    ticketEl.className   = 'ticket-num' + (ctx.position_label === 'На приеме' ? ' serving' : '');

    const queueLabel = ctx.queue_label ? ` · Очередь ${ctx.queue_label}` : '';
    document.getElementById('m-position').textContent = ctx.position_label ? ctx.position_label + queueLabel : '—';
    setStatusChip(data.current_status);
    updateTimer(data, ['m-user-timer']);

    const fmt = s => s < 60 ? `${s}с` : `${Math.floor(s/60)}м ${s%60}с`;
    const avgEl = document.getElementById('m-avg-serve');
    if (avgEl) avgEl.textContent = data.avg_serve_seconds ? fmt(data.avg_serve_seconds) : '—';
}

function renderAdmin(data) {
    const ctx = data.admin_context || {};
    const queues = ctx.queues || [];
    const container = document.getElementById('adm-queues-container');
    if (!container) return;

    container.innerHTML = queues.map(q => `
        <div class="card" style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1.1rem;font-weight:700;font-family:monospace;">Очередь ${q.label}</span>
                    <span class="chip ${q.status}">${q.status === 'serving' ? '● Идёт приём' : '○ Ожидание'}</span>
                </div>
                <button class="btn btn-secondary btn-sm" onclick="adminRemoveQueue('${q.label}')">✕</button>
            </div>
            <div class="adm-ticket-big" style="font-size:2rem;">${q.current_ticket}</div>
            ${q.status === 'serving' ? `<div class="timer-display active" id="adm-timer-${q.label}">00:00</div>` : ''}
            <div id="adm-action-slot-${q.label}" style="margin:12px 0 8px;">
                ${q.status === 'serving'
                    ? `<button class="btn btn-danger" onclick="adminComplete('${q.label}')">Завершить · ${q.label}</button>`
                    : `<button class="btn btn-success" onclick="adminNext('${q.label}')">Вызвать следующего · ${q.label}</button>`
                }
            </div>
            <div class="queue-line">
                ${q.length === 0
                    ? '<span class="queue-empty">Очередь пуста</span>'
                    : `<span class="q-chip">${q.length} чел. ожидают</span>`
                }
            </div>
        </div>
    `).join('');

    clearInterval(uiTimer);
    const servingQueues = queues.filter(q => q.status === 'serving');
    if (servingQueues.length > 0) {
        currentElapsed = (ctx.elapsed_time ?? data.elapsed_time) || 0;
        servingQueues.forEach(q => {
            const el = document.getElementById(`adm-timer-${q.label}`);
            if (el) el.textContent = fmtTime(currentElapsed);
        });
        uiTimer = setInterval(() => {
            currentElapsed++;
            servingQueues.forEach(q => {
                const el = document.getElementById(`adm-timer-${q.label}`);
                if (el) el.textContent = fmtTime(currentElapsed);
            });
        }, 1000);
    }
}

// ── Timer ──────────────────────────────────────────────────────────────────
function updateTimer(data, ids) {
    clearInterval(uiTimer);
    const els = ids.map(id => document.getElementById(id)).filter(Boolean);
    if (data.current_status === 'serving') {
        currentElapsed = data.elapsed_time || 0;
        els.forEach(el => { el.textContent = fmtTime(currentElapsed); el.classList.add('active'); });
        uiTimer = setInterval(() => {
            currentElapsed++;
            els.forEach(el => el.textContent = fmtTime(currentElapsed));
        }, 1000);
    } else {
        els.forEach(el => { el.textContent = '—'; el.classList.remove('active'); });
    }
}

function fmtTime(s) {
    return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
}

// ── Restore session ────────────────────────────────────────────────────────
async function restoreSession() {
    const savedRoom = localStorage.getItem(ROOM_KEY);
    const savedRole = localStorage.getItem(ROLE_KEY);
    if (!savedRoom || !savedRole) return;

    currentRoomId = savedRoom;

    try {
        await ensureToken();
    } catch (_) {
        goMain();
        return;
    }

    if (savedRole === 'admin') {
        // Re-verify admin rights: re-enter the room and check the server response.
        // After a service restart the JWT secret may have changed, or the admin token
        // may have expired — in either case we get a fresh token from take_ticket.
        try {
            const res = await apiFetch('/api/v1/queue/ticket', {
                method: 'POST',
                body: JSON.stringify({ room_id: savedRoom }),
            });
            const data = await res.json();
            if (res.ok && data.is_admin) {
                setToken(data.access_token);
                currentRole = 'admin';
                localStorage.setItem(ROLE_KEY, 'admin');
                enterAdminPage();
                initWebSocket();
                return;
            }
        } catch (_) {}
        // fingerprint no longer matches owner — drop to main
        goMain();
        return;
    }

    currentRole = 'user';
    enterUserPage();
    initWebSocket();
}

restoreSession();
</script>
</body>
</html>"""
