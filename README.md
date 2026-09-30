# RetailIQ: Ask Your Data

## Project Overview
A text-to-SQL and RAG analytics assistant built on FastAPI/PostgreSQL with an evaluation harness.

## Stack
- Backend: FastAPI, Python
- DB: PostgreSQL + pgvector (Vector Store)
- LLM: OpenAI (via API)
- Frontend: Streamlit
- Eval: Built-in Harness

## Setup
1. Install the packages with `python -m pip install -r requirements.txt`.
2. Set a valid `OPENAI_API_KEY` in `.env` to enable SQL generation.
3. Start PostgreSQL with `docker-compose up -d`.
4. Create the database tables with `python setup_db.py`.
5. Start the API with `uvicorn main:app --reload`.
6. In a second terminal, start the UI with `streamlit run app/streamlit_app.py`.

## Evaluation
With the API running, run `python eval_harness.py` to check the API health endpoints. This is a startup smoke test, not a SQL accuracy benchmark.

## Current Scope
- The SQL endpoint generates and checks a read-only `SELECT` query; it does not execute that query.
- The RAG endpoint returns HTTP 503 until document ingestion and retrieval are configured.
- SQL safety checks are a guard on generated output, not a substitute for database permissions if query execution is added.

## Deployment
PostgreSQL with pgvector is started by `docker-compose.yml`. The API and Streamlit UI currently run as local processes.
