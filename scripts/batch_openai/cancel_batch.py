from openai import OpenAI

batch_id = ""
with open(batch_id, 'r') as file:
    batch_id = file.readlines()[0]

client = OpenAI(api_key=)
client.batches.cancel(batch_id)
