import os
import json
import importlib
from CachedAnnotations import CachedAnnotations
from icecream import ic


class Agent(CachedAnnotations):
    def __init__(self, connector: str = 'openai', model: str = 'gpt-4o', additional_connector_args: dict = {}, cache_filepath: str = None):
        """
        Initialize the agent with a connector, model, and any additional connector arguments.
        """
        self.model = model
        self.connector = connector
        self.additional_connector_args = additional_connector_args
        self.chat_method = None

        # Initialize the parent class and ensure json_cache is initialized
        if cache_filepath is not None:
            super().__init__(cache_filepath=cache_filepath)
        else:
            super().__init__()

        # Ensure json_cache exists
        if not hasattr(self, 'json_cache'):
            self.json_cache = {}  # Create a json_cache if missing

        self.load_connector()

    def load_connector(self):
        """
        Load the specified connector (e.g., OpenAI) dynamically from the connectors folder.
        """
        connector_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'connectors', f'{self.connector}.py'))
        try:
            spec = importlib.util.spec_from_file_location('chat_connector', connector_path)
            self.chat_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.chat_module)
            self.chat_method = self.chat_module.chat
        except (FileNotFoundError, ImportError) as e:
            raise ImportError(f"Failed to load connector {self.connector}. Error: {e}")

    def switch_connector_and_model(self, connector: str, model: str, additional_connector_args: dict = {}):
        """
        Dynamically switch the connector and model.
        """
        self.model = model
        self.connector = connector
        self.additional_connector_args = additional_connector_args
        self.load_connector()

    def chat(self, messages, restrict_tools=None, force_tools_usage=False, disable_tools=False, **kwds):
        if disable_tools:
            tools = {}
        else:
            tools = self.get_tracked_methods_source_and_json_annotation()

        if restrict_tools:
            for tool in restrict_tools:
                if tool not in tools:
                    raise ValueError(f"Tool '{tool}' not found in the tracked methods.")
            tools = {k: v for k, v in tools.items() if k in restrict_tools}

        tools = [{"type": "function", "function": json.loads(tool["json_annotation"])} for tool in tools.values()]

        # Log the tools being sent to the model for clarity
        #ic(f"Tools sent to model: {tools}")

        # Send the current messages and tools to the model
        additional_args = {}
        if len(tools) > 0:
            assert not disable_tools, "Shouldn't happen"
            additional_args["tools"] = tools
            additional_args["parallel_tool_calls"] = False
            if force_tools_usage:
                additional_args["tool_choice"] = "required"
        else:
            assert not force_tools_usage, "Cannot force tools usage when no tools are available."

        additional_args.update(kwds)

        response = self.chat_method(
            model=self.model,
            messages=messages,
            **additional_args,
            **self.additional_connector_args
        )

        return response.choices[0].message

    def call(self, message):
        """
        Executes the function call suggested by the model and appends the result to the messages.
        """
        func_name = message.tool_calls[0].function.name
        func_args = message.tool_calls[0].function.arguments
        call_id = message.tool_calls[0].id

        # Check if the function exists
        tracked_methods = self.get_tracked_methods_source_and_json_annotation().keys()
        if func_name in tracked_methods:
            func = getattr(self, func_name)
            try:
                # Execute the function
                result = func(**json.loads(func_args))

            except Exception as e:
                result = f"Error during execution of {func_name}: {str(e)}"
        else:
            result = f"Function '{func_name}' not found."

        message = {"role": "tool", "content": json.dumps(result), "tool_call_id": call_id}
        return message

    @staticmethod
    def get_message_role(message):
        try:
            return message.role
        except:
            return message.get("role", None)

    @staticmethod
    def is_message_containing_function_call(message):
        try:
            if message.function_call is not None:
                return True
        except:
            pass
        try:
            if message.tool_calls is not None:
                return True
        except:
            pass
        return False

    @staticmethod
    def get_function_name_from_message(message):
        try:
            return message.function_call.name
        except:
            return message.tool_calls[0].function.name

    @staticmethod
    def get_function_arguments_from_message(message):
        try:
            return message.function_call.arguments
        except:
            return message.tool_calls[0].function.arguments

    @staticmethod
    def get_content_from_message(message):
        try:
            return message.content
        except:
            return message["content"]

