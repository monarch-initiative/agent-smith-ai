from monarch_assistant.cli_agent import CLIAgent

import textwrap
from typing import Any, Dict

# load environment variables from .env file
import dotenv
dotenv.load_dotenv()

class MonarchAgent(CLIAgent):
    # A MonarchAgent extends the CLIAgent, which extends the UtilityAgent.
    def __init__(self, name):
        
        # define a system message
        system_message = textwrap.dedent(f"""
            You are the Monarch Assistant, an AI-powered chatbot that can answer questions about data from the Monarch Initiative knowledge graph. 
            You can search for entities such as genes, diseases, and phenotypes by name to get the associated ontology identifier. 
            You can retrieve associations between entities via their identifiers. 
            Users may use synonyms such as 'illness' or 'symptom'. Do not assume the user is familiar with biomedical terminology. 
            Always add additional information such as lay descriptions of phenotypes. 
            If the user changes the show function call setting, do not make any further function calls immediately.
            IMPORTANT: Include markdown-formatted links to the Monarch Initiative for all results using the templates provided by function call responses.'.
            """).strip()
        # call the parent constructor providing a name for the agent and the system message
        super().__init__(name, system_message)

        # register some API endpoints (inherited fro UtilityAgent)
        self.register_api("monarch", 
                          "https://oai-monarch-plugin.monarchinitiative.org/openapi.json", 
                          "https://oai-monarch-plugin.monarchinitiative.org",
                          callable_endpoints = ['search_entity', 
                                                'get_disease_gene_associations', 
                                                'get_disease_phenotype_associations', 
                                                'get_gene_disease_associations', 
                                                'get_gene_phenotype_associations', 
                                                'get_phenotype_gene_associations', 
                                                'get_phenotype_disease_associations'])


        # the agent can also call local methods, but we have to register them
        self.register_callable_methods(['compute_entropy'])

        # let's also show the function calls and results behind the scenes as they happen (inherited from CLIAgent)
        self.show_function_calls()

    ## Callable methods should be type-annotated and well-documented with docstrings parsable by the docstring_parser library
    ## try asking something like "What is the entropy of a standard tile set in Scrabble?"
    def compute_entropy(self, items: Dict[Any, int]):
        """Compute the information entropy of a given set of item counts.
        
        Args:
            items (str): A dictionary of items and their counts.
            
        Returns:
            The information entropy of the item counts.
        """
        from math import log2
        
        total = sum(items.values())
        return -sum([count / total * log2(count / total) for count in items.values()])


# Create a new agent
agent = MonarchAgent("Monarch Assistant")

# We won't include this information in the chat, but we do want to render some welcome text for the user
# We can use the render_panel method to do this (inherited from CLIAgent)
agent.render_panel("""Hello! I'm the Monarch Assistant, an AI-powered chatbot that can answer questions about genes, diseases, and phenotypes, based on information hosted at https://monarchinitiative.org.
* You can exit by saying 'exit', and you can request that I turn on or off function call responses by saying 'show function calls' or 'hide function calls' at any time. They are shown by default.
* I do not currently implement context-window management, so after a while your conversation will produce an error.
* For a bit of fun, try asking me to describe my plan. For example, "What are the symptoms of Cystic Fibrosis? Describe your plan before you execute it."
""", title = "Welcome", style = "green", title_align = "center", newline = False)

# Start the chat UI (inherited from CLIAgent)
agent.start_chat_ui()