import os
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, status, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="Cashbox Queue API")

class JoinRequest(BaseModel):
    queue_id: str          
    user_identifier: str   
    prefix: str = "A"      

# ─── МИНИМАЛИСТИЧНЫЙ ВЕБ-ИНТЕРФЕЙС (HTML/CSS/JS) ───────────────────────

@app.get("/", response_class=HTMLResponse)
async def get_web_interface():
    """Возвращает легкую фронтенд-страницу для управления и просмотра очереди"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Университетская Очередь</title>
        <style>
            :root {
                --bg: #f8f9fa;
                --surface: #ffffff;
                --text: #212529;
                --primary: #0d6efd;
                --success: #198754;
                --border: #dee2e6;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            .container {
                width: 100%;
                max-width: 500px;
                background: var(--surface);
                padding: 24px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                margin-bottom: 20px;
                border: 1px solid var(--border);
            }
            h1, h2 { margin-top: 0; text-align: center; font-size: 1.5rem;}
            label { display: block; margin-bottom: 8px; font-weight: 500; font-size: 0.9rem; }
            input, select {
                width: 100%; padding: 10px; margin-bottom: 16px;
                border: 1px solid var(--border); border-radius: 6px; box-sizing: border-box;
            }
            button {
                width: 100%; padding: 12px; background: var(--primary);
                color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;
            }
            button.secondary { background: var(--success); }
            .ticket-display {
                text-align: center; padding: 20px; background: #e7f1ff;
                border-radius: 8px; margin-top: 15px; display: none;
            }
            .ticket-number { font-size: 2.5rem; font-weight: 8xl; color: var(--primary); margin: 10px 0; }
            .queue-list { list-style: none; padding: 0; margin: 0; }
            .queue-item {
                display: flex; justify-content: space-between; padding: 12px;
                border-bottom: 1px solid var(--border); font-size: 1.1rem;
            }
            .queue-item:first-child { font-weight: bold; color: var(--success); background: #f0fff4; }
            .tabs { display: flex; gap: 10px; margin-bottom: 20px; width: 100%; max-width: 500px; }
            .tab-btn { flex: 1; padding: 10px; background: #e2e8f0; border: none; border-radius: 6px; cursor: pointer; }
            .tab-btn.active { background: var(--primary); color: white; }
            .panel { display: none; }
            .panel.active { display: block; }
        </style>
    </head>
    <body>

        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('student')">Студент</button>
            <button class="tab-btn" onclick="switchTab('professor')">Преподаватель</button>
        </div>

        <!-- ПАНЕЛЬ СТУДЕНТА -->
        <div id="student-panel" class="container panel active">
            <h1>Вход в очередь</h1>
            <label>ID Очереди (Предмет)</label>
            <input type="text" id="queue_id" value="math_exam">
            
            <label>Ваш индентификатор (Слепок браузера)</label>
            <input type="text" id="user_identifier" readonly>

            <button onclick="takeTicket()">Получить талон</button>

            <div id="ticket-result" class="ticket-display">
                <div id="ticket-status">Вы записаны!</div>
                <div id="ticket-code" class="ticket-number">A1</div>
                <div>Позиция в очереди: <span id="ticket-pos">0</span></div>
            </div>
        </div>

        <!-- ПАНЕЛЬ ПРЕПОДАВАТЕЛЯ -->
        <div id="professor-panel" class="container panel">
            <h1>Панель управления</h1>
            <button class="secondary" onclick="callNext()">Вызвать следующего (Next FIFO)</button>
            <div id="called-result" style="text-align:center; margin-top:15px; font-size:1.2rem; font-weight:bold; color:var(--success)"></div>
        </div>

        <!-- МОНИТОР ОЧЕРЕДИ -->
        <div class="container">
            <h2>Текущая очередь (Табло)</h2>
            <ul id="live-queue" class="queue-list">
                <!-- Сюда JS подставит данные -->
            </ul>
        </div>

        <script>
            // Автогенерация слепка браузера при первом входе
            if (!localStorage.getItem('web_fingerprint')) {
                localStorage.setItem('web_fingerprint', 'web_' + Math.random().toString(36).substring(2, 11));
            }
            document.getElementById('user_identifier').value = localStorage.getItem('web_fingerprint');

            function switchTab(tab) {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
                if (tab === 'student') {
                    document.querySelectorAll('.tab-btn')[0].classList.add('active');
                    document.getElementById('student-panel').classList.add('active');
                } else {
                    document.querySelectorAll('.tab-btn')[1].classList.add('active');
                    document.getElementById('professor-panel').classList.add('active');
                }
            }

            async function takeTicket() {
                const qId = document.getElementById('queue_id').value;
                const uId = document.getElementById('user_identifier').value;

                const response = await fetch('/api/v1/queue/ticket', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ queue_id: qId, user_identifier: uId, prefix: 'A' })
                });
                const res = await response.json();
                
                if (response.ok) {
                    document.getElementById('ticket-result').style.display = 'block';
                    document.getElementById('ticket-code').innerText = res.ticket;
                    document.getElementById('ticket-pos').innerText = res.position_in_queue;
                    if(res.status === 'already_in_queue') {
                        document.getElementById('ticket-status').innerText = "Вы уже в очереди!";
                    } else {
                        document.getElementById('ticket-status').innerText = "Талон успешно выдан!";
                    }
                } else {
                    alert(res.detail || "Ошибка работы с очередью");
                }
                updateQueueView();
            }

            async function callNext() {
                const qId = document.getElementById('queue_id').value;
                const response = await fetch(`/api/v1/queue/${qId}/next`, { method: 'POST' });
                const res = await response.json();
                
                if (res.status === 'called') {
                    document.getElementById('called-result').innerText = `Сейчас идет талон: ${res.next_ticket}`;
                } else {
                    document.getElementById('called-result').innerText = "Очередь пуста!";
                }
                updateQueueView();
            }

            async function updateQueueView() {
                const qId = document.getElementById('queue_id').value;
                try {
                    const response = await fetch(`/api/v1/queue/${qId}/status`);
                    const res = await response.json();
                    const listContainer = document.getElementById('live-queue');
                    listContainer.innerHTML = '';

                    if(res.current_queue.length === 0) {
                        listContainer.innerHTML = '<li class="queue-item" style="justify-content:center; color:#888;">Очередь пуста</li>';
                        return;
                    }

                    res.current_queue.forEach(item => {
                        listContainer.innerHTML += `
                            <li class="queue-item">
                                <span>Позиция ${item.position}</span>
                                <span>Талон ${item.ticket}</span>
                            </li>
                        `;
                    });
                } catch (e) { console.error("Ошибка обновления табло", e); }
            }

            // Автоматическое обновление табло каждые 3 секунды
            setInterval(updateQueueView, 3000);
            updateQueueView();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ─── CORE API (БИЗНЕС-ЛОГИКА БЕЗ ИЗМЕНЕНИЙ) ───────────────────────────

@app.post("/api/v1/queue/ticket", status_code=status.HTTP_200_OK)
async def get_or_create_ticket(payload: JoinRequest):
    queue_id = payload.queue_id
    user_id = payload.user_identifier
    prefix = payload.prefix

    hash_key = f"queue:{queue_id}:identifiers"
    counter_key = f"queue:{queue_id}:counter"
    list_key = f"queue:{queue_id}:list"

    existing_ticket = await redis_client.hget(hash_key, user_id)
    
    if existing_ticket:
        position = await redis_client.lpos(list_key, user_id)
        if position is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Ваш талон уже был обслужен или аннулирован."
            )
        return {
            "status": "already_in_queue",
            "ticket": existing_ticket,
            "position_in_queue": position + 1
        }

    current_number = await redis_client.incr(counter_key)
    ticket_code = f"{prefix}{current_number}"

    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.hset(hash_key, user_id, ticket_code)
        pipe.rpush(list_key, user_id)
        await pipe.execute()

    queue_length = await redis_client.llen(list_key)
    return {
        "status": "success",
        "ticket": ticket_code,
        "position_in_queue": queue_length
    }

@app.get("/api/v1/queue/{queue_id}/status")
async def get_queue_status(queue_id: str):
    list_key = f"queue:{queue_id}:list"
    hash_key = f"queue:{queue_id}:identifiers"

    users_in_queue = await redis_client.lrange(list_key, 0, -1)
    if not users_in_queue:
        return {"queue_id": queue_id, "total": 0, "current_queue": []}

    tickets = await redis_client.hmget(hash_key, users_in_queue)
    current_queue = [
        {"position": idx + 1, "ticket": ticket} 
        for idx, ticket in enumerate(tickets) if ticket
    ]
    return {"queue_id": queue_id, "total": len(current_queue), "current_queue": current_queue}

@app.post("/api/v1/queue/{queue_id}/next")
async def serve_next_user(queue_id: str):
    list_key = f"queue:{queue_id}:list"
    hash_key = f"queue:{queue_id}:identifiers"

    served_user = await redis_client.lpop(list_key)
    if not served_user:
        return {"status": "empty", "message": "Очередь пуста"}

    ticket = await redis_client.hget(hash_key, served_user)
    await redis_client.hdel(hash_key, served_user)
    return {"status": "called", "next_ticket": ticket}

@app.post("/api/v1/telegram-webhook")
async def telegram_webhook(update: dict):
    message = update.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text_data = message.get("text", "")

    if not chat_id:
        return {"status": "ignored"}
    if text_data.startswith("/start"):
        return {"status": "ok", "reply": "Отправьте команду /get для получения талона."}
    return {"status": "ok"}