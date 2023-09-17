from agent_smith_ai.utility_agent import UtilityAgent

import textwrap
import os
from typing import Any, Dict

#load environment variables from .env file
import dotenv
dotenv.load_dotenv()


## A UtilityAgent can call API endpoints and local methods
class MonarchAgent(UtilityAgent):

    def __init__(self, name, model = "gpt-3.5-turbo-0613"):
        
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
        
        super().__init__(name,                                             # Name of the agent
                         system_message,                                   # Agent system message
                         model = model,                                    # (Default "gpt-3.5-turbo-0613") Openai model name
                         openai_api_key = os.environ["OPENAI_API_KEY"],    # (Default os.environ["OPENAI_API_KEY"]) API key; will default to OPENAI_API_KEY env variable
                         auto_summarize_buffer_tokens = 500,               # (Default 500) Summarize and clear the history when fewer than this many tokens remains in the context window. Checked prior to each message sent to the model.
                         summarize_quietly = False,                        # (Default False) If True, do not alert the user when a summarization occurs
                         max_tokens = None,                                # (Default None) maximum number of tokens this agent can bank (default: None, no limit)
                         token_refill_rate = 10000.0 / 3600.0)             # (Default 10k/hr) number of tokens to add to the bank per second

        ## register some API endpoints (inherited from UtilityAgent)
        ## the openapi.json spec must be available at the spec_url:
        ##    callable endpoints must have a "description" and "operationId"
        ##    params can be in body or query, but must be fully specified
        self.register_api("monarch", 
                          spec_url = "https://oai-monarch-plugin.monarchinitiative.org/openapi.json", 
                          base_url = "https://oai-monarch-plugin.monarchinitiative.org",
                          callable_endpoints = ['search_entity', 
                                                'get_disease_gene_associations', 
                                                'get_disease_phenotype_associations', 
                                                'get_gene_disease_associations', 
                                                'get_gene_phenotype_associations', 
                                                'get_phenotype_gene_associations', 
                                                'get_phenotype_disease_associations'])

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
