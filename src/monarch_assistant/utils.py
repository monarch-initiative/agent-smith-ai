import openai
import os

# a function that makes a call to the openai API, taking a system message (str) and user message (str)
# and returning a response (str)
def call_openai(system_message: str, user_message: str) -> str:
    openai.api_key = os.environ["OPENAI_API_KEY"]

    response = openai.ChatCompletion.create(
              model="gpt-3.5-turbo",
              messages=[{"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
              ])

    print(response)
    return response


system_prompt = """You are a helpful assistant that has the ability to call external tools using a specialized syntax.
Your message will be returned with the result of the call embedded as JSON.
For example, if you send the following message:

"The sum of 4 and 5 is {{sum(4, 5)}}"

The response will be 

"The sum of 4 and 5 is {'call': 'sum(4, 5)', 'result': 9}"

The following tools are available:
- sum(a, b): returns the sum of a and b
- product(a, b): returns the product of a and b
"""

import re
if __name__ == "__main__":
    call_openai(system_prompt, "What is the sum of 15 and 16?")
    x = "IMPUTE" + os.environ["INPUT_STRING"]
    # if x starts with IMPUTE, remove it and any following whitespace using regular expressions
    if x.startswith("IMPUTE"):
        x = re.sub(r"IMPUTE\s*", "", x)

