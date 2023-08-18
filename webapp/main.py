import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agent_smith_ai.utility_agent import UtilityAgent

import dotenv
dotenv.load_dotenv()

app = FastAPI()


##### API #####

class ChatRequest(BaseModel):
    question: str

@app.post("/chat/")
async def chat(request_data: ChatRequest):
    question = request_data.question
    agent = UtilityAgent(name="Webapp Agent")
    responses = agent.new_chat(question, yield_prompt_message=True)
    messages = [message.model_dump() for message in responses]
    return {"responses": messages}




#### Frontend ####

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

@app.get("/manifest.json")
def get_manifest():
    return FileResponse(BASE_DIR / "frontend/build/manifest.json", media_type="application/json")


app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend/build/static"), name="static")

@app.get("/{path:path}")
def serve_root(path: str):
    return FileResponse(BASE_DIR / "frontend/build/index.html")


