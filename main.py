from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import logging
from typing import List, Dict
from llm_service import generate_ai_response_with_llm

# Setup basic logging for Vercel Serverless Function logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Vercel's serverless environment has a read-only filesystem except for /tmp.
# Removing os.makedirs("templates", exist_ok=True) because it can throw a PermissionError
# if the directory doesn't exist, and the directory is already included in the Git repo.

# Use an absolute path for Jinja templates to ensure Vercel finds them correctly regardless of the CWD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)

class ChatRequest(BaseModel):
    cv: str
    job_role: str
    transcript: str
    context: List[Dict[str, str]]

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    try:
        return templates.TemplateResponse(request=request, name="index.html", context={})
    except Exception as e:
        logger.error(f"Error serving homepage: {str(e)}")
        return HTMLResponse(content="<h1>Internal Server Error loading homepage.</h1>", status_code=500)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Stateless endpoint for Serverless execution (e.g. Vercel).
    The frontend is responsible for maintaining and passing the interview context.
    """
    try:
        logger.info(f"Received chat request for role: {request.job_role}")
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
            "success": True,
            "response": response_script,
            "provider": provider
        }
    except Exception as e:
        logger.error(f"Error in /chat endpoint: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "An internal error occurred while processing the request.",
                "details": str(e),
                "provider": "Mock (Error Fallback)"
            }
        )
