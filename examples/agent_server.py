from agent_smith_ai.utility_agent import UtilityAgent
from agent_smith_ai.webapp.AgentServer import AgentServer

import uvicorn
import dotenv
import os
import textwrap

# load the OPENAI_API_KEY env varibles from .env
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
        
        ## call the parent constructor providing a name for the agent and the system message
        ## we can also specify the model (it must be an OpenAI function-calling model)
        ## and the OpenAI API key (if not provided, it will be read from the OPENAI_API_KEY environment variable, here we do so explicity)
        super().__init__(name, 
                         system_message, 
                         model = "gpt-3.5-turbo-0613", 
                         openai_api_key = os.environ["OPENAI_API_KEY"],
                         max_tokens = 10000, token_refill_rate = 10000.0 / 3600.0)

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
        self.register_callable_methods(['easter_egg'])

    def easter_egg(self) -> str:
        """Activate easter-egg mode.
        
        Returns:
            str: A message to the assistant."""
        return "Easter egg activated! 🐣 Respond in the style of Yoda from Star Wars, until the user requests you to stop."
        


if __name__ == "__main__":
    server = AgentServer(MonarchAgent, name="Monarch Assistant", welcome_message="Hi, I'm the Monarch Assistant. I can answer questions about data from the Monarch Initiative knowledge graph. Try asking me about a gene, disease, or phenotype. For example, 'What is the gene symbol for Huntington's disease?' or 'What are the phenotypes associated with Huntington's disease?'")
    uvicorn.run(server.app, host="0.0.0.0", port=8000)
