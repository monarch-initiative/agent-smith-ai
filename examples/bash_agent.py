from agent_smith_ai.utility_agent import UtilityAgent
import dotenv
import sys

dotenv.load_dotenv()

class BashAIAgent(UtilityAgent):
    def __init__(self, name, system_prompt=None):
        super().__init__(name, system_prompt, model="gpt-3.5-turbo-0613")

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



import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='BashAI: An AI assistant for bash commands.')
    parser.add_argument('--init', action='store_true', help='Initialize BashAI configuration.')
    parser.add_argument('--profile', '-p', type=str, default="default", help='Name of the agent profile (optional, default is "default").')
    parser.add_argument('--system-prompt', type=str, default="You are a helpful AI assistant that can execute commands in a bash shell.", help='System prompt for the agent.')
    parser.add_argument('question', type=str, nargs='?', default="Please describe your functionality", help='A free-text question for the AI agent.')
    return parser.parse_args()



import os
import json

CONFIG_DIR = os.path.expanduser("~/.bash_ai")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def create_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)

def read_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return {}

def write_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)


import shutil

def initialize(default_prompt="You are a helpful AI assistant that can execute commands in a bash shell."):
    print("Initializing BashAI...")
    create_config_dir()

    existing_config = read_config()
    api_key = existing_config.get("openai_api_key", None)

    # Check if API key exists and prompt the user
    if api_key:
        decision = input("An existing API key was found. Do you want to keep it? (y/n): ").lower()
        if decision != 'y':
            api_key = input("Enter your new OpenAI API key: ")
            existing_config["openai_api_key"] = api_key
            write_config(existing_config)

    else:
        api_key = input("Enter your OpenAI API key: ")
        write_config({"openai_api_key": api_key})

    # Check if default profile exists; if not or if user decides to override, create it
    if os.path.exists(get_profile_config_path("default")):
        decision = input("Existing default profile found. Do you want it keep it (system prompt and chat history)? (y/n): ").lower()
        if decision == 'y':
            print("Existing profiles retained.")
        else:
            create_profile("default", default_prompt)

    else:
        create_profile("default", default_prompt)

    existing_profiles = get_existing_profiles()
    if existing_profiles:
        decision = input(f"Existing profiles found: {', '.join(existing_profiles)}. Do you want to keep them? (y/n): ").lower()
        if decision != 'y':
            for profile in existing_profiles:
                profile_path = os.path.join(CONFIG_DIR, profile)
                # Remove the profile directory
                shutil.rmtree(profile_path)
                print(f"Removed profile '{profile}'.")


    print("Initialization complete. You can now use BashAI.")



def get_existing_profiles():
    profiles = [d for d in os.listdir(CONFIG_DIR) if os.path.isdir(os.path.join(CONFIG_DIR, d)) and d != "default"]
    return profiles


def get_profile_dir(profile_name):
    return os.path.join(CONFIG_DIR, profile_name)

def get_profile_config_path(profile_name):
    return os.path.join(get_profile_dir(profile_name), "config.json")

def get_conversation_log_path(profile_name):
    return os.path.join(get_profile_dir(profile_name), "conversation.log")

def create_profile(profile_name, system_prompt):
    profile_dir = get_profile_dir(profile_name)
    os.makedirs(profile_dir, exist_ok=True)
    
    config = {
        "system_prompt": system_prompt
    }

    with open(get_profile_config_path(profile_name), 'w') as file:
        json.dump(config, file, indent=4)


def read_profile_config(profile_name):
    config_path = get_profile_config_path(profile_name)
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            return json.load(file)
    return {}


from datetime import datetime

def log_conversation(profile_name, message):
    log_path = get_conversation_log_path(profile_name)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "message": message.dict()  # Assuming message is an object with a `dict` method
    }
    with open(log_path, 'a') as file:
        file.write(json.dumps(log_entry) + '\n')








def main():
    args = parse_arguments()
    
    if args.init:
        initialize(args.system_prompt)
        return


    profile_name = args.profile
    profile_config_path = get_profile_config_path(profile_name)

    if not os.path.exists(profile_config_path):
        if args.system_prompt is None:
            print(f"Error: Profile '{profile_name}' does not exist. Please provide --system-prompt to create it.")
            return
        create_profile(profile_name, args.system_prompt)
        print(f"Profile '{profile_name}' created successfully.")

    profile_config = read_profile_config(profile_name)
    system_prompt = profile_config.get("system_prompt", "")

    # Initialize the agent
    agent = BashAIAgent(profile_name, system_prompt)

    # Interact with the agent
    for message in agent.new_chat(args.question, yield_prompt_message=True, author="User"):
        log_conversation(args.profile, message)  # Log the conversation

        # Handle bash command execution
        if message.is_function_call and message.func_name == 'execute_bash_command':
            command = message.func_arguments['command']
            # print(f"Proposal: {command}")
            sys.stderr.write(f"{command} # Execute? y/n [n]: ")
            confirmation = input()
            if confirmation.lower() != 'y':
                sys.exit(0)
        # elif message.role == "function":
        #     continue
        # else:
        #     # Handle other messages
        #     print(f"Message: {message.content}")

if __name__ == "__main__":
    main()