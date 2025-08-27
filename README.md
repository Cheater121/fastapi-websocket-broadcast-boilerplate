# README — RT WebSocket Boilerplate (FastAPI)

Учебный проект/бойлерплейт для курса **«Быстрый старт FastAPI Python»**.
Демонстрирует реал-тайм коммуникации через WebSocket + Redis Pub/Sub с базовой аутентификацией по JWT, контролем Origin и «presence» (онлайн-статус).

## Возможности

* WebSocket-эндпоинт `/ws/{room}` с проверкой **Origin** и **JWT** до `accept()`.
* Шина событий через **Redis** (через `broadcaster`): сообщения доставляются всем подключённым к комнате клиентам.
* Локальный менеджер соединений и процессные подписки на комнаты с авто-отпиской.
* Heartbeat (`system.ping`), `idle timeout` и простая схема presence (TTL в Redis).
* Pydantic v2, Python 3.11+ (используется `asyncio.TaskGroup`).

## Стек

* FastAPI, Uvicorn
* Redis (Pub/Sub + хранение presence)
* broadcaster, redis-py (asyncio)
* PyJWT, Pydantic v2

## Структура

```
app/
  config.py            # конфиг, нормализация Origin, константы
  logger.py            # базовая настройка логов
  protocol.py          # модели и типы сообщений (Pydantic)
  auth.py              # верификация JWT
  state.py             # глобальные синглтоны (Redis, Broadcast)
  managers.py          # RoomManager — локальные WS-соединения
  subscriptions.py     # подписки на каналы Redis по комнатам
  lifespan.py          # init/cleanup Redis и Broadcast
  websocket_routes.py  # /ws/{room}
  main.py              # FastAPI(app), подключение роутера
```

## Требования

* Python **3.11+**
* Запущенный **Redis**
* (опционально) `websocat` или `wscat` для тестов WS

## Установка и запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip

# Минимальные зависимости
cat > requirements.txt <<'REQ'
fastapi>=0.111
uvicorn[standard]>=0.30
pydantic>=2.5
redis>=5.0
broadcaster>=0.3
PyJWT>=2.8
REQ
pip install -r requirements.txt

# Переменные окружения (пример)
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET="change-me"
export JWT_ALG="HS256"
export ALLOWED_ORIGINS="http://localhost:8000"  # whitelist для Origin заголовка

# Старт
uvicorn app.main:app --reload
```

## Переменные окружения

* `REDIS_URL` — адрес Redis (по умолчанию `redis://localhost:6379`)
* `JWT_SECRET`, `JWT_ALG` — параметры верификации JWT (по умолчанию `change-me`, `HS256`)
* `ALLOWED_ORIGINS` — список разрешённых Origin (через запятую), формат `scheme://host[:port]`
* `PRESENCE_TTL` — TTL ключа присутствия пользователя в секундах (по умолчанию `60`)
* `HEARTBEAT_INTERVAL` — период отправки `system.ping` (по умолчанию `25`)
* `IDLE_TIMEOUT` — отключение бездействующих соединений (по умолчанию `70`)

## Быстрый смоук-тест WebSocket

1. Сгенерировать токен:

```bash
python - <<'PY'
import jwt, time
print(jwt.encode({"sub":"u1","iat":int(time.time())}, "change-me", algorithm="HS256"))
PY
```

2. Подключиться к комнате `test` (пример с websocat):

```bash
TOKEN=... # вставьте токен
websocat -H=Origin:http://localhost:8000 "ws://127.0.0.1:8000/ws/test?token=$TOKEN"
```

3. Отправить сообщение:

```json
{"type":"chat.message","room":"test","text":"hi"}
```

Ожидается ответ-доставка:

```json
{"type":"chat.delivery","room":"test","user":"u1","text":"hi","id":"...","ts":...}
```

Периодически будет приходить `{"type":"system.ping", ...}`.

## Примечания

* Код предназначен для обучения: не претендует на полноту прод-решения, но задаёт здравый каркас.
* Для продакшена добавьте: метрики/трейсинг, rate-limit/кучевые защиты, персистентный стор для истории, расширенную обработку ошибок и ретраи внешних зависимостей.

Лицензируйте и модифицируйте по своему усмотрению. Удачи в реальном времени! 🚀
