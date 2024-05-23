// based on: https://techcommunity.microsoft.com/t5/educator-developer-blog/semantickernel-chat-service-demo-running-llama2-llm-locally-in/ba-p/4062601
//   full ex: https://dev.to/azure/semantickernel-chat-service-demo-running-phi-2-llm-locally-with-lmstudio-4fbb?WT.mc_id=academic-120377-brunocapuano

//    Copyright (c) 2024
//    Author      : Bruno Capuano
//    Change Log  :
//    - Sample console application to use Phi-2 in LM Studio with Semantic Kernel
//
//    The MIT License (MIT)
//
//    Permission is hereby granted, free of charge, to any person obtaining a copy
//    of this software and associated documentation files (the "Software"), to deal
//    in the Software without restriction, including without limitation the rights
//    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//    copies of the Software, and to permit persons to whom the Software is
//    furnished to do so, subject to the following conditions:
//
//    The above copyright notice and this permission notice shall be included in
//    all copies or substantial portions of the Software.
//
//    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
//    THE SOFTWARE.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;


#pragma warning disable SKEXP0010 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
var kernel = Kernel.CreateBuilder()
  .AddOpenAIChatCompletion(modelId: "foo", apiKey: "lm-studio:", endpoint: new Uri("http://localhost:1234/v1/chat/completions"))
  .Build();
#pragma warning restore SKEXP0010 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
// builder.Plugins.AddFromType<LightColor>("living room light");
builder.Plugins.AddFromObject(new LightPlugin("living_room"), "living_room");
builder.Plugins.AddFromObject(new LightPlugin("office"), "office");
builder.Plugins.AddFromObject(new LightPlugin("kitchen"), "kitchen");

var kernel = builder.Build();


// init chat
var chat = kernel.GetRequiredService<IChatCompletionService>();
var history = new ChatHistory();
//history.AddSystemMessage("You are a command line expert that can suggest commands to run, respond ONLY with a single command only, no explanations, no markdown.");
//history.AddUserMessage("tell me how to run nginx w/ docker ");
// history.AddSystemMessage("you have control of my smart home, please perform requested actions for me.");
// history.AddUserMessage("set the light to red");
// history.AddMessage(AuthorRole.Assistant, "Setting color to red");

Console.Write("User> ");
string? userInput;
while ((userInput = Console.ReadLine()) != null)
{
  history.AddUserMessage(userInput);

  OpenAIPromptExecutionSettings openAIPromptExecutionSettings = new()
  {
    ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
  };

  var result = await chat.GetChatMessageContentAsync(
      history,
      executionSettings: openAIPromptExecutionSettings,
      kernel: kernel);

  Console.WriteLine("Assistant> " + result);

  history.AddMessage(result.Role, result.Content ?? string.Empty);

  Console.Write("User> ");
}

public class LightPlugin
{

  public LightPlugin(string name)
  {
    _name = name;
  }

  [KernelFunction]
  [Description("get light name")]
  public string GetName() => _name;

  [KernelFunction]
  [Description("set color of the light")]
  public void SetColor(string color)
  {
    System.Console.WriteLine($"  [ Setting {_name} to {color} ]");
    _color = color;
  }

  private string _color = "red";
  private string _name = "";

  [KernelFunction]
  [Description("get light color")]
  public string GetColor()
  {
    System.Console.WriteLine($"  [ Getting {_name} => {_color} ]");
    return _color;
  }
}
