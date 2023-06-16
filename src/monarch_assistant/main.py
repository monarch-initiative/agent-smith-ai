from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from os.path import abspath, dirname

from .tool_agent import new_chat_safeeval_agent, continue_chat
from .models import Chat, Message

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# endpoint for starting a new chat
@app.post("/new_chat")
def new_chat_endpoint(model: str = "gpt-3.5-turbo") -> Chat:
    """Starts a new, empty chat"""
    #chat: Chat = [{"role": "user", "content": "test", "thoughts": []}]
    #return chat

    result = new_chat_safeeval_agent(model = model)

    # import pprint
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(result)

    return result

# endpoint for continuing a chat. The messages are passed in as a JSON object in the body of the request
@app.post("/continue_chat")
def continue_chat_endpoint(messages: Chat, user_message: str, model: str = "gpt-3.5-turbo") -> Chat:
    """Continues a chat with the given user message."""

    result = continue_chat(messages, user_message, model = model)

    return result

# Serve static files needed for OpenAI plugin
app.mount("/static", StaticFiles(directory=dirname(abspath(__file__)) + "/static"), name="static")


