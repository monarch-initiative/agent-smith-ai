from monarch_agent import MonarchAgent
import agent_smith_ai.streamlit_server as sv
import dotenv
import os

### You may wish to create a .streamlit/config.toml file in the same directory as this script
### with contents to adjust the theme:
# [theme]
# base = "light"
# primaryColor = "#4bbdff"



# initialize the application and set some page settings
# parameters here are passed to streamlit.set_page_config, see more at https://docs.streamlit.io/library/api-reference/utilities/st.set_page_config
# this function must be run first
sv.initialize_app_config(
    page_title = "Monarch Assistant",
    page_icon = "https://avatars.githubusercontent.com/u/5161984?s=200&v=4",
    menu_items = {
            "Get Help": "https://github.com/monarch-initiative/agent-smith-ai/issues",
            "Report a Bug": "https://github.com/monarch-initiative/agent-smith-ai/issues",
            "About": "Agent Smith (AI) is a framework for developing tool-using AI-based chatbots.",
        }
)

# define a function that returns a dictionary of agents to serve
def get_agents():
    # add some useful agents
    return {
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
    }

# tell the app to use that function to create agents when needed
sv.set_app_agents(get_agents)

# set a default API key from an env var; if not set the user will have to input one to chat
#   - users can input their own in the UI to override the default as well
dotenv.load_dotenv()          # load env variables defined in .env file (if any)
sv.set_app_default_api_key(os.environ["OPENAI_API_KEY"])

# start the app
sv.serve_app()
