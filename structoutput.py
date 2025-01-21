import os
import atexit
import readline
from termcolor import colored
from Agent import Agent
from SourceTracker import expose_to_agent
from icecream import ic
from pydantic import BaseModel

class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str

class BananLogic(BaseModel):
    aSentenceThatDoesNotIncludeTheWordBanana: str
    aSentenceThatIncludesTheWordBanana: str
    anotherSentenceThatDoesNotIncludeTheWordBanana: str

def set_history():
    # Set the path for the history file
    history_file = os.path.join(os.path.expanduser("~"), ".python_history")

    # Load the history if the file exists
    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass

    # Set the maximum number of history items
    readline.set_history_length(1000)

    # Save the history on exit
    atexit.register(readline.write_history_file, history_file)


def main():
    set_history()

    agent = Agent(model="gpt-4o-2024-08-06", connector="openai_beta")
    messages = []

    user_input = input("user> ")
    messages.append({"role": "user", "content": user_input})

    response = agent.chat(messages, response_format=BananLogic)
    messages.append(response)

    if agent.get_content_from_message(response):
        print(colored(agent.get_content_from_message(response), attrs=['reverse']))

if __name__ == '__main__':
    main()
