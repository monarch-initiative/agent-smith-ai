from agent.bashai_agent import BashAIAgent
from config.init import initialize, read_config
from config.profiles import create_profile, read_profile_config, get_profile_config_path
from utils.conversation_log import log_conversation
import argparse
import sys
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description='BashAI: An AI assistant for bash commands.')
    parser.add_argument('--init', action='store_true', help='Initialize BashAI configuration.')
    parser.add_argument('--profile', '-p', type=str, default="default", help='Name of the agent profile (optional, default is "default").')
    parser.add_argument('--system-prompt', type=str, default="You are a helpful AI assistant that can execute commands in a bash shell.", help='System prompt for the agent.')
    parser.add_argument('--api-key', type=str, help='API key for the agent.')
    parser.add_argument('question', type=str, nargs='?', default="Please describe your functionality", help='A free-text question for the AI agent.')
    return parser.parse_args()




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
        create_profile(profile_name, args.system_prompt, args.api_key)
        print(f"Profile '{profile_name}' created successfully.")

    profile_config = read_profile_config(profile_name)
    system_prompt = profile_config.get("system_prompt", "")

    api_key = read_config().get("openai_api_key")
    if "openai_api_key" in profile_config and profile_config["openai_api_key"] is not None:
        api_key = profile_config["openai_api_key"]

    # Initialize the agent
    agent = BashAIAgent(profile_name, system_prompt, api_key=api_key)

    # Interact with the agent
    for message in agent.new_chat(args.question, author="User"):
        # Handle bash command execution
        if message.is_function_call and message.func_name == 'execute_bash_command':
            command = message.func_arguments['command']
            # print(f"Proposal: {command}")
            sys.stderr.write(f"{command} # Execute? y/n [n]: ")
            confirmation = input()

            if confirmation.lower() != 'y':
                sys.exit(0)
        elif message.role == "function":
            # we don't print the result here, the agent prints to stdout/stderr
            continue
        elif message.author == "User":
            # no need to repeat the user back to themselves
            continue
        else:
            # in fact let's just not not print anything else
            continue
            #sys.stderr.write(f"{message.content}\n")


if __name__ == "__main__":
    main()
