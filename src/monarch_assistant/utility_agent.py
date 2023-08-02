# Standard library imports
from datetime import datetime
import inspect
import os
import json
from typing import Any, Dict, List, Union, Literal, get_args, get_origin

# Third party imports
from docstring_parser import parse
import openai
import tiktoken

# Local application imports
from monarch_assistant.openapi_wrapper import APIWrapperSet 
from monarch_assistant.models import *



class UtilityAgent:
    def __init__(self, name: str = "Assistant", system_message: str = "You are a helpful assistant.", model: str = "gpt-3.5-turbo-0613", openai_api_key = None):
        if openai_api_key is not None:
            openai.api_key = openai_api_key
        elif "OPENAI_API_KEY" in os.environ:
            openai.api_key = os.environ["OPENAI_API_KEY"]
        else:
            raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable or provide it during agent instantiation.")

        self.model = model
        self.name = name
        self.system_message = system_message
        self.history = Chat(messages = [Message(role = "system", content = self.system_message, author = "System", intended_recipient = self.name)])
    
        self.api_set = APIWrapperSet([])
        self.callable_methods = []

        self.function_schema_tokens = None # to be computed later if needed by _count_function_schema_tokens, which costs a couple of messages and is cached
        self.register_callable_methods(["time", "help"])



    def register_api(self, name: str, spec_url: str, base_url: str, callable_endpoints: List[str] = []):
        self.api_set.add_api(name, spec_url, base_url, callable_endpoints)

    def register_callable_methods(self, method_names: List[str]):
        for method_name in method_names:
            self.callable_methods.append(method_name)


    def _get_method_schemas(self):
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        return [_generate_schema(m[1]) for m in methods if m[0] in self.callable_methods]


    def _call_method(self, method_name: str, params: dict):
        method = getattr(self, method_name, None)
        if method is not None and callable(method):
            result = method(**params)
            if inspect.isgenerator(result):
                yield from result
            else:
                yield result
        else:
            raise ValueError(f"No such method: {method_name}")


    def _count_history_tokens(self) -> int:
        """
        Uses the tiktoken library to count the number of tokens stored in self.history.
        """
        history_tokens = _num_tokens_from_messages(self._reserialize_chat(self.history), model = self.model)
        return history_tokens


    def _count_function_schema_tokens(self, force_update: bool = True) -> int:
        """
        Uses the tiktoken library to count the number of tokens in the function schemas.

        Args:
            force_update (bool): If true, recompute the function schemas. Otherwise, use the cached count.

        Returns:
            The number of tokens in the function schemas.
        """

        if self.function_schema_tokens is not None and not force_update:
            return self.function_schema_tokens

        response_raw_w_functions = openai.ChatCompletion.create(
                  model=self.model,
                  temperature = 0,
                  messages = [{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'hi'}],
                  functions = self.api_set.get_function_schemas() + self._get_method_schemas(),
                  function_call = "auto")
       
        response_raw_no_functions = openai.ChatCompletion.create(
                  model=self.model,
                  temperature = 0,
                  messages = [{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'hi'}])

        diff = response_raw_w_functions['usage']['prompt_tokens'] - response_raw_no_functions['usage']['prompt_tokens']

        self.function_schema_tokens = diff + 2 # I dunno why 2, a simple diff is just 2 off
        return diff


    def help(self):
        """Returns information about this agent, including a list of callable methods and functions."""
        return {"callable_methods": self._get_method_schemas() + self.api_set.get_function_schemas(), 
                "system_prompt": self.system_message,
                "name": self.name,
                "chat_history_length": len(self.history.messages),
                "model": self.model}

    def time(self):
        """Get the current date and time.

        Returns: MM/DD/YY HH:MM formatted string.
        """
        now = datetime.now()
        formatted_now = now.strftime("%m/%d/%y %H:%M")
        return formatted_now



    def new_chat(self, user_message: str, yield_system_message = False, yield_prompt_message = False, author = "User") -> Chat:
        """Starts a new chat with the given system message and user message.
        If the response contains <eval> tags, a response back to the model with the evaluated results will be added to the conversation. See the replace_eval_tags() function for more details.
        Example usage: start_new_chat("You are a helpful assistant.", "Hi!")"""
        self.history = Chat(messages = [Message(role = "system", content = self.system_message, author = "System", intended_recipient = self.name)])

        if yield_system_message:
            yield self.history.messages[0]

        user_message = Message(role = "user", content = user_message, author = author, intended_recipient = self.name)

        if yield_prompt_message:
            yield user_message

        self.history.messages.append(user_message)
        
        try:
            response_raw = openai.ChatCompletion.create(
                      model=self.model,
                      temperature = 0,
                      messages = self._reserialize_chat(self.history),
                      functions = self.api_set.get_function_schemas() + self._get_method_schemas(),
                      function_call = "auto")

            for message in self._process_model_response(response_raw, intended_recipient = author):
                self.history.messages.append(message)
                ## TODO: check for running out of context length here and delegate to summarizer agent to refresh confo if needed
                yield message
        except Exception as e:
            yield Message(role = "assistant", content = f"Error in new chat creation: {str(e)}", author = "System", intended_recipient = author)



    def continue_chat(self, new_user_message: str, yield_prompt_message = False, author = "User") -> Chat:
        """Continues a chat with the given messages and new user message.
        If the response contains <eval> tags, a response back to the model with the evaluated results will be added to the conversation. See the replace_eval_tags() function for more details.
        Example usage: continue_chat([{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hi!"}, {"role": "assistant", "content": "Hello, how can I help today?"}], "What are pillows?")"""

        new_user_message = Message(role = "user", content = new_user_message, author = author, intended_recipient = self.name)


        self.history.messages.append(new_user_message)

        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)

        # num_tokens = _num_tokens_from_messages(self._reserialize_chat(self.history), model = self.model) + self._count_function_schema_tokens()
        # new_history = None
        # print(num_tokens)
        # if num_tokens > 500:
        #     #yield Message(role = "assistant", content = "Ah, just a second, our conversation is getting a bit long. Let me collect my thoughts.", author = self.name, intended_recipient = author)
        #     self.history.messages[-1].content = "First, summarize our conversation so far, then answer the following question:\n\n" + new_user_message.content
        #     new_history =  Chat(messages = [Message(role = "system", content = self.system_message, author = "System", intended_recipient = self.name)])
        #     new_history.messages.append(self.history.messages[-1])

        if yield_prompt_message:
            yield new_user_message



        # if summary is not None:
        #     summary = "This message is a continuation of a previous conversation, summarized as follows:\n\n" + summary + "\n\n" + "Please respond to the following user input:\n\n" + new_user_message.content
        #     yield from self.new_chat(summary, yield_prompt_message = False, author = author)
        #     return None

        try:
            response_raw = openai.ChatCompletion.create(
                      model=self.model,
                      temperature = 0,
                      messages = self._reserialize_chat(self.history),
                      functions = self.api_set.get_function_schemas() + self._get_method_schemas(),
                      function_call = "auto")

            for message in self._process_model_response(response_raw, intended_recipient = author):
                self.history.messages.append(message)
                ## TODO: check for running out of context length here and delegate to summarizer agent to refresh confo if needed
                yield message
        except Exception as e:
            yield Message(role = "assistant", content = f"Error in attempted continue chat: {str(e)}", author = "System", intended_recipient = author)

        ## TODO: implement rolling summarization
        ## Q: start new chat w/ updated system dialog maybe? in which case I'd need to keep track of the original system message,
        ## otherwise 
        # summary = self._summarize_history(self)
        # if summary is not None:
        #     pass


    # def _summarize_and_respond(self, new_user_message) -> str:
    #     """If the number of tokens in the history exceeds the given threshold, summarize the history and return the summary.
            
    #     Returns:
    #         The summary of the history, or None if no summarization was performed."""
        
    #     summary_agent = UtilityAgent("Summarizer", "You are a summarizer agent. Your goal is to *accurately* summarize the given conversation to be approximately one quarter its current size. You will be providing this information to another agent who will continue the conversation from the summary, so be sure to include all relevant information.")
    #     query = "Please summarize the following conversation for a new agent to continue from:" + "\n\n" + "\n\n".join([f"{m.author}: {m.content}" for m in self.history.messages[1:]]) # don't summarize the system message
    #     result = list(summary_agent.new_chat(query))[-1].content
    #     return result


    def _process_model_response(self, response_raw, intended_recipient) -> Chat:
        finish_reason = response_raw["choices"][0]["finish_reason"]
        message = response_raw["choices"][0]["message"]

        ## The model is not trying to make a function call, 
        ## so we just return the message as-is
        if "function_call" not in message:
            new_message = Message(role = message["role"], 
                                  content = message["content"], 
                                  finish_reason = finish_reason, 
                                  author = self.name,
                                  intended_recipient = intended_recipient,
                                  is_function_call = False)
            yield new_message
            ## do not continue, nothing more to do
            return None
        
        ## otherwise, the model is trying to call a function
        else:
            ## first we extract it (the call info) and format it as a message, yielding it to the stream
            func_name = message["function_call"]["name"]
            func_arguments = json.loads(message["function_call"]["arguments"])

            new_message = Message(role = message["role"], 
                                  content = message["content"],
                                  is_function_call = True,
                                  func_name = func_name, 
                                  author = self.name,
                                  ## the intended recipient is the calling agent, noted as a function call
                                  intended_recipient = f"{self.name} ({func_name} function)",
                                  func_arguments = func_arguments)
            yield new_message

            ## next we need to call the function and get the result
            ## if the function is an API call, we call it and yield the result
            if func_name in self.api_set.get_function_names():
                func_result = self.api_set.call_endpoint({"name": func_name, "arguments": func_arguments})
                if func_result["status_code"] == 200:
                    func_result = json.dumps(func_result["data"])
                else:
                    func_result = f"Error in attempted API call: {json.dumps(func_result)}"

                new_message = Message(role = "function", 
                                      content = func_result, 
                                      func_name = func_name, 
                                      ## the author is the calling agent's function
                                      author = f"{self.name} ({func_name} function)",
                                      ## the intended recipient is the calling agent
                                      intended_recipient = self.name,
                                      is_function_call = False)
                yield new_message
            
            ## if its not an API call, maybe it's one of the local callable methods
            elif func_name in self.callable_methods:
                try:
                    # call_method is a generator, even if the method it's calling is not
                    # but if the method being called is a generator, it yields from the called generator
                    # so regardless, we are looping over results, checking each to see if the result is 
                    # already a message (as will happen in the case of a method that calls a sub-agent)
                    func_result = self._call_method(func_name, func_arguments)
                    for potential_message in func_result:
                        # if it is a message already, just yield it to the stream
                        if isinstance(potential_message, Message):
                            yield potential_message
                        else:
                            # otherwise we turn the result into a message and yield it
                            new_message = Message(role = "function", 
                                                  content = json.dumps(potential_message), 
                                                  func_name = func_name, 
                                                  author = f"{self.name} ({func_name} function)",
                                                  intended_recipient = self.name,
                                                  is_function_call = False)
                            yield new_message


                except ValueError as e:
                    yield Message(role = "function",
                                  content = f"Error in attempted method call: {str(e)}",
                                  func_name = func_name,
                                  author = f"{self.name} ({func_name} function)",
                                  intended_recipient = self.name,
                                  is_function_call = False)
                    
            ## if the function isn't found, let the model know (this shouldn't happen)
            else:
                yield Message(role = "function",
                              content = f"Error: function {func_name} not found.",
                              func_name = None,
                              author = "System",
                              intended_recipient = self.name,
                              is_function_call = False
                              )
                
        # if we've gotten here, there was a function call and a result
        # now we send the result back to the model for summarization for the caller or,
        # the model may want to make *another* function call, so it is processed recursively using the logic above
        # (TODO? set a maximum recursive depth to avoid infinite-loop behavior)
        try:
            reponse_raw = openai.ChatCompletion.create(
                              model=self.model,
                              temperature = 0,
                              messages = self._reserialize_chat(self.history),
                              functions = self.api_set.get_function_schemas() + self._get_method_schemas(),
                              function_call = "auto")
        except Exception as e:
            yield Message(role = "assistant", content = f"Error in sending function or method call result to model: {str(e)}", author = "System", intended_recipient = intended_recipient)
            # if there was a failure in the summary/further work determination, we shouldn't try to do further work, just exit
            return None

        # the intended recipient of the summary/further work is still the original indended recipient            
        # and we just want to yield all the messages that come out
        yield from self._process_model_response(reponse_raw, intended_recipient = intended_recipient)



    def _reserialize_message(self, message: Message) -> Dict[str, Any]:
        """Deserializes a message object into a dictionary of arguments; for converting internal messages format to the format used by the OpenAI API."""

        if message.is_function_call:
            return {"role": message.role, 
                        "content": message.content, 
                        "function_call": {"name": message.func_name,
                                          "arguments": json.dumps(message.func_arguments)}}
        if message.role == "function":
            return {"role": message.role, 
                        "name": message.func_name,
                        "content": message.content}
            
        return {"role": message.role, "content": message.content}


    def _reserialize_chat(self, chat: Chat) -> List[Dict[str, Any]]:
        """Deserializes a chat object into a list of dictionaries of arguments; for converting internal chat format to the format used by the OpenAI API."""
        messages = []
        for message in chat.messages:
            messages.append(self._reserialize_message(message))
        return messages





def _python_type_to_json_schema(py_type):
    """Translate Python typing annotation to JSON schema-like types."""
    origin = get_origin(py_type)
    if origin is None:  # means it's a built-in type
        if py_type in [float, int]:
            return {'type': 'number'}
        elif py_type is str:
            return {'type': 'string'}
        elif py_type is bool:
            return {'type': 'boolean'}
        elif py_type is None:
            return {'type': 'null'}
        elif py_type is Any:
            return {'type': 'object'}
        else:
            raise NotImplementedError(f'Unsupported type: {py_type}')
    elif origin is list:
        item_type = get_args(py_type)[0]
        return {'type': 'array', 'items': _python_type_to_json_schema(item_type)}
    elif origin is dict:
        key_type, value_type = get_args(py_type)
        return {'type': 'object', 'properties': {
            'key': _python_type_to_json_schema(key_type),
            'value': _python_type_to_json_schema(value_type)
        }}
    elif origin is Union:
        return {'anyOf': [_python_type_to_json_schema(t) for t in get_args(py_type)]}
    elif origin is Literal:
        return {'enum': get_args(py_type)}
    elif origin is tuple:
        return {'type': 'array', 'items': [_python_type_to_json_schema(t) for t in get_args(py_type)]}
    elif origin is set:
        return {'type': 'array', 'items': _python_type_to_json_schema(get_args(py_type)[0]), 'uniqueItems': True}
    else:
        raise NotImplementedError(f'Unsupported type: {origin}')
    


def _generate_schema(fn):
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
            **_python_type_to_json_schema(params[p.arg_name].annotation),
            'description': p.description
        }
    return schema



## Straight from https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
def _num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        return _num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return _num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens
