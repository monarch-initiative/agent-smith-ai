"""Command line interface for monarch-assistant."""
import click
import logging

from monarch_assistant import __version__
from monarch_assistant.tool_agent import new_chat_safeeval_agent, continue_chat
from monarch_assistant.models import Chat

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

@main.command()
def run():
    """Run the monarch-assistant's demo command."""

    # create a new chat
    chat: Chat = new_chat_safeeval_agent()

    print("Assistant: Hello! I am the Monarch Assistant, an AI-powered chatbot that can answer questions about genes, diseases, and phenotypes. I am still learning, and cannot gaurantee that I will always give the correct answer. Enter 'exit' to exit. What would you like to know?")

    user_input = None
    while user_input != "exit":
        user_input = input("User: ")
        chat = continue_chat(chat, user_input)
        print("Assistant: " + chat.messages[-1].content)

if __name__ == "__main__":
    main()
