import json
import ollama
import asyncio
import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# FYI # brew install chromedriver

started_new_browser = False


def use_new_browser_instance() -> webdriver.Chrome:
    global started_new_browser
    started_new_browser = True
    brave_path = '/Applications/Brave Browser Beta.app/Contents/MacOS/Brave Browser Beta'

    options = webdriver.ChromeOptions()
    options.binary_location = brave_path
    # options.add_argument("--start-maximized")
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})  # w/o this you can get logs, but not from driver.execute_script(code)

    chromedriver_path = '/opt/homebrew/bin/chromedriver'
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)

    driver.get("https://www.google.com")
    # *** have this connect to my current browser (frontmost window, current tab) instead of opening a new one
    # TODO hook up epoch times again and use ChatGPT to see how it handles it w/ tools, I think it will do really well actually... and/or try Claude too
    return driver


def use_existing_browser_instance() -> webdriver.Chrome:
    # remote debug port is 9222
    # https://stackoverflow.com/questions/38081076/how-to-connect-to-existing-chrome-browser-using-selenium
    options = webdriver.ChromeOptions()
    # how do I know what tab to use?
    options.add_experimental_option("debuggerAddress", "localhost:9222")
    return webdriver.Chrome(options=options)


def run_javascript_selenium(code: str):
    try:
        if code.startswith("return "):
            output = driver.execute_script(code)
        else:
            # I shouldn't need this hack but llama doesn't listen... to the tool description... maybe I need the system prompt to be more specific?
            lines_before_last = code.splitlines()[:-1]
            last_line = code.splitlines()[-1]
            last_line_with_return = f"return {last_line}"
            code_with_return = "\n".join(lines_before_last + [last_line_with_return])
            print(f"Running modified JavaScript code:\n{code_with_return}\n")
            output = driver.execute_script(code_with_return)

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
    # user_request = {'role': 'user', 'content': 'Delete everything on the page'} # works llama3
    # user_request = {'role': 'user', 'content': 'What website am I on?'}
    # user_request = {'role': 'user', 'content': 'Find which search engine is loaded and use it to search for bananas.'} # I bet OpenAI/Claude can handle this one! llama went off the rails and made a mess of JS and then made up a response b/c it didn't successfully get back anything to know which website it was on
    # user_request = {'role': 'user', 'content': 'write a random string to console and then read the value from the console'} # kinda llama3.1
    # user_request = {'role': 'user', 'content': 'remove the paywall on this page'}
    # user_request = {'role': 'user', 'content': 'are there any failures loading this page? If so can you try to help me fix them?'}
    user_request = {'role': 'user', 'content': 'what is this website?'}
    messages.append(user_request)
    print_message(user_request)

    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'eval_javascript',
                # PRN should I add a method specific to eval_javascript that makes it clear it can be used to look up information?
                'description': 'Run a script in the browser. The last return statment is returned to you.',
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
            # PRN add some way to ask if it fulfilled the request or not, did it give up? if so try again, if not just repeat response
            return

        for tool in response['message']['tool_calls']:
            name = tool['function']['name']
            args = tool['function']['arguments']
            if name == 'eval_javascript':
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


def test_selenium_without_llm():
    # test (temporary) for injecting return when LLM assumes it's not needed
    print("test single line w/o return: ", run_javascript_selenium("document.title"))
    print("test multi line w/o return: ", run_javascript_selenium("document.title\ndocument.location.href"))

    # print("test hello world: ", run_javascript_selenium("return 'hello world'"))
    # logs = driver.get_log('browser')
    # print("logs\n", logs)


def test_llm():
    # Run the async function
    model = "mistral"
    model = 'llama3.1:8b'  # makes up args/value that don't comport with requests :( ... maybe due to issues with initial quantization?
    # model = 'llama3-groq-tool-use'
    asyncio.run(run(model))


driver = use_new_browser_instance()
# driver = use_existing_browser_instance()

test_selenium_without_llm()

# test_llm()

if started_new_browser:
    input("Press return to quit, leaving browser open to inspect...")
