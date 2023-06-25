from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class Message(BaseModel):
    """A message in a chat conversation, in internal representation, with RawMessages being accompanied by lists of thoughts."""
    role: str
    is_function_call: bool = False
    content: Optional[str] = None
    name: Optional[str] = None # for function call results
    arguments: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None

class Chat(BaseModel):
    """A chat conversation."""
    messages: List[Message] = []




# for function JSON schema sent to the model

class ParameterProperty(BaseModel):
    type: str
    description: Optional[str] = None
    enum: Optional[List[str]] = None

class Parameter(BaseModel):
    type: str
    properties: Dict[str, ParameterProperty]
    required: List[str]

class Function(BaseModel):
    name: str
    description: str
    parameters: Parameter

class FunctionList(BaseModel):
    __root__: List[Function]     # type aliasing, cool!
