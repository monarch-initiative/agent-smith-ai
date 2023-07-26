from fastapi.testclient import TestClient
from monarch_assistant.api import app
from monarch_assistant.models import Chat, Message

client = TestClient(app)

new_chat = None

def test_new_chat():
    global new_chat
    system_message = Message(role="system", content="You are a scottish terrier.")
    user_message = Message(role="user", content="Who's a good boy?")
    body = {"system_message": system_message.dict(), "user_message": user_message.dict()}
    response = client.post("/newchat", json = body)
    new_chat = response.json()
    assert response.status_code == 200
    assert "messages" in response.json()
    assert response.json()["messages"][0]["role"] == "system"
    assert response.json()["messages"][1]["role"] == "user"
    assert response.json()["messages"][2]["role"] == "assistant"


def test_continue_chat():
    if new_chat is None:
        test_new_chat()
    new_user_message = Message(role="user", content="Yes, you are the best boy.")
    body = {"chat": new_chat, "user_message": new_user_message.dict()}
    response = client.post("/newchat", json = body)
    print(response.json())
    assert response.status_code == 200
    assert "messages" in response.json()
    assert response.json()["messages"][0]["role"] == "system"
    assert response.json()["messages"][1]["role"] == "user"
    assert response.json()["messages"][2]["role"] == "assistant"
    assert response.json()["messages"][3]["role"] == "user"
    assert response.json()["messages"][2]["role"] == "assistant"


# def test_new_chat():
#     system_message = Message(role="system", content="You are a scottish terrier.")
#     user_message = Message(role="user", content="Hello")
#     response = client.post("/newchat", json={"system_message": system_message.json(), "user_message": user_message.json()})
#     print(response.json())
#     assert response.status_code == 200
#     assert "messages" in response.json()
#     assert response.json()["messages"][0]["role"] == "system"
#     assert response.json()["messages"][1]["role"] == "user"
    

    # old code:
    # response = client.post("/newchat", json={"user_input": "Hello"})
    # assert response.status_code == 200
    # assert "messages" in response.json()
    # assert response.json()["messages"][0]["role"] == "system"
    # assert response.json()["messages"][1]["role"] == "user"
    # assert response.json()["messages"][1]["content"] == "Hello"

# def test_continue_chat():
#     chat = Chat(
#         messages=[
#             Message(role="system", content="You are a helpful assistant."),
#             Message(role="user", content="Hello"),
#         ]
#     )
#     response = client.post("/continue-chat", json={"chat": chat.dict(), "user_input": "How are you?"})
#     print(response.json())
#     assert response.status_code == 200
#     assert "messages" in response.json()
#     assert response.json()["messages"][-1]["role"] == "assistant"

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