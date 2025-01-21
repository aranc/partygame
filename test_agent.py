import json
import readline
import os
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
from termcolor import colored
from Agent import Agent
from SourceTracker import expose_to_agent
from icecream import ic

# Subclassing Agent
class TestAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = {}

    @expose_to_agent
    def add(self, a, b):
        """Adds two numbers."""
        return a + b

    @expose_to_agent
    def mul(self, a, b):
        """Multiplies two numbers."""
        return a * b

    @expose_to_agent
    def get(self, key):
        """Retrieves a value from the store."""
        return self.store.get(key, None)

    @expose_to_agent
    def set(self, key, value):
        """Sets a value in the store."""
        self.store[key] = value
        return f"Set {key} to {value}"

    @expose_to_agent
    def secret(self):
        """Returns a secret string."""
        return self._secret()

    def _secret(self):
        return "banana"

    @expose_to_agent
    def secret2(self, secret_input):
        """Returns a secret string based on the input."""
        return self._secret2(secret_input)

    def _secret2(self, secret_input):
        if secret_input == "bomb":
             raise ValueError("Boom!")
        return "OK" if secret_input == "monkey" else "NO"

    @expose_to_agent
    def plot(self, expr):
        """Plots an expression using matplotlib, numpy, and sympy."""
        x = sp.symbols('x')
        expression = sp.sympify(expr)  # Convert the expression to sympy format

        # Generate values for x from -10 to 10
        x_vals = np.linspace(-10, 10, 400)
        f = sp.lambdify(x, expression, 'numpy')  # Convert the sympy expression to a numpy function
        y_vals = f(x_vals)

        # Plot the function
        plt.plot(x_vals, y_vals, label=str(expr))
        plt.title(f"Plot of {expr}")
        plt.xlabel("x")
        plt.ylabel("f(x)")
        plt.grid(True)
        plt.legend()
        plt.show()

        return "Plot displayed successfully to the user."

def main():
    agent = TestAgent()
    messages = [{"role": "user", "content": "Hi"}]
    messages = [{"role": "user", "content": "Hi, which function calls do you support?"}]
    print(f"user> {messages[0]['content']}")

    # Enter the conversation loop
    while True:
        message = messages[-1]
        role = agent.get_message_role(message)
        is_function_call = agent.is_message_containing_function_call(message)

        if role == "assistant" and not is_function_call:
            user_input = input("user> ")
            messages.append({"role": "user", "content": user_input})

        elif role == "assistant" and is_function_call:
            function_name = agent.get_function_name_from_message(message)
            function_arguments = agent.get_function_arguments_from_message(message)
            ic(f"Calling function: {function_name} with arguments: {function_arguments}")

            message = agent.call(message)

            ic(f"Function call response: {json.loads(agent.get_content_from_message(message))}")
            messages.append(message)

        else:
            response = agent.chat(messages)
            messages.append(response)

            if agent.get_content_from_message(response):
                print(colored(agent.get_content_from_message(response), attrs=['reverse']))

if __name__ == '__main__':
    main()
