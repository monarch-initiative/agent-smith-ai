from .profiles import create_profile, get_existing_profiles, get_profile_config_path, read_profile_config
import os
import json
import shutil

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
            print("Existing default profile removed. New default profile created.")

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

