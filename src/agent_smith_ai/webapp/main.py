import os
from pathlib import Path
from fastapi import FastAPI, Request, Depends, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agent_smith_ai.utility_agent import UtilityAgent
from uuid import uuid4

import dotenv
dotenv.load_dotenv()

app = FastAPI()

# allow CORS requests from localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

##### API #####

# In-memory storage for agent states
SESSIONS = {}

# Define a dependency to get or create the agent state for a session
def get_agent_state(request: Request):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        session_id = str(uuid4())  # Generate a new session ID if not provided
    agent = SESSIONS.get(session_id)
    if not agent:
        agent = UtilityAgent(name="Webapp Agent")
        SESSIONS[session_id] = agent
    return agent, session_id



@app.websocket("/ws/chat/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()

        question = data.get("question")

        session_id = data.get("session_id")
        if not session_id:
            session_id = str(uuid4())


        agent = SESSIONS.get(session_id)
        if not agent:
            agent = UtilityAgent(name="Webapp Agent")
            SESSIONS[session_id] = agent
        
        responses = agent.new_chat(question, yield_prompt_message=True)
        for message in responses:
            await websocket.send_json(message.model_dump())



#### Frontend ####

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

@app.get("/manifest.json")
def get_manifest():
    return FileResponse(BASE_DIR / "frontend/build/manifest.json", media_type="application/json")


app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend/build/static"), name="static")

@app.get("/{path:path}")
def serve_root(path: str):
    return FileResponse(BASE_DIR / "frontend/build/index.html")


