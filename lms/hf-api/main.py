from huggingface_hub import HfApi
api = HfApi()
# models = api.list_models(search="bert", filter="text-classification")
# models = api.list_models(search="Qwen/Qwen") # works! too good! too many results!
# for model in models:
#     print(model.modelId)
users = api.list_user_followers("weshigbee")
for user in users:
    print(user.fullname, user.username)
