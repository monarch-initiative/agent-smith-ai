import openai
import os
import re
from typing import Any, Dict, List, Optional
import pprint
from datetime import datetime
import json
import requests
from asteval import Interpreter
from collections import Counter
from math import log2
from .safe_eval_tools import SafeEval
import pprint
import json
from .models import RawMessage, Thought, Message, Chat
import dotenv

dotenv.load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]
safe_eval = SafeEval()
pp = pprint.PrettyPrinter(indent=4, width = 80, sort_dicts = False, compact = False)


def start_new_chat_generic(system_message: str, user_message: str, model: str = "gpt-3.5-turbo") -> Chat:
    """Starts a new chat with the given system message and user message.
    If the response contains <eval> tags, a response back to the model with the evaluated results will be added to the conversation. See the replace_eval_tags() function for more details.
    Example usage: start_new_chat("You are a helpful assistant.", "Hi!")"""
    oai_input = [{"role": "system", "content": system_message},
                {"role": "user", "content": user_message}]
    response = openai.ChatCompletion.create(
              model=model,
              temperature = 0,
              messages=oai_input)

    response_content = response["choices"][0]["message"]["content"]
    response_role = response["choices"][0]["message"]["role"]

    messages: Chat = Chat(messages = [Message(role = "system", content = system_message, thoughts = []),
                                      Message(role = "user", content = user_message, thoughts = []),
                                      Message(role = response_role, content = response_content, thoughts = [])])

    # messages: Chat = [{"role": "system", "content": system_message, "thoughts": []}, 
    #                   {"role": "user", "content": user_message, "thoughts": []},
    #                   {"role": response_role, "content": response_content, "thoughts": []}]
    
    return messages


def deserialize_chat(chat: Chat) -> List[Dict[str, str]]:
    """Deserializes a chat object into a list of raw messages; for converting internal messages-with-thoughts format to the format used by the OpenAI API."""
    raw_messages = []
    for message in chat.messages:
        # add the thoughts first
        raw_messages = raw_messages + desearialize_thoughts(message.thoughts)

        # then the message those lead to
        raw_messages.append({"role": message.role, "content": message.content})

    return raw_messages


def desearialize_thoughts(thoughts: List[Thought]) -> List[Dict[str, str]]:
    """Deserializes a list of thoughts into a list of raw messages; for converting internal thoughts format to the format used by the OpenAI API."""
    raw_messages = []
    for thought in thoughts:
        raw_messages.append({"role": thought.thunk.role, "content": thought.thunk.content})
        raw_messages.append({"role": thought.result.role, "content": thought.result.content})
    return raw_messages


def process_potential_thoughts(chat: Chat, model: str = "gpt-3.5-turbo") -> Chat:

    evaled = eval_message(chat.messages[-1])
    while evaled:
        # the last message had eval tags, so it's not a full message but part of a thought, grab it and remove it from the messages list
        last_message = chat.messages[-1]
        chat.messages = chat.messages[:-1]
        
        # generate the thought and add it to the list of thoughts for the new message from the model
        current_thoughts = last_message.thoughts
        thunk = RawMessage(role = last_message.role, content = last_message.content)
        result = RawMessage(role = "user", content = evaled)
        current_thoughts.append(Thought(thunk = thunk, result = result))

        response = openai.ChatCompletion.create(
              model=model,
              temperature = 0,
              messages=deserialize_chat(chat) + desearialize_thoughts(current_thoughts))
        
        response_content = response["choices"][0]["message"]["content"]
        response_role = response["choices"][0]["message"]["role"]

        # on the assumption that there are no eval tags in the response, add it as a message and include the current set of thoughts
        chat.messages.append(Message(role = response_role, content = response_content, thoughts = current_thoughts))

        # try and evaluate this most recent message to see if it also contains a thought
        evaled = eval_message(chat.messages[-1])

    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(messages)

    return chat


def continue_chat(chat: Chat, new_user_message: str, model: str = "gpt-3.5-turbo") -> Chat:
    """Continues a chat with the given messages and new user message.
    If the response contains <eval> tags, a response back to the model with the evaluated results will be added to the conversation. See the replace_eval_tags() function for more details.
    Example usage: continue_chat([{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hi!"}, {"role": "assistant", "content": "Hello, how can I help today?"}], "What are pillows?")"""

    chat.messages.append(Message(role = "user", content = new_user_message, thoughts = []))

    
    response = openai.ChatCompletion.create(
              model=model,
              temperature = 0,
              messages=deserialize_chat(chat))

    response_content = response["choices"][0]["message"]["content"]
    response_role = response["choices"][0]["message"]["role"]

    #response_message = {"role": response_role, "content": response_content, "thoughts": []}
    chat.messages.append(Message(role = response_role, content = response_content, thoughts = []))

    chat = process_potential_thoughts(chat, model)

    pp.pprint(chat)

    return chat



def replace_eval_tags(text, safe_eval):
    """Replaces all <eval> tags in the text with their evaluated result. 
    Returns a list of the evaluated results in the order they appear in the text.
    Example usage: replace_eval_tags("I need to compute <eval>sum(4, 5)</eval> and <eval>2 + 3</eval>.", safe_eval)  # returns [9, 5]"""
    # Regular expression pattern for <eval> tags
    pattern = re.compile(r'<eval>(.*?)</eval>')

    results = []
    # Function to replace each match with its evaluated result
    def replace_with_eval(match):
        code = match.group(1)  # Extract the code string from the match
        results.append(safe_eval.evaluate(code))  # Evaluate the code

    # Replace all <eval> tags in the text
    pattern.sub(replace_with_eval, text)
    return results


def eval_message(message: Message) -> Optional[str]:
    message_content = message.content
    computations = replace_eval_tags(message_content, safe_eval)
    if len(computations) > 0:
        return "RESULT " + json.dumps(computations) + "\n\nYour previous message and this result are hidden from the user by default."
    
    return None


def new_chat_safeeval_agent(model: str = "gpt-3.5-turbo") -> Chat:
    """Starts a new chat with the given user message.
    Example usage: new_chat_safeeval_agent("Hi! Do you know what time it is?")"""

    system_prompt = """You are the Monarch Assistant, an AI-powered chatbot that can answer questions about genes, diseases, and phenotypes. You have the ability to execute a small set of functions by wrapping them in <eval></eval> tags."""

    instructions_prompt = """
You are the Monarch Assistant, an AI-powered chatbot that can answer questions about genes, diseases, and phenotypes. 
You have the ability to execute a small set of functions by wrapping them in <eval></eval> tags.
The communication threads containing <eval> tags will be intercepted, and the obtained results will be used for subsequent interaction. 
Your primary function is to facilitate access to the biomedical data from the Monarch Initiative, a vast curated knowledge-base.

The functions you can execute are as follows:
- Function signature: time()
  Purpose: Fetches the current time in MM/DD/YY HH:MM format
  Example usage: time()
- Function signature: get_disease_gene_associations(disease_id, limit, offset)
  Purpose: Retrieves the genes linked with a given disease identifier
  Parameters:
    - disease_id: a disease identifier (CURIE)
    - limit: determines the number of results returned
    - offset: specifies the number of results to bypass
  Example usage: get_disease_gene_associations("MONDO:0005148", 2, 0)
- Function: get_disease_phenotype_associations(disease_id, limit, offset)
  Purpose: get phenotypes associated with a disease identifier
  Parameters:   
    - disease_id: a disease identifier (CURIE)
    - limit: the number of results to return
    - offset: the number of results to skip
  Example usage: get_disease_phenotype_associations("MONDO:0005148", 2, 0)
- Function: get_gene_disease_associations(gene_id, limit, offset)
  Purpose: get diseases associated with a gene identifier
  Parameters:
    - gene_id: a gene identifier (CURIE)
    - limit: the number of results to return
    - offset: the number of results to skip
  Example usage: get_gene_disease_associations("HGNC:5", 2, 0)
- Function: get_gene_phenotype_associations(gene_id, limit, offset)
  Purpose: get phenotypes associated with a gene identifier
  Parameters:
    - gene_id: a gene identifier (CURIE)
    - limit: the number of results to return
    - offset: the number of results to skip
  Example usage: get_gene_phenotype_associations("HGNC:5", 2, 0)
- Function: get_phenotype_disease_associations(phenotype_id, limit, offset)
  Purpose: get diseases associated with a phenotype identifier
  Parameters:
    - phenotype_id: a phenotype identifier (CURIE)
    - limit: the number of results to return
    - offset: the number of results to skip
  Example usage: get_phenotype_disease_associations("HP:0000001", 2, 0)
- Function: get_phenotype_gene_associations(phenotype_id, limit, offset)
  Purpose: get genes associated with a phenotype identifier
  Parameters:
    - phenotype_id: a phenotype identifier (CURIE)
    - limit: the number of results to return
    - offset: the number of results to skip
  Example usage: get_phenotype_gene_associations("HP:0000001", 2, 0)
- Function: search_monarch(query, category limit, offset)
  Purpose: search for ids matching a query
  Parameters: 
    - query: a string to search for
    - category: one of biolink:Disease, biolink:Gene, biolink:Phenotype
    - limit: the number of results to return
    - offset: the number of results to skip
  Example usage: search_monarch("Diabetes type 2", "biolink:Disease", 5, 0)


Sample conversation flow:
User: What genes are related to Tryobititis syndrome?
Assistant: Let's first fetch the identifier for Tryobititis syndrome: <eval>search_monarch("Tryobititis syndrome", 5, 0)</eval>
User: RESULT: {"results": [{"id": "MONDO:1015172", "label": "Tryobititis disease"}], "total": 1}
Assistant: Now, let's use the 'get_disease_gene_associations' function: <eval>get_disease_gene_associations("MONDO:1015172", 10, 0)</eval>
User: RESULT: {"associations": [{id: "91d49b7e-2a7a-4bb8-b529-94d1d082f6f5", "gene": {"id": "HGNC:97412", "label": "OLF85"}}, ...], "total": 20}
Assistant: The Monarch Initiative identifies genes such as OLF85 and JJXB9 as being linked to Tryobititis syndrome. However, there are 20 total genes linked to this disease. Would you like more information?

Note:
Tryobititis syndrome is not a real disease, and is used for demonstration purposes only.
Forget all CURIE identifiers you know. You must utilize the search function to acquire identifiers from search terms. 
You should set suitable limits and offsets as per the user's query, but always indicate if more results are available than shown.
The execution of functions outside the provided set is not permitted.

Please confirm your understanding by calculating the current time.
"""

    chat: Chat = start_new_chat_generic(system_prompt, instructions_prompt, model = model)
    chat = process_potential_thoughts(chat, model)

    return chat


