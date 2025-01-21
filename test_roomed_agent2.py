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

def main():
    agentOrange = Agent(name="agentOrange")
    agentBlue = Agent(name="agentBlue")
    agentYellow = Agent(name="agentYellow")
    agentGreen = Agent(name="agentGreen")
    rooms = Rooms((agentOrange, agentBlue, agentYellow, agentGreen))

    rooms.dm("agentOrange", "You are agentOrange")
    rooms.dm("agentBlue", "You are agentBlue")
    rooms.dm("agentYellow", "You are agentYellow")
    rooms.dm("agentGreen", "You are agentGreen")

    rooms.move("agentOrange", "saloon")
    rooms.move("agentBlue", "saloon")
    rooms.move("agentYellow", "saloon")
    rooms.move("agentGreen", "saloon")
    rooms.localAnnouncer("saloon", "Hello, everyone!")
    rooms.localAnnouncer("saloon", "the first word is avocado. please remember that")

    rooms.move("agentOrange", "kitchen")
    rooms.move("agentBlue", "kitchen")
    rooms.localAnnouncer("saloon", "the second word is banana. please remember that")
    rooms.localAnnouncer("kitchen", "the second word is brocoli. please remember that")
    rooms.globalAnnouncer("the third word is carrot. please remember that")

    rooms.move("agentBlue", "saloon")
    rooms.localAnnouncer("saloon", "the fourth word is deli. please remember that")
    rooms.localAnnouncer("kitchen", "the fourth word is device. please remember that")
    rooms.dm("agentBlue", "hey agent blue, can you please tell a joke to lighten the mood? dont tell your words yet")
    rooms.chat("agentBlue")

    rooms.dm("agentOrange", "hey agent orange, how are you feeling so far? we are almost done (dont mention the words yet)")
    rooms.chat("agentOrange")

    rooms.dm("agentYellow", "the fifth word is eggplant. please remember that")

    print(rooms.rooms.rooms)
    rooms.clear_all()
    print(rooms.rooms.rooms)

    expected = {}
    expected["agentOrange"] = "agentOrange is expected to have the following words: avocado, brocoli, carrot, device"
    expected["agentBlue"] = "agentBlue is expected to have the following words: avocado, brocoli, carrot, deli"
    expected["agentYellow"] = "agentYellow is expected to have the following words: avocado, banana, carrot, deli, eggplant"
    expected["agentGreen"] = "agentGreen is expected to have the following words: avocado, banana, carrot, deli"

    responses = {}
    for agent in ("agentOrange", "agentBlue", "agentYellow", "agentGreen"):
        rooms.dm(agent, "please repeat the words")
        responses[agent] = rooms.chat(agent)[0]

    for message in rooms.get_messages():
        print(message)

    for agent in ("agentOrange", "agentBlue", "agentYellow", "agentGreen"):
        print("====================================")
        print(f"agent: {agent}")
        for message in rooms.get_messages(agent):
            print(message)
        print(expected[agent])
        print("====================================")

    print()
    print()
    for agent in ("agentOrange", "agentBlue", "agentYellow", "agentGreen"):
        print(expected[agent])
        print(colored(f"{agent}: {responses[agent]}", attrs=['reverse']))

if __name__ == '__main__':
    main()
