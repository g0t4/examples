from autogen import ConversableAgent

number_to_guess = "690"

llm_config = {
    "config_list": [{
        # works every time it seems w/ gpt-4o:
        "model": "gpt-4o",
        "base_url": "https://api.openai.com/v1",
    }]
}

# llm_config = {
#     "config_list": [{
#         # fail sauce both llama3 and codellama
#         "model": "llama3",
#         "base_url": "http://localhost:11434/v1",
#         "api_key": "ollama",
#     }]
# }

agent_with_number = ConversableAgent(
    "agent_with_number",
    system_message="You are playing a game of guess-my-number. You have the "
    f"number {number_to_guess} in your mind, and I will try to guess it. "
    "We're going to play this like hot/cold in hide and go seek, say 'hot/hotter/burning' if my current guess is close(r) to it, otherwise say 'cold/colder/freezing' the further away I move from the number. Do not use up/down or high/low. ",
    llm_config=llm_config,
    is_termination_msg=lambda msg: number_to_guess in msg["content"],  # terminate if the number is guessed by the other agent
    human_input_mode="NEVER",  # never ask for human input
)

agent_guess_number = ConversableAgent(
    "agent_guess_number",
    system_message="I have a number in my mind, and you will try to guess it. "
    "If I say 'hot/hotter/burning', your guess is close(r) to it, otherwise say 'cold/colder/freezing' the further away you move from the number. Do not use up/down or high/low.",
    llm_config=llm_config,
    human_input_mode="NEVER",
)

result = agent_with_number.initiate_chat(
    agent_guess_number,
    message="I have a number between 1 and 1200. Guess it!",
)
