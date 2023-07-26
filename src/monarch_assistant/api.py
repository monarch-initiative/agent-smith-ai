from fastapi import FastAPI
from monarch_assistant.tool_agent import start_new_chat_generic, continue_chat as agent_continue_chat
from monarch_assistant.models import Chat, Message


app = FastAPI()

@app.post("/newchat")
def new_chat(system_message: Message, user_message: Message) -> Chat:
    chats = list(start_new_chat_generic(system_message = system_message, user_message = user_message))
    return chats[len(chats) - 1]

@app.post("/continue-chat")
def continue_chat_route(chat: Chat, user_input: Message) -> Chat:
    updated_chats = list(agent_continue_chat(chat, user_input))
    return updated_chats[len(updated_chats) - 1]
