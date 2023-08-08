from agent_smith_ai.utility_agent import UtilityAgent
import sys


class BashAIAgent(UtilityAgent):
    def __init__(self, name, system_prompt=None, api_key=None):
        super().__init__(name, system_prompt, model="gpt-3.5-turbo-0613", openai_api_key = api_key)

        # Register callable methods specific to bash interaction
        self.register_callable_methods(['execute_bash_command'])

    def execute_bash_command(self, command: str):
        """Execute a bash command and return the result.
        
        Args:
            command (str): The bash command to execute.
            
        Returns:
            The result of the bash command execution.
        """
        import subprocess

        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
            if result.stderr:
                sys.stderr.write(result.stderr)
                return f"Error: {result.stderr}"
            sys.stdout.write(result.stdout)
            return result.stdout
        except Exception as e:
            sys.stderr.write(str(e))
            return str(e)

