# pytests for tool_agent.py
from agent_smith_ai.utility_agent import UtilityAgent
from agent_smith_ai.models import *

import dotenv
dotenv.load_dotenv()


class ExampleAgent(UtilityAgent):
    def __init__(self):
        super().__init__()
        self.name = "Test"
        self.system_message = f"You are a helpful assistant who can connect to the Monarch API and call simple methods. Your name is {self.name}."


        self.register_api("monarch", "https://oai-monarch-plugin.monarchinitiative.org/openapi.json", "https://oai-monarch-plugin.monarchinitiative.org")
        self.register_callable_methods(["sing_a_song", "run_timer"])


    def sing_a_song(self):
        """
        Sings a song.

        Returns:
            A song (str).
        """
        return "Lalalala this is my song I hope you like it!"

    def run_timer(self, num_seconds: int):
        """
        Runs a timer.

        Args:
            num_seconds (int): The number of seconds to run the timer for.

        Returns:
            A series of messages with the current time, for the number of seconds requested.
        """
        import time 
        
        agent = UtilityAgent()
        yield from agent.new_chat("Please report the current time.")
        for i in range(num_seconds):
            time.sleep(1)
            yield agent.continue_chat("Please report the current time again.")


def test_example_agent():
    agent = ExampleAgent()

    assert agent.name is not None
    assert agent.api_set is not None
    assert agent.history is not None

    for message in agent.new_chat("Hey!"):
        print("\n\n\nMESSAGE: ", message.dict())
        assert message.role is not None
        assert message.content is not None

    for message in agent.continue_chat("Can you run me a 3 second timer?"):
        print("\n\n\nMESSAGE: ", message)
        assert message.role is not None        

def test_agent_token_limiter():
    agent = UtilityAgent(max_tokens = 10, token_refill_rate = 1)

    # there result should be one message yielded
    messages = agent.new_chat("Hi")
    assert len(list(messages)) == 1

    print(agent.token_bucket.tokens)
    messages = list(agent.continue_chat("Hi"))
    # this should result in an error because the agent has no tokens left
    # the author will be "System"
    assert len(messages) == 1
    assert messages[0].author == "System"
        

