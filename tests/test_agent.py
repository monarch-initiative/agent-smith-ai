# pytests for tool_agent.py
from monarch_assistant.tool_agent import UtilityAgent
from monarch_assistant.models import *



class MonarchAgent(UtilityAgent):
    def __init__(self, name: str = "Assistant", system_message: str = "You are a helpful assistant"):
        super().__init__(name, system_message)

        self.register_api("monarch", "https://oai-monarch-plugin.monarchinitiative.org/openapi.json", "https://oai-monarch-plugin.monarchinitiative.org")
        self.register_callable_method("example_queries")


    def example_queries(self, num_examples: int) -> List[str]:
        """
        Generate example queries for the Monarch API.

        Args:
            num_examples: The number of example queries to generate.

        Returns: 
            A list of example queries.
        """
        util_agent = UtilityAgent("Utility", "Answer the given question as instructed, returning a JSON string as the result.")
        result = list(util_agent.new_chat(f"Please provide {num_examples} example questions one could ask about the Monarch Initiative Knowledge graph. Limit examples to genes, diseases, and phenotypes. Potential examples include 'What genes are associated with Cystic Fibrosis?' and 'What are diseases associated with short stature?'."))[0].content
        return result


def test_monarch_agent_initialize():
    agent = MonarchAgent("Monarch")

    assert agent.name == "Monarch"
    assert agent.api_set is not None
    assert agent.history is not None

    for message in agent.new_chat("Hey! What kinds of things can I ask you anyway? Call your function to give me some examples please?"):
        print("\n\n\n", message)


def test_api_tool_agent_initialize():
    agent = MonarchAgent("Monarch")
    
    assert agent.name == "Monarch"
    assert agent.system_message == "You are a helpful assistant who can connect to the Monarch API."
    assert agent.api_set is not None
    assert agent.history is not None


def test_api_tool_agent_new_chat():
    agent = MonarchAgent("Monarch")
    
    for message in agent.new_chat("Hi!"):
        print("\n\n\n", message)
        assert message.role is not None
        assert message.content is not None

     
    for message in agent.continue_chat("What genes are correlated with Cystic Fibrosis?"):
        print("\n\n\n", message)
        assert message.role is not None
        assert message.content is not None
