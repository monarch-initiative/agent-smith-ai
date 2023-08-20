from datetime import datetime
import json
import os
from config.profiles import get_profile_dir

def get_conversation_log_path(profile_name):
    return os.path.join(get_profile_dir(profile_name), "conversation.log")


def log_conversation(profile_name, message):
    log_path = get_conversation_log_path(profile_name)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "pwd": os.getcwd(),
        "message": message.dict()  # Assuming message is an object with a `dict` method
    }
    with open(log_path, 'a') as file:
        file.write(json.dumps(log_entry) + '\n')

