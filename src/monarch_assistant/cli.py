"""Command line interface for monarch-assistant."""
import click
import logging

from monarch_assistant import __version__
from monarch_assistant.tool_agent import start_new_chat_generic, continue_chat
from monarch_assistant.models import Chat
from models import *
import pprint
import json
import os
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.text import Text
from rich.panel import Panel
from colorama import Fore, Style

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
import os

style = Style.from_dict({
    'prompt': '#00aaaa'
})
histfile = os.path.join(os.path.expanduser("~"), ".my_python_hist")
session = PromptSession(history=FileHistory(histfile), style=style)



OUTPUT_WIDTH = 100

console = Console(width = OUTPUT_WIDTH)
pp = pprint.PrettyPrinter(indent=4)

os.environ["SHOW_FUNCTION_CALLS"] = 'True'

__all__ = [
    "main",
]

logger = logging.getLogger(__name__)


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
@click.version_option(__version__)
def main(verbose: int, quiet: bool):
    """CLI for monarch-assistant.

    :param verbose: Verbosity while running.
    :param quiet: Boolean to be quiet or verbose.
    """
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)


def is_valid_json(myjson: str) -> bool:
    try:
        json.loads(myjson)
    except json.JSONDecodeError:
        return False
    return True


def render_panel(content: str, title: str, style = "default", title_align: str = "left", newline = True):
    """Renders a panel with the given content and title."""
    console = Console(width = OUTPUT_WIDTH)
    title = Text(title, style = style)
    if is_valid_json(content):
        content = "```json\n" + json.dumps(json.loads(content), indent = 4).strip() + "\n```"
    if newline:
        console.print()
    console.print(Panel(Markdown(f"{content}"), title = title, title_align=title_align))


def log_message(message: Message):
    global console
    """Logs a message to the console."""
    if message.role == "user":
        render_panel(message.content, "User", style = "cyan")
    elif message.role == "assistant":
        if(message.content):
            render_panel(message.content, "Assistant", style = "blue")
        if(message.is_function_call and os.environ["SHOW_FUNCTION_CALLS"] == 'True'):
            render_panel(f"{message.name}(params = {message.arguments})", "Function Call", style = "default")
    elif message.role == "function" and os.environ["SHOW_FUNCTION_CALLS"] == 'True':
            render_panel(message.content, "Function Response", style = "default", newline = False)

    console = Console(width = OUTPUT_WIDTH)


@main.command()
def run():
    """Run the monarch-assistant's demo command."""

    console.rule("Monarch Assistant")
    log_message(Message(role="assistant", content="""Hello! I am the Monarch Assistant, an AI-powered chatbot that can answer questions about genes, diseases, and phenotypes. I am a work in progress, and you shouldknow the following:
* I currently rely on https://github.com/monarch-initiative/oai-monarch-plugin, but am not at feature parity.
* You can exit by saying 'exit', and you can request that I turn on or off function call responses by saying 'show function calls' or 'hide function calls' at any time. They are shown by default.
* I do not currently implement context-window management, so after a while your conversation will produce an error.
* For a bit of fun, try asking me to describe my plan. For example, "What are the symptoms of Cystic Fibrosis? Describe your plan before you execute it."
"""))

    system_message: Message = Message(role="system", content="""
You are the Monarch Assistant, an AI-powered chatbot that can answer questions about data from the Monarch Initiative knowledge graph. 
You can search for entities such as genes, diseases, and phenotypes by name to get the associated ontology identifier. 
You can retrieve associations between entities via their identifiers. 
Users may use synonyms such as 'illness' or 'symptom'. Do not assume the user is familiar with biomedical terminology. 
Always add additional information such as lay descriptions of phenotypes. 
If the user changes the show function call setting, do not make any further function calls immediately.
IMPORTANT: Include markdown-formatted links to the Monarch Initiative for all results using the templates provided by function call responses.'.
""")

    user_input = session.prompt([('class:prompt', 'User: ')])

    new_message = Message(role="user", content=user_input)

    # Create a generator for the chat
    new_chat_generator = start_new_chat_generic(system_message, new_message, model = "gpt-3.5-turbo-16k-0613")
    for chat in new_chat_generator: # loops over potential function call sequences
        last_message = chat.messages[-1]
        log_message(last_message)

    while user_input != "exit":
        user_input = session.prompt([('class:prompt', 'User: ')])

        new_message = Message(role="user", content=user_input)
        continue_chat_generator = continue_chat(chat, new_message, model = "gpt-3.5-turbo-16k-0613")

        for chat in continue_chat_generator:
            last_message = chat.messages[-1]
            log_message(last_message)



if __name__ == "__main__":
    main()
