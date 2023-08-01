from monarch_assistant.utility_agent import UtilityAgent
from monarch_assistant.models import *

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
    def __init__(self, name: str = "Assistant", system_message: str = f"You are a helpful assistant.", model: str = "gpt-3.5-turbo-0613", openai_api_key = None, dotfile_history = True):
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

        self.register_callable_methods(["show_function_calls", "hide_function_calls", "log_history", "exit"])

        os.environ["SHOW_FUNCTION_CALLS"] = 'False'


    def show_function_calls(self):
        """
        Sets function calls to hidden.
        """
        os.environ["SHOW_FUNCTION_CALLS"] = 'True'


    def hide_function_calls(self):
        """
        Sets function calls to visible.
        """
        os.environ["SHOW_FUNCTION_CALLS"] = 'False'


    def log_history(self):
        """
        Logs the message history.
        """
        return self.history.dict()
    
    def exit(self):
        """
        Exits the chat.
        """
        sys.exit(0)

    def render_panel(self, content: str, title: str, style = "default", title_align: str = "left", newline = True):
        """Renders a panel with the given content and title."""
        console = Console(width = 100)
        title = Text(title, style = style)
        if self._is_valid_json(content):
            content = "```json\n" + json.dumps(json.loads(content), indent = 4).strip() + "\n```"
        if newline:
            console.print()
        console.print(Panel(Markdown(f"{content}"), title = title, title_align=title_align))


    def start_chat_ui(self):
        user_input = self.prompt_session.prompt([('class:prompt', 'User: ')])

        for message in self.new_chat(user_input):
            self._log_message(message)

        while user_input != "exit":
            user_input = self.prompt_session.prompt([('class:prompt', 'User: ')])

            for message in self.continue_chat(user_input):
                self._log_message(message)


    def _is_valid_json(self, myjson: str) -> bool:
        try:
            json.loads(myjson)
        except json.JSONDecodeError:
            return False
        return True


    def _log_message(self, message: Message):

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
