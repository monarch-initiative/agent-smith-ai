##
## This example demonstrates a basic UtilityAgent that can call API endpoints and local methods
## 
##


from monarch_assistant.utility_agent import UtilityAgent

import textwrap
import os

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
        
        ## call the parent constructor providing a name for the agent and the system message
        ## we can also specify the model (it must be an OpenAI function-calling model)
        ## and the OpenAI API key (if not provided, it will be read from the OPENAI_API_KEY environment variable, here we do so explicity)
        super().__init__(name, system_message, model = "gpt-3.5-turbo-0613", openai_api_key = os.environ["OPENAI_API_KEY"])

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
        self.register_callable_methods(['entropy'])



agent = MonarchAgent("Monarch Assistant")

## agent.new_chat(question) may result in a series of Message objects (to handle function calls and responses)

## by default, the system message and initial prompt question are not included in the output, but can be

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
question = "What genes are associated with Cystic Fibrosis?"
for message in agent.new_chat(question, yield_system_message = True, yield_prompt_message = True, author = "User"):
    print("\n\n", message.dict())

## agent.continue_chat(question) works just like .new_chat(), but doesn't allow including the system message
question_followup = "What other diseases are associated with the first one you listed?"
for message in agent.continue_chat(question_followup, yield_prompt_message = True, author = "User"):
    print("\n\n", message.dict())

