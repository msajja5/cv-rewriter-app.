from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import logging
from typing import List, Dict
import json
from llm_service import generate_ai_response_with_llm_stream, _mock_response

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
    response_style: str = "normal"
    target_role_family: str = "Auto Detect"

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    try:
        return templates.TemplateResponse(request=request, name="index.html", context={})
    except Exception as e:
        logger.error(f"Error serving homepage: {str(e)}")
        return HTMLResponse(content="<h1>Internal Server Error loading homepage.</h1>", status_code=500)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, req: Request):
    """
    Stateless streaming endpoint for Serverless execution (e.g. Vercel).
    """
    logger.info(f"Received chat streaming request for role: {request.job_role}")

    # Pass any custom API keys supplied from the frontend via headers
    custom_keys = {
        "X-Gemini-Key": req.headers.get("X-Gemini-Key"),
        "X-Groq-Key": req.headers.get("X-Groq-Key"),
        "X-Or-Key": req.headers.get("X-Or-Key")
    }

    async def stream_tokens_with_keys(req_body: ChatRequest, keys: dict):
        try:
            async for chunk in generate_ai_response_with_llm_stream(
                question=req_body.transcript,
                cv=req_body.cv,
                job_role=req_body.job_role,
                context=req_body.context,
                response_style=req_body.response_style,
                target_role_family=req_body.target_role_family,
                custom_keys=keys
            ):
                # Format as Server-Sent Events (SSE)
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'content': 'Server error generating response.'})}\n\n"

    return StreamingResponse(
        stream_tokens_with_keys(request, custom_keys),
        media_type="text/event-stream"
    )
