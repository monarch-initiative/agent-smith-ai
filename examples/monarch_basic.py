##
## This example demonstrates a basic UtilityAgent that can call API endpoints and local methods
## 
##
from .monarch_agent import MonarchAgent


agent = MonarchAgent("Monarch Assistant")
question = "What genes are associated with Cystic Fibrosis?"

## agent.new_chat(question) may result in a series of Message objects (which may consist of a series of function-call messages,
## function-call responses, and other messages)
## by default, the system message and initial prompt question are not included in the output, but can be
for message in agent.new_chat(question, yield_system_message = True, yield_prompt_message = True, author = "User"):
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

## agent.continue_chat(question) works just like .new_chat(), but doesn't allow including the system message
question_followup = "What other diseases are associated with the first one you listed?"
for message in agent.continue_chat(question_followup, yield_prompt_message = True, author = "User"):
    print("\n\n", message.model_dump())

question_followup = "What is the entropy of a standard tile set in Scrabble?"
for message in agent.continue_chat(question_followup, yield_prompt_message = True, author = "User"):
    print("\n\n", message.model_dump())