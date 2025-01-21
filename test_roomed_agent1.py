import json
import readline
import random
import os
from copy import deepcopy
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
from termcolor import colored
from RoomedAgent import RoomedAgent as Agent
from RoomedAgent import AutoRooms as Rooms
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
    rooms = Rooms((agentOrange, agentBlue))
    rooms.messages = [{"role": "user", "content": "Hi, please state your name and which function calls do you support?"}]
    #rooms.messages = [{"role": "user", "content": "try calling the functions several times and discover what they do"}]
    #rooms.messages = [{"role": "user", "content": "your goal is to reach 72"}]
    rooms.messages.insert(0, {"role": "system", "content": "Welcome to the AI party ,there is more than one agent in this conversation"})
    for message in rooms.messages:
        print(f"{message['role']}> {message['content']}")

    rooms.dm("agentOrange", "You are agentOrange")
    rooms.dm("agentBlue", "You are agentBlue")

    agents_mapping = {"agentOrange": agentOrange, "agentBlue": agentBlue}
    agents = list(agents_mapping.keys())

    # Enter the conversation loop
    while True:
        random.shuffle(agents)
        for agent in agents + ["user"]:
            print("=========================================")
            if agent == "user":
                user_input = input("user> ")
                if user_input.strip() != "":
                    rooms.user(user_input)
                continue

            response, function_call = rooms.chat(agent)
            if response is not None:
                print(colored(f"{agent}: {response}", attrs=['reverse']))

            if function_call is not None:
                function_name, function_arguments = function_call
                ic(f"Calling function: {function_name} with arguments: {function_arguments}")

                response = rooms.call()

                ic(f"Function call response: {json.loads(response)}")

if __name__ == '__main__':
    main()
