import os
import json
import shutil

CONFIG_DIR = os.path.expanduser("~/.bash_ai")


def get_existing_profiles():
    profiles = [d for d in os.listdir(CONFIG_DIR) if os.path.isdir(os.path.join(CONFIG_DIR, d)) and d != "default"]
    return profiles


def get_profile_dir(profile_name):
    return os.path.join(CONFIG_DIR, profile_name)

def get_profile_config_path(profile_name):
    return os.path.join(get_profile_dir(profile_name), "config.json")

def get_conversation_log_path(profile_name):
    return os.path.join(get_profile_dir(profile_name), "conversation.log")

def create_profile(profile_name, system_prompt, api_key=None):
    profile_dir = get_profile_dir(profile_name)
    # remove directory if it exists
    if os.path.exists(profile_dir):
        shutil.rmtree(profile_dir)

    os.makedirs(profile_dir, exist_ok=True)
    
    config = {
        "system_prompt": system_prompt,
        "openai_api_key": api_key  # Add the api_key to the profile config
    }

    with open(get_profile_config_path(profile_name), 'w') as file:
        json.dump(config, file, indent=4)



def read_profile_config(profile_name):
    config_path = get_profile_config_path(profile_name)
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            return json.load(file)
    return {}

def read_last_n_lines(file_path, n):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        return lines[-n:]



