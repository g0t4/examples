import json
import keyring
import ollama
import asyncio
import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import openai
from openai.types.completion_choice import CompletionChoice

# FYI # brew install chromedriver

started_new_browser = False


def get_common_chrome_options() -> webdriver.ChromeOptions:
    brave_path = '/Applications/Brave Browser Beta.app/Contents/MacOS/Brave Browser Beta'

    options = webdriver.ChromeOptions()
    options.binary_location = brave_path
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})  # w/o this you can get logs, but not from driver.execute_script(code)

    return options


def use_new_browser_instance() -> webdriver.Chrome:
    global started_new_browser

    options = get_common_chrome_options()
    driver = create_driver(options)

    driver.get("https://www.google.com")
    return driver


def create_driver(options):
    chromedriver_path = '/opt/homebrew/bin/chromedriver'
    return webdriver.Chrome(service=Service(chromedriver_path), options=options)


def use_existing_browser_instance() -> webdriver.Chrome:
    options = get_common_chrome_options()
    options.add_experimental_option("debuggerAddress", "localhost:9222")
    return create_driver(options)


def run_javascript_selenium(code: str):
    try:
        # if code.startswith("return "):
        output = driver.execute_script(code)
        # else:
        #     # I shouldn't need this hack but llama doesn't listen... to the tool description... maybe I need the system prompt to be more specific?
        #     lines_before_last = code.splitlines()[:-1]
        #     last_line = code.splitlines()[-1]
        #     last_line_with_return = f"return {last_line}"
        #     code_with_return = "\n".join(lines_before_last + [last_line_with_return])
        #     print(f"Running modified JavaScript code:\n{code_with_return}\n")
        #     output = driver.execute_script(code_with_return)
        #     # FML... "Message: javascript error: Cannot read properties of null (reading 'remove')\n when return on a null

    except Exception as e:
        output = str(e)
    return json.dumps({'output': output})


def get_browser_logs():
    # PRN filter out nuissance logs, i.e. 'Permissions policy violation: unload is not allowed in this document.'?
    # make a new tool to ask when needed
    logs = driver.get_log('browser')
    # PRN get logs since last time this was called... do not always get all logs, can just cache previous logs and remove in new batch... OR there appears to be a timestamp parameter to get_log that is undocumented? https://stackoverflow.com/questions/44991009/clear-chrome-browser-logs-in-selenium-python
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


async def run():

    # *** ollama:
    # api_key = "ollama"
    # base_url = "http://localhost:11434/v1"
    # Run the async function
    # model = "mistral"
    model = 'llama3.1:8b'  # makes up args/value that don't comport with requests :( ... maybe due to issues with initial quantization?
    # model = 'llama3-groq-tool-use' # refuses to even try using tools provided?! keeps asking follow up questions for info that I told it to get

    # *** openai:
    api_key = keyring.get_password("openai", "ask")
    base_url = None
    model = 'gpt-4o'

    client = openai.Client(api_key=api_key, base_url=base_url)
    # initial request
    messages = []
    # system_message = {'role': 'system', 'content': 'You area an expert flight tracker.'}
    system_message = {
        'role': 'system',
        'content': 'You are my browser extension that takes requests from a user to modify the current page that is loaded. I am providing tools for you to run JavaScript code and get back a response. You have control over my browser with these tools. You can ask for multiple rounds of tool calls until you find and change whatever the user asks for. If you use eval_javascript, you must add a return statement to get information back.'
    }
    messages.append(system_message)
    print_message(system_message)
    # user_request = {'role': 'user', 'content': 'Delete everything on the page'} # works llama3
    # user_request = {'role': 'user', 'content': 'Find which search engine is loaded and use it to search for bananas.'} # I bet OpenAI/Claude can handle this one! llama went off the rails and made a mess of JS and then made up a response b/c it didn't successfully get back anything to know which website it was on
    # user_request = {'role': 'user', 'content': 'write a random string to console and then read the value from the console'} # kinda llama3.1
    # user_request = {'role': 'user', 'content': 'remove the paywall on this page'}
    # user_request = {'role': 'user', 'content': 'are there any failures loading this page? If so can you try to help me fix them?'}
    user_request = {'role': 'user', 'content': 'what is this website?'}  # *** GREAT INTRO TO what I am doing here
    messages.append(user_request)
    print_message(user_request)

    tools = [
        {
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
        },
        {
            'type': 'function',
            'function': {
                'name': 'run_javascript',
                'description': 'Run a script in the browser.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'code': {
                            'type': 'string',
                            'description': 'The JavaScript code to run.',
                        }
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

    response = client.chat.completions.create(model=model, messages=messages, tools=tools).choices[0]

    async def process_response(response):

        response_message = response.message
        response_tool_calls = response_message.tool_calls  # array?

        # always append response message (either final or tool_call, which is needed for context of later giving a tool response)
        messages.append(response_message) # FYI it appears ok to mix and match my message dicts and the class from openai here (message type)
        # print_message(response_message) # TODO add printing this so I can see tool call w/o needing to print use_tool below... but I need to standardize on the message interface first as I use a dict sometimmes and then openai message is a class... not sure I can new it up but my print needs to handle both? 

        if not response_tool_calls:
            # PRN add some way to ask if it fulfilled the request or not, did it give up? if so try again, if not just repeat response
            return

        for tool in response_tool_calls:
            name = tool.function.name
            id = tool.id
            arguments = tool.function.arguments
            print("use_tool: ", name, arguments)
            args = json.loads(arguments)  # args as json, need to load it
            print(args)
            if name == 'run_javascript':
                function_response = run_javascript_selenium(args['code'])
            elif name == 'run_javascript_with_return':
                # FML... llama is still using this tool w/o a return randomly... but more often (at least 50% of time) its add a return now! but it never uses the other JS function now?! am I misconfiguring tools?
                function_response = run_javascript_selenium(args['return_statement'])
            elif name == 'get_browser_logs':
                function_response = get_browser_logs()
            else:
                # response with invalid tool to model
                function_response = json.dumps({'error': 'Invalid tool'})

            # based on https://platform.openai.com/docs/guides/function-calling
            tool_response = {
                "tool_call_id": id,
                "role": "tool",
                "name": name,
                "content": function_response,
            }
            messages.append(tool_response)
            print_message(tool_response)

        post_tool_response = client.chat.completions.create(model=model, messages=messages, tools=tools).choices[0]
        return await process_response(post_tool_response)

    return await process_response(response)


def test_selenium_without_llm():
    # test (temporary) for injecting return when LLM assumes it's not needed
    print("test if hidden", run_javascript_selenium("return document.hidden"))
    print("test single line w/o return: ", run_javascript_selenium("document.title"))
    print("test multi line w/o return: ", run_javascript_selenium("document.title\ndocument.location.href"))

    # print("test hello world: ", run_javascript_selenium("return 'hello world'"))
    # logs = driver.get_log('browser')
    # print("logs\n", logs)


def test_llm():
    asyncio.run(run())


def ensure_browser_and_selenium_on_same_tab(driver: webdriver.Chrome):
    # ensure we are on the tab we are working with (FYI we could check document.hidden before doing this, but meh)
    driver.switch_to.window(driver.current_window_handle)
    #print(f"window_handles: {driver.window_handles}")

    # FYI localhost:9222/json remote debug has info that might help
    #   ID == window_handle
    #   type: "background_page", "service_worker", "page" are marked on each window/tab
    #   just missing active tab indicator


# driver = use_new_browser_instance()
driver = use_existing_browser_instance()

ensure_browser_and_selenium_on_same_tab(driver)

# test_selenium_without_llm()
# exit()

test_llm()

if started_new_browser:
    input("Press return to quit, leaving browser open to inspect...")
