# RetailIQ | Ask Your Data

A small local analytics workspace for turning retail questions into read-only PostgreSQL query previews. It includes a FastAPI service, a Streamlit interface, and a PostgreSQL database managed with Docker Compose.

> **Current scope:** the application generates and checks SQL, but does not execute it. Document search (RAG) is not implemented yet. The evaluation script checks service health; it does not measure SQL accuracy.

## Contents

- [Features](#features)
- [Technical architecture](#technical-architecture)
- [Data models](#data-models)
- [API reference](#api-reference)
- [Dependencies and packages](#dependencies-and-packages)
- [Project layout](#project-layout)
- [Requirements](#requirements)
- [Setup on Windows](#setup-on-windows)
- [Run the application](#run-the-application)
- [Use the API](#use-the-api)
- [Checks](#checks)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Security notes](#security-notes)
- [Known limitations](#known-limitations)

## Features

- Generate a PostgreSQL `SELECT` query from a plain-language question using OpenRouter or OpenAI.
- Reject model output that does not begin with `SELECT` or contains selected write-operation keywords, comments, or multiple statements.
- Browse the query builder in a Streamlit UI with service status and schema reference.
- Start PostgreSQL 16 with the pgvector image using Docker Compose.
- Keep provider keys in a local `.env` file that is excluded from Git.

## Technical architecture

### Request flow

1. A user submits a natural-language question from the Streamlit query form.
2. Streamlit sends the question as JSON to the FastAPI `POST /sql` endpoint.
3. FastAPI validates the question with Pydantic, trims surrounding whitespace, and limits it to 2,000 characters.
4. The API sends the question and the declared retail schema to the configured chat-completions provider.
5. The response is checked by `is_safe_query()` before being returned as a SQL preview.
6. Streamlit displays the SQL or a readable service/provider error. It does not execute the SQL.

### Language-model integration

The backend uses the asynchronous `AsyncOpenAI` client from the OpenAI Python SDK. OpenRouter and OpenAI are accessed through their OpenAI-compatible chat-completions API.

| Provider selection | Credential | Default model | API endpoint |
| --- | --- | --- | --- |
| OpenRouter, preferred when its key is non-empty | `OPENROUTER_API_KEY` | `openrouter/auto` | `https://openrouter.ai/api/v1` |
| OpenAI fallback | `OPENAI_API_KEY` | `gpt-4o-mini` | OpenAI SDK default, or `OPENAI_BASE_URL` |

The model ID can be overridden with `OPENROUTER_MODEL` or `MODEL_NAME`. `openrouter/auto` is OpenRouter's model router, not a guarantee of free inference; check account access and current model pricing. For OpenRouter requests the client adds `HTTP-Referer` and `X-Title` attribution headers.

Generation uses `temperature=0`, a configurable `MAX_TOKENS_LIMIT` capped at 4,096, a 30-second client timeout, and up to two SDK retries. A single async client is held on the FastAPI app state and closed during application shutdown.

### SQL output guard

`is_safe_query()` is a lightweight regular-expression filter. It requires the output to begin with `SELECT`, permits at most one trailing semicolon, and rejects SQL comments and selected write/administrative keywords. This is not a SQL parser, a complete read-only guarantee, or a database permission system. The current application only returns query text; it does not run the SQL.

### User interface

The Streamlit analyst desk includes:

- A question form submitted explicitly with **Build query**.
- Query preview rendered with SQL syntax highlighting.
- A status indicator driven by the API health endpoint; the status check is cached for five seconds.
- A sidebar reference to the configured API URL and the two known database tables.
- A Reports tab that states document search is not connected.
- Request timeouts and visible API/provider errors instead of fabricated example results.

## Data models

`setup_db.py` defines two SQLAlchemy declarative models. `Base.metadata.create_all()` creates their tables if they do not already exist.

| SQLAlchemy model | PostgreSQL table | Columns |
| --- | --- | --- |
| `Products` | `products` | `id`: integer primary key; `name`: string, up to 255 characters; `category`: string, up to 100 characters; `price`: floating-point number |
| `Sales` | `sales` | `id`: integer primary key; `product_id`: integer; `quantity`: integer; `date`: string, up to 50 characters |

The `sales.product_id` field is currently a plain integer, not a declared foreign key. The API sends this schema description to the model; it does not inspect the live database schema. PostgreSQL is used by the setup script, but `/sql` does not query the database.

The Compose image includes pgvector, but no vector extension, embedding table, or vector-search operation is currently created or used by this application.

## API reference

The service is a FastAPI application in `main.py`. FastAPI generates interactive OpenAPI documentation at `/docs` while the server is running.

| Method | Path | Purpose | Current behavior |
| --- | --- | --- | --- |
| `GET` | `/` | Basic service check | Returns `{"message":"RetailIQ API is running"}` |
| `POST` | `/sql` | Generate a SQL preview | Accepts `{"question":"..."}` and returns `{"query":"SELECT ..."}` when a configured model returns accepted output |
| `POST` | `/rag` | Document question answering | Returns HTTP `503`; document retrieval is not configured |
| `GET` | `/eval/health` | Evaluation-harness health check | Returns `{"status":"Evaluation Harness Ready"}` |

`POST /sql` returns HTTP `422` for invalid request bodies, HTTP `503` when no provider key is configured, and HTTP `502` when the provider request fails or its output is rejected. It never executes the returned statement.

### Request and response example

Request:

```json
{"question":"Which five products have the highest price?"}
```

Response:

```json
{"query":"SELECT name, price FROM products ORDER BY price DESC LIMIT 5"}
```

## Dependencies and packages

### Used by the current application

| Package | Role |
| --- | --- |
| FastAPI | HTTP routes, request handling, and OpenAPI docs |
| Uvicorn | ASGI server for the API |
| Pydantic | Request schema and question validation |
| OpenAI Python SDK | Async OpenAI-compatible client for OpenRouter/OpenAI chat completions |
| Streamlit | Analyst desk web interface |
| Requests | Streamlit-to-FastAPI HTTP calls and health checks; currently installed transitively through Streamlit |
| SQLAlchemy | PostgreSQL engine and declarative table definitions in `setup_db.py` |
| psycopg2-binary | Synchronous PostgreSQL DBAPI driver used by the schema setup script |
| python-dotenv | Loads local `.env` configuration |
| httpx | HTTP transport used by the OpenAI SDK; constrained below 0.28 for compatibility with the pinned FastAPI/Starlette test stack |

### Declared but not currently used by application code

`asyncpg`, `numpy`, `scikit-learn`, `sentence-transformers`, `chromadb`, and `aiohttp` are listed in `requirements.txt`, but the current API/UI code does not import them. They may support future async database access, analytics, embeddings, document retrieval, or HTTP work; installing them does not mean those features are implemented.

## Project layout

```text
.
├── app/
│   └── streamlit_app.py    # Streamlit analyst desk
├── docker-compose.yml      # Local PostgreSQL service
├── eval_harness.py         # API health smoke checks
├── main.py                 # FastAPI routes and model integration
├── requirements.txt        # Python dependencies
├── setup_db.py             # SQLAlchemy table definitions and initialization
└── .env.example            # Safe configuration template (no credentials)
```

## Requirements

- Windows 10/11, macOS, or Linux
- Python 3.11 recommended
- Docker Desktop (Windows/macOS) or Docker Engine with Compose
- An OpenRouter API key or OpenAI API key for SQL generation

The API and Streamlit UI run as local Python processes. Docker is used for PostgreSQL only.

## Setup on Windows

Run these commands in PowerShell from the project directory.

### 1. Create and activate a virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, either allow scripts for the current user according to your organization's policy or call the environment executables directly as shown below.

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Create your local environment file

```powershell
Copy-Item .env.example .env
```

Open `.env` in your editor and set `OPENROUTER_API_KEY` to your own key. Do not put a real key in this README, source code, screenshots, or a commit. OpenRouter is selected whenever `OPENROUTER_API_KEY` is non-empty; otherwise, the API falls back to `OPENAI_API_KEY`.

For OpenRouter, keep the default `OPENROUTER_BASE_URL` unless your account/provider instructions say otherwise. Set `OPENROUTER_MODEL` to a model ID available to your account. The template uses `openrouter/auto`; availability and cost depend on OpenRouter's current routing and model catalog. Check pricing before sending requests. Alternatively, configure `OPENAI_API_KEY` and `MODEL_NAME` for OpenAI.

### 4. Start PostgreSQL

Make sure Docker Desktop is running, then:

```powershell
docker-compose up -d
docker-compose ps
```

The Compose service creates a database named `retail_db` on first initialization, listening on port `5432` with the development credentials in `docker-compose.yml`.

### 5. Create the application tables

```powershell
python setup_db.py
```

Expected output:

```text
Database Schema Created Successfully.
```

The script creates `products` and `sales` tables if they do not already exist.

### 6. Start the API

Open a PowerShell terminal in the project directory and run:

```powershell
.\.venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8000 --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive endpoint documentation is at `http://127.0.0.1:8000/docs`.

### 7. Start the user interface

Open a second terminal in the project directory and run:

```powershell
.\.venv\Scripts\streamlit.exe run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. Enter a retail question under **Query builder**, then choose **Build query**. The Reports tab currently explains that document search is not connected.

## Run the application

For later runs, start the services in this order:

1. Start Docker Desktop.
2. Run `docker-compose up -d` from the project directory.
3. Start FastAPI in one terminal.
4. Start Streamlit in another terminal.

Stop local Python servers with `Ctrl+C`. Stop the database container without deleting its data with:

```powershell
docker-compose stop
```

To start the existing database again, use `docker-compose start` or `docker-compose up -d`.

## Use the API

### Health checks

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8000/eval/health
```

Expected responses:

```json
{"message":"RetailIQ API is running"}
{"status":"Evaluation Harness Ready"}
```

### Generate a query preview

```powershell
$body = @{ question = "Which five products have the highest price?" } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/sql `
  -ContentType "application/json" `
  -Body $body
```

A successful response has this shape:

```json
{"query":"SELECT name, price FROM products ORDER BY price DESC LIMIT 5"}
```

The returned SQL is a preview only. It is not run against PostgreSQL and no query results are returned.

### Reports endpoint

`POST /rag` currently returns HTTP `503` because document ingestion and retrieval have not been implemented. It does not return a sample or fabricated answer.

## Checks

Run these from the project directory with the virtual environment activated:

```powershell
python -m compileall -q main.py setup_db.py eval_harness.py app\streamlit_app.py
python -m pip check
python eval_harness.py
```

`eval_harness.py` requires the API to be running. It checks only `/` and `/eval/health`; it is not a question/answer benchmark and does not call the model.

To confirm Compose can parse its configuration:

```powershell
docker-compose config --quiet
```

## Configuration

Copy `.env.example` to `.env` and adjust values for your machine. Never commit `.env`.

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Selects OpenRouter when non-empty | Empty |
| `OPENROUTER_BASE_URL` | OpenRouter OpenAI-compatible API URL | `https://openrouter.ai/api/v1` |
| `OPENROUTER_MODEL` | OpenRouter model ID | `openrouter/auto` |
| `OPENROUTER_SITE_URL` | Optional OpenRouter attribution header | `http://localhost:8501` |
| `OPENROUTER_APP_NAME` | Optional OpenRouter app attribution | `RetailIQ` |
| `OPENAI_API_KEY` | OpenAI fallback credential | Empty |
| `OPENAI_BASE_URL` | Optional OpenAI-compatible endpoint override | SDK default |
| `MODEL_NAME` | OpenAI model name | `gpt-4o-mini` |
| `DATABASE_URL` | SQLAlchemy connection URL for schema setup | Local `retail_db` URL |
| `MAX_TOKENS_LIMIT` | Maximum generated tokens, capped at 4096 | `4096` |
| `API_BASE_URL` | FastAPI URL used by Streamlit and the evaluation harness | `http://localhost:8000` |

When both provider keys are set, OpenRouter takes precedence. After changing `.env`, restart FastAPI so the new settings are loaded. Keep API keys private and use the provider's own dashboard to review available models and pricing.

## Troubleshooting

### `OPENROUTER_API_KEY` or `OPENAI_API_KEY` is not configured

Check that `.env` exists in the project root, that the key variable name is correct, and that the value is non-empty. Restart FastAPI after editing `.env`. Do not include surrounding quotes unless the key itself requires them.

### Provider rejects the key or model

Confirm the key is active, the chosen model ID is available to your account, and the account has any required quota or billing enabled. OpenRouter model IDs and availability can change; consult its model catalog. The API intentionally returns a generic model-request error to clients; inspect the FastAPI terminal for provider-side details.

### Docker cannot connect to its engine

Start Docker Desktop and wait for its engine to become ready, then retry `docker-compose up -d`.

### `database "retail_db" does not exist`

`POSTGRES_DB` is used only when PostgreSQL initializes an empty data volume. If the volume was initialized earlier, create the database in the running container without removing the volume:

```powershell
docker-compose exec -T postgres psql -U user -d postgres -c "CREATE DATABASE retail_db;"
```

Then rerun `python setup_db.py`. Do not use `docker-compose down -v` unless you intentionally want to permanently delete the database volume and its data.

### Port 5432, 8000, or 8501 is already in use

Stop the other process using that port or change the relevant port and matching connection URL/configuration. PostgreSQL's host port is set in `docker-compose.yml`; the API and UI ports are command-line options in the run steps above.

### Streamlit shows “API unavailable”

Confirm FastAPI is running at `http://localhost:8000`. If it uses another address, set `API_BASE_URL` in `.env` and restart Streamlit.

## Security notes

- `.env` is ignored by Git. Keep real provider keys there or in a managed secret store; never commit them.
- The Compose PostgreSQL username and password are development defaults. Change them before using this setup beyond a local trusted environment.
- The SQL validator is a lightweight output filter, not a complete SQL parser or authorization boundary. Do not execute model-generated SQL or expose this service publicly without database-level read-only permissions, authentication, network controls, and stronger SQL validation.
- The current endpoint does not execute generated SQL, so it does not return database data.

## Known limitations

- SQL generation depends on a configured provider key, accessible model, and available provider quota.
- The model sees the declared `products` and `sales` schema. The database is not queried for live schema metadata.
- Queries are generated and checked, not executed.
- RAG/document search is not implemented.
- The evaluation harness covers API availability only, not SQL correctness, latency, or answer quality.
- Although the database image includes pgvector, this application does not currently create or use vector embeddings.
