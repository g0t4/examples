import json
import keyring
from selenium import webdriver
from selenium.common.exceptions import JavascriptException
from selenium.webdriver.chrome.service import Service
import openai
from openai.types.completion_choice import CompletionChoice
from rich import print

# FYI # brew install chromedriver

started_new_browser = False


def get_common_chrome_options() -> webdriver.ChromeOptions:
    brave_path = '/Applications/Brave Browser Beta.app/Contents/MacOS/Brave Browser Beta'

    options = webdriver.ChromeOptions()
    options.binary_location = brave_path
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})  # w/o this you can get logs, but not from driver.execute_script(code)

    return options


def create_driver(options):
    chromedriver_path = '/opt/homebrew/bin/chromedriver'
    return webdriver.Chrome(service=Service(chromedriver_path), options=options)


def use_new_browser_instance() -> webdriver.Chrome:
    global started_new_browser

    options = get_common_chrome_options()
    driver = create_driver(options)

    driver.get("https://www.google.com")
    return driver


def use_existing_browser_instance() -> webdriver.Chrome:
    options = get_common_chrome_options()
    options.add_experimental_option("debuggerAddress", "localhost:9222")
    return create_driver(options)


def ensure_browser_and_selenium_on_same_tab(driver: webdriver.Chrome):
    # ensure we are on the tab we are working with (FYI we could check document.hidden before doing this, but meh)
    driver.switch_to.window(driver.current_window_handle)
    #print(f"window_handles: {driver.window_handles}")

    # FYI localhost:9222/json remote debug has info that might help
    #   ID == window_handle
    #   type: "background_page", "service_worker", "page" are marked on each window/tab
    #   just missing active tab indicator


def run_javascript_selenium(code: str):
    try:
        output = driver.execute_script(code)
    except JavascriptException as e:
        output = e.msg
    return json.dumps({'output': output})


def get_browser_logs(level='ALL'):
    # PRN filter out nuissance logs, i.e. 'Permissions policy violation: unload is not allowed in this document.'?
    # PRN filter >= level severity (not == level)
    logs = driver.get_log('browser')
    if level != 'ALL':
        logs = [log for log in logs if log['level'] == level]
    # PRN get logs since last time this was called... do not always get all logs, can just cache previous logs and remove in new batch... OR there appears to be a timestamp parameter to get_log that is undocumented? https://stackoverflow.com/questions/44991009/clear-chrome-browser-logs-in-selenium-python
    return json.dumps({'logs': logs})


def get_color_for_role(role):
    if (role == 'user'):
        return "yellow"
    if (role == 'tool'):
        return "red"
    if (role == 'system'):
        return "blue"
    if (role == 'assistant'):
        return "green"
    return "white"


def print_message(message):

    if (isinstance(message, dict)):
        # hand rolled dict messages
        color = get_color_for_role(message['role'])
        print(f"[{color}]{message['role']}:")
        if (message.get('tool_calls')):
            for tool in message['tool_calls']:
                print(f"  [{color}]{tool['function']['name']}({tool['function']['arguments']})")
        if (message.get('content')):
            print(f"  [{color}]{message['content']}")

        return

    # chat completion type from openai
    color = get_color_for_role(message.role)
    print(f"[{color}]{message.role}:")
    if (hasattr(message, 'tool_calls') and message.tool_calls):
        for tool in message.tool_calls:
            print(f"  [{color}]{tool.function.name}({tool.function.arguments})")
    if (hasattr(message, 'content') and message.content):
        print(f"  [{color}]{message.content}")


def run(user_request: str, use_ollama=True):

    # *** ollama:
    if use_ollama:
        api_key = "ollama"
        base_url = "http://localhost:11434/v1"
        # model = "mistral"
        model = 'llama3.1:8b'  # makes up args/value that don't comport with requests :( ... maybe due to issues with initial quantization?
        # model = 'llama3-groq-tool-use' # refuses to even try using tools provided?! keeps asking follow up questions for info that I told it to get
    else:
        api_key = keyring.get_password("openai", "ask")
        base_url = None
        model = 'gpt-4o'

    print(f"Using model: {model}")
    client = openai.Client(api_key=api_key, base_url=base_url)

    messages = []

    system_message = {
        'role': 'system',
        'content': 'You are a browser extension that takes requests from a user to interact with the current page. You have control over my browser with these tools. You can ask for multiple rounds of tool calls until you accomplish whatever was requested. To get a response from javascript you MUST include a `return` i.e. `return 1+1` or `return document.hidden`'
        # ! WOW when I added return warning to the system message, llama3.1:8b pays attention and always includes it!!!! AND when I tried to remove the same caution in the tool descriptions, it stopped adding return, so leave it in both spots for now. AND openai gpt-4o started including return consistently too!!! (it wasn't the first time I tried it prior to update system message here)
    }
    messages.append(system_message)
    print_message(system_message)

    user_request = {'role': 'user', 'content': user_request}
    messages.append(user_request)
    print_message(user_request)

    tools = [{
        'type': 'function',
        'function': {
            'name': 'run_javascript_with_return',
            'description': 'Run a return statement (in the browser) and get the response back.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'return_statement': {
                        'type': 'string',
                        'description': 'The JavaScript code to run. MUST include a return statement i.e. `return 1+1` or `return document.hidden`',
                    }
                },
                'required': ['return_statement'],
            },
        },
    }, {
        'type': 'function',
        'function': {
            'name': 'get_browser_logs',
            'description': 'Get the browser logs from the current page.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'level': {
                        'type': 'string',
                        'description': 'The log level to filter on. Default is ALL.',
                        'enum': ['ALL', 'SEVERE', 'WARNING', 'INFO', 'CONFIG', 'FINE', 'FINER', 'FINEST'],
                    },
                },
            },
        },
    }]

    response = client.chat.completions.create(model=model, messages=messages, tools=tools).choices[0]

    def process_response(response):

        response_message = response.message
        response_tool_calls = response_message.tool_calls

        # always append response message (either final or tool_call, which is needed for context of later giving a tool response)
        messages.append(response_message)
        print_message(response_message)

        if not response_tool_calls:
            # PRN add some way to ask if it fulfilled the request or not, did it give up? if so try again, if not just repeat response
            return

        for tool in response_tool_calls:
            name = tool.function.name
            args = json.loads(tool.function.arguments)

            if name == 'run_javascript_with_return':
                function_response = run_javascript_selenium(args['return_statement'])
            elif name == 'get_browser_logs':
                function_response = get_browser_logs(args.get('level', 'ALL'))
            else:
                # response with invalid tool to model
                function_response = json.dumps({'error': 'Invalid tool'})

            # based on https://platform.openai.com/docs/guides/function-calling
            tool_response = {
                "tool_call_id": tool.id,
                "role": "tool",
                "name": name,
                "content": function_response,
            }
            messages.append(tool_response)
            print_message(tool_response)

        post_tool_response = client.chat.completions.create(model=model, messages=messages, tools=tools).choices[0]
        return process_response(post_tool_response)

    return process_response(response)


def test_selenium_without_llm():
    # test (temporary) for injecting return when LLM assumes it's not needed
    print("test if hidden", run_javascript_selenium("return document.hidden"))
    print("test single line w/o return: ", run_javascript_selenium("document.title"))
    print("test multi line w/o return: ", run_javascript_selenium("document.title\ndocument.location.href"))

    # print("test hello world: ", run_javascript_selenium("return 'hello world'"))

    logs = get_browser_logs('DEBUG')
    print("logs\n", logs)


def test_llm():

    # user_request = 'what is this website?'  # *** GREAT INTRO TO what I am doing here
    # user_request = 'Delete everything on the page'  # llama3 works
    # user_request = 'Find which search engine is loaded and use it to search for bananas.' # both llama3.1 & gpt-4o fail
    user_request = 'generate and write a random string to console and then read the value from the console'  # gpt4o works now (uses sequential tool calls), llama3.1 generates and writes but fails to read logs (hallucinates random string)
    # user_request = 'remove the paywall on this page'
    # user_request = 'are there any failures loading this page? If so can you try to help me fix them?'

    run(user_request, use_ollama=False)


# driver = use_new_browser_instance()
driver = use_existing_browser_instance()

ensure_browser_and_selenium_on_same_tab(driver)

# test_selenium_without_llm()
# exit()

test_llm()

if started_new_browser:
    input("Press return to quit, leaving browser open to inspect...")
