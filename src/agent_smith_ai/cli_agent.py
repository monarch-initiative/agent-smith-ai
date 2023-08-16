from agent_smith_ai.utility_agent import UtilityAgent
from agent_smith_ai.models import *

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from rich.panel import Panel

import os
import re
import json
import sys

class CLIAgent(UtilityAgent):
    """An agent designed for interactive, multi-turn chats on the command line. Inherits from UtilityAgent, and may be inherited from to create custom command-line agents."""

    def __init__(self, name: str = "Assistant", system_message: str = f"You are a helpful assistant.", model: str = "gpt-3.5-turbo-0613", openai_api_key: str = None, dotfile_history: bool = True) -> None:
        """Initializes the agent.
        
        Args:
            name (str, optional): The name of the agent. Defaults to "Assistant".
            system_message (str, optional): The system message provided to the agent. Defaults to f"You are a helpful assistant named {name}."
            model (str, optional): The model to use for the agent. Defaults to "gpt-3.5-turbo-0613".
            openai_api_key (str, optional): The OpenAI API key to use for the agent. Defaults to None, which will use the OPENAI_API_KEY environment variable.
            dotfile_history (bool, optional): Whether to save the agent's history to a dotfile. Defaults to True."""

        super().__init__(name, system_message, model, openai_api_key)
        self.dotfile_history = dotfile_history

        style = Style.from_dict({
            'prompt': '#00aaaa'
        })
        self.prompt_session = PromptSession(style = style)

        if self.dotfile_history:
            # check to see if ~/.utility_agent/ exists, and if not create it
            hist_path = os.path.join(os.path.expanduser("~"), ".utility_agents")
            if not os.path.exists(hist_path):
                os.makedirs(hist_path)

            agent_filename = re.sub(r'[^\w\-]', '', self.name).replace(' ', '_').lower() + ".prompt_history"

            histfile = os.path.join(hist_path, agent_filename)
            self.prompt_session = PromptSession(history=FileHistory(histfile), style=style)

        self.register_callable_methods(["show_function_calls", "hide_function_calls", "exit"])

        os.environ["SHOW_FUNCTION_CALLS"] = 'False'


    def show_function_calls(self) -> None:
        """
        Sets function calls and results to visible.
        """
        os.environ["SHOW_FUNCTION_CALLS"] = 'True'


    def hide_function_calls(self) -> None:
        """
        Sets function calls and results to hidden.
        """
        os.environ["SHOW_FUNCTION_CALLS"] = 'False'


    def log_history(self) -> Dict[str, Any]:
        """
        Return the full chat history, for debugging purposes.

        Returns:
            Dict[str, Any]: The full chat history.
        """
        return self.history.model_dump()
    
    def exit(self) -> None:
        """
        Exits the chat.
        """
        sys.exit(0)


    def render_panel(self, content: str, title: str, style = "default", title_align: str = "left", newline: bool = True) -> None:
        """Renders a panel with the given content and title.
        
        Args:
            content (str): The content to render.
            title (str): The title of the panel.
            style (str, optional): The style of the panel. Defaults to "default".
            title_align (str, optional): The alignment of the title. Defaults to "left".
            newline (bool, optional): Whether to print a newline before the panel. Defaults to True.
        """
        console = Console(width = 100)
        title = Text(title, style = style)
        if self._is_valid_json(content):
            content = "```json\n" + json.dumps(json.loads(content), indent = 4).strip() + "\n```"
        if newline:
            console.print()
        console.print(Panel(Markdown(f"{content}"), title = title, title_align=title_align))


    def start_chat_ui(self) -> None:
        """Starts the chat UI, prompting the user for an initial message."""
        user_input = self.prompt_session.prompt([('class:prompt', 'User: ')])

        for message in self.new_chat(user_input):
            self._log_message(message)

        while user_input != "exit":
            user_input = self.prompt_session.prompt([('class:prompt', 'User: ')])

            for message in self.continue_chat(user_input):
                self._log_message(message)


    def _is_valid_json(self, myjson: str) -> bool:
        """Checks if a string is valid JSON."""
        try:
            json.loads(myjson)
        except json.JSONDecodeError:
            return False
        return True


    def _log_message(self, message: Message) -> None:
        """Logs a message to the console using render_panel."""

        if message.role == "user":
            self.render_panel(message.content, message.author + " -> " + message.intended_recipient, style = "cyan")

        elif message.role == "system":
            self.render_panel(message.content, message.author + " -> " + message.intended_recipient, style = "red")

        elif message.role == "assistant":
            if(message.content):
                self.render_panel(message.content, message.author + " -> " + message.intended_recipient, style = "blue")
            if(message.is_function_call and os.environ["SHOW_FUNCTION_CALLS"] == 'True'):
                self.render_panel(f"```\n{message.func_name}(params = {message.func_arguments})\n```", message.author + " -> " + message.intended_recipient, style = "default")
                
        elif message.role == "function" and os.environ["SHOW_FUNCTION_CALLS"] == 'True':
            self.render_panel(message.content, message.author + " -> " + message.intended_recipient, style = "default", newline = False)
