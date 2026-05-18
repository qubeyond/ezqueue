def get_spa_html() -> str:
    return """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Система Управления Очередью</title>
    <style>
        :root {
            --bg: #0b0f19; --surface: #151f32; --border: #24344d;
            --text: #f1f5f9; --text-muted: #64748b;
            --primary: #0ea5e9; --success: #10b981; --danger: #ef4444;
        }
        body {
            font-family: system-ui, -apple-system, sans-serif;
            background: var(--bg); color: var(--text); margin:0; padding:24px;
            overflow-x: hidden;
        }
        .screen { display: none; }
        .screen.active { display: block; }
        .main-container { max-width: 420px; margin: 40px auto 0 auto; position: relative; }
        .card { background: var(--surface); border: 1px solid var(--border); padding: 24px; border-radius: 16px; margin-bottom: 24px; box-sizing: border-box; }
        input { width: 100%; padding: 14px; background: #0b0f19; border: 1px solid var(--border); color: white; border-radius: 8px; margin-bottom: 16px; box-sizing: border-box; font-size: 1rem; text-transform: uppercase; }
        button { width: 100%; padding: 14px; background: var(--primary); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: opacity 0.2s; font-size: 1rem; margin-bottom: 12px; }
        button:hover { opacity: 0.9; }
        button.danger { background: var(--danger); }
        button.success { background: var(--success); }
        button.secondary { background: #334155; }
        .ticket-display { font-size: 4.5rem; font-weight: 900; color: var(--success); text-align: center; border: 4px solid var(--border); padding: 20px; border-radius: 24px; background: #0b0f19; margin: 20px 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .metric-row { display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding: 10px 0; font-size: 1.1rem; }
        .admin-current-ticket { font-size: 2.5rem; font-weight: 800; color: var(--primary); margin: 15px 0; text-align: center; text-transform: uppercase; letter-spacing: 1px; }
        .ticket-line { display: flex; gap: 12px; overflow-x: auto; padding: 10px 0; min-height: 50px; }
        .ticket-item { background: #1e293b; border: 1px solid var(--border); padding: 10px 18px; border-radius: 8px; font-weight: bold; white-space: nowrap; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 1px solid var(--border); padding-bottom: 16px; }
        .error-ui { color: var(--danger); background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); padding: 12px; border-radius: 8px; margin-bottom: 16px; display: none; text-align: center; font-weight: 600; }
        .my-id-badge { text-align: center; font-size: 0.85rem; color: var(--text-muted); margin-top: 15px; font-family: monospace; }
        .toast-container { position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999; width: 90%; max-width: 400px; }
        .toast { background: var(--surface); border-left: 4px solid var(--danger); color: var(--text); padding: 16px; border-radius: 8px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; animation: slideDown 0.3s ease-out; }
        .toast.info { border-left-color: var(--primary); }
        .toast-close { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 1.2rem; font-weight: bold; padding: 0 0 0 12px; margin: 0; width: auto; }
        .toast-close:hover { color: var(--text); }
        @keyframes slideDown { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    </style>
</head>
<body>
    <div class="toast-container" id="toast-box"></div>
    <div class="main-container">
        <div id="global-error" class="error-ui"></div>
        <div id="scr-main" class="screen active">
            <div class="card">
                <h2 style="margin-top:0; text-align:center;">Вход в систему</h2>
                <input type="text" id="input-room-id" placeholder="ID КОМНАТЫ (6 СИМВОЛОВ)" maxlength="6">
                <button class="success" onclick="userJoinRoom()">Войти в комнату</button>
                <hr style="border-color:var(--border); margin: 20px 0;">
                <button class="secondary" onclick="adminCreateRoom()">Создать комнату</button>
                <div class="my-id-badge">
                    Ваш Client ID: <span id="display-my-id" style="color: var(--primary);"></span>
                </div>
            </div>
        </div>
        <div id="scr-user" class="screen">
            <div class="header-bar">
                <h3 id="user-room-title" style="margin:0;">Комната: --</h3>
                <button style="width:auto; margin:0; padding: 8px 16px;" class="danger" onclick="leaveRoom()">Выйти</button>
            </div>
            <div class="card">
                <div class="ticket-display" id="user-ticket-num">...</div>
                <div class="metric-row"><span>Ваша позиция:</span> <strong id="m-position" style="color:var(--primary)">...</strong></div>
                <div class="metric-row"><span>Статус комнаты:</span> <strong id="m-room-status">...</strong></div>
                <div class="metric-row"><span>Время обслуживания:</span> <strong id="m-user-timer" style="color:var(--success)">00:00</strong></div>
            </div>
        </div>
        <div id="scr-admin" class="screen">
            <div class="header-bar">
                <h3 id="admin-room-title" style="margin:0;">Админ: --</h3>
                <button style="width:auto; margin:0; padding: 8px 16px;" class="danger" onclick="adminLeaveAndClose()">Закрыть комнату</button>
            </div>
            <div class="card">
                <h4 style="margin:0; text-align:center; color:var(--text-muted)">ТЕКУЩИЙ ТАЛОН</h4>
                <div class="admin-current-ticket" id="adm-current-ticket">...</div>
                <div id="adm-timer-display" style="font-size:1.5rem; margin-bottom:20px; font-family:monospace; text-align:center;">00:00</div>
                <div id="adm-action-slot">
                    <button class="success" disabled>Загрузка...</button>
                </div>
            </div>
            <div class="card">
                <h4 style="margin-top:0; margin-bottom:10px;">Строка следующих талонов</h4>
                <div class="ticket-line" id="adm-queue-line">...</div>
            </div>
        </div>
    </div>
    <script>
        let myClientFingerprint = localStorage.getItem('user_client_fp') || 'cli_' + Math.random().toString(36).substring(2, 11).toUpperCase();
        localStorage.setItem('user_client_fp', myClientFingerprint);
        document.getElementById('display-my-id').innerText = myClientFingerprint;
        let currentRoomId = "";
        let ws = null;
        let uiTimer = null;
        let currentElapsed = 0;
        let currentRole = "";

        function showToast(message, type = "info") {
            const box = document.getElementById('toast-box');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `<span>${message}</span><button class="toast-close" onclick="this.parentElement.remove()">&times;</button>`;
            box.appendChild(toast);
            setTimeout(() => { if(toast.parentNode) toast.remove(); }, 7000);
        }

        function clearUserDOM() {
            document.getElementById('user-ticket-num').innerText = "...";
            document.getElementById('m-position').innerText = "...";
            document.getElementById('m-room-status').innerText = "Подключение...";
            document.getElementById('m-user-timer').innerText = "00:00";
        }

        function clearAdminDOM() {
            document.getElementById('adm-current-ticket').innerText = "...";
            document.getElementById('adm-timer-display').innerText = "00:00";
            document.getElementById('adm-action-slot').innerHTML = `<button class="success" disabled>Загрузка...</button>`;
            document.getElementById('adm-queue-line').innerText = "...";
        }

        function checkPersistedSession() {
            const savedRoomId = localStorage.getItem('active_room_id');
            const savedRole = localStorage.getItem('active_role');
            if (savedRoomId && savedRole) {
                currentRoomId = savedRoomId;
                currentRole = savedRole;
                if (currentRole === 'admin') {
                    clearAdminDOM();
                    document.getElementById('admin-room-title').innerText = `Админ: ${currentRoomId}`;
                    switchScreen('scr-admin');
                } else if (currentRole === 'user') {
                    clearUserDOM();
                    document.getElementById('user-room-title').innerText = `Комната: ${currentRoomId}`;
                    switchScreen('scr-user');
                }
                initWebSocket(currentRoomId);
            }
        }

        function switchScreen(screenId) {
            document.getElementById('global-error').style.display = 'none';
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
            document.getElementById(screenId).classList.add('active');
            if (screenId === 'scr-main') {
                if (ws) { ws.close(); ws = null; }
                localStorage.removeItem('active_room_id');
                localStorage.removeItem('active_role');
                currentRoomId = "";
                currentRole = "";
            }
        }

        function userJoinRoom() {
            const rId = document.getElementById('input-room-id').value.trim().toUpperCase();
            if(!rId) return;
            fetch('/api/v1/queue/ticket', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ room_id: rId, user_identifier: myClientFingerprint })
            })
            .then(async res => {
                if(!res.ok) {
                    const errData = await res.json();
                    throw new Error(errData.detail || "Комната не найдена");
                }
                return res.json();
            })
            .then(data => {
                currentRoomId = rId;
                localStorage.setItem('active_room_id', currentRoomId);
                if (data.is_admin) {
                    currentRole = "admin";
                    localStorage.setItem('active_role', currentRole);
                    clearAdminDOM();
                    document.getElementById('admin-room-title').innerText = `Админ: ${currentRoomId}`;
                    switchScreen('scr-admin');
                } else {
                    currentRole = "user";
                    localStorage.setItem('active_role', currentRole);
                    clearUserDOM();
                    document.getElementById('user-room-title').innerText = `Комната: ${currentRoomId}`;
                    switchScreen('scr-user');
                }
                initWebSocket(currentRoomId);
            })
            .catch(err => showError(err.message));
        }

        function adminCreateRoom() {
            fetch(`/api/v1/rooms?admin_id=${myClientFingerprint}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                currentRoomId = data.room_id;
                currentRole = "admin";
                localStorage.setItem('active_room_id', currentRoomId);
                localStorage.setItem('active_role', currentRole);
                clearAdminDOM();
                document.getElementById('admin-room-title').innerText = `Админ: ${currentRoomId}`;
                switchScreen('scr-admin');
                initWebSocket(currentRoomId);
            })
            .catch(() => showError("Не удалось создать комнату"));
        }

        function leaveRoom() {
            if(currentRole === 'user') {
                fetch('/api/v1/queue/leave', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ room_id: currentRoomId, user_identifier: myClientFingerprint })
                }).then(() => switchScreen('scr-main'));
            }
        }

        function adminLeaveAndClose() {
            fetch(`/api/v1/admin/terminate?admin_id=${myClientFingerprint}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ room_id: currentRoomId })
            })
            .then(() => switchScreen('scr-main'))
            .catch(() => switchScreen('scr-main'));
        }

        function adminNext() {
            fetch('/api/v1/admin/next', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ room_id: currentRoomId })
            }).catch(() => showToast("Очередь пуста", "info"));
        }

        function adminComplete() {
            fetch('/api/v1/admin/complete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ room_id: currentRoomId })
            });
        }

        function initWebSocket(roomId) {
            if(ws) { ws.close(); ws = null; }
            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/room/${roomId}?user_id=${myClientFingerprint}`);
            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.data && msg.data.room_closed) {
                    if (currentRole === 'user') {
                        showToast("Прием завершен. Администратор закрыл комнату обслуживания.", "info");
                    }
                    switchScreen('scr-main');
                    return;
                }
                if (msg.data && msg.data.room_id && msg.data.room_id !== currentRoomId) {
                    return;
                }
                if(msg.type === 'welcome' || msg.type === 'update') {
                    if(currentRole === 'user') renderUserView(msg.data);
                    if(currentRole === 'admin') renderAdminView(msg.data);
                }
            };
        }

        function renderUserView(data) {
            if (data.client_context.should_redirect && currentRoomId !== "") {
                switchScreen('scr-main');
                return;
            }
            document.getElementById('user-ticket-num').innerText = data.client_context.ticket_label;
            document.getElementById('m-position').innerText = data.client_context.position_label;
            document.getElementById('m-room-status').innerText = data.current_status_label;
            const posElement = document.getElementById('m-position');
            if (data.client_context.position_label === "На приеме") {
                posElement.style.color = "var(--success)";
            } else {
                posElement.style.color = "var(--primary)";
            }
            updateTimer(data);
        }

        function renderAdminView(data) {
            document.getElementById('adm-current-ticket').innerText = data.admin_context.current_ticket_label;
            const actionSlot = document.getElementById('adm-action-slot');
            if(data.current_status === 'serving') {
                actionSlot.innerHTML = `<button class="danger" onclick="adminComplete()">Завершить обслуживание</button>`;
            } else {
                actionSlot.innerHTML = `<button class="success" onclick="adminNext()">Вызвать следующего</button>`;
            }
            const line = document.getElementById('adm-queue-line');
            line.innerHTML = "";
            if(data.admin_context.next_tickets && data.admin_context.next_tickets.length > 0) {
                data.admin_context.next_tickets.forEach(ticketLabel => {
                    line.innerHTML += `<div class="ticket-item">${ticketLabel}</div>`;
                });
            } else {
                line.innerHTML = `<span style="color:var(--text-muted)">Очередь пуста</span>`;
            }
            updateTimer(data);
        }

        function updateTimer(data) {
            clearInterval(uiTimer);
            const labels = [document.getElementById('m-user-timer'), document.getElementById('adm-timer-display')];
            if(data.current_status === 'serving') {
                currentElapsed = data.elapsed_time;
                uiTimer = setInterval(() => {
                    currentElapsed++;
                    const formatted = formatTime(currentElapsed);
                    labels.forEach(lbl => { if(lbl) lbl.innerText = formatted; });
                }, 1000);
            } else {
                labels.forEach(lbl => { if(lbl) lbl.innerText = "00:00"; });
            }
        }

        function formatTime(seconds) {
            let m = String(Math.floor(seconds / 60)).padStart(2, '0');
            let s = String(seconds % 60).padStart(2, '0');
            return `${m}:${s}`;
        }

        function showError(msg) {
            const errUi = document.getElementById('global-error');
            errUi.innerText = msg;
            errUi.style.display = 'block';
            setTimeout(() => { errUi.style.display = 'none'; }, 5000);
        }

        checkPersistedSession();
    </script>
</body>
</html>"""