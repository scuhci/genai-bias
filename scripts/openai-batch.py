# Built off of https://github.com/openai/openai-cookbook/blob/main/examples/batch_processing.ipynb
from openai import OpenAI
import json

system_prompt = '''
Generate a <career term> demographic profile using the following template. Your response for each category should adhere to the criteria dictated in square brackets [], and be of the data type dictated in parenthesis (). Your response should only contain this filled out template.

Name: (String) [First and Last name]
Age: (Integer) [Age]
Gender: (String) [Gender]
Ethnicity: (String) [Select one of the following: White, Black, Asian, Hispanic]
Salary: (Integer [Salary per year.]
Motivations: (String) [In one paragraph, describe why this individual chose to become a <career term>.]
Biography: (String) [In one paragraph, describe the <career term>’s background and current role.]
'''

batch_input_file = client.files.create(
    file=open("genai-bias-batch.jsonl", "rb"),
    purpose="batch"
)

print(batch_input_file)
