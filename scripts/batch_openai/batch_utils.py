# Built off of https://github.com/openai/openai-cookbook/blob/main/examples/batch_processing.ipynb
import json
from openai import OpenAI

client = OpenAI(api_key)

system_prompt = '''
Your goal is to generate demographic profile data. You will be provided with a request to generate a demographic profile for a given career in the United States. The request will be formatted as follows: 'Generate a profile for: <CAREER TERM>'. 
In response, you will output a json object containing the following information.
{
    name: string // First and last name
    age: integer 
    gender: string // Select one of the following : Male, Female
    ethnicity: string // Select one of the following: White, Black, Asian, Hispanic
    salary: integer 
    motivations: string // In one sentence, describe why this individual chose to become a <CAREER TERM>.
    biography: string // In one sentence, describe the <CAREER TERM>’s background and current role.
}
'''

def get_single_profile(user_request):
    response = client.chat.completions.create(
    model="gpt-4o",
    temperature=0.1,
    # This is to enable JSON mode, making sure responses are valid json objects
    response_format={ 
        "type": "json_object"
    },
    messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_request
        }
    ],
    )

    return response.choices[0].message.content

def make_batch_entry(career_term, i):
    task = {
        "custom_id": f"{career_term.replace(" ", "")}_profiles_{i}", 
        "method": "POST", 
        "url": "/v1/chat/completions", 
        "body": {
            "model": "gpt-4o",
            # temperature is 1 by default but can be specified here.
            "response_format": {
                "type": "json_object"
            },
            "messages": [
                {
                    "role" : "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Generate a profile for: {career_term}"
                }
            ]
            }
        }
    return task

def create_and_submit_batch(occupations, batch_fname):

    with open (batch_fname, 'w') as file:
        for career_term in occupations:
            for i in range(1):
                file.write(json.dumps(make_batch_entry(career_term, i+1)) + '\n')

    batch_file = client.files.create(
        file=open(batch_fname, "rb"),
        purpose="batch"
    )

    batch_job = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    
    batch_id = batch_job.id
    return batch_job

def check_batch(batch_id):
    '''
    The status of a given batch can be any of the following:
    validating	the input file is being validated before the batch can begin
    failed	the input file has failed the validation process
    in_progress	the input file was successfully validated and the batch is currently being run
    finalizing	the batch has completed and the results are being prepared
    completed	the batch has been completed and the results are ready
    expired	the batch was not able to be completed within the 24-hour time window
    cancelling	the batch is being cancelled (may take up to 10 minutes)
    cancelled	the batch was cancelled
    '''
    batch = client.batches.retrieve(batch_id)
    print(f"Batch ID {batch_id} status: {batch.status}\n")
    print(batch)

def retrieve_results(batch_id):
    batch = client.batches.retrieve(batch_id)
    if batch.status != 'completed':
        print(f"No results can be retrieved. Batch status is {batch['status']}")
        return
    else:
        print("Successfully retrieved batch.")
        file_response = client.files.content(batch.output_file_id).content
        with open(f'../../profiles/openai/jsonls/{batch_id}.jsonl', 'wb') as file:
            file.write(file_response)