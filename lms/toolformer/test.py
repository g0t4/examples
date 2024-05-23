import torch
from toolformer_pytorch import Toolformer, PaLM

# simple calendar api call - function that returns a string

def Calendar():
    import datetime
    from calendar import day_name, month_name
    now = datetime.datetime.now()
    return f'Today is {day_name[now.weekday()]}, {month_name[now.month]} {now.day}, {now.year}.'

# prompt for teaching it to use the Calendar function from above

prompt = f"""
Your task is to add calls to a Calendar API to a piece of text.
The API calls should help you get information required to complete the text.
You can call the API by writing "[Calendar()]"
Here are some examples of API calls:
Input: Today is the first Friday of the year.
Output: Today is the first [Calendar()] Friday of the year.
Input: The president of the United States is Joe Biden.
Output: The president of the United States is [Calendar()] Joe Biden.
Input: [input]
Output: 
"""

data = [
    "The store is never open on the weekend, so today it is closed.",
    "The number of days from now until Christmas is 30",
    "The current day of the week is Wednesday."
]

# model - here using PaLM, but any nn.Module that returns logits in the shape (batch, seq, num_tokens) is fine

model = PaLM(
    dim = 512,
    depth = 2,
    heads = 8,
    dim_head = 64
).cuda()

# toolformer

toolformer = Toolformer(
    model = model,
    model_seq_len = 256,
    teach_tool_prompt = prompt,
    tool_id = 'Calendar',
    tool = Calendar,
    finetune = True
)

# invoking this will
# (1) prompt the model with your inputs (data), inserted into [input] tag
# (2) with the sampled outputs, filter out the ones that made proper API calls
# (3) execute the API calls with the `tool` given
# (4) filter with the specialized filter function (which can be used independently as shown in the next section)
# (5) fine-tune on the filtered results

filtered_stats = toolformer(data)

# then, once you see the 'finetune complete' message

response = toolformer.sample_model_with_api_calls("How many days until the next new years?")

# hopefully you see it invoke the calendar and utilize the response of the api call...
