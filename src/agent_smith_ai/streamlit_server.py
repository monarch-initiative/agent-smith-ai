import streamlit as st
import toml
import logging
import pathlib
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
    st.session_state.default_api_key = key
    _update_agents_api_keys()


def set_app_agents(agents_func):
    if "agents" not in st.session_state:
        agents = agents_func()
        st.session_state.agents = agents
        st.session_state.current_agent_name = list(st.session_state.agents.keys())[0]

        for agent in st.session_state.agents.values():
            if "conversation_started" not in agent:
                agent["conversation_started"] = False
            if "messages" not in agent:
                agent["messages"] = []


def serve_app():
    assert "agents" in st.session_state, "No agents have been set. Use set_app_agents() to set agents prior to serve_app()"
    _main()



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
