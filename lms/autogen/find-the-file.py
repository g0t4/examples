from autogen import UserProxyAgent, AssistantAgent

# openai gets it right wihthin 1 or 2 tries, awesome!
llm_config = {
    "config_list": [{
        "model": "gpt-4o",
        "base_url": "https://api.openai.com/v1",
    }]
}

assistant = AssistantAgent(
    "assistant",
    system_message="You are tasked with finding a file that I lost, in the current working directory. I only recall that it has the word 'foo' inside of it. Find it and show me the contents of it. You must devise code to find the file, writtin in python",
    llm_config=llm_config,
    is_termination_msg=lambda msg: "foo the bar" in msg["content"]
)

human = UserProxyAgent(
    "human",
    code_execution_config={"work_dir": "files", "use_docker": False}
)

result = human.initiate_chat(
    assistant,
    message="Please tell me a first command to run to find my file...",
)
