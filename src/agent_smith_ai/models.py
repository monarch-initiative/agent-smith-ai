from typing import Any, Dict, List, Optional
from pydantic import BaseModel, RootModel, Field


class Message(BaseModel):
    """A message in a chat conversation, in internal representation, with RawMessages being accompanied by lists of thoughts."""

    role: str
    """The role of the message, either "user", "assistant", or "function"; used by the OpenAI API."""

    author: str = None
    """The name of the author of the message, for example the name of the agent or user. Not currently heavily used."""

    intended_recipient: str = None
    """The name of the intended recipient of the message, for example the name of the agent or user. Not currently heavily used."""

    is_function_call: bool = False
    """Whether the message represents the model attemtpting to make a function call; will be True if role is 'function'."""

    content: Optional[str] = None
    """The content of the message, as used by the OpenAI API."""

    func_name: Optional[str] = None # for function call results
    """The function name the model is trying to call, if is_function_call is True."""

    func_arguments: Optional[Dict[str, Any]] = None
    """The function arguments the model is trying to pass, if is_function_call is True."""

    finish_reason: Optional[str] = None
    """The reason the conversation ended, as used by the OpenAI API; largely ignorable."""


class Chat(BaseModel):
    """A chat conversation."""

    messages: List[Message] = []
    """The messages in the conversation."""

# for function JSON schema sent to the model

class ParameterProperty(BaseModel):
    """A property of a function parameter, used to generate a JSON schema for the parameter."""

    type: str
    """The type of the property, for example "string" or "integer"."""

    description: Optional[str] = None
    """A description of the property, for example "The name of the user."."""

    enum: Optional[List[str]] = None
    """If the property is an enum, a list of the possible values."""


class Parameter(BaseModel):
    """A function parameter, used to generate a JSON schema for the parameter."""

    type: str
    """The type of the parameter, for example "object" or "string"."""

    properties: Dict[str, ParameterProperty]
    """The properties of the parameter, for example "name" or "age"."""

    required: List[str]
    """The required properties of the parameter, for example "name" or "age"."""


class Function(BaseModel):
    """A function, used to generate a JSON schema for the function."""

    name: str
    """The name of the function, for example "get_user_name"."""

    description: str
    """A description of the function, for example "Gets the name of the user."."""

    parameters: Parameter
    """The parameters of the function, for example "name" or "age"."""
