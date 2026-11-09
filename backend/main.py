from pathlib import Path
from datetime import date

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from openrouter import OpenRouter
from pydantic import BaseModel, Field, ConfigDict
import os
from sqlalchemy import text

load_dotenv(Path(__file__).resolve().with_name(".env"))

from db import engine

app = FastAPI()


class ReviewCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    tool_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)


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

@app.post("/add-review", status_code=201)
async def add_review(review: ReviewCreate):
    with engine.begin() as conn:
        tool = conn.execute(
            text("SELECT id FROM tool WHERE id = :tool_id"),
            {"tool_id": review.tool_id},
        ).first()
        if tool is None:
            raise HTTPException(status_code=404, detail="Tool not found")

        result = conn.execute(
            text("""
                INSERT INTO review (tool_id, rating, title, date, description)
                VALUES (:tool_id, :rating, :title, :date, :description)
                RETURNING id, tool_id, rating, title, date, description
            """),
            {**review.model_dump(), "date": date.today()},
        )
        saved_review = dict(result.mappings().one())

    return saved_review

@app.get("/get-reviews/{tool_id}")
def get_reviews(tool_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM review WHERE tool_id = :tool_id"),
            {"tool_id": tool_id},
        )

        reviews = result.mappings().all()

        output = []

        for row in reviews:
            output.append(dict(row))

        return output


        

