# Standard library imports
from datetime import datetime
import inspect
import os
import pprint
import json
from typing import Any, Dict, List, get_args, get_origin

# Third party imports
from docstring_parser import parse
import openai
import dotenv

# Local application imports
from monarch_assistant.openapi_wrapper import APIWrapperSet 
from monarch_assistant.models import *


dotenv.load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]

pp = pprint.PrettyPrinter(indent=4, width = 80, sort_dicts = False, compact = False)



def python_type_to_json_schema(py_type):
    """Translate Python typing annotation to JSON schema-like types."""
    origin = get_origin(py_type)
    if origin is None:  # means it's a built-in type
        return {'type': 'number' if py_type is float else 'string'}
    elif origin is list:
        item_type = get_args(py_type)[0]
        return {'type': 'array', 'items': python_type_to_json_schema(item_type)}

def generate_schema(fn):
    """Generate JSON schema for a function."""
    docstring = parse(fn.__doc__)
    sig = inspect.signature(fn)
    params = sig.parameters
    schema = {
        'name': fn.__name__,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': list(params.keys())
        },
        'description': docstring.short_description,
    }
    for p in docstring.params:
        schema['parameters']['properties'][p.arg_name] = {
            **python_type_to_json_schema(params[p.arg_name].annotation),
            'description': p.description
        }
    return schema




class UtilityAgent:
    def __init__(self, name: str = "Assistant", system_message: str = "You are a helpful assistant"):
        self.name = name
        self.system_message = system_message
        self.history = Chat(messages = [Message(role = "system", content = self.system_message, author = "System")])
    
        self.api_set = APIWrapperSet([])
        self.callable_methods = ["time", "print_history"]

    def register_api(self, name: str, spec_url: str, base_url: str):
        self.api_set.add_api(name, spec_url, base_url)

    def register_callable_method(self, method_name: str):
        self.callable_methods.append(method_name)

    def get_method_schemas(self):
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        return [generate_schema(m[1]) for m in methods if m[0] in self.callable_methods]


    def call_method(self, method_name: str, params: dict):
        method = getattr(self, method_name, None)
        if method is not None and callable(method):
            result = method(**params)
            if inspect.isgenerator(result):
                yield from result
            else:
                yield result
        else:
            raise ValueError(f"No such method: {method_name}")


    def print_history(self):
        """Prints the full chat history to the console.
        
        Returns: None
        """
        pp.pprint(self.history.dict())

    def time(self):
        """Get the current date and time.

        Returns: MM/DD/YY HH:MM formatted string.
        """
        now = datetime.now()
        formatted_now = now.strftime("%m/%d/%y %H:%M")
        return formatted_now



    def new_chat(self, user_message: str, yield_system_message = False, yield_prompt_message = False, author = "User", model: str = "gpt-3.5-turbo-0613") -> Chat:
        """Starts a new chat with the given system message and user message.
        If the response contains <eval> tags, a response back to the model with the evaluated results will be added to the conversation. See the replace_eval_tags() function for more details.
        Example usage: start_new_chat("You are a helpful assistant.", "Hi!")"""
        self.history = Chat(messages = [Message(role = "system", content = self.system_message, author = "System")])

        if yield_system_message:
            yield self.history.messages[0]

        user_message = Message(role = "user", content = user_message, author = author)

        if yield_prompt_message:
            yield user_message

        self.history.messages.append(user_message)

        try:
            response_raw = openai.ChatCompletion.create(
                      model=model,
                      temperature = 0,
                      messages = self.deserialize_chat(self.history),
                      functions = self.api_set.get_function_schemas() + self.get_method_schemas(),
                      function_call = "auto")
            
            for message in self.process_model_response(response_raw, model = model):
                self.history.messages.append(message)
                ## TODO: check for running out of context length here and delegate to summarizer agent to refresh confo if needed
                yield message
        except Exception as e:
            yield Message(role = "assistant", content = f"Error in attempted function call: {str(e)}", author = self.name)



    def continue_chat(self, new_user_message: str, yield_prompt_message = False, author = "User", model: str = "gpt-3.5-turbo-0613") -> Chat:
        """Continues a chat with the given messages and new user message.
        If the response contains <eval> tags, a response back to the model with the evaluated results will be added to the conversation. See the replace_eval_tags() function for more details.
        Example usage: continue_chat([{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hi!"}, {"role": "assistant", "content": "Hello, how can I help today?"}], "What are pillows?")"""

        new_user_message = Message(role = "user", content = new_user_message, author = author)

        if yield_prompt_message:
            yield new_user_message

        self.history.messages.append(new_user_message)

        try:
            response_raw = openai.ChatCompletion.create(
                      model=model,
                      temperature = 0,
                      messages = self.deserialize_chat(self.history),
                      functions = self.api_set.get_function_schemas() + self.get_method_schemas(),
                      function_call = "auto")

            for message in self.process_model_response(response_raw, model = model):
                self.history.messages.append(message)
                ## TODO: check for running out of context length here and delegate to summarizer agent to refresh confo if needed
                yield message
        except Exception as e:
            yield Message(role = "assistant", content = f"Error in attempted function call: {str(e)}", author = self.name)


    def process_model_response(self, response_raw, model = "gpt-3.5-turbo-0613") -> Chat:
        finish_reason = response_raw["choices"][0]["finish_reason"]
        message = response_raw["choices"][0]["message"]

        if "function_call" not in message:
            new_message = Message(role = message["role"], 
                                  content = message["content"], 
                                  finish_reason = finish_reason, 
                                  author = self.name,
                                  is_function_call = False)
            yield new_message
            return None
        else:
            func_name = message["function_call"]["name"]
            func_arguments = json.loads(message["function_call"]["arguments"])

            new_message = Message(role = message["role"], 
                                  content = message["content"],
                                  is_function_call = True,
                                  name = func_name, 
                                  author = self.name + " (function call)",
                                  arguments = func_arguments)
            yield new_message

            if func_name in self.api_set.get_function_names():
                func_result = self.api_set.call_endpoint({"name": func_name, "arguments": func_arguments})
                if func_result["status_code"] == 200:
                    func_result = json.dumps(func_result["data"])
                else:
                    func_result = f"Sorry, there seems to have been an issue with the API call. {json.dumps(func_result)}"

                new_message = Message(role = "function", 
                                      content = func_result, 
                                      name = func_name, 
                                      author = self.name + " (function response)",
                                      is_function_call = False)
                yield new_message
                
            elif func_name in self.callable_methods:
                try:
                    # call_method is a generator, even if the method it's calling is not
                    # but if the method being called is a generator, it yields from the called generator
                    # so regardless, we are looping over results, but each to see if hte result is already a message (as 
                    # will happen in the case of a method that calls a sub-agent)
                    func_result = self.call_method(func_name, func_arguments)
                    for potential_message in func_result:
                        if isinstance(potential_message, Message):
                            yield potential_message
                        else:
                            new_message = Message(role = "function", 
                                                  content = json.dumps(potential_message), 
                                                  name = func_name, 
                                                  author = self.name + " (function response)",
                                                  is_function_call = False)
                            yield new_message


                except ValueError as e:
                    yield Message(role = "function",
                                  content = f"Error in attempted function call: {str(e)}",
                                  name = func_name,
                                  author = self.name + " (function response)",
                                  is_function_call = False)

        # if we've gotten here, there was a function call and a result
        # now we send the funciton call result back to the model for it to work with
        # the result might be *another* function call, so it is processed recursively
        try:
            reponse_raw = openai.ChatCompletion.create(
                              model=model,
                              temperature = 0,
                              messages = self.deserialize_chat(self.history),
                              functions = self.api_set.get_function_schemas() + self.get_method_schemas(),
                              function_call = "auto")
            
            for message in self.process_model_response(reponse_raw, model = model):
                yield message

        except Exception as e:
            yield Message(role = "assistant", content = f"Error in attempted function call: {str(e)}", author = self.name)


    def deserialize_message(self, message: Message) -> Dict[str, Any]:
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


    def deserialize_chat(self, chat: Chat) -> List[Dict[str, Any]]:
        """Deserializes a chat object into a list of dictionaries of arguments; for converting internal chat format to the format used by the OpenAI API."""
        messages = []
        for message in chat.messages:
            messages.append(self.deserialize_message(message))
        return messages


