import json
import readline
import random
import os
from copy import deepcopy
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
from termcolor import colored
from NamedAgent import NamedAgent as Agent
from SourceTracker import expose_to_agent
from icecream import ic

board = 0

class AgentOrange(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = {}

    @expose_to_agent
    def go_big(self):
        return self._go_big()

    def _go_big(self):
        global board
        board += 10
        return {"board": board}

    @expose_to_agent
    def get_board(self):
        global board
        return board

class AgentBlue(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = {}

    @expose_to_agent
    def go_small(self):
        return self._go_small()

    def _go_small(self):
        global board
        board -= 1
        return {"board": board}

    @expose_to_agent
    def get_board(self):
        global board
        return board

def main():
    agentOrange = AgentOrange()
    agentOrange.set_name("agentOrange")
    agentBlue = AgentBlue()
    agentBlue.set_name("agentBlue")
    messages = []
    messages = [{"role": "user", "content": "Hi, please state your name and which function calls do you support?"}]
    #messages = [{"role": "user", "content": "try calling the functions several times and discover what they do"}]
    #messages = [{"role": "user", "content": "your goal is to reach 72"}]
    messages.insert(0, {"role": "system", "content": "Welcome to the AI party ,there is more than one agent in this conversation"})
    for message in messages:
        print(f"{message['role']}> {message['content']}")

    agents_mapping = {"agentOrange": agentOrange, "agentBlue": agentBlue}
    agents = list(agents_mapping.keys())

    # Enter the conversation loop
    while True:
        if len(messages) == 0 or agentOrange.get_message_role(messages[-1]) != "user":
            user_input = input("user> ")
            if user_input.strip() != "":
                messages.append({"role": "user", "content": user_input})

        random.shuffle(agents)
        for agent in agents:
            agent = agents_mapping[agent]

            while True:
                print("==================================================")
                response = agent.chat(messages)
                messages.append(response)

                if agent.get_content_from_message(response):
                    print(colored(f"{agent.name}: {agent.get_content_from_message(response)}", attrs=['reverse']))

                if agent.is_message_containing_function_call(response):
                    function_name = agent.get_function_name_from_message(response)
                    function_arguments = agent.get_function_arguments_from_message(response)
                    ic(f"Calling function: {function_name} with arguments: {function_arguments}")

                    response = agent.call(response)

                    ic(f"Function call response: {json.loads(agent.get_content_from_message(response))}")
                    messages.append(response)
                else:
                    break

if __name__ == '__main__':
    main()
