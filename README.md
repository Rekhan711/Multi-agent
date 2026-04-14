# Multi-Agent Business Intelligence System

Прототип BI-системы с фронтендом на Streamlit и бекендом на FastAPI. Проект демонстрирует архитектуру с несколькими агентами (Sales, Inventory, Finance, HR) и оркестратором, объединяющим ответы в едином чат-интерфейсе.

## Структура проекта

- `streamlit_app/`
  - `app.py` — главный Streamlit-приложение.
  - `components/ui.py` — общий UI, загрузка страниц и чат.
  - `pages/` — страницы Dashboard, Sales, Inventory, Finance, HR.
- `backend/`
  - `main.py` — FastAPI-приложение.
  - `agents/` — классы агентов и оркестратора.
  - `core/` — LLM-клиент, LlamaIndex knowledge layer и логика метрик.
  - `db/` — SQLAlchemy-модели, сессия и инициализация данных.
- `requirements.txt` — зависимости.

## Как развернуть локально

1. Установите зависимости:

```bash
python -m pip install -r requirements.txt
```

2. Задайте переменные окружения:

- `OPENAI_API_KEY` — ключ OpenAI. Без него агент не сможет формировать ответы.
- `DATABASE_URL` — строка подключения к PostgreSQL, например:
  `postgresql+psycopg2://user:password@localhost:5432/bi_db`

Если PostgreSQL отсутствует, система автоматически использует SQLite в `./local.db`.

3. Запустите FastAPI из корня репозитория:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4. В другом терминале запустите Streamlit из корня репозитория:

```bash
streamlit run streamlit_app/app.py
```

5. Если необходимо, укажите URL бекенда в `API_URL` или через `st.secrets` для Streamlit Cloud.

## Переменные окружения

- `OPENAI_API_KEY` — ключ OpenAI.
- `DATABASE_URL` — PostgreSQL-подключение, например:
  `postgresql+psycopg2://user:pass@localhost:5432/bi_db`
- `API_URL` — URL FastAPI, если Streamlit работает отдельно.
- `CORS_ALLOW_ORIGINS` — список доменов для CORS через запятую (по умолчанию `*`).

## Что реализовано

- Streamlit интерфейс с несколькими страницами:
  - Dashboard
  - Sales
  - Inventory
  - Finance
  - HR
- Общий чат на всех страницах с сохранением истории в `st.session_state`.
- FastAPI endpoints:
  - `POST /chat` — обращается к orchestrator и возвращает ответ.
  - `GET /metrics?page=...` — возвращает метрики для страниц.
- SQLAlchemy-схема с таблицами `sales`, `inventory`, `finance`, `employees`.
- Простой LLM-оркестратор на базе LangChain и LlamaIndex.

## Замена на настоящий Data Warehouse

В `backend/db/session.py` и `backend/core/knowledge_index.py` заложена абстракция. В реальном решении можно заменить запросы на Postgres/BigQuery/Redshift/Snowflake через SQL-интерфейс, сохранив структуру агентов.

> Примечание: интерфейсы LangChain и LlamaIndex могут отличаться в разных версиях. Если возникает ошибка импорта, проверьте актуальную документацию для вашей версии.

## Deploy (Docker)

Из корня проекта:

```bash
docker compose up --build
```

После запуска:

- Frontend: `http://localhost:8501`
- Backend health: `http://localhost:8000/health`

### Переменные окружения для деплоя

- `OPENAI_API_KEY` — ключ OpenAI (обязательно для LLM-ответов).
- `OPENAI_MODEL` — модель (по умолчанию `gpt-4.1-mini`).
- `DATABASE_URL` — если используете внешнюю БД.
- `CORS_ALLOW_ORIGINS` — список доменов через запятую для frontend (например `https://your-frontend.onrender.com`).
- `API_URL` — URL backend для frontend (в docker-compose уже настроен на `http://backend:8000`).

## Deploy (Render/Railway)

Создайте 2 сервиса:

1. Backend service
- Build: `docker build -f Dockerfile.backend -t bi-backend .`
- Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Env: `OPENAI_API_KEY`, `OPENAI_MODEL`, `DATABASE_URL`, `CORS_ALLOW_ORIGINS`

2. Frontend service
- Build: `docker build -f Dockerfile.frontend -t bi-frontend .`
- Start: `streamlit run streamlit_app/app.py --server.address 0.0.0.0 --server.port $PORT`
- Env: `API_URL=<public backend URL>`

## Deploy to Streamlit Community Cloud

Этот проект имеет отдельный backend (FastAPI), поэтому сначала должен быть доступен публичный URL backend.

1. Убедитесь, что backend уже развернут и доступен по HTTPS, например:
   - `https://your-backend-domain.com/health` -> `{"status":"ok"}`
2. Откройте Streamlit Community Cloud и нажмите **Create app**.
3. Укажите:
   - Repository: `Rekhan711/Multi-agent`
   - Branch: `main`
   - Main file path: `streamlit_app/app.py`
4. В **Advanced settings -> Secrets** добавьте:

```toml
api_url = "https://your-backend-domain.com"
```

5. Нажмите **Deploy** и дождитесь запуска приложения.

Если приложение поднялось, но чат недоступен, проверьте:
- корректность `api_url` в Secrets,
- CORS на backend (`CORS_ALLOW_ORIGINS` должен включать URL streamlit.app).
