from agent_smith_ai.utility_agent import UtilityAgent
import dotenv

dotenv.load_dotenv()

class BashAIAgent(UtilityAgent):
    def __init__(self, name, system_message=None):
        super().__init__(name, system_message, model="gpt-3.5-turbo-0613")

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
                return f"Error: {result.stderr}"
            return result.stdout
        except Exception as e:
            return str(e)



import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='BashAI: An AI assistant for bash commands.')
    parser.add_argument('question', type=str, help='A free-text question for the AI agent.')
    parser.add_argument('--name', type=str, default='Bash Assistant', help='Name of the agent.')
    parser.add_argument('--system_message', type=str, default='You are an AI agent that has the ability to execute bash commands using the execute_bash_command function. ALWAYS use this function to execute commands.')
    # parser.add_argument('--system_message', type=str, default='You are an AI agent that has the ability to execute bash commands.')
    return parser.parse_args()


def main():
    args = parse_arguments()

    # Initialize the agent
    agent = BashAIAgent(args.name, args.system_message)

    # Interact with the agent
    print(args)
    for message in agent.new_chat(args.question, yield_prompt_message=True, author="User"):
        print("\n\n", message.dict())

        # Handle bash command execution
        if message.is_function_call and message.func_name == 'execute_bash_command':
            command = message.func_arguments['command']
            print(f"Proposed command: {command}")
            confirmation = input("Do you want to execute this command? (y/n): ")
            if confirmation.lower() == 'y':
                result = agent.execute_bash_command(command)
                print(f"Command result:\n{result}")

if __name__ == "__main__":
    main()
