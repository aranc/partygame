import os
import openai

# read from ~/.openai.token
with open(os.path.expanduser("~/.openai.token")) as f:
    openai_api_key = f.read().strip()

openai.api_key = os.environ.get("OPENAI_API_KEY", openai_api_key)

def chat(**kwds):
    response = openai.chat.completions.create(**kwds)
    return response
