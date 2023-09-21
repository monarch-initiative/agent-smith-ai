# Agent Smith (AI)

Agent smith makes it easy to instantiate AI agents that can safely and easily call APIs and locally defined functions to interact with the world. It is currently designed to use OpenAI's [function-calling models](https://platform.openai.com/docs/guides/gpt/function-calling) and thus requires an OpenAI API key.

Current features:

* Auto-summarization of conversations approaching the model's context window size.
* User messages are checked with OpenAI's moderations endpoint by default and rejected if toxic.
* Messages, including function call and result messages, are yielded to the caller in a stream.
* An optional token-bucket allows built-in rate-limiting.
* A basic, easy-to-deploy streamlit-based UI.


<!-- <img src="https://imgix.bustle.com/uploads/image/2021/12/7/cc0e73f8-0020-4c7f-9564-da20f309622d-agent-smith.jpg?w=350" alt="Agent Smith Matrix" style="align: center;" />  -->


## Basic Usage

Primary functionality is provided by a `agent_smith_ai.utility_agent.UtilityAgent` class, which yields `Message` objects in response to user questions. They also manage internal state chat, including the system prompt, chat history, token usage, and auto-summarization when the conversation length nears the context length. Finally, using OpenAI's [function-calling models](https://platform.openai.com/docs/guides/gpt/function-calling), they can register endpoints of REST API's, and locally defined methods and functions as callable functions.

Here's some code from the basic example in `examples/monarch_basic.py`, which makes calls to a [Monarch Initiative](https://monarchinitiative.org) API. We start by using `dotenv` to read a `.env` file defining our `OPENAI_API_KEY` environment variable 
if present (we just need some way to access the key). We inherit from the `UtilityAgent` class, defining a name and system
message for the agent. 

```python
from agent_smith_ai.utility_agent import UtilityAgent

import textwrap
import os
from typing import Any, Dict

# load environment variables from .env file
import dotenv
dotenv.load_dotenv()

## A UtilityAgent can call API endpoints and local methods
class MonarchAgent(UtilityAgent):

    def __init__(self, name):
        
        ## define a system message
        system_message = textwrap.dedent(f"""
            You are the Monarch Assistant, an AI-powered chatbot that can answer questions about data from the Monarch Initiative knowledge graph. 
            You can search for entities such as genes, diseases, and phenotypes by name to get the associated ontology identifier. 
            You can retrieve associations between entities via their identifiers. 
            Users may use synonyms such as 'illness' or 'symptom'. Do not assume the user is familiar with biomedical terminology. 
            Always add additional information such as lay descriptions of phenotypes. 
            If the user changes the show function call setting, do not make any further function calls immediately.
            IMPORTANT: Include markdown-formatted links to the Monarch Initiative for all results using the templates provided by function call responses.'.
            """).strip()
```

Next in the constructor, we call the parent constructor which defines various agent properties. 

```python
        super().__init__(name,                                             # Name of the agent
                         system_message,                                   # Openai system message
                         model = "gpt-3.5-turbo-0613",                     # Openai model name
                         openai_api_key = os.environ["OPENAI_API_KEY"],    # API key; will default to OPENAI_API_KEY env variable
                         auto_summarize_buffer_tokens = 500,               # Summarize and clear the history when fewer than this many tokens remains in the context window. Checked prior to each message sent to the model.
                         summarize_quietly = False,                        # If True, do not alert the user when a summarization occurs
                         max_tokens = None,                                # maximum number of tokens this agent can bank (default: None, no limit)
                         token_refill_rate = 10000.0 / 3600.0)             # number of tokens to add to the bank per second
```

Still in the constructor, we can register some API endpoints for the agent to call. It is possible to register multiple
APIs.

```python
        ## register some API endpoints (inherited from UtilityAgent)
        ## the openapi.json spec must be available at the spec_url:
        ##    callable endpoints must have a "description" and "operationId"
        ##    params can be in body or query, but must be fully specified
        self.register_api("monarch",  # brief alphanumeric ID, used internally
                          spec_url = "https://oai-monarch-plugin.monarchinitiative.org/openapi.json", 
                          base_url = "https://oai-monarch-plugin.monarchinitiative.org",
                          callable_endpoints = ['search_entity', 
                                                'get_disease_gene_associations', 
                                                'get_disease_phenotype_associations', 
                                                'get_gene_disease_associations', 
                                                'get_gene_phenotype_associations', 
                                                'get_phenotype_gene_associations', 
                                                'get_phenotype_disease_associations'])
```

Finally, the constructor is also where we register methods that the agent can call. Agent-callable methods are defined 
like normal, but to be properly callable they should be type-annotated and documented with docstrings
parsable by [docstring-parser](https://pypi.org/project/docstring-parser/). 

```python
        ## the agent can also call local methods, but we have to register them
        self.register_callable_functions({'compute_entropy': self.compute_entropy})

    ## Callable methods should be type-annotated and well-documented with docstrings parsable by the docstring_parser library
    def compute_entropy(self, items: Dict[Any, int]) -> float:
        """Compute the information entropy of a given set of item counts.
        
        Args:
            items (str): A dictionary of items and their counts.
            
        Returns:
            The information entropy of the item counts.
        """
        from math import log2
        
        total = sum(items.values())
        return -sum([count / total * log2(count / total) for count in items.values()])
```

The above will allow the model to accurately answer questions like `"What is the entropy of the tile counts in a standard Scrabble set?"`! 

To use the agent, we first instantiate it and define a question to ask. The agent's `.new_chat()` method takes the
question and yields a stream of `Message` objects. It may yield multiple message objects if the agent decides
to call a function to answer the question. The first yielded Message will have `is_function_call` set to `True` and
information about the function call in other fields. The second message will be the result of the function call
in `content` and `role` set to `"function"`; this is sent back to the model, resulting in a third message yielded with the
models' response in `content` and `role` set to `"assistant`. It may be that the model's immediate response is *another* function
call, in which case function calls and results will continue to be yielded. It is also possible to yield the system message to the
stream with `yield_system_message` and the question itself with `yield_prompt_message` prior to the main message stream.

Messages are `pydantic` models, so `message.model_dump()` converts each message to a dictionary.

```python

agent = MonarchAgent("Monarch Assistant")
question = "What genes are associated with Cystic Fibrosis?"

## agent.chat(question) may result in a series of Message objects (which may consist of a series of function-call messages,
## function-call responses, and other messages)
## by default, the system message and initial prompt question are not included in the output, but can be
for message in agent.chat(question, yield_system_message = True, yield_prompt_message = True, author = "User"):
    ## each Message object as the following attributes and defaults:
        # role: str                                         // required, either "user", "assistant", or "function" (as used by OpenAI API)
        # author: str = None                                // the name of the author of the message
        # intended_recipient: str = None                    // the name of the intended recipient of the message
        # is_function_call: bool = False                    // whether the message represents the model attemtpting to make a function call
        # content: Optional[str] = None                     // the content of the message (as used by OpenAI API)
        # func_name: Optional[str] = None                   // the function name the model is trying to call (if is_function_call is True)
        # func_arguments: Optional[Dict[str, Any]] = None   // the function arguments the model is trying to pass (if is_function_call is True)
        # finish_reason: Optional[str] = None               // (as used by the OpenAI API, largely ignorable)

    ## the author and intended_recipient may be useful for multi-agent conversions or logging, they will typically be filled 
    ## with agent names, "User", or the agent name and the function it is trying to call
    print("\n\n", message.model_dump())
```

Once a chat has been initialized this way, it can be continued with further calls to `.chat()`:

```python
question_followup = "What other diseases are associated with the first one you listed?"
for message in agent.chat(question_followup, yield_prompt_message = True, author = "User"):
    print("\n\n", message.model_dump())

question_followup = "What is the entropy of a standard tile set in Scrabble?"
for message in agent.continue_chat(question_followup, yield_prompt_message = True, author = "User"):
    print("\n\n", message.model_dump())
```

Other functionality provided by agents includes `.set_api_key()` for changing an agent's API-key mid-conversation, `.clear_history()` for 
clearing an agent's conversation history (but not it's token usage), and `.compute_token_cost()` to estimate the total token cost of a potential
message, including the conversation history and function definitions. The basic `UtilityAgent` comes with two callable functions by default, `time()`
and `help()`, which report the current date and time to the model, and a summary of callable functions and API endpoints, respectively.


## Streamlit-based UI

This package includes a basic, opinionated web-UI for serving agents based on streamlit, `examples/streamlit_app.py` provides an example. We assume
an agent class such as `MonarchAgent` in `examples/monarch_agent.py` has been defined; this example is defined to accept the model name (e.g.
`gpt-3.5-turbo-0613`) during the agent creation.

```python
from monarch_agent import MonarchAgent
import agent_smith_ai.streamlit_server as sv
import os
import dotenv
dotenv.load_dotenv()          # load env variables defined in .env file (if any)
```

Next we initialize the application, specifying the page title and icon and other application features. Arguments are passed
to streamlit's [`set_page_config()`](https://docs.streamlit.io/library/api-reference/utilities/st.set_page_config), and calling this once before other functions below is required.

```python
sv.initialize_app_config(
    page_title = "Monarch Assistant",
    page_icon = "https://avatars.githubusercontent.com/u/5161984?s=200&v=4",
    initial_sidebar_state = "collapsed", # or "expanded"
    menu_items = {
            "Get Help": "https://github.com/monarch-initiative/agent-smith-ai/issues",
            "Report a Bug": "https://github.com/monarch-initiative/agent-smith-ai/issues",
            "About": "Agent Smith (AI) is a framework for developing tool-using AI-based chatbots.",
        }
)
```

Next we define some agents. In order to make this performance with streamlit, we define a function that will return a dictionary
of agents when called, and then pass this function to `sv.set_app_agents()` function. The agent dictionary keys are used to define
agent names, with values containing the agent object itself in `"agent"`, a `"greeting"` that is shown to the user by the agent when first
loaded (but that is not part of the agent's conversation history), and avatars for both the user and the agent, which can be characters (including
unicode/emoji) or URLs to images.

```python
def get_agents():
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
```

We can set a default OpenAI API key to use. If one is not provided this way, the user will need to enter one in the sidebar to chat.
If one is set this way, the user can still enter their own key if they like, which will override the default key.

```python
sv.set_app_default_api_key(os.environ["OPENAI_API_KEY"])
```

Lasly we start the app.

```python
sv.serve_app()
```

To run the app, install `streamlit` and run `streamlit run examples/streamlit_app.py`. Messages are logged as they are generated and associated with session IDs for conversation tracking.

### Notes on streamlit

[Streamlit](https://streamlit.io/) is a framework designed to make it easy to develop and deploy python-based web applications. Its execution model
involves re-running the entire python script every time the UI changes or an action is taken, using deliberate state tracking and making heavy use of caching for efficiency. Beware of this if attempting to do extra work as part of the main application.

It is also easy to publish your streamit app to their [community cloud](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app). 
Note that at this time the application does not handle user authentication or rate-limiting of any kind.

You may want to add a `.streamlit/config.toml` in the same directory as your app to adjust the default theme settings:

```
[theme]
base = "light"
primaryColor = "#4bbdff"
```

## Additional Experiments and Examples

These are not complete and may be moved, but the following are currently included here:

**agent_smith_ai.CLIAgent**: A basic command-line agent with some formatting and markdown rendering provided by `rich`. May be inhereted in the same way as `UtilityAgent` for added functionality.

**agent_smith_ai/bash_agent/main.py**: Early version of a command-line-based AI assistant that can write and execute (after confirmation) complex commands.


Here's an example conversation from the `examples/monarch_cli.py` which uses the `CLIAgent` 
(sadly, markdown-defined colors and links are not shown here):


```
╭──────────────────────────────────────────── Welcome ─────────────────────────────────────────────╮
│ Hello! I'm the Monarch Assistant, an AI-powered chatbot that can answer questions about genes,   │
│ diseases, and phenotypes, based on information hosted at https://monarchinitiative.org.          │
│                                                                                                  │
│  • You can exit by saying 'exit', and you can request that I turn on or off function call        │
│    responses by saying 'show function calls' or 'hide function calls' at any time. They are      │
│    shown by default.                                                                             │
│  • I do not currently implement context-window management, so after a while your conversation    │
│    will produce an error.                                                                        │
│  • For a bit of fun, try asking me to describe my plan. For example, "What are the symptoms of   │
│    Cystic Fibrosis? Describe your plan before you execute it."                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: What are the symptoms of Cystic Fibrosis? Describe your plan before you execute it.

╭─ Monarch Assistant -> Monarch Assistant (monarch-search_entity function) ────────────────────────╮
│ To find the symptoms of Cystic Fibrosis, I will first search for the disease using the term      │
│ "Cystic Fibrosis" in the Monarch Initiative knowledge graph. Once I have the ontology identifier │
│ for Cystic Fibrosis, I will use it to retrieve the associated phenotypes. These phenotypes       │
│ represent the symptoms of the disease. I will then provide a description of the symptoms of      │
│ Cystic Fibrosis based on the retrieved information.                                              │
│                                                                                                  │
│ Here is my plan:                                                                                 │
│                                                                                                  │
│  1 Search for the disease "Cystic Fibrosis" in the Monarch Initiative knowledge graph.           │
│  2 Retrieve the ontology identifier for Cystic Fibrosis.                                         │
│  3 Use the ontology identifier to retrieve the associated phenotypes.                            │
│  4 Provide a description of the symptoms of Cystic Fibrosis based on the retrieved information.  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> Monarch Assistant (monarch-search_entity function) ────────────────────────╮
│                                                                                                  │
│  monarch-search_entity(params = {'term': 'Cystic Fibrosis', 'category': 'biolink:Disease',       │
│  'limit': 1})                                                                                    │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Monarch Assistant (monarch-search_entity function) -> Monarch Assistant ────────────────────────╮
│                                                                                                  │
│  {                                                                                               │
│      "results": [                                                                                │
│          {                                                                                       │
│              "id": "MONDO:0009061",                                                              │
│              "name": "cystic fibrosis",                                                          │
│              "categories": [                                                                     │
│                  "biolink:Disease"                                                               │
│              ],                                                                                  │
│              "description": "Cystic fibrosis (CF) is a genetic disorder characterized by the     │
│  production of sweat with a high salt content and mucus secretions with an abnormal viscosity."  │
│          }                                                                                       │
│      ],                                                                                          │
│      "total": 3                                                                                  │
│  }                                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> Monarch Assistant (monarch-get_disease_phenotype_associations function) ───╮
│                                                                                                  │
│  monarch-get_disease_phenotype_associations(params = {'disease_id': 'MONDO:0009061', 'limit':    │
│  10})                                                                                            │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Monarch Assistant (monarch-get_disease_phenotype_associations function) -> Monarch Assistant ───╮
│                                                                                                  │
│  {                                                                                               │
│      "associations": [                                                                           │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0004401",                                                   │
│                  "label": "Meconium ileus (HPO)"                                                 │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0006528",                                                   │
│                  "label": "Chronic lung disease (HPO)"                                           │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0006538",                                                   │
│                  "label": "Recurrent bronchopulmonary infections (HPO)"                          │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0100582",                                                   │
│                  "label": "Nasal polyposis (HPO)"                                                │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0002035",                                                   │
│                  "label": "Rectal prolapse (HPO)"                                                │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0002099",                                                   │
│                  "label": "Asthma (HPO)"                                                         │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0002150",                                                   │
│                  "label": "Hypercalciuria (HPO)"                                                 │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0002595",                                                   │
│                  "label": "Ileus (HPO)"                                                          │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0002613",                                                   │
│                  "label": "Biliary cirrhosis (HPO)"                                              │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0003251",                                                   │
│                  "label": "Male infertility (HPO)"                                               │
│              }                                                                                   │
│          }                                                                                       │
│      ],                                                                                          │
│      "total": 62,                                                                                │
│      "phenotype_url_template": "https://monarchinitiative.org/phenotype/{phenotype_id}"          │
│  }                                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> User ──────────────────────────────────────────────────────────────────────╮
│ The symptoms of Cystic Fibrosis include:                                                         │
│                                                                                                  │
│   1 Meconium ileus: This is a condition where the meconium, the first stool of a newborn, is     │
│     thick and sticky, causing a blockage in the intestines. More information                     │
│   2 Chronic lung disease: Cystic Fibrosis can lead to the development of chronic lung disease,   │
│     characterized by persistent respiratory symptoms such as coughing, wheezing, and shortness   │
│     of breath. More information                                                                  │
│   3 Recurrent bronchopulmonary infections: Individuals with Cystic Fibrosis are prone to         │
│     frequent and recurrent infections in the bronchial tubes and lungs. More information         │
│   4 Nasal polyposis: Cystic Fibrosis can cause the development of polyps in the nasal passages,  │
│     leading to nasal congestion and difficulty breathing through the nose. More information      │
│   5 Rectal prolapse: In some cases, Cystic Fibrosis can result in the protrusion of the rectum   │
│     through the anus. More information                                                           │
│   6 Asthma: Individuals with Cystic Fibrosis may also experience symptoms of asthma, such as     │
│     wheezing and difficulty breathing. More information                                          │
│   7 Hypercalciuria: Cystic Fibrosis can lead to increased levels of calcium in the urine, which  │
│     may result in the formation of kidney stones. More information                               │
│   8 Ileus: This refers to a blockage or obstruction in the intestines, which can occur in        │
│     individuals with Cystic Fibrosis. More information                                           │
│   9 Biliary cirrhosis: In rare cases, Cystic Fibrosis can lead to the development of liver       │
│     disease, specifically biliary cirrhosis. More information                                    │
│  10 Male infertility: Men with Cystic Fibrosis may experience infertility due to the absence or  │
│     blockage of the vas deferens, the tube that carries sperm from the testes. More information  │
│                                                                                                  │
│ Please note that this is not an exhaustive list of symptoms, and the severity and presentation   │
│ of symptoms can vary among individuals with Cystic Fibrosis. It is important to consult with a   │
│ healthcare professional for a comprehensive evaluation and diagnosis.                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: That's nice. I know you can call local functions too - can you do that and tell me what time it is?

╭─ Monarch Assistant -> Monarch Assistant (time function) ─────────────────────────────────────────╮
│                                                                                                  │
│  time(params = {})                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Monarch Assistant (time function) -> Monarch Assistant ─────────────────────────────────────────╮
│                                                                                                  │
│  "08/02/23 10:28"                                                                                │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> User ──────────────────────────────────────────────────────────────────────╮
│ The current time is 10:28 AM on August 2, 2023.                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: Fun! Can you hide the function calls, and then tell me the entropy of a standard scrabble set?

╭─ Monarch Assistant -> Monarch Assistant (hide_function_calls function) ──────────────────────────╮
│                                                                                                  │
│  hide_function_calls(params = {})                                                                │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> User ──────────────────────────────────────────────────────────────────────╮
│ The entropy of a standard Scrabble set is approximately 4.37.                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: Nice :) What time is it now?

╭─ Monarch Assistant -> User ──────────────────────────────────────────────────────────────────────╮
│ The current time is 10:29 AM on August 2, 2023.                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: Ok, show the function calls again, and tell me more about the CFTR gene.
╭─ Monarch Assistant (show_function_calls function) -> Monarch Assistant ──────────────────────────╮
│                                                                                                  │
│  null                                                                                            │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> Monarch Assistant (monarch-search_entity function) ────────────────────────╮
│                                                                                                  │
│  monarch-search_entity(params = {'term': 'CFTR', 'category': 'biolink:Gene', 'limit': 1})        │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Monarch Assistant (monarch-search_entity function) -> Monarch Assistant ────────────────────────╮
│                                                                                                  │
│  {                                                                                               │
│      "results": [                                                                                │
│          {                                                                                       │
│              "id": "HGNC:1884",                                                                  │
│              "name": "CFTR",                                                                     │
│              "categories": [                                                                     │
│                  "biolink:Gene"                                                                  │
│              ],                                                                                  │
│              "description": null                                                                 │
│          }                                                                                       │
│      ],                                                                                          │
│      "total": 41                                                                                 │
│  }                                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> Monarch Assistant (monarch-get_gene_disease_associations function) ────────╮
│                                                                                                  │
│  monarch-get_gene_disease_associations(params = {'gene_id': 'HGNC:1884', 'limit': 10})           │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Monarch Assistant (monarch-get_gene_disease_associations function) -> Monarch Assistant ────────╮
│                                                                                                  │
│  {                                                                                               │
│      "associations": [                                                                           │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "causal"                                                        │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0009061",                                                  │
│                  "label": "cystic fibrosis"                                                      │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "causal"                                                        │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0010178",                                                  │
│                  "label": "congenital bilateral aplasia of vas deferens from CFTR mutation"      │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0008185",                                                  │
│                  "label": "hereditary chronic pancreatitis"                                      │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0008185",                                                  │
│                  "label": "hereditary chronic pancreatitis"                                      │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0008887",                                                  │
│                  "label": "bronchiectasis with or without elevated sweat chloride 1"             │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0009061",                                                  │
│                  "label": "cystic fibrosis"                                                      │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0018393",                                                  │
│                  "label": "male infertility with azoospermia or oligozoospermia due to single    │
│  gene mutation"                                                                                  │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0018801",                                                  │
│                  "label": "congenital bilateral absence of vas deferens"                         │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0018956",                                                  │
│                  "label": "idiopathic bronchiectasis"                                            │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0044663",                                                  │
│                  "label": "aquagenic palmoplantar keratoderma"                                   │
│              },                                                                                  │
│              "type": null                                                                        │
│          }                                                                                       │
│      ],                                                                                          │
│      "total": 10,                                                                                │
│      "disease_url_template": "https://monarchinitiative.org/disease/{disease_id}"                │
│  }                                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> User ──────────────────────────────────────────────────────────────────────╮
│ The CFTR gene, also known as the Cystic Fibrosis Transmembrane Conductance Regulator gene, is    │
│ associated with several diseases. Here are some of the diseases associated with the CFTR gene:   │
│                                                                                                  │
│  1 Cystic Fibrosis: The CFTR gene is causally associated with Cystic Fibrosis, a genetic         │
│    disorder characterized by the production of sweat with a high salt content and mucus          │
│    secretions with an abnormal viscosity. More information                                       │
│  2 Congenital Bilateral Aplasia of Vas Deferens from CFTR Mutation: Mutations in the CFTR gene   │
│    can lead to the congenital absence of the vas deferens, which can cause infertility in males. │
│    More information                                                                              │
│  3 Hereditary Chronic Pancreatitis: The CFTR gene is correlated with hereditary chronic          │
│    pancreatitis, a condition characterized by inflammation of the pancreas that persists over    │
│    time. More information                                                                        │
│  4 Bronchiectasis with or without Elevated Sweat Chloride 1: Mutations in the CFTR gene can also │
│    be correlated with bronchiectasis, a condition characterized by the abnormal widening of the  │
│    bronchial tubes. More information                                                             │
│                                                                                                  │
│ Please note that this is not an exhaustive list of diseases associated with the CFTR gene. The   │
│ CFTR gene plays a crucial role in various physiological processes, and mutations in this gene    │
│ can have diverse effects on different organ systems.                                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Changelog

* 1.0.1: improved error logging
* 1.0.0:
  * Replace .new_chat() and .continue_chat() with just chat()
  * Update function spec to provide actual Callables, not just method nodes
* 0.14.0: Added streamlit-based UI component
* 0.13.0: Added ability to clear history 
* 0.12.0: Added toxicity check for user messages with OpenAI Moderation endpoint
* 0.11.2: Added ability to swap out OpenAI API key for an active agent
