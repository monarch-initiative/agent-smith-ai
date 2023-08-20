from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from uuid import uuid4

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

class AgentServer:
    def __init__(self, agent_class, name: str = "Agent Smith"):
        self.app = FastAPI(title=name)

        # Setup CORS for the FastAPI app (for dev)
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


        BUILD_DIR = Path(__file__).parent / "frontend/build"

        # Websocket for chat
        self.app.websocket("/ws/chat/")(self.websocket_endpoint)

        # Mount the entire build directory at the root
        self.app.mount("/", StaticFiles(directory=str(BUILD_DIR), html=True), name="static")

        # Catch-all route to serve the index.html for any path not explicitly defined
        @self.app.get("/{full_path:path}")
        async def catch_all(full_path: str):
            return FileResponse(BUILD_DIR / "index.html")


        self.sessions = {}
        self.agent_class = agent_class
        self.name = name



    def get_agent_state(self, session_id=None):
        if not session_id:
            session_id = str(uuid4())
        agent = self.sessions.get(session_id)
        if not agent:
            agent = self.agent_class(name=self.name)
            self.sessions[session_id] = agent
        return agent, session_id


    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        while True:
            data = await websocket.receive_json()
            question = data.get("question")
            session_id = data.get("session_id")
            agent, session_id = self.get_agent_state(session_id)
            responses = agent.new_chat(question, yield_prompt_message=True)
            for message in responses:
                await websocket.send_json(message.model_dump())

