"""Command line interface for monarch-assistant."""
import click
import logging
import pprint
import json
import os

from monarch_assistant import __version__
from monarch_assistant.tool_agent import UtilityAgent
from monarch_assistant.models import *

from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from rich.panel import Panel
from colorama import Style

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

#console = Console(width = OUTPUT_WIDTH)
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



def log_message(message: Message, output_width = 100):
#    global console
    """Logs a message to the console."""



    if message.role == "user":
        render_panel(message.content, message.author, style = "cyan")
    elif message.role == "assistant":
        if(message.content):
            render_panel(message.content, message.author, style = "blue")
        if(message.is_function_call and os.environ["SHOW_FUNCTION_CALLS"] == 'True'):
            render_panel(f"```\n{message.name}(params = {message.arguments})\n```", message.author, style = "default")
    elif message.role == "function" and os.environ["SHOW_FUNCTION_CALLS"] == 'True':
            render_panel(message.content, message.author, style = "default", newline = False)

#    console = Console(width = OUTPUT_WIDTH)



class MonarchAgent(UtilityAgent):
    def __init__(self, name: str):

        self.name = name
        self.system_message = """
You are a Monarch Assistant named {self.name}, an AI-powered chatbot that can answer questions about data from the Monarch Initiative knowledge graph. 
You can search for entities such as genes, diseases, and phenotypes by name to get the associated ontology identifier. 
You can retrieve associations between entities via their identifiers. 
Users may use synonyms such as 'illness' or 'symptom'. Do not assume the user is familiar with biomedical terminology. 
Always add additional information such as lay descriptions of phenotypes. 
If the user changes the show function call setting, do not make any further function calls immediately.
IMPORTANT: Include markdown-formatted links to the Monarch Initiative for all results using the templates provided by function call responses.'.
"""

        super().__init__(name, self.system_message)

        self.register_api("monarch", "https://oai-monarch-plugin.monarchinitiative.org/openapi.json", "https://oai-monarch-plugin.monarchinitiative.org")
        self.register_callable_method("example_queries")


    def example_queries(self, num_examples: int):
        """
        Generate example queries for the Monarch API.

        Args:
            num_examples: The number of example queries to generate.

        Returns: 
            A list of example queries.
        """
        util_agent = UtilityAgent("SubAgent")
        yield from util_agent.new_chat(f"Please provide {num_examples} example questions one could ask about the Monarch Initiative Knowledge graph. And report the time.", author = self.name + " (in function call)", yield_prompt_message = True)


@main.command()
def run():
    """Run the monarch-assistant's demo command."""

    log_message(Message(role="assistant", content="""Hello! I'm the Monarch Assistant, an AI-powered chatbot that can answer questions about genes, diseases, and phenotypes, based on information hosted at https://monarchinitiative.org.
* You can exit by saying 'exit', and you can request that I turn on or off function call responses by saying 'show function calls' or 'hide function calls' at any time. They are shown by default.
* I do not currently implement context-window management, so after a while your conversation will produce an error.
* For a bit of fun, try asking me to describe my plan. For example, "What are the symptoms of Cystic Fibrosis? Describe your plan before you execute it."
""", author="Monarch Assistant"))

    agent = MonarchAgent("Monarch Assistant")

    user_input = session.prompt([('class:prompt', 'User: ')])

    for message in agent.new_chat(user_input):
        log_message(message)

    while user_input != "exit":
        user_input = session.prompt([('class:prompt', 'User: ')])

        for message in agent.continue_chat(user_input):
            log_message(message)



if __name__ == "__main__":
    main()
