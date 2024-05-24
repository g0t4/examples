import os

from autogen import UserProxyAgent, AssistantAgent

config_list = [
  {
    "model": "codellama",
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
  }
]
llm_config={"config_list": config_list}
# llm_config={"config_list": [{"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]}]}

assistant = AssistantAgent(
    "assistant",
    system_message="You are tasked with finding a file that I lost, in the current working directory. I only recall that it has the word 'foo' inside of it. You must devise code to find the file, writtin in python",
    llm_config=llm_config,
    is_termination_msg=lambda msg: "test.txt" in msg["content"]
)

human = UserProxyAgent(
    "human",
    code_execution_config={"work_dir": "files", "use_docker": False}
)

result = human.initiate_chat(
    assistant,
    message="Please tell me a first command to run to find my file...",
)