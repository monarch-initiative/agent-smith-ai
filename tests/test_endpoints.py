from fastapi.testclient import TestClient
import pprint


from monarch_assistant.main import app  # replace with the actual path of your FastAPI app
import monarch_assistant.utils as utils
from monarch_assistant.tool_agent import new_chat_safeeval_agent, continue_chat
from monarch_assistant.safe_eval_tools import SafeEval

test_client = TestClient(app)
pp = pprint.PrettyPrinter(indent=4)

# def test_new_chat_endpoint():
#     """Tests the /new_chat endpoint. This is shaky, since it relies on the model response to be good as well."""
#     new_chat = test_client.post("/new_chat", json = {"model": "gpt-3.5-turbo"}).json()
#     response = test_client.post("/continue_chat", json={"messages": new_chat, "user_message": "What can you tell me about Mowat-Wilson syndrome from the Monarch database?"})
#     print("Ummm")
#     pp.pprint(response.json())

def test_new_chat():
    """Tests the /new_chat endpoint. This is shaky, since it relies on the model response to be good as well."""
    messages = new_chat_safeeval_agent()
    pp.pprint(messages)
    #assert "4.3" in messages[-1]["content"]

# def test_chat_chain():
#     safe_eval = SafeEval()
#     print(safe_eval.evaluate("get_disease_gene_associations('MONDO:0009061', 5, 0)"))
#     messages = new_chat_safeeval_agent("What genes are associated with Cystic Fibrosis?", model = "gpt-4")
#     pp.pprint(messages)


# def test_search():
#     safe_eval = SafeEval()
#     res = safe_eval.search("Cystic Fibrosis")
#     pp.pprint(res)

# def test_new_chat_safeeval_agent():
#     response = new_chat_safeeval_agent("Can you tell me genes involved with MONDO:0009061? I am looking for the top 5.")
#     print(response)
#     assert 1 == 2