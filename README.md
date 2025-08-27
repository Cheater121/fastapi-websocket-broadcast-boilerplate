# RT WebSocket Boilerplate (FastAPI + Docker)

Учебный проект/бойлерплейт для курса **[«Быстрый старт FastAPI Python»](https://stepik.org/course/179694/)**.
Демонстрирует реал-тайм коммуникации через **WebSocket** с Redis Pub/Sub, JWT-аутентификацией, проверкой Origin и простейшей системой presence.

---

## Возможности

* **WebSocket-эндпоинт** `/ws/{room}` с проверкой **Origin** и **JWT** до `accept()`.
* **Pub/Sub через Redis** (с помощью [`broadcaster`](https://pypi.org/project/broadcaster/)): сообщения доставляются всем подключённым клиентам в комнате.
* **Локальный менеджер соединений** и процессные подписки на комнаты с автоотпиской.
* **Heartbeat** (`system.ping`), **idle timeout** и хранение **онлайн-статуса (presence)** в Redis.
* **Pydantic v2**, **Python 3.11+** (используется `asyncio.TaskGroup`), готово к многопроцессной работе.

---

## Стек

* **FastAPI**, **Uvicorn**
* **Redis** (Pub/Sub + хранение presence)
* **broadcaster**, **redis-py (asyncio)**
* **PyJWT**, **Pydantic v2**
* **Docker Compose** для запуска инфраструктуры

---

## Структура проекта

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
Dockerfile             # сборка приложения
docker-compose.yml     # app + redis
.env.example           # пример конфигурации окружения
README.md              # вы читаете его :)
```

---

## Запуск (Docker)

### 1. Подготовьте `.env`:

```bash
cp .env.example .env
# отредактируйте при необходимости (секреты, ALLOWED_ORIGINS и т.п.)
```

### 2. Запустите:

```bash
docker compose up -d --build
```

### 3. Проверка состояния:

```bash
docker compose ps
docker compose logs -f app
```

Приложение будет доступно на `127.0.0.1:8000`, Redis — внутри сети Compose.

---

## Переменные окружения (`.env`)

* `JWT_SECRET`, `JWT_ALG` — параметры верификации JWT (по умолчанию `change-me`, `HS256`)
* `REDIS_URL` — адрес Redis (по умолчанию `redis://redis:6379`)
* `ALLOWED_ORIGINS` — список разрешённых Origin (через запятую), формат `scheme://host[:port]`
* `PRESENCE_TTL` — TTL ключа присутствия пользователя (сек, по умолчанию `60`)
* `HEARTBEAT_INTERVAL` — интервал пингов `system.ping` (по умолчанию `25`)
* `IDLE_TIMEOUT` — отключение бездействующих соединений (по умолчанию `70`)

---

## Курс

Более подробное объяснение кода, архитектуры и деплоя — в курсе **[«Быстрый старт FastAPI Python»](https://stepik.org/course/179694/)**.
Советуем пройти его, если хотите быстро освоить FastAPI для реальных приложений.
