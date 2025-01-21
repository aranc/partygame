from icecream import ic
from Agent import Agent

DEBUG_MODE = False

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
    return type(message) is dict and set(message.keys()) == {"name", "message"}

def filter_messages(messages, name):
    _messages = []
    for message in messages:
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
        _messages.append({"role": "user", "content": f"{message['name']}: {get_content(message['message'])}"})

    return _messages

def add_name_message(messages, name):
    system_message = {"role": "system", "content": f"Your name is {name}"}

    for idx, message in enumerate(messages):
        if message["role"] != "system":
            break
    else:
        idx = len(messages)

    return messages[:idx] + [system_message] + messages[idx:]

class NamedAgent(Agent):
    def __init__(self, *args, **kwds):
        self.name = None
        Agent.__init__(self, *args, **kwds)

    def set_name(self, name):
        self.name = name

    def chat(self, messages, **kwds):
        if self.name is None:
            return super().chat(messages, **kwds)

        messages = filter_messages(messages, self.name)
        messages = add_name_message(messages, self.name)
        if DEBUG_MODE:
            print("==================================================")
            print(f"Agent: {self.name}") 
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            for message in messages:
                print(message)
                print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print("==================================================")
        response = super().chat(messages, **kwds)
        return {"name": self.name, "message": response}
    
    def call(self, message):
        if self.name is None:
            return super().call(message)

        assert message["name"] == self.name
        response = super().call(message["message"])
        return {"name": self.name, "message": response}

    def get_message_role(self, message):
        if self.name is None:
            return super().get_message_role(message)

        if is_encapsulated_message(message):
            return super().get_message_role(message["message"])
        else:
            return super().get_message_role(message)

    def is_message_containing_function_call(self, message):
        if self.name is None:
            return super().is_message_containing_function_call(message)

        if is_encapsulated_message(message):
            return super().is_message_containing_function_call(message["message"])
        else:
            return super().is_message_containing_function_call(message)

    def get_function_name_from_message(self, message):
        if self.name is None:
            return super().get_function_name_from_message(message)

        if is_encapsulated_message(message):
            return super().get_function_name_from_message(message["message"])
        else:
            return super().get_function_name_from_message(message)

    def get_function_arguments_from_message(self, message):
        if self.name is None:
            return super().get_function_arguments_from_message(message)

        if is_encapsulated_message(message):
            return super().get_function_arguments_from_message(message["message"])
        else:
            return super().get_function_arguments_from_message(message)

    def get_content_from_message(self, message):
        if self.name is None:
            return super().get_content_from_message(message)

        if is_encapsulated_message(message):
            return super().get_content_from_message(message["message"])
        else:
            return super().get_content_from_message(message)

