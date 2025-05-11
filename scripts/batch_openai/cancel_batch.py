from openai import OpenAI

batch_id = ""
with open("/home/lonalynn/HCI/genai-bias/profiles/openai/jsonlsbatch_1_id.txt", 'r') as file:
    batch_id = file.readlines()[0]

client = OpenAI(api_key=)
client.batches.cancel(batch_id)
