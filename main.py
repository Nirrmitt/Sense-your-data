import os
import re
from contextlib import asynccontextmanager
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, StringConstraints

load_dotenv()

Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.llm_client = None
    yield
    if app.state.llm_client is not None:
        await app.state.llm_client.close()


app = FastAPI(title="Ask Your Data API", lifespan=lifespan)


def get_llm_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured.")
    if app.state.llm_client is None:
        app.state.llm_client = AsyncOpenAI(api_key=api_key, timeout=30.0, max_retries=2)
    return app.state.llm_client


async def call_llm(question: str, system_prompt: str) -> str:
    try:
        max_tokens = min(int(os.getenv("MAX_TOKENS_LIMIT", "4096")), 4096)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="MAX_TOKENS_LIMIT must be an integer.") from exc
    response = await get_llm_client().chat.completions.create(
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        max_tokens=max_tokens,
        temperature=0,
    )
    content = response.choices[0].message.content
    if not content:
        raise HTTPException(status_code=502, detail="The model returned an empty response.")
    return content.strip()


def is_safe_query(query: str) -> bool:
    statement = query.strip()
    if not re.match(r"(?i)^select\b", statement):
        return False
    body = statement[:-1] if statement.endswith(";") else statement
    if ";" in body or "--" in statement or "/*" in statement:
        return False
    forbidden = r"\b(insert|update|delete|drop|truncate|alter|create|grant|revoke|copy|call|do|set|reset|into)\b"
    return re.search(forbidden, statement, flags=re.IGNORECASE) is None

@app.get("/")
def read_root():
    return {"message": "RetailIQ API is running"}

class TextToSQLRequest(BaseModel):
    question: Question

@app.post("/sql")
async def text_to_sql(request: TextToSQLRequest):
    system_prompt = """Generate one read-only PostgreSQL SELECT query for this schema:
products(id, name, category, price)
sales(id, product_id, quantity, date)
Return SQL only. Never modify data or use comments."""
    try:
        raw_sql = await call_llm(request.question, system_prompt)
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail="The language model request failed.") from exc
    if not is_safe_query(raw_sql):
        raise HTTPException(status_code=502, detail="The model did not return a safe SELECT query.")

    return {"query": raw_sql}

@app.post("/rag")
async def rag_search():
    raise HTTPException(status_code=503, detail="Document retrieval is not configured.")

@app.get("/eval/health")
def eval_health():
    return {"status": "Evaluation Harness Ready"}
