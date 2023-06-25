"""Command line interface for monarch-assistant."""
import click
import logging

from monarch_assistant import __version__
from monarch_assistant.tool_agent import start_new_chat_generic, continue_chat
from monarch_assistant.models import Chat
from models import *
import pprint
import json
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.text import Text
console = Console(width = 80)

from colorama import Fore, Style


pp = pprint.PrettyPrinter(indent=4)

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


def log_message(message: Message):
    """Logs a message to the console."""
    if message.role == "user":
        console.print(Markdown(f"{Fore.RED}User: {Style.RESET_ALL} {message.content}"))
    elif message.role == "assistant":
        if(message.content):
            console.print(Markdown(f"{Fore.BLUE}Assistant: {Style.RESET_ALL} {message.content}"))
        if(message.is_function_call):
            console.print(Markdown(f"{Fore.GREEN}Call: {Style.RESET_ALL}{message.name}({message.arguments})"))
    elif message.role == "function":
            console.print(Markdown(f"{Fore.CYAN}Call Result: {Style.RESET_ALL} {json.dumps(message.content)}"), overflow = "crop")


@main.command()
def run():
    """Run the monarch-assistant's demo command."""

    # create a new chat
    #chat: Chat = new_chat_safeeval_agent()
    console.rule("Monarch Assistant")
    sys.stdout.write(f"{Fore.BLUE}Assistant: {Style.RESET_ALL}")
    console.print("Hello! I am the Monarch Assistant, an AI-powered chatbot that can answer questions about genes, diseases, and phenotypes. I am still learning, and cannot guarantee that I will always give the correct answer. Enter 'exit' to exit. What would you like to know?")

    system_message: Message = Message(role="system", content="""
You are the Monarch Assistant, an AI-powered chatbot that can answer questions about data from the Monarch Initiative knowledge graph. 
You can search for entities such as genes, diseases, and phenotypes by name to get the associated ontology identifier. 
You can retrieve associations between entities via their identifiers. 
Users may use synonyms such as 'illness' or 'symptom'. Do not assume the user is familiar with biomedical terminology. 
Always add additional information such as lay descriptions of phenotypes. 
IMPORTANT: Include links to the Monarch Initiative for all results. For example, instead of 'Irregular hyperpigmentation', include a markdown link: '[Irregular hyperpigmentation](https://monarchinitiative.org/phenotype/HP:0007400)', and instead of 'Cystic Fibrosis', use '[Cystic Fibrosis](https://monarchinitiative.org/disease/MONDO:0009061)'.
""")
    user_input = input(f"{Fore.RED}User: {Style.RESET_ALL}")
    new_message = Message(role="user", content=user_input)

    # Create a generator for the chat
    new_chat_generator = start_new_chat_generic(system_message, new_message)
    for chat in new_chat_generator: # loops over potential function call sequences
        last_message = chat.messages[-1]
        log_message(last_message)

    while user_input != "exit":
        user_input = input("\033[31mUser: \033[0m")
        new_message = Message(role="user", content=user_input)
        continue_chat_generator = continue_chat(chat, new_message)

        # throwaway = next(continue_chat_generator) # throw away the first message, which is the last assistant response
        for chat in continue_chat_generator:
            last_message = chat.messages[-1]
            log_message(last_message)



    
    # # Iterate through the generator
    # for chat in chat_generator:
    #     if user_input != "exit":
    #         # pp.pprint(chat)
    #         print("Assistant: " + str(chat.messages[-1].content)) # str for debugging since it comes back as None if its a function call
    #         user_input = input("User: ")
    #         new_message = Message(role="user", content=user_input, is_function_call = False)
    #         # Continue the chat with a new generator
    #         chat_generator = continue_chat(chat, new_message)


if __name__ == "__main__":
    main()
