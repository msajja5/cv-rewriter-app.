from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
from typing import List, Dict
from llm_service import generate_ai_response_with_llm

app = FastAPI()

os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

class ChatRequest(BaseModel):
    cv: str
    job_role: str
    transcript: str
    context: List[Dict[str, str]]

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Stateless endpoint for Serverless execution (e.g. Vercel).
    The frontend is responsible for maintaining and passing the interview context.
    """
    transcript = request.transcript

    # We append the current interviewer's question to the context history inside the LLM service.
    # The frontend manages the overarching context.
    response_script, provider = await generate_ai_response_with_llm(
        question=transcript,
        cv=request.cv,
        job_role=request.job_role,
        context=request.context
    )

    return {
        "response": response_script,
        "provider": provider
    }
