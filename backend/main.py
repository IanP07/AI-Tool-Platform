from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openrouter import OpenRouter
import os

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
