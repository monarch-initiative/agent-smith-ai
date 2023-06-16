from typing import List
from pydantic import BaseModel

class RawMessage(BaseModel):
    """A message in a chat conversation, sans thoughts; used for passing to the OpenAI API"""
    role: str
    content: str

class Thought(BaseModel):
    """A thought in a chat conversation. The thunk content will typically have <eval> tags and the role will typically be "assistant", and the result is the evaluated response with role "user"."""
    # a thunk and result could maybe be full Messaages with their own thoughts for some recursive fun
    # but for now, they are just RawMessages
    thunk: RawMessage
    result: RawMessage

class Message(RawMessage):
    """A message in a chat conversation, in internal representation, with RawMessages being accompanied by lists of thoughts."""
    thoughts: List[Thought] = []

class Chat(BaseModel):
    """A chat conversation."""
    messages: List[Message] = []
