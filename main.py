from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import asyncio
import os
from pydantic import BaseModel
from llm_service import generate_ai_response_with_llm

app = FastAPI()

# Setup templates directory
# Create a directory named templates if it doesn't exist
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
templates = Jinja2Templates(directory="templates")

# In-memory storage for simplicity
app_state = {
    "cv": "",
    "job_role": "",
    "interview_context": [] # to store the transcript history
}

class UserData(BaseModel):
    cv: str
    job_role: str

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"app_state": app_state})

@app.post("/setup")
async def setup_data(cv: str = Form(...), job_role: str = Form(...)):
    app_state["cv"] = cv
    app_state["job_role"] = job_role
    app_state["interview_context"] = [] # Reset context
    return {"message": "Setup successful", "cv_length": len(cv), "job_role_length": len(job_role)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connected")

    try:
        while True:
            # We expect JSON messages containing either audio data or transcript snippets
            # from the client.
            # Real deployment would use WebRTC or send binary audio frames here
            # to Deepgram or OpenAI Whisper.
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "interviewer_speech":
                # Received text from the interviewer (from client-side STT or server-side proxy)
                transcript = message["text"]
                print(f"Interviewer: {transcript}")

                app_state["interview_context"].append({"role": "interviewer", "text": transcript})

                # AI processing based on CV and Job Role for Supply Chain / Data Analytics
                response_script = await generate_ai_response_with_llm(
                    transcript,
                    app_state["cv"],
                    app_state["job_role"],
                    app_state["interview_context"]
                )

                await websocket.send_text(json.dumps({
                    "type": "ai_script",
                    "text": response_script
                }))

            elif message["type"] == "candidate_speech":
                # Candidate is speaking (reading the script or improvising)
                # We just track it to maintain context, but don't generate a response
                transcript = message["text"]
                print(f"Candidate: {transcript}")
                app_state["interview_context"].append({"role": "candidate", "text": transcript})

    except WebSocketDisconnect:
        print("WebSocket disconnected")
