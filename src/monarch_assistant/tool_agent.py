import openai
import os
import re
from typing import Any, Dict, List, Optional, Union
import pprint
from datetime import datetime
import json
import requests
from asteval import Interpreter
from collections import Counter
from math import log2
from .safe_eval_tools import SafeEval
import pprint
import json
from .models import *
import dotenv

dotenv.load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]
safe_eval = SafeEval()
pp = pprint.PrettyPrinter(indent=4, width = 80, sort_dicts = False, compact = False)


## possible? hoping so:
# user: query
# model: function_call
# user: function_response
# model: function call 2
# user: function_response 2
# ...
# model: final answer


def start_new_chat_generic(system_message: Message, user_message: Message, model: str = "gpt-3.5-turbo-0613") -> Chat:
    """Starts a new chat with the given system message and user message.
    If the response contains <eval> tags, a response back to the model with the evaluated results will be added to the conversation. See the replace_eval_tags() function for more details.
    Example usage: start_new_chat("You are a helpful assistant.", "Hi!")"""

    initial_chat: Chat = Chat(messages = [system_message, user_message])

    response_raw = openai.ChatCompletion.create(
              model=model,
              temperature = 0,
              messages = deserialize_chat(initial_chat),
              functions = SafeEval().generate_function_schemas(),
              function_call = "auto")

    yield from process_model_response(initial_chat, response_raw, model = model)



def continue_chat(history: Chat, new_user_message: Message, model: str = "gpt-3.5-turbo-0613") -> Chat:
    """Continues a chat with the given messages and new user message.
    If the response contains <eval> tags, a response back to the model with the evaluated results will be added to the conversation. See the replace_eval_tags() function for more details.
    Example usage: continue_chat([{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hi!"}, {"role": "assistant", "content": "Hello, how can I help today?"}], "What are pillows?")"""

    history.messages.append(new_user_message)

    response_raw = openai.ChatCompletion.create(
              model=model,
              temperature = 0,
              messages=deserialize_chat(history),
              functions = SafeEval().generate_function_schemas(),
              function_call = "auto")

    yield from process_model_response(history, response_raw, model = model)


def process_model_response(history: Chat, response_raw, model = "gpt-3.5-turbo-0613") -> Chat:
    finish_reason = response_raw["choices"][0]["finish_reason"]
    message = response_raw["choices"][0]["message"]

    if "function_call" not in message:
        new_message = Message(role = message["role"], 
                              content = message["content"], 
                              finish_reason = finish_reason, 
                              is_function_call = False)
        history.messages.append(new_message)
        yield history
        return None
    else:
        func_name = message["function_call"]["name"]
        func_arguments = json.loads(message["function_call"]["arguments"])

        new_message = Message(role = message["role"], 
                              content = message["content"],
                              is_function_call = True,
                              name = func_name, 
                              arguments = func_arguments)
        history.messages.append(new_message)
        yield history

        func = SafeEval().get_function(func_name)
        func_result = func(**func_arguments)

        #function_call = FunctionCall(name = func_name, arguments = func_arguments, result = func_result)
        new_message = Message(role = "function", 
                              content = func_result, 
                              name = func_name, 
                              is_function_call = False)
        
        history.messages.append(new_message)
        yield history

    reponse_raw = openai.ChatCompletion.create(
                      model=model,
                      temperature = 0,
                      messages = deserialize_chat(history),
                      functions = SafeEval().generate_function_schemas(),
                      function_call = "auto")
    
    yield from process_model_response(history, reponse_raw, model = model)



def deserialize_message(message: Message) -> Dict[str, Any]:
    """Deserializes a message object into a dictionary of arguments; for converting internal messages format to the format used by the OpenAI API."""

    if message.is_function_call:
        return {"role": message.role, 
                    "content": message.content, 
                    "function_call": {"name": message.name,
                                      "arguments": json.dumps(message.arguments)}}
    if message.role == "function":
        return {"role": message.role, 
                    "name": message.name,
                    "content": message.content}
        
    return {"role": message.role, "content": message.content}


def deserialize_chat(chat: Chat) -> List[Dict[str, Any]]:
    """Deserializes a chat object into a list of dictionaries of arguments; for converting internal chat format to the format used by the OpenAI API."""
    messages = []
    for message in chat.messages:
        messages.append(deserialize_message(message))
    return messages
