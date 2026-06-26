# Queue Service

Сервис электронной очереди для живых мероприятий. Одна ссылка — несколько очередей, real-time обновления, статистика.

[Перейти](https://ezqueue.ru/)

---

## Для пользователей

### Что умеет

**Пользователь**
- Заходит в комнату по коду, получает талон
- Автоматически попадает в наименьшую очередь (балансировщик)
- Видит своё место, текущее время обслуживания, среднее время ожидания
- Может уйти досрочно

**Администратор**
- Создаёт комнату, получает код для раздачи
- Добавляет и удаляет очереди — люди перераспределяются автоматически
- Вызывает следующего, завершает обслуживание
- Видит статистику: всего талонов, обслужено, среднее время

### Безопасность

- Авторизация через JWT: короткоживущий access token + refresh token в httpOnly cookie
- Access token хранится только в памяти браузера — не в localStorage, недоступен для JS
- WebSocket принимает только валидный JWT, без токена соединение закрывается
- Закрыть комнату может только владелец — двойная проверка: роль в токене и владелец в Redis
- Rate limiting на все мутирующие эндпоинты
- Security headers на всех ответах
- HTTPS через Caddy с автоматическим Let's Encrypt (на проде)

---

## Для разработчиков

### Стек

- fastapi >= 0.136, uvicorn >= 0.47, websockets >= 16
- sqlalchemy >= 2.0 (async), asyncpg >= 0.31, postgresql 16
- redis >= 7.4 (asyncio client), redis 7 (server)
- dishka >= 0.9
- pydantic >= 2.13, pydantic-settings
- PyJWT >= 2.10
- slowapi >= 0.1.9
- caddy2

### Архитектура

Гексагональная (ports & adapters): `domain` не зависит ни от чего, `infrastructure` реализует интерфейсы домена, `services` содержат бизнес-логику, `api` — точка входа. Живое состояние — Redis (с TTL), история — PostgreSQL.

### Тесты

70 тестов: unit (моки) + integration (реальный Redis, SQLite in-memory).

### Pre-commit

```bash
uv run --directory backend pre-commit install
```

При каждом коммите автоматически запускаются ruff check, ruff format и unit-тесты. Интеграционные тесты в хук не включены — требуют живой Redis.

### Запуск

```bash
cp backend/.env.example backend/.env
# заполнить JWT_SECRET
docker compose up --build
```

На проде — прописать домен в `Caddyfile`, затем:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
