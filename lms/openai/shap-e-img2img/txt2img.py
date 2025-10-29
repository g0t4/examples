import torch
from diffusers import ShapEPipeline
from diffusers.utils import export_to_gif


ckpt_id = "openai/shap-e"
pipe = ShapEPipeline.from_pretrained(ckpt_id).to("cuda")

# %% 


guidance_scale = 15.0
prompt = "a shark"
images = pipe(
    prompt,
    guidance_scale=guidance_scale,
    num_inference_steps=64,
    frame_size=256,
).images


# %% 

for index, img_set in enumerate(images):
    gif_path = export_to_gif(img_set, f"shark_sampled_3d_{index}.gif")

