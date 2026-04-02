from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import logging
from typing import List, Dict
from llm_service import generate_ai_response_with_llm, _mock_response

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
        response_dict, provider = await generate_ai_response_with_llm(
            question=transcript,
            cv=request.cv,
            job_role=request.job_role,
            context=request.context,
            response_style=request.response_style,
            target_role_family=request.target_role_family
        )

        return {
            "success": True,
            "response": response_dict["script"],
            "intent": response_dict["intent"],
            "answer_strategy": response_dict.get("answer_strategy", "Unknown"),
            "role_family": response_dict["role_family"],
            "cv_facts": response_dict["cv_facts"],
            "jd_signals": response_dict["jd_signals"],
            "provider": provider
        }
    except Exception as e:
        logger.error(f"Error in /chat endpoint: {str(e)}", exc_info=True)
        # Attempt to generate a proper mock response to keep the UI completely functional
        try:
            from domain_knowledge import detect_role_family
            role_fam = request.target_role_family if request.target_role_family != "Auto Detect" else detect_role_family(request.job_role)
            fallback_dict = _mock_response(transcript, request.cv, request.job_role, request.response_style, role_fam)
        except Exception as e2:
            logger.error(f"Error in /chat endpoint mock fallback: {str(e2)}", exc_info=True)
            fallback_dict = {
                "script": "Yeah, absolutely. I couldn't connect to the live AI provider right now, but jumping into safe fallback mode—please continue with the interview.",
                "intent": "Error Fallback",
                "answer_strategy": "Error Fallback",
                "role_family": "Error",
                "cv_facts": "None",
                "jd_signals": "None"
            }

        # Return 200 so the frontend fetch() sees response.ok = true
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "response": fallback_dict["script"],
                "intent": fallback_dict["intent"],
                "answer_strategy": fallback_dict.get("answer_strategy", "Unknown"),
                "role_family": fallback_dict["role_family"],
                "cv_facts": fallback_dict["cv_facts"],
                "jd_signals": fallback_dict["jd_signals"],
                "error": str(e),
                "provider": "Mock (Error Fallback)"
            }
        )
