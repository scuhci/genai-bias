import os
from openai import OpenAI

batch_id = ""
with open(batch_id, 'r') as file:
    batch_id = file.readlines()[0]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client.batches.cancel(batch_id)
