from monarch_agent import MonarchAgent
from agent_smith_ai.streamlit_server import set_app_agents, initialize_app_config, set_app_default_api_key, serve_app
from dotenv import load_dotenv
import os

load_dotenv()

initialize_app_config(
    page_title="Monarch Assistant",
    page_icon="https://avatars.githubusercontent.com/u/5161984?s=200&v=4",
)

# add some useful agents
set_app_agents({
    "Monarch Assistant": {
        "agent": MonarchAgent("Monarch Assistant", model="gpt-3.5-turbo-16k-0613"),
        "greeting": "Hello, I'm the Monarch Assistant.",
        "avatar": "https://avatars.githubusercontent.com/u/5161984?s=200&v=4",
        "user_avatar": "👤",
    },
    "Monarch Assistant (GPT-4)": {
        "agent": MonarchAgent("Monarch Assistant (GPT-4)", model="gpt-4-0613"),
        "greeting": "Hello, I'm the Monarch Assistant, based on GPT-4.",
        "avatar": "https://avatars.githubusercontent.com/u/5161984?s=200&v=4",
        "user_avatar": "👤",
    }
})

set_app_default_api_key(os.environ["OPENAI_API_KEY"])

serve_app()
