import json
import ollama
import asyncio


# Simulates an API call to get flight times
# In a real application, this would fetch data from a live database or API
def get_flight_times(departure: str, arrival: str) -> str:
    flights = {
        'NYC-LAX': {
            'departure': '08:00 AM',
            'arrival': '11:35 AM',
            'duration': '5h 35m'
        },
        'LAX-NYC': {
            'departure': '02:00 PM',
            'arrival': '08:50 PM',
            'duration': '4h 50m'
        },
        'LHR-JFK': {
            'departure': '10:00 AM',
            'arrival': '01:00 PM',
            'duration': '8h 00m'
        },
        'JFK-LHR': {
            'departure': '09:00 PM',
            'arrival': '09:00 AM',
            'duration': '7h 00m'
        },
        'CDG-DXB': {
            'departure': '11:00 AM',
            'arrival': '08:00 PM',
            'duration': '6h 00m'
        },
        'DXB-CDG': {
            'departure': '03:00 AM',
            'arrival': '07:30 AM',
            'duration': '7h 30m'
        },
    }

    key = f'{departure}-{arrival}'.upper()
    return json.dumps(flights.get(key, {'error': 'Flight not found'}))


def print_message(message):
    print(f"{message['role']}:")
    if (message.get('tool_calls')):
        for tool in message['tool_calls']:
            print(f"  {tool['function']['name']}({tool['function']['arguments']})")
    if (message.get('content')):
        print(f"  {message['content']}")


async def run(model: str):
    client = ollama.AsyncClient()
    # initial request
    messages = []
    system_message = {'role': 'system', 'content': 'You area an expert flight tracker.'}
    messages.append(system_message)
    print_message(system_message)
    # user_request = {'role': 'user', 'content': 'What is the flight time from New York (NYC) to Los Angeles (LAX)? Also what is the return flight time?'}
    user_request = {'role': 'user', 'content': 'Which flight is longer, from NYC to LAX, or from LAX to NYC?'}
    messages.append(user_request)
    print_message(user_request)

    # First API call: Send the query and function description to the model
    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'get_flight_times',
                'description': 'Get the flight times between two cities',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'departure': {
                            'type': 'string',
                            'description': 'The departure city (airport code)',
                        },
                        'arrival': {
                            'type': 'string',
                            'description': 'The arrival city (airport code)',
                        },
                    },
                    'required': ['departure', 'arrival'],
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

        available_functions = {
            'get_flight_times': get_flight_times,
        }
        for tool in response['message']['tool_calls']:
            function_to_call = available_functions[tool['function']['name']]
            function_response = function_to_call(tool['function']['arguments']['departure'], tool['function']['arguments']['arrival'])

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
# model = 'llama3.1:8b' # makes up args/value that don't comport with requests :( ... maybe due to issues with initial quantization?
# model = 'llama3-groq-tool-use'
asyncio.run(run(model))
