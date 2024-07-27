import json
import ollama
import asyncio
import pyperclip


def run_javascript(code):
    # for now I will manually copy/paste JS/response
    print(f"Running JavaScript code:\n{code}\n")
    console_output = input("Please copy output to clipboard, then press return to proceed and I will send the clipboard back to the model.")
    # read output from clipboard
    console_output = pyperclip.paste()
    return json.dumps({'output': console_output})


def print_message(message):
    print(f"{message['role']}:")
    if (message.get('tool_calls')):
        for tool in message['tool_calls']:
            print(f"  {tool['function']['name']}({tool['function']['arguments']})")
    if (message.get('content')):
        print(f"  {message['content']}")


async def run(model: str):
    print(f"Running with model: {model}\n")

    client = ollama.AsyncClient()
    # initial request
    messages = []
    # system_message = {'role': 'system', 'content': 'You area an expert flight tracker.'}
    system_message = {
        'role': 'system',
        'content': 'You are my browser extension that takes requests from a user to modify the current page that is loaded. You can ask to have JavaScript code run and you can get the response back. You can ask for multiple rounds of tool calls until you find and change whatever the user asks for.'
    }
    messages.append(system_message)
    print_message(system_message)
    # user_request = {'role': 'user', 'content': 'Delete everything on the page'}
    user_request = {'role': 'user', 'content': 'what is the default font?'}
    messages.append(user_request)
    print_message(user_request)

    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'run_javascript',
                'description': 'Run a JavaScript function in the browser and return console output',
                # TODO setup run_javascript and run_javascript_expression (latter returns value of last expression, or add a parameter for deciding what the output is?)
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'code': {
                            'type': 'string',
                            'description': 'The JavaScript code to run',
                        },
                    },
                    'required': ['code'],
                },
            },
        },
    ]

    response = await client.chat(
        model=model,
        messages=messages,
        tools=tools,
    )

    async def process_response(response):

        messages.append(response['message'])
        print_message(response['message'])

        if not response['message'].get('tool_calls'):
            return

        for tool in response['message']['tool_calls']:
            name = tool['function']['name']
            args = tool['function']['arguments']
            if name == 'run_javascript':
                function_response = run_javascript(args['code'])
            else:
                # response with invalid tool to model
                function_response = json.dumps({'error': 'Invalid tool'})

            tool_response = {
                'role': 'tool',
                'content': function_response,
            }
            messages.append(tool_response)
            print_message(tool_response)

        post_tool_response = await client.chat(model=model, tools=tools, messages=messages)
        return await process_response(post_tool_response)

    return await process_response(response)


# Run the async function
model = "mistral"
model = 'llama3.1:8b'  # makes up args/value that don't comport with requests :( ... maybe due to issues with initial quantization?
# model = 'llama3-groq-tool-use'
asyncio.run(run(model))
