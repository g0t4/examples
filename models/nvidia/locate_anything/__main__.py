# setup an example of 
# https://huggingface.co/google/gemma-4-12B
#  w.r.t. its native multimodal capabilities
#
#  I want it to transcribe an audio file first:
#  /home/wes/repos/github/g0t4/examples/models/qwen3omni/clips/editing_samples/sample1/sample1.wav
#  verbatim transcription (request this first)
#     preferrably get timestamps too if it can do that
#
#  then follow up and ask it for suggested edits to make a final video
#    see if it can produce an edited transcript (w/ retakes edited out)
#    then if it can do that, see if it can provide time ranges to clip out (or keep) to get that final form
#
#
# also ask it to categorize the audio clips (what is going on in the clip):
#    /home/wes/repos/github/g0t4/examples/models/qwen3omni/clips/clip*.wav 
#
