from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from openrouter import OpenRouter
import os
from sqlalchemy import text
from db import engine 

load_dotenv(Path(__file__).resolve().with_name(".env"))

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/prompt")
async def func():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or not api_key.strip():
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY is not configured")

    with OpenRouter(api_key=api_key) as client:
        response = client.responses.send(
            model="~openai/gpt-sol-latest",
            input="What is the meaning of life?",
        )

        if response.status != "completed":
            message = response.error.message if response.error else f"Response ended as {response.status}"
            raise RuntimeError(message)

        message = next(item for item in response.output if item.type == "message")
        print(next(part.text for part in message.content if part.type == "output_text"))


@app.get("/tools")
async def get_tools(
    amount: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT * FROM tool
                ORDER BY name, id
                LIMIT :amount OFFSET :offset
            """),
            {"amount": amount, "offset": offset}
        ) 

        rows = result.mappings().all()

        tools = []
        for row in rows:
            tools.append(dict(row))

        return {
            "tools": tools,
            "count": len(tools),
            "hasMore": len(tools) == amount 
        }

@app.get("/tool/{id}")
async def get_tool(id: int):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT * FROM tool
                WHERE id = :id
                LIMIT 1
            """),
            {"id": id}
        ) 

        tool = result.mappings().first()

        if not tool:
            raise HTTPException(
                status_code=404,
                detail="Tool not found"
            )

        return dict(tool)
        

