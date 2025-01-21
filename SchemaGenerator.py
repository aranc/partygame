import json

def generate_schema(source_code: str, connector, model: str):
    """
    Generates a JSON schema for a given function source code using OpenAI or another connector.

    :param source_code: The source code of the function.
    :param connector: The connector to use for the LLM (e.g., 'openai').
    :param model: The model to use (e.g., 'chatgpt-4o-latest').
    :return: The JSON schema as a string (not parsed).
    """

    # Few-shot examples to guide the LLM in understanding the desired output
    few_shot_examples = [
        {
            "function": """
def get_order_status(order_id: str) -> str:
    '''Fetches the status of an order based on the given order ID.'''
    pass
            """,
            "json_schema": {
                "name": "get_order_status",
                "description": "Fetches the status of an order based on the given order ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The unique identifier for the order."
                        }
                    },
                    "required": ["order_id"],
                    "additionalProperties": False
                }
            }
        },
        {
            "function": """
def calculate_total(price: float, tax: float) -> float:
    '''Calculates the total price after applying the tax.'''
    pass
            """,
            "json_schema": {
                "name": "calculate_total",
                "description": "Calculates the total price after applying the tax.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "price": {
                            "type": "number",
                            "description": "The price of the item before tax."
                        },
                        "tax": {
                            "type": "number",
                            "description": "The tax percentage applied to the price."
                        }
                    },
                    "required": ["price", "tax"],
                    "additionalProperties": False
                }
            }
        }
    ]

    # Construct few-shot examples in the prompt
    examples_string = ""
    for example in few_shot_examples:
        examples_string += f"Function:\n```{example['function']}```\nJSON Schema:\n{json.dumps(example['json_schema'], indent=2)}\n\n"

    # Supreme system prompt with detailed instructions
    system_prompt = (
        "You are an expert in converting Python function source code into JSON schema. "
        "Your job is to return a valid JSON schema describing the function name, description, and parameters. "
        "Do not return any extra text or formatting. The schema should be well-formatted and strictly adhere to JSON standards.\n\n"
        "Here are some examples to guide you:\n\n" + examples_string +
        "Now, convert the following function source code to JSON schema."
    )

    # User message with the provided source code
    user_message = f"Function source code:\n```{source_code}```"

    # Prepare messages for the connector
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    # Call the connector to process the messages and get the JSON schema
    response = connector.chat(
        model=model,
        messages=messages
    )

    content = response.choices[0].message.content

    # verify we can load the JSON
    try:
        json.loads(content)
    except:
        print("===================Source======================================")
        print(source_code)
        print("====================JSON=======================================")
        print(content)
        print("==================Expection====================================")
        raise


    # Return the raw JSON schema as a string
    return content
