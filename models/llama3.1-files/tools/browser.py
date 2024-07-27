import json
import ollama
import asyncio
import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# FYI # brew install chromedriver

brave_path = '/Applications/Brave Browser Beta.app/Contents/MacOS/Brave Browser Beta'

options = webdriver.ChromeOptions()
options.binary_location = brave_path
# options.add_argument("--start-maximized")
options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})  # w/o this you can get logs, but not from driver.execute_script(code)

chromedriver_path = '/opt/homebrew/bin/chromedriver'
driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)

driver.get("https://www.google.com")


def run_javascript_selenium(code):
    try:
        output = driver.execute_script(code)
    except Exception as e:
        output = str(e)
    return json.dumps({'output': output})


def test_selenium_without_llm():
    # response = run_javascript_selenium("return 'hello world'")
    response = run_javascript_selenium("return document.location.href")
    print(f"response: {response}")
    response = run_javascript_selenium("console.log('testing 1 2 3...')")
    print(f"response: {response}")
    logs = driver.get_log('browser')
    print(logs)
    input("when done, press return")
    exit(0)
# test_selenium_without_llm()


def get_browser_logs():
    # make a new tool to ask when needed
    logs = driver.get_log('browser')
    return json.dumps({'logs': logs})


def run_javascript_manually(code):
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
    user_request = {
        'role': 'user',
        'content': 'What website am I on?'
    }  # tries multiple things to answer, of course fails.. but still tries multiple tool rounds!
    messages.append(user_request)
    print_message(user_request)

    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'run_javascript',
                'description': 'Run a script in the browser, and if you use a return statement, the output will be returned.',
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
        {
            'type': 'function',
            'function': {
                'name': 'get_browser_logs',
                # TODO can I flush the logs after getting them each time so future calls dont get all of them again too...
                'description': 'Get the browser logs from the current page.',
                'parameters': {
                    'type': 'object',
                    'properties': {},
                },
            },
        }
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
                function_response = run_javascript_selenium(args['code'])
            elif name == 'get_browser_logs':
                function_response = get_browser_logs()
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
input("Press return to quit, will terminate the browser too..")
