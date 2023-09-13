import streamlit as st
import os
import dotenv
import logging
from agent_smith_ai.utility_agent import UtilityAgent


def initialize_app_config(**kwargs):
    _initialize_session_state()
    defaults = {
        "page_title": "Agent Smith AI",
        "page_icon": None,
        "layout": "centered",
        "initial_sidebar_state": "collapsed",
        "menu_items": {
            "Get Help": "https://github.com/monarch-initiative/agent-smith-ai",
            "Report a Bug": "https://github.com/monarch-initiative/agent-smith-ai/issues",
            "About": "Agent Smith (AI) is a framework for developing tool-using AI-based chatbots.",
        }
    }

    st.set_page_config(
        **{**defaults, **kwargs}
    )

def set_app_default_api_key(key):
    _initialize_session_state()
    st.session_state.default_api_key = key
    _update_agents_api_keys()


def set_app_agents(agents):
    _initialize_session_state()
    st.session_state.agents = agents
    st.session_state.current_agent_name = list(st.session_state.agents.keys())[0]

    for agent in st.session_state.agents.values():
        if "conversation_started" not in agent:
            agent["conversation_started"] = False
        if "messages" not in agent:
            agent["messages"] = []


def serve_app():
    _initialize_session_state()
    _main()


# Update agents to use the current API key
# if the user has provided one, use that
# otherwise, use the default
# if there is no default, use "placeholder" (agent's cant have a None key)
def _update_agents_api_keys():
    key = st.session_state.user_api_key if st.session_state.user_api_key else st.session_state.default_api_key
    if key is None:
        key = "placeholder"

    for agent in st.session_state.agents.values():
        agent["agent"].set_api_key(key)



# Check if we have a valid API key
def _has_valid_api_key():
    return bool(st.session_state.user_api_key) or bool(st.session_state.default_api_key)


# Render chat message
def _render_message(message):
    current_agent_avatar = st.session_state.agents[st.session_state.current_agent_name].get("avatar", None)
    current_user_avatar = st.session_state.agents[st.session_state.current_agent_name].get("user_avatar", None)

    if message.role == "user":
        with st.chat_message("user", avatar = current_user_avatar):
            st.write(message.content)

    elif message.role == "system":
        with st.chat_message("assistant", avatar="ℹ️"):
            st.write(message.content)

    elif message.role == "assistant" and not message.is_function_call:
        with st.chat_message("assistant", avatar=current_agent_avatar):
            st.write(message.content)

    if st.session_state.show_function_calls:
        if message.is_function_call:
            with st.chat_message("assistant", avatar="🛠️"):
                st.text(f"{message.func_name}(params = {message.func_arguments})")

        elif message.role == "function":
            with st.chat_message("assistant", avatar="✔️"):
                st.text(message.content)

    current_action = "*Thinking...*"

    if message.is_function_call:
        current_action = f"*Checking source ({message.func_name})...*"
    elif message.role == "function":
        current_action = f"*Evaluating result ({message.func_name})...*"

    return current_action
    
# Handle chat input and responses
def _handle_chat_input():
    if prompt := st.chat_input(disabled=st.session_state.lock_widgets, on_submit=_lock_ui):  # Step 4: Add on_submit callback
        agent = st.session_state.agents[st.session_state.current_agent_name]

        # Continue with conversation
        if not agent.get('conversation_started', False):
            messages = agent['agent'].new_chat(prompt, yield_prompt_message=True)
            agent['conversation_started'] = True
        else:
            messages = agent['agent'].continue_chat(prompt, yield_prompt_message=True)

        st.session_state.current_action = "*Thinking...*"
        while True:
            try:
                with st.spinner(st.session_state.current_action):
                    message = next(messages)
                    agent['messages'].append(message)
                    st.session_state.current_action = _render_message(message)
       
                    session_id = st.runtime.scriptrunner.add_script_run_ctx().streamlit_script_run_ctx.session_id
                    info = {"session_id": session_id, "message": message.model_dump(), "agent": st.session_state.current_agent_name}
                    st.session_state.logger.info(info)
            except StopIteration:
                break

        st.session_state.lock_widgets = False  # Step 5: Unlock the UI
        st.experimental_rerun()

def _clear_chat_current_agent():
    current_agent = st.session_state.agents[st.session_state.current_agent_name]
    current_agent['conversation_started'] = False
    current_agent['agent'].clear_history()
    st.session_state.agents[st.session_state.current_agent_name]['messages'] = []


# Lock the UI when user submits input
def _lock_ui():
    st.session_state.lock_widgets = True

# Main Streamlit UI
def _main():
    with st.sidebar:
        # st.title("Settings")

        agent_names = list(st.session_state.agents.keys())
        #return
        current_agent_name = st.selectbox(label = "**Assistant**", 
                                          options=agent_names, 
                                          key="current_agent_name", 
                                          disabled=st.session_state.lock_widgets, 
                                          label_visibility="visible")
        st.button(label = "Clear chat for current assistant", 
                  on_click=_clear_chat_current_agent, 
                  disabled=st.session_state.lock_widgets)
        st.checkbox("🛠️ Show calls to external tools", 
                    key="show_function_calls", 
                    disabled=st.session_state.lock_widgets)

        st.markdown("---")

        # Add user input for API key

        user_key = st.text_input("Set API Key", 
                                 value = st.session_state.user_api_key, 
                                 max_chars=51, type="password", 
                                 help = "Enter your OpenAI API key here to override the default provided by the app.", 
                                 disabled=st.session_state.lock_widgets)
        if user_key != st.session_state.user_api_key and len(user_key) == 51:
            st.session_state.user_api_key = user_key
            _update_agents_api_keys()
            # write a label like "sk-...lk6" to let the user know a custom key is set and which one
            st.write(f"Using API key: `{user_key[:3]}...{user_key[-3:]}`")


    st.header(st.session_state.current_agent_name)

    current_agent_avatar = st.session_state.agents[st.session_state.current_agent_name].get("avatar", None)
    with st.chat_message("assistant", avatar = current_agent_avatar):
        st.write(st.session_state.agents[st.session_state.current_agent_name]['greeting'])

    for message in st.session_state.agents[st.session_state.current_agent_name]['messages']:
        _render_message(message)

    # Check for valid API key and adjust chat input box accordingly
    if _has_valid_api_key():
        _handle_chat_input()
    else:
        st.chat_input(placeholder="Enter an API key to begin chatting.", disabled=True)


# Initialize session states
def _initialize_session_state():
    if "logger" not in st.session_state:
        st.session_state.logger = logging.getLogger(__name__)
        st.session_state.logger.handlers = []
        st.session_state.logger.setLevel(logging.INFO)
        st.session_state.logger.addHandler(logging.StreamHandler())

    st.session_state.setdefault("user_api_key", "")
    st.session_state.setdefault("default_api_key", None)  # Store the original API key
    st.session_state.setdefault("show_function_calls", False)
    st.session_state.setdefault("ui_disabled", False)
    st.session_state.setdefault("lock_widgets", False)

    st.session_state.setdefault("agents" , {"Default Agent": 
                                                {"agent": UtilityAgent("Default Agent"),
                                                 "greeting": "Hello, I'm the default agent. I can't do much other than talk. Oh! I can tell you the current time if you like.",
                                                 "avatar": "🤖",
                                                 "user_avatar": "👤"}
                                           })

    st.session_state.setdefault("current_agent_name", "Default Agent")

    for agent in st.session_state.agents.values():
        if "conversation_started" not in agent:
            agent["conversation_started"] = False
        if "messages" not in agent:
            agent["messages"] = []

# # Main script execution
# if __name__ == "__main__":
#     initialize_page()
#     dotenv.load_dotenv()
#     _initialize_session_state()
#     _main()


# # agent_server_streamlit.py

# import streamlit as st
# import os
# import toml
# import pathlib
# import logging

# class AgentServerStreamlit:
#     def __init__(self, agents):
#         self.agents = agents
#         self.page_config = {}
#         self._ensure_streamlit_config()
#         self._initialize_session_state()

#     def set_page_config(self, **kwargs):
#         self.page_config = kwargs

#     def serve(self):
#         self._initialize_page()
#         self._initialize_session_state()
#         self._main()

#     def set_default_api_key(self, key):
#         self._update_agents_api_key(key)

#     def _initialize_page(self):
#         st.set_page_config(**self.page_config)

#     def _initialize_session_state(self):
#         if "logger" not in st.session_state:
#             st.session_state.logger = logging.getLogger(__name__)
#             st.session_state.logger.handlers = []
#             st.session_state.logger.setLevel(logging.INFO)
#             st.session_state.logger.addHandler(logging.StreamHandler())

#         st.session_state.setdefault("user_api_key", "")
#         st.session_state.setdefault("default_api_key", "placeholder")  # Store the original API key
#         st.session_state.setdefault("show_function_calls", False)
#         st.session_state.setdefault("ui_disabled", False)
#         st.session_state.setdefault("lock_widgets", False)

#         if "agents" not in st.session_state:
#             st.session_state.agents = self.agents

#         st.session_state.setdefault("current_agent_name", list(st.session_state.agents.keys())[0])

#         for agent in st.session_state.agents.values():
#             if "conversation_started" not in agent:
#                 agent["conversation_started"] = False
#             if "messages" not in agent:
#                 agent["messages"] = []


#     def _render_message(self, message):
#         current_agent_avatar = st.session_state.agents[st.session_state.current_agent_name].get("avatar", None)
#         current_user_avatar = st.session_state.agents[st.session_state.current_agent_name].get("user_avatar", None)

#         if message.role == "user":
#             with st.chat_message("user", avatar = current_user_avatar):
#                 st.write(message.content)

#         elif message.role == "system":
#             with st.chat_message("assistant", avatar="ℹ️"):
#                 st.write(message.content)

#         elif message.role == "assistant" and not message.is_function_call:
#             with st.chat_message("assistant", avatar=current_agent_avatar):
#                 st.write(message.content)

#         if st.session_state.show_function_calls:
#             if message.is_function_call:
#                 with st.chat_message("assistant", avatar="🛠️"):
#                     st.text(f"{message.func_name}(params = {message.func_arguments})")

#             elif message.role == "function":
#                 with st.chat_message("assistant", avatar="✔️"):
#                     st.text(message.content)

#         current_action = "*Thinking...*"

#         if message.is_function_call:
#             current_action = f"*Checking source ({message.func_name})...*"
#         elif message.role == "function":
#             current_action = f"*Evaluating result ({message.func_name})...*"

#         return current_action



#     def _handle_chat_input(self):
#         if prompt := st.chat_input(disabled=st.session_state.lock_widgets, on_submit=self._lock_ui):  # Step 4: Add on_submit callback
#             agent = st.session_state.agents[st.session_state.current_agent_name]

#             # Continue with conversation
#             if not agent.get('conversation_started', False):
#                 messages = agent['agent'].new_chat(prompt, yield_prompt_message=True)
#                 agent['conversation_started'] = True
#             else:
#                 messages = agent['agent'].continue_chat(prompt, yield_prompt_message=True)

#             st.session_state.current_action = "*Thinking...*"
#             while True:
#                 try:
#                     with st.spinner(st.session_state.current_action):
#                         message = next(messages)
#                         agent['messages'].append(message)
#                         st.session_state.current_action = self._render_message(message)
           
#                         # Log the message
#                         session_id = st.runtime.scriptrunner.add_script_run_ctx().streamlit_script_run_ctx.session_id
#                         info = {"session_id": session_id, "message": message.model_dump(), "agent": st.session_state.current_agent_name}
#                         st.session_state.logger.info(info)
#                 except StopIteration:
#                     break

#             st.session_state.lock_widgets = False  # Step 5: Unlock the UI
#             st.experimental_rerun()


#     def _lock_ui(self):
#         st.session_state.lock_widgets = True


#     def _clear_chat_current_agent(self):
#         current_agent = st.session_state.agents[st.session_state.current_agent_name]
#         current_agent['conversation_started'] = False
#         current_agent['agent'].clear_history()
#         st.session_state.agents[st.session_state.current_agent_name]['messages'] = []


#     # Get the current API key, either the user's or the default
#     def _get_current_api_key_for_agent_use(self):
#         key = st.session_state.user_api_key if st.session_state.user_api_key else st.session_state.default_api_key
#         if key is None:
#             key = "placeholder"
#         return key

#     # Update agents with new API key
#     # if no key is given, it looks for it in the session state / UI
#     def _update_agents_api_key(self, key = None):
#         for agent in st.session_state.agents.values():
#             if key is None:
#                 agent["agent"].set_api_key(self._get_current_api_key_for_agent_use())
#             else:
#                 agent["agent"].set_api_key(key)

#     # Check if we have a valid API key
#     def _has_valid_api_key(self):
#         return bool(st.session_state.user_api_key) or bool(st.session_state.default_api_key)




#     def _ensure_streamlit_config(self):
#         # Ensure .streamlit directory exists
#         config_dir = pathlib.Path('.streamlit')
#         config_dir.mkdir(exist_ok=True)

#         # Path to the config.toml
#         config_path = config_dir / 'config.toml'

#         # Default values
#         default_config = {
#             'theme': {
#                 'base': 'light',
#                 'primaryColor': '#4bbdff'
#             }
#         }

#         # If config.toml doesn't exist, create it with default values
#         if not config_path.exists():
#             with open(config_path, 'w') as config_file:
#                 toml.dump(default_config, config_file)
#         else:
#             # If it exists, ensure it has the theme settings
#             with open(config_path, 'r') as config_file:
#                 config = toml.load(config_file)

#             config['theme'] = default_config['theme']

#             with open(config_path, 'w') as config_file:
#                 toml.dump(config, config_file)



#     def _main(self):
#         with st.sidebar:
#             # st.title("Settings")

#             agent_names = list(st.session_state.agents.keys())
#             current_agent_name = st.selectbox(label = "**Assistant**", 
#                                               options=agent_names, 
#                                               key="current_agent_name", 
#                                               disabled=st.session_state.lock_widgets, 
#                                               label_visibility="visible")
#             st.button(label = "Clear chat for current assistant", 
#                       on_click=self._clear_chat_current_agent, 
#                       disabled=st.session_state.lock_widgets)
#             st.checkbox("🛠️ Show calls to external tools", 
#                         key="show_function_calls", 
#                         disabled=st.session_state.lock_widgets)

#             st.markdown("---")

#             # Add user input for API key

#             user_key = st.text_input("Set API Key", 
#                                      value = st.session_state.user_api_key, 
#                                      max_chars=51, type="password", 
#                                      help = "Enter your OpenAI API key here to override the default provided by the app.", 
#                                      disabled=st.session_state.lock_widgets)
#             if user_key != st.session_state.user_api_key and len(user_key) == 51:
#                 st.session_state.user_api_key = user_key
#                 self._update_agents_api_key()
#                 # write a label like "sk-...lk6" to let the user know a custom key is set and which one
#                 st.write(f"Using API key: `{user_key[:3]}...{user_key[-3:]}`")


#         st.header(st.session_state.current_agent_name)

#         current_agent_avatar = st.session_state.agents[st.session_state.current_agent_name].get("avatar", None)
#         with st.chat_message("assistant", avatar = current_agent_avatar):
#             st.write(st.session_state.agents[st.session_state.current_agent_name]['greeting'])

#         for message in st.session_state.agents[st.session_state.current_agent_name]['messages']:
#             self._render_message(message)

#         # Check for valid API key and adjust chat input box accordingly
#         if self._has_valid_api_key():
#             self._handle_chat_input()
#         else:
#             st.chat_input(placeholder="Enter an API key to begin chatting.", disabled=True)
