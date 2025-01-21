import os
import sys
import json
from copy import deepcopy
from icecream import ic
from Agent import Agent

DEBUG_MODE1 = False
DEBUG_MODE2 = False
DEBUG_MODE3 = False

def get_content(message):
    try:
        return message.content
    except:
        return message["content"]

def get_role(message):
    try:
        return message.role
    except:
        return message["role"]

def is_encapsulated_message(message):
    return type(message) is dict and set(message.keys()) == {"name", "message", "listeners"}

def filter_messages(messages, name):
    _messages = []
    for message in messages:
        if type(message) is dict and "log" in message:
            continue

        if not is_encapsulated_message(message):
            _messages.append(message)
            continue

        if message["name"] == name:
            _messages.append(message["message"])
            continue

        if get_role(message["message"]) == "tool":
            continue

        if not get_content(message["message"]):
            continue

        if name not in message.get("listeners", ()):
            continue

        _messages.append({"role": "user", "content": f"{message['name']}: {get_content(message['message'])}"})

    return _messages

class RoomedAgent(Agent):
    def __init__(self, *args, **kwds):
        if "name" in kwds:
            self.name = kwds.pop("name")
        else:
            self.name = None
        Agent.__init__(self, *args, **kwds)

    def set_name(self, name):
        self.name = name

    def chat(self, messages, listeners=(), **kwds):
        if self.name is None:
            return super().chat(messages, **kwds)

        listeners = list(listeners)

        messages = filter_messages(messages, self.name)
        if DEBUG_MODE1:
            print("==================================================")
            print(f"Agent: {self.name}")
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            for message in messages:
                print(message)
                print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print("==================================================")
        response = super().chat(messages, **kwds)
        return {"name": self.name, "message": response, "listeners": listeners}
    
    def call(self, message):
        if self.name is None:
            return super().call(message)

        assert message["name"] == self.name
        response = super().call(message["message"])
        return {"name": self.name, "message": response, "listeners": ()}

    @staticmethod
    def get_message_role(message):
        if is_encapsulated_message(message):
            return Agent.get_message_role(message["message"])
        else:
            return Agent.get_message_role(message)

    @staticmethod
    def is_message_containing_function_call(message):
        if is_encapsulated_message(message):
            return Agent.is_message_containing_function_call(message["message"])
        else:
            return Agent.is_message_containing_function_call(message)

    @staticmethod
    def get_function_name_from_message(message):
        if is_encapsulated_message(message):
            return Agent.get_function_name_from_message(message["message"])
        else:
            return Agent.get_function_name_from_message(message)

    @staticmethod
    def get_function_arguments_from_message(message):
        if is_encapsulated_message(message):
            return Agent.get_function_arguments_from_message(message["message"])
        else:
            return Agent.get_function_arguments_from_message(message)

    @staticmethod
    def get_content_from_message(message):
        if is_encapsulated_message(message):
            return Agent.get_content_from_message(message["message"])
        else:
            return Agent.get_content_from_message(message)

class ManualRooms:
    def __init__(self, _agents=()):
        self.agents = {agent.name: agent for agent in _agents} # agent name -> agent
        self.rooms = {} # room name -> agent names
        self.agent_locations = {} # agent name -> room name

    def introduce_new_agent(self, agent):
        self.agents[agent.name] = agent

    def where_is(self, name):
        return self.agent_locations.get(name, None)

    def who(self, room):
        return self.rooms.get(room, set())

    def move(self, name, room):
        if self.where_is(name) is not None:
            self.leave(name)
        self.agent_locations[name] = room
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(name)

    def leave(self, name):
        room = self.where_is(name)
        if room is None:
            return
        self.rooms[room].remove(name)
        self.agent_locations[name] = None

    def clear(self, room):
        for agent in list(self.rooms[room]):
            self.leave(agent)

    def clear_all(self):
        for agent in list(self.agents.keys()):
            self.leave(agent)

    def chat(self, name, messages, **kwds):
        room = self.where_is(name)
        if room is None:
            listeners = ()
        else:
            listeners = self.rooms[room] - {name}
        return self.agents[name].chat(messages, listeners, **kwds)

    def localAnnouncer(self, voice_name, room, message):
        message = {"role": "assistant", "content": message}
        listeners = list(self.rooms[room])
        return {"name": voice_name, "message": message, "listeners": listeners}

    def globalAnnouncer(self, voice_name, message):
        message = {"role": "assistant", "content": message}
        listeners = list(self.agents.keys())
        return {"name": voice_name, "message": message, "listeners": listeners}

    def dm(self, voice_name, name, message):
        message = {"role": "assistant", "content": message}
        listeners = [name]
        return {"name": voice_name, "message": message, "listeners": listeners}


def save_json(filename, messages):
    with open(filename, "w") as f:
        f.write("[\n")
        for idx, message in enumerate(messages):
            sep = ",\n" if idx < len(messages) - 1 else "\n"
            try:
                f.write("  " + json.dumps(str(message))+ sep)
            except Exception as e:
                ic(e)
                ic(message)
                import pdb; pdb.set_trace()
        f.write("]\n")

def save_messages_after_call(func):
    def wrapper(self, *args, **kwargs):
        if DEBUG_MODE2:
            print("=========== BEFORE")
            for message in self.messages:
                print(message)
            print("=========== /BEFORE")
        result = func(self, *args, **kwargs)
        if DEBUG_MODE2:
            print("=========== AFTER")
            for message in self.messages:
                print(message)
            print("=========== /AFTER")
        self.save_messages()  # Save messages after the function call
        return result
    return wrapper

class AutoRooms:
    def __init__(self, _agents=()):
        self.rooms = ManualRooms(_agents)

        # feel free to get / set the messages and voice_name attributes
        self.messages = []
        self.voice_name = "announcer"
        self.save_file = None

    def set_save_file(self, save_file):
        self.save_file = os.path.expanduser(save_file)

    def get_messages(self, name=None):
        if name is None:
            return self.messages
        messages = filter_messages(self.messages, name)
        return messages

    @save_messages_after_call
    def system(self, message):
        self.messages.append({"role": "system", "content": message})
        return message

    @save_messages_after_call
    def user(self, message):
        self.messages.append({"role": "user", "content": message})
        return message

    def introduce_new_agent(self, agent):
        self.rooms.introduce_new_agent(agent)

    def where_is(self, name):
        return self.rooms.where_is(name)

    def who(self, room):
        return self.rooms.who(room)

    def move(self, name, room):
        self.rooms.move(name, room)

    def leave(self, name):
        self.rooms.leave(name)

    def clear(self, room):
        self.rooms.clear(room)

    def clear_all(self):
        self.rooms.clear_all()

    @save_messages_after_call
    def chat(self, name, **kwds):
        if DEBUG_MODE3:
            for idx, message in enumerate(self.get_messages(name)):
                print(idx, message)
        response = self.rooms.chat(name, self.messages, **kwds)
        self.messages.append(response)

        if RoomedAgent.is_message_containing_function_call(response):
            return RoomedAgent.get_content_from_message(response), (RoomedAgent.get_function_name_from_message(response), RoomedAgent.get_function_arguments_from_message(response))

        return RoomedAgent.get_content_from_message(response), None

    @save_messages_after_call
    def call(self):
        messages = self.messages
        assert RoomedAgent.is_message_containing_function_call(self.messages[-1])
        agent = self.rooms.agents[self.messages[-1]["name"]]
        response = agent.call(self.messages[-1])
        self.messages.append(response)
        return RoomedAgent.get_content_from_message(response)

    @save_messages_after_call
    def localAnnouncer(self, room, message, voice=None):
        if voice is None:
            voice = self.voice_name
        _message = self.rooms.localAnnouncer(voice, room, message)
        self.messages.append(_message)
        return message

    @save_messages_after_call
    def globalAnnouncer(self, message, voice=None):
        if voice is None:
            voice = self.voice_name
        _message = self.rooms.globalAnnouncer(voice, message)
        self.messages.append(_message)
        return message

    @save_messages_after_call
    def dm(self, name, message, voice=None):
        if voice is None:
            voice = self.voice_name
        _message = self.rooms.dm(voice, name, message)
        self.messages.append(_message)
        return message

    @save_messages_after_call
    def log(self, message):
        self.messages.append({"log": message})
        return message

    def save_messages(self):
        if self.save_file is not None:
            save_json(self.save_file, self.messages)
